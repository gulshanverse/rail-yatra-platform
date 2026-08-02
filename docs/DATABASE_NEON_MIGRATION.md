# Neon PostgreSQL Database Migration & Architecture Guide

**Platform**: RailYatra AI Platform  
**Target Migration**: Railway PostgreSQL -> Neon Serverless PostgreSQL  
**Status**: Step 2 Complete — Validated & Ready for Production Provisioning  
**ORM Engine**: Prisma 6.2.0 (`@prisma/client`)  
**Database Provider**: `postgresql`

---

## 1. Executive Overview

This guide details the complete database infrastructure migration from Railway PostgreSQL (expired) to Neon Serverless PostgreSQL. 

The database schema encompasses 22 relational models supporting core user profiles, authentication, trips, saved routes, PNR tracking, AI conversation sessions, monetization, system metrics, and feature flags.

---

## 2. Schema Integrity & Neon Compatibility Verification

### Schema Structure
- **Prisma Schema File**: `apps/backend/prisma/schema.prisma`
- **Migration SQL**: `apps/backend/prisma/migrations/20260712104037_init/migration.sql` (391 lines of DDL)
- **Lockfile**: `apps/backend/prisma/migrations/migration_lock.toml` (`provider = "postgresql"`)

### Compatibility Matrix

| Schema Element | Inspection Result | Neon Compatibility | Notes |
| :--- | :--- | :--- | :--- |
| **Provider** | `postgresql` | 100% Compatible | Standard PostgreSQL engine |
| **Data Types** | `TEXT`, `TIMESTAMP(3)`, `DECIMAL(65,30)`, `DOUBLE PRECISION`, `INTEGER`, `BOOLEAN` | 100% Compatible | Fully supported standard ANSI SQL types |
| **Primary Keys** | `@id @default(uuid())` (String UUID) | 100% Compatible | Application-layer UUID string generation |
| **Foreign Keys** | 8 foreign keys with `ON DELETE CASCADE ON UPDATE CASCADE` | 100% Compatible | Fully enforced by Neon Postgres engine |
| **Indexes** | 11 Unique Indexes (`User_email_key`, `User_phone_key`, `PnrHistory_pnr_key`, etc.) | 100% Compatible | B-Tree index structures |
| **JSON Columns** | Stored as string representations (`aiPreferences`, `travelPrefs`, `filters`, `context`) | 100% Compatible | Ensures zero DB engine type lock-in |
| **Enum Values** | Stored as String defaults (`role @default("USER")`, etc.) | 100% Compatible | App-layer enum validation |

---

## 3. Neon Provisioning & Infrastructure Architecture

### Project Configuration
- **Project Name**: `railyatra-production`
- **Database Name**: `railyatra_prod`
- **PostgreSQL Version**: `15` or `16`
- **Region**: `aws-us-east-1` (aligned with Render backend hosting region)
- **Branching Strategy**: 
  - `main` branch (production database)
  - `staging` branch (preview / integration database)
- **Backups**: Neon automated daily Point-In-Time Recovery (PITR) up to 30 days.

---

## 4. Dual Connection String Strategy

Neon utilizes an integrated PgBouncer connection pooler to prevent connection exhaustion from containerized/serverless Node.js apps.

### 1. Runtime Connection String (`DATABASE_URL`)
Used by NestJS runtime application (`PrismaService` / `@prisma/client`) connecting through Neon's PgBouncer pooler.

```env
DATABASE_URL="postgres://user:password@ep-pooler-name.eastus2.azure.neon.tech/railyatra_prod?sslmode=require"
```

### 2. Migration Connection String (`DIRECT_URL`)
Used by Prisma CLI for DDL migrations (`prisma migrate deploy`) which require direct access without PgBouncer session pooling.

```env
DIRECT_URL="postgres://user:password@ep-direct-name.eastus2.azure.neon.tech/railyatra_prod?sslmode=require"
```

---

## 5. Prisma Migration Execution Plan

When deploying to a new Neon database instance, run the following sequence:

```bash
# 1. Validate Prisma schema syntax
pnpm --filter backend exec prisma validate

# 2. Generate latest Prisma Client types
pnpm --filter backend exec prisma generate

# 3. Apply SQL migrations to Neon target database
pnpm --filter backend exec prisma migrate deploy

# 4. Verify table structure against deployed schema
pnpm --filter backend exec prisma db pull --print
```

---

## 6. Pre-flight Health & Startup Validation

The NestJS backend performs automated PostgreSQL pre-flight checks during service bootstrap (`apps/backend/src/main.ts` lines 114–126):

```typescript
// 3. Pre-flight PostgreSQL validation
const prisma = app.get(PrismaService);
try {
  logger.log('Validating PostgreSQL connectivity...');
  await prisma.$queryRaw`SELECT 1`;
  logger.log('PostgreSQL connectivity verified successfully.');
} catch (err: unknown) {
  logger.error(`[FATAL CONNECTION ERROR] PostgreSQL check failed: ${err}`);
  process.exit(1);
}
```

The readiness probe (`GET /api/health/ready`) in `apps/backend/src/health/health.controller.ts` line 92 tests DB connectivity via `SELECT 1`.

---

## 7. Historical Platform Deprecation Notice

> [!NOTE]
> **Railway PostgreSQL Deprecation**: All Railway PostgreSQL plugins and auto-injected `DATABASE_URL` references have been marked **[DEPRECATED]**. Railway deployment files (`railway.toml`) are retained strictly as historical context and must not be used for current deployments.
