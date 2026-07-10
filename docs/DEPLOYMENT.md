# RailYatra PM2 Deployment and Cluster Configuration Guide

This guide details PM2 ecosystem provisions and system configurations for production deployments of RailYatra.

---

## 1. Process Monitoring Configuration

Create `ecosystem.config.js` in the workspace root:

```javascript
module.exports = {
  apps: [
    {
      name: 'railyatra-backend',
      script: './apps/backend/dist/main.js',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 5000,
        DATABASE_URL: 'file:./dev.db',
        JWT_SECRET: 'super-secure-production-jwt-key-123'
      },
      listen_timeout: 10000,
      kill_timeout: 15000
    },
    {
      name: 'railyatra-ai-service',
      script: './venv/Scripts/python.exe',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      env: {
        ENV: 'production'
      }
    }
  ]
};
```

---

## 2. Startup Seed Verification

Before exposing the public API endpoints, check system configurations and default feature flags by verifying database state:

```powershell
# 1. Run migrations
npx prisma db push

# 2. Start applications in cluster mode
pm2 start ecosystem.config.js

# 3. Monitor console logs
pm2 logs
```
