# app/integration/config.py
import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger("ai-service.integration.config")


class IntegrationConfig:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.settings: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        # Default fallback configurations
        default_config = {
            "environment": os.getenv("ENV", "development"),
            "vault_provider": "env",
            "default_policies": {
                "timeout_ms": 1000,
                "max_retries": 3,
                "base_retry_delay_ms": 100,
            },
            "routing_policies": {
                "pnr_lookup": "business_priority",
                "live_train_status": "lowest_latency",
                "seat_availability": "highest_accuracy",
            },
            "feature_flags": {
                "enable_new_provider": {
                    "confirmtkt_gds": True,
                    "ntes_cris": True,
                    "static_local": True,
                },
                "routing_canary_percentage": {
                    "confirmtkt_gds": 100.0,
                    "rapidapi_railway": 0.0,
                },
                "experimental_capabilities": {"bulk_pnr_lookup": False},
            },
        }

        self.settings = default_config

        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    file_settings = yaml.safe_load(f)
                    if file_settings:
                        self._deep_merge(self.settings, file_settings)
                        logger.info(
                            f"Successfully loaded configuration overrides from {self.config_path}"
                        )
            except Exception as e:
                logger.error(
                    f"Failed to load configuration overrides from {self.config_path}: {e}"
                )

    def _deep_merge(self, base: dict, override: dict):
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def get(self, path: str, default: Any = None) -> Any:
        keys = path.split(".")
        curr = self.settings
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr
