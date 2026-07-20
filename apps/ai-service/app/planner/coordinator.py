# app/planner/coordinator.py
import logging
from typing import Optional, Dict, Any
from app.orchestrator.types import IntentDescriptor
from app.planner.models import StructuredTravelPlan, PlanStatus
from app.planner.factory import StructuredTravelPlanFactory
from app.planner.sequencer import StepSequencer
from app.planner.validator import PlanValidator
from app.planner.clarification import ClarificationHandler
from app.planner.events import PlanFormulated, PlanVerified, PlanConflictDetected
from app.planner.errors import PlanningError
from app.planner.interfaces import IPlanningCoordinator

logger = logging.getLogger("ai-service.planner.coordinator")


class PlanningCoordinator(IPlanningCoordinator):
    """Application service coordinating intent parsing outputs to validated StructuredTravelPlans."""

    def __init__(
        self,
        sequencer: Optional[StepSequencer] = None,
        validator: Optional[PlanValidator] = None,
        clarification_handler: Optional[ClarificationHandler] = None,
    ):
        self.sequencer = sequencer or StepSequencer()
        self.validator = validator or PlanValidator()
        self.clarification_handler = clarification_handler or ClarificationHandler()

    async def coordinate_planning(
        self, intent_descriptor: IntentDescriptor
    ) -> StructuredTravelPlan:
        """Orchestrates plan formulation, validation, policy checks, and signs plan status."""
        trace_id = intent_descriptor.metadata.get("trace_id") or "sys_trace"
        logger.info(f"Initiating travel planning orchestration. Trace ID: {trace_id}")

        # 1. Ambiguity Recovery: Check if intent descriptor requires clarification
        if intent_descriptor.needs_clarification:
            logger.warning(
                f"Intent descriptor requires clarification. Redirecting to ClarificationHandler. Trace: {trace_id}"
            )
            return self.clarification_handler.handle_clarification(intent_descriptor)

        try:
            # 2. Plan Formulation: Step sequencing
            steps = self.sequencer.sequence_steps(intent_descriptor)

            # Extract user_id and authorization flags from intent context for metadata mapping
            metadata: Dict[str, Any] = {
                "user_id": intent_descriptor.context.get("user_id"),
                "is_authorized_proxy": intent_descriptor.context.get(
                    "is_authorized_proxy", False
                ),
            }

            # 3. Create the travel plan aggregate via factory
            plan = StructuredTravelPlanFactory.create_plan(
                trace_id=trace_id,
                steps=steps,
                metadata=metadata,
            )

            # Emit PlanFormulated event
            formulated_event = PlanFormulated(
                plan_id=plan.plan_id,
                trace_id=plan.trace_id,
                payload={
                    "steps_count": len(steps),
                    "intent": intent_descriptor.intent.name,
                },
            )
            logger.info(
                f"Event published: {formulated_event.event_type} for Plan: {plan.plan_id}"
            )

            # 4. Plan Verification: Evaluate specifications and domain policies
            report = self.validator.validate_plan(plan)
            plan.validation_report = report

            if report.is_valid:
                plan.status = PlanStatus.VALIDATED
                logger.info(
                    f"StructuredTravelPlan validated successfully. Plan ID: {plan.plan_id}"
                )
            else:
                plan.status = PlanStatus.REJECTED
                logger.error(
                    f"StructuredTravelPlan validation failed. Plan ID: {plan.plan_id}"
                )

            # Check for conflict events
            has_conflicts = any(
                c.category == "double_booking" for c in report.violated_constraints
            )
            if has_conflicts:
                conflict_event = PlanConflictDetected(
                    plan_id=plan.plan_id,
                    trace_id=plan.trace_id,
                    payload={
                        "violated_constraints": [
                            c.rule_id for c in report.violated_constraints
                        ]
                    },
                )
                logger.warning(
                    f"Event published: {conflict_event.event_type} for Plan: {plan.plan_id}"
                )

            # Emit PlanVerified event
            verified_event = PlanVerified(
                plan_id=plan.plan_id,
                trace_id=plan.trace_id,
                payload={
                    "is_valid": report.is_valid,
                    "violation_count": len(report.violated_constraints),
                },
            )
            logger.info(
                f"Event published: {verified_event.event_type} for Plan: {plan.plan_id}"
            )

            return plan

        except PlanningError:
            logger.exception(
                f"Planning engine exception during coordination. Trace: {trace_id}"
            )
            # Raise planning errors up to the API/workflow layer
            raise
        except Exception as e:
            logger.exception(
                f"Unexpected system error during planning coordination. Trace: {trace_id}"
            )
            raise PlanningError(f"Unexpected planning system error: {str(e)}") from e
