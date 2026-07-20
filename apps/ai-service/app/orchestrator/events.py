import logging
import time
import uuid
from typing import Dict, Any, List, Callable, Coroutine

logger = logging.getLogger("ai-service.orchestrator.events")


class AIEvent:
    """
    Standardized event contract carried across the internal Event Bus.
    """

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        trace_id: str,
        correlation_id: str,
        sender: str = "orchestrator",
    ) -> None:
        self.event_id: str = f"evt-{uuid.uuid4().hex[:12]}"
        self.event_type: str = event_type
        self.payload: Dict[str, Any] = payload
        self.trace_id: str = trace_id
        self.correlation_id: str = correlation_id
        self.sender: str = sender
        self.timestamp: float = time.time()


class EventBus:
    """
    Decoupled Event Bus enabling publish-subscribe communication.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[
            str, List[Callable[[AIEvent], Coroutine[Any, Any, None]]]
        ] = {}

    def subscribe(
        self, event_type: str, callback: Callable[[AIEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Registers a subscriber callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed callback to event type: {event_type}")

    async def publish(self, event: AIEvent) -> None:
        """Publishes an event asynchronously to all registered subscribers."""
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                await callback(event)
            except Exception as e:
                logger.error(
                    f"Error in subscriber callback for event {event.event_id} ({event.event_type}): {e}",
                    exc_info=True,
                )


# Global singleton Event Bus
event_bus = EventBus()
