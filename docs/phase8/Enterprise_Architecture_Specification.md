# RailYatra AI Platform
## Phase 8 – Real-Time Operations Platform
### Document 2 – Enterprise Architecture Specification

**Version:** 1.0  
**Phase:** 8  
**Status:** Architecture Design  

---

## Table of Contents
1. Architecture Vision
2. Architectural Goals
3. Architecture Principles
4. Existing Platform Assessment
5. Enterprise System Architecture
6. Architectural Layers
7. Core Domain Model
8. Module Architecture
9. Event-Driven Architecture
10. AI Integration Architecture
11. Data Flow Architecture
12. Service Communication
13. State Management Architecture
14. Operational Intelligence Architecture
15. Notification Architecture
16. Dashboard Architecture
17. Security Architecture
18. Observability Architecture
19. Scalability Strategy
20. Reliability Strategy
21. Integration Strategy
22. Architecture Decisions
23. Architecture Constraints
24. Future Extension Points

---

## 1. Architecture Vision

The Real-Time Operations Platform transforms RailYatra into an event-driven railway intelligence system.

Instead of periodically querying data, the platform reacts continuously to operational events, updates train and journey state, coordinates AI reasoning, and proactively assists passengers.

The architecture must support real-time responsiveness while remaining modular, scalable, resilient, and fully compatible with Phases 1–7.

---

## 2. Architectural Goals

The architecture shall:
- Maintain a single source of truth for live operational state.
- Decouple event producers from consumers.
- Minimize inter-module dependencies.
- Reuse existing AI and orchestration services.
- Support future integrations without architectural redesign.
- Scale horizontally as event volume increases.
- Preserve clean boundaries between business domains.

---

## 3. Architecture Principles

The platform follows these principles:
- **Event-Driven:** Every operational change is represented as an immutable event.
- **Domain-Driven:** Modules are organized by business capability rather than technical utility.
- **Single Responsibility:** Each service owns one business concern.
- **Loose Coupling:** Services communicate through events or well-defined interfaces.
- **High Cohesion:** Related business logic remains within the same bounded context.
- **Extensibility:** Future railway providers and integrations can be added without modifying existing modules.

---

## 4. Existing Platform Assessment

Phase 8 extends—not replaces—the existing platform.

| Phase | Subsystem Reuse |
| :--- | :--- |
| Phase 1 – Foundation | 100% |
| Phase 2 – Authentication | 100% |
| Phase 3 – AI Core | 100% |
| Phase 4 – Journey Platform | 100% |
| Phase 5 – Intelligence | 95% |
| Phase 6 – AI Orchestration | 100% |
| Phase 7 – Predictive Intelligence | 100% |

No existing subsystem should be redesigned.

---

## 5. Enterprise System Architecture

```
                  Railway Event Sources
                           │
                           ▼
                 Real-Time Event Gateway
                           │
                           ▼
                Event Processing Platform
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  Train State       Journey State       Event Store
     Platform          Platform
        │                  │
        └────────────┬─────┘
                     ▼
         Operational Intelligence Engine
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 AI Core       Notification      Dashboard
 Platform         Platform         Platform
```

---

## 6. Architectural Layers

### Presentation Layer
- Dashboard APIs
- Journey APIs
- Notification APIs
- Monitoring APIs

### Application Layer
- Coordinates workflows without containing business rules.

### Domain Layer
Contains:
- Train state
- Journey state
- ETA calculation
- Incident detection
- Operational decisions

*This layer owns the core business logic.*

### Infrastructure Layer
Contains:
- Persistence
- Event transport
- Logging
- Metrics
- External adapters

---

## 7. Core Domain Model

The platform revolves around six primary domains:
1. **Train**
2. **Journey**
3. **Passenger**
4. **Operational Event**
5. **Incident**
6. **Notification**

Each domain has a clear owner, boundary, and lifecycle.

---

## 8. Module Architecture

### Event Platform
Responsible for:
- Receiving events
- Validation
- Normalization
- Routing
- Replay support

### Train State Platform
Responsible for:
- Current location
- Delay tracking
- Platform assignments
- Coach composition
- Journey progress

### Journey State Platform
Responsible for:
- Passenger lifecycle
- Boarding state
- Transfer state
- Connection monitoring

### ETA Platform
Responsible for:
- Dynamic ETA
- Confidence scoring
- Delay propagation

### Operational Intelligence Platform
Responsible for:
- Incident detection
- Passenger impact calculation
- Operational recommendations
- AI context generation

### Notification Platform
Responsible for:
- Alert prioritization
- Notification orchestration
- Delivery history

