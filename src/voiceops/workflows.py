from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import ActionProposal, ActionResult, ApprovalDecision


@dataclass(slots=True)
class SyntheticGuardianIncident:
    """Synthetic projection of a Physical Guardian normalized event.

    This is demo data only. VoiceOps does not inspect camera streams, infer
    anomalies, or decide that an offline camera constitutes an incident.
    Production input must arrive from the canonical Physical Guardian capability.
    """

    event_id: str = field(default_factory=lambda: f"evt-demo-{uuid4().hex[:10]}")
    source_id: str = "camera-north-01"
    event_type: str = "camera_offline"
    severity: str = "high"
    zone_id: str = "north-access"
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_refs: tuple[str, ...] = ("synthetic://guardian/camera-north-01/offline",)

    def as_voiceops_context(self) -> dict[str, Any]:
        """Return a downstream view of Guardian output plus its action candidate."""
        return {
            "contract_owner": "Rafa-Innerchispa/inneros-physical-guardian",
            "contract_projection": "NormalizedEvent",
            "event_id": self.event_id,
            "source_id": self.source_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "zone_id": self.zone_id,
            "occurred_at": self.occurred_at,
            "evidence_refs": list(self.evidence_refs),
            "source": "synthetic_guardian_adapter",
            "action_candidate": {
                "action_type": "create_work_order",
                "summary": (
                    f"Physical Guardian reported {self.event_type} for {self.source_id} "
                    f"in {self.zone_id}. Create a priority technical work order for inspection."
                ),
                "requires_approval": True,
                "payload": {
                    "source_event_id": self.event_id,
                    "source_id": self.source_id,
                    "zone_id": self.zone_id,
                    "priority": "high",
                    "reason_code": "GUARDIAN_CAMERA_OFFLINE",
                    "evidence_refs": list(self.evidence_refs),
                },
            },
        }


class SyntheticServiceWorkflow:
    """Demo-safe VoiceOps integration over downstream Guardian/Service Ops ports.

    It deliberately does not contain physical anomaly interpretation. The
    synthetic Guardian fixture emits a normalized incident and action candidate;
    VoiceOps only governs approval/orchestration and executes a synthetic Service
    Operations action.
    """

    def __init__(self, incident: SyntheticGuardianIncident | None = None) -> None:
        self.incident = incident or SyntheticGuardianIncident()
        self.created_orders: list[dict[str, Any]] = []

    def inspect(self) -> dict[str, Any]:
        return self.incident.as_voiceops_context()

    def propose(self, facts: dict[str, Any]) -> ActionProposal:
        candidate = facts.get("action_candidate")
        if not isinstance(candidate, dict):
            return ActionProposal(
                action_type="no_action",
                summary="Physical Guardian supplied no consequential action candidate.",
                requires_approval=False,
                payload={
                    "source_event_id": facts.get("event_id"),
                    "reason_code": "NO_GUARDIAN_ACTION_CANDIDATE",
                },
            )

        required = {"action_type", "summary", "requires_approval", "payload"}
        missing = required.difference(candidate)
        if missing:
            raise ValueError(f"Guardian action candidate missing fields: {sorted(missing)}")

        return ActionProposal(
            action_type=str(candidate["action_type"]),
            summary=str(candidate["summary"]),
            requires_approval=bool(candidate["requires_approval"]),
            payload=dict(candidate["payload"]),
        )

    def execute(self, proposal: ActionProposal, approval: ApprovalDecision | None) -> ActionResult:
        if proposal.requires_approval and (approval is None or not approval.approved):
            raise PermissionError("consequential action blocked: explicit approval required")

        if proposal.action_type == "no_action":
            return ActionResult(
                action_id=f"noop-{uuid4().hex[:10]}",
                action_type="no_action",
                status="created",
                details={"executed": False, "source": "synthetic_service_ops_adapter"},
            )

        order_id = f"WO-DEMO-{uuid4().hex[:8].upper()}"
        order = {
            "work_order_id": order_id,
            **proposal.payload,
            "environment": "synthetic_demo",
            "contract_owner": "InnerOps Service Operations",
        }
        self.created_orders.append(order)
        return ActionResult(
            action_id=order_id,
            action_type=proposal.action_type,
            status="created",
            details=order,
        )
