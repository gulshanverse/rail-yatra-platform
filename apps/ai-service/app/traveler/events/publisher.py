# app/traveler/events/publisher.py
import logging
from typing import Dict, Any
from app.traveler.interfaces.contracts import IEventPublisher

logger = logging.getLogger("ai-service.traveler.events")


class TravelerEventPublisher(IEventPublisher):
    def __init__(self, broker: Any = None):
        self.broker = broker

    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        logger.info(f"PUBLISHING_TRAVELER_EVENT name={name} payload={payload}")
        if self.broker:
            await self.broker.publish(name, payload)
