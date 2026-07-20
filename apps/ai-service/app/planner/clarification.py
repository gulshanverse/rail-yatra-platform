# app/planner/clarification.py
from app.orchestrator.types import IntentDescriptor
from app.planner.models import (
    StructuredTravelPlan,
    PlanStep,
    PlanStepStatus,
    PlanStatus,
)
from app.planner.factory import StructuredTravelPlanFactory
from app.planner.interfaces import IClarificationHandler


class ClarificationHandler(IClarificationHandler):
    """Application service to handle missing slot recoveries by creating clarification plan prompts."""

    def handle_clarification(
        self, intent_descriptor: IntentDescriptor
    ) -> StructuredTravelPlan:
        # Determine which slots are missing/low-confidence from validation errors or slots evaluation
        validation_errors = intent_descriptor.context.get("validation_errors", [])

        missing_slots = []
        for err in validation_errors:
            if err.startswith("Missing required slot: "):
                missing_slots.append(err.replace("Missing required slot: ", ""))
            elif err.startswith("Low slot confidence: "):
                missing_slots.append(err.replace("Low slot confidence: ", ""))

        # Fallback if no specific errors are parsed, check intent required slots mapping
        if not missing_slots:
            intent_name = intent_descriptor.intent.name.lower()
            required_map = {
                "plan_travel": ["origin", "destination"],
                "check_pnr": ["pnr"],
                "journey_intelligence": ["train_number"],
            }
            if intent_name in required_map:
                for req in required_map[intent_name]:
                    if req not in intent_descriptor.slots:
                        missing_slots.append(req)

        # Assemble request_clarification plan step
        clarification_step = PlanStep(
            step_id="clarify_step_1",
            sequence_number=1,
            function_name="request_clarification",
            input_args={"missing_slots": missing_slots},
            expected_output="user_response",
            status=PlanStepStatus.PENDING,
        )

        plan = StructuredTravelPlanFactory.create_plan(
            trace_id=intent_descriptor.metadata.get("trace_id") or "sys_trace",
            steps=[clarification_step],
            metadata={
                "user_id": intent_descriptor.context.get("user_id"),
                "original_intent": intent_descriptor.intent.name,
            },
        )
        plan.status = PlanStatus.NEEDS_CLARIFICATION
        return plan
