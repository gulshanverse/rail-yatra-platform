"""
Configuration Management for Enterprise Integration Providers.
"""

from typing import Dict, Optional
from app.integrations.interfaces import IntegrationDomain, AuthStrategyType
from app.integrations.models import ProviderConfiguration


class ProviderConfigManager:
    def __init__(self) -> None:
        self._configs: Dict[str, ProviderConfiguration] = {}
        self._load_default_configs()

    def _load_default_configs(self) -> None:
        """Populates default configuration blueprints for core integration providers."""
        defaults = [
            ProviderConfiguration(
                provider_id="railway_ntes",
                domain=IntegrationDomain.RAILWAY,
                base_url="https://api.railway.example.com",
                api_key="ntes_live_key_mock",
                timeout_seconds=5.0,
                max_retries=3,
                auth_type=AuthStrategyType.API_KEY,
            ),
            ProviderConfiguration(
                provider_id="weather_openmeteo",
                domain=IntegrationDomain.WEATHER,
                base_url="https://api.weather.example.com",
                api_key="weather_key_mock",
                timeout_seconds=3.0,
                max_retries=2,
                auth_type=AuthStrategyType.API_KEY,
            ),
            ProviderConfiguration(
                provider_id="maps_google",
                domain=IntegrationDomain.MAPS,
                base_url="https://maps.example.com",
                api_key="maps_key_mock",
                timeout_seconds=4.0,
                max_retries=3,
                auth_type=AuthStrategyType.API_KEY,
            ),
            ProviderConfiguration(
                provider_id="payment_razorpay",
                domain=IntegrationDomain.PAYMENTS,
                base_url="https://api.razorpay.example.com",
                api_key="rzp_key_mock",
                secret_key="rzp_secret_mock",
                timeout_seconds=6.0,
                max_retries=2,
                auth_type=AuthStrategyType.HMAC_SIGNATURE,
            ),
            ProviderConfiguration(
                provider_id="notification_multi",
                domain=IntegrationDomain.NOTIFICATIONS,
                base_url="https://notify.example.com",
                api_key="notify_key_mock",
                timeout_seconds=4.0,
                max_retries=3,
                auth_type=AuthStrategyType.BEARER_TOKEN,
            ),
        ]
        for cfg in defaults:
            self._configs[cfg.provider_id] = cfg

    def get_config(self, provider_id: str) -> Optional[ProviderConfiguration]:
        """Retrieves provider configuration by ID."""
        return self._configs.get(provider_id)

    def set_config(self, config: ProviderConfiguration) -> ProviderConfiguration:
        """Registers or updates a provider configuration."""
        self._configs[config.provider_id] = config
        return config

    def list_configs(self) -> Dict[str, ProviderConfiguration]:
        """Lists all registered configurations."""
        return self._configs.copy()
