"""
Phase 9 Enterprise Integrations Platform Test Suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.gateway import IntegrationGateway
from app.integrations.registry.provider_registry import ProviderRegistry
from app.integrations.interfaces import ProviderStatus, IntegrationDomain, WebhookEventType, CircuitState
from app.integrations.models import ProviderConfiguration
from app.integrations.adapters.railway_adapter import RailwayAdapter
from app.integrations.adapters.weather_adapter import WeatherAdapter
from app.integrations.adapters.maps_adapter import MapsAdapter
from app.integrations.adapters.payment_adapter import PaymentAdapter
from app.integrations.adapters.notification_adapter import NotificationAdapter
from app.integrations.normalization.normalizer import PayloadNormalizer
from app.integrations.validation.validator import IntegrationValidator
from app.integrations.resilience.retry_policy import RetryPolicy
from app.integrations.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.integrations.webhook.webhook_receiver import WebhookReceiver
from app.integrations.webhook.webhook_sender import WebhookSender


client = TestClient(app)


class TestProviderRegistry:
    def test_register_and_get_provider(self):
        reg = ProviderRegistry()
        cfg = ProviderConfiguration(
            provider_id="test_provider",
            domain=IntegrationDomain.RAILWAY,
            base_url="https://test.example.com",
        )
        provider = reg.register_provider("test_provider", "Test Provider", IntegrationDomain.RAILWAY, cfg)
        assert provider.provider_id == "test_provider"
        assert provider.status == ProviderStatus.REGISTERED

        fetched = reg.get_provider("test_provider")
        assert fetched is not None
        assert fetched.name == "Test Provider"

    def test_status_state_machine(self):
        reg = ProviderRegistry()
        cfg = ProviderConfiguration(
            provider_id="test_provider",
            domain=IntegrationDomain.RAILWAY,
            base_url="https://test.example.com",
        )
        reg.register_provider("test_provider", "Test Provider", IntegrationDomain.RAILWAY, cfg)

        # Valid transition: REGISTERED -> INITIALIZED
        updated = reg.update_status("test_provider", ProviderStatus.INITIALIZED)
        assert updated.status == ProviderStatus.INITIALIZED

        # Invalid transition attempt: INITIALIZED -> COMPLETED (Not in allowed set)
        rejected = reg.update_status("test_provider", ProviderStatus.REGISTERED)
        assert rejected.status == ProviderStatus.INITIALIZED

    def test_list_providers_by_domain(self):
        reg = ProviderRegistry()
        cfg = ProviderConfiguration(
            provider_id="p1",
            domain=IntegrationDomain.WEATHER,
            base_url="https://w.example.com",
        )
        reg.register_provider("p1", "Weather P1", IntegrationDomain.WEATHER, cfg)
        weather_list = reg.get_providers_by_domain(IntegrationDomain.WEATHER)
        assert len(weather_list) == 1
        assert weather_list[0].provider_id == "p1"


class TestAdapters:
    def test_railway_adapter(self):
        cfg = ProviderConfiguration(
            provider_id="railway_ntes",
            domain=IntegrationDomain.RAILWAY,
            base_url="https://rail.example.com",
            api_key="mock_key",
        )
        adapter = RailwayAdapter(cfg)
        adapter.initialize()
        assert adapter.authenticate() is True

        raw = adapter.execute("TRACK", {"train_number": "12951", "delay_minutes": 15})
        norm = adapter.normalize(raw)
        assert norm["train_number"] == "12951"
        assert norm["delay_minutes"] == 15
        assert norm["source_provider"] == "railway_ntes"
        adapter.shutdown()
        assert adapter.is_initialized is False

    def test_weather_adapter(self):
        cfg = ProviderConfiguration(
            provider_id="weather_openmeteo",
            domain=IntegrationDomain.WEATHER,
            base_url="https://weather.example.com",
        )
        adapter = WeatherAdapter(cfg)
        adapter.initialize()
        raw = adapter.execute("GET_WEATHER", {"station_code": "NDLS", "condition": "DENSE_FOG"})
        norm = adapter.normalize(raw)
        assert norm["station_code"] == "NDLS"
        assert norm["journey_delay_risk"] is True

    def test_maps_adapter(self):
        cfg = ProviderConfiguration(
            provider_id="maps_google",
            domain=IntegrationDomain.MAPS,
            base_url="https://maps.example.com",
        )
        adapter = MapsAdapter(cfg)
        adapter.initialize()
        raw = adapter.execute("NAVIGATE", {"latitude": 28.61, "longitude": 77.20})
        norm = adapter.normalize(raw)
        assert norm["nearest_station"] == "NDLS"
        assert norm["distance_km"] == 1.2

    def test_payment_adapter(self):
        cfg = ProviderConfiguration(
            provider_id="payment_razorpay",
            domain=IntegrationDomain.PAYMENTS,
            base_url="https://pay.example.com",
            api_key="rzp_key",
        )
        adapter = PaymentAdapter(cfg)
        adapter.initialize()
        raw = adapter.execute("PAY", {"transaction_id": "TXN_100", "amount": 500.0})
        norm = adapter.normalize(raw)
        assert norm["transaction_id"] == "TXN_100"
        assert norm["amount"] == 500.0

    def test_notification_adapter(self):
        cfg = ProviderConfiguration(
            provider_id="notification_multi",
            domain=IntegrationDomain.NOTIFICATIONS,
            base_url="https://notify.example.com",
            api_key="notify_key",
        )
        adapter = NotificationAdapter(cfg)
        adapter.initialize()
        raw = adapter.execute("SEND", {"channel": "SMS", "recipient": "+919999999999"})
        norm = adapter.normalize(raw)
        assert norm["channel"] == "SMS"
        assert norm["delivery_status"] == "DELIVERED"


class TestNormalizerAndValidator:
    def test_payload_normalizer(self):
        norm = PayloadNormalizer()
        res = norm.normalize_payload(IntegrationDomain.RAILWAY, "p1", {"raw_train_no": "12002", "raw_delay": "5"})
        assert res["train_number"] == "12002"
        assert res["delay_minutes"] == 5

    def test_validator_signature(self):
        val = IntegrationValidator()
        body = "test_body"
        secret = "secret123"
        import hmac
        import hashlib
        sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        assert val.verify_webhook_signature(body, secret, sig) is True
        assert val.verify_webhook_signature(body, secret, "invalid_sig") is False


class TestResilience:
    def test_retry_policy_success(self):
        policy = RetryPolicy(max_retries=2, backoff_factor=0.01)
        count = 0

        def _work():
            nonlocal count
            count += 1
            if count < 2:
                raise ValueError("Transient error")
            return "SUCCESS"

        res = policy.execute_with_retry(_work)
        assert res == "SUCCESS"
        assert count == 2

    def test_circuit_breaker_tripping(self):
        cb = CircuitBreaker(provider_id="fail_prov", failure_threshold=2, recovery_seconds=0.1)

        def _always_fail():
            raise RuntimeError("Provider down")

        with pytest.raises(RuntimeError):
            cb.call(_always_fail)

        with pytest.raises(RuntimeError):
            cb.call(_always_fail)

        assert cb.state == CircuitState.OPEN

        # Next call while open raises CircuitBreakerOpenException
        with pytest.raises(CircuitBreakerOpenException):
            cb.call(_always_fail)


class TestWebhookEngines:
    def test_webhook_receiver(self):
        rec = WebhookReceiver()
        event = rec.receive_webhook("railway_ntes", WebhookEventType.TRAIN_UPDATED, {"train": "12951"})
        assert event.processed is True
        assert event.provider_id == "railway_ntes"

        fetched = rec.get_event(event.event_id)
        assert fetched is not None
        assert len(rec.list_events()) == 1

    def test_webhook_sender(self):
        sender = WebhookSender()
        res = sender.dispatch_webhook("https://subscriber.com/hook", "TRAIN_DELAY", {"delay": 20}, secret="sec")
        assert res["status"] == "DISPATCHED"
        assert res["signature"] is not None


class TestGatewayAndOrchestrator:
    def test_gateway_bootstrap_and_execution(self):
        gateway = IntegrationGateway()
        providers = gateway.registry.list_all_providers()
        assert len(providers) >= 5

        response = gateway.execute_integration("railway_ntes", "TRACK", {"train_number": "12004"})
        assert response.success is True
        assert response.normalized_data["train_number"] == "12004"

    def test_gateway_health_check(self):
        gateway = IntegrationGateway()
        health = gateway.get_system_health()
        assert health["overall_status"] == "HEALTHY"
        assert health["total_providers"] >= 5


class TestIntegrationAPIRoutes:
    def test_list_providers_endpoint(self):
        res = client.get("/api/integrations/providers")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 5

    def test_get_provider_details_endpoint(self):
        res = client.get("/api/integrations/providers/railway_ntes")
        assert res.status_code == 200
        data = res.json()
        assert data["provider_id"] == "railway_ntes"

    def test_get_provider_not_found(self):
        res = client.get("/api/integrations/providers/non_existent")
        assert res.status_code == 404

    def test_health_endpoint(self):
        res = client.get("/api/integrations/health")
        assert res.status_code == 200
        data = res.json()
        assert "overall_status" in data

    def test_execute_test_request_endpoint(self):
        payload = {
            "provider_id": "weather_openmeteo",
            "action": "GET_WEATHER",
            "payload": {"station_code": "NDLS", "condition": "DENSE_FOG"},
        }
        res = client.post("/api/integrations/test", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["normalized_data"]["journey_delay_risk"] is True

    def test_ingest_webhook_endpoint(self):
        payload = {
            "provider_id": "payment_razorpay",
            "event_type": "PAYMENT_CONFIRMED",
            "payload": {"txn_id": "TXN_7766"},
        }
        res = client.post("/api/integrations/webhooks", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["processed"] is True

    def test_metrics_endpoint(self):
        res = client.get("/api/integrations/metrics")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, dict)
