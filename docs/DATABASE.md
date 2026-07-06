# RailYatra Database Design Specification

This document details the schema models, indexing rules, caching strategies, and data governance policies.

---

## 💾 Primary Database: PostgreSQL

The application uses PostgreSQL as its primary source of truth, integrated via **Prisma ORM**.

### Core Schema Entity Relationships
```
[User] ──(1:1)── [UserSetting]
  │
  ├──(1:N)── [Trip]
  ├──(1:N)── [SearchHistory]
  ├──(1:N)── [SavedRoute]
  ├──(1:N)── [PnrHistory]
  ├──(1:N)── [Conversation] ──(1:N)── [ChatMessage]
  └──(1:N)── [Subscription]
```

---

## ⚡ Caching Strategy: Redis

Redis is utilized for session management, rate-limiting counters, and caching static resources:
- **API Cache Targets:**
  - Station list queries (TTL: 24 Hours).
  - Train schedules (TTL: 12 Hours).
  - Popular route search results (TTL: 1 Hour).
- **Session Store:**
  - Manages active JWT tokens and short-term chat window histories.

---

## 🔍 Vector Store: Qdrant

Qdrant hosts semantic text embedding indexes:
- **Collections:**
  - `railway_policies`: Storing railway rules, guidelines, and FAQs.
  - `user_travel_history`: Vectorized trip logs for personalized advice.
