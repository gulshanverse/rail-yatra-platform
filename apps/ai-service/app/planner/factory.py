# app/planner/factory.py
import time
import uuid
from typing import List, Dict, Any, Optional
from app.planner.models import StructuredTravelPlan, PlanStep, PlanStatus


class StructuredTravelPlanFactory:
    """Factory to instantiate new StructuredTravelPlan aggregate roots and enforce invariants."""

    @staticmethod
    def create_plan(
        trace_id: str,
        steps: List[PlanStep],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StructuredTravelPlan:
        """Assembles a new StructuredTravelPlan with trace correlation, UUID, and draft status."""
        plan_id = str(uuid.uuid4())
        created_at = time.time()

        # Enforce step count invariant before construction
        if not steps:
            raise ValueError(
                "Cannot factory create StructuredTravelPlan with an empty list of steps."
            )

        return StructuredTravelPlan(
            plan_id=plan_id,
            trace_id=trace_id,
            status=PlanStatus.DRAFT,
            steps=steps,
            validation_report=None,
            created_at=created_at,
            metadata=metadata or {},
        )
