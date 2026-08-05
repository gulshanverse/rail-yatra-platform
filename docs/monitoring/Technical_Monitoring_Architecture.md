# RailYatra AI Platform — Technical Monitoring Architecture & Blueprint

## Executive Technical Overview

This document specifies the exact **Technical Design & Repository Implementation Specification** for the **RailYatra AI Platform Monitoring System**. It translates the Enterprise Architecture (Document 2) into a precise technical blueprint ready for implementation across `apps/frontend`, `apps/backend`, `apps/ai-service`, and `.github/workflows`.

---

## Target Repository Directory Hierarchy

```text
Rail-Yatra/
├── apps/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── lib/
│   │   │   │   └── monitoring/
│   │   │   │       ├── sentry.client.config.ts    # Sentry Client SDK Init
│   │   │   │       ├── sentry.server.config.ts    # Sentry Server Side Init
│   │   │   │       ├── sentry.edge.config.ts      # Sentry Edge Worker Init
│   │   │   │       ├── web-vitals.ts              # Core Web Vitals Collector
│   │   │   │       └── posthog.ts                 # Product Analytics SDK Wrapper
│   │   │   └── components/
│   │   │       └── ErrorBoundary.tsx              # React Sentry Error Boundary
│   │   ├── next.config.ts                         # Next.js Sentry Plugin Config
│   │   └── package.json                           # @sentry/nextjs, posthog-js
│   │
│   ├── backend/
│   │   ├── src/
│   │   │   ├── monitoring/
│   │   │   │   ├── monitoring.module.ts           # NestJS Monitoring Module
│   │   │   │   ├── sentry.service.ts              # Sentry NestJS Service
│   │   │   │   ├── prometheus.controller.ts       # Exposes GET /metrics
│   │   │   │   ├── metrics.service.ts             # Custom NestJS Metrics Collector
│   │   │   │   ├── trace.middleware.ts            # W3C Trace Context Middleware
│   │   │   │   └── logging.interceptor.ts         # Updated Structured Logger
│   │   │   └── app.module.ts                      # Imports MonitoringModule
│   │   └── package.json                           # @sentry/nestjs, prom-client
│   │
│   └── ai-service/
│       ├── app/
│       │   ├── monitoring/
│       │   │   ├── __init__.py
│       │   │   ├── sentry_config.py               # Sentry Python SDK Configuration
│       │   │   ├── metrics_collector.py           # Enhanced Prometheus Exporter
│       │   │   ├── otel_tracer.py                 # OpenTelemetry Tracer Provider
│       │   │   ├── logger_formatter.py            # JSON Formatter with Redaction
│       │   │   └── middleware.py                  # FastAPI Monitoring Middleware
│       │   └── main.py                            # Registers Monitoring Middleware
│       └── requirements.txt                       # sentry-sdk, opentelemetry-api
│
├── docs/
│   └── monitoring/
│       ├── Monitoring_Discovery_Strategy.md       # Document 1
│       ├── Enterprise_Monitoring_Architecture.md   # Document 2
│       └── Technical_Monitoring_Architecture.md    # Document 3 (This File)
│
└── .github/
    └── workflows/
        ├── ci.yml                                 # CI with Linting & Monitoring Tests
        └── deploy.yml                             # Release Tagging & Sentry Deployment
```

---

## Detailed Technology Integration Specifications

### 1. Sentry Integration Blueprint

#### Frontend (`apps/frontend`)
- **Packages**: `@sentry/nextjs`
- **Config Files**:
  - `sentry.client.config.ts`: Client-side error capturing, browser tracing, session replay.
  - `sentry.server.config.ts`: Node.js server component error capturing.
  - `sentry.edge.config.ts`: Vercel Edge Runtime error capturing.
- **Environment Variables**:
  - `NEXT_PUBLIC_SENTRY_DSN`: `https://***@o***.ingest.sentry.io/***`
  - `SENTRY_AUTH_TOKEN`: *(CI/CD pipeline build secret for uploading source maps)*
