# RailYatra AI Platform — Monitoring Discovery & Strategy

## Executive Summary

The **RailYatra AI Platform** has successfully completed its core engineering roadmap (Phases 1–10) and production deployment. The system features a modern microservice architecture consisting of a Next.js 14 frontend deployed on Vercel, a NestJS core backend API deployed on Render, a Python FastAPI AI microservice deployed on Render, a serverless Neon PostgreSQL relational database, and an Upstash serverless Redis cache.

As the platform transitions from initial deployment to enterprise scale, establishing a comprehensive **Discovery & Monitoring Strategy** is essential. This document serves as the architectural foundation for observability across the entire platform. It defines *what* must be monitored, *why* it must be monitored, *who* consumes the observability data, *which* tools deliver optimal capability, and *how* the platform guarantees reliability, security, performance, and cost-efficiency as traffic grows from MVP to millions of travelers.

---

## Current Production Architecture Audit

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND TIER                                    │
│  Next.js 14 (App Router) on Vercel Edge Platform                                │
│  • Static Prerendering, Server Actions, Client Components                        │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ HTTPS / SSE
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                BACKEND CORE API                                 │
│  NestJS 10 Framework on Render Container Instance                               │
│  • Global Exception Filter, Logging Interceptor, JWT Guard, Validation Pipe     │
└──────────────┬─────────────────────────┬─────────────────────────┬──────────────┘
               │                         │                         │
               │ PostgreSQL              │ TLS Redis               │ HTTP / SSE
               ▼                         ▼                         ▼
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│  NEON POSTGRESQL DB    │  │  UPSTASH REDIS CACHE   │  │  FASTAPI AI SERVICE    │
│  Serverless Pooled     │  │  Serverless In-Memory  │  │  Python 3.11 on Render  │
│  (Prisma ORM L2)       │  │  Session & Rate Limit  │  │  LangChain / Orchestrator│
└────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

### Component Inventory & Hosting Topology

1. **Frontend (`apps/frontend`)**: Next.js 14 App Router hosted on **Vercel**. Provides traveler dashboard, interactive PNR lookup, real-time train status visualizer, subscription portal, and AI chat interface.
2. **Backend (`apps/backend`)**: NestJS core API hosted on **Render**. Serves authentication, monetization, booking orchestration, admin management, and health endpoints.
3. **AI Service (`apps/ai-service`)**: FastAPI microservice hosted on **Render**. Runs LangGraph multi-agent orchestrator, journey intelligence engine, vector search fallback, and streaming chat endpoints (`/chat/stream`).
4. **Relational Database**: **Neon Serverless PostgreSQL**. Handles persistent data (Users, Conversations, Subscriptions, Audit Logs).
5. **Caching & Session Storage**: **Upstash Serverless Redis**. Provides distributed session storage, token bucket rate limiting, and railway delay cache.
6. **CI/CD Pipeline**: **GitHub Actions**. Automated linting (ESLint, Ruff), unit testing (Jest, Pytest), and multi-package build validation.

---

## Current Observability Capabilities & Baseline Analysis

The repository currently includes baseline operational features:

- **NestJS Logging Interceptor** (`apps/backend/src/common/logging.interceptor.ts`): Emits structured JSON logs containing timestamp, correlation ID (`x-correlation-id`), HTTP method, path, status code, and execution duration (`durationMs`). Includes slow query warnings for requests exceeding 800ms.
- **NestJS Global Exception Filter** (`apps/backend/src/common/http-exception.filter.ts`): Catches unhandled errors and outputs structured JSON logs with error names, stack traces, and request details while returning sanitized response payloads.
- **FastAPI Structured Logger** (`apps/ai-service/app/production/logging_config.py`): Formats log entries as JSON with categories (`STARTUP`, `SECURITY`, `REQUEST`, `ERROR`, `AUDIT`, `BACKGROUND`) and automatic sensitivity scrubbing for passwords, keys, and tokens.
- **FastAPI Prometheus Metrics Collector** (`apps/ai-service/app/production/metrics.py`): In-memory collector storing counters (`http_requests_total`, `ai_predictions_total`), gauges (`active_connections`, `memory_usage_mb`), and histogram latency buckets exported in Prometheus exposition format (`/metrics`).
- **FastAPI OpenTelemetry Trace Manager** (`apps/ai-service/app/production/tracing.py`): In-memory span collector maintaining root and child spans with trace IDs and duration tracking.
- **Multi-Tier Health Checks**:
  - NestJS `/api/health`, `/api/health/live`, `/api/health/ready`: Validates DB ping, Redis TCP connectivity, and AI service health.
  - FastAPI `/health`, `/health/live`, `/health/ready`: Validates memory manager, vector fallback, and background syncer loops.

