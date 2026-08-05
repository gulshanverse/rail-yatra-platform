# RailYatra AI Platform — Enterprise Monitoring Architecture

## Executive Architectural Summary

This document defines the high-level **Enterprise Monitoring Architecture** for the **RailYatra AI Platform**. It translates the Discovery Strategy (Document 1) into an operational blueprint that spans the entire platform stack: Next.js frontend (Vercel), NestJS core API (Render), FastAPI AI service (Render), Neon Serverless PostgreSQL, Upstash Redis, and GitHub Actions CI/CD pipelines.

The architecture adopts an **OpenTelemetry-first, multi-tier observability paradigm** designed for high availability, zero application friction, robust data privacy, and seamless scaling from early deployment up to 1,000,000+ active travelers.

---

## Observability Pillars & Layered Architecture

The RailYatra observability framework is structured across five primary execution layers:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DASHBOARD & PRESENTATION LAYER                        │
│   Grafana Cloud  │  Sentry Portal  │  Better Stack Console  │  PostHog Analytics   │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────┴────────────────────────────────────────┐
│                          INGESTION & AGGREGATION PIPELINE                       │
│   OpenTelemetry Collector Pipeline  │  Vector Log Shipper  │  Prometheus Scraper    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────┴────────────────────────────────────────┐
│                        TELEMETRY DOMAIN ENGINES (PILLARS)                       │
├─────────────────┬──────────────────┬──────────────────┬─────────────────────────┤
│  Metrics Engine │   Logs Engine    │  Tracing Engine  │  Events & Analytics     │
│  (Prometheus)   │   (Structured)   │  (OTel / W3C)    │  (PostHog / Audit)      │
└─────────────────┴──────────────────┴──────────────────┴─────────────────────────┘
                                         │
┌────────────────────────────────────────┴────────────────────────────────────────┐
│                           APPLICATION INSTRUMENTATION                           │
│   Next.js (Vercel)  │  NestJS (Render API)  │  FastAPI (Render AI Service)          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Instrumentation Layer**: Code-level hooks, middleware, interceptors, and HTTP guards across Next.js, NestJS, and FastAPI.
2. **Telemetry Pillars**:
   - **Metrics**: Standardized counter, gauge, and histogram exposition.
   - **Logs**: High-performance, structured JSON logging with dynamic severity and log scrubbing.
   - **Traces**: Distributed W3C trace-context propagation across HTTP boundaries.
   - **Events**: Product analytics and security audit events.
3. **Ingestion & Aggregation Pipeline**: Asynchronous, non-blocking telemetry batchers transmitting data via secure HTTPS/gRPC protocol to telemetry collectors.
4. **Presentation & Dashboard Layer**: Role-specific visualization dashboards in Grafana, Sentry, Better Stack, and PostHog.
5. **Incident & Alerting Layer**: Automated notification routing, deduplication, escalation, and status page synchronization.

---

## Unified Data Flow & Trace Propagation

To trace a request end-to-end, RailYatra enforces the **W3C Trace Context Specification** (`traceparent` header: `version-traceid-parentid-traceflags`).

```
[ Traveler Browser / Client ]
             │
             │ 1. HTTP GET /api/journey/search
             │    Header: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ▼
[ Next.js Edge (Vercel) ]
             │
             │ 2. Proxy request to NestJS Backend Core API
             │    Header: x-correlation-id: 4bf92f3577b34da6a3ce929d0e0e4736
             ▼
[ NestJS Backend (Render) ] ── (SQL Tracing) ──▶ [ Neon PostgreSQL DB ]
             │                                 ──▶ [ Upstash Redis Cache ]
             │ 3. Inter-Service HTTP Call to FastAPI AI Service
             │    Header: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-a287766e8783459c-01
             ▼
[ FastAPI AI Service (Render) ]
             │
             │ 4. LangGraph Multi-Agent Execution & LLM Inference
             ▼
[ Model Provider (Gemini / OpenAI) ]
```

### Telemetry Pipeline Data Flows
- **Metrics Flow**: Service `/metrics` endpoints $\rightarrow$ Prometheus Scraper / Grafana Agent $\rightarrow$ Grafana Cloud.
- **Log Flow**: Application `stdout` $\rightarrow$ Render/Vercel Log Drain $\rightarrow$ Better Stack Logs Ingest $\rightarrow$ Alert Manager & Log Search.
- **Error Flow**: Unhandled Exceptions $\rightarrow$ Sentry SDK (Batching Worker) $\rightarrow$ Sentry Cloud $\rightarrow$ Issue De-duplication & Slack Alert.
- **Trace Flow**: OpenTelemetry Spans $\rightarrow$ Trace Exporter $\rightarrow$ Tempo / Sentry Performance $\rightarrow$ Distributed Trace Waterfall.

