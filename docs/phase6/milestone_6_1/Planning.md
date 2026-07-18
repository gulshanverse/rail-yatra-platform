# Phase 6 - Milestone 6.1 Planning Blueprint
## Enterprise AI Gateway & Orchestration Foundation Specification

---

## 1. Document Control
- **Document Reference**: RY-P6-M6.1-PLN-2.0
- **Version**: 2.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: APPROVED / ACTIVE / FROZEN
- **Planning Approval Status**: Approved by the Architecture Review Board (ARB)
- **Related Documents**:
  - `docs/phase6/Phase6_Engineering_Constitution.md`
  - `docs/phase6/Phase6_Roadmap.md`
  - `docs/phase6/milestone_6_1/Discovery.md`

---

## 2. Executive Summary
This Planning Document defines the architectural blueprint for **Milestone 6.1 (AI Gateway & Orchestration Foundation)**. Derived from the frozen Milestone 6.1 Discovery document, this specification establishes the structural interfaces, request boundaries, orchestrator state schemas, session lifecycles, and observability hooks required to implement the entrypoint gateway for Phase 6. 

All sections are written in conceptual, technology-independent architectural language to prevent implementation leakage.

---

## 3. Planning Objectives

### 3.1 Business Objectives
- Enable standard entry points for conversational queries, ensuring consistent customer experiences.
- Enforce strict validation rules on traveler profile privacy settings.

### 3.2 Architecture Objectives
- Segregate execution orchestrators from presentation APIs.
- Define a stateless graph configuration pattern.

### 3.3 Engineering Objectives
- Ensure that the execution graph compiles statelessly without runtime session locks.
- Minimize serialization latency overhead.

---

## 4. Architectural Overview

```
                      [Presentation Boundary]
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   AI Gateway Facade   │
                     └───────────┬───────────┘
                                 │ Logical Context
                                 ▼
                     ┌───────────────────────┐
                     │   State Orchestrator  │
                     └───────────┬───────────┘
                                 │ Subsystem Call
                                 ▼
                     ┌───────────────────────┐
                     │  Core Domain Gateway  │
                     └───────────────────────┘
```

The system is structured as a decoupled, layered architecture:
- **Presentation Boundary**: Translates external request signals into internal domain models.
- **AI Gateway Facade**: Handles token claims mapping, request validation, and metadata tracing.
- **State Orchestrator**: Runs workflow planning nodes, tracking execution steps in a thread-isolated context state.
- **Core Domain Gateway**: Delegates business queries to downstream analytical engines.

---

## 5. Domain-Driven Design (DDD) Planning

### 5.1 Bounded Contexts
- **AI Gateway Bounded Context**: Governs conversation initialization, request validation, authentication translation, and correlation mappings.
- **Orchestration Bounded Context**: Governs state graph compiling, execution node routing, and step failure recovery workflows.

### 5.2 Context Map
- The **AI Gateway Context** acts as an **Upstream Partner** to the **Orchestration Context**, feeding it validated requests.
- The **Orchestration Context** utilizes an **Anti-Corruption Layer (ACL)** to convert raw external requests into internal domain entities, preserving the integrity of core domain models.

---

## 6. Clean Architecture Design
The subsystem strictly follows the Dependency Inversion Principle. Dependencies flow inward-only:

```
[API Routing Layers] ──▶ [Gateway Controller] ──▶ [Orchestrator Interfaces] ──▶ [Domain State Models]
```

- **Imports Rules**: Domain entities must never import components from the gateway or API routing layers. All communication must occur through interfaces.

---

## 7. Module Decomposition

### 7.1 Input validation Module
- **Purpose**: Verifies incoming payload compliance.
- **Responsibilities**: Checks string bounds and schema formats.
- **Inputs**: Raw request parameters.
- **Outputs**: Validated context payload.
- **Dependencies**: Domain DTO Schemas.

### 7.2 Session Lifecycle Module
- **Purpose**: Controls conversational state durations.
- **Responsibilities**: Generates session IDs, handles timeouts, and releases resources.
- **Inputs**: Active session tokens.
- **Outputs**: Live session state metrics.

---

## 8. Component Planning

### 8.1 Schema Validator Component
- **Purpose**: Evaluates payload structural integrity.
- **Responsibilities**: Prevents malformed prompts from entering the orchestrator.
- **Consumers**: Gateway Router.
- **Providers**: Schema validation rules.
- **Failure Boundary**: Throws immediate validation exceptions.

### 8.2 Trace Manager Component
- **Purpose**: Governs request observability.
- **Responsibilities**: Propagates correlation IDs across threads.
- **Consumers**: AI Gateway, State Orchestrator.
- **Providers**: Logging and telemetry interfaces.

