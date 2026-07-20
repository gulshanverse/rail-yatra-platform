# app/execution/policies.py
import random
from typing import List
from app.execution.models import ExecutionStepTracker, StepExecutionStatus, RetryPolicy


class ControlledRetryPolicy:
    """Policy governing transient failure retries with progressive delay and optional jitter."""

    def should_retry(self, tracker: ExecutionStepTracker, policy: RetryPolicy) -> bool:
        """Determines if a step should be retried based on current attempts."""
        # Only retry if step is in a failed status and has remaining retry budget
        return (
            tracker.status in [StepExecutionStatus.FAILED, StepExecutionStatus.RETRYING]
            and tracker.attempts_made < policy.max_attempts
        )

    def calculate_delay(
        self, tracker: ExecutionStepTracker, policy: RetryPolicy
    ) -> float:
        """Calculates backoff delay using exponential backoff + optional random jitter."""
        if tracker.attempts_made == 0:
            return 0.0

        # Exponential backoff formula: delay = base * (multiplier ** (attempt - 1))
        delay = policy.base_delay_seconds * (
            policy.backoff_multiplier ** (tracker.attempts_made - 1)
        )

        if policy.jitter:
            # Apply uniform random jitter (e.g. +/- 20% variation or uniform between 0 and delay)
            jitter_range = delay * 0.2
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.0, delay)


class StrictReversalSequencePolicy:
    """Policy dictating that compensation/rollback runs in exact reverse chronological order of step execution."""

    def get_reversal_sequence(
        self, trackers: List[ExecutionStepTracker]
    ) -> List[ExecutionStepTracker]:
        """
        Filters and sorts step trackers to determine the sequence in which compensation should run.
        Only steps that succeeded and have a compensation reference (e.g. booked tickets) need rollback.
        """
        succeeded_trackers = [
            tracker
            for tracker in trackers
            if tracker.status == StepExecutionStatus.SUCCEEDED
            and tracker.compensation_reference is not None
        ]

        # Sort by sequence_number in descending order to execute rollback in reverse
        return sorted(
            succeeded_trackers, key=lambda t: t.plan_step.sequence_number, reverse=True
        )
