"""
Security Hardening Platform – HTTP headers, CSP, HSTS, rate limiting, audit logging.
"""

import time
import logging
import threading
from typing import Any, Dict
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger("ai-service.production.security")


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        with self._lock:
            window_start = now - self.window_seconds
            self._requests[client_id] = [
                t for t in self._requests[client_id] if t > window_start
            ]
            if len(self._requests[client_id]) >= self.max_requests:
                return False
            self._requests[client_id].append(now)
            return True

    def get_status(self, client_id: str) -> Dict[str, Any]:
        now = time.time()
        with self._lock:
            window_start = now - self.window_seconds
            recent = [t for t in self._requests.get(client_id, []) if t > window_start]
            return {
                "client_id": client_id,
                "requests_in_window": len(recent),
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "remaining": max(0, self.max_requests - len(recent)),
            }


class AuditLogger:
    """Security audit event logger."""

    def __init__(self) -> None:
        self._events: list = []
        self._lock = threading.Lock()

    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._events.append(event)
            if len(self._events) > 10000:
                self._events = self._events[-5000:]
        logger.info(f"AUDIT: {event_type} – {details}")

    def get_recent_events(self, count: int = 50) -> list:
        with self._lock:
            return list(self._events[-count:])


class SecurityManager:
    """Centralized security management for production hardening."""

    def __init__(self) -> None:
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()

    def get_security_headers(self) -> Dict[str, str]:
        return dict(SECURITY_HEADERS)

    def validate_configuration(self) -> Dict[str, Any]:
        return {
            "headers_configured": len(SECURITY_HEADERS),
            "rate_limiting_enabled": True,
            "audit_logging_enabled": True,
            "csp_enabled": "Content-Security-Policy" in SECURITY_HEADERS,
            "hsts_enabled": "Strict-Transport-Security" in SECURITY_HEADERS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


security_manager = SecurityManager()
