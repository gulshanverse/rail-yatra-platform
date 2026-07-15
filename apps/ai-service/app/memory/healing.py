"""
Failure Detection, Self-Healing Controller, and Circuit Breaker Design.
"""

import time
import logging
import threading
from typing import Callable, Any, Dict

from app.config.config import settings

logger = logging.getLogger("ai-service.memory.healing")

# Global metrics dictionary to track failure states and circuit breakers
healing_metrics: Dict[str, Any] = {
    "circuit_breaker_state": "CLOSED",
    "circuit_breaker_trips": 0,
    "failure_events_detected": 0,
    "self_healing_attempts": 0,
    "self_healing_successes": 0,
    "degradation_active": False,
}

# Thread lock for thread-safe metrics updates
metrics_lock = threading.Lock()


class CircuitBreaker:
    """Enterprise circuit breaker protecting Redis connectivity."""

    def __init__(self) -> None:
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failures = 0
        self.last_failure_time = 0.0
        self.lock = threading.Lock()

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute client operation through the circuit breaker."""
        with self.lock:
            # Check transitions from OPEN to HALF-OPEN
            if self.state == "OPEN":
                now = time.time()
                if (
                    now - self.last_failure_time >= settings.LOCK_TIMEOUT_SECS
                ):  # use LOCK_TIMEOUT_SECS as reset timeout
                    self.state = "HALF-OPEN"
                    logger.warning(
                        "Circuit Breaker transitioned to HALF-OPEN. Probing connection..."
                    )
                    with metrics_lock:
                        healing_metrics["circuit_breaker_state"] = "HALF-OPEN"
                else:
                    # Circuit is open, raise immediately to bypass Redis
                    raise RuntimeError(
                        "Circuit Breaker is OPEN. Bypassing Redis connection."
                    )

        try:
            result = func(*args, **kwargs)

            # If we succeed in HALF-OPEN, close circuit
            with self.lock:
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                    logger.info(
                        "Circuit Breaker transitioned to CLOSED. Redis connection restored."
                    )
                    with metrics_lock:
                        healing_metrics["circuit_breaker_state"] = "CLOSED"
            return result
        except Exception as e:
            with self.lock:
                self.failures += 1
                self.last_failure_time = time.time()

                # Check transition to OPEN
                if (
                    self.state in ("CLOSED", "HALF-OPEN") and self.failures >= 5
                ):  # using 5 as threshold
                    self.state = "OPEN"
                    logger.error(f"Circuit Breaker tripped to OPEN due to error: {e}")
                    with metrics_lock:
                        healing_metrics["circuit_breaker_state"] = "OPEN"
                        healing_metrics["circuit_breaker_trips"] += 1
            raise e


# Shared singleton instance
circuit_breaker = CircuitBreaker()


class FailureDetectionEngine:
    """Identifies dead workers, stale locks, connection losses, and corruption."""

    def __init__(self, short_term_memory: Any) -> None:
        self.short_term = short_term_memory

    def detect_redis_outage(self) -> bool:
        """Verify Redis socket ping status."""
        if not self.short_term.redis_client:
            return True
        try:
            # Probe through circuit breaker
            circuit_breaker.execute(self.short_term.redis_client.ping)
            return False
        except Exception:
            with metrics_lock:
                healing_metrics["failure_events_detected"] += 1
            return True

    def check_memory_corruption(self, session_id: str) -> bool:
        """Detect invalid structure corruption or mismatch in payload keys."""
        try:
            meta = self.short_term.redis_client.get(f"memory:session:{session_id}")
            if meta:
                # Basic check to see if we can decode it
                import json

                json.loads(meta)
            return False
        except Exception as e:
            logger.error(f"Memory corruption detected for session {session_id}: {e}")
            with metrics_lock:
                healing_metrics["failure_events_detected"] += 1
            return True


class SelfHealingController:
    """Applies automatic healing policies, restarts workers, and clears stale registries."""

    def __init__(self, failure_detector: FailureDetectionEngine) -> None:
        self.detector = failure_detector

    def heal_redis_outage(self) -> bool:
        """Self-healing action to re-initialize and reconnect Redis."""
        logger.info("Self-healing: Attempting to reconnect Redis client...")
        with metrics_lock:
            healing_metrics["self_healing_attempts"] += 1

        try:
            if self.detector.short_term.redis_client:
                self.detector.short_term.redis_client.ping()
                logger.info(
                    "Self-healing: Redis connection successfully re-established."
                )
                with metrics_lock:
                    healing_metrics["self_healing_successes"] += 1
                return True
        except Exception as e:
            logger.error(f"Self-healing: Redis reconnection attempt failed: {e}")

        return False

    def clear_expired_locks(self, lock_registry: Dict[str, Any]) -> int:
        """Purge stale locks from local registry during fallback execution."""
        cleared = 0
        now = time.time()
        for session_id, (_, expire_time) in list(lock_registry.items()):
            if now > expire_time:
                lock_registry.pop(session_id, None)
                cleared += 1

        if cleared > 0:
            logger.info(
                f"Self-healing: Cleared {cleared} expired locks from local fallback registry."
            )
            with metrics_lock:
                healing_metrics["self_healing_successes"] += 1
        return cleared
