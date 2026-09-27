from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.request import Request, urlopen

from voiceops.models import ActionProposal
from voiceops.reasoning import ReasoningResult


DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen2.5-coder:7b"


class LocalQwenReasoner:
    """Bounded local Ollama/Qwen reasoner for the sovereign VoiceOps runtime."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
        post_json: Callable[[str, dict[str, Any], float], dict[str, Any]] | None = None,
    ) -> None:
        self.endpoint = endpoint or os.getenv("VOICEOPS_LOCAL_QWEN_URL", DEFAULT_ENDPOINT)
        self.model = model or os.getenv("VOICEOPS_LOCAL_QWEN_MODEL", DEFAULT_MODEL)
        self.timeout_seconds = timeout_seconds
        self._post_json = post_json or _post_json

    def propose(self, facts: dict[str, Any]) -> ReasoningResult:
        candidate = facts.get("action_candidate")
        if not isinstance(candidate, dict):
            return ReasoningResult(
                proposal=ActionProposal(
                    action_type="no_action",
                    summary="No consequential action candidate was supplied.",
                    requires_approval=False,
                    payload={
                        "source_event_id": facts.get("event_id"),
                        "reason_code": "NO_ACTION_CANDIDATE",
                    },
                ),
                route={
                    "policy": "local_first",
                    "provider": "local-intel-4",
                    "model": self.model,
                    "external_fallback": False,
                    "truth": "LIVE_NO_MODEL_CALL",
                },
            )

        required = {"action_type", "summary", "requires_approval", "payload"}
        missing = required.difference(candidate)
        if missing:
            raise ValueError(f"action candidate missing fields: {sorted(missing)}")

        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 180},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the local InnerOS reasoning layer. Return ONLY JSON "
                        "with one key named summary. Do not change the action, target, "
                        "approval policy, or payload. Keep the summary under 220 characters."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "event": {
                                "event_id": facts.get("event_id"),
                                "event_type": facts.get("event_type"),
                                "severity": facts.get("severity"),
                                "source_id": facts.get("source_id"),
                                "zone_id": facts.get("zone_id"),
                            },
                            "action_candidate": candidate,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        response = self._post_json(self.endpoint, payload, self.timeout_seconds)
        content = _extract_content(response)
        summary = _extract_summary(content) or str(candidate["summary"])

        return ReasoningResult(
            proposal=ActionProposal(
                action_type=str(candidate["action_type"]),
                summary=summary,
                requires_approval=bool(candidate["requires_approval"]),
                payload=dict(candidate["payload"]),
            ),
            route={
                "policy": "local_first",
                "provider": "local-intel-4",
                "model": self.model,
                "external_fallback": False,
                "truth": "LIVE_MODEL_RESPONSE",
            },
        )


def _post_json(endpoint: str, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise ValueError("local Qwen response must be a JSON object")
    return body


def _extract_content(response: dict[str, Any]) -> str:
    message = response.get("message")
    if not isinstance(message, dict):
        raise ValueError("local Qwen response missing message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("local Qwen response content must be non-empty")
    return content.strip()


def _extract_summary(content: str) -> str | None:
    cleaned = content.strip()
    if cleaned.startswith("~~~"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("~~~"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "~~~":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    summary = payload.get("summary")
    if not isinstance(summary, str):
        return None
    normalized = " ".join(summary.split())
    return normalized[:220] if normalized else None
