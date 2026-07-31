"""
Telemetry Metrics and Diagnostic Counters for Integration Services.
"""

from typing import Any, Dict
from datetime import datetime, timezone
from app.integrations.interfaces import IntegrationDomain
from app.integrations.models import IntegrationMetric


class IntegrationMetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, IntegrationMetric] = {}

    def record_request(
        self,
        provider_id: str,
        domain: IntegrationDomain,
        latency_ms: float,
        success: bool,
        retried: bool = False,
        circuit_tripped: bool = False,
    ) -> IntegrationMetric:
        """Records telemetry for an execution request."""
        now_str = datetime.now(timezone.utc).isoformat()
        existing = self._metrics.get(provider_id)

        if not existing:
            total = 1
            succ = 1 if success else 0
            failed = 0 if success else 1
            retries = 1 if retried else 0
            avg_lat = latency_ms
            trips = 1 if circuit_tripped else 0
        else:
            total = existing.total_requests + 1
            succ = existing.successful_requests + (1 if success else 0)
            failed = existing.failed_requests + (0 if success else 1)
            retries = existing.retried_requests + (1 if retried else 0)
            avg_lat = round((existing.avg_latency_ms * existing.total_requests + latency_ms) / total, 2)
            trips = existing.circuit_trips + (1 if circuit_tripped else 0)

        metric = IntegrationMetric(
            metric_id=f"metric_{provider_id}",
            provider_id=provider_id,
            domain=domain,
            total_requests=total,
            successful_requests=succ,
            failed_requests=failed,
            retried_requests=retries,
            avg_latency_ms=avg_lat,
            circuit_trips=trips,
            last_updated=now_str,
        )
        self._metrics[provider_id] = metric
        return metric

    def get_metrics(self, provider_id: str) -> Dict[str, Any]:
        """Returns metric summary for a provider."""
        m = self._metrics.get(provider_id)
        if not m:
            return {"provider_id": provider_id, "total_requests": 0, "success_rate_pct": 100.0}
        success_rate = round((m.successful_requests / m.total_requests) * 100.0, 2) if m.total_requests > 0 else 100.0
        return {
            "provider_id": m.provider_id,
            "domain": m.domain.value,
            "total_requests": m.total_requests,
            "successful_requests": m.successful_requests,
            "failed_requests": m.failed_requests,
            "retried_requests": m.retried_requests,
            "avg_latency_ms": m.avg_latency_ms,
            "success_rate_pct": success_rate,
            "circuit_trips": m.circuit_trips,
            "last_updated": m.last_updated,
        }

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Returns metric summaries across all providers."""
        return {pid: self.get_metrics(pid) for pid in self._metrics}
