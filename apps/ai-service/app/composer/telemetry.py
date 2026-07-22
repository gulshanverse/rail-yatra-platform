"""
Observability and Telemetry Collector for Milestone 6.6 AI Response Composer Platform.
Provides metrics aggregation, OpenTelemetry span recording, and structured diagnostic logging.
"""

from typing import Dict, Any, List
import time
import logging

logger = logging.getLogger("railyatra.ai.composer")


class ComposerTelemetryCollector:
    """Monotonic metrics counter and observability collector for Response Composer operations."""

    def __init__(self):
        self._metrics_store: Dict[str, int] = {
            "responses_composed_total": 0,
            "arbitrations_resolved_total": 0,
            "explanations_generated_total": 0,
            "low_confidence_warnings_total": 0,
            "pii_masked_total": 0,
            "safety_overrides_total": 0,
            "unconsented_personalizations_blocked_total": 0,
            "quality_validation_failures_total": 0,
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
        session_id: str,
        status: str = "SUCCESS",
        duration_ms: float = 0.0,
        details: Dict[str, Any] | None = None,
    ) -> None:
        span = {
            "action": action,
            "session_id": session_id,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "details": details or {},
            "timestamp": time.time(),
        }
        self._audit_spans.append(span)
        logger.info(
            f"[COMPOSER TELEMETRY] {action} | Session: {session_id} | Status: {status} | Latency: {duration_ms:.2f}ms"
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._metrics_store),
            "total_spans_recorded": len(self._audit_spans),
        }


# Singleton telemetry instance
telemetry_collector = ComposerTelemetryCollector()
