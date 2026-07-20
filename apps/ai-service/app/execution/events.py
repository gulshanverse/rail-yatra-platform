# app/execution/events.py
import time
import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field


class ExecutionEvent(BaseModel):
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier"
    )
    event_type: str = Field(..., description="Canonical event classification label")
    session_id: str = Field(..., description="Target execution session ID")
    trace_id: str = Field(..., description="Correlation trace ID")
    timestamp: float = Field(
        default_factory=time.time, description="Epoch timestamp of occurrence"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Event payload context data"
    )


class ExecutionStarted(ExecutionEvent):
    event_type: str = "execution_started"


class ExecutionPaused(ExecutionEvent):
    event_type: str = "execution_paused"


class ExecutionResumed(ExecutionEvent):
    event_type: str = "execution_resumed"


class ExecutionCancelled(ExecutionEvent):
    event_type: str = "execution_cancelled"


class ExecutionTimedOut(ExecutionEvent):
    event_type: str = "execution_timed_out"


class StepExecutionSucceeded(ExecutionEvent):
    event_type: str = "step_execution_succeeded"


class StepExecutionFailed(ExecutionEvent):
    event_type: str = "step_execution_failed"


class ReversalInitiated(ExecutionEvent):
    event_type: str = "reversal_initiated"


class CompensationCompleted(ExecutionEvent):
    event_type: str = "compensation_completed"


class ManualInterventionRequested(ExecutionEvent):
    event_type: str = "manual_intervention_requested"


class ExecutionRecovered(ExecutionEvent):
    event_type: str = "execution_recovered"


class ExecutionAborted(ExecutionEvent):
    event_type: str = "execution_aborted"


class ExecutionFinalized(ExecutionEvent):
    event_type: str = "execution_finalized"
