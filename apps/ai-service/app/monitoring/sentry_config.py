"""
Sentry Python SDK Configuration with PII Redaction & Environment Controls
"""

import os
import logging
from typing import Any, Dict

logger = logging.getLogger("ai-service.monitoring.sentry")


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes PII and sensitive keys from error reports prior to transmission."""
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED_HEADER]"

    return event


def init_sentry() -> bool:
    """Initializes Sentry Python SDK if DSN is configured in environment."""
    dsn = os.getenv("SENTRY_DSN")
    env = os.getenv("ENV", "production")

    if not dsn:
        logger.info("SENTRY_DSN not set. Application error tracking operating in log-only fallback mode.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=env,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.05")),
            before_send=before_send,
            integrations=[FastApiIntegration()],
        )
        logger.info(f"Sentry SDK successfully initialized for environment: {env}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Sentry Python SDK: {e}")
        return False
