"""
Provider Registry: Manages registration, discovery, versioning, and health state transitions of external integrations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.integrations.interfaces import ProviderStatus, IntegrationDomain, CircuitState
from app.integrations.models import IntegrationProvider, ProviderHealth, ProviderConfiguration

logger = logging.getLogger("ai-service.integrations.registry")


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, IntegrationProvider] = {}

    def register_provider(
        self,
        provider_id: str,
        name: str,
        domain: IntegrationDomain,
        configuration: ProviderConfiguration,
        version: str = "1.0.0",
    ) -> IntegrationProvider:
        """Registers a new provider or updates an existing registration."""
        now_str = datetime.now(timezone.utc).isoformat()
        health = ProviderHealth(
            provider_id=provider_id,
            domain=domain,
            status=ProviderStatus.REGISTERED,
            latency_ms=0.0,
            success_rate_pct=100.0,
            total_requests=0,
            failed_requests=0,
            circuit_state=CircuitState.CLOSED,
            last_checked=now_str,
        )
        provider = IntegrationProvider(
            provider_id=provider_id,
            name=name,
            domain=domain,
            version=version,
            status=ProviderStatus.REGISTERED,
            configuration=configuration,
            health=health,
            created_at=now_str,
            updated_at=now_str,
        )
        self._providers[provider_id] = provider
        logger.info(f"Registered provider '{provider_id}' for domain {domain.value}.")
        return provider

    def get_provider(self, provider_id: str) -> Optional[IntegrationProvider]:
        """Returns provider metadata by ID."""
        return self._providers.get(provider_id)

    def get_providers_by_domain(self, domain: IntegrationDomain) -> List[IntegrationProvider]:
        """Returns all providers matching a given domain."""
        return [p for p in self._providers.values() if p.domain == domain]

    def list_all_providers(self) -> List[IntegrationProvider]:
        """Lists all registered integration providers."""
        return list(self._providers.values())

    def update_status(self, provider_id: str, new_status: ProviderStatus, error_msg: Optional[str] = None) -> Optional[IntegrationProvider]:
        """Updates provider state machine status with validation rules."""
        provider = self._providers.get(provider_id)
        if not provider:
            return None

        # State machine transition rules validation
        allowed_transitions = {
            ProviderStatus.REGISTERED: {ProviderStatus.INITIALIZED, ProviderStatus.UNAVAILABLE},
            ProviderStatus.INITIALIZED: {ProviderStatus.AUTHENTICATED, ProviderStatus.UNAVAILABLE, ProviderStatus.DEGRADED},
            ProviderStatus.AUTHENTICATED: {ProviderStatus.HEALTHY, ProviderStatus.ACTIVE, ProviderStatus.DEGRADED, ProviderStatus.UNAVAILABLE},
            ProviderStatus.HEALTHY: {ProviderStatus.ACTIVE, ProviderStatus.DEGRADED, ProviderStatus.UNAVAILABLE},
            ProviderStatus.ACTIVE: {ProviderStatus.DEGRADED, ProviderStatus.UNAVAILABLE, ProviderStatus.HEALTHY},
            ProviderStatus.DEGRADED: {ProviderStatus.RECOVERING, ProviderStatus.ACTIVE, ProviderStatus.UNAVAILABLE},
            ProviderStatus.UNAVAILABLE: {ProviderStatus.RECOVERING, ProviderStatus.INITIALIZED},
            ProviderStatus.RECOVERING: {ProviderStatus.ACTIVE, ProviderStatus.HEALTHY, ProviderStatus.DEGRADED, ProviderStatus.UNAVAILABLE},
        }

        current_status = provider.status
        if new_status != current_status:
            valid_targets = allowed_transitions.get(current_status, set())
            if new_status not in valid_targets:
                logger.warning(
                    f"Rejected invalid provider status transition from {current_status.value} to {new_status.value} for provider '{provider_id}'."
                )
                return provider

        now_str = datetime.now(timezone.utc).isoformat()
        health_updated = ProviderHealth(
            provider_id=provider.health.provider_id,
            domain=provider.health.domain,
            status=new_status,
            latency_ms=provider.health.latency_ms,
            success_rate_pct=provider.health.success_rate_pct,
            total_requests=provider.health.total_requests,
            failed_requests=provider.health.failed_requests,
            circuit_state=provider.health.circuit_state,
            last_checked=now_str,
            error_message=error_msg or provider.health.error_message,
        )

        updated_provider = IntegrationProvider(
            provider_id=provider.provider_id,
            name=provider.name,
            domain=provider.domain,
            version=provider.version,
            status=new_status,
            configuration=provider.configuration,
            health=health_updated,
            created_at=provider.created_at,
            updated_at=now_str,
        )

        self._providers[provider_id] = updated_provider
        return updated_provider

    def update_health_metrics(
        self,
        provider_id: str,
        latency_ms: float,
        success: bool,
        circuit_state: CircuitState = CircuitState.CLOSED,
    ) -> Optional[IntegrationProvider]:
        """Updates health metrics (latency, success rate, requests, circuit state)."""
        provider = self._providers.get(provider_id)
        if not provider:
            return None

        h = provider.health
        total = h.total_requests + 1
        failed = h.failed_requests + (0 if success else 1)
        success_pct = round(((total - failed) / total) * 100.0, 2)
        now_str = datetime.now(timezone.utc).isoformat()

        health_updated = ProviderHealth(
            provider_id=h.provider_id,
            domain=h.domain,
            status=provider.status,
            latency_ms=round(latency_ms, 2),
            success_rate_pct=success_pct,
            total_requests=total,
            failed_requests=failed,
            circuit_state=circuit_state,
            last_checked=now_str,
            error_message=h.error_message if success else "Execution failure recorded",
        )

        updated_provider = IntegrationProvider(
            provider_id=provider.provider_id,
            name=provider.name,
            domain=provider.domain,
            version=provider.version,
            status=provider.status,
            configuration=provider.configuration,
            health=health_updated,
            created_at=provider.created_at,
            updated_at=now_str,
        )

        self._providers[provider_id] = updated_provider
        return updated_provider
