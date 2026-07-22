"""
Observability and Telemetry Collector for Milestone 6.5 AI Memory Platform.
Provides metrics aggregation, audit tracing, and structured diagnostic logging.
"""

from typing import Dict, Any, List
import time
import logging

logger = logging.getLogger("railyatra.ai.memory")


class MemoryTelemetryCollector:
    """Monotonic metrics counter and observability collector for Memory Platform operations."""

    def __init__(self):
        self._metrics_store: Dict[str, int] = {
            "memory_created_total": 0,
            "preference_updated_total": 0,
            "consent_granted_total": 0,
            "consent_withdrawn_total": 0,
            "memory_purged_total": 0,
            "saga_resumed_total": 0,
            "query_hits_total": 0,
            "unconsented_rejections_total": 0,
        }
        self._audit_spans: List[Dict[str, Any]] = []

    def record_metric(self, metric_name: str, value: int = 1) -> None:
        if metric_name in self._metrics_store:
            self._metrics_store[metric_name] += value
        else:
            self._metrics_store[metric_name] = value

    def record_span(
        self,
        action: str,
        traveler_id: str,
        status: str = "SUCCESS",
        duration_ms: float = 0.0,
    ) -> None:
        span = {
            "action": action,
            "traveler_id": traveler_id,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "timestamp": time.time(),
        }
        self._audit_spans.append(span)
        logger.info(
            f"[MEMORY TELEMETRY] {action} | Traveler: {traveler_id} | Status: {status} | Latency: {duration_ms:.2f}ms"
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._metrics_store),
            "total_spans_recorded": len(self._audit_spans),
        }


# Singleton telemetry instance
telemetry_collector = MemoryTelemetryCollector()
