"""
Event Taxonomy & Event Envelope Factory for Phase 8 Real-Time Operations Platform.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.realtime.interfaces import EventType
from app.realtime.models import OperationalEvent


class EventFactory:
    @staticmethod
    def create_event(
        event_type: EventType,
        train_number: str,
        station_code: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OperationalEvent:
        """Constructs a standardized OperationalEvent envelope."""
        now_str = datetime.now(timezone.utc).isoformat()
        return OperationalEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            train_number=train_number,
            station_code=station_code,
            timestamp=now_str,
            payload=payload or {},
        )
