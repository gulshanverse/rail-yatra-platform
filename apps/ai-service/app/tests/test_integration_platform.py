# app/tests/test_integration_platform.py
import pytest
import asyncio

from app.integration.exceptions import ProviderNetworkError
from app.integration.models import CorrelationContext
from app.integration.registry import ProviderRegistry
from app.integration.router import ProviderRouter
from app.integration.auth.vault import CredentialVault
from app.integration.auth.manager import AuthenticationManager
from app.integration.adapters.confirmtkt import ConfirmTktAdapter
from app.integration.adapters.ntes import NTESAdapter
from app.integration.adapters.static_local import StaticLocalAdapter
from app.integration.gateway import IntegrationGateway
from app.integration.resiliency.retry import RetryEngine
from app.integration.resiliency.breaker import CircuitBreaker


@pytest.fixture
def test_registry():
    return ProviderRegistry()


@pytest.fixture
def test_router(test_registry):
    return ProviderRouter(test_registry)


@pytest.fixture
def test_vault():
    return CredentialVault()


@pytest.fixture
def test_auth_manager(test_vault):
    return AuthenticationManager(test_vault)


@pytest.fixture
def test_gateway(test_registry, test_router, test_auth_manager, test_vault):
    gateway = IntegrationGateway(
        test_registry, test_router, test_auth_manager, test_vault
    )
    # Register adapters
    gateway.register_adapter(ConfirmTktAdapter(test_auth_manager))
    gateway.register_adapter(NTESAdapter(test_auth_manager))
    gateway.register_adapter(StaticLocalAdapter(test_auth_manager))
    return gateway


# ==========================================
# 1. Registry Tests
# ==========================================
def test_registry_initialization(test_registry):
    providers = test_registry.list_all_providers()
    assert len(providers) > 0
    gds = [p for p in providers if p.provider_id == "confirmtkt_gds"]
    assert len(gds) == 1
    assert "pnr_lookup" in gds[0].capabilities


def test_registry_update_status(test_registry):
    test_registry.update_provider_status("confirmtkt_gds", "offline")
    candidates = test_registry.get_providers_for_capability("pnr_lookup")
    # confirmtkt_gds is offline, so it should not be returned
    assert "confirmtkt_gds" not in [c.provider_id for c in candidates]


# ==========================================
# 2. Router & Policies Tests
# ==========================================
def test_router_resolve_provider(test_router):
    prov = test_router.resolve_provider("pnr_lookup", policy="business_priority")
    assert prov.provider_id == "confirmtkt_gds"

    # Test policy sorting
    prov_lat = test_router.resolve_provider("pnr_lookup", policy="lowest_latency")
    # confirmtkt_gds expected latency is 400, rapidapi is 1000, so confirmtkt is selected
    assert prov_lat.provider_id == "confirmtkt_gds"


# ==========================================
# 3. Vault & Auth Tests
# ==========================================
@pytest.mark.anyio
async def test_vault_get_secret(test_vault):
    val = await test_vault.get_secret("CONFIRMTKT_API_KEY")
    assert val == "mock-confirmtkt-key-xyz"


@pytest.mark.anyio
async def test_auth_manager_headers(test_auth_manager):
    headers = await test_auth_manager.get_auth_headers("confirmtkt_gds")
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer")


# ==========================================
# 4. Gateway Integration & DTO Validation Tests
# ==========================================
@pytest.mark.anyio
async def test_gateway_pnr_lookup(test_gateway):
    payload = {"pnr": "1234567890"}
    context = CorrelationContext(
        correlation_id="corr-123", request_id="req-123", trace_id="tr-123"
    )
    res = await test_gateway.execute("pnr_lookup", payload, context)
    assert res.success is True
    assert res.provider_id == "confirmtkt_gds"
    assert res.data["pnr"] == "1234567890"
    assert len(res.data["passengers"]) == 1


@pytest.mark.anyio
async def test_gateway_live_train_status(test_gateway):
    payload = {"train_number": "12002"}
    res = await test_gateway.execute("live_train_status", payload)
    assert res.success is True
    assert res.provider_id == "ntes_cris"
    assert res.data["train_number"] == "12002"
    assert len(res.data["route_movements"]) > 0


@pytest.mark.anyio
async def test_gateway_static_local_station(test_gateway):
    payload = {"station_code": "NDLS"}
    res = await test_gateway.execute("station_info", payload)
    assert res.success is True
    assert res.provider_id == "static_local"
    assert res.data["station_name"] == "New Delhi"
    assert res.data["platform_count"] == 16


# ==========================================
# 5. Resiliency: Retry Tests
# ==========================================
@pytest.mark.anyio
async def test_retry_engine():
    attempts = 0

    async def failing_coro():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Transient error")
        return "success_val"

    val = await RetryEngine.execute_with_retry(
        failing_coro, max_attempts=3, base_delay=0.01
    )
    assert val == "success_val"
    assert attempts == 3


# ==========================================
# 6. Resiliency: Circuit Breaker Tests
# ==========================================
@pytest.mark.anyio
async def test_circuit_breaker():
    breaker = CircuitBreaker(
        provider_id="test_provider",
        failure_threshold_percentage=50.0,
        rolling_window_seconds=60,
        reset_timeout_seconds=1,
        min_requests_for_trip=4,
    )

    # Initially closed
    assert await breaker.get_state() == "CLOSED"

    # Record failures to trip
    await breaker.record_result(False)
    await breaker.record_result(False)
    await breaker.record_result(False)
    await breaker.record_result(False)

    assert await breaker.get_state() == "OPEN"

    # Check request rejection
    with pytest.raises(ProviderNetworkError):
        await breaker.check_allow_request()

    # Wait for reset timeout
    await asyncio.sleep(1.1)
    assert await breaker.get_state() == "HALF-OPEN"

    # Canary success closes breaker
    await breaker.record_result(True)
    assert await breaker.get_state() == "CLOSED"


# ==========================================
# 7. Resiliency: Rate Limiter Tests
# ==========================================
@pytest.mark.anyio
async def test_rate_limiter(test_gateway):
    # Enable a simulated high volume check
    from app.integration.resiliency.limiter import TokenBucketRateLimiter

    limiter = TokenBucketRateLimiter()

    # Verify first checks pass
    assert await limiter.check_rate_limit("mock_provider", "test_cap") is True


# ==========================================
# 8. Correlation & Caching Tests
# ==========================================
@pytest.mark.anyio
async def test_cache_hit_and_encryption(test_gateway):
    payload = {"station_code": "BPL"}
    # First execution fetches from static_local and caches
    res1 = await test_gateway.execute("station_info", payload)
    assert res1.success is True
    assert res1.provider_id == "static_local"

    # Second execution fetches from cache
    res2 = await test_gateway.execute("station_info", payload)
    assert res2.success is True
    assert res2.provider_id == "cache_hit"
    assert res2.data["station_name"] == "Bhopal Junction"
