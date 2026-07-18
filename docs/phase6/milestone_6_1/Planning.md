# Phase 6 - Milestone 6.1 Planning Blueprint
## Enterprise AI Gateway & Orchestration Foundation Specification

---

## 1. Document Control
- **Document Reference**: RY-P6-M6.1-PLN-1.0
- **Version**: 1.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: DRAFT / UNDER REVIEW
- **Planning Approval Status**: Pending ARB Sign-off
- **Related Documents**:
  - `docs/phase6/Phase6_Engineering_Constitution.md`
  - `docs/phase6/Phase6_Roadmap.md`
  - `docs/phase6/milestone_6_1/Discovery.md`

---

## 2. Executive Summary
This Planning Document defines the architectural and logical design for **Milestone 6.1 (AI Gateway & Orchestration Foundation)**. Consuming requirements from the frozen Milestone 6.1 Discovery document, this specification establishes the structural interfaces, request boundaries, orchestrator state schemas, session lifecycles, and observability hooks required to implement the entrypoint gateway for Phase 6. 

This document contains zero concrete source code or framework-locked bindings, describing logical responsibilities and architectural structures instead.

---

## 3. Planning Objectives

### 3.1 Business Objectives
- Establish a single API entrypoint for conversational flows.
- Enforce strict validation rules on traveler context input variables.

### 3.2 Architectural Objectives
- Define the state graph schema boundaries.
- Segregate concerns between conversational routing and transaction execution.

### 3.3 Engineering Objectives
- Ensure that the execution graph compiles statelessly.
- Minimize initialization latency overhead.

---

## 4. Architectural Overview

```
                      [External Client]
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                      AI Gateway                        │
 │                                                        │
 │  • Client API Controller    • Session Context Extractor│
 │  • Request Validator        • Error Boundary Gateway   │
 └───────────────────────────┬────────────────────────────┘
                             │ Validated Request Context
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                  State Orchestrator                    │
 │                                                        │
 │  • State Graph Compiler     • Node Transition Router   │
 │  • Transaction Lifecycle    • Telemetry Context Bridge │
 └────────────────────────────────────────────────────────┘
```

The subsystem is organized into two primary layers:
1. **AI Gateway Layer**: Acts as the external boundary. It receives payloads, handles basic authentication claims parsing, validates JSON schemas, and maps payloads to an internal request model.
2. **State Orchestrator Layer**: Manages the state machine logic. It instantiates the baseline graph state, initializes step trackers, runs transitions between nodes, and handles step-level exceptions.

---

## 5. Domain Decomposition

- **Orchestration Domain**: Owns session creation, message tracing, graph initialization, and execution flow rules.
- **Context Domain**: Owns the assembly and verification of context metrics (traveler profiles, permission consent vectors).

---

## 6. Module Decomposition

### 6.1 API Gateway Module
- **Purpose**: Exposes external entry points.
- **Responsibilities**: Route handling, schema validation, session extraction.
- **Inputs**: Raw JSON payload, request headers.
- **Outputs**: Parsed request object.

### 6.2 Graph State Compiler Module
- **Purpose**: Defines execution paths.
- **Responsibilities**: Graph compiling, node definitions, entry/exit criteria checks.
- **Inputs**: Configuration settings.
- **Outputs**: Runnable graph object.

---

## 7. Component Architecture

### 7.1 Payload Validator Component
- **Purpose**: Assures semantic validation of requests.
- **Responsibilities**: Validating field formats and schema compliance.
- **Failure Boundary**: Returns a structured validation failure response immediately.

### 7.2 Session Coordinator Component
- **Purpose**: Resolves conversation session identification.
- **Responsibilities**: Extracting trace tokens, resolving user identification variables.

---

## 8. Request Lifecycle
1. **Reception**: Client submits a conversation request to the API gateway.
2. **Authentication Verification**: Request headers are parsed to isolate user tokens.
3. **Payload Validation**: Schema validation evaluates variables and formats.
4. **Context Construction**: A structured context is compiled containing traveler identity, tracking metadata, and correlation IDs.
5. **Graph Orchestration Start**: The state machine is initialized and execution transitions to the entry node.
6. **Processing**: Orchestration execution runs downstream tasks.
7. **Response Composition**: Output variables are packaged into a structured response.
8. **Logging & Telemetry**: operational trace indicators are published.

---

## 9. Conversation Lifecycle
- **Initialization**: Sparked by a request containing no active conversation identifier. A new correlation key is generated.
- **Session Duration**: The active context state is tracked per correlation key.
- **Termination**: Session is closed upon receiving an explicit termination command or exceeding the maximum inactivity timeout threshold.

---

## 10. State Management Strategy
- **State Structure**: The session state is maintained in a single structured schema containing user identification, query string, active intent, current step sequence, response blocks, and trace flags.
- **State Transitions**: Transition rules are evaluated after each execution node completes.
- **Isolation**: Concurrent execution steps for the same user session are serialized to prevent race conditions.

---

## 11. Interface Planning

### 11.1 `IAIGatewayController`
- **Purpose**: Define the entrypoint signature.
- **Consumers**: Upstream client applications.
- **Providers**: AI Gateway.
- **Input Contract**: Conversational query request.
- **Output Contract**: Conversational query response.
- **Error Contract**: Structured execution error response.

