"""
Exponential Backoff Retry Engine for Enterprise Integration Providers.
"""

import time
import logging
from typing import Callable, Any

logger = logging.getLogger("ai-service.integrations.resilience.retry")


class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def execute_with_retry(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes a function with exponential backoff retries on failure."""
        attempts = 0
        last_exception = None

        while attempts <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                attempts += 1
                last_exception = exc
                if attempts > self.max_retries:
                    logger.error(f"Retry limit ({self.max_retries}) reached. Error: {exc}")
                    raise exc

                sleep_time = self.backoff_factor ** (attempts - 1)
                logger.warning(f"Retry attempt {attempts}/{self.max_retries} failed. Retrying in {sleep_time:.2f}s. Error: {exc}")
                time.sleep(sleep_time)

        if last_exception:
            raise last_exception
