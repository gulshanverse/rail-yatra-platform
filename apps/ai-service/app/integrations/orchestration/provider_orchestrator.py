"""
Provider Orchestrator: Coordinates adapter resolution, execution, retries, circuit breakers, and metrics.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.integrations.interfaces import ProviderStatus, CircuitState
from app.integrations.models import IntegrationRequest, IntegrationResponse
from app.integrations.registry.provider_registry import ProviderRegistry
from app.integrations.adapters.base_adapter import BaseAdapter
from app.integrations.normalization.normalizer import PayloadNormalizer
from app.integrations.validation.validator import IntegrationValidator
from app.integrations.resilience.retry_policy import RetryPolicy
from app.integrations.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.integrations.monitoring.integration_metrics import IntegrationMetricsCollector

logger = logging.getLogger("ai-service.integrations.orchestration")


class ProviderOrchestrator:
    def __init__(
        self,
        registry: ProviderRegistry,
        normalizer: Optional[PayloadNormalizer] = None,
        validator: Optional[IntegrationValidator] = None,
        metrics: Optional[IntegrationMetricsCollector] = None,
    ) -> None:
        self.registry = registry
        self.normalizer = normalizer or PayloadNormalizer()
        self.validator = validator or IntegrationValidator()
        self.metrics = metrics or IntegrationMetricsCollector()

        self._adapters: Dict[str, BaseAdapter] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register_adapter(self, provider_id: str, adapter: BaseAdapter) -> None:
        """Registers an adapter instance with the orchestrator."""
        adapter.initialize()
        adapter.authenticate()
        self._adapters[provider_id] = adapter
        self._circuit_breakers[provider_id] = CircuitBreaker(
            provider_id=provider_id,
            failure_threshold=adapter.config.circuit_failure_threshold,
            recovery_seconds=adapter.config.circuit_recovery_seconds,
        )
        self.registry.update_status(provider_id, ProviderStatus.HEALTHY)
        logger.info(f"Orchestrator registered adapter for provider '{provider_id}'.")

    def execute_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Orchestrates third-party request execution through validation, retry, circuit breaker, and normalization."""
        start_time = time.time()
        now_str = datetime.now(timezone.utc).isoformat()
        provider_id = request.provider_id

        # 1. Validate provider registration
        provider = self.registry.get_provider(provider_id)
        if not provider:
            return IntegrationResponse(
                request_id=request.request_id,
                provider_id=provider_id,
                domain=request.domain,
                status_code=404,
                success=False,
                data={},
                normalized_data={},
                latency_ms=0.0,
                error_message=f"Provider '{provider_id}' is not registered.",
                timestamp=now_str,
            )

        adapter = self._adapters.get(provider_id)
        circuit = self._circuit_breakers.get(provider_id)

        if not adapter or not circuit:
            return IntegrationResponse(
                request_id=request.request_id,
                provider_id=provider_id,
                domain=request.domain,
                status_code=503,
                success=False,
                data={},
                normalized_data={},
                latency_ms=0.0,
                error_message=f"No active adapter configured for provider '{provider_id}'.",
                timestamp=now_str,
            )

        # 2. Validate request payload
        if not self.validator.validate_request_payload(request.payload):
            return IntegrationResponse(
                request_id=request.request_id,
                provider_id=provider_id,
                domain=request.domain,
                status_code=400,
                success=False,
                data={},
                normalized_data={},
                latency_ms=0.0,
                error_message="Invalid request payload structure.",
                timestamp=now_str,
            )

        retry_policy = RetryPolicy(
            max_retries=provider.configuration.max_retries,
            backoff_factor=provider.configuration.retry_backoff_factor,
        )

        success = True
        raw_output: Dict[str, Any] = {}
        error_msg: Optional[str] = None
        retried = False

        # 3. Execute request wrapped inside circuit breaker and retry policy
        try:
            def _call_target():
                return adapter.execute(request.action, request.payload)

            raw_output = circuit.call(retry_policy.execute_with_retry, _call_target)
        except CircuitBreakerOpenException as exc:
            success = False
            error_msg = str(exc)
            self.registry.update_status(provider_id, ProviderStatus.UNAVAILABLE, error_msg)
        except Exception as exc:
            success = False
            error_msg = str(exc)
            self.registry.update_status(provider_id, ProviderStatus.DEGRADED, error_msg)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        # 4. Normalize response payload
        normalized = {}
        if success:
            normalized = adapter.normalize(raw_output)
            self.registry.update_status(provider_id, ProviderStatus.ACTIVE)

        # 5. Record telemetry
        cb_state = circuit.state if circuit else CircuitState.CLOSED
        self.metrics.record_request(
            provider_id=provider_id,
            domain=request.domain,
            latency_ms=elapsed_ms,
            success=success,
            retried=retried,
            circuit_tripped=(cb_state == CircuitState.OPEN),
        )
        self.registry.update_health_metrics(provider_id, elapsed_ms, success, cb_state)

        return IntegrationResponse(
            request_id=request.request_id,
            provider_id=provider_id,
            domain=request.domain,
            status_code=200 if success else (503 if "Circuit" in (error_msg or "") else 500),
            success=success,
            data=raw_output,
            normalized_data=normalized,
            latency_ms=elapsed_ms,
            error_message=error_msg,
            timestamp=now_str,
        )
