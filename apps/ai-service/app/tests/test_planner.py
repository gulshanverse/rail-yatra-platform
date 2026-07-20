# app/tests/test_planner.py
import pytest
import time
from datetime import datetime, timedelta
from app.orchestrator.types import IntentDescriptor, IntentCandidate, Slot
from app.planner import (
    StructuredTravelPlan,
    PlanStep,
    PlanStatus,
    SequencingError,
    function_registry,
    StructuredTravelPlanFactory,
    StepSequencer,
    PlanValidator,
    ClarificationHandler,
    PlanningCoordinator,
)


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def base_intent_descriptor():
    candidate = IntentCandidate(
        name="plan_travel", confidence=0.95, reason="User wants to travel"
    )
    slots = {
        "origin": Slot(
            name="origin", value="NDLS", type="StationCode", confidence=0.98
        ),
        "destination": Slot(
            name="destination", value="HWH", type="StationCode", confidence=0.98
        ),
        "date": Slot(name="date", value="2026-07-25", type="Date", confidence=0.98),
        "train_number": Slot(
            name="train_number", value="12302", type="TrainNumber", confidence=0.98
        ),
        "class": Slot(name="class", value="3A", type="ClassCode", confidence=0.98),
        "passenger_id": Slot(
            name="passenger_id", value="P123", type="PassengerID", confidence=0.98
        ),
        "passenger_age": Slot(
            name="passenger_age", value=65, type="Age", confidence=0.98
        ),
        "concession": Slot(
            name="concession", value="senior", type="Concession", confidence=0.98
        ),
    }
    context = {"user_id": "P123", "is_authorized_proxy": False}
    metadata = {"trace_id": "test_trace_123"}
    return IntentDescriptor(
        intent=candidate,
        slots=slots,
        context=context,
        metadata=metadata,
        needs_clarification=False,
    )


# ==========================================
# 1. Model Invariants Tests
# ==========================================
def test_model_invariants_empty_steps():
    with pytest.raises(ValueError, match="must contain at least one step"):
        StructuredTravelPlan(
            plan_id="plan_1",
            trace_id="trace_1",
            status=PlanStatus.DRAFT,
            steps=[],
            created_at=time.time(),
        )


def test_model_invariants_ascending_sequence():
    step1 = PlanStep(
        step_id="s1",
        sequence_number=2,
        function_name="search_trains",
        expected_output="ok",
    )
    step2 = PlanStep(
        step_id="s2",
        sequence_number=1,
        function_name="book_ticket",
        expected_output="ok",
    )
    with pytest.raises(ValueError, match="sorted by sequence_number"):
        StructuredTravelPlan(
            plan_id="plan_1",
            trace_id="trace_1",
            status=PlanStatus.DRAFT,
            steps=[step1, step2],
            created_at=time.time(),
        )


def test_model_invariants_duplicate_sequence():
    step1 = PlanStep(
        step_id="s1",
        sequence_number=1,
        function_name="search_trains",
        expected_output="ok",
    )
    step2 = PlanStep(
        step_id="s2",
        sequence_number=1,
        function_name="book_ticket",
        expected_output="ok",
    )
    with pytest.raises(ValueError, match="unique sequence numbers"):
        StructuredTravelPlan(
            plan_id="plan_1",
            trace_id="trace_1",
            status=PlanStatus.DRAFT,
            steps=[step1, step2],
            created_at=time.time(),
        )


def test_model_invariants_double_booking():
    # Attempting to book passenger P123 on two different trains on the same day
    step1 = PlanStep(
        step_id="s1",
        sequence_number=1,
        function_name="book_ticket",
        input_args={
            "passenger_id": "P123",
            "date": "2026-07-25",
            "train_number": "12301",
        },
        expected_output="ok",
    )
    step2 = PlanStep(
        step_id="s2",
        sequence_number=2,
        function_name="book_ticket",
        input_args={
            "passenger_id": "P123",
            "date": "2026-07-25",
            "train_number": "12302",
        },
        expected_output="ok",
    )
    with pytest.raises(ValueError, match="Overlapping booking detected"):
        StructuredTravelPlan(
            plan_id="plan_1",
            trace_id="trace_1",
            status=PlanStatus.DRAFT,
            steps=[step1, step2],
            created_at=time.time(),
        )


# ==========================================
# 2. Factory Tests
# ==========================================
def test_factory_creation():
    step = PlanStep(
        step_id="s1",
        sequence_number=1,
        function_name="search_trains",
        expected_output="ok",
    )
    plan = StructuredTravelPlanFactory.create_plan(
        trace_id="trace_factory", steps=[step]
    )

    assert plan.plan_id is not None
    assert len(plan.plan_id) > 10
    assert plan.trace_id == "trace_factory"
    assert plan.status == PlanStatus.DRAFT
    assert plan.created_at <= time.time()
    assert plan.steps[0].step_id == "s1"


# ==========================================
# 3. Registry Tests
# ==========================================
def test_registry_approved_functions():
    assert function_registry.is_approved("search_trains") is True
    assert function_registry.is_approved("book_ticket") is True
    assert function_registry.is_approved("malicious_unapproved_command") is False

    meta = function_registry.get_metadata("search_trains")
    assert meta is not None
    assert meta["function_name"] == "search_trains"


# ==========================================
# 4. Sequencer Tests
# ==========================================
def test_sequencer_plan_travel(base_intent_descriptor):
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)

    assert len(steps) == 3
    assert steps[0].function_name == "search_trains"
    assert steps[1].function_name == "check_seat_availability"
    assert steps[2].function_name == "book_ticket"
    assert steps[2].input_args["concession"] == "senior"
    assert steps[2].input_args["passenger_age"] == 65


