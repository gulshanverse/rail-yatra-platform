# RailYatra AI Platform
## Phase 8 – Real-Time Operations Platform
### Document 3 – Technical Architecture Specification

**Version:** 1.0  
**Phase:** 8  
**Status:** Approved Technical Blueprint for Implementation  

---

## 📑 Table of Contents
1. Technical Overview
2. Project Structure
3. File Mapping
4. Module Responsibilities
5. API Contracts
6. Domain Models
7. Repository Layer
8. Service Layer
9. Event Taxonomy
10. State Machines
11. AI Integration
12. Database & Persistence Design
13. Error Handling & Resilience Strategy
14. Observability & Telemetry
15. Testing Strategy
16. CI/CD Validation & Quality Gates
17. Performance Targets
18. Security Design
19. Implementation Rules & Directives
20. Deliverables Checklist
21. Sequence Diagrams
22. Interface Contracts
23. Dependency Matrix

---

## 1. Technical Overview

### Technical Objectives
- Build an event-driven, real-time railway operations engine (`app/realtime/`) inside `apps/ai-service`.
- Ingest, validate, normalize, and dispatch operational events across train states, passenger journey lifecycles, ETAs, incidents, notifications, and operational dashboards.
- Provide live operational context to AI Core (Phase 3), Enterprise Intelligence (Phase 5), AI Orchestration (Phase 6), and Predictive Intelligence (Phase 7).
- Maintain 100% backward compatibility, strict zero-lint-error policy with Ruff (`ruff==0.15.21`), and green CI pipeline (`pytest`).

### Existing Codebase Analysis
- **Framework**: Python 3.11 / FastAPI, Pydantic v2, Pytest, Ruff `0.15.21`.
- **Existing Architecture**:
  - Phase 1 & 2: Base FastAPI application, endpoints, JWT authentication.
  - Phase 3 & 4: AI Core, Journey Platform, agent tools, vector store (Qdrant), memory models.
  - Phase 5: Enterprise Intelligence Platform (`app/intelligence/`).
  - Phase 6: AI Orchestration & Response Composer (`app/memory/`, `app/planner/`).
  - Phase 7: Predictive Intelligence Platform (`app/predictive/`).
- **Phase 8 Integration Point**: New top-level module `app/realtime/` with REST router `app/api/realtime_router.py` mounted on main FastAPI application instance.

### Design Constraints
- Zero modification to existing domain models or database schemas from Phase 1–7.
- Complete domain isolation under `app/realtime/`.
- In-memory event store and state cache with strict thread safety and async concurrency support.

---

## 2. Project Structure

```
apps/ai-service/app/
├── realtime/
│   ├── __init__.py
│   ├── interfaces.py          # Interfaces, Enums, Contracts
│   ├── models.py              # Domain Data Models (Pydantic v2)
│   ├── events.py              # Event Taxonomy & Envelope definitions
│   ├── gateway.py             # Event Ingestion & Normalization Gateway
│   ├── dispatcher.py          # Asynchronous Event Dispatcher & Router
│   ├── store.py               # In-Memory Event Store & History Log
│   ├── train_tracker.py       # Live Train State Tracker
│   ├── journey_tracker.py     # Active Passenger Journey State Tracker
│   ├── eta_engine.py          # Dynamic ETA Recalculation Engine
│   ├── incident_engine.py     # Operational Incident Detection Engine
│   ├── decision_engine.py     # Operational Decision Support Engine
│   ├── notification_engine.py # Prioritized Notification Orchestrator
│   ├── dashboard_service.py   # Operational Metrics & Dashboard Visualizer
│   ├── observability.py       # Telemetry, Metrics, Tracing & Logging
│   └── orchestrator.py        # Central Real-Time Operations Orchestrator
├── api/
│   └── realtime_router.py     # REST API Router (/api/realtime/*)
└── tests/
    └── test_realtime_operations_platform.py # Complete Test Suite
```

---

## 3. File Mapping

### New Files to Create

