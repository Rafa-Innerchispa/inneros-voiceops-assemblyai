from __future__ import annotations

import re
import unicodedata

from .models import ApprovalDecision


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower().strip())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9 ]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


class ExplicitApprovalGate:
    """Conservative voice approval parser. Ambiguity fails closed."""

    _exact_approvals = {
        "yes",
        "yes proceed",
        "yes authorize",
        "yes authorize it",
        "authorize",
        "authorize it",
        "approve",
        "approve it",
        "approved",
        "proceed",
        "go ahead",
        "si",
        "si autorizo",
        "si autoriza",
        "si procede",
        "autorizar",
        "autoriza",
        "autorizo",
        "autorizado",
        "aprobar",
        "aprueba",
        "apruebo",
        "adelante",
        "adelante autorizado",
    }
    _approval_verbs = {"authorize", "approve", "autorizar", "autoriza", "autorizo", "autorizado", "aprobar", "aprueba", "apruebo"}
    _negations = {"no", "not", "dont", "do not", "cancel", "stop", "cancela", "deten"}

    def decide(self, phrase: str) -> ApprovalDecision:
        clean = _normalize(phrase)
        if not clean:
            return ApprovalDecision(False, phrase, "empty_or_missing_approval")

        tokens = set(clean.split())
        if tokens.intersection({"no", "not", "dont", "cancel", "stop", "cancela", "deten"}):
            return ApprovalDecision(False, phrase, "explicit_denial_or_negation")

        if clean in self._exact_approvals:
            return ApprovalDecision(True, phrase, "explicit_approval_phrase")

        if tokens.intersection(self._approval_verbs):
            return ApprovalDecision(True, phrase, "explicit_approval_verb")

        return ApprovalDecision(False, phrase, "ambiguous_phrase_fail_closed")
