"""
FastAPI Monitoring & Request Latency Middleware
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics_collector import ai_metrics_collector
from app.monitoring.otel_tracer import tracer_provider

logger = logging.getLogger("ai-service.monitoring.middleware")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Interceptors requests to capture latency, status counters, and W3C trace context."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Parse trace context
        traceparent = request.headers.get("traceparent")
        correlation_id = request.headers.get("x-correlation-id")
        context = tracer_provider.parse_traceparent(traceparent)
        trace_id = context["trace_id"]

        span = tracer_provider.start_span(
            name=f"HTTP {request.method} {request.url.path}",
            trace_id=trace_id,
            parent_id=context["parent_span_id"],
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            span.finish("OK")

            # Record Prometheus Metrics
            ai_metrics_collector.increment("railyatra_ai_http_requests_total")
            ai_metrics_collector.observe("railyatra_ai_request_duration_seconds", duration)

            if response.status_code >= 500:
                ai_metrics_collector.increment("railyatra_ai_http_errors_total")

            # Outgoing headers
            response.headers["x-correlation-id"] = correlation_id or trace_id
            response.headers["traceparent"] = f"00-{trace_id}-{span.span_id}-01"

            return response
        except Exception as exc:
            duration = time.time() - start_time
            span.finish("ERROR")
            ai_metrics_collector.increment("railyatra_ai_http_errors_total")
            logger.error(f"Unhandled exception in API request [{request.method} {request.url.path}]: {exc}")
            raise exc
