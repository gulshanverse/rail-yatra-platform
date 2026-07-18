import logging
from typing import Dict, Any

logger = logging.getLogger("ai-service.orchestrator.config")


class AIPlatformConfig:
    """
    Centralized configuration manager for AI platform capabilities and timeouts.
    """

    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {
            "default_timeout_ms": 5000,
            "max_retry_attempts": 3,
            "backoff_base_delay": 1.0,
            "feature_flags": {
                "enable_cost_monitoring": True,
                "enable_advanced_observability": True,
                "strict_policy_validation": False,
            },
            "resource_limits": {
                "max_message_length": 4096,
                "max_session_history": 20,
            },
            "governance": {
                "enforce_privacy_scrubbing": True,
                "allowed_providers": ["openai", "anthropic", "synthetic"],
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration setting by key name."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Dynamically updates a configuration setting value."""
        self._settings[key] = value
        logger.info(f"Configuration updated: {key} = {value}")

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Evaluates whether a specific feature flag is active."""
        flags = self._settings.get("feature_flags", {})
        return bool(flags.get(feature_name, False))


# Global singleton configuration manager
platform_config = AIPlatformConfig()
