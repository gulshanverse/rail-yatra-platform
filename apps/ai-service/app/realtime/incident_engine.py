"""
Operational Incident Detection Engine for Phase 8 Real-Time Operations Platform.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from app.realtime.interfaces import EventType, IncidentSeverity
from app.realtime.models import OperationalEvent, TrainState, JourneyState, Incident


class IncidentEngine:
    def __init__(self) -> None:
        self._incidents: List[Incident] = []

    def evaluate_event_for_incidents(
        self,
        event: OperationalEvent,
        train_state: Optional[TrainState] = None,
        affected_journeys: Optional[List[JourneyState]] = None,
    ) -> List[Incident]:
        """Evaluates operational event and active state to detect new operational incidents."""
        new_incidents: List[Incident] = []
        now_str = datetime.now(timezone.utc).isoformat()
        affected_count = len(affected_journeys) if affected_journeys else 0

        if event.event_type == EventType.TRAIN_CANCELLED:
            inc = Incident(
                incident_id=f"inc-{uuid.uuid4().hex[:10]}",
                train_number=event.train_number,
                severity=IncidentSeverity.CRITICAL,
                title=f"Train {event.train_number} Service Cancelled",
                description="Railway operational control has issued a full service cancellation for this train.",
                affected_passengers_count=affected_count,
                created_at=now_str,
                resolved=False,
            )
            new_incidents.append(inc)

        elif event.event_type == EventType.PLATFORM_CHANGED:
            new_platform = (event.payload or {}).get("new_platform", "UNKNOWN")
            inc = Incident(
                incident_id=f"inc-{uuid.uuid4().hex[:10]}",
                train_number=event.train_number,
                severity=IncidentSeverity.HIGH,
                title=f"Platform Change for Train {event.train_number}",
                description=f"Train arrival platform changed to Platform {new_platform} at {event.station_code or 'station'}.",
                affected_passengers_count=affected_count,
                created_at=now_str,
                resolved=False,
            )
            new_incidents.append(inc)

        elif event.event_type in (EventType.TRAIN_DELAYED, EventType.TRAIN_STOPPED):
            delay = (event.payload or {}).get("delay_minutes") or (train_state.delay_minutes if train_state else 0)
            if delay >= 60:
                severity = IncidentSeverity.HIGH if delay >= 120 else IncidentSeverity.MEDIUM
                inc = Incident(
                    incident_id=f"inc-{uuid.uuid4().hex[:10]}",
                    train_number=event.train_number,
                    severity=severity,
                    title=f"Significant Delay on Train {event.train_number}",
                    description=f"Train is currently running {delay} minutes behind schedule.",
                    affected_passengers_count=affected_count,
                    created_at=now_str,
                    resolved=False,
                )
                new_incidents.append(inc)

        self._incidents.extend(new_incidents)
        return new_incidents

    def get_active_incidents(self) -> List[Incident]:
        """Returns all unresolved incidents."""
        return [inc for inc in self._incidents if not inc.resolved]

    def resolve_incident(self, incident_id: str) -> bool:
        """Marks an incident as resolved."""
        for inc in self._incidents:
            if inc.incident_id == incident_id:
                inc.resolved = True
                return True
        return False
