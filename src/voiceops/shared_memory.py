from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ALLOWED_TRUTH = {"LIVE", "REPLAY", "SYNTHETIC"}


@dataclass
class SharedMemoryBridge:
    """Optional bridge to Personal Brain/Cognee with an honest synthetic fallback."""

    mode: str = field(default_factory=lambda: os.getenv("VOICEOPS_SHARED_MEMORY_MODE", "synthetic").strip().lower())
    base_url: str = field(default_factory=lambda: os.getenv("PERSONAL_BRAIN_URL", "http://127.0.0.1:8231").rstrip("/"))
    timeout_seconds: float = 0.8
    _journal: list[dict[str, object]] = field(default_factory=list)

    def status(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "provider": "personal-brain-cognee" if self.mode == "live" else "judge-safe-memory",
            "network_required": self.mode == "live",
        }

    def recall(self, query: str, *, limit: int = 5) -> dict[str, object]:
        if self.mode == "disabled":
            return {"status": "disabled", "truth": "UNVERIFIED", "count": 0, "hits": []}
        if self.mode == "live":
            try:
                params = urlencode({"q": query[:600], "limit": max(1, min(limit, 8))})
                with urlopen(f"{self.base_url}/api/internal/shared-memory/recall?{params}", timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                return {
                    "status": "live",
                    "truth": "LIVE",
                    "provider": "personal-brain-cognee",
                    "dataset": payload.get("dataset"),
                    "count": int(payload.get("count") or 0),
                    "hits": list(payload.get("hits") or [])[:limit],
                }
            except Exception as exc:
                return {
                    "status": "unavailable",
                    "truth": "UNVERIFIED",
                    "provider": "personal-brain-cognee",
                    "count": 0,
                    "hits": [],
                    "reason": type(exc).__name__,
                }

        tokens = [token for token in query.lower().split() if len(token) > 4]
        matches = []
        for item in reversed(self._journal):
            searchable = (
                str(item.get("summary") or "")
                + " "
                + json.dumps(item.get("metadata") or {}, sort_keys=True)
            ).lower()
            if any(token in searchable for token in tokens):
                matches.append(item)
            if len(matches) >= limit:
                break
        if not matches:
            matches = [{
                "summary": "Prior judge-safe demo memory: a north-access incident required human-reviewed technical follow-up.",
                "source": "voiceops-synthetic-memory",
                "metadata": {
                    "kind": "prior_demo_outcome",
                    "source_truth": "SYNTHETIC",
                    "verification_passed": True,
                },
            }]
        return {
            "status": "synthetic",
            "truth": "SYNTHETIC",
            "provider": "judge-safe-memory",
            "dataset": "voiceops-demo-memory",
            "count": len(matches),
            "hits": matches,
        }

    def remember_verified(
        self,
        *,
        correlation_id: str,
        summary: str,
        evidence_ref: str,
        source_truth: str,
        verification_passed: bool,
    ) -> dict[str, object]:
        if not verification_passed:
            return {"status": "blocked", "truth": "UNVERIFIED", "stored": False, "reason": "verification_required"}
        truth = source_truth.strip().upper()
        if truth not in ALLOWED_TRUTH:
            return {"status": "blocked", "truth": "UNVERIFIED", "stored": False, "reason": "truth_label_invalid"}
        if self.mode == "disabled":
            return {"status": "disabled", "truth": "UNVERIFIED", "stored": False}
        payload = {
            "correlation_id": correlation_id[:160],
            "summary": summary[:600],
            "evidence_ref": evidence_ref[:300],
            "source_truth": truth,
            "verification_passed": True,
        }
        if self.mode == "live":
            try:
                request = Request(
                    f"{self.base_url}/api/internal/shared-memory/verified-outcome",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    receipt = json.loads(response.read().decode("utf-8"))
                return {
                    "status": "stored",
                    "truth": truth,
                    "provider": "personal-brain-cognee",
                    **receipt,
                }
            except Exception as exc:
                return {
                    "status": "unavailable",
                    "truth": "UNVERIFIED",
                    "provider": "personal-brain-cognee",
                    "stored": False,
                    "reason": type(exc).__name__,
                }

        item = {
            "summary": summary[:600],
            "source": "voiceops-synthetic-memory",
            "metadata": {
                "kind": "verified_demo_outcome",
                "correlation_id": correlation_id[:160],
                "evidence_ref": evidence_ref[:300],
                "source_truth": "SYNTHETIC",
                "verification_passed": True,
            },
        }
        self._journal.append(item)
        return {
            "status": "stored",
            "truth": "SYNTHETIC",
            "provider": "judge-safe-memory",
            "dataset": "voiceops-demo-memory",
            "stored": True,
            "memory_id": f"demo-{len(self._journal):04d}",
            "verification_passed": True,
        }
