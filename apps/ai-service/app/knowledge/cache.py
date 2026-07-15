"""
Knowledge Cache: Exact result matches and semantic similarity cache lookup with LRU eviction.
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional

from app.knowledge.interfaces import ISemanticCache
from app.knowledge.vector_store import cosine_similarity

logger = logging.getLogger("ai-service.knowledge.cache")


class SemanticCache(ISemanticCache):
    """Semantic vector cache avoiding duplicate search lookups."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 43200.0) -> None:
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}  # query_text -> Cache Entry
        self._lock = threading.Lock()

    def get(
        self, query: str, query_vector: List[float]
    ) -> Optional[List[Dict[str, Any]]]:
        now = time.time()

        with self._lock:
            # 1. Exact string match lookup
            if query in self._cache:
                entry = self._cache[query]
                if now < entry["expires_at"]:
                    entry["last_accessed"] = now
                    logger.info(f"Cache hit: exact query match for '{query}'")
                    return list(entry["results"])
                else:
                    self._cache.pop(query, None)

            # 2. Semantic vector distance lookup
            for cached_query, entry in list(self._cache.items()):
                if now > entry["expires_at"]:
                    self._cache.pop(cached_query, None)
                    continue

                sim = cosine_similarity(query_vector, entry["vector"])
                if sim >= 0.96:
                    entry["last_accessed"] = now
                    logger.info(
                        f"Cache hit: semantic similarity match for '{query}' (similarity: {sim:.3f})"
                    )
                    return list(entry["results"])

            return None

    def set(
        self, query: str, query_vector: List[float], results: List[Dict[str, Any]]
    ) -> None:
        now = time.time()

        with self._lock:
            # Enforce LRU eviction if cache size exceeded
            if len(self._cache) >= self.max_size:
                # Evict the oldest accessed item
                oldest_query = min(
                    self._cache.keys(), key=lambda k: self._cache[k]["last_accessed"]
                )
                self._cache.pop(oldest_query, None)
                logger.info(
                    f"Cache eviction: removed oldest query entry '{oldest_query}'"
                )

            self._cache[query] = {
                "vector": list(query_vector),
                "results": [dict(r) for r in results],
                "expires_at": now + self.ttl,
                "last_accessed": now,
            }
            logger.info(f"Cache set: cached results for query '{query}'")

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()
            logger.warning("Cache invalidation: cleared all semantic cache entries")

    def get_cache_size(self) -> int:
        """Returns the number of active entries currently cached."""
        with self._lock:
            return len(self._cache)
