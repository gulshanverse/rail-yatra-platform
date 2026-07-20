# app/execution/coordinator.py
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any
from app.planner.models import StructuredTravelPlan
from app.execution.models import (
    ExecutionSession,
    ExecutionSessionStatus,
    ExecutionStepTracker,
    StepExecutionStatus,
    ExecutionToken,
    RetryPolicy,
)
from app.execution.interfaces import (
    IExecutionSessionRepository,
    IRailwayAdapter,
    IEventPublisher,
)
from app.execution.errors import (
    ExecutionError,
    IdempotencyViolationError,
    StepExecutionFailedError,
    AuthorizationFailedError,
)
from app.execution.specifications import (
    ReadyToExecuteSpecification,
    CompensationRequiredSpecification,
)
from app.execution.policies import ControlledRetryPolicy
from app.execution.compensation import CompensationOrchestrator
from app.execution.events import (
    ExecutionStarted,
    StepExecutionSucceeded,
    StepExecutionFailed,
    ExecutionRecovered,
    ExecutionAborted,
    ExecutionFinalized,
)

logger = logging.getLogger("ai-service.execution.coordinator")


class InMemoryExecutionSessionRepository(IExecutionSessionRepository):
    """InMemory stateful store for ExecutionSession aggregates."""

    def __init__(self):
        self._sessions: Dict[str, ExecutionSession] = {}
        self._tokens: Dict[str, ExecutionSession] = {}

    def save(self, session: ExecutionSession) -> None:
        self._sessions[session.session_id] = session
        self._tokens[session.execution_token.token_value] = session

    def find_by_id(self, session_id: str) -> Optional[ExecutionSession]:
        return self._sessions.get(session_id)

    def find_by_token(self, token: str) -> Optional[ExecutionSession]:
        return self._tokens.get(token)


class InMemoryEventPublisher(IEventPublisher):
    """InMemory stateful event dispatcher for integration tests and auditable events."""

    def __init__(self):
        self.published_events: List[Any] = []

    def publish(self, event: Any) -> None:
        self.published_events.append(event)
        logger.info(
            f"Published event: {event.event_type} for session: {event.session_id}"
        )

    def get_published_events(self) -> List[Any]:
        return self.published_events