---

## Domain Architecture Specifications

### 1. Application & API Monitoring (NestJS Core Backend)
- **Instrumentation**: NestJS `LoggingInterceptor` and `GlobalExceptionFilter` coupled with `@sentry/nestjs`.
- **Metrics Tracked**: HTTP request volume per path/method, p50/p95/p99 response latency, HTTP 4xx/5xx error rates, active JWT sessions, and NestJS event loop lag.
- **Key Interceptors**: Trace context extraction, response timing, correlation ID injection.

### 2. AI Model & Orchestrator Monitoring (FastAPI AI Service)
- **Instrumentation**: FastAPI `logging_config`, `metrics.py`, `tracing.py`, and `@sentry/python`.
- **Metrics Tracked**: Time-To-First-Token (TTFT) for streaming responses, total token count per session (prompt vs completion), LLM provider selection (Gemini vs OpenAI vs Anthropic vs Mock), provider fallback triggers, and LangGraph node execution duration.

### 3. Database & Connection Pool Monitoring (Neon PostgreSQL)
- **Instrumentation**: Prisma ORM middleware and Neon serverless telemetry integration.
- **Metrics Tracked**: Query latency per model/operation, active connection pool utilization, Prisma connection acquisition wait time, slow query logging threshold (> 200ms), and database transaction failure rates.

### 4. Cache & Memory Monitoring (Upstash Redis)
- **Instrumentation**: Redis client interceptor and TCP ping health probe.
- **Metrics Tracked**: Command execution duration, hit ratio percentage ($\frac{\text{Hits}}{\text{Hits} + \text{Misses}} \times 100$), eviction rate, memory usage bytes, and rate-limiter bucket consumption.

### 5. Frontend & Real User Monitoring (Next.js Vercel)
- **Instrumentation**: `@sentry/nextjs` and Next.js `useReportWebVitals` hook.
- **Metrics Tracked**: Core Web Vitals (LCP, FID, CLS, INP), JavaScript bundle execution errors, page load durations, route transition times, and client-side HTTP request errors.

---

## Technology Component & Architecture Matrix

| Component | Selected Technology | Architecture Role | High Availability / Scaling Model |
|-----------|--------------------|-------------------|------------------------------------|
| **Error Aggregator** | **Sentry Cloud** | Central error tracking, stack trace symbolication, release health tracking | Global multi-region SaaS ingestion with offline SDK queuing |
| **Uptime & Logs** | **Better Stack** | Synthetic health checks, centralized log storage, status page host | Multi-location synthetic probes (US, EU, ASIA) with redundant status hosting |
| **Metrics Collector** | **Prometheus + Grafana Cloud** | Time-series metrics storage and visualization | Managed Grafana Cloud TSDB with 13-month data retention |
| **Product Analytics** | **PostHog Cloud** | User funnels, subscription conversion tracking, feature flags | Serverless event ingestion pipeline with anonymized user IDs |
| **Tracing Protocol** | **OpenTelemetry (W3C)** | Standardized distributed trace propagation | Native zero-dependency trace headers (`traceparent`) |

---

## Security, Privacy & Compliance Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATA PRIVACY & REDACTION PIPELINE                        │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. LOCAL REDACTION FILTER (Application Side)                                    │
│    • Scrub sensitive keys: password, secret, token, api_key, jwt, credit_card   │
│    • Regex mask: Indian PNR (10 digits), Phone (+91), Aadhaar, Email            │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. ANONYMIZATION & HASHING LAYER                                                │
│    • User ID -> SHA-256 HMAC Pseudonym                                          │
│    • IP Address -> Truncated IPv4 (/24) or IPv6 (/64)                           │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. ENCRYPTED TRANSPORT & REST                                                   │
│    • TLS 1.3 in Transit to Sentry / Better Stack / Grafana                      │
│    • AES-256 at Rest on Storage Providers                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Zero Raw PII Storage**: Application logging pipelines strictly sanitize PII before handing off log messages to stdout or external collectors.
2. **Cryptographic User Pseudonymization**: Real database user IDs and traveler names are replaced with deterministic SHA-256 HMAC strings in external telemetry tools.
3. **Strict RBAC & Least Privilege**: Telemetry vendor access is partitioned:
   - *Engineers/SREs*: Read-only operational metrics, stack traces, and de-identified performance logs.
   - *Security Auditors*: Access to security audit category logs only.
   - *Product Managers*: Aggregate conversion and usage metrics in PostHog.
4. **Data Retention & Lifecycle Policies**:
   - Short-term operational logs: 30 days.
   - Performance metrics & histograms: 90 days.
   - Security audit logs: 730 days (Compliance store).

---