---

## 9. Component Responsibility Matrix

| Component | Owns | Does Not Own | Collaborates With |
| :--- | :--- | :--- | :--- |
| **Schema Validator** | Structural validation logic | Authentication | Gateway Router |
| **Session Manager** | Session lifecycle timers | Persisted state storage | State Orchestrator |
| **Trace Manager** | Correlation token mapping | Log message writing | Logging System |

---

## 10. Interface Planning

### 10.1 `IGatewayController`
- **Purpose**: Decouples API handlers from gateway execution.
- **Consumer**: Web API routers.
- **Provider**: Gateway execution engines.
- **Responsibilities**: Accept request variables, validate schema constraints, and dispatch execution contexts.

### 10.2 `IStateOrchestrator`
- **Purpose**: Orchestrates node sequence logic.
- **Consumer**: Gateway controller.
- **Provider**: Graph execution runtimes.
- **Responsibilities**: Compiles graphs, runs transitions, and coordinates error recovery.

---

## 11. Contract Planning
- **Request Contract**: Conceptual schema detailing user reference (UUID), prompt text (String), and session token (String).
- **Response Contract**: Conceptual schema detailing response text (String), session token (UUID), and correlation token (UUID).
- **State Schema Contract**: The internal state carrying session tokens, intent markers, execution steps, and active context metrics.

---

## 12. State Management

```
               [Initialize State]
                       │
                       ▼
            [State Context Created]
                       │
                       ▼
          [Orchestration Transitions]
             /                   \
            ▼                     ▼
     [Step Complete]       [Step Failure]
            │                     │
            ▼                     ▼
      [State Saved]        [Fallback State]
```

- **Isolation**: Each conversational thread executes within an isolated thread context, preventing concurrency collisions.
- **Recovery**: If a node fails, the orchestrator reverts the state to the last verified fallback marker.

---

## 13. Request Lifecycle
1. **Reception**: Gateway receives input payload.
2. **Context Resolution**: Extracts traveler identity credentials from request metadata headers.
3. **Validation**: Schema validator evaluates formats.
4. **Graph Compilation**: The orchestrator instantiates the graph state with correlation IDs.
5. **Execution**: Graph nodes process the request.
6. **Telemetry Publication**: Writes operational tracking trace logs.
7. **Response Output**: Formats outputs and returns response packages.

---

## 14. Conversation Lifecycle
- **Initialization**: Sparked by a request containing no active session token. A new correlation key is generated.
- **Continuation**: Context is updated with active user messages under the same session ID.
- **Termination**: Session is closed upon receiving an explicit termination command or exceeding the maximum inactivity timeout threshold.

---

## 15. Cross-Component Communication
- **Allowed Interactions**: The Gateway module is permitted to query the State Orchestrator interface. The State Orchestrator is permitted to call downstream gateways.
- **Forbidden Interactions**: Downstream gateways are forbidden from reading active Orchestrator state variables directly.

---

## 16. Security Planning
- **Authentication**: Pre-validated by API gateway proxies before routing to the AI Gateway.
- **Sensitive Data Isolation**: Profile data is encrypted in transit and must be redacted from operational logs.

---

## 17. Observability Planning
- **Correlation ID**: Generates a unique UUID on request entry.
- **Logs**: Centralized trace logs track graph node entries and exits.
- **Metrics**: Captures graph completion counts, transaction times, and validation failures.

---

## 18. Performance Planning
- **Concurrency**: State orchestration runs statelessly, enabling horizontal scalability.
- **Resource Limits**: Requests exceeding message length budgets are pruned at the entry boundary.

---

## 19. Reliability & Resilience Planning
- **Fault Isolation**: Graph execution runs within error boundaries; node exceptions do not impact concurrent worker threads.
- **Graceful Degradation**: Fallback templates are rendered on execution failure.

---

## 20. Extensibility Planning
- **Milestone 6.2 (Intent parsing)**: Added as the initial node in the state graph.
- **Milestone 6.3 (Planning)**: Integrated after the intent parsing node.
- **Milestone 6.4 (Tool Execution)**: Mapped to tool routers executing plan steps.
- **Milestone 6.5 (Memory)**: Registered as a state persistence observer.
- **Milestone 6.6 (Composer)**: Registered as the final execution node.

---

## 21. Integration Planning
- **Phase 5 Gateways**: The orchestrator interacts with prior gateways strictly through read-only adapters.
- **Frontend / Android**: Interface via standardized API contracts.

---

## 22. Risks

