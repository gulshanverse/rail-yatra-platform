# Phase 6 — Milestone 6.4 Enterprise Architecture Planning
## Execution Engine

---

## PART 1 — Architecture Foundation

### 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.4-PLAN-3.1 |
| **Version** | 3.1.0 |
| **Status** | APPROVED FOR ARCHITECTURE FREEZE |
| **Architecture Owner** | Principal Enterprise Architect |
| **Architecture Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Authors** | Chief Software Architect, Enterprise Solution Architect, Principal AI Architect |
| **Approvers** | Enterprise Governance Committee, Technical Design Authority, Product Sponsor |
| **Classification** | Internal Enterprise Confidential |
| **Governing References** | `Phase6_Engineering_Constitution.md`, `Enterprise Planning Standard v3.1` |
| **Related Discovery Document**| `docs/phase6/milestone_6_4/Discovery.md` |
| **Related Roadmap** | `Phase6_Roadmap.md` |

#### Purpose
This document establishes the frozen technical planning specification for the **Execution Engine** (Milestone 6.4). It defines the structural domain model, application layer use cases, interaction boundaries, security parameters, and quality attributes required to guide the subsequent engineering implementation phase.

---

### 2. Executive Summary

#### Strategic Context
Milestone 6.3 finalized the generation and verification of a stateless, structured travel plan. Milestone 6.4 is the operational layer designed to carry out this plan safely. The Execution Engine coordinates execution commands, handles failures, executes rollback sequences, and updates traveler context without exposing transactional APIs to state inconsistencies.

#### Key Architectural Decisions
* **Stateful Execution Isolation**: Maintain execution state separately from formulation logic, tracking step transitions dynamically.
* **Compensating Transactions**: Apply transactional rollback commands to revert intermediate successes when downstream actions fail.
* **Asynchronous Coordination**: Execute steps asynchronously while checking dependencies and timeouts.
* **Idempotent Dispatch**: Enforce execution token tracking to prevent duplicate transactions.

---

### 3. Architecture Vision
To build a highly reliable, stateful, and observable execution engine that guarantees business transaction consistency when interacting with unstable external railway partner networks. The engine ensures that traveler instructions are executed accurately, safely, and transparently.

---

### 4. Architecture Goals
* **Reliability**: Zero orphan bookings left uncompensated upon partial failures.
* **Consistency**: Strict transition validations preventing out-of-order execution.
* **Safety**: Prevent duplicate partner API calls for identical travel plan steps.
* **Auditability**: Secure, immutable audit traces for all step outcomes.

---

### 5. Architecture Principles
* **Loose Coupling**: Clean separation between plan formulation (6.3) and plan execution (6.4).
* **Isolation of Concerns**: Execution logic must not touch payment gateway processing or frontend layout systems directly.
* **Self-Healing Execution**: Step failures should trigger localized, configured retries or alternate paths before falling back to full reversals.
* **State Immutability**: Historical steps, once finalized (completed or failed), must not be modified or re-run within the same execution context.

---

### 6. Scope
* Structural definitions of the execution state model.
* Application services coordinating step dispatch and execution tracking.
* Fallback and retry policy execution contracts.
* Automated compensation and rollback coordination.
* Execution tracking event generation.

---

### 7. Out of Scope
* Network connection protocols, socket bindings, or HTTP client configurations.
* Database engine tuning, caching libraries, or connection pools.
* Human customer service ticketing dashboards.
* Auxiliary transport services (flight, bus, hotel booking execution).

---

### 8. Assumptions
* The input travel plan has cleared all validation specifications and policies.
* External railway networks return readable response payloads for status queries.
* The traveler context contains verified payment authorizations before execution is triggered.

---

### 9. Constraints
* **Stateless Formulation Reference**: Cannot alter the original travel plan steps once execution begins; adjustments must be managed through plan revisions or alternate steps.
* **Downstream Latency**: Must tolerate connection timeouts up to 60 seconds from partner systems.
* **Rate Limits**: Must limit concurrent booking dispatches to partners.

---

### 10. Quality Attributes

#### Reliability
p99 execution completion rate with automated recovery. All failed composite bookings must revert cleanly to a consistent state within 30 seconds of failure detection.

#### Security
Absolute confidentiality of traveler credentials. No logging of payment tokens or identity secrets in progress updates.

#### Observability
Full traceability of plan states. Support operators must be able to view the live execution graph, showing active, completed, or reversed nodes.

---

### 11. Architectural Drivers
* High volatility and latency spikes on Indian railway ticketing channels.
* Strict regulatory audits required by payment networks and railway operators.
* Requirement for non-blocking conversational turns while bookings execute in the background.

