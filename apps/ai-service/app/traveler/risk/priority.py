# app/traveler/risk/priority.py
from typing import Any
from app.traveler.interfaces.contracts import (
    IPriorityEngine,
    ISuppressionEngine,
    IEscalationEngine,
)


class PriorityEngine(IPriorityEngine):
    def resolve_priority(self, context: Any) -> Any:
        return "HIGH"


class SuppressionEngine(ISuppressionEngine):
    def apply_suppression(self, context: Any) -> bool:
        # Suppress alerts if passenger is in overnight sleeping hours
        is_sleeping_hours = context.telemetry.get("is_sleeping_hours", False)
        return is_sleeping_hours


class EscalationEngine(IEscalationEngine):
    def check_escalation(self, context: Any) -> bool:
        return False
