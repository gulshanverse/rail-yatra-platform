"""
Circuit Breaker Pattern (CLOSED, OPEN, HALF_OPEN) for Enterprise Integration Fault Isolation.
"""

import time
import logging
from typing import Callable, Any
from app.integrations.interfaces import CircuitState

logger = logging.getLogger("ai-service.integrations.resilience.circuit")


class CircuitBreakerOpenException(Exception):
    """Raised when an execution request is attempted while circuit is OPEN."""
    pass


class CircuitBreaker:
    def __init__(
        self,
        provider_id: str,
        failure_threshold: int = 5,
        recovery_seconds: float = 30.0,
    ) -> None:
        self.provider_id = provider_id
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_state_change: float = time.time()
        self.trip_count: int = 0

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes function wrapped inside circuit breaker state guards."""
        now = time.time()

        if self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_seconds:
                logger.info(f"Circuit for provider '{self.provider_id}' transitioning OPEN -> HALF_OPEN (Testing recovery).")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
            else:
                raise CircuitBreakerOpenException(f"Circuit breaker for provider '{self.provider_id}' is OPEN.")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit for provider '{self.provider_id}' transitioning HALF_OPEN -> CLOSED (Recovery successful).")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = now
            return result
        except Exception as exc:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.error(f"Circuit threshold ({self.failure_threshold}) reached. Tripping provider '{self.provider_id}' to OPEN.")
                    self.state = CircuitState.OPEN
                    self.last_state_change = now
                    self.trip_count += 1
            raise exc