---

### 12. Guiding Principles
* **Fail Safely**: When in doubt, halt execution and revert rather than risk duplicate charges or orphan bookings.
* **Design for Recovery**: Anticipate network drops at every step boundary.
* **Maintain Traceability**: Maintain a correlation trace identifier through all external API invocations.

---

### 13. Risks
* **Unresolvable Partial State**: A ticket is successfully cancelled, but the partner refund system fails to acknowledge, leaving the customer billed without a booking.
* **Throttling Lockout**: Retrying too aggressively may result in platform-wide IP bans.
* **Concurrency Race Conditions**: Parallel steps modifying overlapping inventories simultaneously.

---

### 14. Trade-offs
* **Latency vs. Consistency**: We choose strict sequential consistency over extreme execution speed. Steps wait for confirmation rather than predicting success.
* **Audit Size vs. Storage**: We log highly detailed execution steps, accepting larger database storage requirements to ensure absolute trace visibility.

---

### 15. Success Criteria
* Zero financial discrepancies recorded from failed automated cancellations.
* 100% of execution processes publish traceable state updates.
* Successful technical validation of state transitions under simulated network failures.

---

## PART 2A — Domain Architecture

### 16. Business Capability Model

```
       [Travel Plan Execution Capability]
                       │
     ┌─────────────────┼──────────────────┐
     ▼                 ▼                  ▼
[Coordination]    [Compensation]     [Auditing]
  - Step Dispatch   - Rollback         - Trace Logs
  - Retries         - Cancellation     - Event Audits
```

---

### 17. Domain Analysis
The domain is focused on *state transition management under uncertainty*. A travel plan is modeled as a directed step chain. The execution domain consumes this plan and controls step transitions while managing failures, executing reversals, and publishing updates.

---

### 18. Ubiquitous Language
* **Execution Session**: The stateful lifecycle of executing a travel plan.
* **Command Dispatcher**: Concept coordinating the transition of steps to active status.
* **Compensation Command**: An action designed to reverse a previously completed step.
* **Orphan Status**: An invalid state where a subset of related steps is finalized without companion steps.
* **Execution Ledger**: Conceptual immutable list recording all step executions.

---

### 19. Bounded Context
The **Execution Context** is bounded strictly by the receipt of a validated travel plan and the delivery of a final execution result. It interacts with the *Intent Context* (for inputs), the *Planning Context* (for plan steps), and the *Infrastructure Context* (for external integration execution).

---

### 20. Context Map

```
[Planning Context] ──(Validated Plan)──► [Execution Context] ──(Adapter Contract)──► [Infrastructure Context]
                                                │
                                                └──(Events)──► [Observability Context]
```

---

### 21. Aggregate Strategy
The **Execution Session** is defined as the Aggregate Root. It encapsulates the session state, the execution steps history, and validation checks. No changes to execution progress can occur outside this aggregate boundary.

---

### 22. Aggregate Root Definition
* **Identifier**: Unique Execution Session ID.
* **State**: Current overall status (Initiated, Processing, Completed, Reverting, Reverted, Failed).
* **Associated Travel Plan ID**: Trace pointer to the original formulated plan.
* **Step Trackers**: Collections tracking the progress of each step.

---

### 23. Entity Definitions
* **Execution Step Tracker**: Tracks the lifecycle of a specific step (Pending, Dispatching, Succeeded, Retrying, Failed, Compensating, Reverted).
* **Compensation Step Tracker**: Tracks rollback actions associated with a completed execution step.

---

### 24. Value Object Definitions
* **Execution State Log**: Record of state transitions with millisecond timestamps.
* **Failure Context**: Details of connection timeouts, status codes, or partner messages.
* **Correlation Metadata**: User ID, trace ID, and device metadata.

---

### 25. Domain Services
* **Execution Evaluator**: Domain service assessing if execution can proceed to the next step based on prerequisites.
* **Rollback Planner**: Service constructing a compensation step list from a failed execution sequence.

---

### 26. Domain Policies
* **Lockout Window Verification Policy**: Check that the current departure window has not closed during execution delay.
* **Strict Reversal Sequence Policy**: Reversals must be executed in the exact reverse order of step completion.

---

### 27. Domain Events
* **ExecutionStarted**: Published when the session starts processing.
* **StepExecutionSucceeded**: Published when a single plan step completes.
* **StepExecutionFailed**: Published when a step fails after all retries are exhausted.
* **ReversalInitiated**: Published when compensation sequence begins.
* **ExecutionFinalized**: Published when the session reaches a terminal state (Completed or Reverted).

