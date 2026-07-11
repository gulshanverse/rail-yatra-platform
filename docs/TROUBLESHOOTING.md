# RailYatra Production Operations and Troubleshooting Manual

Operational guidelines for resolving common production issues.

---

## 1. Circuit Breaker Outage (AI Service Degraded)

- **Symptom**: Outgoing chat responses raise `503 Service Unavailable` with message `"Circuit Breaker is open"`.
- **Reason**: The FastAPI Python service failed 5 consecutive times (timed out or threw errors).
- **Resolution**:
  1. Check FastAPI logs in the Railway Console: Dashboard → `railyatra-ai-service` → **Deployments** → **Logs**.
  2. Verify Uvicorn is running and reachable.
  3. If Python service crashed or is hanging, trigger a Redeploy or Restart from the Railway Console.
  4. The NestJS backend circuit breaker automatically recovers after a 30-second cooldown timeout.

---

## 2. Pre-Flight Startup Failures (Backend Exits Instantly)

- **Symptom**: The NestJS container logs show error and the container exits with exit code 1.
- **Reason**: The startup guard failed to establish a connection to PostgreSQL or Redis within the allowed timeout.
- **Resolution**:
  1. Check if the PostgreSQL or Redis service in the Railway project is healthy.
  2. Verify that the `DATABASE_URL` and `REDIS_URL` are correctly bound/linked in the backend service variables.
  3. Verify database credentials and connection parameters.
  4. Once connectivity is restored, trigger a rebuild or redeployment of the backend service.

---

## 3. JWT Expiration and Refresh Issues

- **Symptom**: Users are signed out frequently, or token refresh requests fail with `401 Unauthorized`.
- **Reason**: The `JWT_REFRESH_SECRET` or token verification logic failed, or the refresh token is missing.
- **Resolution**:
  1. Confirm that `JWT_SECRET` and `JWT_REFRESH_SECRET` are correctly configured in Railway variables and are identical across scale replicas.
  2. Inspect the network requests on the frontend to verify refresh cookies or request payloads.
