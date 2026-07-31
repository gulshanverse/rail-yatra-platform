"""
Provider Health Monitoring and Diagnostic Service.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.integrations.registry.provider_registry import ProviderRegistry


class ProviderMonitor:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def check_health(self) -> Dict[str, Any]:
        """Aggregates health diagnostics across all registered providers."""
        providers = self.registry.list_all_providers()
        total = len(providers)
        healthy = len([p for p in providers if p.status.value in ("HEALTHY", "ACTIVE", "REGISTERED", "INITIALIZED", "AUTHENTICATED")])
        degraded = len([p for p in providers if p.status.value == "DEGRADED"])
        unavailable = len([p for p in providers if p.status.value == "UNAVAILABLE"])

        overall_status = "HEALTHY"
        if unavailable > 0:
            overall_status = "DEGRADED"
        if unavailable > (total / 2) and total > 0:
            overall_status = "UNHEALTHY"

        return {
            "overall_status": overall_status,
            "total_providers": total,
            "healthy_count": healthy,
            "degraded_count": degraded,
            "unavailable_count": unavailable,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "providers": [p.health.model_dump() for p in providers],
        }
