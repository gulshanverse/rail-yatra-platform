import logging
import json
import redis
from typing import List, Dict, Any, Optional
from app.config.config import settings

logger = logging.getLogger("ai-service.memory.short_term")

class ShortTermMemory:
    """
    Manages short-term conversation context and sliding-window memory in Redis.
    Falls back gracefully to a local dictionary cache if Redis is unavailable.
    """
    def __init__(self):
        self._local_cache: Dict[str, Any] = {}
        self.redis_client = None
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis for short-term memory.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Falling back to in-memory cache.")
            self.redis_client = None

    def save_session_context(self, session_id: str, context_data: Dict[str, Any], expire_seconds: int = 3600) -> None:
        """Saves current state metrics or search criteria for a chat session."""
        key = f"session:{session_id}:context"
        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(context_data), ex=expire_seconds)
                return
            except Exception as e:
                logger.error(f"Redis save_session_context error: {e}")
        
        # Local fallback
        self._local_cache[key] = {
            "value": context_data,
            "expiry": time.time() + expire_seconds if hasattr(time, "time") else 0
        }

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieves cached state context or returns an empty dictionary."""
        key = f"session:{session_id}:context"
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get_session_context error: {e}")

        # Local fallback
        cached = self._local_cache.get(key)
        if cached:
            return cached["value"]
        return {}

    def add_message(self, session_id: str, role: str, content: str, limit: int = 20) -> None:
        """Adds a message to the sliding window history."""
        key = f"session:{session_id}:history"
        msg = {"role": role, "content": content, "timestamp": time.time() if hasattr(time, "time") else 0}
        
        if self.redis_client:
            try:
                # Add to right of list
                self.redis_client.rpush(key, json.dumps(msg))
                # Trim list to sliding window limit
                self.redis_client.ltrim(key, -limit, -1)
                # Set expiration
                self.redis_client.expire(key, 86400) # 24 hours expiry
                return
            except Exception as e:
                logger.error(f"Redis add_message error: {e}")

        # Local fallback
        if key not in self._local_cache:
            self._local_cache[key] = []
        history = self._local_cache[key]
        history.append(msg)
        if len(history) > limit:
            self._local_cache[key] = history[-limit:]

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns the list of messages in the short-term sliding window."""
        key = f"session:{session_id}:history"
        if self.redis_client:
            try:
                items = self.redis_client.lrange(key, 0, -1)
                return [json.loads(i) for i in items]
            except Exception as e:
                logger.error(f"Redis get_history error: {e}")

        # Local fallback
        return self._local_cache.get(key, [])

short_term_memory = ShortTermMemory()
import time # imported here to support local fallback timestamp checks
