# RailYatra Operations Runbook

This runbook contains the complete checklist and procedures for managing the production RailYatra platform on Railway and Vercel.

---

## 1. Production Topology & URLs

### 1.1 Service Directory

| Service / Resource | Platform | URL / Connection |
|--------------------|----------|------------------|
| **Frontend** | Vercel | `https://railyatra-frontend.vercel.app` |
| **Backend Core API**| Railway | `https://railyatra-backend.up.railway.app` |
| **AI Service (FastAPI)** | Railway | `https://railyatra-ai-service.up.railway.app` |
| **PostgreSQL Database** | Railway | Managed (Auto-generated internal host) |
| **Redis Cache** | Railway | Managed (Auto-generated internal host) |
| **Qdrant Vector DB** | Qdrant Cloud | `https://your-qdrant-cluster.qdrant.io` |

### 1.2 Health Check Endpoints

| Service | Endpoint | Verified Output |
|---------|----------|-----------------|
| **Backend Liveness** | `/api/health/live` | `{"status": "ok"}` |
| **Backend Readiness** | `/api/health/ready` | `{"status": "ready", "checks": {"database": "up", "redis": "up"}}` |
| **AI Service Liveness** | `/health` | `{"status": "healthy", "redis": "connected", "qdrant": "connected"}` |

---

## 2. Infrastructure Setup & Environment Variables

### 2.1 Railway Services

#### `railyatra-backend` (NestJS)
- **Deployment Source:** GitHub Repo Root (`apps/backend`)
- **Port:** `5000`
- **Procfile command:** `web: pnpm run start:prod`
- **Required Variables:**
  - `DATABASE_URL` (Auto-injected by Railway Postgres plugin link)
  - `REDIS_URL` (Auto-injected by Railway Redis plugin link)
  - `JWT_SECRET` (Secure JWT Token encryption key)
  - `JWT_REFRESH_SECRET` (Secure Refresh Token encryption key)
  - `AI_SERVICE_URL` (`https://railyatra-ai-service.up.railway.app`)
  - `CORS_ORIGIN` (`https://railyatra-frontend.vercel.app`)
  - `NODE_ENV` (`production`)
  - `PORT` (`5000`)

#### `railyatra-ai-service` (FastAPI)
- **Deployment Source:** GitHub Repo Root (`apps/ai-service`)
- **Port:** `8000`
- **Procfile command:** `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Required Variables:**
  - `REDIS_URL` (Link to Railway Redis instance)
  - `QDRANT_URL` (Qdrant Cloud URL, e.g. `https://xxx.qdrant.io:6333`)
  - `QDRANT_API_KEY` (Qdrant Read/Write Token)
  - `GOOGLE_API_KEY` (Gemini API Key)
  - `ENV` (`production`)
  - `PORT` (`8000`)

### 2.2 Vercel Frontend

#### `railyatra-frontend` (Next.js)
- **Root Directory:** `apps/frontend`
- **Build Command:** `pnpm build`
- **Output Directory:** `.next`
- **Required Variables:**
  - `NEXT_PUBLIC_API_URL` (`https://railyatra-backend.up.railway.app/api`)
  - `NEXT_PUBLIC_AI_SERVICE_URL` (`https://railyatra-ai-service.up.railway.app`)
  - `NEXT_PUBLIC_APP_ENV` (`production`)

---

## 3. Monitoring & Observability

### 3.1 Log Aggregation
- **Railway Console Logs:** Navigate to Railway Dashboard → Project → Service Name → **Deployments** → **Logs**. Filter by warnings or errors.
- **Vercel Console Logs:** Navigate to Vercel Dashboard → Project → **Logs**.

### 3.2 Key Performance Indicators (KPIs)
- **Liveness Alerts:** If `/api/health/live` returns non-200, restart the service.
- **Readiness Checks:** If `/api/health/ready` returns degraded status for Redis or Database:
  - Check database/redis plugin connection status on Railway.
  - Verify if connections have exceeded pool limits.

---

## 4. Rollback & Failover Procedures

### 4.1 Railway Services Rollback
1. Open the **Railway Dashboard** and click on the affected service (`railyatra-backend` or `railyatra-ai-service`).
2. Go to the **Deployments** tab.
3. Find the previous stable build deployment.
4. Click on the three dots `...` on the right side of the deployment and select **Rollback**.
5. Railway will automatically redirect traffic to the rolled-back deployment.

### 4.2 Vercel Frontend Rollback
1. Navigate to the Vercel Dashboard → **Deployments** tab.
2. Search for the last known stable deployment.
3. Click the three dots `...` on that deployment and select **Promote to Production**.
4. The DNS routing changes are applied instantly.

### 4.3 Prisma Schema Rollback
If a database migration goes wrong:
1. Revert code changes to the previous Prisma schema version.
2. Mark the failed migration as rolled-back:
   ```bash
   railway run npx prisma migrate resolve --rolled-back <migration_name>
   ```

---

## 5. Incident Response & Troubleshooting Playbooks

### 5.1 Playbook A: Pre-Flight Check Failure (Backend Refuses to Boot)
- **Symptom:** Backend container exits instantly with code 1 during startup.
- **Diagnostics:** Check deployment logs for `"CRITICAL: Pre-flight database connection check failed"` or `"CRITICAL: Pre-flight Redis connection check failed"`.
- **Mitigation:**
  1. Verify credentials and configuration strings in Railway variables.
  2. Confirm PostgreSQL service status has not been suspended due to credit/billing limits.
  3. Ping Redis locally to verify if it is accepting TCP connections.

### 5.2 Playbook B: AI Agent Degraded (503 circuit breaker)
- **Symptom:** User questions receive `"Service Unavailable"` or `"Circuit Breaker is open"`.
- **Diagnostics:** FastAPI server logs show exceptions connecting to Redis or Qdrant Cloud.
- **Mitigation:**
  1. Check AI service logs for connection errors.
  2. Test Qdrant connectivity:
     ```bash
     curl -I -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/readyz"
     ```
  3. Restart `railyatra-ai-service` via Railway console.

---

## 6. Pre-flight Deployment Verification Checklist

Execute this checklist before signaling Closed Beta launch approval:

- [ ] **Step 1:** Confirm `DATABASE_URL` uses PostgreSQL provider scheme (`postgresql://`).
- [ ] **Step 2:** Ensure Prisma Client has been generated inside the build container (`npx prisma generate`).
- [ ] **Step 3:** Validate that backend CORS matches Vercel production domain.
- [ ] **Step 4:** Deploy and run migrations on production: `railway run npx prisma migrate deploy`.
- [ ] **Step 5:** Execute the automated smoke test script locally:
  ```powershell
  .\scripts\smoke-test.ps1 -BaseUrl "https://railyatra-backend.up.railway.app" -AiUrl "https://railyatra-ai-service.up.railway.app"
  ```
- [ ] **Step 6:** Access the Vercel URL, inspect browser console for any mixed-content warnings or failed API fetches.
