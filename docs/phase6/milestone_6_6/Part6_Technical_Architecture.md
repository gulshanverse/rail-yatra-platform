# RAILYATRA AI PLATFORM
## Phase 6 – Milestone 6.6: AI Response Composer & Explainability Platform
### ENTERPRISE ARCHITECTURE — PART 6: TECHNICAL ARCHITECTURE & DEPLOYMENT

```
================================================================================
Document Type:      Enterprise Technical Architecture & Infrastructure Blueprint
Milestone:          6.6 – AI Response Composer & Explainability Platform
Version:            1.0
Status:             APPROVED ENTERPRISE TECHNICAL BASELINE
Domain:             Technical Topology, Security, Deployment, Performance & Observability
Target Audience:    Chief Software Architect, Principal Cloud Architect, DevSecOps Leads
================================================================================
```

---

## 1. TECHNICAL ARCHITECTURE PRINCIPLES

The Technical Architecture translates business, domain, and solution blueprints into a high-availability, cloud-native technical topology:

```
+-----------------------------------------------------------------------------------+
|                     ENTERPRISE TECHNICAL ARCHITECTURE PRINCIPLES                  |
+-----------------------------------------------------------------------------------+
| 1. Cloud-Native & Containerized | Packaged in OCI containers, orchestrated via K8s.|
| 2. Event-Driven Communication  | Asynchronous decoupling via Redis Pub/Sub / NATS. |
| 3. Zero Trust Security         | Mandatory mTLS, JWT validation, and RBAC / ABAC.  |
| 4. Stateless Microservices     | Services hold no session state; backed by Redis.  |
| 5. High Availability & HA      | Multi-AZ deployment with auto-healing topologies. |
| 6. Observability-First Design  | OpenTelemetry traces, Prometheus metrics, logs.  |
+-----------------------------------------------------------------------------------+
```

---

## 2. DEPLOYMENT TOPOLOGY & INFRASTRUCTURE

### 2.1 Multi-Environment Deployment Topology
RailYatra operates across 4 isolated environment tiers:

```
+-----------------------------------------------------------------------------------+
|                        MULTI-ENVIRONMENT TOPOLOGY                                 |
+-----------------------------------------------------------------------------------+
| PRODUCTION (Prod)      | Multi-AZ Kubernetes Cluster (Primary & Secondary Regions)|
| STAGING (Stage)        | Single-AZ Mirror Cluster with anonymized data feeds      |
| DEVELOPMENT (Dev)      | Local Docker Compose & K3s developer instances           |
| TESTING (CI/CD)        | Automated GitHub Actions runner nodes & pytest pipelines  |
+-----------------------------------------------------------------------------------+
```

### 2.2 Deployment Strategy
- **Blue-Green & Canary Rollouts**: Deployments to the AI Response Composer module utilize zero-downtime Canary strategies (10% traffic routing initially, scaling to 100% after health metric validation).
- **Automated Rollback Trigger**: Sudden latency spikes (> 300ms) or error rates (> 1%) trigger instant automated rollback to the previous stable release hash.

---

## 3. SERVICE TOPOLOGY & MONOREPO STRUCTURE

The service topology maps directly to the RailYatra monorepo ecosystem:

```
rail-yatra-platform/
├── apps/
│   ├── frontend/          # Next.js 15 Web & Mobile App (Node 20, Tailwind v4)
│   ├── backend/           # NestJS REST API Gateway & User Management
│   └── ai-service/        # FastAPI Python 3.14 AI Core Platform
│       └── app/
│           ├── composer/      # Milestone 6.6 AI Response Composer Module
│           ├── memory/        # Milestone 6.5 AI Memory Platform
│           ├── planner/       # Journey Intelligence Engine
│           ├── prediction/    # Waitlist & Delay Forecast Models
│           └── knowledge/     # RAG Knowledge Base & IRCTC Policies
```

---

## 4. API ARCHITECTURE & INTER-SERVICE CONTRACTS

```
+-----------------------------------------------------------------------------------+
|                           ENTERPRISE API STRATEGY                                 |
+-----------------------------------------------------------------------------------+
| API Type              | Protocol / Technology    | Usage Scenario                 |
+-----------------------+--------------------------+--------------------------------+
| Client-Facing REST    | HTTPS / REST (JSON)      | Synchronous travel queries     |
| Real-Time Streaming   | SSE (Server-Sent Events) | Token-by-token response streaming|
| Internal Subsystems   | gRPC / HTTP2 Protobuf    | High-speed microservice links |
| Async Event Bus       | Redis Pub/Sub / NATS     | Audit events, telemetry spans  |
+-----------------------------------------------------------------------------------+
```

### 4.1 Resiliency & Rate Limiting Controls
- **Rate Limiting**: Token-Bucket algorithm (100 req/min for authenticated travelers, 20 req/min for anonymous users).
- **Timeouts**: Hard timeout budget of **150ms** for the AI Response Composer pipeline; fallback to pre-rendered response templates on budget breach.