class ExecutionCoordinator:
    """Application service Saga Orchestrator executing validated StructuredTravelPlans."""

    def __init__(
        self,
        repository: Optional[IExecutionSessionRepository] = None,
        adapter: Optional[IRailwayAdapter] = None,
        event_publisher: Optional[IEventPublisher] = None,
        retry_policy: Optional[ControlledRetryPolicy] = None,
        compensation_orchestrator: Optional[CompensationOrchestrator] = None,
    ):
        self.repository = repository or InMemoryExecutionSessionRepository()
        self.adapter = adapter
        self.event_publisher = event_publisher or InMemoryEventPublisher()
        self.retry_policy = retry_policy or ControlledRetryPolicy()
        self.compensation_orchestrator = (
            compensation_orchestrator
            or CompensationOrchestrator(event_publisher=self.event_publisher)
        )
        self.ready_spec = ReadyToExecuteSpecification()
        self.compensation_spec = CompensationRequiredSpecification()
        self.default_retry_policy = RetryPolicy()

    async def execute_plan(
        self, plan: StructuredTravelPlan, token_value: str
    ) -> ExecutionSession:
        """Orchestrates plan step dispatch, retries, failure mapping, and compensations."""
        # 1. Idempotency Gate
        existing_session = self.repository.find_by_token(token_value)
        if existing_session:
            logger.error(f"Duplicate execution token detected: {token_value}")
            raise IdempotencyViolationError(
                f"Duplicate execution token: {token_value} already processed."
            )

        # 2. Construct Execution Session Aggregate
        session_id = f"SES-{uuid.uuid4().hex[:10].upper()}"
        token = ExecutionToken(token_value=token_value)

        # Instantiate ExecutionStepTracker entity for each step in the plan
        step_trackers = []
        for step in plan.steps:
            step_trackers.append(
                ExecutionStepTracker(
                    step_id=step.step_id,
                    plan_step=step,
                    status=StepExecutionStatus.PENDING,
                )
            )

        session = ExecutionSession(
            session_id=session_id,
            plan_id=plan.plan_id,
            trace_id=plan.trace_id,
            execution_token=token,
            step_trackers=step_trackers,
            user_id=plan.metadata.get("user_id"),
        )
        session.metadata = plan.metadata

        self.repository.save(session)

        # 3. Ready Spec Checks
        if not self.ready_spec.is_satisfied_by(session):
            session.transition_to(ExecutionSessionStatus.ABORTED)
            self.repository.save(session)
            self.event_publisher.publish(
                ExecutionAborted(
                    session_id=session.session_id,
                    trace_id=session.trace_id,
                    payload={
                        "reason": "ReadyToExecuteSpecification checked unsatisfied."
                    },
                )
            )
            raise AuthorizationFailedError(
                "Authorization failed or safe execution window check violated."
            )

        # Transition to Processing
        session.transition_to(ExecutionSessionStatus.PROCESSING)
        self.repository.save(session)
        self.event_publisher.publish(
            ExecutionStarted(
                session_id=session.session_id,
                trace_id=session.trace_id,
                payload={"total_steps": len(plan.steps)},
            )
        )

        try:
            # 4. Saga Execution loop
            while session.status == ExecutionSessionStatus.PROCESSING:
                runnable_trackers = self._get_runnable_steps(session)
                if not runnable_trackers:
                    # All steps successfully executed
                    session.transition_to(ExecutionSessionStatus.COMPLETED)
                    self.event_publisher.publish(
                        ExecutionFinalized(
                            session_id=session.session_id,
                            trace_id=session.trace_id,
                            payload={"status": "COMPLETED"},
                        )
                    )
                    self.repository.save(session)
                    return session

                # Process current runnable steps
                for tracker in runnable_trackers:
                    await self._dispatch_step_with_retries(session, tracker)

            self.repository.save(session)
            return session

        except StepExecutionFailedError as sefe:
            logger.error(
                f"Step execution failure encountered. Processing rollback. Error: {str(sefe)}"
            )
            # Evaluate Compensation Specification
            if self.compensation_spec.is_satisfied_by(session):
                # Trigger Sagad Rollback
                await self.compensation_orchestrator.execute_rollback(
                    session, self.adapter
                )
            else:
                session.transition_to(ExecutionSessionStatus.FAILED)
                self.event_publisher.publish(
                    ExecutionFinalized(
                        session_id=session.session_id,
                        trace_id=session.trace_id,
                        payload={"status": "FAILED", "reason": str(sefe)},
                    )
                )
            self.repository.save(session)
            return session

        except Exception as e:
            logger.exception("Unexpected exception inside coordinator saga loop.")
            session.transition_to(ExecutionSessionStatus.ABORTED)
            self.repository.save(session)
            self.event_publisher.publish(
                ExecutionAborted(
                    session_id=session.session_id,
                    trace_id=session.trace_id,
                    payload={"error": str(e)},
                )
            )
            raise ExecutionError(
                f"Execution saga aborted due to unexpected coordinator failure: {str(e)}"
            ) from e

    def _get_runnable_steps(
        self, session: ExecutionSession
    ) -> List[ExecutionStepTracker]:
        """Returns pending trackers whose prerequisite step IDs have all completed successfully."""
        runnable = []
        succeeded_step_ids = {
            t.step_id
            for t in session.step_trackers
            if t.status == StepExecutionStatus.SUCCEEDED
        }

        for tracker in session.step_trackers:
            if tracker.status == StepExecutionStatus.PENDING:
                prereqs_met = True
                for prereq_id in tracker.plan_step.prerequisites:
                    if prereq_id not in succeeded_step_ids:
                        prereqs_met = False
                        break
                if prereqs_met:
                    runnable.append(tracker)
        return runnable

    async def _dispatch_step_with_retries(
        self, session: ExecutionSession, tracker: ExecutionStepTracker
    ) -> None:
        """Executes a single step tracker, attempting Controlled Retry policies on transient failures."""
        tracker.status = StepExecutionStatus.DISPATCHING
        self.repository.save(session)

        # Retrieve step retry settings or fall back to default
        policy = self.default_retry_policy

        while True:
            tracker.record_attempt()
            self.repository.save(session)
            logger.info(
                f"Dispatching step {tracker.step_id} (Attempt {tracker.attempts_made})"
            )

            try:
                out = await self._call_adapter(tracker.plan_step)

                # Verify mock or real adapter outcome status
                if out.get("status") in ["FAILED", "FAIL"]:
                    raise StepExecutionFailedError(
                        out.get("error", "Adapter transaction reported failure.")
                    )

                tracker.mark_success(out)
                self.repository.save(session)

                self.event_publisher.publish(
                    StepExecutionSucceeded(
                        session_id=session.session_id,
                        trace_id=session.trace_id,
                        payload={
                            "step_id": tracker.step_id,
                            "function_name": tracker.plan_step.function_name,
                        },
                    )
                )

                if tracker.attempts_made > 1:
                    self.event_publisher.publish(
                        ExecutionRecovered(
                            session_id=session.session_id,
                            trace_id=session.trace_id,
                            payload={
                                "step_id": tracker.step_id,
                                "attempts": tracker.attempts_made,
                            },
                        )
                    )
                return

            except Exception as e:
                logger.warning(
                    f"Attempt {tracker.attempts_made} failed for step {tracker.step_id}. Error: {str(e)}"
                )
                tracker.mark_failure(str(e))
                self.repository.save(session)

                # Check if retry policy permits retrying
                if self.retry_policy.should_retry(tracker, policy):
                    tracker.status = StepExecutionStatus.RETRYING
                    self.repository.save(session)
                    delay = self.retry_policy.calculate_delay(tracker, policy)
                    logger.info(
                        f"Sleeping for {delay:.2f}s before retry attempt {tracker.attempts_made + 1}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Retry threshold exceeded
                    self.event_publisher.publish(
                        StepExecutionFailed(
                            session_id=session.session_id,
                            trace_id=session.trace_id,
                            payload={
                                "step_id": tracker.step_id,
                                "attempts_made": tracker.attempts_made,
                                "error": str(e),
                            },
                        )
                    )
                    raise StepExecutionFailedError(
                        f"Step {tracker.step_id} failed after {tracker.attempts_made} attempts."
                    )

    async def _call_adapter(self, step) -> Dict[str, Any]:
        """Bridges generic PlanStep names to specific Adapter interfaces."""
        if not self.adapter:
            raise ExecutionError("Railway adapter not configured on coordinator.")

        func = step.function_name
        args = step.input_args

        if func == "search_trains" or func == "check_seat_availability":
            return await self.adapter.verify_availability(
                train_number=args.get("train_number", "UNKNOWN"),
                travel_date=args.get("date", "UNKNOWN"),
                class_code=args.get("class", "SL"),
            )
        elif func == "book_ticket":
            # Check concession and passenger age from slots
            return await self.adapter.reserve_seat(
                passenger_id=args.get("passenger_id", "UNKNOWN"),
                train_number=args.get("train_number", "UNKNOWN"),
                class_code=args.get("class", "SL"),
                concession_tier=args.get("concession"),
                passenger_age=args.get("passenger_age"),
            )
        elif func == "cancel_ticket":
            return await self.adapter.cancel_seat(
                pnr=args.get("pnr", "UNKNOWN"),
                passenger_id=args.get("passenger_id"),
            )
        else:
            # Fallback mock for non-ticketing checks
            return {"status": "SUCCESS", "message": f"Evaluated helper step: {func}"}
