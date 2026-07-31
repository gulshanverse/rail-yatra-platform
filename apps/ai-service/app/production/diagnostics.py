"""
Production Diagnostics – Runtime information and dependency status.
"""

import os
import sys
import platform
import logging
from typing import Any, Dict
from datetime import datetime, timezone

from app.production.version import get_version_info
from app.production.config import production_config
from app.production.secrets import secrets_manager

logger = logging.getLogger("ai-service.production.diagnostics")


class DiagnosticsEngine:
    """Collects runtime diagnostics for operational visibility."""

    def collect(self) -> Dict[str, Any]:
        return {
            "version": get_version_info(),
            "runtime": self._runtime_info(),
            "configuration": self._config_status(),
            "secrets": self._secrets_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _runtime_info(self) -> Dict[str, Any]:
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "architecture": platform.machine(),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
        }

    def _config_status(self) -> Dict[str, Any]:
        return {
            "environment": production_config.environment.value,
            "debug": production_config.is_debug(),
            "validation": production_config.validate(),
        }

    def _secrets_status(self) -> Dict[str, str]:
        return secrets_manager.summary()


diagnostics_engine = DiagnosticsEngine()
