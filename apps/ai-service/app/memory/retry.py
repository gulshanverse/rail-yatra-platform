"""
Exponential backoff retry mechanism with random jitter for transient errors.
"""

import time
import random
import logging
from typing import Callable, Any, Tuple, Type
import redis

from app.memory.exceptions import ConcurrencyLockError
from app.config.config import settings

logger = logging.getLogger("ai-service.memory.retry")

# Explicit list of retryable transient exceptions
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConcurrencyLockError,
    redis.exceptions.ConnectionError,
    redis.exceptions.TimeoutError,
    ConnectionError,
)


class RetryPolicy:
    """Calculates and applies backoff retries for transient exceptions."""

    def __init__(
        self,
        max_attempts: int = None,
        base_delay: float = None,
        backoff_factor: float = None,
        jitter: bool = None,
    ):
        self.max_attempts = (
            max_attempts if max_attempts is not None else settings.LOCK_RETRY_ATTEMPTS
        )
        self.base_delay = (
            base_delay if base_delay is not None else settings.LOCK_RETRY_DELAY_SECS
        )
        self.backoff_factor = (
            backoff_factor
            if backoff_factor is not None
            else settings.LOCK_BACKOFF_FACTOR
        )
        self.jitter = jitter if jitter is not None else settings.LOCK_JITTER

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Executes the provided callable. If a transient error occurs,
        retries with exponential delay + jitter.
        """
        attempt = 1
        delay = self.base_delay

        while True:
            try:
                return func(*args, **kwargs)
            except RETRYABLE_EXCEPTIONS as e:
                if attempt >= self.max_attempts:
                    logger.error(
                        f"Retry attempts exhausted ({attempt}/{self.max_attempts}) for error: {e}"
                    )
                    raise

                jitter_val = random.uniform(0.0, 0.05) if self.jitter else 0.0
                sleep_time = delay + jitter_val
                logger.warning(
                    f"Transient failure encountered: {e}. "
                    f"Attempt {attempt}/{self.max_attempts} failed. Retrying in {sleep_time:.3f}s..."
                )
                time.sleep(sleep_time)

                attempt += 1
                delay = min(2.0, delay * self.backoff_factor)
