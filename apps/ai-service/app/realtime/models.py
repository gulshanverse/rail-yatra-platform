"""
Domain Data Models for Phase 8 Real-Time Operations Platform.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.realtime.interfaces import (
    EventType,
    TrainStatus,
    JourneyStatus,
    IncidentSeverity,
    NotificationPriority,
)


class OperationalEvent(BaseModel):
    event_id: str
    event_type: EventType
    train_number: str
    station_code: Optional[str] = None
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class TrainState(BaseModel):
    train_number: str
    current_station: str
    next_station: Optional[str] = None
    status: TrainStatus = TrainStatus.SCHEDULED
    delay_minutes: int = 0
    current_platform: Optional[str] = None
    speed_kmh: float = 0.0
    last_updated: str


class JourneyState(BaseModel):
    journey_id: str
    passenger_id: str
    train_number: str
    status: JourneyStatus = JourneyStatus.PLANNED
    origin_station: str
    destination_station: str
    current_station: Optional[str] = None
    eta_destination: str
    transfer_risk: bool = False
    last_updated: str


class Incident(BaseModel):
    incident_id: str
    train_number: str
    severity: IncidentSeverity
    title: str
    description: str
    affected_passengers_count: int = 0
    created_at: str
    resolved: bool = False


class ETAResult(BaseModel):
    train_number: str
    station_code: str
    scheduled_arrival: str
    predicted_eta: str
    delay_minutes: int
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    last_calculated: str


class NotificationPayload(BaseModel):
    notification_id: str
    journey_id: str
    passenger_id: str
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    dispatched_at: str


class DashboardMetrics(BaseModel):
    total_events_processed: int = 0
    active_trains_count: int = 0
    active_journeys_monitored: int = 0
    active_incidents_count: int = 0
    on_time_performance_percent: float = 100.0
    system_health_status: str = "HEALTHY"
    timestamp: str


class RealTimeAIContext(BaseModel):
    train_number: str
    journey_id: Optional[str] = None
    live_train_state: Optional[TrainState] = None
    active_journey_state: Optional[JourneyState] = None
    active_incidents: List[Incident] = Field(default_factory=list)
    dynamic_eta: Optional[ETAResult] = None
    ai_recommendations: List[str] = Field(default_factory=list)