def test_sequencer_check_pnr(base_intent_descriptor):
    base_intent_descriptor.intent.name = "check_pnr"
    base_intent_descriptor.slots = {
        "pnr": Slot(name="pnr", value="4234567890", type="PNR", confidence=0.99)
    }
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)

    assert len(steps) == 3
    assert steps[0].function_name == "check_pnr"
    assert steps[1].function_name == "check_waitlist_probability"
    assert steps[2].function_name == "search_alternative_route"


def test_sequencer_missing_slots(base_intent_descriptor):
    base_intent_descriptor.slots = {}  # clear slots
    sequencer = StepSequencer()
    with pytest.raises(SequencingError):
        sequencer.sequence_steps(base_intent_descriptor)


# ==========================================
# 5. Specifications Tests
# ==========================================
def test_spec_age_eligible_valid(base_intent_descriptor):
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)
    plan = StructuredTravelPlanFactory.create_plan(trace_id="test", steps=steps)

    validator = PlanValidator()
    report = validator.validate_plan(plan)

    # Age is 65, so senior concession is valid
    assert report.is_valid is True
    assert len(report.violated_constraints) == 0


def test_spec_age_eligible_invalid(base_intent_descriptor):
    # Underage senior citizen attempt
    base_intent_descriptor.slots["passenger_age"].value = 45
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)
    plan = StructuredTravelPlanFactory.create_plan(trace_id="test", steps=steps)

    validator = PlanValidator()
    report = validator.validate_plan(plan)

    assert report.is_valid is False
    assert any(c.rule_id == "RULE-AGE-002" for c in report.violated_constraints)


def test_spec_time_window_layover_invalid(base_intent_descriptor):
    sequencer = StepSequencer()
    sequencer.sequence_steps(base_intent_descriptor)  # verify sequencer runs

    # Configure connecting booking steps with small layover (< 45 mins)
    step1 = PlanStep(
        step_id="step_3",
        sequence_number=3,
        function_name="book_ticket",
        input_args={
            "passenger_id": "P123",
            "origin": "NDLS",
            "destination": "PUNE",
            "departure_time": "2026-07-25T10:00:00",
            "arrival_time": "2026-07-25T12:00:00",
        },
        expected_output="ok",
    )
    step2 = PlanStep(
        step_id="step_4",
        sequence_number=4,
        function_name="book_ticket",
        input_args={
            "passenger_id": "P123",
            "origin": "PUNE",
            "destination": "SBC",
            "departure_time": "2026-07-25T12:30:00",  # 30 mins layover
            "arrival_time": "2026-07-25T15:00:00",
        },
        expected_output="ok",
    )

    plan = StructuredTravelPlanFactory.create_plan(
        trace_id="test", steps=[step1, step2]
    )
    validator = PlanValidator()
    report = validator.validate_plan(plan)

    assert report.is_valid is False
    assert any(c.rule_id == "RULE-TIME-001" for c in report.violated_constraints)


# ==========================================
# 6. Policies Tests
# ==========================================
def test_policy_lockout(base_intent_descriptor):
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)

    # Set departure 2 hours from now (within 4-hour chart preparation lockout)
    lockout_time = (datetime.now() + timedelta(hours=2)).isoformat()
    steps[2].input_args["departure_time"] = lockout_time

    plan = StructuredTravelPlanFactory.create_plan(trace_id="test", steps=steps)
    validator = PlanValidator()
    report = validator.validate_plan(plan)

    assert report.is_valid is False
    assert any(
        c.rule_id == "POLICY-VIOLATION-LOCKOUTPOLICY"
        for c in report.violated_constraints
    )


def test_policy_identity_safety_mismatch(base_intent_descriptor):
    sequencer = StepSequencer()
    steps = sequencer.sequence_steps(base_intent_descriptor)

    # Passenger ID does not match metadata owner user_id, and proxy not authorized
    plan = StructuredTravelPlanFactory.create_plan(trace_id="test", steps=steps)
    plan.metadata["user_id"] = "DIFFERENT_USER_ID"
    plan.metadata["is_authorized_proxy"] = False

    validator = PlanValidator()
    report = validator.validate_plan(plan)

    assert report.is_valid is False
    assert any(
        c.rule_id == "POLICY-VIOLATION-IDENTITYSAFETYPOLICY"
        for c in report.violated_constraints
    )


# ==========================================
# 7. Clarification Tests
# ==========================================
def test_clarification_mapping(base_intent_descriptor):
    base_intent_descriptor.needs_clarification = True
    base_intent_descriptor.context["validation_errors"] = [
        "Missing required slot: origin"
    ]

    handler = ClarificationHandler()
    plan = handler.handle_clarification(base_intent_descriptor)

    assert plan.status == PlanStatus.NEEDS_CLARIFICATION
    assert plan.steps[0].function_name == "request_clarification"
    assert plan.steps[0].input_args["missing_slots"] == ["origin"]


# ==========================================
# 8. Coordinator integration Tests
# ==========================================
def test_coordinator_happy_path(base_intent_descriptor):
    import asyncio

    coordinator = PlanningCoordinator()
    plan = asyncio.run(coordinator.coordinate_planning(base_intent_descriptor))

    assert plan.plan_id is not None
    assert plan.status == PlanStatus.VALIDATED
    assert len(plan.steps) == 3
    assert plan.validation_report.is_valid is True


def test_coordinator_clarification(base_intent_descriptor):
    import asyncio

    base_intent_descriptor.needs_clarification = True
    base_intent_descriptor.context["validation_errors"] = [
        "Missing required slot: origin"
    ]

    coordinator = PlanningCoordinator()
    plan = asyncio.run(coordinator.coordinate_planning(base_intent_descriptor))

    assert plan.status == PlanStatus.NEEDS_CLARIFICATION
    assert plan.steps[0].function_name == "request_clarification"
