from __future__ import annotations

import argparse
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .adapters.local_amd import LocalAMDReasoner
from .audit import replay_summary
from .gateway import VoiceGateway


MAX_BODY_BYTES = 16_384
MAX_TRANSCRIPT_CHARS = 1_000
DEFAULT_INTENT = (
    "Ralphi, revisa la incidencia del acceso norte y abre una orden tecnica si corresponde."
)
DEFAULT_APPROVAL = "Si, autorizo."


class DemoSessionStore:
    """Thread-safe in-memory state for the judge-facing demo.

    The UI is a presentation adapter over VoiceGateway. It does not own Physical
    Guardian detection, real work-order persistence, or Audit Fabric primitives.
    The bundled workflow is synthetic and therefore cannot write to production.
    """

    def __init__(self, gateway_factory: Callable[[], VoiceGateway] | None = None) -> None:
        self._lock = threading.Lock()
        self._gateway_factory = gateway_factory or VoiceGateway
        self._gateway = self._gateway_factory()
        self._last_result: dict[str, object] | None = None

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._gateway = self._gateway_factory()
            self._last_result = None
            return self._snapshot_unlocked()

    def submit_transcript(self, transcript: str) -> dict[str, Any]:
        normalized = transcript.strip()
        if not normalized:
            raise ValueError("transcript must not be empty")
        if len(normalized) > MAX_TRANSCRIPT_CHARS:
            raise ValueError(f"transcript exceeds {MAX_TRANSCRIPT_CHARS} characters")
        with self._lock:
            self._last_result = self._gateway.process_final_transcript(normalized)
            return self._snapshot_unlocked()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_unlocked()

    def evidence(self) -> dict[str, Any]:
        with self._lock:
            return self._gateway.evidence.to_dict()

    def replay(self) -> dict[str, Any]:
        with self._lock:
            return replay_summary(self._gateway.evidence)

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

        return {
            "mode": "synthetic_demo",
            "reasoning_mode": _reasoning_mode(route),
            "production_writes": False,
            "session_id": evidence.session_id,
            "correlation_id": evidence.correlation_id,
            "pending_approval": self._gateway.pending_approval,
            "last_result": self._last_result,
            "transcript": evidence.turns[-1].transcript if evidence.turns else None,
            "guardian": guardian,
            "route": route,
            "proposal": {
                "action_type": proposal.action_type,
                "summary": proposal.summary,
                "requires_approval": proposal.requires_approval,
                "payload": proposal.payload,
            }
            if proposal
            else None,
            "approval": {
                "approved": approval.approved,
                "reason": approval.reason,
            }
            if approval
            else None,
            "action": {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "status": action.status,
                "details": action.details,
            }
            if action
            else None,
            "htr": {
                "manual_seconds": htr.manual_seconds,
                "human_active_seconds": htr.human_active_seconds,
                "saved_seconds": htr.saved_seconds,
                "classification": htr.classification,
            }
            if htr
            else None,
            "timeline": [
                {"kind": event.kind, "at": event.at, "data": event.data}
                for event in evidence.events
            ],
        }


def _reasoning_mode(route: dict[str, Any]) -> str:
    if route.get("provider") == "local-amd-5" and route.get("truth") == "LIVE_MODEL_RESPONSE":
        return "amd5_live"
    if route.get("truth") == "SYNTHETIC":
        return "synthetic"
    return "pending"


def build_gateway_factory(reasoner_mode: str) -> Callable[[], VoiceGateway]:
    if reasoner_mode == "synthetic":
        return VoiceGateway
    if reasoner_mode == "amd5":
        return lambda: VoiceGateway(reasoner=LocalAMDReasoner())
    raise ValueError(f"unsupported reasoner mode: {reasoner_mode}")


class VoiceOpsHandler(BaseHTTPRequestHandler):
    server_version = "VoiceOpsDemo/0.2"

    @property
    def store(self) -> DemoSessionStore:
        return self.server.store  # type: ignore[attr-defined]

    @property
    def web_root(self) -> Path:
        return Path(__file__).with_name("web")

    def log_message(self, format: str, *args: object) -> None:
        # Avoid accidental transcript leakage through default HTTP request logs.
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            self._send_json(self.store.snapshot())
            return
        if self.path == "/api/evidence":
            self._send_json(self.store.evidence())
            return
        if self.path == "/api/replay":
            self._send_json(self.store.replay())
            return
        static_map = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
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
            if self.path == "/api/reset":
                self._send_json(self.store.reset())
                return
            if self.path in {"/api/intent", "/api/approve"}:
                payload = self._read_json()
                default = DEFAULT_INTENT if self.path == "/api/intent" else DEFAULT_APPROVAL
                transcript = str(payload.get("transcript") or default)
                self._send_json(self.store.submit_transcript(transcript))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except (OSError, TimeoutError) as exc:
            self._send_json(
                {"error": f"reasoning provider unavailable: {type(exc).__name__}"},
                status=HTTPStatus.BAD_GATEWAY,
            )

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
    ) -> None:
        super().__init__(server_address, VoiceOpsHandler)
        self.store = DemoSessionStore(gateway_factory=gateway_factory)


def main() -> None:
    parser = argparse.ArgumentParser(description="InnerOS VoiceOps judge demo web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--reasoner",
        choices=("synthetic", "amd5"),
        default="synthetic",
        help="Use offline-safe synthetic reasoning or the existing local AMD .5 runtime.",
    )
    args = parser.parse_args()
    server = VoiceOpsDemoServer(
        (args.host, args.port),
        gateway_factory=build_gateway_factory(args.reasoner),
    )
    print(f"InnerOS VoiceOps demo: http://{args.host}:{args.port} · reasoner={args.reasoner}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
