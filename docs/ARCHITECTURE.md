# RailYatra Technical Architecture Specification

This document details the monorepo-based architecture, service boundaries, and production infrastructure of **RailYatra**.

---

## 🏗️ Monorepo Structure

```
/Rail-Yatra
├── apps/
│   ├── frontend/             # Next.js 15 Frontend (Vercel)
│   ├── backend/              # NestJS Core Server API (Railway)
│   └── ai-service/           # FastAPI Agent Service (Railway)
├── packages/
│   ├── design-system/        # Tailwind styling & tokens (v4 configurations)
│   └── api-contracts/        # TS types & interfaces
├── scripts/                  # Deployment & smoke test automation
├── docs/                     # Technical specifications & runbooks
└── docker-compose.yml        # Local development: PostgreSQL, Redis, Qdrant
```

---

## 🌐 Production Infrastructure

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Vercel     │     │   Railway        │     │   Railway        │
│   Frontend   │────▶│   Backend API    │────▶│   AI Service     │
│   Next.js 15 │     │   NestJS         │     │   FastAPI        │
└──────────────┘     └───────┬──────────┘     └───────┬──────────┘
                             │                         │
                    ┌────────┴────────┐       ┌────────┴────────┐
                    │  Railway        │       │  Qdrant Cloud   │
                    │  PostgreSQL     │       │  Vector DB      │
                    │  + Redis        │       │                 │
                    └─────────────────┘       └─────────────────┘
```

| Service        | Platform     | Runtime         | Health Endpoint         |
|----------------|-------------|-----------------|-------------------------|
| Frontend       | Vercel       | Next.js 15      | —                       |
| Backend API    | Railway      | NestJS (Node)   | `/api/health/ready`     |
| AI Service     | Railway      | FastAPI (Python) | `/health`               |
| PostgreSQL     | Railway      | Managed          | Auto-monitored          |
| Redis          | Railway      | Managed          | Auto-monitored          |
| Vector DB      | Qdrant Cloud | Managed          | Qdrant dashboard        |

---

## 🎨 Tech Stack & Abstraction Boundaries

### 1. Frontend
- **Framework:** Next.js 15, React 19, TypeScript.
- **Styling:** Tailwind CSS v4, global HSL variables, glassmorphism filters, and CSS transitions.
- **State Management:** Zustand for lightweight client configuration states.
- **Charts:** Recharts for rendering confirmation probabilities, cancellation trends, and delays.
- **Responsiveness:** Designed Mobile-First, supporting bottom navigation and responsive grids.
- **API Layer:** Centralized `API_BASE_URL` via `lib/api.ts` — all backend calls route through a single configurable endpoint.
- **Deployment:** Vercel with automatic preview deployments on pull requests.

### 2. Backend Core
- **Framework:** NestJS (Node.js framework for server-side architecture).
- **ORM:** Prisma Client connected to PostgreSQL (Railway managed).
- **Validation:** Global `ValidationPipe` with `class-validator` DTO annotations.
- **Config:** Encapsulated in NestJS `ConfigModule` with environment-specific `.env` loading.
- **CORS:** Pre-configured to support cross-origin API calls from the Vercel frontend.
- **Health Checks:** Liveness (`/api/health/live`) and readiness (`/api/health/ready`) probes with DB and Redis connectivity verification.
- **Startup Guards:** Pre-flight connection checks for PostgreSQL and Redis; process exits with code 1 on failure to prevent unhealthy instances from receiving traffic.
- **Deployment:** Railway with `railway.toml` and `Procfile` configuration.

### 3. AI Service
- **Framework:** FastAPI, Python 3.14+.
- **Orchestrator:** LangGraph state graph.
- **Vector Database:** Qdrant Cloud for semantic vector embedding search and RAG contexts.
- **Cache:** Redis for session and response caching.
- **Health Checks:** `/health` endpoint with dependency status reporting.
- **Lifecycle:** Graceful startup/shutdown handlers for Redis and Qdrant connections.
- **Deployment:** Railway via Dockerfile with non-root user execution.

---

## 🧩 Modularity Abstraction Rules

To prevent coupling external service providers directly to business logic, the backend and AI services use the Strategy Pattern:
- **`AIProvider`**: Interface wrapping communication with LLM providers.
- **`PaymentProvider`**: Interface mapping gateways.
- **`PredictionProvider`**: Interface mapping waitlist forecasting algorithms.
- **`NotificationProvider`**: Interface wrapper for SMS, Email, and Push integrations.

---

## 🚀 CI/CD Pipeline

```
Push to main
  └── CI Gate
       ├── Lint & Type Check
       ├── Backend Tests (Jest)
       ├── AI Service Tests (Pytest)
       └── Build Validation (pnpm build)
            └── Deploy Gate
                 ├── Vercel Frontend Deploy
                 ├── Railway Backend Deploy
                 └── Railway AI Service Deploy
                      └── Post-Deploy Smoke Tests
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full deployment instructions.

---

## 📊 Operational Monitoring

| Metric                   | Target (Closed Beta) | Target (GA)  |
|--------------------------|----------------------|-------------|
| API Success Rate         | ≥ 95%                | ≥ 99.5%     |
| AI Response Latency (p95)| ≤ 5s                 | ≤ 3s        |
| Frontend TTFB (p50)      | ≤ 1.5s               | ≤ 800ms     |
| Deployment Success Rate  | ≥ 90%                | ≥ 99%       |
| Health Check Pass Rate   | ≥ 95%                | ≥ 99.9%     |
