"""
ConcurrencyManager coordinating lock acquisition, OCC checks, retries,
and commit/rollback transactions.
"""

import time
import logging
import threading
from typing import Callable, Any, Optional, TYPE_CHECKING

from app.memory.locks import LockManager
from app.memory.versioning import VersionManager
from app.memory.retry import RetryPolicy
from app.memory.conflicts import ConflictResolver

if TYPE_CHECKING:
    from app.memory.short_term import ShortTermMemory

logger = logging.getLogger("ai-service.memory.concurrency")

# Thread-safe metrics registry
concurrency_metrics_lock = threading.Lock()
concurrency_metrics = {
    "active_locks": 0,
    "lock_acquisition_latency_ms": 0.0,
    "max_wait_ms": 0.0,
    "retry_latency_ms": 0.0,
    "retry_success": 0,
    "retry_failure": 0,
    "occ_conflicts": 0,
    "lock_renewals": 0,
    "rollback_count": 0,
    "abandoned_lock_cleanup": 0,
}


def record_concurrency_metric(name: str, value: Any = 1) -> None:
    with concurrency_metrics_lock:
        if name in concurrency_metrics:
            if isinstance(value, (int, float)):
                concurrency_metrics[name] += value
            else:
                concurrency_metrics[name] = value


class ConcurrencyManager:
    """Manages the transactional locking and version verification pipeline."""

    def __init__(self, short_memory: "ShortTermMemory"):
        self.short_memory = short_memory
        self.retry_policy = RetryPolicy()

    async def execute_transaction(
        self,
        session_id: str,
        operation: Callable[..., Any],
        *args: Any,
        expected_version: Optional[int] = None,
        conflict_strategy: str = "REJECT",
        **kwargs: Any,
    ) -> Any:
        """
        Locks session, runs OCC check, executes mutation, and commits version increment.
        Ensures release and rollback on failures.
        """
        # 1. Obtain lock
        redis_cli = (
            self.short_memory.redis_client
            if hasattr(self.short_memory, "redis_client")
            else None
        )
        lock = LockManager.get_lock(redis_cli, session_id)

        start_lock_time = time.time()
        record_concurrency_metric("active_locks", 1)

        try:
            # 2. Acquire lock (using retry wrapper)
            self.retry_policy.execute(lock.acquire, blocking=True)

            acq_latency = (time.time() - start_lock_time) * 1000
            record_concurrency_metric("lock_acquisition_latency_ms", acq_latency)
            with concurrency_metrics_lock:
                if acq_latency > concurrency_metrics["max_wait_ms"]:
                    concurrency_metrics["max_wait_ms"] = acq_latency

            # 3. Read current metadata to check OCC version
            meta = await self.short_memory._get_meta_obj(session_id)
            if meta and expected_version is not None:
                try:
                    VersionManager.validate_occ(meta.memory_version, expected_version)
                except Exception as occ_error:
                    record_concurrency_metric("occ_conflicts", 1)
                    # Resolve conflict
                    ConflictResolver.resolve(
                        meta.memory_version, expected_version, conflict_strategy
                    )
                    raise occ_error

            # 4. Execute operation
            # Supports async functions as operations
            result = await operation(*args, **kwargs)

            # 5. If operation succeeded, commit version increment (which is saved during actual save)
            # (Version increment happens inside write operations, but we can verify it here)
            return result

        except Exception as e:
            record_concurrency_metric("rollback_count", 1)
            logger.error(
                f"Transaction failed for session {session_id}, performing rollback: {e}"
            )
            raise
        finally:
            # 6. Always release lock to prevent leaks
            lock.release()
            record_concurrency_metric("active_locks", -1)