- **Configuration Defaults**:
  - `tracesSampleRate`: `0.1` (10% of transactions in production).
  - `replaysSessionSampleRate`: `0.01` (1% of normal user sessions).
  - `replaysOnErrorSampleRate`: `1.0` (100% of sessions with unhandled errors).

#### Backend Core API (`apps/backend`)
- **Packages**: `@sentry/nestjs`, `@sentry/node`
- **Module**: `apps/backend/src/monitoring/sentry.service.ts`
- **Initialization**: Integrated inside `main.ts` prior to NestFactory bootstrap.
- **Environment Variables**:
  - `SENTRY_DSN`: `https://***@o***.ingest.sentry.io/***`
  - `SENTRY_ENVIRONMENT`: `production` | `staging` | `development`

#### AI Service (`apps/ai-service`)
- **Packages**: `sentry-sdk[fastapi]`
- **Initialization**: Called inside `app/main.py` before FastAPI app instantiation.
- **Integration**:
  ```python
  import sentry_sdk
  from sentry_sdk.integrations.fastapi import FastApiIntegration

  sentry_sdk.init(
      dsn=os.getenv("SENTRY_DSN"),
      environment=os.getenv("ENV", "production"),
      traces_sample_rate=0.1,
      integrations=[FastApiIntegration()],
  )
  ```

---

### 2. Better Stack Integration Blueprint

#### A. Synthetic Uptime Monitoring Probes
Better Stack monitors platform endpoints at 60-second intervals from 3 global regions:

| Probe Name | Target URL | HTTP Method | Expected Status | Max Latency Threshold | Alert Escalation |
|------------|------------|-------------|-----------------|-----------------------|------------------|
| **Frontend UI** | `https://railyatra-frontend.vercel.app` | `GET` | `200 OK` | 2000ms | P1 Warning |
| **Backend Live** | `https://railyatra-backend.onrender.com/api/health/live` | `GET` | `200 OK` | 1000ms | P0 Critical |
| **Backend Ready** | `https://railyatra-backend.onrender.com/api/health/ready` | `GET` | `200 OK` | 1500ms | P0 Critical |
| **AI Service Health**| `https://railyatra-ai-service.onrender.com/health` | `GET` | `200 OK` | 1200ms | P0 Critical |

#### B. Log Aggregation Drain
- **Render Log Drain**: Configure Render Log Drain HTTP target pointing to `https://in.logs.betterstack.com` with bearer token authentication.
- **Vercel Log Drain**: Enable Vercel Better Stack integration for stdout streaming.

---

### 3. Prometheus Metrics & Namespace Specification

All metric names follow the strict naming convention: `railyatra_<subsystem>_<metric_name>_<unit>`.

```text
# HELP railyatra_backend_http_requests_total Total HTTP requests processed by NestJS
# TYPE railyatra_backend_http_requests_total counter
railyatra_backend_http_requests_total{method="POST",path="/api/journey/search",status="200"} 1420

# HELP railyatra_backend_http_request_duration_seconds HTTP request latency histogram
# TYPE railyatra_backend_http_request_duration_seconds histogram
railyatra_backend_http_request_duration_seconds_bucket{le="0.1"} 980
railyatra_backend_http_request_duration_seconds_bucket{le="0.5"} 1390
railyatra_backend_http_request_duration_seconds_bucket{le="1.0"} 1415
railyatra_backend_http_request_duration_seconds_bucket{le="+Inf"} 1420

# HELP railyatra_ai_stream_first_token_seconds Time to first token for SSE responses
# TYPE railyatra_ai_stream_first_token_seconds histogram
railyatra_ai_stream_first_token_seconds_bucket{provider="gemini",le="0.5"} 410
railyatra_ai_stream_first_token_seconds_bucket{provider="gemini",le="1.0"} 890

# HELP railyatra_ai_tokens_consumed_total Total LLM tokens used by provider
# TYPE railyatra_ai_tokens_consumed_total counter
railyatra_ai_tokens_consumed_total{provider="gemini",type="prompt"} 452000
railyatra_ai_tokens_consumed_total{provider="gemini",type="completion"} 128000

# HELP railyatra_ai_provider_fallback_total Total times model provider fallback was triggered
# TYPE railyatra_ai_provider_fallback_total counter
railyatra_ai_provider_fallback_total{from_provider="openai",to_provider="gemini"} 12
```