---

## Gap Analysis

While the baseline capability is well-structured, several production observability gaps remain:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 OBSERVABILITY GAPS                              │
├───────────────────────┬─────────────────────────┬───────────────────────────────┤
│ Domain                │ Current State           │ Production Requirement        │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ Distributed Tracing   │ Local In-Memory Spans   │ OpenTelemetry Collector/Tempo │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ Error Aggregation     │ Console / Container Logs│ Sentry Error Tracking         │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ Synthetic Uptime      │ Local Polling in CI     │ Better Stack / UptimeRobot    │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ Real User Mon. (RUM)  │ None                    │ Web Vitals & Client Errors    │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ Central Log Storage   │ stdout (Render/Vercel)  │ Vector / Better Stack Logs    │
├───────────────────────┼─────────────────────────┼───────────────────────────────┤
│ AI Observability      │ Simple Latency Counters │ Token Cost & Fallback Audits  │
└───────────────────────┴─────────────────────────┴───────────────────────────────┘
```

1. **No External Error Aggregation**: Exceptions logged to stdout on Render/Vercel are ephemeral and lack grouping, stack trace de-minification, user impact tracking, or release regression tagging.
2. **Disconnected Tracing Pipeline**: Request correlation IDs generated in NestJS are not automatically propagated downstream to FastAPI HTTP requests or upstream from Next.js server components.
3. **No Synthetic End-to-End Probe**: Outages occurring between Vercel and Render outside of active user sessions are not detected proactively.
4. **Lack of Frontend Web Vitals Instrumentation**: No metrics are collected for Largest Contentful Paint (LCP), Interaction to Next Paint (INP), or Cumulative Layout Shift (CLS) experienced by end-users.
5. **Unmonitored AI Token Economics**: Token consumption, provider fallback occurrences (e.g. Gemini → OpenAI → Mock), and prompt/response costs are recorded in logs but not aggregated into financial or operational dashboards.

---

## Business Requirements

1. **Service Availability SLA**: Maintain 99.9% uptime for core travel search and booking services, corresponding to no more than 43.8 minutes of unscheduled downtime per month.
2. **User Experience Safeguard**: Guarantee that 95% of AI streaming responses return the initial token within 1.2 seconds, and journey intelligence searches complete within 800ms.
3. **Financial Protection**: Implement real-time monitoring of AI API costs to prevent runaway consumption or denial-of-wallet incidents.
4. **Incident Response MTTR**: Reduce Mean Time To Detect (MTTD) to under 2 minutes and Mean Time To Resolve (MTTR) to under 15 minutes for Critical (P0) production outages.
5. **Data Privacy & Compliance**: Ensure 100% masking of PII (Passenger Name Records, phone numbers, payment tokens, emails) prior to sending log or trace data to external vendors.

---

## Functional & Non-Functional Requirements

### Functional Requirements

- **FR-1**: Capture every unhandled exception in Next.js, NestJS, and FastAPI with full stack trace, context headers, release commit SHA, and active environment tag.
- **FR-2**: Trace a single end-user interaction across Next.js UI → NestJS API → FastAPI AI Service → Upstash Redis → Neon PostgreSQL using a unified `traceparent` / `x-correlation-id` header.
- **FR-3**: Expose standardized `/metrics` endpoints across all backend services for Prometheus scraping.
- **FR-4**: Track product usage analytics including journey searches, subscription conversions, AI chat sessions, and feature tier access.
- **FR-5**: Route high-priority alerts to Discord/Slack webhooks and email notifications with automated escalation policies for unacknowledged incidents.

### Non-Functional Requirements

- **NFR-1 (Performance Overhead)**: Monitoring instrumentation must consume less than 2% CPU overhead and add no more than 5ms latency to API request processing.
- **NFR-2 (Reliability)**: The monitoring system must be decoupled from core application logic. Outages in external monitoring vendors (e.g. Sentry or Better Stack) must never degrade core travel search or booking functionality.
- **NFR-3 (Data Retention)**: Store high-resolution operational metrics for 30 days, aggregated metrics for 365 days, and security audit logs for 730 days.
- **NFR-4 (Scalability)**: Telemetry data pipelines must seamlessly process up to 10,000 telemetry events per second without dropping records or overloading application threads.

---

## Monitoring Domains

```
                               ┌───────────────────────────┐
                               │  ENTERPRISE MONITORING    │
                               │        DOMAINS            │
                               └─────────────┬─────────────┘
                                             │
       ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Frontend    │   │  Backend &   │   │  AI Model &  │   │ Database &   │   │ Security &   │
