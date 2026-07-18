# app/personalization/metrics/engine.py
from datetime import datetime
import logging
from typing import Optional, Dict
from app.personalization.interfaces.contracts import IMetricsEngine, IMetricsRepository
from app.personalization.dto.models import PreferenceMetricsDTO

logger = logging.getLogger(__name__)


class MetricsEngine(IMetricsEngine):
    def __init__(self, metrics_repository: IMetricsRepository) -> None:
        self._metrics_repo = metrics_repository

    def increment(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> None:
        logger.info("Incrementing metric %s", metric_name)
        metric = PreferenceMetricsDTO(
            metric_name=metric_name,
            value=1.0,
            timestamp=datetime.utcnow(),
            tags=tags if tags is not None else {},
        )
        self._metrics_repo.save(metric)

    def observe(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        logger.info("Observing metric %s with value %f", metric_name, value)
        metric = PreferenceMetricsDTO(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags if tags is not None else {},
        )
        self._metrics_repo.save(metric)