---

## Grafana Dashboard Panel Queries (PromQL)

### Panel 1: API HTTP Request Rate (RPS)
```promql
sum(rate(railyatra_backend_http_requests_total[2m])) by (method, status)
```

### Panel 2: API Response Latency (p95 & p99)
```promql
histogram_quantile(0.95, sum(rate(railyatra_backend_http_request_duration_seconds_bucket[5m])) by (le))
```

### Panel 3: AI Service Time-To-First-Token (TTFT p95)
```promql
histogram_quantile(0.95, sum(rate(railyatra_ai_stream_first_token_seconds_bucket[5m])) by (le, provider))
```

### Panel 4: Redis Cache Hit Ratio Percentage
```promql
(sum(rate(railyatra_redis_hits_total[5m])) / (sum(rate(railyatra_redis_hits_total[5m])) + sum(rate(railyatra_redis_misses_total[5m])))) * 100
```

---

## Structured Logging & Redaction Specification

### Standardized JSON Log Schema

```json
{
  "timestamp": "2026-08-04T22:00:00.123Z",
  "level": "INFO",
  "service": "railyatra-backend",
  "environment": "production",
  "correlation_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "category": "REQUEST",
  "context": {
    "method": "POST",
    "path": "/api/journey/search",
    "status_code": 200,
    "duration_ms": 142.5,
    "user_id": "usr_sha256_8f9a2b...",
    "client_ip": "103.21.126.xxx"
  },
  "message": "HTTP POST /api/journey/search 200 - 142.5ms"
}
```

### Automated Redaction Rules Matrix

```typescript
// Sanitization target regex patterns enforced in LoggingInterceptor
const REDACTION_PATTERNS = [
  { key: /password|pass|pwd/i, replace: '[REDACTED_PASSWORD]' },
  { key: /token|jwt|auth|bearer/i, replace: '[REDACTED_TOKEN]' },
  { key: /api_key|secret|private_key/i, replace: '[REDACTED_KEY]' },
  { key: /pnr|mobile|phone/i, replace: '[REDACTED_PII]' },
  { value: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i, replace: '[REDACTED_EMAIL]' },
  { value: /\b\d{10}\b/g, replace: '[REDACTED_PNR_OR_PHONE]' }
];
```

---

## Alert Rules Engine Configuration

```yaml
groups:
  - name: railyatra_alert_rules
    rules:
      - alert: HighHTTP5xxErrorRate
        expr: (sum(rate(railyatra_backend_http_requests_total{status=~"5.."}[2m])) / sum(rate(railyatra_backend_http_requests_total[2m]))) * 100 > 3
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP 5xx error rate detected ({{ $value }}%)"
          description: "Backend HTTP 5xx error rate exceeds 3% over a 2-minute window."

      - alert: AIServiceHighLatency
        expr: histogram_quantile(0.95, sum(rate(railyatra_ai_stream_first_token_seconds_bucket[5m])) by (le)) > 2.5
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "AI Service streaming initial token latency high ({{ $value }}s)"
          description: "p95 time to first token has exceeded 2.5 seconds for 3 minutes."

      - alert: RedisCacheDegraded
        expr: (sum(rate(railyatra_redis_hits_total[5m])) / (sum(rate(railyatra_redis_hits_total[5m])) + sum(rate(railyatra_redis_misses_total[5m])))) * 100 < 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis cache hit ratio dropped below 50%"
          description: "Cache efficiency drop detected. Database load may increase."
```

