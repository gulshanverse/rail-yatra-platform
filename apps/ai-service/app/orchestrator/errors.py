import asyncio
import logging
import random
from typing import Callable, Any, TypeVar, cast
from functools import wraps
from app.orchestrator.constants import (
    ERR_TIMEOUT,
    ERR_ROUTING,
    ERR_AGENT_EXECUTION,
    ERR_GRAPH_EXECUTION,
    ERR_UNKNOWN,
)

logger = logging.getLogger("ai-service.orchestrator.errors")

T = TypeVar("T", bound=Callable[..., Any])


class AIError(Exception):
    """Base exception for all AI platform errors."""

    def __init__(self, message: str, error_code: str = ERR_UNKNOWN):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class WorkflowTimeoutError(AIError):
    """Raised when execution of workflow exceeds timeout."""

    def __init__(self, message: str):
        super().__init__(message, error_code=ERR_TIMEOUT)


class RoutingError(AIError):
    """Raised when routing fails to resolve a valid agent."""

    def __init__(self, message: str):
        super().__init__(message, error_code=ERR_ROUTING)


class AgentExecutionError(AIError):
    """Raised when executing a specialist agent fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code=ERR_AGENT_EXECUTION)


class IntentClassificationError(AIError):
    """Raised when intent classification encounters errors."""

    def __init__(self, message: str):
        super().__init__(message, error_code=ERR_GRAPH_EXECUTION)


class GraphExecutionError(AIError):
    """Raised when the LangGraph workflow breaks internally."""

    def __init__(self, message: str):
        super().__init__(message, error_code=ERR_GRAPH_EXECUTION)


def retry_on_failure(
    retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0
):
    """
    Decorator that retries an async function upon exceptions with exponential backoff and jitter.
    """

    def decorator(func: T) -> T:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            delay = base_delay
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt > retries:
                        logger.error(
                            f"Function {func.__name__} failed after {retries} retries: {e}"
                        )
                        raise

                    # Apply jitter to delay calculation: delay = delay * backoff_factor + random jitter
                    jitter = random.uniform(0, 0.5)
                    sleep_time = (delay * (backoff_factor ** (attempt - 1))) + jitter
                    logger.warning(
                        f"Retrying async function '{func.__name__}' due to error: '{e}'. "
                        f"Attempt {attempt}/{retries}. Sleeping for {sleep_time:.2f}s."
                    )
                    await asyncio.sleep(sleep_time)

        return cast(T, wrapper)

    return decorator
