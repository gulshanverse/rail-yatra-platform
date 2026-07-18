# app/personalization/telemetry/adapter.py
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TelemetryAdapter:
    def __init__(self) -> None:
        pass

    def record_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        logger.info(
            "Telemetry span recorded: name=%s attributes=%s", name, attributes or {}
        )
