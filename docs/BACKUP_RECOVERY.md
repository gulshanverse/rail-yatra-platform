# RailYatra Backup and Disaster Recovery Procedures

This guide details backup strategies and recovery procedures for the RailYatra production PostgreSQL database hosted on Railway.

---

## 1. Automated Backups (Railway Managed)

Railway PostgreSQL includes automatic daily backups with point-in-time recovery. These are managed by Railway's infrastructure and require no manual configuration.

### Railway Backup Features

- **Automatic daily snapshots** retained for 7 days (Pro plan).
- **Point-in-time recovery** within the retention window.
- **Access:** Railway Dashboard → PostgreSQL Service → Backups tab.

---

## 2. Manual Backup with pg_dump

For additional safety, create manual backups using `pg_dump`:

### Prerequisites

- PostgreSQL client tools installed locally.
- Railway CLI installed and authenticated (`railway login`).

### Backup Command

```bash
# Option 1: Using Railway CLI to get connection string
railway run pg_dump --format=custom --no-owner --clean \
  "$DATABASE_URL" > backup-$(date +%Y%m%d-%H%M%S).dump

# Option 2: Direct connection string
pg_dump --format=custom --no-owner --clean \
  "postgresql://user:password@host:port/database" \
  > backup-$(date +%Y%m%d-%H%M%S).dump
```

### Automated Backup Script (Linux/CI)

Create `scripts/db-backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/railyatra-db-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."
pg_dump --format=custom --no-owner --clean "$DATABASE_URL" > "$BACKUP_FILE"

echo "Backup completed: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Retain only last 30 backups
ls -t "$BACKUP_DIR"/railyatra-db-*.dump | tail -n +31 | xargs -r rm
echo "Cleanup complete. Retained last 30 backups."
```

### Schedule via CI/CD (GitHub Actions)

```yaml
# .github/workflows/backup.yml
name: Database Backup
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 02:00 UTC
  workflow_dispatch: {}

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Run Backup
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          railway run bash scripts/db-backup.sh
```

---

## 3. Disaster Recovery Procedures

### 3.1 Database Restore from pg_dump

```bash
# Restore from custom-format dump
pg_restore --no-owner --clean --if-exists \
  -d "$DATABASE_URL" backup-file.dump

# Verify schema integrity after restore
railway run npx prisma migrate deploy
```

### 3.2 Railway Point-in-Time Recovery

1. Open Railway Dashboard → PostgreSQL Service → **Backups**.
2. Select the target recovery point.
3. Click **Restore**.
4. Verify data integrity after restore.

### 3.3 Full Recovery Checklist

In the event of database corruption or catastrophic failure:

1. **Stop incoming traffic:** Remove the backend service from the Railway project's public networking (or set maintenance mode).
2. **Assess damage:** Check Railway logs for the root cause.
3. **Choose recovery method:**
   - **Railway backup available:** Use Railway point-in-time recovery (Section 3.2).
   - **Manual backup available:** Restore using `pg_restore` (Section 3.1).
4. **Verify schema:** Run `railway run npx prisma migrate deploy`.
5. **Verify data integrity:** Run health checks:
   ```bash
   curl https://<backend>.railway.app/api/health/ready
   curl https://<ai-service>.railway.app/health
   ```
6. **Restore traffic:** Re-enable public networking.
7. **Post-incident:** Document the incident and update runbooks.

---

## 4. Redis Recovery

Railway Redis does not persist data across restarts by default. Redis is used as a cache layer — data loss does not affect system correctness.

**Recovery:** Redis caches are automatically repopulated on the next request cycle.

---

## 5. Qdrant Cloud Recovery

Qdrant Cloud manages its own backup and replication strategy.

**Manual re-indexing:** If vector data is lost, re-run the embedding pipeline to regenerate collections:

```bash
railway run python -m app.scripts.reindex_vectors
```

---

## 6. Backup Verification Schedule

| Check                        | Frequency | Owner       |
|------------------------------|-----------|-------------|
| Verify Railway auto-backup   | Weekly    | DevOps      |
| Test pg_dump restore          | Monthly   | DevOps      |
| Validate health endpoints    | Daily     | CI/CD       |
| Review backup retention      | Quarterly | Engineering |
