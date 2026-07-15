# app/intelligence/events.py
import json
import logging
from typing import Dict, Any
from app.intelligence.interfaces import IRailwayEventEngine

logger = logging.getLogger("ai-service.intelligence.events")


class RailwayEventEngine(IRailwayEventEngine):
    def __init__(self, redis_client=None):
        self.redis_client = redis_client

    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        event_channel = f"railway:events:{event_type}"
        event_data = {
            "event_type": event_type,
            "payload": payload,
            "channel": event_channel,
        }

        # Log event publication
        logger.info(
            f"Publishing canonical event '{event_type}' to channel '{event_channel}'"
        )

        if self.redis_client:
            try:
                # Publish to Redis channel
                self.redis_client.publish(event_channel, json.dumps(event_data))
            except Exception as e:
                logger.warning(f"Failed to publish event to Redis pub/sub: {e}")
        else:
            # Fallback to local memory log
            pass
