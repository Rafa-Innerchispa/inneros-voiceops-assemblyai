from __future__ import annotations

import argparse
import hmac
import json
import os
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from .adapters.local_amd import LocalAMDReasoner
from .adapters.local_qwen import LocalQwenReasoner
from .approval import ExplicitApprovalGate
from .auth import OAUTH_FLOW_COOKIE, SESSION_COOKIE, VoiceOpsAuth
from .audit import replay_summary
from .execution_permit import VoiceExecutionPermitManager
from .gateway import VoiceGateway
from .inneros_system_bridge import InnerOSSystemBridge
from .shared_memory import SharedMemoryBridge


MAX_BODY_BYTES = 16_384
MAX_TRANSCRIPT_CHARS = 1_000
DEFAULT_INTENT = (
    "Ralphi, revisa la incidencia del acceso norte y abre una orden tecnica si corresponde."
)
DEFAULT_APPROVAL = "Si, autorizo."
VOICE_AGENT_TOKEN_URL = "https://agents.assemblyai.com/v1/token"
VOICE_AGENT_TOKEN_TTL_SECONDS = 120
VOICE_AGENT_TOKEN_RATE_LIMIT_SECONDS = 5.0
INNEROS_PROVIDER_PYTHON_ENV = "VOICEOPS_INNEROS_PROVIDER_PYTHON"
INNEROS_PLATFORM_PATH_ENV = "VOICEOPS_INNEROS_PLATFORM_PATH"


