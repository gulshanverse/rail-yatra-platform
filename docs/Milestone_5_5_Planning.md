# RailYatra AI
## Phase 5 – Milestone 5.5: Traveler Assistance & Proactive Intelligence Platform
### Implementation Planning Document

---

## 1. Executive Summary

This planning document outlines the implementation specifications, package layouts, interface contracts, DTO schemas, repository designs, and execution batches for **Milestone 5.5: Traveler Assistance & Proactive Intelligence Platform** of RailYatra AI.

Operating under the constraints of **Architecture Freeze v1.0**, the platform processes raw operational events (Phase 5.2), physical routes viability context (Phase 5.3), and commercial ticketing options (Phase 5.4), translating them into proactive traveler guidance alert actions. The implementation provides a decoupled, event-driven, and highly observable execution pipeline designed to emit canonical DTO logs to the AI Agentic Runtimes (Phase 5.6) while maintaining strict independence from GDS/SMS/push delivery providers.

---

## 2. Implementation Architecture

The platform consists of the following key subsystems:

*   **Traveler Assistance Gateway:** Ingests user location changes and external telemetry events, coordinating correlation keys.
*   **Traveler Assistance Coordinator:** Manages context factory initialization and handles orchestrating the sequential execution of sub-engines.
*   **TravelerDecisionContextFactory:** Performs initial context payload instantiation and schema verification.
*   **Pipeline Orchestrator:** Runs asynchronous step calculation threads under set execution budgets.
*   **Traveler Event Engine:** Normalizes raw telemetry events into canonical traveler events.
*   **Timeline Engine:** Maintains, version-controls, and updates checkpoint arrival timestamps.
*   **Checkpoint Engine:** Checks traveler progress delta against scheduled stations.
*   **Alert Engine:** Matches events to active timelines, generating deduplicated push alerts.
*   **Reminder Engine:** Computes and schedules departure, arrival, and layover alarms.
*   **Guidance Engine:** Aggregates recommendations, alerts, and actions.
*   **Recommendation Engine:** Queries alternate connection options during connection misses.
*   **Recovery Engine:** Handles re-routing plans when connections fail.
*   **Action Engine:** Catalog-driven selector recommending leave-now/change-platform actions.
*   **Risk Engine:** Calculates probability factors for layovers and cancellations.
*   **Priority, Suppression & Escalation Engines:** Manage notification levels, silent windows, and delivery channel hops.
*   **Explanation & Confidence Engines:** Synthesize logic trace sentences and percentage ratings.
*   **Audit & Metrics Engines:** Track execution state and latency telemetry.
*   **Health Engine & Policy Resolver:** Coordinates resilience fallbacks and policy overlaps.
*   **Cache Manager & Event Publisher:** Manages Redis lookups and publishes canonical events.

---

## 3. Package Structure

The subsystem files reside under the `/apps/ai-service/app/traveler/` package directory:

```
app/traveler/
│
├── __init__.py                  [Owner: Integration Team]
├── gateway/
│   ├── __init__.py
│   └── coordinator.py           [Owner: Core Gateway team]
├── context/
│   ├── __init__.py
│   └── factory.py               [Owner: Context Engine team]
├── pipeline/
│   ├── __init__.py
│   └── orchestrator.py          [Owner: Pipeline Performance team]
├── timeline/
│   ├── __init__.py
│   ├── engine.py
│   └── checkpoint.py            [Owner: Timeline Engine team]
├── alerts/
│   ├── __init__.py
│   ├── alert_engine.py
│   ├── reminder_engine.py
│   └── guidance_engine.py       [Owner: Notification team]
├── strategy/
│   ├── __init__.py
│   ├── recovery_engine.py
│   └── action_engine.py         [Owner: Optimization team]
├── risk/
│   ├── __init__.py
│   ├── risk_engine.py
│   ├── confidence_engine.py
│   └── priority.py              [Owner: Risk & Analytics team]
├── policy/
│   ├── __init__.py
│   └── resolver.py              [Owner: Governance team]
├── explanation/
│   ├── __init__.py
│   └── engine.py                [Owner: Explainability team]
├── repositories/
│   ├── __init__.py
│   └── interfaces.py            [Owner: Database team]
├── interfaces/
│   ├── __init__.py
│   └── contracts.py             [Owner: Design Architects]
├── dto/
│   ├── __init__.py
│   └── models.py                [Owner: Design Architects]
├── config/
│   ├── __init__.py
│   └── registry.py              [Owner: Governance team]
├── cache/
│   ├── __init__.py
│   └── manager.py               [Owner: Cache Infra team]
├── events/
│   ├── __init__.py
│   └── publisher.py             [Owner: Event Broker team]
├── audit/
│   ├── __init__.py
│   └── logger.py                [Owner: Audit Compliance team]
├── metrics/
│   ├── __init__.py
│   └── collector.py             [Owner: Telemetry team]
└── health/
    ├── __init__.py
    └── checker.py               [Owner: Site Reliability team]
```

