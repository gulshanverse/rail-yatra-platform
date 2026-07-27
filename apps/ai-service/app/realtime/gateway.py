"""
Real-Time Event Gateway: Validates, normalizes, and sanitizes incoming operational events.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from app.realtime.interfaces import EventType
from app.realtime.models import OperationalEvent
from app.realtime.events import EventFactory


class RealTimeEventGateway:
    def validate_and_normalize(self, raw_data: Dict[str, Any]) -> OperationalEvent:
        """Validates incoming event payloads and converts them into an OperationalEvent model."""
        if not isinstance(raw_data, dict):
            raise ValueError("Event payload must be a JSON dictionary.")

        train_number = raw_data.get("train_number")
        if not train_number:
            raise ValueError("Missing required field 'train_number' in event payload.")

        raw_event_type = raw_data.get("event_type")
        if not raw_event_type:
            raise ValueError("Missing required field 'event_type' in event payload.")

        try:
            event_type = EventType(str(raw_event_type).upper())
        except ValueError:
            raise ValueError(f"Unsupported event_type '{raw_event_type}'.")

        station_code = raw_data.get("station_code")
        payload = raw_data.get("payload", {})
        timestamp = raw_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
        event_id = raw_data.get("event_id")

        if event_id:
            return OperationalEvent(
                event_id=event_id,
                event_type=event_type,
                train_number=str(train_number),
                station_code=station_code,
                timestamp=timestamp,
                payload=payload,
            )

        return EventFactory.create_event(
            event_type=event_type,
            train_number=str(train_number),
            station_code=station_code,
            payload=payload,
        )
