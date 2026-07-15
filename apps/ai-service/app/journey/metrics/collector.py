# app/journey/metrics/collector.py
import logging
from typing import Dict, Any, Optional
from app.journey.interfaces.contracts import IMetricsEngine

logger = logging.getLogger("ai-service.journey.metrics")


class MetricsEngine(IMetricsEngine):
    def record_metrics(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        tag_str = ""
        if tags:
            tag_str = " ".join(f"{k}={v}" for k, v in tags.items())
        
        # Log structure for Datadog / OpenTelemetry parsers
        logger.info(f"METRIC_LOG name={metric_name} value={value} {tag_str}")
        
        # In a production context, write directly to statsd or prometheus client registry.
