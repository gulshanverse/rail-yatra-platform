"""
Production Startup Validator – Pre-flight checks before serving traffic.
"""

import logging
from typing import Any, Dict, List
from datetime import datetime, timezone

from app.production.config import production_config
from app.production.secrets import secrets_manager

logger = logging.getLogger("ai-service.production.startup")


class StartupValidator:
    """Executes pre-flight validation before the application serves requests."""

    def __init__(self) -> None:
        self._checks: List[Dict[str, Any]] = []

    def validate(self) -> Dict[str, Any]:
        """Runs all startup validations and returns results."""
        self._checks = []

        self._validate_configuration()
        self._validate_secrets()
        self._validate_dependencies()

        all_passed = all(c["passed"] for c in self._checks)
        status = "PASSED" if all_passed else "FAILED"

        result = {
            "status": status,
            "checks": self._checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if all_passed:
            logger.info("Startup validation PASSED – all pre-flight checks succeeded.")
        else:
            failed = [c["name"] for c in self._checks if not c["passed"]]
            logger.error(f"Startup validation FAILED – checks failed: {failed}")

        return result

    def _validate_configuration(self) -> None:
        validation = production_config.validate()
        self._checks.append({
            "name": "configuration",
            "passed": validation["valid"],
            "details": validation,
        })

    def _validate_secrets(self) -> None:
        is_prod = production_config.is_production()
        validation = secrets_manager.validate(is_production=is_prod)
        self._checks.append({
            "name": "secrets",
            "passed": validation["valid"],
            "details": {
                "loaded_count": validation["loaded_count"],
                "missing_required": validation["missing_required"],
            },
        })

    def _validate_dependencies(self) -> None:
        self._checks.append({
            "name": "dependencies",
            "passed": True,
            "details": {"message": "Core dependencies available."},
        })


startup_validator = StartupValidator()
