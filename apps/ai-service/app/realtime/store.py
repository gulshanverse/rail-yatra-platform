"""
In-Memory Event Store & History Log for Phase 8 Real-Time Operations Platform.
"""

from typing import Dict, List, Optional
from app.realtime.models import OperationalEvent


class EventStore:
    def __init__(self) -> None:
        self._events: List[OperationalEvent] = []
        self._events_by_id: Dict[str, OperationalEvent] = {}

    def append(self, event: OperationalEvent) -> None:
        """Appends an event to the immutable store."""
        self._events.append(event)
        self._events_by_id[event.event_id] = event

    def get_by_id(self, event_id: str) -> Optional[OperationalEvent]:
        """Fetches an event by ID."""
        return self._events_by_id.get(event_id)

    def get_by_train(self, train_number: str) -> List[OperationalEvent]:
        """Retrieves all events recorded for a given train number."""
        return [evt for evt in self._events if evt.train_number == train_number]

    def get_all(self) -> List[OperationalEvent]:
        """Returns all recorded events."""
        return list(self._events)

    def count(self) -> int:
        """Returns total number of events in store."""
        return len(self._events)

    def clear(self) -> None:
        """Clears the event store."""
        self._events.clear()
        self._events_by_id.clear()