| Risk Area | Description | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **State Bloat** | Context state growing too large. | High | Enforce strict size limits on prompt strings. |
| **Context Leaks** | Session variables leaking between concurrent requests. | High | Enforce complete instance isolation in graph compilation steps. |

---

## 23. Assumptions
- Security claims parsing is verified by external proxies before requests reach the Gateway.
- Container runtimes manage execution lifecycle signals.

---

## 24. Constraints
- Must comply with **Architecture Freeze v1.0**.
- Zero database writes are permitted inside the gateway context execution phase.

---

## 25. Architectural Decision Records (ADR)

### ADR 6.1.1: State-Based Orchestration Flow Routing
- **Context**: Deciding between a linear workflow pipeline and a state-graph router.
- **Decision**: State-graph routing.
- **Alternatives**: Linear sequence pipelines.
- **Trade-offs**: Graph architectures require slightly more initialization overhead but offer infinite workflow flexibility.
- **Consequences**: Complex routing loops (e.g. error recovery tatkal flows) can be mapped without refactoring.

---

## 26. Sequence Diagrams

### 26.1 Successful Request Lifecycle

```
[Client]             [Gateway API]         [State Orchestrator]        [Core Engines]
   │                       │                         │                       │
   │─── Submit prompt ────▶│                         │                       │
   │                       │── Check constraints ───▶│                       │
   │                       │                         │── Run tool queries ──▶│
   │                       │                         │                       │── Resolve ──▶
   │                       │◀── Combine context ─────│                       │
   │◀── Render response ───│                         │                       │
```

---

## 27. Dependency Graph

```
           [Gateway Interfaces]
                    ▲
                    │
           [Gateway Controller] ──▶ [State Orchestrator Engine]
                    │
                    ▼
           [Domain DTO Schemas]
```

---

## 28. Implementation Roadmap

### Package 1: Gateway Interfaces and Contracts
- **Goal**: Define all core gateway protocols and base exception wrappers.
- **Dependencies**: None.
- **Expected Output**: Standard interface classes and custom error classes.
- **Completion Criteria**: 100% check-in of interface contracts.

### Package 2: Controller Routing and Schemas
- **Goal**: Expose endpoints and validate incoming payloads.
- **Dependencies**: Package 1.
- **Expected Output**: Router classes, request/response validation schemas.
- **Completion Criteria**: Unit validation tests pass successfully.

### Package 3: State Graph Compiler
- **Goal**: Initialize the execution state graph and run tests.
- **Dependencies**: Package 2.
- **Expected Output**: Graph compilation classes and status runners.
- **Completion Criteria**: Integration scenario tests pass.

---

## 29. Traceability Matrix

| Discovery Objective | Planning Decision | Architecture Component |
| :--- | :--- | :--- |
| Single AI Entrypoint | `IGatewayController` Interface | Gateway Router |
| Validation & Context | Payload Validator Component | Schema Validator |
| Orchestration State | State Orchestrator Engine | State Orchestrator |

---

## 30. Quality Attributes
- **Maintainability**: Low coupling via dependency inversion interfaces.
- **Scalability**: Stateless request handling architecture.
- **Reliability**: Isolated execution boundary runtimes.
- **Observability**: correlation trace tokens are generated on entry.

---

## 31. Non-Functional Architecture Review
The proposed design is verified against core principles:
- **DDD Compliance**: Clean bounded context map separating gateway routing from orchestration state variables.
- **Clean Architecture Compliance**: Inward-only dependency flow. No domain classes import routing controllers.
- **SOLID Compliance**: High interface segregation and clear single responsibility.

---

## 32. Review Checklist
- [ ] Does this document omit concrete code? (Yes)
- [ ] Are DTO schemas described conceptually without JSON formats? (Yes)
- [ ] Is the design technology independent? (Yes)

---

## 33. Planning Review Summary
- **Major Improvements**: Added Context map, Bounded Context mappings, layer validation, and custom exception definitions.
- **Implementation Leakage Removed**: Replaced references to specific libraries, frameworks, HTTP route paths, class designs, and target latency metrics with conceptual architecture and governance descriptions.
- **Planning Completeness**: High. Complete design maps logical components.

---

## 34. Planning Freeze Certification
The Architecture Review Board hereby approves this document.

- **Status**: **FINAL** / **APPROVED** / **READY FOR IMPLEMENTATION** / **FROZEN**
- **Effective Date**: 2026-07-19

All future implementation work for Milestone 6.1 must strictly follow this Planning document. No architectural modifications are permitted after freeze unless approved through a formal Architecture Change Request (ACR).
