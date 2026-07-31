"""
Domain Data Models (Pydantic v2) for Phase 9 Enterprise Integrations Platform.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.integrations.interfaces import (
    ProviderStatus,
    IntegrationDomain,
    AuthStrategyType,
    CircuitState,
    WebhookEventType,
)


class ProviderConfiguration(BaseModel):
    provider_id: str
    domain: IntegrationDomain
    base_url: str
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    timeout_seconds: float = 5.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    circuit_failure_threshold: int = 5
    circuit_recovery_seconds: float = 30.0
    enabled: bool = True
    auth_type: AuthStrategyType = AuthStrategyType.API_KEY
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class ProviderHealth(BaseModel):
    provider_id: str
    domain: IntegrationDomain
    status: ProviderStatus
    latency_ms: float = 0.0
    success_rate_pct: float = 100.0
    total_requests: int = 0
    failed_requests: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    last_checked: str
    error_message: Optional[str] = None


class IntegrationProvider(BaseModel):
    provider_id: str
    name: str
    domain: IntegrationDomain
    version: str = "1.0.0"
    status: ProviderStatus = ProviderStatus.REGISTERED
    configuration: ProviderConfiguration
    health: ProviderHealth
    created_at: str
    updated_at: str


class IntegrationRequest(BaseModel):
    request_id: str
    provider_id: str
    domain: IntegrationDomain
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class IntegrationResponse(BaseModel):
    request_id: str
    provider_id: str
    domain: IntegrationDomain
    status_code: int = 200
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    normalized_data: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    timestamp: str


class WebhookEvent(BaseModel):
    event_id: str
    provider_id: str
    event_type: WebhookEventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None
    timestamp: str
    processed: bool = False


class IntegrationMetric(BaseModel):
    metric_id: str
    provider_id: str
    domain: IntegrationDomain
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0
    avg_latency_ms: float = 0.0
    circuit_trips: int = 0
    last_updated: str


class AuthenticationContext(BaseModel):
    auth_type: AuthStrategyType
    credentials: Dict[str, Any] = Field(default_factory=dict)
    authenticated: bool = False
    expires_at: Optional[str] = None
