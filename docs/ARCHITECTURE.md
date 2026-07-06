# RailYatra Technical Architecture Specification

This document details the monorepo-based backend, frontend, and AI platform configuration of **RailYatra**.

---

## 🏗️ Services Layout

```
/Rail-Yatra
├── apps/
│   ├── frontend/             # Next.js 15 Frontend
│   ├── backend/              # NestJS Core Server API
│   └── ai-service/           # FastAPI Agent Service
├── packages/
│   ├── design-system/        # Tailwind styling & tokens (v4 configurations)
│   └── api-contracts/        # TS types & interfaces
├── docs/                     # Technical specifications & backlog
└── docker-compose.yml        # PostgreSQL, Redis, Qdrant runner
```

---

## 🎨 Tech Stack & Abstraction Boundaries

### 1. Frontend
- **Framework:** Next.js 15, React 19, TypeScript.
- **Styling:** Tailwind CSS v4, global HSL variables, glassmorphism filters, and CSS transitions.
- **State Management:** Zustand for lightweight client configuration states.
- **Charts:** Recharts for rendering confirmation probabilities, cancellation trends, and delays.
- **Responsiveness:** Designed Mobile-First, supporting bottom navigation and responsive grids.

### 2. Backend Core
- **Framework:** NestJS (Node.js framework for server-side architecture).
- **ORM:** Prisma Client connected to PostgreSQL.
- **Validation:** Global `ValidationPipe` with `class-validator` DTO annotations.
- **Config:** Encapsulated in NestJS `ConfigModule`.
- **CORS:** Pre-configured to support cross-origin API calls.

### 3. AI Service
- **Framework:** FastAPI, Python 3.14+.
- **Orchestrator:** LangGraph state graph.
- **Database:** Qdrant for semantic vector embedding search and RAG contexts.
- **Deployment:** Executed in a virtual environment (`venv`) with uvicorn.

---

## 🧩 Modularity Abstraction Rules

To prevent coupling external service providers directly to business logic, the backend and AI services use the Strategy Pattern:
- **`AIProvider`**: Interface wrapping communication with LLM providers.
- **`PaymentProvider`**: Interface mapping gateways.
- **`PredictionProvider`**: Interface mapping waitlist forecasting algorithms.
- **`NotificationProvider`**: Interface wrapper for SMS, Email, and Push integrations.
