# app/personalization/cache/manager.py
import logging
from typing import Any, Optional
from app.personalization.interfaces.contracts import ICacheManager, ICacheRepository

logger = logging.getLogger(__name__)


class CacheManager(ICacheManager):
    def __init__(self, cache_repository: ICacheRepository) -> None:
        self._cache_repo = cache_repository

    def get(self, cache_name: str, key: str) -> Optional[Any]:
        cache_key = f"{cache_name}:{key}"
        val = self._cache_repo.get(cache_key)
        logger.debug(
            "Cache get cache_name=%s key=%s hit=%s", cache_name, key, val is not None
        )
        return val

    def put(self, cache_name: str, key: str, value: Any, ttl_seconds: int) -> None:
        cache_key = f"{cache_name}:{key}"
        self._cache_repo.set(cache_key, value, ttl_seconds)
        logger.debug(
            "Cache put cache_name=%s key=%s ttl=%s", cache_name, key, ttl_seconds
        )

    def invalidate(self, cache_name: str, key: str) -> None:
        cache_key = f"{cache_name}:{key}"
        self._cache_repo.delete(cache_key)
        logger.debug("Cache invalidate cache_name=%s key=%s", cache_name, key)

    def invalidate_all(self, cache_name: str) -> None:
        if hasattr(self._cache_repo, "_cache"):
            internal_cache = getattr(self._cache_repo, "_cache")
            prefix = f"{cache_name}:"
            keys_to_del = [k for k in internal_cache.keys() if k.startswith(prefix)]
            for k in keys_to_del:
                del internal_cache[k]
        logger.info("Cache invalidate_all cache_name=%s", cache_name)
