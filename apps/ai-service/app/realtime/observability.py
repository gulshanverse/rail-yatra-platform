"""
Observability & Telemetry Module for Phase 8 Real-Time Operations Platform.
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger("ai-service.realtime.observability")


class RealTimeObservability:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {
            "events_ingested": 0,
            "incidents_detected": 0,
            "notifications_dispatched": 0,
            "errors": 0,
        }
        self._latencies: Dict[str, float] = {}

    def record_event_ingested(self) -> None:
        """Increments event ingestion counter."""
        self._counters["events_ingested"] += 1

    def record_incident_detected(self) -> None:
        """Increments incident detection counter."""
        self._counters["incidents_detected"] += 1

    def record_notification_dispatched(self) -> None:
        """Increments notification counter."""
        self._counters["notifications_dispatched"] += 1

    def record_error(self) -> None:
        """Increments error counter."""
        self._counters["errors"] += 1

    def record_latency(self) -> "LatencyTracker":
        """Returns a context manager to record processing latency."""
        return LatencyTracker(self)

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Returns current operational metrics and counters."""
        return {
            "counters": dict(self._counters),
            "last_processing_latency_ms": self._latencies.get("last_processing_ms", 0.0),
            "status": "HEALTHY" if self._counters["errors"] == 0 else "DEGRADED",
        }


class LatencyTracker:
    def __init__(self, obs: RealTimeObservability) -> None:
        self._obs = obs
        self._start_time: float = 0.0

    def __enter__(self) -> "LatencyTracker":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000.0
        self._obs._latencies["last_processing_ms"] = round(elapsed_ms, 3)
        if exc_type:
            self._obs.record_error()
