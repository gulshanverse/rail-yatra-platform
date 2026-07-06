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
