from typing import List, Any
from app.orchestrator.types import IntentDescriptor
from app.planner.models import PlanStep, PlanStepStatus
from app.planner.registry import function_registry
from app.planner.errors import SequencingError, UnauthorizedFunctionError
from app.planner.interfaces import IStepSequencer


class StepSequencer(IStepSequencer):
    """Domain service to sequence a structured list of PlanSteps from intent slots."""

    def sequence_steps(self, intent_descriptor: IntentDescriptor) -> List[PlanStep]:
        intent_name = intent_descriptor.intent.name.lower()
        slots = intent_descriptor.slots
        steps: List[PlanStep] = []

        # Helper to extract slot value
        def get_slot_val(key: str, default: Any = None) -> Any:
            return slots[key].value if key in slots else default

        # 1. Sequence plans based on intent type
        if intent_name == "plan_travel":
            origin = get_slot_val("origin")
            destination = get_slot_val("destination")
            date = get_slot_val("date")
            train_num = get_slot_val("train_number")
            class_code = get_slot_val("class")
            passenger_id = (
                get_slot_val("passenger_id") or get_slot_val("user_id") or "passenger_1"
            )
            age = get_slot_val("passenger_age") or get_slot_val("age")
            concession = get_slot_val("concession")

            # Check if we have minimum requirements
            if not origin or not destination:
                raise SequencingError(
                    "Missing origin or destination slots to plan travel."
                )

            # Step 1: Search trains
            search_step = PlanStep(
                step_id="step_1",
                sequence_number=1,
                function_name="search_trains",
                input_args={"origin": origin, "destination": destination, "date": date},
                expected_output="train_list",
                status=PlanStepStatus.PENDING,
            )
            steps.append(search_step)

            # Step 2: Check availability (if train is known or fallback search)
            avail_step = PlanStep(
                step_id="step_2",
                sequence_number=2,
                function_name="check_seat_availability",
                input_args={
                    "train_number": train_num or "MATCH_FROM_STEP_1",
                    "date": date,
                    "class": class_code or "SL",
                },
                expected_output="seat_status",
                status=PlanStepStatus.PENDING,
                prerequisites=["step_1"],
            )
            steps.append(avail_step)

            # Step 3: Book ticket
            # Provide mockup times for validation checks (e.g. departure 5 hours from now)
            from datetime import datetime, timedelta

            mock_departure = (datetime.now() + timedelta(hours=6)).isoformat()
            mock_arrival = (datetime.now() + timedelta(hours=10)).isoformat()

            book_step = PlanStep(
                step_id="step_3",
                sequence_number=3,
                function_name="book_ticket",
                input_args={
                    "train_number": train_num or "MATCH_FROM_STEP_2",
                    "passenger_id": passenger_id,
                    "date": date,
                    "class": class_code or "SL",
                    "concession": concession,
                    "passenger_age": age,
                    "origin": origin,
                    "destination": destination,
                    "departure_time": mock_departure,
                    "arrival_time": mock_arrival,
                },
                expected_output="booking_confirmation",
                status=PlanStepStatus.PENDING,
                prerequisites=["step_2"],
            )
            steps.append(book_step)

        elif intent_name == "check_pnr":
            pnr = get_slot_val("pnr")
            if not pnr:
                raise SequencingError("Missing PNR slot to perform status check.")

            pnr_step = PlanStep(
                step_id="step_1",
                sequence_number=1,
                function_name="check_pnr",
                input_args={"pnr": pnr},
                expected_output="pnr_status",
                status=PlanStepStatus.PENDING,
            )
            steps.append(pnr_step)

            # Add conditional waitlist check if PNR status step returns waitlist
            wl_step = PlanStep(
                step_id="step_2",
                sequence_number=2,
                function_name="check_waitlist_probability",
                input_args={"pnr": pnr},
                expected_output="waitlist_probability",
                status=PlanStepStatus.PENDING,
                prerequisites=["step_1"],
                fallback_step_id="step_3",  # routes to fallback search if probability is too low
            )
            steps.append(wl_step)

            # Fallback alternative route search step
            fallback_step = PlanStep(
                step_id="step_3",
                sequence_number=3,
                function_name="search_alternative_route",
                input_args={
                    "origin": "MATCH_FROM_PNR",
                    "destination": "MATCH_FROM_PNR",
                    "date": "MATCH_FROM_PNR",
                },
                expected_output="alternative_trains",
                status=PlanStepStatus.PENDING,
                prerequisites=["step_2"],
            )
            steps.append(fallback_step)

        elif intent_name == "journey_intelligence":
            train_num = get_slot_val("train_number")
            if not train_num:
                raise SequencingError(
                    "Missing train number slot to get journey intelligence."
                )

            avail_step = PlanStep(
                step_id="step_1",
                sequence_number=1,
                function_name="check_seat_availability",
                input_args={
                    "train_number": train_num,
                    "date": get_slot_val("date", "today"),
                    "class": "ALL",
                },
                expected_output="seat_status",
                status=PlanStepStatus.PENDING,
            )
            steps.append(avail_step)

        else:
            raise SequencingError(f"Unsupported planning intent: {intent_name}")

        # 2. Safety filter: Verify every sequenced step function exists in whitelisted ApprovedFunctionRegistry
        for step in steps:
            if not function_registry.is_approved(step.function_name):
                raise UnauthorizedFunctionError(
                    f"Sequencing failed: Step {step.step_id} references unapproved function '{step.function_name}'."
                )

        return steps
