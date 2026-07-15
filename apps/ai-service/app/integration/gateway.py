# app/integration/gateway.py
import time
import uuid
import base64
import logging
from typing import Dict, Any, Optional, Type, Tuple
from pydantic import BaseModel

from app.integration.interfaces import (
    IIntegrationGateway,
    IProviderRegistry,
    IProviderRouter,
    IAuthenticationManager,
    ICredentialVault,
    ICapabilityNegotiator,
    NormalizedResponse,
)
from app.integration.models import (
    CorrelationContext,
    PNRStatusResponse,
    TrainStatusResponse,
)
from app.integration.exceptions import ProviderRateLimitError
from app.integration.resiliency.limiter import TokenBucketRateLimiter
from app.integration.resiliency.breaker import CircuitBreaker
from app.integration.resiliency.retry import RetryEngine
from app.integration.resiliency.health import HealthMonitor

logger = logging.getLogger("ai-service.integration.gateway")


class IntegrationGateway(IIntegrationGateway, ICapabilityNegotiator):
    def __init__(
        self,
        registry: IProviderRegistry,
        router: IProviderRouter,
        auth_manager: IAuthenticationManager,
        vault: ICredentialVault,
        redis_client=None,
    ):
        self.registry = registry
        self.router = router
        self.auth_manager = auth_manager
        self.vault = vault
        self.redis_client = redis_client

        # Resiliency components
        self.rate_limiter = TokenBucketRateLimiter(redis_client)
        self.health_monitor = HealthMonitor(registry)
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Cache backend reference (Redis or local dict)
        self._local_cache: Dict[
            str, Tuple[str, float]
        ] = {}  # key -> (encrypted_payload, expires_at)

        # Pluggable adapters: provider_id -> IProviderAdapter
        self._adapters: Dict[str, Any] = {}

        # Dynamic feature flags
        self.canary_percentage: Dict[str, float] = {}

    def register_adapter(self, adapter: Any) -> None:
        self._adapters[adapter.provider_id] = adapter
        logger.info(f"Gateway registered adapter: {adapter.provider_id}")

    def _get_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        if provider_id not in self._circuit_breakers:
            self._circuit_breakers[provider_id] = CircuitBreaker(
                provider_id=provider_id, redis_client=self.redis_client
            )
        return self._circuit_breakers[provider_id]

    # ==========================================
    # Capability Negotiation (Section 5.3)
    # ==========================================
    def negotiate_capability(
        self, provider_id: str, capability: str, requested_version: str
    ) -> Tuple[bool, str]:
        # Validate if provider metadata contains capability
        for p in self.registry.list_all_providers():
            if p.provider_id == provider_id:
                if capability not in p.capabilities:
                    return (
                        False,
                        f"Capability '{capability}' not supported by provider '{provider_id}'",
                    )
                if p.status == "offline":
                    return False, f"Provider '{provider_id}' is offline"
                return True, "Negotiated"
        return False, f"Provider '{provider_id}' not found in registry"

    # ==========================================
    # Caching Encryption Helper (AES-256 Mock/XOR)
    # ==========================================
    def _encrypt_cache_value(self, value: str) -> str:
        # Secure simulation of AES-256 encryption using base64 and XOR key
        key = b"RailYatraSecureKey32BytesLong12"
        b_val = value.encode("utf-8")
        xor_val = bytes(b_val[i] ^ key[i % len(key)] for i in range(len(b_val)))
        return base64.b64encode(xor_val).decode("utf-8")

    def _decrypt_cache_value(self, encrypted_value: str) -> str:
        key = b"RailYatraSecureKey32BytesLong12"
        xor_val = base64.b64decode(encrypted_value.encode("utf-8"))
        b_val = bytes(xor_val[i] ^ key[i % len(key)] for i in range(len(xor_val)))
        return b_val.decode("utf-8")

    def _get_cache(self, key: str) -> Optional[str]:
        now = time.time()
        if self.redis_client:
            try:
                val = self.redis_client.get(f"cache:{key}")
                if val:
                    decrypted = self._decrypt_cache_value(val.decode("utf-8"))
                    return decrypted
            except Exception as e:
                logger.warning(f"Redis cache fetch failed: {e}")

        # Local cache check
        if key in self._local_cache:
            enc_payload, expires_at = self._local_cache[key]
            if now < expires_at:
                return self._decrypt_cache_value(enc_payload)
            else:
                self._local_cache.pop(key, None)
        return None

    def _set_cache(self, key: str, value: str, ttl_seconds: int = 30) -> None:
        enc_payload = self._encrypt_cache_value(value)
        if self.redis_client:
            try:
                self.redis_client.setex(f"cache:{key}", ttl_seconds, enc_payload)
                return
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")

        # Local cache set
        self._local_cache[key] = (enc_payload, time.time() + ttl_seconds)

    # ==========================================
    # Gateway Query Dispatching
    # ==========================================
    async def execute(
        self,
        capability: str,
        payload: Dict[str, Any],
        context: Optional[CorrelationContext] = None,
    ) -> NormalizedResponse:
        start_time = time.time()

        # 1. Establish Correlation & Tracing Context (Section 4.3)
        correlation_id = (
            context.correlation_id if context else f"corr-{uuid.uuid4().hex[:12]}"
        )
        request_id = context.request_id if context else f"req-{uuid.uuid4().hex[:12]}"
        trace_id = context.trace_id if context else f"tr-{uuid.uuid4().hex[:12]}"
        session_id = context.session_id if context else None

        # Scrub sensitive input values (Redaction filters) in logging outputs
        logged_payload = payload.copy()
        if "pnr" in logged_payload:
            logged_payload["pnr"] = "******" + str(logged_payload["pnr"])[-4:]

        logger.info(
            f"[{trace_id}] Gateway dispatch request: req_id='{request_id}', correlation_id='{correlation_id}', session_id='{session_id}', capability='{capability}', params={logged_payload}"
        )

        # 2. Check Cache layer first to avoid network overhead
        cache_key = f"{capability}:{hash(frozenset(payload.items()))}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            logger.info(
                f"[{trace_id}] Cache hit for capability '{capability}' key: {cache_key}"
            )
            import json

            latency = (time.time() - start_time) * 1000
            return NormalizedResponse(
                success=True,
                provider_id="cache_hit",
                latency_ms=latency,
                data=json.loads(cached_data),
            )

        # 3. Resolve Provider Route based on current policy profiles
        try:
            provider = self.router.resolve_provider(capability)
        except Exception as e:
            logger.error(f"[{trace_id}] Routing failed: {e}")
            return NormalizedResponse(
                success=False,
                provider_id="none",
                latency_ms=(time.time() - start_time) * 1000,
                data={},
                error_message=str(e),
            )

        # 4. Negotiate Capability before executing
        is_supported, reason = self.negotiate_capability(
            provider.provider_id, capability, provider.version
        )
        if not is_supported:
            logger.warning(
                f"[{trace_id}] Pre-flight negotiation failed for {provider.provider_id}: {reason}"
            )
            # Dynamic fallback to second-ranked provider
            try:
                # Bypass current failing provider by setting status offline temporarily
                self.registry.update_provider_status(provider.provider_id, "offline")
                provider = self.router.resolve_provider(capability)
            except Exception as ex:
                return NormalizedResponse(
                    success=False,
                    provider_id="none",
                    latency_ms=(time.time() - start_time) * 1000,
                    data={},
                    error_message=f"Pre-flight negotiation failed: {reason}. Fallback routing crashed: {ex}",
                )

        # 5. Check Rate Limits
        try:
            await self.rate_limiter.check_rate_limit(provider.provider_id, capability)
        except ProviderRateLimitError as e:
            logger.warning(
                f"[{trace_id}] Provider {provider.provider_id} rate limited: {e}"
            )
            return NormalizedResponse(
                success=False,
                provider_id=provider.provider_id,
                latency_ms=(time.time() - start_time) * 1000,
                data={},
                error_message=str(e),
            )

        # 6. Check Circuit Breaker
        breaker = self._get_circuit_breaker(provider.provider_id)
        try:
            await breaker.check_allow_request()
        except Exception as e:
            logger.warning(f"[{trace_id}] Circuit breaker blocked query: {e}")
            return NormalizedResponse(
                success=False,
                provider_id=provider.provider_id,
                latency_ms=(time.time() - start_time) * 1000,
                data={},
                error_message=str(e),
            )

        # 7. Execute Query wrapped inside Retry Engine
        adapter = self._adapters.get(provider.provider_id)
        if not adapter:
            return NormalizedResponse(
                success=False,
                provider_id=provider.provider_id,
                latency_ms=(time.time() - start_time) * 1000,
                data={},
                error_message=f"No local adapter implementation registered for provider '{provider.provider_id}'",
            )

        # Resolve expected return model class
        ret_model: Type[BaseModel] = BaseModel
        if capability == "pnr_lookup":
            ret_model = PNRStatusResponse
        elif capability == "live_train_status":
            ret_model = TrainStatusResponse

        async def query_wrapper():
            # Inbound validation schema verification
            return await adapter.execute_query(capability, payload, ret_model)

        success = False
        res_data = {}
        err_msg = None

        try:
            # Run wrapper through retry engine
            result_dto = await RetryEngine.execute_with_retry(
                query_wrapper,
                max_attempts=provider.rate_limits.burst_limit
                if provider.rate_limits.burst_limit < 3
                else 3,
                base_delay=0.1,
            )
            success = True
            res_data = result_dto.model_dump()

            # Cache the response DTO
            import json

            self._set_cache(cache_key, json.dumps(res_data))
        except Exception as e:
            err_msg = str(e)
            logger.error(f"[{trace_id}] Query execution failed after retries: {e}")

        # 8. Record metrics for Circuit Breakers and Health Monitors
        await breaker.record_result(success)
        latency = (time.time() - start_time) * 1000
        self.health_monitor.record_heartbeat(provider.provider_id, latency, success)

        return NormalizedResponse(
            success=success,
            provider_id=provider.provider_id,
            latency_ms=latency,
            data=res_data,
            error_message=err_msg,
        )