1. [`apps/ai-service/app/realtime/__init__.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/__init__.py): Module initialization.
2. [`apps/ai-service/app/realtime/interfaces.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/interfaces.py): Enums (`EventType`, `TrainStatus`, `JourneyStatus`, `IncidentSeverity`), protocol interfaces (`IEventGateway`, `ITrainTracker`, `IJourneyTracker`, `IETAEngine`, `IIncidentEngine`, `INotificationEngine`).
3. [`apps/ai-service/app/realtime/models.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/models.py): Pydantic domain models (`OperationalEvent`, `TrainState`, `JourneyState`, `Incident`, `ETAResult`, `NotificationPayload`, `DashboardMetrics`).
4. [`apps/ai-service/app/realtime/events.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/events.py): Factory methods for constructing typed operational events.
5. [`apps/ai-service/app/realtime/gateway.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/gateway.py): Validates, normalizes, and sanitizes incoming raw operational events.
6. [`apps/ai-service/app/realtime/dispatcher.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/dispatcher.py): Event pub/sub router dispatching events to state trackers and engines.
7. [`apps/ai-service/app/realtime/store.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/store.py): Immutable event history log & state snapshot storage.
8. [`apps/ai-service/app/realtime/train_tracker.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/train_tracker.py): Manages live train location, speed, current station, platform, and delay.
9. [`apps/ai-service/app/realtime/journey_tracker.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/journey_tracker.py): Tracks passenger active travel state, transfer connections, and status transitions.
10. [`apps/ai-service/app/realtime/eta_engine.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/eta_engine.py): Recalculates dynamic ETA based on live delay, weather, and signal holds.
11. [`apps/ai-service/app/realtime/incident_engine.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/incident_engine.py): Detects disruptions, platform changes, cancellations, and connection risks.
12. [`apps/ai-service/app/realtime/decision_engine.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/decision_engine.py): Generates operational recommendations for impacted passengers and control teams.
13. [`apps/ai-service/app/realtime/notification_engine.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/notification_engine.py): Prioritizes, formats, and dispatches passenger alerts.
14. [`apps/ai-service/app/realtime/dashboard_service.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/dashboard_service.py): Generates aggregated operational metrics for control room dashboards.
15. [`apps/ai-service/app/realtime/observability.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/observability.py): Emits latency counters, event metrics, and health diagnostics.
16. [`apps/ai-service/app/realtime/orchestrator.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/realtime/orchestrator.py): Single entry point coordinating event ingestion, tracking, decisioning, and notification.
17. [`apps/ai-service/app/api/realtime_router.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/api/realtime_router.py): REST API router exposing real-time operational endpoints.
18. [`apps/ai-service/app/tests/test_realtime_operations_platform.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/tests/test_realtime_operations_platform.py): Full test suite covering all functional requirements and API endpoints.

### Existing Files to Modify

1. [`apps/ai-service/app/main.py`](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/main.py): Import and include `realtime_router` under `/api/realtime`.

---

## 4. Module Responsibilities

### Event Gateway (`gateway.py`)
- **Inputs**: Raw event dictionaries or HTTP payloads.
- **Outputs**: Validated `OperationalEvent` instances.
- **Public Interface**: `ingest_event(raw_data: dict) -> OperationalEvent`
- **Failure Modes**: Raises `ValueError` on invalid payloads or missing fields.

### Dispatcher (`dispatcher.py`)
- **Inputs**: Validated `OperationalEvent`.
- **Outputs**: Async execution of registered handlers.
- **Public Interface**: `dispatch(event: OperationalEvent) -> None`

### Event Store (`store.py`)
- **Inputs**: `OperationalEvent` instances.
- **Outputs**: Event history queries, event replay streams.
- **Public Interface**: `append(event)`, `get_events_by_train(train_number)`, `get_all_events()`

### Train Tracker (`train_tracker.py`)
- **Inputs**: Train-related operational events.
- **Outputs**: Authoritative `TrainState`.
- **Public Interface**: `update_state(event)`, `get_state(train_number) -> TrainState`

### Journey Tracker (`journey_tracker.py`)
- **Inputs**: Passenger events & TrainState changes.
- **Outputs**: Authoritative `JourneyState`.
- **Public Interface**: `update_journey(event)`, `get_journey(journey_id) -> JourneyState`

### ETA Engine (`eta_engine.py`)
- **Inputs**: `TrainState`, route distance, delay metrics.
- **Outputs**: `ETAResult`.
- **Public Interface**: `calculate_eta(train_number, station_code) -> ETAResult`

### Incident Engine (`incident_engine.py`)
- **Inputs**: Train & Journey state changes.
- **Outputs**: List of detected `Incident` instances.
- **Public Interface**: `evaluate_incidents(train_state, journey_state) -> List[Incident]`

### Decision Engine (`decision_engine.py`)
- **Inputs**: Active `Incident` and `JourneyState`.
- **Outputs**: Actionable operational recommendations.
- **Public Interface**: `generate_recommendations(incident, journey) -> List[str]`

### Notification Engine (`notification_engine.py`)
- **Inputs**: `Incident`, passenger contact, priorities.
- **Outputs**: Formatted `NotificationPayload`.
- **Public Interface**: `send_notification(journey_id, incident, message) -> NotificationPayload`

### Dashboard Service (`dashboard_service.py`)
- **Inputs**: Live TrainState, JourneyState, and Incident records.
- **Outputs**: `DashboardMetrics`.
- **Public Interface**: `get_metrics() -> DashboardMetrics`

---

## 5. API Contracts

### Endpoints Overview

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/realtime/events` | Ingest live operational event | Admin / Ingestion Gateway |
| `GET` | `/api/realtime/trains/{train_number}` | Retrieve live train operational state | Authenticated / Public |
| `GET` | `/api/realtime/journeys/{journey_id}` | Retrieve live passenger journey state | Authenticated |
| `GET` | `/api/realtime/eta/{train_number}/{station_code}` | Compute dynamic ETA for a station | Authenticated / Public |
| `GET` | `/api/realtime/incidents` | List active operational incidents | Operations / Admin |
| `POST` | `/api/realtime/notifications/dispatch` | Manually dispatch notification | Operations / Admin |
| `GET` | `/api/realtime/dashboard` | Retrieve live control room metrics | Operations / Admin |
| `GET` | `/api/realtime/health` | Health check endpoint | Public |

---

## 6. Domain Models

### Key Entities

```python
class OperationalEvent(BaseModel):
    event_id: str
    event_type: EventType
    train_number: str
    station_code: Optional[str] = None
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class TrainState(BaseModel):
    train_number: str
    current_station: str
    next_station: Optional[str] = None
    status: TrainStatus
    delay_minutes: int = 0
    current_platform: Optional[str] = None
    speed_kmh: float = 0.0
    last_updated: str

class JourneyState(BaseModel):
    journey_id: str
    passenger_id: str
    train_number: str
    status: JourneyStatus
    origin_station: str
    destination_station: str
    current_station: Optional[str] = None
    eta_destination: str
    transfer_risk: bool = False
    last_updated: str

class Incident(BaseModel):
    incident_id: str
    train_number: str
    severity: IncidentSeverity
    title: str
    description: str
    affected_passengers_count: int = 0
    created_at: str
    resolved: bool = False

class NotificationPayload(BaseModel):
    notification_id: str
    journey_id: str
    passenger_id: str
    title: str
    message: str
    priority: str  # HIGH, MEDIUM, LOW
    dispatched_at: str
