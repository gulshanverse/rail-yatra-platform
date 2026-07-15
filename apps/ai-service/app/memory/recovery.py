"""
Recovery Manager, Memory Synchronizer, Priority Queue, and Audit Trail.
"""

import time
import logging
import heapq
import threading
from typing import Dict, List, Any, Optional


logger = logging.getLogger("ai-service.memory.recovery")

# Thread-safe audit trail list
audit_trail_store: List[Dict[str, Any]] = []
audit_lock = threading.Lock()


class RecoveryAuditTrail:
    """Records full recovery and self-healing action history."""

    @staticmethod
    def log_event(
        component: str,
        reason: str,
        duration_ms: float,
        success: bool,
        rollback: bool = False,
        manual_intervention: bool = False,
    ) -> None:
        event = {
            "timestamp": time.time(),
            "component": component,
            "reason": reason,
            "duration_ms": duration_ms,
            "success": success,
            "rollback": rollback,
            "manual_intervention": manual_intervention,
        }
        with audit_lock:
            audit_trail_store.append(event)
            logger.info(f"Audit Logged [{component}]: {reason} - Success: {success}")

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        with audit_lock:
            return list(audit_trail_store)


class RecoveryPriorityQueue:
    """Schedules session restoration tasks according to priority tiers."""

    # Priority values: lower numbers mean higher priority
    PRIORITIES = {
        "critical": 1,
        "premium": 2,
        "authenticated": 3,
        "anonymous": 4,
        "background": 5,
    }

    def __init__(self) -> None:
        self.queue: List[tuple] = []
        self.lock = threading.Lock()

    def push_session(self, session_id: str, tier: str = "authenticated") -> None:
        priority = self.PRIORITIES.get(tier.lower(), 3)
        with self.lock:
            # heapq tracks tuples (priority, timestamp, session_id)
            heapq.heappush(self.queue, (priority, time.time(), session_id))

    def pop_session(self) -> Optional[str]:
        with self.lock:
            if not self.queue:
                return None
            _, _, session_id = heapq.heappop(self.queue)
            return session_id

    def is_empty(self) -> bool:
        with self.lock:
            return len(self.queue) == 0


class MemorySynchronizer:
    """Handles incremental reconciliation between local fallback cache and Redis."""

    def __init__(self, short_term_memory: Any) -> None:
        self.short_term = short_term_memory

    def sync_session_to_redis(
        self, session_id: str, local_data: Dict[str, Any]
    ) -> bool:
        """Pushes local fallback data to Redis using version reconciliation."""
        if not self.short_term.redis_client:
            return False

        redis_key = f"memory:session:{session_id}"
        try:
            # Fetch remote version
            remote_raw = self.short_term.redis_client.get(redis_key)
            remote_version = 0

            if remote_raw:
                try:
                    import json

                    remote_parsed = json.loads(remote_raw)
                    remote_version = remote_parsed.get("memory_version", 0)
                except Exception:
                    pass

            local_version = local_data.get("memory_version", 0)

            # Simple reconciliation: Last Write Wins based on memory_version increment
            if local_version >= remote_version:
                # Local has newer or same data, update Redis
                import json

                self.short_term.redis_client.set(redis_key, json.dumps(local_data))
                logger.info(
                    f"Reconciliation: Synced session {session_id} to Redis (Local version {local_version} >= Remote {remote_version})"
                )
                return True
            else:
                # Remote has newer data, ignore local synchronization
                logger.info(
                    f"Reconciliation: Ignored session {session_id} sync (Local version {local_version} < Remote {remote_version})"
                )
                return False
        except Exception as e:
            logger.error(f"Sync failed for session {session_id}: {e}")
            return False


class RecoveryManager:
    """Coordinates overall connection restorations and queue draining."""

    def __init__(self, short_term_memory: Any) -> None:
        self.short_term = short_term_memory
        self.synchronizer = MemorySynchronizer(short_term_memory)
        self.priority_queue = RecoveryPriorityQueue()

    def run_restoration_cycle(self, local_cache: Dict[str, Any]) -> int:
        """Drains the restoration queue and reconciles sessions back to Redis."""
        start_time = time.time()
        restored = 0

        while not self.priority_queue.is_empty():
            session_id = self.priority_queue.pop_session()
            if not session_id:
                continue

            local_data = local_cache.get(session_id)
            if local_data:
                success = self.synchronizer.sync_session_to_redis(
                    session_id, local_data
                )
                if success:
                    restored += 1

        duration_ms = (time.time() - start_time) * 1000
        if restored > 0:
            RecoveryAuditTrail.log_event(
                component="RecoveryManager",
                reason=f"Restored {restored} sessions from fallback priority queue.",
                duration_ms=duration_ms,
                success=True,
            )

        return restored
