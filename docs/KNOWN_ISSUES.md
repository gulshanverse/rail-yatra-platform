# RailYatra Known Issues & Operations Log

This document lists the active known issues, performance bottlenecks, and graceful workarounds for the RailYatra platform.

---

## 1. SQLite Database Concurrency Locking (RY-KI-001)

- **Issue:** SQLite does not support high concurrency write transactions. Under load testing or parallel operations, requests might fail with `PrismaClientKnownRequestError: Database is locked`.
- **Impact:** Medium. Rare during closed beta, but likely under higher load during GA.
- **Workaround:**
  1. The backend uses the `ResilienceClient` strategy pattern to queue requests or retry operations.
  2. For GA deployment, migrate to a dedicated PostgreSQL instance using docker-compose overrides or a managed database.
- **Target Resolution Version:** v1.1.0-GA (Migration to PostgreSQL is pre-configured).

---

## 2. External API Provider Rate Limiting (RY-KI-002)

- **Issue:** Third-party railway data providers enforce strict token bucket limits.
- **Impact:** High.
- **Workaround:**
  1. Local Redis cache is configured to act as the primary lookup layer with high TTLs (station list: 24h, schedules: 12h, searches: 1h).
  2. If the external provider returns `429 Too Many Requests` or times out, the system automatically falls back to `synthetic.py` data to guarantee uninterrupted user experience.
- **Target Resolution Version:** Ongoing performance tuning.

---

## 3. Large LangGraph Graph Execution Overhead (RY-KI-003)

- **Issue:** Multi-agent LangGraph pipelines run sequentially, introducing response delays under complex routing prompts.
- **Impact:** Low.
- **Workaround:**
  1. Master Classifier classifies intents quickly and bypasses complex specialist agents when user requests are simple chat or conversion queries.
  2. Endpoints stream response tokens in real-time via Server-Sent Events (SSE) to reduce perceived latency.
- **Target Resolution Version:** v1.2.0

---

## 4. Tatkal Time Lock (RY-KI-004)

- **Issue:** During peak Tatkal hours (10:00 AM - 12:00 PM IST), mock waitlist predictions may have high standard deviation due to rapid fluctuations in availability.
- **Impact:** Low.
- **Workaround:** The Journey Intelligence system displays a warning card alerting users about high Tatkal volatility.
- **Target Resolution Version:** Continuous engine updates.
