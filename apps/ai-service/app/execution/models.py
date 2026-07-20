# app/execution/models.py
from enum import Enum
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.planner.models import PlanStep
from app.execution.errors import InvalidStateTransitionError


class ExecutionSessionStatus(str, Enum):
    INITIATED = "INITIATED"
    PROCESSING = "PROCESSING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    REVERTING = "REVERTING"
    REVERTED = "REVERTED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class StepExecutionStatus(str, Enum):
    PENDING = "PENDING"
    DISPATCHING = "DISPATCHING"
    SUCCEEDED = "SUCCEEDED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    COMPENSATING = "COMPENSATING"
    REVERTED = "REVERTED"


class ExecutionToken(BaseModel):
    model_config = ConfigDict(frozen=True)
    token_value: str = Field(..., description="Idempotency token value")
    created_at: float = Field(default_factory=time.time)


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_attempts: int = Field(default=3, ge=1)
    base_delay_seconds: float = Field(default=1.0, ge=0.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    jitter: bool = Field(default=True)


class ExecutionStepTracker(BaseModel):
    step_id: str = Field(..., description="Pointer to the PlanStep ID")
    plan_step: PlanStep = Field(
        ..., description="Structured travel plan step being executed"
    )
    status: StepExecutionStatus = Field(default=StepExecutionStatus.PENDING)
    attempts_made: int = Field(default=0, ge=0)
    last_attempt_at: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    output_data: Optional[Dict[str, Any]] = Field(default=None)
    compensation_reference: Optional[str] = Field(
        default=None, description="PNR or booking reference to reverse if needed"
    )

    def record_attempt(self) -> None:
        self.attempts_made += 1
        self.last_attempt_at = time.time()

    def mark_success(self, output: Dict[str, Any]) -> None:
        self.status = StepExecutionStatus.SUCCEEDED
        self.output_data = output
        # If output contains a PNR or confirmation, store it as compensation reference
        if "pnr" in output:
            self.compensation_reference = output["pnr"]
        elif "booking_confirmation" in output:
            self.compensation_reference = output["booking_confirmation"]

    def mark_failure(self, error: str) -> None:
        self.status = StepExecutionStatus.FAILED
        self.error_message = error

    def mark_compensating(self) -> None:
        self.status = StepExecutionStatus.COMPENSATING

    def mark_reverted(self) -> None:
        self.status = StepExecutionStatus.REVERTED


class ExecutionSession(BaseModel):
    session_id: str = Field(..., description="Unique execution session identifier")
    plan_id: str = Field(..., description="Structured travel plan identifier")
    trace_id: str = Field(..., description="Correlation trace identifier")
    execution_token: ExecutionToken = Field(
        ..., description="Idempotency key associated with this session"
    )
    status: ExecutionSessionStatus = Field(default=ExecutionSessionStatus.INITIATED)
    step_trackers: List[ExecutionStepTracker] = Field(default_factory=list)
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    user_id: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_invariants(self) -> "ExecutionSession":
        # Invariant F: Exactly one active execution state must be present at any point.
        # Implied by the single status field structure.

        # Invariant E: Terminal states must not have active transitions
        if self.status in [
            ExecutionSessionStatus.COMPLETED,
            ExecutionSessionStatus.REVERTED,
            ExecutionSessionStatus.ABORTED,
        ]:
            pass  # Handled by state transition guard methods
        return self

    def _record_transition(
        self, old_status: ExecutionSessionStatus, new_status: ExecutionSessionStatus
    ) -> None:
        self.state_history.append(
            {
                "from_status": old_status,
                "to_status": new_status,
                "timestamp": time.time(),
            }
        )
        self.updated_at = time.time()
        self.status = new_status

    def transition_to(self, new_status: ExecutionSessionStatus) -> None:
        """Enforces Invariant E (Terminal state immutability) and strict lifecycle transitions."""
        current = self.status

        if current in [
            ExecutionSessionStatus.COMPLETED,
            ExecutionSessionStatus.REVERTED,
            ExecutionSessionStatus.ABORTED,
        ]:
            raise InvalidStateTransitionError(
                f"Terminal state immutability violation: Cannot transition execution session {self.session_id} "
                f"from terminal status '{current}' to '{new_status}'."
            )

        # Map allowed transitions
        allowed = {
            ExecutionSessionStatus.INITIATED: [
                ExecutionSessionStatus.PROCESSING,
                ExecutionSessionStatus.ABORTED,
            ],
            ExecutionSessionStatus.PROCESSING: [
                ExecutionSessionStatus.PROCESSING,
                ExecutionSessionStatus.PAUSED,
                ExecutionSessionStatus.COMPLETED,
                ExecutionSessionStatus.REVERTING,
                ExecutionSessionStatus.FAILED,
                ExecutionSessionStatus.ABORTED,
            ],
            ExecutionSessionStatus.PAUSED: [
                ExecutionSessionStatus.PROCESSING,
                ExecutionSessionStatus.ABORTED,
            ],
            ExecutionSessionStatus.REVERTING: [
                ExecutionSessionStatus.REVERTED,
                ExecutionSessionStatus.FAILED,
                ExecutionSessionStatus.ABORTED,
            ],
            ExecutionSessionStatus.FAILED: [ExecutionSessionStatus.ABORTED],
        }

        if new_status not in allowed.get(current, []):
            raise InvalidStateTransitionError(
                f"Invalid state transition: Transition from '{current}' to '{new_status}' is not permitted."
            )

        self._record_transition(current, new_status)
