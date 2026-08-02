# RailYatra Changelog

All notable changes to the **RailYatra** platform will be documented in this file.

---

## [1.0.0-phase1] - 2026-07-06

### Added
- Monorepo folder setup under pnpm workspaces.
- Scaffolding of Next.js 15 app under `apps/frontend`.
- Scaffolding of NestJS backend under `apps/backend` (with configuration options, Prisma config, and global validation pipes).
- Scaffolding of FastAPI service under `apps/ai-service`.
- Custom HSL styling palette mapped in `globals.css` with Tailwind CSS v4 support.
- Complete Prisma Database schema including `User`, `UserSetting`, `Trip`, `PnrHistory`, etc.
- Docker Compose configuration for local Postgres, Redis, and Qdrant database nodes.
- Structured project documentation under `docs/`.

---

## [1.0.0] - 2026-08-02

### Added
- **Phase 7 — Predictive Intelligence Platform**: Congestion, delay, waitlist, seat availability, and risk forecasting engines with explainability and governance.
- **Phase 8 — Real-Time Operations Platform**: Event-driven railway intelligence engine with train tracking, ETA updates, incident dispatcher, and state transition guards.
- **Phase 9 — Enterprise Integrations Platform**: Resilient integration gateway with circuit breakers, retry policies, provider registries, and webhooks for weather, maps, payment, and railway APIs.
- **Phase 10 — Production Platform & Launch Readiness**: Hardened production diagnostics, health/readiness/liveness probes, maintenance recovery, security secrets management, and automated backup/restore scripts.
- **Milestone 6.6 — AI Response Composer & Explainability Platform**: Pipeline-based response generation with prompt registries, formatters, and confidence scoring evaluators.

---

## [1.1.0-phase6-m6.5] - 2026-07-22

### Added
- Complete AI Memory Platform implementation for Milestone 6.5.
- Core DDD aggregates: `TravelerMemory`, `ConsentProfile`, and `JourneySagaMemory` with strict invariant checks.
- Value objects, entities, events, specifications, and policies for the memory platform.
- Clean Architecture repository ports and thread-safe In-Memory database adapters.
- CQRS commands and queries separating mutations from consent-filtered read queries.
- Lifecycle state transitions state machine implementing opt-in / opt-out purges and inactivity expirations.
- Structured logging, telemetry metrics registry, and central environment variables config.
- Domain and Application automated pytest verification suites passing 100% green.

