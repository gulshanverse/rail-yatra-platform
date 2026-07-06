# RailYatra Engineering Backlog & TODO Checklist

This is the central execution tracking document for the **RailYatra (RailGPT AI)** platform. Each deliverable must satisfy the strict **Definition of Done** before being marked complete.

---

## 📋 Definition of Done (DoD)
For every checked item:
- [ ] Business logic complete & integrated
- [ ] API endpoints versioned and documented
- [ ] Frontend responsive UI complete (with Dark/Light/Auto modes)
- [ ] Error boundary handling & graceful fallbacks implemented
- [ ] Loading, Empty, Success, and Micro-interaction states implemented
- [ ] Accessibility (WCAG 2.1 AA) and mobile viewport verified
- [ ] Security validation (SQL injection, XSS, rate limiting, RBAC checks) verified
- [ ] Unit & integration test suites written and passing (coverage target > 90%)
- [ ] Git commit created on branch & pushed to origin/develop
- [ ] Screenshots, logs, or verification evidence documented

---

## 🏁 Phase 1: Foundation & Design System (Current Target)
- [x] Monorepo workspace configuration (`pnpm-workspace.yaml`, root `package.json`)
- [x] Setup Docker Compose structure (PostgreSQL, Redis, Qdrant services)
- [x] Scaffold NestJS backend inside `/apps/backend` (registered ConfigModule, CORS, ValidationPipe)
- [x] Scaffold Next.js 15 frontend inside `/apps/frontend`
- [x] Scaffold FastAPI AI service inside `/apps/ai-service`
- [x] Create Prisma DB schema models (`User`, `UserSetting`, `Trip`, `SavedRoute`, `PnrHistory`, etc.)
- [x] Establish global CSS variables for dark/light themes and glassmorphism styling in frontend
- [ ] Add basic health checks across all services

## 🔑 Phase 2: Authentication & User Platform
- [ ] Setup NestJS auth modules (Argon2id hashing, JWT access token, and HttpOnly refresh cookies)
- [ ] Develop authentication views: Login screen, Registration screen, and recovery screens
- [ ] Implement user settings dashboard and user settings JSON database synchronization
- [ ] Setup Role-Based Access Control (RBAC) route guards

## 🤖 Phase 3: AI Core Platform
- [ ] Create LangGraph multi-agent infrastructure in FastAPI
- [ ] Implement short-term sliding-window Redis conversation memory
- [ ] Setup persistent conversation history database sync
- [ ] Develop Next.js chat layout displaying streamable Markdown text and custom card loaders

## 🔮 Phase 4: Journey Intelligence Engine
- [ ] Configure ML-driven waitlist prediction and platform delay prediction services
- [ ] Develop PNR tracker API and dashboard showcasing prediction confidence metrics
- [ ] Integrate Recharts graphs plotting seat availability and delay timelines

## 🔍 Phase 5: Search & Planning
- [ ] Establish station and train autocomplete search indexing APIs
- [ ] Design and construct main user dashboard with travel timeline widgets
- [ ] Add natural language context search engine

## 📊 Phase 6: Recommendation Engine
- [ ] Implement multi-criteria ranking algorithm mapping cost, duration, and safety scores
- [ ] Expose explainability parameters (`confidence_score`, `explanation` Markdown, `pros`/`cons`)
- [ ] Render journey recommendation summary view on Next.js client

## 💳 Phase 7: Premium Platform & Feature Gating
- [ ] Deploy subscription gating middleware and AI credit limit counters
- [ ] Setup Feature Flag service for remote environment switches
- [ ] Build premium subscription plan compare and checkout page

## 🔔 Phase 8: Notifications & Real-Time
- [ ] Connect NestJS Socket.io server and Client context listener
- [ ] Implement notification hubs and smart alerts (Tatkal reminders, weather warning signals)
- [ ] Setup SMS/Email template dispatcher

## 📈 Phase 9: Admin Panel & Analytics Dashboard
- [ ] Build role-based administrative control console
- [ ] Create business telemetry, active user logs, and error rate charts
- [ ] Log admin state override histories securely

## 🛡️ Phase 10: AI Optimization & RAG Integration
- [ ] Establish vector database pipelines storing rules, guides, and docs
- [ ] Secure agent prompts with guardrails checking prompt inject attempts

## ⚙️ Phase 11: Production Hardening & Testing
- [ ] Attain complete suite of E2E browser test logs
- [ ] Execute lighthouse core-web-vital audit checks
- [ ] Conduct API vulnerability scanners

## 🚀 Phase 12: Deployment & Launch
- [ ] Build production-ready multi-stage Dockerfiles
- [ ] Configure Prometheus metric pipelines and deployment templates
