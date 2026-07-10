import logging
import json
import time
from typing import Optional, Any
from app.memory.short_term import short_term_memory # Reuse Redis connection checks from short term memory

logger = logging.getLogger("ai-service.data.cache")

class RailwayCacheManager:
    """
    Intelligent caching layer that stores normalized JSON models in Redis.
    Supports TTL expiration policies based on data mutability (e.g. schedules vs PNRs).
    """
    def __init__(self):
        # We reuse the redis connection check from short_term_memory
        self.redis_client = short_term_memory.redis_client
        self._local_cache: dict = {}

    def _get_ttl(self, data_type: str) -> int:
        # Time-To-Live mappings in seconds
        ttls = {
            "pnr": 120,          # 2 minutes (highly mutable)
            "availability": 600, # 10 minutes
            "delay": 3600,       # 1 hour
            "schedule": 86400,   # 24 hours
            "station": 604800    # 7 days (mostly static)
        }
        return ttls.get(data_type.lower(), 300)

    def set(self, data_type: str, key_id: str, value: Any) -> None:
        """Saves value to Redis or local memory dictionary with data-specific TTL."""
        ttl = self._get_ttl(data_type)
        cache_key = f"cache:{data_type}:{key_id}"
        serialized = json.dumps(value)
        
        if self.redis_client:
            try:
                self.redis_client.set(cache_key, serialized, ex=ttl)
                return
            except Exception as e:
                logger.error(f"Redis cache set failure: {e}")
                
        # Local fallback
        self._local_cache[cache_key] = {
            "data": serialized,
            "expiry": time.time() + ttl
        }

    def get(self, data_type: str, key_id: str) -> Optional[Any]:
        """Gets value from cache if it exists and has not expired."""
        cache_key = f"cache:{data_type}:{key_id}"
        
        if self.redis_client:
            try:
                val = self.redis_client.get(cache_key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error(f"Redis cache get failure: {e}")

        # Local fallback check
        cached = self._local_cache.get(cache_key)
        if cached:
            if time.time() < cached["expiry"]:
                return json.loads(cached["data"])
            else:
                del self._local_cache[cache_key] # remove expired
        return None

railway_cache_manager = RailwayCacheManager()