---

## 5. SECURITY & PRIVACY ARCHITECTURE

```
+-----------------------------------------------------------------------------------+
|                      ENTERPRISE SECURITY & PRIVACY MODEL                          |
+-----------------------------------------------------------------------------------+
| Security Layer     | Mechanism Implemented                                        |
+--------------------+--------------------------------------------------------------+
| Authentication     | OAuth 2.0 + OpenID Connect (JWT validation at API Gateway)   |
| Authorization      | Fine-grained Role-Based & Attribute-Based Access Control     |
| Data Encryption    | AES-256 at rest (Postgres/Redis), TLS 1.3 in transit          |
| DPDP Privacy Gate  | Mandatory `ConsentGrantedSpecification` check before synthesis|
| PII Scrubbing      | Real-time regex scanner masking names, phones, and PNRs       |
+-----------------------------------------------------------------------------------+
```

---

## 6. DATA ARCHITECTURE & PERSISTENCE STACK

```
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE DATA ARCHITECTURE MATRIX                        |
+-----------------------------------------------------------------------------------+
| Storage Component   | Technology Selected | Data Owned & Retention Policy         |
+---------------------+---------------------+---------------------------------------+
| Operational DB      | PostgreSQL 16       | User accounts, booking sagas (5 years)|
| Session Cache       | Redis 7.2           | Active conversation state (24 hours)  |
| Vector Store        | Qdrant Vector DB    | RAG policy embeddings (Permanent)     |
| Cryptographic Audit | Append-Only Logs    | Hash-verified composition logs (7 yrs)|
+-----------------------------------------------------------------------------------+
```

---

## 7. SCALABILITY & PERFORMANCE ARCHITECTURE

### 7.1 Scalability Blueprint
- **Horizontal Pod Autoscaling (HPA)**: Scales FastAPI `ai-service` worker instances dynamically between 5 and 50 pods based on CPU (> 70%) and concurrent request queue depth.
- **Connection Pooling**: PgBouncer for PostgreSQL database pools and Redis Connection Pools to optimize socket reuse under heavy load (100,000+ users).

### 7.2 Performance Latency Budget
```
+-----------------------------------------------------------------------------------+
|                   COMPOSITION LATENCY BUDGET BREAKDOWN (< 150ms)                  |
+-----------------------------------------------------------------------------------+
| 1. Upstream Intelligence Fetching (Parallel) : 45ms                               |
| 2. Conflict Arbitration & Trade-off Logic     : 25ms                               |
| 3. Explainability Depth Calculation           : 30ms                               |
| 4. DPDP Privacy Check & PII Masking           : 20ms                               |
| 5. Layout Rendering & Action Chip Generation   : 30ms                               |
| TOTAL PROCESSING BUDGET                       : 150ms                             |
+-----------------------------------------------------------------------------------+
```

---

## 8. OBSERVABILITY, METRICS & TELEMETRY

```
+-----------------------------------------------------------------------------------+
|                         ENTERPRISE OBSERVABILITY STACK                            |
+-----------------------------------------------------------------------------------+
| Telemetry Type  | Technology Standard    | Target SLO / SLA Metric                |
+-----------------+------------------------+----------------------------------------+
| Metrics         | Prometheus + Grafana   | 99.99% Composition Availability        |
| Distributed Trace| OpenTelemetry + Jaeger | 95th Percentile Latency < 150ms         |
| Structured Logs | JSON Logs + ELK Stack  | 100% Correlation ID propagation        |
| Health Checks   | `/health/liveness`     | K8s readiness & liveness probes        |
+-----------------------------------------------------------------------------------+
```

---

## 9. ARCHITECTURE DECISION RECORDS (ADRS)

### ADR-01: FastAPI for AI Response Composition
- **Status**: Approved.
- **Context**: Need high-performance, asynchronous Python execution for AI model integration and data parsing.
- **Decision**: Adopt FastAPI (Python 3.14) inside `apps/ai-service`.
- **Consequence**: Delivers sub-millisecond route handling and native Pydantic type safety.

### ADR-02: Qdrant for RAG Policy Vector Search
- **Status**: Approved.
- **Context**: Need fast, reliable vector search for IRCTC rules and refund policy citations.
- **Decision**: Adopt Qdrant vector database.
- **Consequence**: Provides sub-10ms similarity search for grounded explainability.

---

## 10. TECHNICAL READINESS SIGN-OFF

```
================================================================================
RAILYATRA ENTERPRISE TECHNICAL ARCHITECTURE COUNCIL

Deployment Topology:       ✅ FULLY DESIGNED
Security & DPDP Model:     ✅ FULLY DESIGNED
Performance & Latency:     ✅ APPROVED (< 150ms Budget)
Technology Stack & ADRs:   ✅ APPROVED

FINAL TECHNICAL STATUS: 🟢 ENTERPRISE TECHNICAL ARCHITECTURE BASELINE COMPLETE (Part 6)
================================================================================
```
