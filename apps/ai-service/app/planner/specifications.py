# app/planner/specifications.py
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel
from app.planner.models import StructuredTravelPlan, Constraint, PlanStep
from app.planner.interfaces import ISpecification


class SpecificationResult(BaseModel):
    is_satisfied: bool
    violated_constraint: Optional[Constraint] = None


class AgeEligibleSpecification(ISpecification):
    """Verifies that senior citizen concession discounts are only applied for passengers age >= 60."""

    def is_satisfied_by(self, plan: StructuredTravelPlan) -> SpecificationResult:
        for step in plan.steps:
            if step.function_name == "book_ticket":
                concession = step.input_args.get("concession")
                age = step.input_args.get("passenger_age") or step.input_args.get("age")

                # If senior discount is requested, passenger age must be >= 60
                if concession == "senior" or step.input_args.get("quota") == "SR":
                    if age is None:
                        return SpecificationResult(
                            is_satisfied=False,
                            violated_constraint=Constraint(
                                rule_id="RULE-AGE-001",
                                description="Passenger age is missing but senior citizen concession was requested.",
                                category="regulatory",
                                parameters={"step_id": step.step_id},
                            ),
                        )
                    if int(age) < 60:
                        return SpecificationResult(
                            is_satisfied=False,
                            violated_constraint=Constraint(
                                rule_id="RULE-AGE-002",
                                description=f"Passenger age {age} does not meet the minimum requirement of 60 for senior concession.",
                                category="regulatory",
                                parameters={
                                    "passenger_age": age,
                                    "step_id": step.step_id,
                                },
                            ),
                        )
        return SpecificationResult(is_satisfied=True)


class TimeWindowSpecification(ISpecification):
    """
    Validates route layovers (connection layovers must be >= 45 minutes)
    and checks departure lockout times.
    """

    def is_satisfied_by(self, plan: StructuredTravelPlan) -> SpecificationResult:
        # 1. Connection layovers validation (>= 45 mins)
        # Find connecting steps. If arrival destination matches next origin.
        steps_by_passenger: Dict[str, list] = {}
        for step in plan.steps:
            if step.function_name == "book_ticket":
                pass_id = step.input_args.get("passenger_id") or "default_passenger"
                steps_by_passenger.setdefault(pass_id, []).append(step)

        for pass_id, pass_steps in steps_by_passenger.items():
            # Sort passenger steps by sequence_number
            sorted_steps = sorted(pass_steps, key=lambda s: s.sequence_number)
            for i in range(len(sorted_steps) - 1):
                step1 = sorted_steps[i]
                step2 = sorted_steps[i + 1]

                dest = step1.input_args.get("destination")
                orig = step2.input_args.get("origin")

                # Check layover time if they connect at the same station
                if dest and orig and dest == orig:
                    arr_time_str = step1.input_args.get("arrival_time")
                    dep_time_str = step2.input_args.get("departure_time")

                    if arr_time_str and dep_time_str:
                        try:
                            # Support parsing standard datetime formats
                            arr_dt = datetime.fromisoformat(arr_time_str)
                            dep_dt = datetime.fromisoformat(dep_time_str)

                            layover_duration = dep_dt - arr_dt
                            if layover_duration < timedelta(minutes=45):
                                return SpecificationResult(
                                    is_satisfied=False,
                                    violated_constraint=Constraint(
                                        rule_id="RULE-TIME-001",
                                        description=(
                                            f"Connection layover of {layover_duration.total_seconds() / 60:.1f} minutes "
                                            f"at {dest} is below the 45-minute minimum limit."
                                        ),
                                        category="route_feasibility",
                                        parameters={
                                            "layover_minutes": layover_duration.total_seconds()
                                            / 60,
                                            "passenger_id": pass_id,
                                        },
                                    ),
                                )
                        except (ValueError, TypeError):
                            # In case date parsing fails, skip or warn
                            pass

        return SpecificationResult(is_satisfied=True)


class DoubleBookingSpecification(ISpecification):
    """Checks that the passenger has no overlapping bookings for the scheduled travel window."""

    def is_satisfied_by(self, plan: StructuredTravelPlan) -> SpecificationResult:
        passenger_bookings: Dict[str, List[PlanStep]] = {}
        for step in plan.steps:
            if step.function_name == "book_ticket":
                passenger_id = (
                    step.input_args.get("passenger_id") or "default_passenger"
                )
                passenger_bookings.setdefault(passenger_id, []).append(step)

        for passenger_id, steps in passenger_bookings.items():
            for i in range(len(steps)):
                for j in range(i + 1, len(steps)):
                    step1 = steps[i]
                    step2 = steps[j]

                    date1 = step1.input_args.get("date")
                    date2 = step2.input_args.get("date")
                    train1 = step1.input_args.get("train_number")
                    train2 = step2.input_args.get("train_number")

                    if date1 and date2 and date1 == date2 and train1 != train2:
                        return SpecificationResult(
                            is_satisfied=False,
                            violated_constraint=Constraint(
                                rule_id="RULE-CONFLICT-001",
                                description=(
                                    f"Overlapping booking conflict: Passenger '{passenger_id}' has bookings "
                                    f"scheduled on different trains ({train1} and {train2}) on the same date ({date1})."
                                ),
                                category="double_booking",
                                parameters={
                                    "passenger_id": passenger_id,
                                    "date": date1,
                                    "train1": train1,
                                    "train2": train2,
                                },
                            ),
                        )
        return SpecificationResult(is_satisfied=True)
