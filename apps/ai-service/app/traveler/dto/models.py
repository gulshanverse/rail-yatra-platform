# app/traveler/dto/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class TravelerEventDTO(BaseModel):
    event_id: str
    event_type: str  # DELAY, PLATFORM_CHANGE, CANCELLATION, etc.
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL, EMERGENCY
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelerActionDTO(BaseModel):
    action_code: str  # LEAVE_EARLIER, CHANGE_PLATFORM, BOOK_ALTERNATIVE, etc.
    description: str
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL


class TravelerExplanationDTO(BaseModel):
    reason_code: str
    text: str
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)


class TravelerGuidanceDTO(BaseModel):
    guidance_id: str
    correlation_id: str
    timestamp: float
    traveler_id: str
    active_state: str  # PRE_DEPARTURE, IN_TRANSIT, LAYOVER, COMPLETED
    status: str  # PUNCTUAL, DELAYED, MISSED_CONNECTION
    recommended_action: Optional[TravelerActionDTO] = None
    explanation: Optional[TravelerExplanationDTO] = None
    confidence_score: float


class TravelerAlertDTO(BaseModel):
    alert_id: str
    priority: str
    title: str
    body: str
    geofence_radius_meters: int


class TravelerReminderDTO(BaseModel):
    reminder_id: str
    fire_time: float
    title: str
    body: str


class TravelerRecoveryDTO(BaseModel):
    recovery_id: str
    incident_type: str
    alternative_options: List[Dict[str, Any]] = Field(default_factory=list)


class TravelerCheckpointDTO(BaseModel):
    checkpoint_id: str
    station_code: str
    scheduled_arrival: float
    actual_arrival: Optional[float] = None
    variance_minutes: float


class TravelerTimelineDTO(BaseModel):
    timeline_id: str
    version: str
    events: List[TravelerCheckpointDTO] = Field(default_factory=list)


class TravelerAuditDTO(BaseModel):
    audit_record_id: str
    guidance_id: str
    traveler_id: str
    journey_id: str
    booking_id: str
    timeline_version: str
    decision_version: str
    correlation_id: str
    reason_code: str
    supporting_evidence: Dict[str, Any]
    confidence: float
    selected_action: str
    outcome_status: str
    retention_policy: str


class TravelerMetricsDTO(BaseModel):
    metric_name: str
    value: float
    tags: Dict[str, str] = Field(default_factory=dict)
