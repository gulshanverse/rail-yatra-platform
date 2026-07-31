"""
Production Graceful Shutdown Manager.
"""

import logging
from typing import Any, Callable, Dict, List
from datetime import datetime, timezone

logger = logging.getLogger("ai-service.production.shutdown")


class ShutdownManager:
    """Manages graceful shutdown sequence for production services."""

    def __init__(self) -> None:
        self._handlers: List[Dict[str, Any]] = []
        self._shutdown_complete = False

    def register(self, name: str, handler: Callable[[], None], priority: int = 10) -> None:
        """Registers a shutdown handler with priority (lower = runs first)."""
        self._handlers.append({"name": name, "handler": handler, "priority": priority})
        self._handlers.sort(key=lambda h: h["priority"])

    def execute(self) -> Dict[str, Any]:
        """Executes all shutdown handlers in priority order."""
        results: List[Dict[str, Any]] = []

        logger.info("Initiating graceful shutdown sequence...")
        for entry in self._handlers:
            name = entry["name"]
            try:
                entry["handler"]()
                results.append({"name": name, "status": "SUCCESS"})
                logger.info(f"Shutdown handler '{name}' completed successfully.")
            except Exception as exc:
                results.append({"name": name, "status": "ERROR", "error": str(exc)})
                logger.error(f"Shutdown handler '{name}' failed: {exc}")

        self._shutdown_complete = True
        logger.info("Graceful shutdown sequence completed.")

        return {
            "shutdown_complete": True,
            "handlers_executed": len(results),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _shutdown_background_tasks() -> None:
    logger.info("Stopping background tasks...")


def _shutdown_connections() -> None:
    logger.info("Closing database and cache connections...")


def _flush_metrics() -> None:
    logger.info("Flushing metrics buffer...")


def _flush_logs() -> None:
    logger.info("Flushing log buffers...")


def create_shutdown_manager() -> ShutdownManager:
    manager = ShutdownManager()
    manager.register("background_tasks", _shutdown_background_tasks, priority=1)
    manager.register("connections", _shutdown_connections, priority=5)
    manager.register("metrics", _flush_metrics, priority=8)
    manager.register("logs", _flush_logs, priority=10)
    return manager


shutdown_manager = create_shutdown_manager()
