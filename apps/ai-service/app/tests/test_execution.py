# app/tests/test_execution.py
import pytest
import time
from datetime import datetime, timedelta
from app.planner.models import StructuredTravelPlan, PlanStep
from app.execution.models import (
    ExecutionSessionStatus,
    StepExecutionStatus,
    RetryPolicy,
)
from app.execution.errors import (
    IdempotencyViolationError,
    InvalidStateTransitionError,
    AuthorizationFailedError,
    CompensationFailedError,
)
from app.execution.adapters import MockRailwayAdapter
from app.execution.coordinator import ExecutionCoordinator


@pytest.fixture
def mock_adapter():
    return MockRailwayAdapter()


@pytest.fixture
def plan_steps():
    from datetime import datetime, timedelta

    dep_time = (datetime.now() + timedelta(hours=6)).isoformat()
    arr_time = (datetime.now() + timedelta(hours=10)).isoformat()

    step1 = PlanStep(
        step_id="step_1",
        sequence_number=1,
        function_name="search_trains",
        input_args={"origin": "NDLS", "destination": "PUNE", "date": "2026-07-25"},
        expected_output="train_list",
    )
    step2 = PlanStep(
        step_id="step_2",
        sequence_number=2,
        function_name="check_seat_availability",
        input_args={"train_number": "12002", "date": "2026-07-25", "class": "CC"},
        expected_output="seat_status",
        prerequisites=["step_1"],
    )
    step3 = PlanStep(
        step_id="step_3",
        sequence_number=3,
        function_name="book_ticket",
        input_args={
            "train_number": "12002",
            "passenger_id": "U77",
            "date": "2026-07-25",
            "class": "CC",
            "departure_time": dep_time,
            "arrival_time": arr_time,
        },
        expected_output="booking_confirmation",
        prerequisites=["step_2"],
    )
    return [step1, step2, step3]


@pytest.fixture
def travel_plan(plan_steps):
    return StructuredTravelPlan(
        plan_id="PLAN-MOCK-1",
        trace_id="TRACE-EXEC-1",
        steps=plan_steps,
        created_at=time.time(),
        metadata={"user_id": "U77"},
    )


@pytest.fixture
def connecting_travel_plan():
    from datetime import datetime, timedelta

    dep_time1 = (datetime.now() + timedelta(hours=6)).isoformat()
    arr_time1 = (datetime.now() + timedelta(hours=8)).isoformat()
    dep_time2 = (datetime.now() + timedelta(hours=9)).isoformat()
    arr_time2 = (datetime.now() + timedelta(hours=11)).isoformat()

    step1 = PlanStep(
        step_id="step_1",
        sequence_number=1,
        function_name="book_ticket",
        input_args={
            "train_number": "12001",
            "passenger_id": "U77",
            "date": "2026-07-25",
            "class": "CC",
            "departure_time": dep_time1,
            "arrival_time": arr_time1,
        },
        expected_output="booking_confirmation_1",
    )
    step2 = PlanStep(
        step_id="step_2",
        sequence_number=2,
        function_name="book_ticket",
        input_args={
            "train_number": "12002",
            "passenger_id": "U77",
            "date": "2026-07-26",
            "class": "CC",
            "departure_time": dep_time2,
            "arrival_time": arr_time2,
        },
        expected_output="booking_confirmation_2",
        prerequisites=["step_1"],
    )
    return StructuredTravelPlan(
        plan_id="PLAN-MOCK-2",
        trace_id="TRACE-EXEC-2",
        steps=[step1, step2],
        created_at=time.time(),
        metadata={"user_id": "U77"},
    )


@pytest.mark.anyio
async def test_coordinator_happy_path(travel_plan, mock_adapter):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)
    token = "token_happy_path"

    session = await coordinator.execute_plan(travel_plan, token)

    assert session.status == ExecutionSessionStatus.COMPLETED
    assert len(session.state_history) > 0
    assert session.step_trackers[0].status == StepExecutionStatus.SUCCEEDED
    assert session.step_trackers[1].status == StepExecutionStatus.SUCCEEDED
    assert session.step_trackers[2].status == StepExecutionStatus.SUCCEEDED
    assert session.step_trackers[2].compensation_reference is not None

    # Check that events were published
    published = coordinator.event_publisher.get_published_events()
    event_types = [e.event_type for e in published]
    assert "execution_started" in event_types
    assert "step_execution_succeeded" in event_types
    assert "execution_finalized" in event_types


