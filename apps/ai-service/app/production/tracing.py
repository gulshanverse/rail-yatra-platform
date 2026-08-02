"""
Distributed Tracing Platform – OpenTelemetry-compatible trace context management.
"""

import uuid
import time
import threading
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("ai-service.production.tracing")


class Span:
    """Represents a single trace span."""

    def __init__(self, trace_id: str, span_id: str, operation: str, parent_id: Optional[str] = None) -> None:
        self.trace_id = trace_id
        self.span_id = span_id
        self.operation = operation
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.status = "IN_PROGRESS"

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def finish(self, status: str = "OK") -> None:
        self.end_time = time.time()
        self.status = status

    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return round((end - self.start_time) * 1000, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "operation": self.operation,
            "duration_ms": self.duration_ms(),
            "status": self.status,
            "attributes": self.attributes,
        }


class TracingPlatform:
    """OpenTelemetry-compatible distributed tracing manager."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._traces: Dict[str, List[Span]] = {}
        self._active_spans: Dict[str, Span] = {}

    def start_trace(self, operation: str) -> Span:
        """Starts a new trace with a root span."""
        trace_id = uuid.uuid4().hex[:16]
        span_id = uuid.uuid4().hex[:8]
        span = Span(trace_id=trace_id, span_id=span_id, operation=operation)
        with self._lock:
            self._traces[trace_id] = [span]
            self._active_spans[span_id] = span
        return span

    def start_span(self, trace_id: str, operation: str, parent_id: Optional[str] = None) -> Span:
        """Starts a child span within an existing trace."""
        span_id = uuid.uuid4().hex[:8]
        span = Span(trace_id=trace_id, span_id=span_id, operation=operation, parent_id=parent_id)
        with self._lock:
            if trace_id not in self._traces:
                self._traces[trace_id] = []
            self._traces[trace_id].append(span)
            self._active_spans[span_id] = span
        return span

    def finish_span(self, span: Span, status: str = "OK") -> None:
        """Finishes a span."""
        span.finish(status)
        with self._lock:
            self._active_spans.pop(span.span_id, None)

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Returns all spans for a trace."""
        with self._lock:
            spans = self._traces.get(trace_id, [])
            return [s.to_dict() for s in spans]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_traces": len(self._traces),
                "active_spans": len(self._active_spans),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


tracing_platform = TracingPlatform()
