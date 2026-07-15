# app/journey/events/publisher.py
import logging
from typing import Dict, Any
from app.journey.interfaces.contracts import IEventPublisher

logger = logging.getLogger("ai-service.journey.events")


class JourneyEventPublisher(IEventPublisher):
    def __init__(self, message_broker: Any = None):
        self.message_broker = message_broker

    async def publish_journey_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> None:
        logger.info(f"PUBLISHING_DOMAIN_EVENT type={event_type} payload={payload}")
        
        # Publish event downstream if message broker is connected
        if self.message_broker:
            await self.message_broker.publish(event_type, payload)
        
        # System event loop propagation hook
        # Emit event updates asynchronously
        pass