@pytest.mark.anyio
async def test_coordinator_idempotency_gate(travel_plan, mock_adapter):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)
    token = "token_idempotency"

    # First execution should succeed
    await coordinator.execute_plan(travel_plan, token)

    # Second execution with same token should raise IdempotencyViolationError
    with pytest.raises(IdempotencyViolationError):
        await coordinator.execute_plan(travel_plan, token)


@pytest.mark.anyio
async def test_invalid_state_transitions(travel_plan, mock_adapter):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)
    session = await coordinator.execute_plan(travel_plan, "token_state_transition")

    # Session is completed. Completed is a terminal state.
    # Transitioning to any state from Completed must raise InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError):
        session.transition_to(ExecutionSessionStatus.PROCESSING)


@pytest.mark.anyio
async def test_ready_to_execute_specification_fail(travel_plan, mock_adapter):
    # Alter travel plan metadata so that user_id is missing (violates auth check in specification)
    travel_plan.metadata = {}
    coordinator = ExecutionCoordinator(adapter=mock_adapter)

    with pytest.raises(AuthorizationFailedError):
        await coordinator.execute_plan(travel_plan, "token_auth_fail")


@pytest.mark.anyio
async def test_ready_to_execute_spec_lockout_window(travel_plan, mock_adapter):
    # Create booking step departing in 2 hours (violates 4-hour departure lockout window check)
    dep_time = (datetime.now() + timedelta(hours=2)).isoformat()
    travel_plan.steps[2].input_args["departure_time"] = dep_time

    coordinator = ExecutionCoordinator(adapter=mock_adapter)

    with pytest.raises(AuthorizationFailedError):
        await coordinator.execute_plan(travel_plan, "token_lockout_fail")


@pytest.mark.anyio
async def test_retry_policy_exhaustion(connecting_travel_plan, mock_adapter):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)

    # Configure retry policy with no delays for faster test runs
    coordinator.default_retry_policy = RetryPolicy(
        max_attempts=2, base_delay_seconds=0.0
    )

    # Set mock adapter response to fail booking seat step 2
    mock_adapter.reservation_mock_responses["U77@12002"] = "FAIL"

    session = await coordinator.execute_plan(
        connecting_travel_plan, "token_retry_exhaustion"
    )

    # The coordinator should mark step 2 failed, trigger rollback, and mark session as REVERTED
    assert session.status == ExecutionSessionStatus.REVERTED
    assert session.step_trackers[1].status == StepExecutionStatus.FAILED
    assert session.step_trackers[1].attempts_made == 2


@pytest.mark.anyio
async def test_compensation_policy_reverse_order(connecting_travel_plan, mock_adapter):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)
    coordinator.default_retry_policy = RetryPolicy(
        max_attempts=1, base_delay_seconds=0.0
    )

    # Set mock adapter to fail step 2 so compensation is triggered
    mock_adapter.reservation_mock_responses["U77@12002"] = "FAIL"

    session = await coordinator.execute_plan(
        connecting_travel_plan, "token_reverse_order"
    )

    assert session.status == ExecutionSessionStatus.REVERTED

    # Ensure step 2 failed and step 1 (which succeeded and has compensation reference) was rolled back.
    # Verify that ReversalInitiated and CompensationCompleted events were emitted.
    published = coordinator.event_publisher.get_published_events()
    event_types = [e.event_type for e in published]
    assert "reversal_initiated" in event_types
    assert "compensation_completed" in event_types


@pytest.mark.anyio
async def test_compensation_fails_trigger_operator_handoff(
    connecting_travel_plan, mock_adapter
):
    coordinator = ExecutionCoordinator(adapter=mock_adapter)
    coordinator.default_retry_policy = RetryPolicy(
        max_attempts=1, base_delay_seconds=0.0
    )

    # Inject failure into mock cancel_seat by mocking cancellation error
    async def failing_cancellation(*args, **kwargs):
        raise Exception("Mock cancel_seat partner system completely crashed!")

    mock_adapter.cancel_seat = failing_cancellation

    # Fail step 2 to trigger rollback compensation
    mock_adapter.reservation_mock_responses["U77@12002"] = "FAIL"

    # Executing plan should raise CompensationFailedError due to failed cancellation rollback
    with pytest.raises(CompensationFailedError):
        await coordinator.execute_plan(
            connecting_travel_plan, "token_compensation_fail"
        )

    session = coordinator.repository.find_by_token("token_compensation_fail")
    assert session is not None
    assert session.status == ExecutionSessionStatus.ABORTED
    published = coordinator.event_publisher.get_published_events()
    event_types = [e.event_type for e in published]
    assert "manual_intervention_requested" in event_types
