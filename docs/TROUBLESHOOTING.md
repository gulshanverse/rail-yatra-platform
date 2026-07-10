# RailYatra Production Operations and Troubleshooting Manual

Operational guidelines for resolving common production issues.

---

## 1. Circuit Breaker Outage (AI Service Degraded)

- **Symptom**: Outgoing chat responses raise `503 Service Unavailable` with message `"Circuit Breaker is open"`.
- **Reason**: The FastAPI Python service failed 5 consecutive times (timed out or threw errors).
- **Resolution**:
  1. Check FastAPI logs: `pm2 logs railyatra-ai-service`.
  2. Verify Uvicorn is running on port 8000: `Test-NetConnection -ComputerName localhost -Port 8000`.
  3. If Python service crashed, restart it: `pm2 restart railyatra-ai-service`.
  4. The NestJS circuit breaker automatically recovers after a 30-second cooldown timeout.

---

## 2. SQLite Database File Locked

- **Symptom**: API endpoints write `PrismaClientKnownRequestError: Database is locked`.
- **Reason**: SQLite is single-write only. High write volumes or unclosed connection handles are causing concurrency lockouts.
- **Resolution**:
  1. Identify processes blocking the database file.
  2. Stop backend: `pm2 stop railyatra-backend`.
  3. Ensure SQLite journal files (e.g. `dev.db-journal`) are cleared, indicating a clean transaction close.
  4. Restart: `pm2 start railyatra-backend`.
