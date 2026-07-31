# RailYatra AI Platform
## Phase 9 – Enterprise Integrations Platform
### Document 3 – Technical Architecture Specification

**Version:** 1.0  
**Phase:** 9  
**Status:** Technical Architecture Baseline  

---

## 1. Project Structure

```
apps/
└── ai-service/
    └── app/
        ├── integrations/
        │   ├── __init__.py
        │   ├── interfaces.py          # Enums (ProviderStatus, IntegrationDomain, etc.), Protocols & Base Contracts
        │   ├── models.py              # Pydantic v2 schemas (IntegrationProvider, ProviderHealth, WebhookEvent, etc.)
        │   ├── gateway/
        │   │   ├── __init__.py
        │   │   └── gateway.py         # Integration Gateway & request router
        │   ├── registry/
        │   │   ├── __init__.py
        │   │   └── provider_registry.py # Provider Registry, discovery & health management
        │   ├── adapters/
        │   │   ├── __init__.py
        │   │   ├── base_adapter.py    # Base Provider Adapter Class
        │   │   ├── railway_adapter.py # Railway Feed Adapter
        │   │   ├── weather_adapter.py # Weather Intelligence Adapter
        │   │   ├── maps_adapter.py    # Maps & Geolocation Adapter
        │   │   ├── payment_adapter.py # Payment Gateway Adapter
        │   │   └── notification_adapter.py # Multi-channel Notification Adapter
        │   ├── normalization/
        │   │   ├── __init__.py
        │   │   └── normalizer.py      # Response Normalization Layer
        │   ├── validation/
        │   │   ├── __init__.py
        │   │   └── validator.py       # Payload & Webhook Validation Layer
        │   ├── orchestration/
        │   │   ├── __init__.py
        │   │   └── provider_orchestrator.py # Provider Execution Orchestrator
        │   ├── webhook/
        │   │   ├── __init__.py
        │   │   ├── webhook_receiver.py# Incoming Webhook Receiver & Signature Verifier
        │   │   └── webhook_sender.py  # Outgoing Webhook Dispatcher
        │   ├── resilience/
        │   │   ├── __init__.py
        │   │   ├── retry_policy.py    # Exponential Backoff Retry Policy
        │   │   └── circuit_breaker.py # Circuit Breaker (CLOSED, OPEN, HALF_OPEN)
        │   ├── monitoring/
        │   │   ├── __init__.py
        │   │   ├── integration_metrics.py # Latency & Counter Telemetry
        │   │   └── provider_monitor.py # Provider Health Tracker
        │   └── configuration/
        │       ├── __init__.py
        │       └── provider_config.py # Config Loader & Secret Management
        ├── api/
        │   └── integration_router.py   # REST API router (/api/integrations/*)
        └── tests/
            └── test_enterprise_integrations.py # Phase 9 Test Suite
```

---

## 2. API Endpoints

- `GET /api/integrations/providers` – List all registered integration providers.
- `GET /api/integrations/providers/{provider_id}` – Retrieve detailed provider metadata and health.
- `GET /api/integrations/health` – Return health summary across all integration adapters.
- `POST /api/integrations/webhooks` – Ingest and process incoming webhooks with signature validation.
- `POST /api/integrations/test` – Execute an integration test request through the provider orchestrator.
- `GET /api/integrations/metrics` – Retrieve telemetry metrics (request counts, latency, circuit breaker state).

---

## 3. Provider State Machine

```
REGISTERED -> INITIALIZED -> AUTHENTICATED -> HEALTHY -> ACTIVE -> DEGRADED -> UNAVAILABLE -> RECOVERING -> ACTIVE
```
Illegal state transitions (e.g. `UNAVAILABLE` directly to `ACTIVE` without `RECOVERING`) are blocked and logged.
