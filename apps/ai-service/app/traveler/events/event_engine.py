# app/traveler/events/event_engine.py
"""
Event Engine – normalises raw telemetry dictionaries into canonical
``TravelerEventDTO`` instances (Planning §2, §22).
"""

from typing import Any, Dict
from app.traveler.interfaces.contracts import IEventEngine
from app.traveler.dto.models import TravelerEventDTO

_SEVERITY_MAP: Dict[str, str] = {
    "DELAY": "MEDIUM",
    "PLATFORM_CHANGE": "CRITICAL",
    "CANCELLATION": "EMERGENCY",
    "CONNECTION_MISSED": "HIGH",
    "MEDICAL_EMERGENCY": "EMERGENCY",
    "ARRIVAL_UPDATE": "LOW",
}


class EventEngine(IEventEngine):
    """Parses raw telemetry dicts into strongly-typed event DTOs."""

    def parse_raw_event(self, raw: Dict[str, Any]) -> TravelerEventDTO:
        event_type = raw.get("event_type", "UNKNOWN")
        severity = raw.get("severity") or _SEVERITY_MAP.get(event_type, "LOW")
        return TravelerEventDTO(
            event_id=raw.get("event_id", "evt_unknown"),
            event_type=event_type,
            severity=severity,
            timestamp=raw.get("timestamp", 0.0),
            metadata=raw.get("metadata", {}),
        )
