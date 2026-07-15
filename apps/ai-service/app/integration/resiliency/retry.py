# app/integration/resiliency/retry.py
import asyncio
import random
import logging
import inspect
from typing import Callable, Any

logger = logging.getLogger("ai-service.integration.resiliency.retry")


class RetryEngine:
    @staticmethod
    async def execute_with_retry(
        func: Callable[..., Any],
        *args,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 1.5,
        **kwargs,
    ) -> Any:
        """
        Executes a synchronous or asynchronous callable with exponential backoff and jitter.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_attempts} failed with: {e}")
                if attempt == max_attempts:
                    raise e
                # Calculate exponential backoff with jitter
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                jittered_delay = delay * (0.5 + random.random())
                await asyncio.sleep(jittered_delay)
