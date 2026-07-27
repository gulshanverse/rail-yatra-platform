"""
Interfaces, Protocols, and Enumerations for Phase 8 Real-Time Operations Platform.
"""

from enum import Enum
from typing import Protocol, Dict, Any, List, Optional


class EventType(str, Enum):
    TRAIN_STARTED = "TRAIN_STARTED"
    TRAIN_STOPPED = "TRAIN_STOPPED"
    TRAIN_DELAYED = "TRAIN_DELAYED"
    TRAIN_RESCHEDULED = "TRAIN_RESCHEDULED"
    TRAIN_CANCELLED = "TRAIN_CANCELLED"
    PLATFORM_CHANGED = "PLATFORM_CHANGED"
    COACH_CHANGED = "COACH_CHANGED"
    TRAIN_DIVERTED = "TRAIN_DIVERTED"
    BOARDING_STARTED = "BOARDING_STARTED"
    BOARDING_COMPLETED = "BOARDING_COMPLETED"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"


class TrainStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    BOARDING = "BOARDING"
    DEPARTED = "DEPARTED"
    RUNNING = "RUNNING"
    DELAYED = "DELAYED"
    DIVERTED = "DIVERTED"
    CANCELLED = "CANCELLED"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"


class JourneyStatus(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    BOARDING = "BOARDING"
    ONBOARD = "ONBOARD"
    TRANSFER = "TRANSFER"
    DISRUPTED = "DISRUPTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class IEventGateway(Protocol):
    def ingest_event(self, raw_data: Dict[str, Any]) -> Any: ...


class ITrainTracker(Protocol):
    def update_state(self, event: Any) -> Any: ...
    def get_state(self, train_number: str) -> Optional[Any]: ...


class IJourneyTracker(Protocol):
    def update_journey(self, event: Any) -> Any: ...
    def get_journey(self, journey_id: str) -> Optional[Any]: ...


class IETAEngine(Protocol):
    def calculate_eta(self, train_number: str, station_code: str) -> Any: ...


class IIncidentEngine(Protocol):
    def evaluate_incidents(self, train_state: Any, journey_state: Any) -> List[Any]: ...


class INotificationEngine(Protocol):
    def send_notification(self, journey_id: str, incident: Any, message: str) -> Any: ...
