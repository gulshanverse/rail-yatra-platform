# app/integration/resiliency/health.py
import time
import logging
from typing import Dict
from app.integration.interfaces import IProviderRegistry

logger = logging.getLogger("ai-service.integration.resiliency.health")


class HealthMonitor:
    def __init__(self, registry: IProviderRegistry):
        self.registry = registry
        self._provider_health_scores: Dict[
            str, float
        ] = {}  # provider_id -> score (0.0 to 100.0)
        self._last_active_probes: Dict[str, float] = {}  # provider_id -> timestamp

    def record_heartbeat(
        self, provider_id: str, latency_ms: float, success: bool
    ) -> None:
        """
        Passive check hook to calculate health score based on requests.
        """
        current_score = self._provider_health_scores.get(provider_id, 100.0)

        # Simple moving average health computation
        factor = 0.1
        success_val = 100.0 if success else 0.0
        new_score = (current_score * (1.0 - factor)) + (success_val * factor)

        self._provider_health_scores[provider_id] = round(new_score, 2)

        # Dynamically transition statuses
        if new_score < 50.0:
            self.registry.update_provider_status(provider_id, "offline")
            logger.error(
                f"Provider {provider_id} marked OFFLINE (Health score: {new_score}%)"
            )
        elif new_score >= 80.0:
            # Check current status, if offline promote to active
            for p in self.registry.list_all_providers():
                if p.provider_id == provider_id and p.status == "offline":
                    self.registry.update_provider_status(provider_id, "active")
                    logger.info(
                        f"Provider {provider_id} recovered and marked ACTIVE (Health score: {new_score}%)"
                    )

    async def run_active_probe(self, provider_id: str, probe_func) -> bool:
        """
        Dispatches a simple active probe to check if provider has recovered.
        """
        now = time.time()
        self._last_active_probes[provider_id] = now
        logger.info(f"Running active health probe for: {provider_id}")

        try:
            success = await probe_func()
            self.record_heartbeat(provider_id, 50.0, success)
            return success
        except Exception as e:
            logger.warning(f"Active health probe failed for {provider_id}: {e}")
            self.record_heartbeat(provider_id, 0.0, False)
            return False

    def get_health_score(self, provider_id: str) -> float:
        return self._provider_health_scores.get(provider_id, 100.0)
