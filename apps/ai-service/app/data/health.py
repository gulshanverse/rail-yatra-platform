import logging
import time
from typing import Dict, Any

logger = logging.getLogger("ai-service.data.health")


class ProviderHealthMonitor:
    """
    Tracks consecutive request failures, response latencies, and offline states
    of registered Railway data adapters to coordinate automatic failover.
    """

    def __init__(self):
        # Health status matrix: provider_name -> status dict
        self._registry: Dict[str, Dict[str, Any]] = {
            "synthetic": {
                "status": "healthy",
                "consecutive_failures": 0,
                "last_checked": time.time(),
            },
            "irctc": {
                "status": "healthy",
                "consecutive_failures": 0,
                "last_checked": time.time(),
            },
            "ntes": {
                "status": "healthy",
                "consecutive_failures": 0,
                "last_checked": time.time(),
            },
        }

    def record_success(self, provider_name: str) -> None:
        """Resets consecutive failures on successful execution."""
        p_name = provider_name.lower()
        if p_name in self._registry:
            self._registry[p_name]["consecutive_failures"] = 0
            self._registry[p_name]["status"] = "healthy"
            self._registry[p_name]["last_checked"] = time.time()

    def record_failure(self, provider_name: str, threshold: int = 3) -> None:
        """Increments consecutive failures. Marks provider offline if threshold is crossed."""
        p_name = provider_name.lower()
        if p_name in self._registry:
            self._registry[p_name]["consecutive_failures"] += 1
            self._registry[p_name]["last_checked"] = time.time()

            failures = self._registry[p_name]["consecutive_failures"]
            if failures >= threshold:
                self._registry[p_name]["status"] = "offline"
                logger.warning(
                    f"Provider '{p_name}' has been marked OFFLINE due to {failures} consecutive failures."
                )

    def is_healthy(self, provider_name: str) -> bool:
        """Returns True if the provider status is healthy."""
        p_name = provider_name.lower()
        if p_name in self._registry:
            return self._registry[p_name]["status"] == "healthy"
        return False

    def get_status_report(self) -> Dict[str, Any]:
        """Returns the full health monitoring registry details."""
        return self._registry


provider_health_monitor = ProviderHealthMonitor()