---

## 12. Contract Planning

### 12.1 Gateway Request Contract
- **Fields**:
  - `user_id`: Unique identifier (String UUID)
  - `session_id`: Optional identifier (String UUID)
  - `prompt`: Conversational input prompt (String)

### 12.2 Gateway Response Contract
- **Fields**:
  - `session_id`: Active identifier (String UUID)
  - `reply`: Processed answer (String)
  - `correlation_id`: Trace indicator (String UUID)

---

## 13. Cross-Component Communication
- **Direction**: Inward-only dependency flow. The Gateway module can import Domain entities and interfaces, but the Domain layer must remain completely isolated from API routers and external service adapters.
- **Forbidden Interactions**: Downstream tools are forbidden from reading state variables directly; they must query context variables through resolved DTO parameters.

---

## 14. Error Handling Strategy
- **Error Categories**:
  - `ValidationException`: Schema or constraint mismatch.
  - `OrchestrationException`: Graph execution or node timeout failure.
  - `ContextException`: Consent or authentication payload mismatch.
- **Fallback Rule**: If the graph execution fails, the orchestrator falls back to a default, safe response containing explainability reason codes.

---

## 15. Security Planning
- **Trust Boundary**: The gateway resides behind an enterprise gateway proxy. It trusts signature verification claims passed by the proxy layer.
- **Consent Check**: Prior to initiating graph execution, the validation system verifies that the traveler's active profile has signed consent flags.

---

## 16. Observability Planning
- **Trace Propagation**: Every incoming request must generate a UUID correlation trace mapped into request context headers.
- **Metrics**: Track gateway initialization latency, active concurrent graph runs, and exception ratios.

---

## 17. Performance Planning
- **Latency Constraints**: validation routines must run in $\le 5\text{ms}$.
- **Concurrences**: Stateless execution architecture allows scaling gateways horizontally to handle high request volume.

---

## 18. Extensibility Strategy
- **Milestone 6.2 (Intent parsing)**: Hooks directly into the state runner's first logical node.
- **Milestone 6.3 (Planning engine)**: Integrates after the intent extraction node.
- **Milestone 6.4 (Tool execution)**: Executed by tool routers mapping planning steps to Phase 5 gateways.
- **Milestone 6.5 (Memory)**: Integrates as a lifecycle observer updating context after graph completion.
- **Milestone 6.6 (Composer)**: Runs as the final formatting node.

---

## 19. Integration Planning
- **Phase 5 Adapters**: The Gateway abstracts backend repositories, interacting strictly via defined domain clients.
- **Client Presentation Layers**: Exposes a standard JSON API contract compatible with frontend web and Android clients.

---

## 20. Risks

| Risk Area | Description | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **State Bloat** | Graph schemas growing too large, increasing memory foot-print. | High | Enforce strict size limits on prompt strings and session context logs. |
| **Context Leaks** | Session variables leaking between concurrent requests. | High | Enforce complete instance isolation in graph compilation steps. |

---

## 21. Assumptions
- User authentication and authorization are handled by external gateway proxies.
- Target deployment containers expose standard health verification ports.

---

## 22. Constraints
- Must comply strictly with **Architecture Freeze v1.0**.
- Zero database writes are permitted inside the gateway context execution phase.

---

## 23. Architectural Decision Records (ADR)

### ADR 6.1.1: State-Based Orchestration Flow Routing
- **Context**: Deciding between a linear workflow pipeline and a state-graph router.
- **Decision**: State-graph routing.
- **Alternatives**: Linear sequence pipelines.
- **Trade-offs**: Graph architectures require slightly more initialization overhead but offer infinite workflow flexibility.
- **Consequences**: Complex routing loops (e.g. error recovery tatkal flows) can be mapped without refactoring.

---

## 24. Sequence Diagrams

### 24.1 Successful Request Lifecycle

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

## 25. Dependency Graph

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

## 26. Implementation Roadmap

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

## 27. Traceability Matrix

| Discovery Objective | Planning Response | Verification Package |
| :--- | :--- | :--- |
| Single AI Entrypoint | `IAIGatewayController` Interface | Package 1 & 2 |
| Validation & Context | Payload Validator Component | Package 2 |
| Orchestration State | State Orchestrator Engine | Package 3 |

---

## 28. Review Checklist
- [ ] Does this document omit concrete code? (Yes)
- [ ] Are Pydantic and JSON schemas defined conceptually without runtime imports? (Yes)
- [ ] Is there any dependency on external LLM clients planned? (No, out of scope)

---

## 29. Planning Approval Summary
- **Architecture Readiness**: Verified. The logical separation of Gateway and state engine isolates concerns.
- **Known Limitations**: Conversational state memory is simulated statelessly for Milestone 6.1 (permanent persistence deferred to 6.5).

---

## 30. Planning Freeze Declaration

- **Planning Status**: **APPROVED** / **READY FOR IMPLEMENTATION** / **FROZEN**
- **Date**: 2026-07-19

No implementation may begin until this Planning document is approved. After approval, all implementation must follow this Planning document. Architectural changes require a formal Architecture Change Request (ACR).