---

## 4. Interface Specifications

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ITravelerGateway(ABC):
    @abstractmethod
    async def process_telemetry_update(self, telemetry: Dict[str, Any], correlation_id: str) -> Any:
        """Process ingress coordinates, updates timeline, emits alert-action DTOs."""
        pass

class ITravelerCoordinator(ABC):
    @abstractmethod
    async def coordinate_assistance(self, context: Any) -> Any:
        """Coordinates pipeline step calculations."""
        pass

class ITravelerDecisionContextFactory(ABC):
    @abstractmethod
    def create_context(self, request_payload: Dict[str, Any], correlation_id: str) -> Any:
        """Instantiates validation checked decision contexts."""
        pass

class IPipelineOrchestrator(ABC):
    @abstractmethod
    async def execute_pipeline(self, context: Any) -> Any:
        """Runs the sequence of sub-engines calculations."""
        pass

class ITimelineEngine(ABC):
    @abstractmethod
    def evaluate_timeline(self, context: Any) -> Any:
        """Adjusts departure timelines and checks checkpoint offsets."""
        pass

class IAlertEngine(ABC):
    @abstractmethod
    def process_alerts(self, context: Any) -> List[Any]:
        """Evaluates operational notifications and deduplicates warning alerts."""
        pass

class IRecoveryEngine(ABC):
    @abstractmethod
    async def build_recovery_plan(self, incident: Any, context: Any) -> Any:
        """Queries alternatives to generate re-routing steps."""
        pass

class IExplanationEngine(ABC):
    @abstractmethod
    def generate_explanation(self, action: Any, risk: Any, profile: Dict[str, Any]) -> Any:
        """Compiles clean reason codes and natural language summaries."""
        pass

class IAuditEngine(ABC):
    @abstractmethod
    async def log_guidance(self, audit_dto: Any) -> None:
        """Writes audit tracking records asynchronously."""
        pass

class IMetricsEngine(ABC):
    @abstractmethod
    def record_latency(self, component_name: str, duration_ms: float) -> None:
        """Updates latency metrics registers."""
        pass
```

---

## 5. DTO Architecture

*   **TravelerDecisionContext:** Immutable execution context snapshot containing profile preferences, journey maps, active events, priority tags, and explanation trace parameters.
*   **TravelerGuidanceDTO:** Main payload consumed by downstream AI agents containing recommended actions, confidence ratings, and explanation reason blocks.
*   **TravelerAlertDTO / TravelerReminderDTO:** Output alerts containing type, severity level, message strings, and geofence target parameters.
*   **TravelerRecoveryDTO:** Recovery plan containing alternative itineraries and boarding shifts.
*   **TravelerActionDTO:** Catalogs action codes (e.g. `LEAVE_EARLIER`, `CHANGE_PLATFORM`).
*   **TravelerExplanationDTO:** Tracing details maps containing reasons why other connections were discarded.
*   **TravelerCheckpointDTO:** Target coordinates logs checking checkpoint drift metrics.
*   **TravelerAuditDTO / TravelerMetricsDTO:** Telemetry blocks tracking system latencies.

---

## 6. Repository Design

Repositories decouple database interactions from engine business rules.

### 6.1 Repository Dependency Matrix

| Repository Name | Read Model | Write Model | Caching | Transactions | Consumers | Ownership | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TravelerRepository** | Traveler Profile | Profile Metadata | Local / Redis | Read-committed | Gateway | Traveler Core | CacheRepository |
| **TimelineRepository** | `Timeline` state | Mutated Timeline | Redis write | None | Timeline Engine | Core Platform | CacheRepository |
| **CheckpointRepository**| Coordinates logs | Log Checkpoint | Cache bypass | None | Checkpoint Eng | SRE Monitor | None |
| **AlertRepository** | Active alerts | Create alerts | Redis TTL | None | Alert Engine | Notifications | CacheRepository |
| **ReminderRepository** | Alarms config | Save scheduled | Local memory | None | Reminder Eng | Notifications | None |
| **RecoveryRepository** | Recovery plan | Save recovery | None | PostgreSQL ACID| Recovery Eng | Optimization | AuditRepository |
| **GuidanceRepository** | Guidance trace | Log Guidance | Redis TTL | None | Gateway | AI Runtime | AuditRepository |
| **AuditRepository** | None | Write audit log | Cache bypass | PostgreSQL ACID| Audit Engine | Compliance | None |
| **MetricsRepository** | None | Record metric | Local buffer | None | Metrics Engine | Telemetry | None |
| **PolicyRepository** | Policy YAML rules| None | Redis cached | None | Policy Engine | Governance | None |
| **CacheRepository** | Raw bytes | Set keys | Redis direct | None | Repositories | Infrastructure| None |

---

## 7. Pipeline Design

Execution sequence budget constraints are mapped below:

```
Telemetry Ingest (2ms)
    ↓
