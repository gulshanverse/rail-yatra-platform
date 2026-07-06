# RailYatra API Specification

All external and internal REST and WebSocket APIs conform to these structures.

---

## 🌐 API Design Rules
- **Versioning:** Prefixed with `/api/v1/`.
- **Response Format:** Uniform JSON envelopes.
- **WebSocket Gateway:** Secure WebSockets (`wss://`) for live telemetry and chat streaming.

---

## 🛠️ Global Envelopes

### Success Envelope
```json
{
  "success": true,
  "data": {},
  "timestamp": "2026-07-06T13:17:00Z"
}
```

### Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "WAITLIST_PREDICTION_ERROR",
    "message": "Waitlist prediction parameters are invalid.",
    "traceId": "9123-abcde-1290"
  },
  "timestamp": "2026-07-06T13:17:00Z"
}
```

---

## 📡 Initial Core Endpoints

### 1. Health Status
- **URL:** `GET /api/v1/health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "backend-core",
    "database": "connected"
  }
  ```

### 2. AI Parsing Chat Service (FastAPI)
- **URL:** `POST /api/v1/ai/chat`
- **Request Payload:**
  ```json
  {
    "message": "I want to travel from NDLS to BGP next Friday",
    "conversationId": "uuid-string-here"
  }
  ```
- **Response Payload:**
  ```json
  {
    "reply": "Analyzing NDLS to BGP routes for next Friday.",
    "parsed_intent": "route_search",
    "confidence": 0.95
  }
  ```
