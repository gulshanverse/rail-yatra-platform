# app/booking/events/publisher.py
import logging
from typing import Dict, Any
from app.booking.interfaces.contracts import IEventPublisher

logger = logging.getLogger("ai-service.booking.events")


class BookingEventPublisher(IEventPublisher):
    def __init__(self, message_broker: Any = None):
        self.message_broker = message_broker

    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        logger.info(f"PUBLISHING_BOOKING_EVENT name={name} payload={payload}")
        if self.message_broker:
            await self.message_broker.publish(name, payload)
