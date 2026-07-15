# app/booking/metrics/collector.py
import logging
from typing import Dict, Optional
from app.booking.interfaces.contracts import IMetricsEngine

logger = logging.getLogger("ai-service.booking.metrics")


class MetricsEngine(IMetricsEngine):
    def increment_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        tag_str = ""
        if tags:
            tag_str = " ".join(f"{k}={v}" for k, v in tags.items())
        logger.info(f"METRIC_BOOKING_LOG name={name} value={value} {tag_str}")
