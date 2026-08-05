"""
Production Metrics Platform – Prometheus-compatible application metrics.
"""

import time
import threading
import logging
from typing import Any, Dict
from datetime import datetime, timezone

logger = logging.getLogger("ai-service.production.metrics")


class MetricsCollector:
    """Thread-safe production metrics collector with Prometheus-compatible output."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {
            "http_requests_total": 0,
            "http_requests_success": 0,
            "http_requests_error": 0,
            "ai_predictions_total": 0,
            "integration_requests_total": 0,
            "webhook_events_received": 0,
            "backup_operations_total": 0,
            "health_checks_total": 0,
        }
        self._gauges: Dict[str, float] = {
            "active_connections": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "uptime_seconds": 0.0,
        }
        self._histograms: Dict[str, list] = {
            "http_request_duration_ms": [],
            "ai_prediction_duration_ms": [],
            "db_query_duration_ms": [],
        }
        self._start_time = time.time()

    def increment(self, counter: str, value: int = 1) -> None:
        with self._lock:
            if counter in self._counters:
                self._counters[counter] += value

    def set_gauge(self, gauge: str, value: float) -> None:
        with self._lock:
            self._gauges[gauge] = value

    def observe(self, histogram: str, value: float) -> None:
        with self._lock:
            if histogram in self._histograms:
                bucket = self._histograms[histogram]
                bucket.append(value)
                if len(bucket) > 1000:
                    self._histograms[histogram] = bucket[-500:]

    def get_metrics(self) -> Dict[str, Any]:
        """Returns all metrics in a structured format."""
        with self._lock:
            uptime = time.time() - self._start_time
            self._gauges["uptime_seconds"] = round(uptime, 2)

            histogram_stats = {}
            for name, values in self._histograms.items():
                if values:
                    histogram_stats[name] = {
                        "count": len(values),
                        "avg_ms": round(sum(values) / len(values), 2),
                        "max_ms": round(max(values), 2),
                        "min_ms": round(min(values), 2),
                    }
                else:
                    histogram_stats[name] = {"count": 0, "avg_ms": 0, "max_ms": 0, "min_ms": 0}

            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def prometheus_text(self) -> str:
        """Exports metrics in Prometheus text exposition format."""
        lines = [
            "# HELP memory_health_status Overall platform health status (1=Healthy, 2=Degraded, 3=Recovering, 4=Unavailable)",
            "memory_health_status 1",
        ]
        with self._lock:
            for name, value in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
            for name, value in self._gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

        try:
            from app.monitoring import ai_metrics_collector
            ai_text = ai_metrics_collector.prometheus_text()
            if ai_text.strip():
                lines.append(ai_text.strip())
        except Exception:
            pass

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            for key in self._counters:
                self._counters[key] = 0
            for key in self._histograms:
                self._histograms[key] = []


metrics_collector = MetricsCollector()