│  & RUM       │   │  Microservice│   │  Orchestration│  │ Cache Tier   │   │ Compliance   │
├──────────────┤   ├──────────────┤   ├──────────────┤   ├──────────────┤   ├──────────────┤
│• Web Vitals  │   │• Request Rate│   │• Token Usage │   │• Pool Latency│   │• Auth Failures│
│• Client Errors│  │• Latency p95 │   │• TTFT Stream │   │• Slow Queries│   │• Rate Limits │
│• Route Timing│   │• Error Rate  │   │• Fallbacks   │   │• Hit Ratios  │   │• Secret Redac│
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

### 1. Application Monitoring (APM)
Tracks execution flow, internal function timing, unhandled exceptions, and middleware performance across NestJS and FastAPI services.

### 2. Infrastructure & Container Monitoring
Monitors Render container CPU usage, RAM allocation, thread contention, garbage collection pauses, and container restarts.

### 3. AI Service & Model Monitoring
Monitors LangGraph agent state transitions, Time-To-First-Token (TTFT) for Server-Sent Events (SSE), LLM provider fallback frequency, context window token limits, and prompt cost tracking.

### 4. Database Monitoring (Neon PostgreSQL)
Monitors active connection pool saturation, query latency percentiles (p50, p95, p99), Prisma transaction durations, table lock contention, and storage auto-scaling.

### 5. Cache Monitoring (Upstash Redis)
Monitors command execution latency, cache hit/miss ratios, key memory eviction rates, connection counts, and rate-limiting bucket consumption.

### 6. Frontend & User Experience Monitoring
Monitors Core Web Vitals (LCP, FID, CLS, INP), JavaScript runtime errors, visual layout shifts, client-side route transitions, and API response wait times.

### 7. Deployment & CI/CD Monitoring
Monitors GitHub Actions build durations, test suite execution times, Vercel preview deployment statuses, and Render release health checks.

### 8. Security & Audit Monitoring
Monitors failed authentication attempts, JWT verification errors, rate-limit triggers, privilege escalation checks, and administrative action logs.

### 9. Business & Monetization Analytics
Monitors journey searches per minute, PNR status lookup counts, subscription tier conversions (Free → Pro → Enterprise), active AI chat sessions, and booking completion rates.

---

## Key Performance Indicators (KPIs) & Metrics Matrix

| Category | Indicator / Metric | Target Baseline | Critical Threshold | SLA/SLO Impact |
|----------|-------------------|-----------------|--------------------|----------------|
| **Availability** | Platform Uptime | 99.9% | < 99.5% | Core SLA Gate |
| **Backend Latency** | API p95 Response Time | < 250ms | > 800ms | User Satisfaction |
| **Backend Errors** | HTTP 5xx Error Rate | < 0.05% | > 1.0% | Reliability Gate |
| **AI Performance** | Time To First Token (TTFT) | < 800ms | > 2500ms | UX Streaming Gate |
| **AI Reliability** | Model Provider Fallback Rate | < 2.0% | > 10.0% | Cost & Quality |
| **Database** | PostgreSQL Query p95 | < 45ms | > 200ms | Database Health |
| **Database** | Connection Pool Usage | < 60% | > 85% | Outage Predictor |
| **Cache** | Redis Cache Hit Ratio | > 85% | < 65% | Latency & DB Load |
| **Frontend** | Largest Contentful Paint (LCP) | < 1.8s | > 3.5s | Core Web Vitals |
| **Business** | Journey Search Success Rate | > 99.0% | < 95.0% | Conversion Impact |

