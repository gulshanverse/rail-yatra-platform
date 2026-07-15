"""
Background Worker Framework and Worker Supervisor.
"""

import time
import logging
import threading
from typing import Dict, Any, List

from app.memory.health import health_metrics_store

logger = logging.getLogger("ai-service.memory.workers")


class BaseWorker(threading.Thread):
    """Abstract base worker implementing continuous loop execution and heartbeat metrics."""

    def __init__(self, name: str, interval_secs: float = 10.0) -> None:
        super().__init__(name=name, daemon=True)
        self.worker_name = name
        self.interval = interval_secs
        self.last_heartbeat = time.time()
        self.running = False
        self.crashed = False
        self.restart_count = 0

    def run(self) -> None:
        self.running = True
        logger.info(f"Worker {self.worker_name} started.")

        while self.running:
            try:
                self.last_heartbeat = time.time()
                self.execute_task()
            except Exception as e:
                logger.error(f"Worker {self.worker_name} task failed: {e}")
                self.running = False
                self.crashed = True
                break

            time.sleep(self.interval)

        logger.info(f"Worker {self.worker_name} loop terminated.")

    def stop(self) -> None:
        self.running = False

    def execute_task(self) -> None:
        raise NotImplementedError("Subclasses must implement execute_task.")


class TTLCleanupWorker(BaseWorker):
    """Sweeps and purges expired sessions from memory cache."""

    def execute_task(self) -> None:
        logger.debug("TTL Sweep: Evicting expired session cache records...")
        cleared = 0

        from app.memory.short_term import short_term_memory
        fallback = short_term_memory.fallback_store
        from app.memory.session import ConversationSessionMetadata
        from app.memory.serializer import MemorySerializer
        from app.memory.ttl import TTLEngine

        with fallback._lock:
            for session_id, meta_json in list(fallback._meta.items()):
                try:
                    meta_obj = MemorySerializer.deserialize(
                        meta_json, ConversationSessionMetadata
                    )
                    if TTLEngine.is_expired(meta_obj):
                        fallback._meta.pop(session_id, None)
                        fallback._sessions.pop(session_id, None)
                        user_id = meta_obj.user_id
                        if user_id in fallback._user_indexes:
                            fallback._user_indexes[user_id].discard(session_id)
                        cleared += 1
                except Exception as e:
                    logger.error(f"TTL Sweep error parsing session {session_id}: {e}")

        if cleared > 0:
            logger.info(f"TTL Sweep: Evicted {cleared} expired sessions from fallback.")
            health_metrics_store["session_cleanup_count"] += cleared


class LockCleanupWorker(BaseWorker):
    """Sweeps and force-releases orphaned or dead locks."""

    def execute_task(self) -> None:
        logger.debug("Lock Sweep: Clearing orphaned distributed lock keys...")
        now = time.time()
        cleared = 0

        # Sweep local lock registry
        from app.memory.locks import in_memory_locks_registry, in_memory_locks_mutex

        with in_memory_locks_mutex:
            for session_id, (_, expire_time) in list(in_memory_locks_registry.items()):
                if now > expire_time:
                    in_memory_locks_registry.pop(session_id, None)
                    cleared += 1

        # Sweep Redis lock keys if Redis is active
        from app.memory.short_term import short_term_memory
        if short_term_memory.redis_client:
            try:
                # Scan lock keys in Redis
                keys = short_term_memory.redis_client.keys("memory:lock:*")
                for key in keys:
                    # If TTL of key has expired, delete it (handled by Redis expire usually, but let's check)
                    ttl = short_term_memory.redis_client.ttl(key)
                    if ttl <= 0:
                        short_term_memory.redis_client.delete(key)
                        cleared += 1
            except Exception:
                pass

        if cleared > 0:
            logger.info(f"Lock Sweep: Force-released {cleared} orphaned session locks.")
            health_metrics_store["lock_cleanup_count"] += cleared


class WorkerSupervisor(threading.Thread):
    """Supervises active worker threads, validating heartbeats, and restarting crashed loop tasks."""

    def __init__(self) -> None:
        super().__init__(name="worker-supervisor", daemon=True)
        self.workers: Dict[str, BaseWorker] = {}
        self.quarantine: List[str] = []
        self.lock = threading.Lock()
        self.running = False

    def register_worker(
        self, worker_class: Any, name: str, interval: float = 10.0
    ) -> None:
        with self.lock:
            worker = worker_class(name, interval)
            self.workers[name] = worker

    def start_all_workers(self) -> None:
        self.running = True
        super().start()
        with self.lock:
            for worker in self.workers.values():
                worker.start()

    def stop_all_workers(self) -> None:
        self.running = False
        with self.lock:
            for worker in self.workers.values():
                worker.stop()

    def run(self) -> None:
        logger.info("Worker Supervisor monitoring loop started.")

        while self.running:
            time.sleep(5.0)  # validate loop status every 5 seconds
            with self.lock:
                now = time.time()
                for name, worker in list(self.workers.items()):
                    if name in self.quarantine:
                        continue

                    # Check thread heartbeat or crashed flag
                    drift = now - worker.last_heartbeat
                    is_crashed = worker.crashed or (
                        not worker.is_alive() and worker.running
                    )

                    if is_crashed or drift > (worker.interval * 3.0):
                        logger.error(
                            f"Supervisor detected unhealthy worker {name} (drift: {drift:.1f}s, crashed: {is_crashed}). Restarting..."
                        )

                        # Stop and prepare clean instance
                        try:
                            worker.stop()
                        except Exception:
                            pass

                        # Check restart count
                        worker.restart_count += 1
                        health_metrics_store["worker_restart_count"] += 1

                        if worker.restart_count > 3:
                            logger.critical(
                                f"Worker {name} has crashed too many times! Quarantined."
                            )
                            self.quarantine.append(name)
                            continue

                        # Replace and launch new thread
                        new_worker = type(worker)(name, worker.interval)
                        new_worker.restart_count = worker.restart_count
                        self.workers[name] = new_worker
                        new_worker.start()

    def get_workers_status(self) -> Dict[str, Any]:
        with self.lock:
            status_map = {}
            for name, w in self.workers.items():
                status_map[name] = {
                    "running": w.is_alive(),
                    "restart_count": w.restart_count,
                    "last_heartbeat_ago": time.time() - w.last_heartbeat,
                    "quarantined": name in self.quarantine,
                }
            return {
                "active_workers": len(self.workers),
                "details": status_map,
                "quarantine_list": self.quarantine,
            }


# Shared singleton instance
supervisor = WorkerSupervisor()
supervisor.register_worker(TTLCleanupWorker, "ttl-cleanup", interval=2.0)
supervisor.register_worker(LockCleanupWorker, "lock-cleanup", interval=2.0)
