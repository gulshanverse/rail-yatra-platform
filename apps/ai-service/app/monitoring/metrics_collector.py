"""
Enhanced Prometheus Metrics Collector for AI Service
"""

import threading
import logging
from typing import Dict

logger = logging.getLogger("ai-service.monitoring.metrics")


class AIMetricsCollector:
    """Thread-safe Prometheus metrics collector for AI Service microservice."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {
            "railyatra_ai_http_requests_total": 0,
            "railyatra_ai_http_errors_total": 0,
            "railyatra_ai_chat_requests_total": 0,
            "railyatra_ai_journey_requests_total": 0,
            "railyatra_ai_token_prompt_total": 0,
            "railyatra_ai_token_completion_total": 0,
            "railyatra_ai_provider_fallback_total": 0,
        }
        self._gauges: Dict[str, float] = {
            "railyatra_ai_active_streams": 0.0,
            "railyatra_ai_up": 1.0,
        }
        self._histograms: Dict[str, list] = {
            "railyatra_ai_request_duration_seconds": [],
            "railyatra_ai_stream_first_token_seconds": [],
        }

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
                if len(bucket) > 2000:
                    self._histograms[histogram] = bucket[-1000:]

    def prometheus_text(self) -> str:
        """Renders Prometheus text exposition format metrics."""
        lines = [
            "# HELP railyatra_ai_up Overall AI Service operational status (1=Up, 0=Down)",
            "# TYPE railyatra_ai_up gauge",
            "railyatra_ai_up 1",
        ]
        with self._lock:
            for name, value in self._counters.items():
                lines.append(f"# HELP {name} Counter metric")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")

            for name, value in self._gauges.items():
                lines.append(f"# HELP {name} Gauge metric")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            buckets = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            for name, values in self._histograms.items():
                if not values:
                    continue
                lines.append(f"# HELP {name} Histogram latency metric")
                lines.append(f"# TYPE {name} histogram")
                count = len(values)
                sum_val = sum(values)
                for b in buckets:
                    b_count = sum(1 for v in values if v <= b)
                    lines.append(f'{name}_bucket{{le="{b}"}} {b_count}')
                lines.append(f'{name}_bucket{{le="+Inf"}} {count}')
                lines.append(f"{name}_sum {round(sum_val, 4)}")
                lines.append(f"{name}_count {count}")

        return "\n".join(lines) + "\n"


ai_metrics_collector = AIMetricsCollector()