---

## Vendor Evaluation & Architecture Decision Matrix

| Vendor / Tool | Primary Strengths | Limitations / Drawbacks | Operational Cost | Rec. Role in RailYatra |
|---------------|-------------------|-------------------------|------------------|------------------------|
| **Sentry** | Exceptional error aggregation, stack de-minification, release tracking, lightweight SDKs | Can become costly at high event volumes | Free Tier $\rightarrow$ \$26/mo growth | **Primary APM & Error Tracking** |
| **Better Stack** | Unified uptime monitoring, status pages, log management, instant alert routing | Less specialized for deep distributed tracing | Free Tier $\rightarrow$ \$24/mo growth | **Uptime, Logging & Status Page** |
| **PostHog** | Open-source user analytics, session replay, feature flags, conversion funnels | Requires careful PII scrubbing configuration | Free Tier (1M events) | **Product & User Analytics** |
| **Prometheus** | Industry standard metrics format, highly efficient pull/push model | Requires storage backend for long-term retention | Self-Hosted / Free | **Native Metrics Exposition** |
| **Grafana** | Rich visualization dashboards, multi-datasource querying | Requires configuration management | Self-Hosted / Free Cloud | **Unified SRE Dashboard** |
| **OpenTelemetry** | Vendor-neutral standard, rich context propagation | Requires collector pipeline setup for complex filters | Open Source / Free | **Tracing Instrumentation Standard** |

### Recommended Stack Architecture
- **Error Tracking & Performance APM**: **Sentry** (Frontend Next.js, Backend NestJS, FastAPI AI Service).
- **Synthetic Uptime & Incident Routing**: **Better Stack Uptime & Incident Management**.
- **Centralized Log Ingestion**: **Better Stack Logs** (ingesting JSON logs from Render and Vercel).
- **Metrics Exposition & Visualization**: **Prometheus Exposition Format** exposed natively by services and visualized via **Grafana Cloud Free**.
- **Product & Business Analytics**: **PostHog Cloud** (Client-side user interactions and feature usage).

---

## Alerting & Escalation Strategy

```
                               ┌───────────────────────────┐
                               │     TELEMETRY EVENT       │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   EVALUATION ENGINE       │
                               │ (Thresholds & Cooldowns)  │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │ P0 / Critical               │ P1 / Warning                │ P2 / Info
               ▼                             ▼                             ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│     CRITICAL CHANNEL      │ │      WARNING CHANNEL      │ │       INFO CHANNEL        │
│  • PagerDuty / Phone Call │ │  • Slack / Discord Alert  │ │  • Daily Email Digest     │
│  • On-Call Auto Escalated │ │  • Ack Required in 30m    │ │  • Non-blocking Audit Log │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

### Alert Severity Matrix

1. **P0 - Critical (Immediate Action Required)**:
   - *Triggers*: Overall service availability < 98%, DB connection pool exhausted, HTTP 5xx error rate > 5% over 3 minutes, AI Service unresponsive for > 2 minutes.
   - *Channels*: Better Stack Incident Call/SMS, PagerDuty, Discord `#alerts-critical`. Escalates to Lead Architect after 5 minutes if unacknowledged.
2. **P1 - Warning (Action Required within 1 hour)**:
   - *Triggers*: Memory usage > 85%, Redis cache hit ratio < 60%, AI provider fallback active for > 15 minutes, API response latency p95 > 1000ms.
   - *Channels*: Discord `#alerts-warning`, Email digest to On-Call SRE.
3. **P2 - Informational (Non-blocking)**:
   - *Triggers*: Successful deployment completion, ssl certificate renewal notice, background syncer interval summary.
   - *Channels*: Discord `#deployments-log`.

---

## Security, Compliance & Data Privacy Strategy

