# app/execution/specifications.py
from datetime import datetime, timedelta
from app.execution.models import ExecutionSession, StepExecutionStatus


class ReadyToExecuteSpecification:
    """Verifies if an execution session is valid, authorized, and is within safe execution time windows."""

    def is_satisfied_by(self, session: ExecutionSession) -> bool:
        # 1. Enforce that session is in INITIATED status
        if session.status != "INITIATED":
            return False

        # 2. Check for required user metadata (Authorization verification)
        user_id = session.user_id or session.metadata.get("user_id")
        if not user_id:
            return False

        # 3. Check departure lockout times for booking steps
        for tracker in session.step_trackers:
            if tracker.plan_step.function_name == "book_ticket":
                dep_time_str = tracker.plan_step.input_args.get("departure_time")
                if dep_time_str:
                    try:
                        dep_dt = datetime.fromisoformat(dep_time_str)
                        current_time = datetime.fromtimestamp(session.created_at)

                        # Lockout window validation: Departure must be > 4 hours in the future
                        if dep_dt - current_time <= timedelta(hours=4):
                            return False
                    except (ValueError, TypeError):
                        # Skip or fail if dates are invalid
                        return False

        return True


class CompensationRequiredSpecification:
    """Evaluates if a failed or cancelled execution session has successfully processed steps requiring compensation."""

    def is_satisfied_by(self, session: ExecutionSession) -> bool:
        # Evaluate if any tracker has succeeded and has a stored compensation reference
        for tracker in session.step_trackers:
            if (
                tracker.status == StepExecutionStatus.SUCCEEDED
                and tracker.compensation_reference is not None
            ):
                return True
        return False
