# RailYatra Production Deployment Guide

This guide covers the complete deployment workflow for RailYatra across Vercel (frontend) and Railway (backend, AI service, databases).

---

## 1. Infrastructure Overview

| Service        | Platform       | Runtime         |
|----------------|----------------|-----------------|
| Frontend       | Vercel          | Next.js 15      |
| Backend API    | Railway         | NestJS (Node)   |
| AI Service     | Railway         | FastAPI (Python) |
| PostgreSQL     | Railway         | Managed         |
| Redis          | Railway         | Managed         |
| Vector DB      | Qdrant Cloud    | Managed         |

---

## 2. Multi-Environment Strategy

### Environments

| Environment   | Branch   | Promotion Gate                    |
|---------------|----------|-----------------------------------|
| Development   | `dev`    | Automatic on push                 |
| Staging       | `staging`| Automatic on push + smoke tests   |
| Production    | `main`   | Manual approval after smoke tests |

### Deployment Flow

```
Development → Staging → Smoke Tests → Manual Approval → Production
```

---

## 3. Platform Configuration

### 3.1 Vercel (Frontend)

1. Connect the GitHub repository to Vercel.
2. Set the **Root Directory** to `apps/frontend`.
3. Set the **Framework Preset** to `Next.js`.
4. Configure build settings:
   - **Build Command:** `pnpm build`
   - **Output Directory:** `.next`
5. Add environment variables:

| Variable                       | Value                                         |
|--------------------------------|-----------------------------------------------|
| `NEXT_PUBLIC_API_URL`          | `https://<backend>.railway.app/api`           |
| `NEXT_PUBLIC_AI_SERVICE_URL`   | `https://<ai-service>.railway.app`            |
| `NEXT_PUBLIC_APP_ENV`          | `production`                                  |

### 3.2 Railway (Backend)

1. Create a new Railway project.
2. Add a service from the GitHub repository.
3. Set the **Root Directory** to `apps/backend`.
4. Railway auto-detects the `railway.toml` configuration.
5. Add environment variables:

| Variable             | Value                                              |
|----------------------|----------------------------------------------------|
| `DATABASE_URL`       | Railway PostgreSQL connection string (auto-injected)|
| `REDIS_URL`          | Railway Redis connection string (auto-injected)     |
| `JWT_SECRET`         | Strong random secret (≥64 characters)              |
| `CORS_ORIGIN`        | `https://<your-vercel-domain>.vercel.app`          |
| `NODE_ENV`           | `production`                                       |
| `PORT`               | `5000`                                             |
| `AI_SERVICE_URL`     | `https://<ai-service>.railway.app`                 |

### 3.3 Railway (AI Service)

1. Add another service in the same Railway project.
2. Set the **Root Directory** to `apps/ai-service`.
3. Railway auto-detects the `Dockerfile` and `railway.toml`.
4. Add environment variables:

| Variable             | Value                                              |
|----------------------|----------------------------------------------------|
| `REDIS_URL`          | Railway Redis connection string                     |
| `QDRANT_URL`         | Qdrant Cloud cluster URL                            |
| `QDRANT_API_KEY`     | Qdrant Cloud API key                                |
| `GOOGLE_API_KEY`     | Google AI API key                                   |
| `ENV`                | `production`                                       |
| `PORT`               | `8000`                                             |

### 3.4 Railway (PostgreSQL & Redis)

1. Add **PostgreSQL** plugin to the Railway project.
2. Add **Redis** plugin to the Railway project.
3. Railway auto-injects `DATABASE_URL` and `REDIS_URL` into linked services.

### 3.5 Qdrant Cloud

1. Create a cluster at [cloud.qdrant.io](https://cloud.qdrant.io).
2. Copy the cluster URL and API key into the AI Service environment variables.

---

## 4. GitHub Secrets

Configure the following secrets in **GitHub → Settings → Secrets → Actions**:

| Secret                   | Platform  | Purpose                              |
|--------------------------|-----------|--------------------------------------|
| `RAILWAY_TOKEN`          | Railway   | CI/CD deployment trigger             |
| `VERCEL_TOKEN`           | Vercel    | CI/CD deployment trigger             |
| `VERCEL_ORG_ID`         | Vercel    | Organization identifier              |
| `VERCEL_PROJECT_ID`     | Vercel    | Project identifier                   |
| `PRODUCTION_BACKEND_URL`| CI/CD     | Smoke test target URL                |
| `PRODUCTION_AI_URL`     | CI/CD     | Smoke test target URL                |

---

## 5. CI/CD Pipeline

The deployment pipeline is defined in `.github/workflows/deploy.yml`.

### Pipeline Stages

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
                      └── Smoke Tests
                           └── Production Readiness ✓
```

### Running Database Migrations

After a Railway deployment that includes schema changes:

```bash
# Railway CLI
railway run npx prisma migrate deploy
```

---

## 6. Health Check Endpoints

| Service    | Endpoint                | Expected Response     |
|------------|-------------------------|-----------------------|
| Backend    | `GET /api/health/live`  | `200 OK`              |
| Backend    | `GET /api/health/ready` | `200 OK` (DB + Redis) |
| AI Service | `GET /health`           | `200 OK`              |

---

## 7. Smoke Testing

### Local (PowerShell)

```powershell
.\scripts\smoke-test.ps1 -BackendUrl "https://<backend>.railway.app" -AIServiceUrl "https://<ai-service>.railway.app"
```

### CI/CD Pipeline (Bash)

```bash
./scripts/smoke-test-prod.sh
```

---

## 8. Rollback Procedure

### Railway

1. Open the Railway dashboard.
2. Navigate to the affected service.
3. Click on the previous successful deployment.
4. Select **Rollback to this deployment**.

### Vercel

1. Open the Vercel dashboard.
2. Navigate to **Deployments**.
3. Find the last stable deployment.
4. Click **Promote to Production**.

### Database

If a migration must be reverted:

```bash
railway run npx prisma migrate resolve --rolled-back <migration_name>
```

---

## 9. Legacy Files (Removed)

The following files were part of the legacy VPS/PM2 deployment strategy and have been removed:

| File                    | Reason                                    |
|-------------------------|-------------------------------------------|
| `ecosystem.config.js`   | PM2 process manager — replaced by Railway |
| `docker-compose.prod.yml` | Self-hosted Docker stack — replaced by Railway managed services |
| `scripts/deploy.ps1`    | PM2-based deployment script — replaced by CI/CD pipeline        |