---

### 28. Business Invariants
* **Invariant A**: No step may execute until all its prerequisites have succeeded.
* **Invariant B**: A session cannot be marked Completed if any step has failed without compensation.
* **Invariant C**: Compensation steps must never run in parallel with active execution steps.

---

### 29. Specifications
* **ReadyToExecuteSpecification**: Checks if the session is in a valid state and payment captures are ready.
* **CompensationRequiredSpecification**: Evaluates if a failed session requires active rollback commands.

---

### 30. Repositories (Conceptual)
* **ExecutionSessionRepository**: Conceptual interface to persist and retrieve active execution session states.
* **AuditLedgerRepository**: Interface to record immutable event records.

---

### 31. Factories (Conceptual)
* **ExecutionSessionFactory**: Handles the instantiation of an Execution Session from a validated Structured Travel Plan, mapping steps to trackable entities.

---

### 32. Domain Responsibilities
* Maintain transactional integrity across all steps.
* Manage state changes safely.
* Isolate logical state checks from network protocols.

---

### 33. Lifecycle Model

```
[Draft] ──► [Initiated] ──► [Processing] ──┬──► [Completed]
                                          │
                                          └──► [Reverting] ──► [Reverted]
```

---

## PART 2B — Application Architecture

### 34. Application Services
* **ExecutionCoordinator**: The primary facade coordinating the orchestration flow.
* **CompensationOrchestrator**: Coordinates execution of rollback operations.
* **StateNotifier**: Handles formatting and dispatching progress notifications.

---

### 35. Use Case Catalogue
* **UC-PLAN-EXEC-01**: Start Plan Execution.
* **UC-PLAN-EXEC-02**: Process Step Confirmation.
* **UC-PLAN-EXEC-03**: Handle Step Timeout.
* **UC-PLAN-EXEC-04**: Execute Automated Rollback.
* **UC-PLAN-EXEC-05**: Force Manual Support Intervention.

---

### 36. Command Model
* **StartExecutionCommand**: Triggers a new execution session.
* **UpdateStepStatusCommand**: Records results from external adapters.
* **TriggerRollbackCommand**: Forces compensation workflows.

---

### 37. Query Model
* **GetExecutionStateQuery**: Returns the current status of all steps.
* **GetAuditLogQuery**: Retrieves execution history for debugging.

---

### 38. Execution Workflow
1. Receive StartExecutionCommand.
2. Load session via factory, set status to Initiated, save to repository, emit ExecutionStarted.
3. Fetch next runnable steps (no outstanding prerequisites).
4. Dispatch step commands to external adapters.
5. Await UpdateStepStatusCommand.
6. If success, verify invariants, and loop to step 3.
7. If failure, execute recovery strategy.

---

### 39. Orchestration Strategy
Use a stateful saga pattern. The coordinator tracks active steps in-memory or in state stores, evaluating prerequisite resolutions before triggering next tasks.

---

### 40. Execution Coordination Model

```
  [ExecutionCoordinator]
            │
            ├──► Check Prerequisites 
            ├──► Dispatch to Adapters
            └──► Handle Outcomes ──► Success ──► Continue
                                  └──► Failure ──► CompensationOrchestrator
```

---

### 41. Collaboration Model
The Coordinator coordinates actions between the Session Repository, the Step Trackers, the Audit Log, and the External Integration Gateways.

---

### 42. Interaction Boundaries
* **Inbound Boundary**: Validated travel plans from the Planning Context.
* **Outbound Boundary**: Abstract Adapter interfaces defining capabilities like searching, booking, and cancelling.

---

### 43. External Capability Contracts
Adapters must implement standard business contracts:
* `check_availability(train, date) -> Status`
* `book_seat(passenger, train, class) -> Confirmation`
* `cancel_seat(pnr) -> RefundAmount`

---

### 44. Failure Management Strategy
Categorize errors at the boundary:
* **Transient Error (e.g., Network drop)**: Trigger retry policy.
* **Fatal Error (e.g., Seat Sold Out)**: Stop execution, trigger compensation workflow.
* **System Failure (e.g., Adapter crashed)**: Pause execution, await operator review.

---

### 45. Recovery Strategy
* **Retry Policy**: Maximum 3 attempts with progressive delay.
* **Alternate Path**: If a preferred class is unavailable, check if the travel plan contains a configured fallback (e.g., alternative class or route).

---

