# RailYatra Deployment Guide

This document describes how to launch, scale, and maintain the **RailYatra** infrastructure.

---

## 💻 Local Development Setup

To run Postgres, Redis, and Qdrant containers locally, execute:
```bash
docker compose up -d
```

### Running Services Locally

1. **Frontend App:**
   ```bash
   pnpm --filter frontend dev
   ```
2. **Backend API:**
   ```bash
   pnpm --filter backend start:dev
   ```
3. **AI Service:**
   Activate the virtual environment and launch FastAPI:
   ```bash
   cd apps/ai-service
   .\venv\Scripts\activate
   uvicorn app.main:app --port 8000 --reload
   ```

---

## 🐳 Containerization Strategy
Each service is built using multi-stage production Dockerfiles:
- **Build Stage:** Installs devDependencies, builds distribution files.
- **Production Stage:** Copies built static files, installs only production dependencies, and drops root permissions to maximize security.
