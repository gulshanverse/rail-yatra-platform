# app/booking/cache/manager.py
from typing import Dict, Any, Optional
from app.booking.interfaces.contracts import ICacheManager


class BookingCacheManager(ICacheManager):
    def __init__(self, redis_client: Any = None):
        self.redis_client = redis_client
        self._local_cache = {}

    async def get_cached_recommendation(self, key: str) -> Optional[Dict[str, Any]]:
        if self.redis_client:
            # Simulated Redis read
            return await self.redis_client.get(key)
        return self._local_cache.get(key)

    async def cache_recommendation(
        self, key: str, data: Dict[str, Any], ttl: int
    ) -> None:
        if self.redis_client:
            # Simulated Redis set
            await self.redis_client.set(key, data, ttl)
        else:
            self._local_cache[key] = data