```

---

## 7. Repository Layer

- In-memory thread-safe dictionaries with `asyncio.Lock()` protection.
- Maintained repositories:
  - `EventRepository`
  - `TrainStateRepository`
  - `JourneyStateRepository`
  - `IncidentRepository`
  - `NotificationRepository`

---

## 8. Service Layer

`RealTimeOperationsOrchestrator`: Coordinates the full workflow:
1. `ingest_and_process_event(raw_event)`
2. Updates `TrainTracker`
3. Updates `JourneyTracker`
4. Re-evaluates `ETAEngine`
5. Evaluates `IncidentEngine`
6. Dispatches notifications via `NotificationEngine`
7. Updates `DashboardService` metrics

---

## 9. Event Taxonomy

| Event Type | Priority | Description |
| :--- | :--- | :--- |
| `TRAIN_STARTED` | MEDIUM | Train departed origin station |
| `TRAIN_STOPPED` | HIGH | Unexpected unscheduled stop |
| `TRAIN_DELAYED` | HIGH | Delay updated |
| `TRAIN_RESCHEDULED` | CRITICAL | Rescheduled departure time |
| `TRAIN_CANCELLED` | CRITICAL | Service cancelled |
| `PLATFORM_CHANGED` | HIGH | Platform reassigned at station |
| `COACH_CHANGED` | MEDIUM | Coach position / composition modified |
| `TRAIN_DIVERTED` | CRITICAL | Route diverted to alternate track |
| `BOARDING_STARTED` | LOW | Passenger boarding open |
| `BOARDING_COMPLETED` | LOW | Passenger boarding closed |
| `INCIDENT_CREATED` | CRITICAL | Operational incident logged |
| `INCIDENT_RESOLVED` | MEDIUM | Operational incident cleared |

---

## 10. State Machines

### Train State Machine
`SCHEDULED` ──► `BOARDING` ──► `DEPARTED` ──► `RUNNING` ──► `DELAYED` ──► `ARRIVED` ──► `COMPLETED`  
*(Special transitions: `CANCELLED`, `DIVERTED`)*

### Journey State Machine
`PLANNED` ──► `READY` ──► `BOARDING` ──► `ONBOARD` ──► `TRANSFER` ──► `COMPLETED`  
*(Special transitions: `DISRUPTED`, `CANCELLED`)*

---

## 11. AI Integration

- Phase 8 exports live operational context via `orchestrator.get_live_ai_context(train_number, journey_id)`.
- Context object includes:
  - `live_train_state`: Delay, current platform, speed.
  - `active_incidents`: Disruptions, platform changes.
  - `journey_status`: Connection risk, dynamic ETA.
  - `predictive_comparison`: Phase 7 predicted waitlist/delay vs live actual state.

---

## 12. Database & Persistence Design

- Phase 8 utilizes an in-memory event-sourcing and active state storage pattern inside `app/realtime/store.py`.
- Fully forward-compatible with PostgreSQL / Redis persistence adapters for future production phases.

---

## 13. Error Handling & Resilience Strategy

- Validation failures return standard `400 Bad Request` HTTP responses.
- Ingestion errors are captured without bringing down the event dispatcher loop.
- Graceful degradation: If ETA calculation fails, last known ETA is returned with `confidence_score = 0.0`.

---

## 14. Observability & Telemetry

- Structured logging with JSON format via `logging.getLogger("ai-service.realtime")`.
- Real-time performance counters:
  - `total_events_processed`
  - `active_incidents_count`
  - `active_journeys_monitored`
  - `average_processing_latency_ms`

---

## 15. Testing Strategy

- Unit tests for all state machines, event gateway, ETA calculation, and incident detection.
- Integration tests for REST API endpoints (`/api/realtime/*`).
- Target: 100% pass rate across all existing 371 tests + new Phase 8 test suite.

---

## 16. CI/CD Validation & Quality Gates

- **Ruff Compliance**: Zero errors under `ruff==0.15.21`.
- **Pytest Suite**: All tests pass cleanly.
- **GitHub Actions**: Must result in GREEN build status on push.

---

## 17. Performance Targets

- Event processing latency: `< 15ms`
- ETA calculation latency: `< 5ms`
- Dashboard metrics fetch: `< 10ms`

---

## 18. Security Design

- Reuses Phase 2 JWT authentication and security middlewares.
- Protects administrative operational endpoints (`POST /api/realtime/events`, `POST /api/realtime/notifications/dispatch`).

---

## 19. Implementation Rules & Directives

1. Clean architectural boundaries under `apps/ai-service/app/realtime/`.
2. Explicit router inclusion in `apps/ai-service/app/main.py`.
3. Strict adherence to typed Pydantic models.
4. No modification of Phases 1–7 existing business logic.

---

## 20. Deliverables Checklist

- `app/realtime/interfaces.py`
- `app/realtime/models.py`
- `app/realtime/events.py`
- `app/realtime/gateway.py`
- `app/realtime/dispatcher.py`
- `app/realtime/store.py`
- `app/realtime/train_tracker.py`
- `app/realtime/journey_tracker.py`
- `app/realtime/eta_engine.py`
- `app/realtime/incident_engine.py`
- `app/realtime/decision_engine.py`
- `app/realtime/notification_engine.py`
- `app/realtime/dashboard_service.py`
- `app/realtime/observability.py`
- `app/realtime/orchestrator.py`
- `app/api/realtime_router.py`
- `app/tests/test_realtime_operations_platform.py`

---

## 21. Sequence Diagrams

### Event Ingestion & Impact Flow
```
Railway Source ──► Gateway ──► Dispatcher ──► TrainTracker ──► IncidentEngine ──► NotificationEngine ──► Passenger
                                                 │
                                                 └──► JourneyTracker ──► DashboardService
```

---

## 22. Interface Contracts

```python
class IEventGateway(Protocol):
    def ingest(self, raw_data: dict) -> OperationalEvent: ...

class ITrainTracker(Protocol):
    def update(self, event: OperationalEvent) -> TrainState: ...

class IJourneyTracker(Protocol):
    def update(self, event: OperationalEvent) -> JourneyState: ...

class INotificationEngine(Protocol):
    def dispatch(self, journey_id: str, incident: Incident) -> NotificationPayload: ...
```

---

## 23. Dependency Matrix

| Layer / Module | Gateway | Store | TrainTracker | JourneyTracker | IncidentEngine | NotificationEngine | DashboardService |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gateway** | — | Yes | No | No | No | No | No |
| **Dispatcher** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **TrainTracker** | No | Yes | — | No | No | No | No |
| **JourneyTracker**| No | Yes | Yes | — | No | No | No |
| **IncidentEngine**| No | Yes | Yes | Yes | — | No | No |
| **Notification** | No | Yes | No | Yes | Yes | — | No |
| **Dashboard** | No | Yes | Yes | Yes | Yes | Yes | — |

---