---

## Environment Variable Master Matrix

| Service | Environment Variable | Purpose | Target Production Value |
|---------|----------------------|---------|-------------------------|
| **Frontend** | `NEXT_PUBLIC_SENTRY_DSN` | Sentry client reporting URL | Sentry Client DSN |
| **Frontend** | `NEXT_PUBLIC_POSTHOG_KEY` | PostHog product analytics key | PostHog API Key |
| **Backend** | `SENTRY_DSN` | Sentry NestJS backend DSN | Sentry Server DSN |
| **Backend** | `ENABLE_PROMETHEUS_METRICS` | Enables `/metrics` scraper endpoint | `true` |
| **AI Service** | `SENTRY_DSN` | Sentry FastAPI AI DSN | Sentry Python DSN |
| **AI Service** | `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | `https://otlp.grafana.net` |
| **CI/CD** | `SENTRY_AUTH_TOKEN` | Source map upload credential | GitHub Repository Secret |

---

## CI/CD Pipeline Integration (`.github/workflows/deploy.yml`)

The production deployment workflow incorporates release tracking and health verification:

```yaml
  sentry-release:
    name: Create Sentry Release & Upload Source Maps
    needs: validate-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create Sentry Release
        uses: getsentry/action-release@v1
        env:
          SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
          SENTRY_ORG: 'railyatra'
          SENTRY_PROJECT: 'railyatra-platform'
        with:
          environment: 'production'
          version: ${{ github.sha }}

      - name: Notify Deployment Success
        run: |
          echo "Release ${{ github.sha }} registered with Sentry and deployed successfully."
```

---

## Implementation Roadmap & Milestone Phasing

### Phase 11 — Foundation: Error Tracking & Uptime Probes
- **Target Repository Files**:
  - `apps/frontend/src/lib/monitoring/sentry.*.config.ts`
  - `apps/backend/src/monitoring/sentry.service.ts`
  - `apps/ai-service/app/monitoring/sentry_config.py`
- **Deliverables**: Verified exception reporting across all 3 microservices; Better Stack uptime probes configured.
- **Rollback Strategy**: Unset `SENTRY_DSN` env vars; services fall back cleanly without error.

### Phase 12 — Tracing & Log Streaming
- **Target Repository Files**:
  - `apps/backend/src/monitoring/trace.middleware.ts`
  - `apps/ai-service/app/monitoring/otel_tracer.py`
  - Render Log Drain HTTP Integration
- **Deliverables**: W3C `traceparent` propagation across Next.js $\rightarrow$ NestJS $\rightarrow$ FastAPI; central log streaming to Better Stack.

### Phase 13 — Metrics & Grafana Dashboards
- **Target Repository Files**:
  - `apps/backend/src/monitoring/prometheus.controller.ts`
  - `apps/ai-service/app/monitoring/metrics_collector.py`
- **Deliverables**: `/metrics` scrapable by Prometheus; 4 Grafana dashboards provisioned.

### Phase 14 — Real User Monitoring & Product Analytics
- **Target Repository Files**:
  - `apps/frontend/src/lib/monitoring/web-vitals.ts`
  - `apps/frontend/src/lib/monitoring/posthog.ts`
- **Deliverables**: Core Web Vitals telemetry captured; PostHog analytics conversion funnels operational.

---

## Final Production Readiness Sign-Off Matrix

- [x] **Discovery Strategy Document Completed**: `docs/monitoring/Monitoring_Discovery_Strategy.md`
- [x] **Enterprise Architecture Document Completed**: `docs/monitoring/Enterprise_Monitoring_Architecture.md`
- [x] **Technical Blueprint Document Completed**: `docs/monitoring/Technical_Monitoring_Architecture.md`
- [x] **Repository Analysis & Verification**: All target directories, existing log interceptors, and metrics collectors audited.
- [x] **Zero Code Changes Enforced**: Discovery and planning phase executed with zero code modifications to existing applications.
