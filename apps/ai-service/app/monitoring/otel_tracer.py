"""
OpenTelemetry & W3C Trace Context Manager for FastAPI AI Service
"""

import uuid
import time
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ai-service.monitoring.tracer")


class AISpan:
    """Represents a lightweight OpenTelemetry-compatible span."""

    def __init__(self, trace_id: str, span_id: str, name: str, parent_id: Optional[str] = None) -> None:
        self.trace_id = trace_id
        self.span_id = span_id
        self.name = name
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.status = "OK"

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def finish(self, status: str = "OK") -> None:
        self.end_time = time.time()
        self.status = status

    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return round((end - self.start_time) * 1000, 2)


class AITracerProvider:
    """Tracer provider parsing and generating W3C traceparent headers."""

    def parse_traceparent(self, traceparent: Optional[str]) -> Dict[str, str]:
        """Parses W3C traceparent header format: 00-traceid-spanid-flags."""
        if traceparent and traceparent.startswith("00-"):
            parts = traceparent.split("-")
            if len(parts) >= 3:
                return {"trace_id": parts[1], "parent_span_id": parts[2]}

        # Fallback generate new trace ID
        new_trace_id = uuid.uuid4().hex[:32]
        return {"trace_id": new_trace_id, "parent_span_id": None}

    def start_span(self, name: str, trace_id: str, parent_id: Optional[str] = None) -> AISpan:
        span_id = uuid.uuid4().hex[:16]
        return AISpan(trace_id=trace_id, span_id=span_id, name=name, parent_id=parent_id)


tracer_provider = AITracerProvider()