### 46. Idempotency Strategy
Generate a unique execution token for each transaction. Downstream adapters must verify that this token has not been processed before executing booking actions.

---

### 47. Authorization Strategy
Verify traveler context signatures before executing booking commands. Steps requesting senior concessions must check age validations against profiles.

---

### 48. Validation Strategy
Check that the travel plan has not expired. Ensure that target departure times are at least 4 hours in the future before dispatching bookings.

---

### 49. State Transition Strategy
Only allow valid state changes. For example, a session cannot transition directly from Completed to Reverting without a verified step failure.

---

### 50. Result Aggregation Strategy
Compile step outcomes into a final execution report containing confirmation numbers, PNRs, and refund receipts.

---

## PART 2C — Enterprise Architecture

### 51. Security Architecture
* **Data Masking**: Passenger credentials must be masked in audit logs.
* **Access Control**: Only authorized application roles can query session repositories or trigger rollbacks.

---

### 52. Privacy Architecture
Passenger data must be stored in transient states. Once execution completes, state stores must clear sensitive details, keeping only masked receipts.

---

### 53. Compliance Architecture
All bookings must align with IRCTC concession guidelines and consumer protection cancellation rules. Refund values must match calculation metrics.

---

### 54. Observability Architecture
Emit standard trace spans for each step execution. Trace correlation IDs must be passed to downstream adapters.

---

### 55. Reliability Strategy
Persistent state stores are required. If the execution worker crashes, a supervisor process must reload active sessions and resume tracking.

---

### 56. Availability Strategy
Deploy active-passive coordinators across separate availability zones to prevent single-point failures.

---

### 57. Scalability Strategy
Partition execution sessions by traveler ID, allowing multiple engines to run concurrently.

---

### 58. Performance Strategy
Orchestration checks must complete in under 5ms, ensuring latency is driven strictly by external network calls.

---

### 59. Fault Tolerance Strategy
If external databases become unavailable, write state changes to local fallback files before retrying database updates.

---

### 60. Monitoring Strategy
Expose transaction success rates, average rollback durations, and active execution counts to system dashboards.

---

### 61. Audit Strategy
Record all event transitions in a log system, enabling root-cause analysis for failed bookings.

---

### 62. Extensibility Strategy
Add new execution adapters (e.g., hotel reservation adapters) by implementing the standard adapter interface without modifying the core coordinator.

---

### 63. Maintainability Strategy
Separate domain policies from application sagas, allowing developers to change retry rules without altering state transition logic.

---

### 64. Dependency Strategy
Apply dependency inversion: Core coordinator must only depend on abstract protocols.

---

### 65. Versioning Strategy
Version all execution state payloads, allowing older models to migrate to updated schemas during updates.

---

### 66. Backward Compatibility
Ensure that updates to execution contracts do not break active sessions currently processing bookings.

---

### 67. Architectural Decision Records (ADR)

#### ADR-M6.4-001: Stateful Saga Orchestration
* **Context**: Multi-leg bookings require transactional safety.
* **Decision**: Implement a stateful Saga coordinator rather than stateless chains.
* **Rationale**: Sagas track step completions and coordinate compensating transactions when failures occur.

#### ADR-M6.4-002: Idempotent Execution Tokens
* **Context**: Latency spikes cause users to submit booking requests twice.
* **Decision**: Generate execution tokens at start, validated by downstream adapters.
* **Rationale**: Eliminates double-booking and double-billing risk.

---

### 68. Risk Register

| Risk | Impact | Likelihood | Mitigation |
| :--- | :---: | :---: | :--- |
| Rollback fails | Critical | Low | Fallback to manual support queue |
| Rate-limit block | High | Medium | Implement queue spacing |

---

### 69. Technical Debt Strategy
Avoid custom retry code in adapters; consolidate all policy checks inside the central engine.

---

### 70. Evolution Roadmap
* **Milestone 6.4**: Core Execution Engine (Current).
* **Milestone 6.5**: Memory integration.
* **Milestone 6.6**: Multi-provider execution (Bus/Hotel).

---

### 71. Architecture Governance
Any modifications to the state model or execution rules require review by the Technical Governance Board.

---

### 72. Planning Readiness Assessment
This document satisfies all requirements of the Enterprise Planning Standard v3.1. It contains no technical frameworks, programming language code, or file layouts, making it ready for implementation transition.

---

### 73. Architecture Freeze Statement
The technical architecture for Milestone 6.4 (Execution Engine) is formally **FROZEN** and serves as the baseline for implementation.

STATUS:
✅ APPROVED FOR ARCHITECTURE FREEZE
