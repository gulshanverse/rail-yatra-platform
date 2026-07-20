# app/planner/policies.py
from datetime import datetime, timedelta
from app.planner.models import StructuredTravelPlan
from app.planner.errors import PolicyViolationError


class LockoutPolicy:
    """Restricts plan generation for trains departing within the chart preparation window (<= 4 hours)."""

    name: str = "LockoutPolicy"

    def evaluate(self, plan: StructuredTravelPlan) -> bool:
        current_time = datetime.fromtimestamp(plan.created_at)

        for step in plan.steps:
            if step.function_name == "book_ticket":
                dep_time_str = step.input_args.get("departure_time")
                if dep_time_str:
                    try:
                        dep_dt = datetime.fromisoformat(dep_time_str)
                        # Chart preparation lockout is typically 4 hours before departure
                        if dep_dt - current_time <= timedelta(hours=4):
                            raise PolicyViolationError(
                                f"Lockout Policy Violated: Train booking for step {step.step_id} is departing within the "
                                f"4-hour chart preparation lockout window (departure: {dep_time_str})."
                            )
                    except (ValueError, TypeError):
                        pass
        return True


class IdentitySafetyPolicy:
    """Prevents bookings where traveler credentials do not match passenger profiles."""

    name: str = "IdentitySafetyPolicy"

    def evaluate(self, plan: StructuredTravelPlan) -> bool:
        # Check that user_id in plan metadata matches passenger_id or is authorized
        owner_id = plan.metadata.get("user_id") or plan.metadata.get("owner_id")

        for step in plan.steps:
            if step.function_name == "book_ticket":
                passenger_id = step.input_args.get("passenger_id")
                # In our security scheme, a user cannot book for a different passenger ID unless owner_id matches
                if owner_id and passenger_id and passenger_id != owner_id:
                    # Allow override if explicitly allowed in metadata, otherwise fail
                    if not plan.metadata.get("is_authorized_proxy", False):
                        raise PolicyViolationError(
                            f"Identity Safety Policy Violated: Owner ID '{owner_id}' is not authorized to plan "
                            f"bookings for Passenger ID '{passenger_id}' without verified proxy authorization."
                        )
        return True


class ConcessionValidationPolicy:
    """Restricts the application of concessions unless verified age inputs are present in the travel plan."""

    name: str = "ConcessionValidationPolicy"

    def evaluate(self, plan: StructuredTravelPlan) -> bool:
        for step in plan.steps:
            if step.function_name == "book_ticket":
                concession = step.input_args.get("concession")
                age = step.input_args.get("passenger_age") or step.input_args.get("age")

                # If any concession is applied, age must be specified and non-null
                if concession and (age is None or str(age) == ""):
                    raise PolicyViolationError(
                        f"Concession Validation Policy Violated: Concession '{concession}' was requested for "
                        f"step {step.step_id} but no verified passenger age was provided."
                    )
        return True
