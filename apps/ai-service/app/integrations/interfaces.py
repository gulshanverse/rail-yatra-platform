"""
Interfaces, Enums, and Contracts for Phase 9 Enterprise Integrations Platform.
"""

from enum import Enum
from typing import Protocol, Dict, Any


class ProviderStatus(str, Enum):
    REGISTERED = "REGISTERED"
    INITIALIZED = "INITIALIZED"
    AUTHENTICATED = "AUTHENTICATED"
    HEALTHY = "HEALTHY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    RECOVERING = "RECOVERING"


class IntegrationDomain(str, Enum):
    RAILWAY = "RAILWAY"
    WEATHER = "WEATHER"
    MAPS = "MAPS"
    NOTIFICATIONS = "NOTIFICATIONS"
    PAYMENTS = "PAYMENTS"
    IDENTITY = "IDENTITY"
    ANALYTICS = "ANALYTICS"


class AuthStrategyType(str, Enum):
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    HMAC_SIGNATURE = "HMAC_SIGNATURE"
    OAUTH2 = "OAUTH2"
    NONE = "NONE"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class WebhookEventType(str, Enum):
    TRAIN_UPDATED = "TRAIN_UPDATED"
    WEATHER_UPDATED = "WEATHER_UPDATED"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    NOTIFICATION_DELIVERED = "NOTIFICATION_DELIVERED"
    PROVIDER_CONNECTED = "PROVIDER_CONNECTED"
    PROVIDER_DISCONNECTED = "PROVIDER_DISCONNECTED"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"


class IProviderAdapter(Protocol):
    def initialize(self) -> None:
        ...

    def authenticate(self) -> bool:
        ...

    def health(self) -> Dict[str, Any]:
        ...

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def shutdown(self) -> None:
        ...