def _env_truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class DemoSessionStore:
    """Thread-safe in-memory state for the judge-facing demo."""

    def __init__(
        self,
        gateway_factory: Callable[[], VoiceGateway] | None = None,
        memory_bridge: SharedMemoryBridge | None = None,
        system_bridge: InnerOSSystemBridge | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._gateway_factory = gateway_factory or VoiceGateway
        self._gateway = self._gateway_factory()
        self._memory_bridge = memory_bridge or SharedMemoryBridge()
        self._system_bridge = system_bridge or InnerOSSystemBridge()
        self._approval_gate = ExplicitApprovalGate()
        self._live_permits = VoiceExecutionPermitManager(ttl_seconds=45.0)
        self._pending_live_action: dict[str, Any] | None = None
        self._live_action_result: dict[str, Any] | None = None
        self._live_approval: dict[str, Any] | None = None
        self._last_system_query: dict[str, Any] | None = None
        self._last_result: dict[str, object] | None = None
        self._memory_recall: dict[str, object] | None = None
        self._memory_receipt: dict[str, object] | None = None
        self._memory_cross_agent: dict[str, object] | None = None

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._gateway = self._gateway_factory()
            self._last_result = None
            self._memory_recall = None
            self._memory_receipt = None
            self._memory_cross_agent = None
            self._pending_live_action = None
            self._live_action_result = None
            self._live_approval = None
            self._last_system_query = None
            return self._snapshot_unlocked()

    def submit_transcript(self, transcript: str) -> dict[str, Any]:
        normalized = _normalize_transcript(transcript)
        with self._lock:
            self._last_result = self._gateway.process_final_transcript(normalized)
            return self._snapshot_unlocked()

    def submit_intent(self, transcript: str) -> dict[str, Any]:
        normalized = _normalize_transcript(transcript)
        memory_recall = self._memory_bridge.recall(normalized)
        with self._lock:
            if self._gateway.pending_approval:
                raise ValueError("an approval is already pending")
            self._memory_recall = memory_recall
            self._last_result = self._gateway.process_final_transcript(
                normalized,
                shared_memory_context=memory_recall,
            )
            return self._snapshot_unlocked()

    def approve_pending(self, phrase: str) -> dict[str, Any]:
        normalized = _normalize_transcript(phrase)
        outcome: dict[str, object] | None = None
        with self._lock:
            if not self._gateway.pending_approval:
                raise ValueError("no action is awaiting approval")
            self._last_result = self._gateway.process_final_transcript(normalized)
            action = self._gateway.evidence.action_result
            approval = self._gateway.evidence.approval
            if (
                isinstance(self._last_result, dict)
                and self._last_result.get("status") == "completed"
                and action is not None
                and approval is not None
                and approval.approved
            ):
                outcome = {
                    "correlation_id": self._gateway.evidence.correlation_id,
                    "summary": (
                        f"Governed demo action {action.action_type} completed as {action.action_id}; "
                        "explicit approval and a single-use execution permit were recorded."
                    ),
                    "evidence_ref": (
                        f"evidence://voiceops/{self._gateway.evidence.correlation_id}/{action.action_id}"
                    ),
                    "source_truth": "SYNTHETIC",
                    "verification_passed": True,
                }
            state = self._snapshot_unlocked()

        if outcome:
            receipt = self._memory_bridge.remember_verified(**outcome)
            cross_agent = self._memory_bridge.recall(str(outcome["correlation_id"]))
            with self._lock:
                self._memory_receipt = receipt
                self._memory_cross_agent = cross_agent
                self._gateway.evidence.add_event(
                    "shared_memory_writeback",
                    status=receipt.get("status"),
                    truth=receipt.get("truth"),
                    provider=receipt.get("provider"),
                    stored=receipt.get("stored", False),
                    memory_id=receipt.get("memory_id"),
                    verification_passed=True,
                    transcript_persisted=False,
                )
                self._gateway.evidence.add_event(
                    "cross_agent_memory_recall",
                    status=cross_agent.get("status"),
                    truth=cross_agent.get("truth"),
                    provider=cross_agent.get("provider"),
                    hit_count=cross_agent.get("count", 0),
                )
                return self._snapshot_unlocked()
        return state

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_unlocked()

    def evidence(self) -> dict[str, Any]:
        with self._lock:
            return self._gateway.evidence.to_dict()

    def replay(self) -> dict[str, Any]:
        with self._lock:
            return replay_summary(self._gateway.evidence)

    def submit_guardian_voice_command(self, event: dict[str, Any], transcript: str) -> dict[str, Any]:
        """Process an authenticated WhatsApp/voice command bound to one Guardian event."""
        normalized = _normalize_transcript(transcript)
        event_id = str(event.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("Guardian event_id is required")
        with self._lock:
            current = self._gateway.workflow.inspect()
            current_event_id = str(current.get("event_id") or "")
            action = self._gateway.evidence.action_result
            if action is not None:
                action_event_id = str(action.details.get("source_event_id") or "")
                if action_event_id == event_id:
                    state = self._snapshot_unlocked()
                    state["bridge_status"] = "already_completed"
                    return state
                raise ValueError("session already completed for another Guardian event")
            if self._gateway.pending_approval:
                if current_event_id != event_id:
                    raise ValueError("approval is pending for another Guardian event")
            elif current_event_id != event_id or current.get("production_event") is not True:
                self._gateway.bind_guardian_event(event)
            self._last_result = self._gateway.process_final_transcript(normalized)
            state = self._snapshot_unlocked()
            state["bridge_status"] = str(self._last_result.get("status") or "processed")
            state["bridge_surface"] = "whatsapp_voice"
            state["bridge_event_id"] = event_id
            return state

    def tool_system_query(self, query: str) -> dict[str, Any]:
        normalized = _normalize_transcript(query)
        result = self._system_bridge.query(normalized)
        with self._lock:
            self._last_system_query = result
            self._gateway.evidence.add_event(
                "live_system_query",
                ok=result.get("ok"),
                source_truth=result.get("source_truth", "UNVERIFIED"),
                detected_tools=[item.get("tool") for item in result.get("detected", [])],
                read_tool_count=len(result.get("results", [])),
                proposed_write_count=len(result.get("write_proposals", [])),
                credentials_exposed=False,
            )
            correlation_id = self._gateway.evidence.correlation_id
        result["correlation_id"] = correlation_id
        result["requires_approval"] = bool(result.get("write_proposals"))
        if result.get("write_proposals"):
            result["approval_hint"] = "Say 'Sí, autorizo' / 'Yes, authorize' or press Permit + Act."
        return result

    def tool_propose_system_action(self, command: str) -> dict[str, Any]:
        normalized = _normalize_transcript(command)
        result = self._system_bridge.query(normalized)
        proposals = list(result.get("write_proposals") or [])
        protected = list(result.get("protected_proposals") or [])
        if protected and not proposals:
            return {
                "status": "protected",
                "requires_approval": False,
                "reason": "dedicated_approval_adapter_required",
                "protected_proposals": protected,
                "message": "This system action uses a dedicated safety adapter and cannot be executed through the generic VoiceOps permit.",
                "production_writes": False,
            }
        if not proposals:
            return {
                "status": "no_action_detected",
                "requires_approval": False,
                "live_result": result,
                "message": "No approval-gated live action was detected.",
                "production_writes": False,
            }
        proposal = dict(proposals[0])
        with self._lock:
            if self._gateway.pending_approval or self._pending_live_action is not None:
                raise ValueError("an approval is already pending")
            self._pending_live_action = proposal
            self._live_action_result = None
            self._live_approval = None
            self._last_system_query = result
            self._gateway.evidence.add_event(
                "live_action_proposed",
                tool=proposal.get("tool"),
                args=proposal.get("args"),
                source_truth="LIVE",
                execution_blocked=True,
            )
            correlation_id = self._gateway.evidence.correlation_id
        return {
            "status": "approval_required",
            "requires_approval": True,
            "proposal": proposal,
            "correlation_id": correlation_id,
            "approval_hint": "Say 'Sí, autorizo' / 'Yes, authorize' or press Permit + Act.",
            "production_writes": False,
        }

    def _approve_live_action(self, authorization_phrase: str) -> dict[str, Any]:
        normalized = _normalize_transcript(authorization_phrase)
        with self._lock:
            proposal = dict(self._pending_live_action or {})
            if not proposal:
                if self._live_action_result:
                    return {
                        "status": "already_completed",
                        "requires_approval": False,
                        "approval": self._live_approval,
                        "action": self._live_action_result,
                        "correlation_id": self._gateway.evidence.correlation_id,
                        "production_writes": True,
                    }
                raise ValueError("no action is awaiting approval")
            decision = self._approval_gate.decide(normalized)
            self._live_approval = {"approved": decision.approved, "reason": decision.reason, "phrase": authorization_phrase}
            self._gateway.evidence.add_event(
                "live_action_approval",
                approved=decision.approved,
                reason=decision.reason,
                transcript_persisted=False,
            )
            if not decision.approved:
                return {
                    "status": "blocked",
                    "requires_approval": True,
                    "approval": self._live_approval,
                    "proposal": proposal,
                    "reason": decision.reason,
                    "approval_hint": "Say 'Sí, autorizo' / 'Yes, authorize' or press Permit + Act.",
                    "production_writes": False,
                }
            source_event_id = f"inneros:{proposal.get('tool')}"
            action_type = str(proposal.get("tool") or "inneros_action")
            state_snapshot = {"proposal": proposal, "query": self._last_system_query.get("original_query") if self._last_system_query else None}
            permit = self._live_permits.issue(
                session_id=self._gateway.session_id,
                source_event_id=source_event_id,
                action_type=action_type,
                approval_transcript=normalized,
                proposal=proposal,
                state_snapshot=state_snapshot,
            )
            allowed, reason, consumed = self._live_permits.consume(
                permit.permit_id,
                session_id=self._gateway.session_id,
                source_event_id=source_event_id,
                action_type=action_type,
                approval_transcript=normalized,
                proposal=proposal,
                state_snapshot=state_snapshot,
            )
            if not allowed:
                return {
                    "status": "blocked",
                    "requires_approval": True,
                    "reason": reason,
                    "production_writes": False,
                }
            self._gateway.evidence.add_event(
                "live_execution_permit_consumed",
                permit_id=permit.permit_id,
                tool=action_type,
                single_use=True,
            )

        executed = self._system_bridge.execute(proposal)
        with self._lock:
            action = {
                "action_id": f"live_{int(time.time() * 1000)}",
                "action_type": action_type,
                "status": "completed" if executed.get("ok") else "failed",
                "details": {
                    "tool": action_type,
                    "args": proposal.get("args"),
                    "result": executed.get("result"),
                    "source_truth": executed.get("source_truth"),
                    "permit_id": consumed.permit_id if consumed else permit.permit_id,
                },
            }
            self._live_action_result = action
            self._pending_live_action = None
            self._gateway.evidence.add_event(
                "live_action_executed",
                action_id=action["action_id"],
                tool=action_type,
                ok=executed.get("ok"),
                source_truth=executed.get("source_truth"),
                permit_id=permit.permit_id,
            )
            correlation_id = self._gateway.evidence.correlation_id

        if executed.get("ok"):
            receipt = self._memory_bridge.remember_verified(
                correlation_id=correlation_id,
                summary=f"Live InnerOS action {action_type} completed with explicit human approval.",
                evidence_ref=f"evidence://voiceops/{correlation_id}/{action['action_id']}",
                source_truth="LIVE",
                verification_passed=True,
            )
            with self._lock:
                self._memory_receipt = receipt
        return {
            "status": action["status"],
            "requires_approval": False,
            "approval": self._live_approval,
            "action": action,
            "correlation_id": correlation_id,
            "production_writes": bool(executed.get("ok")),
        }

    def tool_inspect(self, intent: str) -> dict[str, Any]:
        normalized = _normalize_transcript(intent)
        duplicate = False
        try:
            state = self.submit_intent(normalized)
        except ValueError as exc:
            if str(exc) != "an approval is already pending":
                raise
            with self._lock:
                latest = self._gateway.evidence.turns[-1].transcript if self._gateway.evidence.turns else None
                if not self._gateway.pending_approval or latest != normalized or self._gateway.evidence.proposal is None:
                    raise
                state = self._snapshot_unlocked()
                duplicate = True
        shared_memory = state.get("shared_memory") if isinstance(state.get("shared_memory"), dict) else {}
        return {
            "status": "already_pending" if duplicate else (
                state.get("last_result", {}).get("status") if isinstance(state.get("last_result"), dict) else None
            ),
            "requires_approval": bool(state.get("pending_approval")),
            "guardian": state.get("guardian"),
            "route": state.get("route"),
            "proposal": state.get("proposal"),
            "memory": shared_memory.get("before_action"),
            "memory_bridge": shared_memory.get("bridge"),
            "correlation_id": state.get("correlation_id"),
            "production_writes": False,
        }

    def tool_recall(self, query: str) -> dict[str, Any]:
        normalized = _normalize_transcript(query)
        recall = self._memory_bridge.recall(normalized)
        with self._lock:
            self._memory_recall = recall
            self._gateway.evidence.add_event(
                "shared_memory_recalled",
                status=recall.get("status"),
                truth=recall.get("truth"),
                provider=recall.get("provider"),
                hit_count=recall.get("count", 0),
                query_bound=True,
            )
            correlation_id = self._gateway.evidence.correlation_id
        return {
            "status": recall.get("status"),
            "truth": recall.get("truth"),
            "provider": recall.get("provider"),
            "dataset": recall.get("dataset"),
            "count": recall.get("count", 0),
            "hits": recall.get("hits", []),
            "reason": recall.get("reason"),
            "correlation_id": correlation_id,
            "production_writes": False,
        }

    def tool_approve(self, authorization_phrase: str) -> dict[str, Any]:
        with self._lock:
            has_live_pending = self._pending_live_action is not None
            has_live_completed = self._live_action_result is not None and not self._gateway.pending_approval
        if has_live_pending or has_live_completed:
            return self._approve_live_action(authorization_phrase)
        duplicate = False
        try:
            state = self.approve_pending(authorization_phrase)
        except ValueError as exc:
            if str(exc) != "no action is awaiting approval":
                raise
            with self._lock:
                approval = self._gateway.evidence.approval
                action = self._gateway.evidence.action_result
                if approval is None or not approval.approved or action is None:
                    raise
                state = self._snapshot_unlocked()
                duplicate = True
        return {
            "status": "already_completed" if duplicate else (
                state.get("last_result", {}).get("status") if isinstance(state.get("last_result"), dict) else None
            ),
            "approval": state.get("approval"),
            "action": state.get("action"),
            "htr": state.get("htr"),
            "correlation_id": state.get("correlation_id"),
            "production_writes": False,
        }

    def _snapshot_unlocked(self) -> dict[str, Any]:
        evidence = self._gateway.evidence
        snapshot_event = next(
            (event for event in reversed(evidence.events) if event.kind == "state_snapshot"),
            None,
        )
        route_event = next(
            (event for event in reversed(evidence.events) if event.kind == "reasoning_route"),
            None,
        )
        guardian = snapshot_event.data.get("snapshot", {}) if snapshot_event else {}
        route = route_event.data.get("route", {}) if route_event else {}
        proposal = evidence.proposal
        approval = evidence.approval
        action = evidence.action_result
        htr = evidence.htr

        live_proposal = self._pending_live_action
        live_action = self._live_action_result
        live_approval = self._live_approval
        return {
            "mode": "hybrid_live",
            "reasoning_mode": _reasoning_mode(route),
            "production_writes": bool(live_action and live_action.get("status") == "completed"),
            "live_system_reads": True,
            "session_id": evidence.session_id,
            "correlation_id": evidence.correlation_id,
            "pending_approval": bool(self._gateway.pending_approval or live_proposal),
            "last_result": self._last_result,
            "live_system": {
                "bridge": self._system_bridge.status(),
                "last_query": self._last_system_query,
            },
            "transcript": evidence.turns[-1].transcript if evidence.turns else None,
            "guardian": guardian,
            "route": route,
            "proposal": (
                {
                    "action_type": str(live_proposal.get("tool") or "live_action"),
                    "summary": f"Execute live InnerOS tool {live_proposal.get('tool')}",
                    "requires_approval": True,
                    "payload": dict(live_proposal.get("args") or {}),
                }
                if live_proposal
                else (
                    {
                        "action_type": proposal.action_type,
                        "summary": proposal.summary,
                        "requires_approval": proposal.requires_approval,
                        "payload": proposal.payload,
                    }
                    if proposal
                    else None
                )
            ),
            "approval": (
                live_approval
                if live_approval
                else (
                    {"approved": approval.approved, "reason": approval.reason}
                    if approval
                    else None
                )
            ),
            "action": (
                live_action
                if live_action
                else (
                    {
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "status": action.status,
                        "details": action.details,
                    }
                    if action
                    else None
                )
            ),
            "htr": {
                "manual_seconds": htr.manual_seconds,
                "human_active_seconds": htr.human_active_seconds,
                "saved_seconds": htr.saved_seconds,
                "classification": htr.classification,
            }
            if htr
            else None,
            "shared_memory": {
                "bridge": self._memory_bridge.status(),
                "before_action": self._memory_recall,
                "writeback": self._memory_receipt,
                "cross_agent_recall": self._memory_cross_agent,
            },
            "timeline": [
                {"kind": event.kind, "at": event.at, "data": event.data}
                for event in evidence.events
            ],
        }


def _normalize_transcript(transcript: str) -> str:
    normalized = transcript.strip()
    if not normalized:
        raise ValueError("transcript must not be empty")
    if len(normalized) > MAX_TRANSCRIPT_CHARS:
        raise ValueError(f"transcript exceeds {MAX_TRANSCRIPT_CHARS} characters")
    return normalized


def _reasoning_mode(route: dict[str, Any]) -> str:
    if route.get("provider") == "local-amd-5" and route.get("truth") == "LIVE_MODEL_RESPONSE":
        return "amd5_live"
    if route.get("provider") == "local-intel-4" and route.get("truth") == "LIVE_MODEL_RESPONSE":
        return "local_qwen_live"
    if route.get("truth") == "SYNTHETIC":
        return "synthetic"
    return "pending"


def _deployment_profile(reasoner_mode: str) -> dict[str, Any]:
    configured = os.getenv("VOICEOPS_DEPLOYMENT_MODE", "").strip().lower()
    if configured in {"cloud", "cloud_run", "managed_cloud"}:
        mode = "cloud_run"
    elif configured in {"local", "sovereign_local", "edge", "on_prem", "on-prem"}:
        mode = "sovereign_local"
    elif os.getenv("K_SERVICE"):
        mode = "cloud_run"
    elif reasoner_mode in {"amd5", "localqwen"}:
        mode = "sovereign_local"
    else:
        mode = "judge_safe"

    if mode == "cloud_run":
        return {
            "mode": mode,
            "label": "GOOGLE CLOUD RUN",
            "surface": "Managed cloud deployment",
            "compute": "Google Cloud Run",
            "inference": "Judge-safe synthetic" if reasoner_mode == "synthetic" else "Configured cloud reasoner",
            "data_boundary": "Cloud demo boundary",
            "local_inference": False,
        }
    if mode == "sovereign_local":
        return {
            "mode": mode,
            "label": "SOVEREIGN LOCAL",
            "surface": "On-prem / edge deployment",
            "compute": "Local server",
            "inference": (
                "AMD / Qwen local"
                if reasoner_mode == "amd5"
                else ("Intel / Qwen local" if reasoner_mode == "localqwen" else "Local judge-safe fixture")
            ),
            "data_boundary": "Customer-controlled local boundary",
            "local_inference": reasoner_mode in {"amd5", "localqwen"},
        }
    return {
        "mode": mode,
        "label": "JUDGE SAFE",
        "surface": "Deterministic demo deployment",
        "compute": "Current host",
        "inference": "Judge-safe synthetic",
        "data_boundary": "No production writes",
        "local_inference": False,
    }


def build_gateway_factory(reasoner_mode: str) -> Callable[[], VoiceGateway]:
    if reasoner_mode == "synthetic":
        return VoiceGateway
    if reasoner_mode == "amd5":
        return lambda: VoiceGateway(reasoner=LocalAMDReasoner())
    if reasoner_mode == "localqwen":
        return lambda: VoiceGateway(reasoner=LocalQwenReasoner())
    raise ValueError(f"unsupported reasoner mode: {reasoner_mode}")


def _inneros_provider_bridge_configured() -> bool:
    python_path = os.getenv(INNEROS_PROVIDER_PYTHON_ENV, "").strip()
    platform_path = os.getenv(INNEROS_PLATFORM_PATH_ENV, "").strip()
    return bool(python_path and platform_path and Path(python_path).is_file() and Path(platform_path).is_dir())


def mint_voice_agent_token_from_inneros_provider(
    *,
    expires_in_seconds: int = VOICE_AGENT_TOKEN_TTL_SECONDS,
    timeout_seconds: float = 8.0,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Mint an ephemeral browser token through the canonical InnerOS provider.

    The permanent AssemblyAI credential remains inside Owner Vault. The child
    process returns only the short-lived token that is already intended for the
    browser session.
    """
    python_path = os.getenv(INNEROS_PROVIDER_PYTHON_ENV, "").strip()
    platform_path = os.getenv(INNEROS_PLATFORM_PATH_ENV, "").strip()
    if not python_path or not platform_path:
        raise ValueError("InnerOS AssemblyAI provider bridge is not configured")
    if not Path(python_path).is_file() or not Path(platform_path).is_dir():
        raise ValueError("InnerOS AssemblyAI provider bridge path is invalid")
    ttl = max(1, min(int(expires_in_seconds), 600))
    helper = (
        "import json,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from inneros_core_runtime import assemblyai_provider;"
        "print(json.dumps(assemblyai_provider.create_browser_token("
        "expires_in_seconds=int(sys.argv[2]))))"
    )
    completed = runner(
        [python_path, "-c", helper, platform_path, str(ttl)],
        capture_output=True,
        text=True,
        timeout=max(2.0, float(timeout_seconds) + 4.0),
        check=False,
    )
    if int(getattr(completed, "returncode", 1)) != 0:
        raise RuntimeError("InnerOS AssemblyAI provider bridge failed")
    raw = str(getattr(completed, "stdout", "") or "").strip().splitlines()
    if not raw:
        raise RuntimeError("InnerOS AssemblyAI provider bridge returned no result")
    try:
        payload = json.loads(raw[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("InnerOS AssemblyAI provider bridge returned invalid JSON") from exc
    token = payload.get("token") if isinstance(payload, dict) else None
    if not payload.get("ok") or not isinstance(token, str) or not token:
        raise RuntimeError("InnerOS AssemblyAI provider could not mint a temporary token")
    return {"token": token, "expires_in_seconds": ttl, "auth_source": "inneros_owner_vault"}


def mint_voice_agent_token(
    api_key: str,
    *,
    expires_in_seconds: int = VOICE_AGENT_TOKEN_TTL_SECONDS,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Mint a short-lived, single-use Voice Agent browser token server-side."""
    if not api_key.strip():
        raise ValueError("AssemblyAI API key is not configured")
    if not 1 <= expires_in_seconds <= 600:
        raise ValueError("expires_in_seconds must be between 1 and 600")
    url = VOICE_AGENT_TOKEN_URL + "?" + urlencode({"expires_in_seconds": expires_in_seconds})
    request = Request(url, headers={"Authorization": f"Bearer {api_key}"}, method="GET")
    with opener(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise ValueError("AssemblyAI token response did not include a token")
    return {"token": token, "expires_in_seconds": expires_in_seconds}


class VoiceOpsHandler(BaseHTTPRequestHandler):
    server_version = "VoiceOpsDemo/0.3"

    @property
    def store(self) -> DemoSessionStore:
        return self.server.store  # type: ignore[attr-defined]

    @property
    def web_root(self) -> Path:
        return Path(__file__).with_name("web")

    @property
    def auth(self) -> VoiceOpsAuth:
        return self.server.auth  # type: ignore[attr-defined]

    def _cookies(self) -> dict[str, str]:
        raw = self.headers.get("Cookie", "")
        result: dict[str, str] = {}
        for part in raw.split(";"):
            if "=" not in part:
                continue
            key, value = part.strip().split("=", 1)
            result[key] = value
        return result

    def _principal(self):
        token = self._cookies().get(SESSION_COOKIE, "")
        return self.auth.parse_session(token) if token else None

    def _auth_required(self) -> bool:
        return bool(self.server.auth_required)  # type: ignore[attr-defined]

    def _require_auth(self) -> bool:
        if not self._auth_required():
            return True
        if self._principal() is not None:
            return True
        self._send_json({"error": "authentication_required"}, status=HTTPStatus.UNAUTHORIZED)
        return False

    def _set_cookie(self, name: str, value: str, *, max_age: int, secure: bool = True) -> None:
        parts = [
            f"{name}={value}",
            "Path=/",
            f"Max-Age={max_age}",
            "HttpOnly",
            "SameSite=Lax",
        ]
        if secure:
            parts.append("Secure")
        self.send_header("Set-Cookie", "; ".join(parts))

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/healthz"}:
            self._send_json(
                {
                    "ok": True,
                    "service": "inneros-voiceops",
                    "deployment": self.server.deployment,  # type: ignore[attr-defined]
                    "live_voice_enabled": bool(self.server.live_voice_enabled),  # type: ignore[attr-defined]
                    "credential_configured": bool(os.getenv("ASSEMBLYAI_API_KEY")) or _inneros_provider_bridge_configured(),
                    "assemblyai_auth_source": (
                        "inneros_owner_vault"
                        if _inneros_provider_bridge_configured()
                        else ("environment" if os.getenv("ASSEMBLYAI_API_KEY") else "none")
                    ),
                    "guardian_voice_bridge_enabled": bool(self.server.bridge_token) or self._loopback_bridge_allowed(),  # type: ignore[attr-defined]
                    "guardian_voice_bridge_mode": "token" if self.server.bridge_token else ("loopback_only" if self._loopback_bridge_allowed() else "disabled"),  # type: ignore[attr-defined]
                    "live_system_bridge": self.store.snapshot().get("live_system", {}).get("bridge", {}),
                    "production_writes": False,
                    "auth": self.auth.public_status(),
                }
            )
            return
        if self.path == "/api/auth/session":
            principal = self._principal()
            self._send_json({
                "authenticated": principal is not None,
                "principal": principal.to_dict() if principal else None,
                "auth": self.auth.public_status(),
            })
            return
        if self.path == "/api/auth/login":
            try:
                location, flow_cookie = self.auth.begin_oauth()
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self.send_response(HTTPStatus.FOUND)
            self._set_cookie(OAUTH_FLOW_COOKIE, flow_cookie, max_age=600)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if self.path.startswith("/auth/callback"):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            code = str((query.get("code") or [""])[0])
            state = str((query.get("state") or [""])[0])
            flow_token = self._cookies().get(OAUTH_FLOW_COOKIE, "")
            try:
                principal = self.auth.complete_oauth(code=code, state=state, flow_token=flow_token)
                session = self.auth.issue_session(principal)
            except (ValueError, OSError, TimeoutError, json.JSONDecodeError):
                self._send_json({"error": "oauth_login_failed"}, status=HTTPStatus.UNAUTHORIZED)
                return
            self.send_response(HTTPStatus.FOUND)
            self._set_cookie(SESSION_COOKIE, session, max_age=self.auth.session_ttl_seconds)
            self._set_cookie(OAUTH_FLOW_COOKIE, "", max_age=0)
            self.send_header("Location", "/console")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if self.path == "/console" and not self._require_auth():
            return
        if self.path == "/api/state":
            if not self._require_auth():
                return
            state = self.store.snapshot()
            principal = self._principal()
            state["auth"] = {
                "authenticated": principal is not None,
                "principal": principal.to_dict() if principal else None,
            }
            state["assemblyai_voice_agent_enabled"] = bool(self.server.live_voice_enabled)  # type: ignore[attr-defined]
            state["deployment"] = self.server.deployment  # type: ignore[attr-defined]
            self._send_json(state)
            return
        if self.path == "/api/evidence":
            if not self._require_auth():
                return
            self._send_json(self.store.evidence())
            return
        if self.path == "/api/replay":
            if not self._require_auth():
                return
            self._send_json(self.store.replay())
            return
        if self.path == "/api/assemblyai/token":
            if not self._require_auth():
                return
            self._handle_voice_agent_token()
            return
        static_map = {
            "/": ("welcome.html", "text/html; charset=utf-8"),
            "/console": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/welcome.js": ("welcome.js", "application/javascript; charset=utf-8"),
            "/welcome.css": ("welcome.css", "text/css; charset=utf-8"),
            "/console_enhance.js": ("console_enhance.js", "application/javascript; charset=utf-8"),
            "/assets/voiceops.png": ("assets/voiceops.png", "image/png"),
            "/assets/voiceops-bg.png": ("assets/voiceops-bg.png", "image/png"),
        }
        item = static_map.get(self.path)
        if item is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        filename, content_type = item
        target = self.web_root / filename
        if not target.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/api/auth/judge-login":
                payload = self._read_json()
                username = str(payload.get("username") or "")
                password = str(payload.get("password") or "")
                principal = self.auth.authenticate_judge(username, password)
                if principal is None:
                    principal = self.auth.authenticate_central_judge(username, password)
                if principal is None:
                    self._send_json({"error": "invalid_credentials"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                session = self.auth.issue_session(principal)
                data = json.dumps(
                    {"authenticated": True, "principal": principal.to_dict()},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self._set_cookie(SESSION_COOKIE, session, max_age=self.auth.session_ttl_seconds)
                self.end_headers()
                self.wfile.write(data)
                return
            if self.path == "/api/auth/logout":
                data = b'{"ok":true}'
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self._set_cookie(SESSION_COOKIE, "", max_age=0)
                self.end_headers()
                self.wfile.write(data)
                return
            if not self._require_auth():
                return
            if self.path == "/api/reset":
                state = self.store.reset()
                state["assemblyai_voice_agent_enabled"] = bool(self.server.live_voice_enabled)  # type: ignore[attr-defined]
                state["deployment"] = self.server.deployment  # type: ignore[attr-defined]
                self._send_json(state)
                return
            if self.path == "/api/intent":
                payload = self._read_json()
                state = self.store.submit_intent(str(payload.get("transcript") or DEFAULT_INTENT))
                state["assemblyai_voice_agent_enabled"] = bool(self.server.live_voice_enabled)  # type: ignore[attr-defined]
                state["deployment"] = self.server.deployment  # type: ignore[attr-defined]
                self._send_json(state)
                return
            if self.path == "/api/approve":
                payload = self._read_json()
                state = self.store.approve_pending(str(payload.get("transcript") or DEFAULT_APPROVAL))
                state["assemblyai_voice_agent_enabled"] = bool(self.server.live_voice_enabled)  # type: ignore[attr-defined]
                state["deployment"] = self.server.deployment  # type: ignore[attr-defined]
                self._send_json(state)
                return
            if self.path == "/api/tool/system-query":
                payload = self._read_json()
                self._send_json(self.store.tool_system_query(str(payload.get("query") or "")))
                return
            if self.path == "/api/tool/propose-system-action":
                payload = self._read_json()
                self._send_json(self.store.tool_propose_system_action(str(payload.get("command") or "")))
                return
            if self.path == "/api/tool/inspect-and-propose":
                payload = self._read_json()
                self._send_json(self.store.tool_inspect(str(payload.get("intent") or DEFAULT_INTENT)))
                return
            if self.path == "/api/tool/recall":
                payload = self._read_json()
                self._send_json(self.store.tool_recall(str(payload.get("query") or "latest verified VoiceOps outcomes")))
                return
            if self.path == "/api/tool/approve-pending":
                payload = self._read_json()
                self._send_json(self.store.tool_approve(str(payload.get("authorization_phrase") or "")))
                return
            if self.path == "/api/guardian/voice-command":
                if not self._bridge_authorized():
                    self._send_json({"error": "guardian voice bridge unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                payload = self._read_json()
                event = payload.get("event")
                if not isinstance(event, dict):
                    raise ValueError("event must be a Guardian NormalizedEvent object")
                self._send_json(
                    self.store.submit_guardian_voice_command(
                        event,
                        str(payload.get("transcript") or ""),
                    )
                )
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except (OSError, TimeoutError) as exc:
            self._send_json(
                {"error": f"provider unavailable: {type(exc).__name__}"},
                status=HTTPStatus.BAD_GATEWAY,
            )

    def _loopback_bridge_allowed(self) -> bool:
        server_host = str(self.server.server_address[0] or "")
        client_host = str(self.client_address[0] or "")
        return server_host in {"127.0.0.1", "::1", "localhost"} and client_host in {"127.0.0.1", "::1"}

    def _bridge_authorized(self) -> bool:
        expected = str(self.server.bridge_token or "")  # type: ignore[attr-defined]
        if expected:
            raw = self.headers.get("Authorization", "")
            prefix = "Bearer "
            return raw.startswith(prefix) and hmac.compare_digest(raw[len(prefix):].strip(), expected)
        return self._loopback_bridge_allowed()

    def _handle_voice_agent_token(self) -> None:
        if not bool(self.server.live_voice_enabled):  # type: ignore[attr-defined]
            self._send_json(
                {"error": "live AssemblyAI Voice Agent mode is disabled"},
                status=HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        api_key = os.getenv("ASSEMBLYAI_API_KEY", "")
        provider_bridge = _inneros_provider_bridge_configured()
        if not api_key and not provider_bridge:
            self._send_json(
                {"error": "AssemblyAI server credential is not configured"},
                status=HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        now = time.monotonic()
        last = float(self.server.last_token_issued_at)  # type: ignore[attr-defined]
        if now - last < VOICE_AGENT_TOKEN_RATE_LIMIT_SECONDS:
            self._send_json({"error": "voice token rate limit"}, status=HTTPStatus.TOO_MANY_REQUESTS)
            return
        token_payload = (
            mint_voice_agent_token_from_inneros_provider()
            if provider_bridge
            else mint_voice_agent_token(api_key)
        )
        self.server.last_token_issued_at = now  # type: ignore[attr-defined]
        self._send_json(token_payload)

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send_json(self, payload: Any, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


class VoiceOpsDemoServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        gateway_factory: Callable[[], VoiceGateway] | None = None,
        live_voice_enabled: bool = False,
        bridge_token: str = "",
        deployment: dict[str, Any] | None = None,
        auth_required: bool = False,
        auth: VoiceOpsAuth | None = None,
    ) -> None:
        super().__init__(server_address, VoiceOpsHandler)
        self.store = DemoSessionStore(gateway_factory=gateway_factory)
        self.live_voice_enabled = live_voice_enabled
        self.bridge_token = bridge_token
        self.deployment = deployment or _deployment_profile("synthetic")
        self.auth_required = auth_required
        self.auth = auth or VoiceOpsAuth()
        self.last_token_issued_at = 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="InnerOS VoiceOps judge demo web UI")
    parser.add_argument("--host", default=os.getenv("VOICEOPS_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", os.getenv("VOICEOPS_PORT", "8765"))),
    )
    parser.add_argument(
        "--reasoner",
        choices=("synthetic", "amd5", "localqwen"),
        default=os.getenv("VOICEOPS_REASONER", "synthetic"),
        help="Use synthetic, AMD/Qwen, or the resilient local Intel/Ollama Qwen runtime.",
    )
    parser.add_argument(
        "--enable-live-assemblyai",
        action="store_true",
        default=_env_truthy("VOICEOPS_ENABLE_LIVE_ASSEMBLYAI"),
        help="Enable short-lived browser Voice Agent tokens. Requires ASSEMBLYAI_API_KEY server-side.",
    )
    args = parser.parse_args()
    server = VoiceOpsDemoServer(
        (args.host, args.port),
        gateway_factory=build_gateway_factory(args.reasoner),
        live_voice_enabled=args.enable_live_assemblyai,
        bridge_token=os.getenv("VOICEOPS_BRIDGE_TOKEN", ""),
        deployment=_deployment_profile(args.reasoner),
        auth_required=_env_truthy("VOICEOPS_AUTH_REQUIRED"),
        auth=VoiceOpsAuth(),
    )
    print(
        f"InnerOS VoiceOps demo: http://{args.host}:{args.port} · reasoner={args.reasoner} "
        f"· live_assemblyai={args.enable_live_assemblyai}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