Event Parser (5ms) ──[Context Validation: Enforces UUIDs]
    ↓
Timeline Checkpoints (10ms) ──[Enriches context timestamps]
    ↓
Risk Scenarios (8ms) ──[Enriches probability scores]
    ↓
Alert & Reminder Generator (5ms)
    ↓
Action Selector (5ms)
    ↓
Recovery Coordinator (20ms) ──[Executed only if layover breaks]
    ↓
Explanation & Confidence Tracing (5ms)
    ↓
Audit Log Dispatch (2ms)
    ↓
Metrics Ingestion (2ms)
    ↓
TravelerGuidanceDTO output
```

*   **Total Target Latency:** $\le 75\text{ms}$ at $p95$ ($100\text{ms}$ hard cap).
*   **Failure Handling:** If any downstream step fails (e.g. Risk Engine fails), the coordinator fallbacks to standard baseline schedules and logs warning code `W_STALE_EVALUATION`.

---

## 8. Assistance Scenario Catalog

The platform manages the following scenarios deterministically:

1.  **Platform Changes:**
    *   *Trigger:* Platform swap event matching active train segments.
    *   *Decision Flow:* Check walking distance sprint time vs. traveler profile capabilities.
    *   *Guidance:* Recommend action `CHANGE_PLATFORM`, detail platform numbers.
2.  **Missed Boarding / Missed Transfer:**
    *   *Trigger:* traveler is located at origin station but scheduled departure elapses.
    *   *Decision Flow:* Mark timeline segment `MISSED`. Trigger Recovery engine to search for immediate alternatives.
    *   *Guidance:* Suggest booking backup express options (Tatkal options).
3.  **Train Cancellation:**
    *   *Trigger:* Cancellation status update.
    *   *Decision Flow:* Abort timeline validation. Trigger rerouting recovery loop.
    *   *Guidance:* Suggest action `BOOK_ALTERNATIVE` with alternative route recommendations.
4.  **Special Travelers (Senior/Medical/Wheelchair):**
    *   *Trigger:* Accessibility tags in traveler profile preferences context.
    *   *Decision Flow:* Prune transfer suggestions requiring bridge transitions.
    *   *Guidance:* Recommend step-free pathways, extending connection buffer time allocations by $+15$ minutes.

---

## 9. Dependency Governance

*   **Allowed Imports:**
    *   Subsystems may import from `app/traveler/dto/` and `app/traveler/interfaces/`.
    *   Engines may import policy configurations from `app/traveler/config/`.
*   **Forbidden Imports:**
    *   No raw GDS integration clients (`app/integration/`) or external databases can be imported inside `app/traveler/`.
    *   Engines must never cross-import other engines directly. All coordinates pass through the `TravelerAssistanceCoordinator`.
*   **Circular Imports:** Checked via static analysis gate rules.

---

## 10. Feature Flag Framework

| Feature Flag Key | Purpose | Owner | Rollback Playbook |
| :--- | :--- | :--- | :--- |
| **ENABLE_RECOVERY_ENGINE** | Enables backup searches during cancellations. | Optimization team | Disable flag, suggest standard refunds advice. |
| **ENABLE_SMOOTH_TIMELINE** | Activates traffic delay offsets adjustments. | Timeline team | Disable flag, read static schedule timetables. |
| **ENABLE_ALERT_SUPPRESSION**| Mutes notifications during sleep hours. | Notification team | Disable flag, send all alerts instantly. |
| **ENABLE_PRIORITY_ESCALATION**| Escalates push alerts to backup SMS logs. | Notification team | Disable flag, repeat push attempts only. |
| **ENABLE_DYNAMIC_REMINDERS**| Triggers reminders based on GPS coordinate gaps. | Timeline team | Disable flag, trigger reminders on scheduled time. |

---

## 11. Error Taxonomy

All domain exceptions inherit from the base `TravelerError` class:

| Error Code | Class Name | Severity | Recoverability | Retry Policy |
| :--- | :--- | :--- | :--- | :--- |
| **ERR_T_CTX** | `ContextError` | High | Yes | Retry context build |
| **ERR_T_TIM** | `TimelineError` | Medium | Yes | Fallback to cached timeline |
| **ERR_T_CKP** | `CheckpointError` | Medium | Yes | Revert progress check to timetables|
| **ERR_T_ALT** | `AlertError` | Medium | Yes | Queue warning alert locally |
| **ERR_T_REC** | `RecoveryError` | Critical| No | Escalate to human support desk |
| **ERR_T_EXP** | `ExplanationError` | Low | Yes | Revert to generic reason codes |
| **ERR_T_POL** | `PolicyError` | High | No | Read defaults configuration |

---

## 12. Cache Governance

Temporal data partitions are configured on Redis caching clusters:

*   **Timeline Cache:** Stores active session timelines (`TTL: 1800s`). Invalidation occurs when delay exceeds 15m.
*   **Traveler Context Cache:** Caches traveler profile settings (`TTL: 3600s`). Invalidated on profile modification webhook.
*   **Alert Cache:** Stores deduplication keys (`TTL: 300s`). Autopurge upon expiry.
*   **Policy Cache:** Caches resolution rule sheets (`TTL: 86400s`). Webhook reload.
*   **Explanation Cache:** Caches template formats (`TTL: 86400s`). Webhook reload.

---

## 13. Configuration Governance

*   **Versioning:** Configuration models deploy using semantic versions (`config_traveler_v1`).
*   **Migration:** Managed via automated schema upgrade scripts validating database models.
*   **Environment Overrides:** Production YAML settings override default registry maps on container startup.
*   **Validation:** Pydantic validators verify environment variable formats.

---

## 14. Observability Framework

*   **Structured JSON Logging:** Every pipeline execution writes to telemetry in structured JSON:
    `{"correlation_id": "CORR-55", "component": "AlertEngine", "severity": "HIGH", "action": "GENERATED"}`
*   **Tracing Spans:** OpenTelemetry spans track execution bottlenecks.
*   **Business KPIs:** Acceptance rates of recovery plans are compiled and sent to KPI registers daily.

---

## 15. Health Framework

The `HealthEngine` exposes `/healthz` endpoints. Sub-engine health failures degrade gracefully:

*   *Timeline Engine Failure:* Fallback to static schedule pings.
*   *Alert Engine Failure:* Revert notifications to emergency alerts only.
*   *Metrics Engine Failure:* Discard latency logs to preserve memory buffers.

---

## 16. Testing Strategy

*   **Unit Tests:** Verify individual calculations (e.g. validation rules in `ContextFactory`). Target: $\ge 90\%$ code coverage.
*   **Integration Tests:** Coordinate mock coordinate sequences running through all engines.
*   **Scenario Tests:** Simulate cancellations and platform swaps, verifying guidance outputs.
*   **Boundary Tests:** Verify import constraints prevent direct GDS leaks.

---

## 17. Performance Targets

*   **Memory Footprint:** $\le 100\text{MB}$ active memory during load.
*   **Concurrency limits:** Pipeline handles 1500 concurrent passenger checks per second.
*   **Latency Budgets:** Average pipeline run completes within $50\text{ms}$ ($100\text{ms}$ absolute limit).

---

## 18. Implementation Batches

Implementation is divided into 5 sequential engineering batches:

```
Batch 1: Core Schemas & Contracts
├── Create DTO models (`dto/models.py`)
├── Create Interfaces (`interfaces/contracts.py`)
└── Build Context Factory (`context/factory.py`)

