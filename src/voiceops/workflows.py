from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .models import ActionProposal, ActionResult, ApprovalDecision


@dataclass(slots=True)
class SyntheticAlarmState:
    site: str = "demo-building"
    zone: str = "north-access"
    device: str = "camera-north-01"
    status: str = "offline"
    severity: str = "high"
    last_seen_seconds_ago: int = 184


class SyntheticServiceWorkflow:
    """Demo-safe Service Operations workflow with no production writes."""

    def __init__(self, state: SyntheticAlarmState | None = None) -> None:
        self.state = state or SyntheticAlarmState()
        self.created_orders: list[dict[str, Any]] = []

    def inspect(self) -> dict[str, Any]:
        return {
            "site": self.state.site,
            "zone": self.state.zone,
            "device": self.state.device,
            "status": self.state.status,
            "severity": self.state.severity,
            "last_seen_seconds_ago": self.state.last_seen_seconds_ago,
            "source": "synthetic_fixture",
        }

    def propose(self, facts: dict[str, Any]) -> ActionProposal:
        if facts.get("status") == "offline":
            return ActionProposal(
                action_type="create_work_order",
                summary=(
                    f"{facts['device']} is offline in {facts['zone']}. "
                    "Create a priority technical work order for inspection."
                ),
                requires_approval=True,
                payload={
                    "site": facts["site"],
                    "zone": facts["zone"],
                    "device": facts["device"],
                    "priority": "high",
                    "reason_code": "DEVICE_OFFLINE",
                },
            )

        return ActionProposal(
            action_type="no_action",
            summary="No consequential action is required for the current synthetic state.",
            requires_approval=False,
            payload={"site": facts.get("site"), "reason_code": "NO_ACTION_REQUIRED"},
        )

    def execute(self, proposal: ActionProposal, approval: ApprovalDecision | None) -> ActionResult:
        if proposal.requires_approval and (approval is None or not approval.approved):
            raise PermissionError("consequential action blocked: explicit approval required")

        if proposal.action_type == "no_action":
            return ActionResult(
                action_id=f"noop-{uuid4().hex[:10]}",
                action_type="no_action",
                status="created",
                details={"executed": False, "source": "synthetic_fixture"},
            )

        order_id = f"WO-DEMO-{uuid4().hex[:8].upper()}"
        order = {
            "work_order_id": order_id,
            **proposal.payload,
            "environment": "synthetic_demo",
        }
        self.created_orders.append(order)
        return ActionResult(
            action_id=order_id,
            action_type=proposal.action_type,
            status="created",
            details=order,
        )