### Dashboard Platform
Responsible for:
- Live metrics
- Active incidents
- Operational health
- Passenger impact overview

---

## 9. Event-Driven Architecture

Every event follows the same lifecycle:

```
Event Received ──► Validation ──► Normalization ──► Classification ──► Persistence
                                                                          │
Audit Log ◄── Dashboard Update ◄── Notification ◄── AI Evaluation ◄── State Update
```

No module may bypass this lifecycle.

---

## 10. AI Integration Architecture

The AI Core consumes live operational context from Phase 8 to:
- Explain ongoing operational disruptions.
- Recommend alternate travel options.
- Answer passenger queries using current operational state.
- Compare live events with predictive outputs.
- Trigger orchestration workflows.

The AI Core remains independent; Phase 8 provides context, not conversational logic.

---

## 11. Data Flow Architecture

```
Railway Event
      │
      ▼
Event Gateway
      │
      ▼
Event Processor
      │
      ├── Update Train State
      ├── Update Journey State
      ├── Store Event
      ├── Trigger AI
      ├── Trigger Notifications
      └── Update Dashboard
```

---

## 12. Service Communication

Communication rules:
- Prefer asynchronous event publication for operational updates.
- Use synchronous APIs only when an immediate response is required.
- Avoid direct dependencies between unrelated domains.
- Publish stable interfaces for cross-module interactions.

---

## 13. State Management Architecture

Three authoritative state stores:
1. **Train State** – current operational status of trains.
2. **Journey State** – progress of passenger journeys.
3. **Event Store** – immutable history of operational events.

Derived views (dashboard, AI context, analytics) must be computed from these sources rather than maintaining duplicate state.

---

## 14. Operational Intelligence Architecture

Operational Intelligence consumes:
- Train state
- Journey state
- Predictive outputs (Phase 7)
- Historical events

It produces:
- Incidents
- Passenger impact evaluations
- Recommendations
- AI operational context

---

## 15. Notification Architecture

```
Operational Event ──► Priority Engine ──► Notification Orchestrator ──► Delivery Manager ──► Notification History
```

The architecture separates decision-making from delivery, allowing future channels (SMS, WhatsApp, email) to be added without changing business rules.

---

## 16. Dashboard Architecture

The dashboard aggregates information from:
- Event Store
- Train State
- Journey State
- Operational Intelligence

It does not contain business logic; it visualizes operational data through dedicated APIs.

---

## 17. Security Architecture

Operational endpoints inherit Phase 2 security:
- JWT authentication.
- Role-based access control.
- Audit logging.
- Input validation.
- Protected administrative APIs.

No Phase 8 module introduces a separate authentication mechanism.

---

## 18. Observability Architecture

Every service emits:
- Structured logs.
- Metrics.
- Health status.
- Processing latency.
- Error counts.
- Trace identifiers.

These signals support monitoring and future SRE capabilities.

---

## 19. Scalability Strategy

The architecture must support:
- High event throughput.
- Thousands of concurrent journeys.
- Horizontal scaling of processing services.
- Stateless application services where practical.

---

## 20. Reliability Strategy

The platform should:
- Preserve event integrity.
- Continue operating during partial failures.
- Retry transient processing failures.
- Ensure idempotent handling of repeated events.
- Record failures for later analysis.

---

## 21. Integration Strategy

Phase 8 integrates with:
- **Phase 3** – AI Core.
- **Phase 5** – Enterprise Intelligence.
- **Phase 6** – AI Orchestration.
- **Phase 7** – Predictive Intelligence.

No breaking changes to public APIs should be introduced.

---

## 22. Architecture Decisions (ADRs)

Key decisions include:
1. Event-driven architecture for operational workflows.
2. Domain-based module boundaries.
3. Immutable event history.
4. Single source of truth for operational state.
5. Asynchronous communication as default.
6. Backward compatibility with existing phases.

---

## 23. Architecture Constraints

The implementation must not:
- Duplicate business logic already implemented.
- Bypass the event-processing lifecycle.
- Introduce circular dependencies.
- Replace existing AI orchestration.
- Break existing APIs.
- Reduce test coverage or quality gates.

---

## 24. Future Extension Points

The architecture intentionally leaves extension points for Phase 9 and Phase 10:
- External railway integrations (IRCTC, NTES, RailMadad).
- Payment providers.
- Weather intelligence.
- Multi-modal travel.
- Kubernetes deployment.
- Distributed event streaming.
- Multi-region operations.
- Advanced SRE and disaster recovery.
