# app/traveler/metrics/collector.py
import logging
from typing import Dict, Optional
from app.traveler.interfaces.contracts import IMetricsEngine

logger = logging.getLogger("ai-service.traveler.metrics")


class MetricsEngine(IMetricsEngine):
    def increment_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        tag_str = ""
        if tags:
            tag_str = " ".join(f"{k}={v}" for k, v in tags.items())
        logger.info(f"METRIC_TRAVELER_LOG name={name} value={value} {tag_str}")
