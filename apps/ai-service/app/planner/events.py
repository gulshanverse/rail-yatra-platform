# app/planner/events.py
import time
import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field


class PlannerEvent(BaseModel):
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier"
    )
    event_type: str = Field(..., description="Canonical event classification label")
    plan_id: str = Field(..., description="Target travel plan ID")
    trace_id: str = Field(..., description="Correlation trace ID")
    timestamp: float = Field(
        default_factory=time.time, description="Epoch timestamp of occurrence"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Event payload context data"
    )


class PlanFormulated(PlannerEvent):
    event_type: str = "plan_formulated"


class PlanVerified(PlannerEvent):
    event_type: str = "plan_verified"


class PlanConflictDetected(PlannerEvent):
    event_type: str = "plan_conflict_detected"
