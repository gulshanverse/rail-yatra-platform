"""
Distributed locking implementations utilizing Redis (with Lua checks)
and an in-memory thread-safe fallback.
"""

import time
import uuid
import logging
import threading
from typing import Dict, Tuple, Optional
import redis

from app.memory.exceptions import ConcurrencyLockError
from app.config.config import settings

logger = logging.getLogger("ai-service.memory.locks")

# Atomic release script: only deletes the lock key if the token matches
LUA_RELEASE = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# Atomic renew script: updates key expire time if the token matches
LUA_RENEW = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("pexpire", KEYS[1], ARGV[2])
else
    return 0
end
"""


class BaseLock:
    """Interface contract for concurrency locks."""

    def __init__(
        self, session_id: str, owner_token: Optional[str] = None, ttl_secs: float = 5.0
    ):
        self.session_id = session_id
        self.owner_token = owner_token or uuid.uuid4().hex
        self.ttl_secs = ttl_secs

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        raise NotImplementedError()

    def release(self) -> bool:
        raise NotImplementedError()

    def renew(self, additional_ttl: float = 5.0) -> bool:
        raise NotImplementedError()


class RedisDistributedLock(BaseLock):
    """Redis-backed distributed lock with atomic Lua validations."""

    def __init__(
        self,
        redis_client: redis.Redis,
        session_id: str,
        owner_token: Optional[str] = None,
        ttl_secs: float = 5.0,
    ):
        super().__init__(session_id, owner_token, ttl_secs)
        self.client = redis_client
        self.lock_key = f"memory:lock:{session_id}"

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        px = int(self.ttl_secs * 1000)
        # Attempt to set NX
        acquired = bool(
            self.client.set(self.lock_key, self.owner_token, nx=True, px=px)
        )
        if acquired:
            return True

        if not blocking:
            return False

        # Blocking retry loop
        max_wait = timeout if timeout is not None else settings.LOCK_TIMEOUT_SECS
        start_time = time.time()
        retry_delay = settings.LOCK_RETRY_DELAY_SECS
        backoff = settings.LOCK_BACKOFF_FACTOR

        while (time.time() - start_time) < max_wait:
            jitter = time.time() % 0.05 if settings.LOCK_JITTER else 0.0
            sleep_time = retry_delay + jitter
            time.sleep(sleep_time)

            acquired = bool(
                self.client.set(self.lock_key, self.owner_token, nx=True, px=px)
            )
            if acquired:
                return True

            retry_delay = min(1.0, retry_delay * backoff)

        raise ConcurrencyLockError(
            f"Lock acquisition timed out for session {self.session_id}"
        )

    def release(self) -> bool:
        try:
            res = self.client.eval(LUA_RELEASE, 1, self.lock_key, self.owner_token)
            return bool(res)
        except Exception as e:
            logger.warning(f"Redis release error on key {self.lock_key}: {e}")
            return False

    def renew(self, additional_ttl: float = 5.0) -> bool:
        px = int(additional_ttl * 1000)
        try:
            res = self.client.eval(LUA_RENEW, 1, self.lock_key, self.owner_token, px)
            return bool(res)
        except Exception as e:
            logger.warning(f"Redis renew error on key {self.lock_key}: {e}")
            return False


# In-memory thread-safe lock manager fallback
in_memory_locks_mutex = threading.Lock()
in_memory_locks_registry: Dict[
    str, Tuple[str, float]
] = {}  # session_id -> (owner_token, expire_timestamp)


class InMemoryDistributedLock(BaseLock):
    """Local fallback memory lock manager using a global thread-safe registry."""

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        max_wait = timeout if timeout is not None else settings.LOCK_TIMEOUT_SECS
        start_time = time.time()
        retry_delay = settings.LOCK_RETRY_DELAY_SECS
        backoff = settings.LOCK_BACKOFF_FACTOR

        while True:
            now = time.time()
            with in_memory_locks_mutex:
                # Expired check
                if self.session_id in in_memory_locks_registry:
                    _, expire_time = in_memory_locks_registry[self.session_id]
                    if now > expire_time:
                        in_memory_locks_registry.pop(self.session_id, None)

                # Check occupancy
                if self.session_id not in in_memory_locks_registry:
                    in_memory_locks_registry[self.session_id] = (
                        self.owner_token,
                        now + self.ttl_secs,
                    )
                    return True

            if not blocking:
                return False

            if (time.time() - start_time) >= max_wait:
                raise ConcurrencyLockError(
                    f"In-memory lock acquisition timed out for session {self.session_id}"
                )

            jitter = time.time() % 0.05 if settings.LOCK_JITTER else 0.0
            time.sleep(retry_delay + jitter)
            retry_delay = min(1.0, retry_delay * backoff)

    def release(self) -> bool:
        with in_memory_locks_mutex:
            if self.session_id in in_memory_locks_registry:
                owner, _ = in_memory_locks_registry[self.session_id]
                if owner == self.owner_token:
                    in_memory_locks_registry.pop(self.session_id, None)
                    return True
            return False

    def renew(self, additional_ttl: float = 5.0) -> bool:
        with in_memory_locks_mutex:
            if self.session_id in in_memory_locks_registry:
                owner, _ = in_memory_locks_registry[self.session_id]
                if owner == self.owner_token:
                    in_memory_locks_registry[self.session_id] = (
                        self.owner_token,
                        time.time() + additional_ttl,
                    )
                    return True
            return False


class LockManager:
    """Lock factory matching Redis state availability."""

    @staticmethod
    def get_lock(
        redis_client: Optional[redis.Redis],
        session_id: str,
        owner_token: Optional[str] = None,
        ttl_secs: float = 5.0,
    ) -> BaseLock:
        if redis_client is not None:
            try:
                redis_client.ping()
                return RedisDistributedLock(
                    redis_client, session_id, owner_token, ttl_secs
                )
            except Exception:
                pass
        return InMemoryDistributedLock(session_id, owner_token, ttl_secs)