## High Availability & Incident Management Architecture

### Resiliency & Failover Strategy

- **Non-Blocking Telemetry Calls**: All monitoring SDKs execute in asynchronous background threads or non-blocking event loops. An outage in Sentry or Better Stack will never cause NestJS or FastAPI requests to fail or hang.
- **Circuit Breaker for Log Drains**: If external log collectors become unreachable, log formatters gracefully degrade to local standard out without throwing exceptions.
- **Multi-Region Synthetic Health Probes**: Better Stack probes verify platform availability from three independent global regions (Oregon, Frankfurt, Singapore).

### Incident Management Lifecycle

```
[ DETECT ] ──▶ [ CLASSIFY ] ──▶ [ NOTIFY ] ──▶ [ INVESTIGATE ] ──▶ [ RESOLVE ] ──▶ [ POSTMORTEM ]
    │                │               │                │               │                │
Synthetic      P0 Critical     Discord/Slack     Distributed     Deployment      Blameless
Probe / Alert  vs P1 Warning   Webhook + Call    Tracing / Logs  Rollback / Patch Review Document
```

1. **Severity Classification**:
   - **P0 (Critical)**: Platform downtime > 2%, database pool exhaustion, AI streaming unresponsiveness. Immediate call/SMS dispatch via Better Stack.
   - **P1 (Warning)**: Elevated error rates (> 1%), latency spikes (p95 > 1s), cache degradation. Discord `#alerts-warning` notification.
   - **P2 (Info)**: Successful deployments, routine backup execution. Discord `#deployments-log`.
2. **Automated Incident Runbooks**: Standardized operational runbooks linked directly inside alert payloads for immediate SRE action.

---

## Dashboard Architecture

The enterprise dashboard suite is organized into specialized domain views in Grafana and Sentry:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GRAFANA DASHBOARD SUITE                            │
├───────────────────┬───────────────────┬───────────────────┬─────────────────────┤
│ 1. Executive Board│ 2. SRE Ops View   │ 3. AI Performance │ 4. Database & Cache │
├───────────────────┼───────────────────┼───────────────────┼─────────────────────┤
│ • System Health   │ • HTTP Rate & 5xx │ • TTFT Latency    │ • DB Pool Saturation│
│ • Daily Travelers │ • Response p95/99 │ • Token Consumption│ • Slow Query Count │
│ • Revenue / Sub   │ • Container RAM   │ • Fallback Ratio  │ • Redis Hit Ratio   │
└───────────────────┴───────────────────┴───────────────────┴─────────────────────┘
```

1. **Executive Overview Dashboard**: High-level platform health indicator, active daily users, journey search volume, and overall SLA compliance percentage.
2. **SRE Operations Dashboard**: Real-time throughput (RPS), error rates (4xx/5xx), latency distribution (p50, p95, p99), host memory/CPU gauges, and active container counts.
3. **AI Service & Model Dashboard**: Time-To-First-Token (TTFT) trends, model invocation breakdown (Gemini vs OpenAI vs Anthropic vs Mock), token generation speed, and cost accumulation graph.
4. **Database & Cache Infrastructure Dashboard**: Neon PostgreSQL connection pool depth, query latency heatmaps, Upstash Redis memory usage, hit/miss percentage graphs, and rate-limiting queue status.

---

## Risk Analysis & Mitigation Matrix

| Identified Risk | Severity | Potential Impact | Mitigation Strategy |
|-----------------|----------|------------------|---------------------|
| **Telemetry Telemetry Storm** | Medium | High volume during outage inflates vendor bill | Implement client-side rate-limiting & error sampling in Sentry SDK |
| **Vendor Outage (Sentry/BetterStack)** | Low | Temporary loss of observability dashboards | Services continue executing with local stdout logging; zero app disruption |
| **Unscrubbed PII Leak** | High | Privacy compliance violation | Double-layer sanitization (Interceptor + Formatter) with automated CI regex tests |
| **Trace Context Disconnect** | Low | Incomplete trace waterfalls across microservices | Standardize on W3C `traceparent` headers enforced by NestJS global HTTP client |

---

## Implementation Milestones & Technical Phasing

- **Phase 11 — Error Monitoring & Synthetic Probes**: Sentry SDK integration across Next.js, NestJS, and FastAPI; Better Stack uptime probe setup.
- **Phase 12 — Logging Centralization & Correlation**: Direct log streaming to Better Stack Logs; W3C trace context header propagation.
- **Phase 13 — Metrics Pipeline & Dashboard Suite**: Expose Prometheus endpoints across services; configure Grafana Cloud dashboard panels.
- **Phase 14 — Product Analytics & Real User Monitoring**: PostHog SDK deployment for user flows; Next.js Core Web Vitals collector.
