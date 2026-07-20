# app/execution/compensation.py
import logging
from typing import Optional
from app.execution.models import ExecutionSession, ExecutionSessionStatus
from app.execution.interfaces import IRailwayAdapter, IEventPublisher
from app.execution.policies import StrictReversalSequencePolicy
from app.execution.errors import CompensationFailedError
from app.execution.events import (
    ReversalInitiated,
    CompensationCompleted,
    ManualInterventionRequested,
)

logger = logging.getLogger("ai-service.execution.compensation")


class CompensationOrchestrator:
    """Orchestrates backward rollbacks (compensating transactions) for failed multi-step bookings."""

    def __init__(
        self,
        reversal_policy: Optional[StrictReversalSequencePolicy] = None,
        event_publisher: Optional[IEventPublisher] = None,
    ):
        self.reversal_policy = reversal_policy or StrictReversalSequencePolicy()
        self.event_publisher = event_publisher

    async def execute_rollback(
        self, session: ExecutionSession, adapter: IRailwayAdapter
    ) -> None:
        """Executes compensation commands in reverse chronological order of step execution."""
        session.transition_to(ExecutionSessionStatus.REVERTING)
        logger.warning(
            f"Initiating execution session rollback. Session: {session.session_id}"
        )

        if self.event_publisher:
            self.event_publisher.publish(
                ReversalInitiated(
                    session_id=session.session_id,
                    trace_id=session.trace_id,
                    payload={"succeeded_steps_count": len(session.step_trackers)},
                )
            )

        # Get the sorted list of trackers that need reversal
        reversal_targets = self.reversal_policy.get_reversal_sequence(
            session.step_trackers
        )

        for tracker in reversal_targets:
            tracker.mark_compensating()
            logger.info(
                f"Reversing step {tracker.step_id} using function {tracker.plan_step.function_name}"
            )

            try:
                # Execution Engine maps whitelisted functions to cancellation capability
                if tracker.plan_step.function_name == "book_ticket":
                    pnr = tracker.compensation_reference
                    passenger_id = tracker.plan_step.input_args.get("passenger_id")

                    if pnr:
                        res = await adapter.cancel_seat(
                            pnr=pnr, passenger_id=passenger_id
                        )
                        if res.get("status") == "CANCELLED":
                            tracker.mark_reverted()
                            logger.info(
                                f"Step {tracker.step_id} successfully reverted. PNR: {pnr}"
                            )
                        else:
                            raise CompensationFailedError(
                                f"Cancellation returned status: {res.get('status')}"
                            )
                    else:
                        # If PNR is missing but step succeeded, we have a consistency warning
                        tracker.mark_reverted()
                else:
                    # Non-state modifying steps (like search) can be directly marked reverted
                    tracker.mark_reverted()

            except Exception as e:
                logger.exception(
                    f"Compensation step failed for step: {tracker.step_id}"
                )
                tracker.mark_failure(f"Rollback failed: {str(e)}")

                # Halt rollback and request manual intervention
                session.transition_to(ExecutionSessionStatus.ABORTED)
                if self.event_publisher:
                    self.event_publisher.publish(
                        ManualInterventionRequested(
                            session_id=session.session_id,
                            trace_id=session.trace_id,
                            payload={
                                "failed_step_id": tracker.step_id,
                                "error": str(e),
                            },
                        )
                    )
                raise CompensationFailedError(
                    f"Compensation saga halted due to step reversal failure: {str(e)}"
                ) from e

        # If all compensations succeeded
        session.transition_to(ExecutionSessionStatus.REVERTED)
        if self.event_publisher:
            self.event_publisher.publish(
                CompensationCompleted(
                    session_id=session.session_id,
                    trace_id=session.trace_id,
                    payload={"reverted_steps_count": len(reversal_targets)},
                )
            )
        logger.info(
            f"Rollback completed successfully for session: {session.session_id}"
        )
