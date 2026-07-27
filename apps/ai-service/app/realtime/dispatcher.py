"""
Event Dispatcher: Pub/Sub Router for Real-Time Operational Events.
"""

import logging
from typing import Callable, Dict, List, Awaitable, Union
from app.realtime.interfaces import EventType
from app.realtime.models import OperationalEvent

logger = logging.getLogger("ai-service.realtime.dispatcher")

EventHandler = Callable[[OperationalEvent], Union[None, Awaitable[None]]]


class EventDispatcher:
    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Registers a callback handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Registers a callback handler for all events."""
        self._global_subscribers.append(handler)

    async def dispatch(self, event: OperationalEvent) -> None:
        """Dispatches an event to all subscribed handlers."""
        handlers = self._subscribers.get(event.event_type, []) + self._global_subscribers
        for handler in handlers:
            try:
                res = handler(event)
                if hasattr(res, "__await__"):
                    await res
            except Exception as e:
                logger.error(
                    f"Error in event handler '{handler.__name__}' for event {event.event_id}: {e}"
                )
