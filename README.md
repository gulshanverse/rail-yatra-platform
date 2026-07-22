# RailYatra Platform

AI-powered Railway Travel Intelligence Platform that helps travelers make smarter travel decisions through AI-driven predictions, recommendations, journey optimization, and personalized travel assistance.

## Architecture

```
rail-yatra-platform/
├── apps/
│   ├── frontend/          # Next.js 15 web application
│   ├── backend/           # NestJS REST API
│   └── ai-service/        # FastAPI AI service
│       └── app/
│           ├── agents/        # AI agent implementations
│           ├── execution/     # Booking execution engine
│           ├── knowledge/     # RAG knowledge retrieval
│           ├── memory/        # AI Memory Platform (Milestone 6.5)
│           │   ├── domain/        # DDD aggregates, entities, value objects
│           │   ├── application/   # CQRS commands, queries, handlers
│           │   ├── state_machine.py
│           │   ├── config.py
│           │   └── telemetry.py
│           ├── orchestrator/  # Agent workflow orchestration
│           └── planner/       # Journey planning engine
├── docs/                  # Project documentation
│   ├── phase6/
│   │   └── milestone_6_5/  # AI Memory Platform architecture docs
│   └── CHANGELOG.md
└── docker-compose.yml     # Local infrastructure (Postgres, Redis, Qdrant)
```

## Tech Stack

- **Frontend**: Next.js 15, React, Tailwind CSS v4
- **Backend**: NestJS, Prisma ORM, PostgreSQL
- **AI Service**: FastAPI, Python 3.14, LangChain
- **Infrastructure**: Docker Compose, Redis, Qdrant (vector DB)
- **Package Manager**: pnpm workspaces (monorepo)

## AI Memory Platform (Phase 6 — Milestone 6.5)

The Memory Platform provides persistent traveler context across AI agent sessions:

- **Domain-Driven Design**: Aggregate roots (`TravelerMemory`, `ConsentProfile`, `JourneySagaMemory`) enforce business invariants
- **CQRS**: Separated command (write) and query (read) pipelines with consent-filtered projections
- **Privacy-by-Design**: DPDP opt-in consent gates, right-to-be-forgotten purges, PII masking
- **Lifecycle State Machine**: `NEW` → `VALIDATED` → `CLASSIFIED` → `ACTIVE` → `EXPIRED` → `PURGED`

## Development

```bash
# Install dependencies
pnpm install

# Start all services
pnpm dev

# Run AI service tests
cd apps/ai-service
venv/Scripts/python -m pytest

# Lint AI service
pnpm --filter ai-service lint

# Format AI service
pnpm --filter ai-service format
```

## License

Private — All rights reserved.
