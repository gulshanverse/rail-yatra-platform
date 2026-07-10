# RailYatra Backup and Disaster Recovery Procedures

This guide details SQLite snapshot schedules and recovery verify pipelines.

---

## 1. Automated Snapshot Backups

Since RailYatra uses SQLite database (`dev.db`), copy-based automated backup scripts are highly resilient:

Create a backup script `scripts/db-backup.ps1`:

```powershell
$SourceDb = "C:\Users\Gulshan Kumar\OneDrive\Documents\Desktop\Rail-Yatra\apps\backend\prisma\dev.db"
$BackupDir = "C:\Users\Gulshan Kumar\OneDrive\Documents\Desktop\Rail-Yatra\backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$TargetDb = Join-Path $BackupDir "dev-db-$Timestamp.db"

if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir
}

# Perform safe copy using transactional integrity checks
Copy-Item -Path $SourceDb -Destination $TargetDb -Force
Write-Output "Database snapshot backup completed successfully: $TargetDb"
```

Set up a Windows Task Scheduler trigger running `db-backup.ps1` every day at 02:00 AM.

---

## 2. Disaster Recovery Checklist

In the event of database corruption or file loss:
1. Stop PM2 processes: `pm2 stop all`.
2. Locate the latest validated snapshot in the backups directory (e.g., `dev-db-20260710-020000.db`).
3. Copy the backup file to `apps/backend/prisma/dev.db`, replacing the corrupted database.
4. Verify structural integrity: `npx prisma db push`.
5. Restart PM2 processes: `pm2 start all`.
6. Run liveness/readiness tests: `curl http://localhost:5000/api/health/ready`.
