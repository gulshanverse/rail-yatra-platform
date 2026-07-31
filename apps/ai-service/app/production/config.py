"""
Production Configuration Platform – Environment-aware configuration loader.
Supports Development, Staging, and Production environments.
"""

import os
import logging
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger("ai-service.production.config")


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class FeatureFlags:
    """Runtime feature flag registry."""

    def __init__(self) -> None:
        self._flags: Dict[str, bool] = {
            "enable_ai_predictions": True,
            "enable_realtime_tracking": True,
            "enable_enterprise_integrations": True,
            "enable_personalization": True,
            "enable_distributed_tracing": True,
            "enable_metrics_endpoint": True,
            "enable_backup_scheduling": True,
            "enable_rate_limiting": True,
        }

    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag, False)

    def set_flag(self, flag: str, enabled: bool) -> None:
        self._flags[flag] = enabled

    def all_flags(self) -> Dict[str, bool]:
        return dict(self._flags)


class ProductionConfig:
    """Centralized production configuration with environment separation."""

    def __init__(self) -> None:
        self.environment = self._resolve_environment()
        self.feature_flags = FeatureFlags()
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _resolve_environment(self) -> Environment:
        env_str = os.getenv("ENV", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            logger.warning(f"Unknown environment '{env_str}', defaulting to development.")
            return Environment.DEVELOPMENT

    def _load_config(self) -> None:
        """Loads environment-specific configuration."""
        base = {
            "app_name": "RailYatra AI Platform",
            "app_version": "10.0.0",
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8000")),
            "workers": int(os.getenv("WORKERS", "1")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "cors_origins": os.getenv("CORS_ORIGIN", "*"),
            "database_url": os.getenv("DATABASE_URL", ""),
            "redis_url": os.getenv("REDIS_URL", ""),
            "qdrant_url": os.getenv("QDRANT_URL", ""),
            "jwt_secret": os.getenv("JWT_SECRET", ""),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_expiry_minutes": int(os.getenv("JWT_EXPIRY_MINUTES", "30")),
            "rate_limit_requests": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            "rate_limit_window_seconds": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            "backup_enabled": os.getenv("BACKUP_ENABLED", "false").lower() == "true",
            "backup_interval_hours": int(os.getenv("BACKUP_INTERVAL_HOURS", "24")),
            "metrics_enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
            "tracing_enabled": os.getenv("TRACING_ENABLED", "true").lower() == "true",
            "debug": False,
        }

        if self.environment == Environment.DEVELOPMENT:
            base["debug"] = True
            base["log_level"] = "DEBUG"
            base["workers"] = 1
        elif self.environment == Environment.STAGING:
            base["debug"] = False
            base["log_level"] = "INFO"
            base["workers"] = 2
        elif self.environment == Environment.PRODUCTION:
            base["debug"] = False
            base["log_level"] = "WARNING"
            base["workers"] = int(os.getenv("WORKERS", "4"))

        self._config = base

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._config.get(key, default)

    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    def is_debug(self) -> bool:
        return self._config.get("debug", False)

    def validate(self) -> Dict[str, Any]:
        """Validates critical configuration and returns validation results."""
        results: Dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

        if self.is_production():
            if not self._config.get("jwt_secret"):
                results["errors"].append("JWT_SECRET is required in production.")
                results["valid"] = False
            if not self._config.get("database_url"):
                results["warnings"].append("DATABASE_URL is not configured.")
            if self._config.get("debug"):
                results["errors"].append("Debug mode must be disabled in production.")
                results["valid"] = False

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Returns safe configuration (secrets redacted)."""
        safe = dict(self._config)
        for key in ("jwt_secret", "database_url", "redis_url"):
            if safe.get(key):
                safe[key] = "***REDACTED***"
        safe["environment"] = self.environment.value
        safe["feature_flags"] = self.feature_flags.all_flags()
        return safe


# Module-level singleton
production_config = ProductionConfig()
