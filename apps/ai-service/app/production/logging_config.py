"""
Structured Logging Platform – Production-grade JSON logging with category support.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter for production environments."""

    SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "authorization", "jwt"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "category"):
            log_entry["category"] = record.category

        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id

        return json.dumps(log_entry, default=str)


class LogCategory:
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    SECURITY = "SECURITY"
    REQUEST = "REQUEST"
    ERROR = "ERROR"
    AUDIT = "AUDIT"
    BACKGROUND = "BACKGROUND"
    DEPLOYMENT = "DEPLOYMENT"
    BACKUP = "BACKUP"


class LoggingPlatform:
    """Configures and manages structured logging for the production platform."""

    def __init__(self) -> None:
        self._configured = False

    def configure(self, log_level: str = "INFO") -> None:
        """Configures structured logging for the application."""
        if self._configured:
            return

        env = os.getenv("ENV", "development")
        root_logger = logging.getLogger()

        if env == "production":
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            for h in root_logger.handlers[:]:
                root_logger.removeHandler(h)
            root_logger.addHandler(handler)
        else:
            logging.basicConfig(
                level=getattr(logging, log_level.upper(), logging.INFO),
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self._configured = True

    def log(
        self,
        logger_name: str,
        level: str,
        message: str,
        category: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Emits a structured log entry."""
        log = logging.getLogger(logger_name)
        extra: Dict[str, Any] = {}
        if category:
            extra["category"] = category
        if trace_id:
            extra["trace_id"] = trace_id
        log_method = getattr(log, level.lower(), log.info)
        log_method(message, extra=extra)

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": self._configured,
            "root_level": logging.getLevelName(logging.getLogger().level),
            "handler_count": len(logging.getLogger().handlers),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


logging_platform = LoggingPlatform()
