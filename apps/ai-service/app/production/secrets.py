"""
Secrets Management Platform – Secure loading and validation of production secrets.
"""

import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ai-service.production.secrets")


class SecretsManager:
    """Centralized secrets loader with validation and secure access."""

    REQUIRED_PRODUCTION_SECRETS = [
        "JWT_SECRET",
        "DATABASE_URL",
    ]

    OPTIONAL_SECRETS = [
        "REDIS_URL",
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "RAZORPAY_KEY",
        "WEBHOOK_SECRET",
        "ENCRYPTION_KEY",
    ]

    def __init__(self) -> None:
        self._secrets: Dict[str, str] = {}
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Loads secrets from environment variables."""
        all_keys = self.REQUIRED_PRODUCTION_SECRETS + self.OPTIONAL_SECRETS
        for key in all_keys:
            value = os.getenv(key, "")
            if value:
                self._secrets[key] = value

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a secret value by key."""
        return self._secrets.get(key, default)

    def has(self, key: str) -> bool:
        """Checks if a secret is loaded."""
        return key in self._secrets and bool(self._secrets[key])

    def validate(self, is_production: bool = False) -> Dict[str, Any]:
        """Validates that required secrets are present."""
        results: Dict[str, Any] = {
            "valid": True,
            "loaded_count": len(self._secrets),
            "missing_required": [],
            "missing_optional": [],
        }

        if is_production:
            for key in self.REQUIRED_PRODUCTION_SECRETS:
                if not self.has(key):
                    results["missing_required"].append(key)
                    results["valid"] = False

        for key in self.OPTIONAL_SECRETS:
            if not self.has(key):
                results["missing_optional"].append(key)

        return results

    def summary(self) -> Dict[str, str]:
        """Returns a redacted summary showing which secrets are loaded."""
        summary: Dict[str, str] = {}
        all_keys = self.REQUIRED_PRODUCTION_SECRETS + self.OPTIONAL_SECRETS
        for key in all_keys:
            if self.has(key):
                summary[key] = "LOADED"
            else:
                summary[key] = "NOT_SET"
        return summary


# Module-level singleton
secrets_manager = SecretsManager()
