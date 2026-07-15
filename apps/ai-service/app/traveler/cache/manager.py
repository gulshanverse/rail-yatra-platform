# app/traveler/cache/manager.py
from typing import Dict, Any, Optional
from app.traveler.interfaces.contracts import ICacheManager


class TravelerCacheManager(ICacheManager):
    def __init__(self, redis_client: Any = None):
        self.redis_client = redis_client
        self._local: Dict[str, Dict[str, Any]] = {}

    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        if self.redis_client:
            return await self.redis_client.get(key)
        return self._local.get(key)

    async def set_cached(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        if self.redis_client:
            await self.redis_client.set(key, data, ttl)
        else:
            self._local[key] = data