1. **Automated Log Scrubbing**: All logging formatters (NestJS `LoggingInterceptor` and FastAPI `StructuredFormatter`) strictly sanitize keys matching `password`, `token`, `secret`, `jwt`, `api_key`, `credit_card`, and `pnr_owner_phone`.
2. **PII Masking at Source**: Passenger identity data (Names, Emails, Phone Numbers) is masked using SHA-256 HMAC tokens before transmitting traces or analytics to external vendors (Sentry/PostHog).
3. **GDPR & Privacy Compliance**: Telemetry storage complies with data minimisation principles. No raw payload bodies containing personal travel itineraries are stored in telemetry retention layers.
4. **Role-Based Access Control (RBAC)**: Telemetry dashboards in Grafana, Sentry, and Better Stack are restricted using single sign-on (SSO) with strict role segregation (Admin, Developer, Auditor).

---

## Cost Analysis & Financial Projection

| Stage / User Scale | Est. Monthly Active Users | Estimated Telemetry Volume | Projected Vendors & Cost | Total Est. Monthly Cost |
|--------------------|---------------------------|----------------------------|--------------------------|-------------------------|
| **MVP / Bootstrap** | 100 - 1,000 | < 100k events/mo | Sentry (Free), Better Stack (Free), PostHog (Free), Grafana Cloud (Free) | **\$0.00 / mo** |
| **Early Growth** | 10,000 | 1.5M events/mo | Sentry Team (\$26), Better Stack Starter (\$24), PostHog (Free tier) | **\$50.00 / mo** |
| **Scale Phase** | 100,000 | 15M events/mo | Sentry Business (\$80), Better Stack Growth (\$85), PostHog (\$50) | **\$215.00 / mo** |
| **Enterprise** | 1,000,000+ | 150M events/mo | Sentry Enterprise, Better Stack Enterprise, Dedicated OpenTelemetry Collector | **\$650 - \$1,200 / mo** |

---

## Implementation Roadmap & Milestones

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           IMPLEMENTATION ROADMAP                                │
├──────────────┬──────────────────────────────────────────┬───────────────────────┤
│ Milestone    │ Scope & Deliverables                     │ Target Timeline       │
├──────────────┼──────────────────────────────────────────┼───────────────────────┤
│ Milestone 1  │ Error Monitoring & Synthetic Probes      │ Phase 11 (Days 1–5)   │
│              │ • Integrate Sentry across Next/Nest/Fast │                       │
│              │ • Configure Better Stack Uptime Checks   │                       │
├──────────────┼──────────────────────────────────────────┼───────────────────────┤
│ Milestone 2  │ Centralized Logging & Correlation        │ Phase 12 (Days 6–10)  │
│              │ • Propagate W3C Trace Context            │                       │
│              │ • Stream JSON logs to Better Stack Logs  │                       │
├──────────────┼──────────────────────────────────────────┼───────────────────────┤
│ Milestone 3  │ Metrics & Grafana Visualizations         │ Phase 13 (Days 11–15) │
│              │ • Prometheus metric scrape targets       │                       │
│              │ • Build Executive & SRE Dashboards       │                       │
├──────────────┼──────────────────────────────────────────┼───────────────────────┤
│ Milestone 4  │ Product Analytics & Web Vitals           │ Phase 14 (Days 16–20) │
│              │ • PostHog integration & Web Vitals       │                       │
│              │ • Conversion funnels & feature flags     │                       │
└──────────────┴──────────────────────────────────────────┴───────────────────────┘
```

---

## Success Criteria & Readiness Gate

The Discovery & Monitoring Strategy will be considered fully validated when:

1. **Coverage**: 100% of production HTTP endpoints, background queues, and AI flows have active error capturing and latency tracking.
2. **Alert Accuracy**: Zero false-positive P0 alerts during standard operations; 100% of synthetic downtime events trigger alerts in under 60 seconds.
3. **Trace Continuity**: End-to-end trace correlation verified across Next.js UI, NestJS API, FastAPI AI service, and database calls.
4. **Performance Impact**: Application performance benchmarks show less than 1.5% overhead with monitoring enabled.