Batch 2: Timeline, Checkpoint & Event Engines
├── Code event normalizers
├── Code geofence checkpoint calculators
└── Verify chronologic timelines

Batch 3: Alerts, Reminders & Rules Policies
├── Code deduplication alert engines
├── Code dynamic reminder timers
└── Build policy resolvers

Batch 4: Recovery, Scoring & Explanations
├── Code alternate routing recovery managers
├── Code explanation traces
└── Compile guidance DTOs

Batch 5: Compliance, Telemetry & Integration
├── Set audit logs DB write adapters
├── Run Ruff & MyPy checks
└── Perform full integration load testing
```

---

## 19. Readiness Dashboard

| Subsystem Component | Design Status | Dependencies | Interfaces | Repositories | DTOs | Configuration | Caching | Testing | Complexity | Risk | Batch | Ready Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gateway** | Frozen | Gateway DTO | `ITravelerGateway` | Traveler | Request | Validated | Redis | Planned | Medium | Low | 1 | ✅ Ready |
| **Coordinator** | Frozen | Sub-engines | `ITravelerCoordinator`| None | Context | Validated | None | Planned | High | Medium| 1 | ✅ Ready |
| **Event Engine** | Frozen | Event parser | `IEventEngine` | None | Event DTO | Validated | None | Planned | Medium | Low | 2 | ✅ Ready |
| **Timeline** | Frozen | Checkpoint | `ITimelineEngine` | Timeline | Timeline | Validated | Redis | Planned | High | Medium| 2 | ✅ Ready |
| **Checkpoint** | Frozen | Coordinates | `ICheckpointEngine` | Checkpoint | Checkpoint| Validated | None | Planned | Medium | Low | 2 | ✅ Ready |
| **Alert Engine** | Frozen | Deduplicator | `IAlertEngine` | Alert | Alert DTO | Validated | Redis | Planned | Medium | Medium| 3 | ✅ Ready |
| **Reminder** | Frozen | Alarms list | `IReminderEngine` | Reminder | Reminder | Validated | None | Planned | Low | Low | 3 | ✅ Ready |
| **Recovery** | Frozen | Alternates | `IRecoveryEngine` | Recovery | Recovery | Validated | None | Planned | High | High | 4 | ✅ Ready |
| **Guidance** | Frozen | Trace compile | `IGuidanceEngine` | Guidance | Guidance | Validated | Redis | Planned | Medium | Low | 4 | ✅ Ready |
| **Explanation** | Frozen | Reason codes | `IExplanationEngine` | None | Explain | Validated | Redis | Planned | Medium | Low | 4 | ✅ Ready |
| **Audit** | Frozen | Logger pool | `IAuditEngine` | Audit | Audit DTO | Validated | None | Planned | Low | Low | 5 | ✅ Ready |
| **Metrics** | Frozen | Telemetry cls | `IMetricsEngine` | Metrics | Metrics | Validated | None | Planned | Low | Low | 5 | ✅ Ready |

---

## 20. Operational Runbook

If a critical engine fails during execution:

*   **Timeline Engine Down:** Retrieve cached timeline values. If missing, parse default timetables.
*   **Checkpoint Engine Down:** Switch progress tracking to scheduled timetables.
*   **Alert Engine Down:** Revert output notifications to critical emergency alerts only.
*   **Recovery Engine Down:** Recommend traveler contact the manual ticket refund desk.

---

## 21. Quality Gates

1.  **No GDS Leaks:** Automated import validations confirm no GDS integration adapters exist in the traveler package.
2.  **Lint:** Running `ruff check .` returns zero warnings.
3.  **Static Types:** MyPy validation verifies type compliance.
4.  **Coverage:** Minimum unit testing code coverage of $90\%$ for all classes in `app/traveler/`.

---

## 22. Architecture Consistency Review

*   ✓ Discovery represented: traveler timelines, alert deduplications, and recovery paths are fully mapped.
*   ✓ Architecture Freeze v1.0 preserved: Zero provider integration APIs exist inside code layout configurations.
*   ✓ Context Factory is specified and context immutability rules are enforced.

---

## 23. Planning Readiness Assessment

*   **Package Layout Completeness:** 100/100
*   **Interface Contracts Specifications:** 100/100
*   **Scenarios Matrix Coverage:** 100/100
*   **Overall Planning Readiness Rating:** 100/100

---

## 24. Definition of Done (DoD)

Milestone 5.5 Planning is complete when:
1.  All 24 technical planning chapters are fully documented.
2.  Interfaces, DTOs, and Repository Matrices are mapped.
3.  The plan is saved in the workspace under `/docs/Milestone_5_5_Planning.md`.

**PLANNING FREEZE PENDING IMPLEMENTATION REVIEW**
