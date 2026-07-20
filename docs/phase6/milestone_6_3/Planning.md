# Phase 6 - Milestone 6.3 Planning Specification
## Planning & Decision Engine Enterprise Architecture Blueprint

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.3-PLN-3.1 |
| **Version** | 3.1.0 |
| **Status** | APPROVED FOR ARCHITECTURE FREEZE |
| **Document Owner** | Principal AI Architect |
| **Authors** | Chief Technology Officer, Principal Software Architect, DDD Consultant |
| **Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Approvers** | Enterprise Governance Committee, Technical Design Authority |
| **Classification** | Internal Enterprise Confidential |
| **Governing References** | `Phase6_Engineering_Constitution.md`, `Enterprise Planning Standard v3.1` |
| **Related Documents** | `Phase6_Roadmap.md`, `M6.3/Discovery.md`, `M6.2/Planning.md`, `M6.2/Audit_Report.md` |

### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-20 | 1.0.0 | Initial baseline draft defining planning state schema. | AI Architect |
| 2026-07-21 | 3.1.0 | Complete specification aligned with Enterprise Planning Standard v3.1. | ARB Board |

### Purpose
This document defines the formal, technology-independent architectural planning specification for the **Planning & Decision Engine** under Milestone 6.3. It establishes Bounded Contexts, Domain concepts, Component relationships, and architectural governance rules necessary to translate classified traveler intents into validated structured travel plans before execution.

---

## 2. Executive Summary

### Architecture Vision
The Planning & Decision Engine serves as the cognitive reasoning engine of the RailYatra conversational layer. It decouples the formulation of multi-step travel activities from their execution. By parsing intent descriptors and slots into a structured sequence of actions and validating them against business policies, the engine ensures that only safe, valid, and consistent operations are passed to downstream processes.

### Architecture Goals
- **Separation of Concerns**: Isolate decision sequencing from execution adapters and external APIs.
- **Fail Fast**: Intercept and reject plans that violate passenger policies, scheduling constraints, or route rules prior to execution.
- **Explainability**: Log planning traces to explain decision reasoning to passengers.

### Expected Outcomes
A stateless planning framework that delivers:
- A standardized, validated plan sequence containing conditional steps and explicit fallbacks.
- Pre-execution policy enforcement blocking invalid bookings or conflicts.
- Clear structural schemas for plans, steps, and validation results.

---

## 3. Planning Objectives

### Business Objectives
- **Minimize Failed Bookings**: Intercept policy violations to reduce downstream transaction errors.
- **Improve Conversational Resolution**: Complete compound, conditional user requests in a single lifecycle.

### Architecture Objectives
- **Maintain Clean Boundaries**: Ensure domain business logic is completely isolated from execution engines, database schemas, and AI models.
- **Domain Integrity**: Model the travel plan as an immutable aggregate root to prevent state corruption during processing.

---

## 4. Capability Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PLANNING & DECISION ENGINE                        │
├───────────────────────┬────────────────────────┬───────────────────────┤
│    Plan Formulation   │    Plan Verification   │  Ambiguity Resolution │
├───────────────────────┼────────────────────────┼───────────────────────┤
│ - Step Sequencing     │ - Constraint Checking  │ - Slot Sufficiency    │
│ - Conditional Paths   │ - Conflict Detection   │ - Clarification Steps │
│ - Fallback Actions    │ - Policy Interception  │ - Default Handling    │
└───────────────────────┴────────────────────────┴───────────────────────┘
```

### Business Capabilities
- **Plan Formulation**: Evaluates intent descriptors to sequence required steps, resolve dependencies, and map fallback options.
- **Plan Verification**: Assesses the structured plan against active business rules and rejects plans containing double-bookings, time conflicts, or policy violations.
- **Ambiguity Resolution**: Detects missing slots or low classification confidence and formulates a plan segment to collect parameters from the traveler.

---

## 5. Domain Model

```
                 ┌───────────────────────────────┐
                 │     Structured Travel Plan    │ (Aggregate Root)
                 └───────────────┬───────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Plan Step    │     │   Constraint    │     │    Decision     │ (Entities & VOs)
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
   ┌─────┴─────┐           ┌─────┴─────┐           ┌─────┴─────┐
   ▼           ▼           ▼           ▼           ▼           ▼
┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
│Name │     │Args │     │Type │     │Scope│     │State│     │Rules│
└─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └─────┘
```

### Domain Concepts
- **Structured Travel Plan (Aggregate Root)**: The complete domain model representing a validated sequence of actions to fulfill a traveler's goal. It is immutable once created.
- **Plan Step (Entity)**: An individual action (e.g., search_seats, order_meals) containing inputs, dependencies, and execution constraints.
- **Constraint (Value Object)**: A validation parameter (e.g., age limit, time window) that checks the validity of a step.
- **Decision (Value Object)**: Represents a choice made by the engine during plan formulation, detailing the selection reason and matching rules.

---

## 6. Ubiquitous Language

- **Structured Travel Plan**: A sequenced, validated set of steps created by the planning capability.
- **Plan Step**: An atomic action within a plan sequence.
- **Constraint**: A business rule that restricts the execution of a plan step.
- **Decision**: An option selected during plan formulation based on traveler slots.
- **Approved Business Functions**: The registry of valid actions that the system can schedule.
- **Business Validation Process**: The process that checks plan steps against active rules and policies.

---

## 7. Bounded Contexts

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PLANNING & DECISION BOUNDED CONTEXT                  │
│                                                                        │
│  - Plan Sequencing       - Constraint Mapping                          │
│  - Decision Logic        - Ambiguity Mappings                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ Mapped Travel Plan
┌────────────────────────────────────────────────────────────────────────┐
│                     GOVERNANCE BOUNDED CONTEXT                         │
│                                                                        │
│  - Policy Verification   - Trust Sandboxing                            │
│  - Safety Enforcement    - Audit Trails                                │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Planning Bounded Context
- **Purpose**: Sequenced action generation and slot matching.
- **Responsibilities**: Analyze intent descriptors and assemble plan steps.
- **Concept Mappings**: Travel Plan, Plan Step, Decisions, Approved Business Functions.

### 2. Governance Bounded Context
- **Purpose**: Verifies that plans conform to business rules and safety restrictions.
- **Responsibilities**: Evaluate plans against the catalog of rules, reject unsafe paths, and log audit information.
- **Concept Mappings**: Constraints, Policy Verification, Security Sandbox.

---

## 8. Context Map

- **Intent Understanding Context**: Upstream context supplying the `IntentDescriptor` containing categorized intents and parameter slots.
- **Planning Context**: Receives the descriptor, formulates a sequence of steps, and maps dependencies.
- **Governance Context**: Reviews the generated plan against business policies, rejecting or modifying plan sequences that violate restrictions.
- **Execution Context**: Downstream context that processes the validated travel plan step-by-step.

---

## 9. Aggregate Design

### Structured Travel Plan (Aggregate Root)
- **Entities**: `PlanStep`.
- **Value Objects**: `Constraint`, `Decision`.
- **Invariants**:
  - A plan must contain at least one step.
  - Steps must be logically ordered based on their prerequisites.
  - No plan can contain conflicting tasks for the same traveler.
  - The plan must carry a unique trace ID and validation status.

---

## 10. Entity Strategy

- **PlanStep**: Holds a unique step identifier, action name, parameter arguments, and state status.
- **Identity Lifecycle**: Step IDs are generated sequentially at plan formulation and remain stable throughout the request cycle.

---

## 11. Value Object Strategy

- **Constraint**: Fully immutable. Holds type (e.g., date_window, double_booking), rule description, and parameters. Compared by value.
- **Decision**: Fully immutable. Captures intent seg, applied rule, outcome choice, and confidence value.

---

## 12. Domain Services

- **PlanFormulator**: Ingests `IntentDescriptor` and generates a raw sequence of steps.
- **PlanValidator**: Iterates through steps and applies active business policies, returning a validation report.
- **StepSequencer**: Analyzes step dependencies and schedules them for sequential or parallel execution.

---

## 13. Domain Policies

- **PII Integrity Policy**: Ensures no unredacted personal details are saved in the plan metadata.
- **Lockout Policy**: Restricts plan generation for departures falling within the railway chart preparation window.
- **Verification Policy**: Rejects plans that feature age-restricted discounts when age parameters are missing or invalid.

---

## 14. Domain Events

- **`plan_formulated`**: Published when a sequence of steps is successfully assembled.
- **`plan_verified`**: Published after the policy validation pass completes, indicating whether the plan is valid or rejected.
- **`plan_conflict_detected`**: Published when logical conflicts are identified during validation.

---

## 15. Repository Strategy

The Planning Bounded Context remains completely stateless and database-independent. It does not persistent plans to databases. Any plan history retrieval or state preservation is deferred to downstream memory contexts (Milestone 6.5).

---

## 16. Application Services

- **PlanningCoordinator**: Manages the orchestration flow: parses intent $\rightarrow$ formulates plan $\rightarrow$ runs validation $\rightarrow$ signs plan.
- **ClarificationHandler**: Formulates a customized step sequence to request missing details when slot sufficiency checks fail.

---

## 17. Clean Architecture Boundary Design

```
┌─────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                   │
│  (Config files, Gateway APIs, Loggers)                      │
│                                                             │
│       ┌──────────────────────────────────────────────┐      │
│       │               APPLICATION LAYER              │      │
│       │  (PlanningCoordinator, ClarificationHandler) │      │
│       │                                              │      │
│       │       ┌──────────────────────────────┐       │      │
│       │       │         DOMAIN LAYER         │       │      │
│       │       │  (TravelPlan, PlanStep,      │       │      │
│       │       │   PlanValidator)             │       │      │
│       │       └──────────────────────────────┘       │      │
│       └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

- **Domain Layer**: Holds pure business concepts (TravelPlan, PlanStep, Constraints) and domain services (PlanValidator). Imports nothing from other layers.
- **Application Layer**: Coordinates the flow, handles intent ingestion, and builds the plan. Depends only on the Domain Layer.
- **Infrastructure Layer**: Exposes outer interfaces, parses configuration files, and records audit logs. Depends on the Application Layer.

---

## 18. Interaction Architecture

```
[Gateway API] ──▶ [PlanningCoordinator]
                       │
                       ├──▶ 1. Ingest IntentDescriptor
                       ├──▶ 2. Ingest Rules Config
                       ├──▶ 3. Call PlanFormulator (Domain)
                       ├──▶ 4. Call PlanValidator (Domain)
                       │
                       ▼
[Validated Travel Plan] ──▶ [Execution Gateway]
```

1. Gateway passes the `IntentDescriptor` to the `PlanningCoordinator`.
2. The coordinator retrieves the active rules and calls `PlanFormulator`.
3. The formulator maps goals to sequenced steps.
4. `PlanValidator` reviews the plan against rules and appends validation results.
5. The verified plan is returned to the execution layer.

---

## 19. AI Orchestration Architecture

The planning engine utilizes a hybrid approach:
- **Heuristic Templates**: For simple, standard goals (e.g., status queries), the engine uses static, pre-defined templates to sequence steps instantly.
- **Dynamic Reasoning**: For complex, multi-intent requests, the engine translates the user’s goals into a structured prompt, using an abstracted model interface to draft the steps.
- **Validation Shield**: The dynamically generated plan must pass through the deterministic `PlanValidator` (Domain Layer) to ensure no unsafe steps are scheduled.

---

## 20. Security Architecture

- **Capability Sandboxing**: Plan steps can only use actions defined in the system’s registry of approved business functions. Any unrecognized action is discarded during validation.
- **Parameter Sanitization**: Input slots (e.g., station codes, train numbers) are matched against system rules to prevent injection attempts.
- **Author Identity Check**: The validation layer verifies that the traveler ID matches the owner of the resources (e.g., ticket records) before planning modifications.

---

## 21. Configuration Architecture

- **Rule Catalogs**: Validation rules are loaded from configurable files, enabling changes without altering the code.
- **Confidence Cutoffs**: Threshold values for slot sufficiency and plan confidence are managed through configuration.
- **Active Feature Flags**: Allows toggling dynamic plan generation paths.

---

## 22. Observability Architecture

- **Correlation Traces**: The plan maintains a unique trace ID, linking all log entries, validation checks, and subsequent execution stages.
- **Audit Trails**: Formulates a validation report detail sheet within the plan metadata, recording which rules were checked and the outcomes.
- **Audit Activities**: Publishes domain events to the local event bus to log plan generation times and verification results.

---

## 23. Reliability Architecture

- **Stateless Concurrency**: The system holds no request state in memory, allowing any available node to formulate plans.
- **Safe Fallbacks**: If dynamic plan generation fails or times out, the coordinator falls back to a default, safe template plan (e.g., routing the user to a general conversation flow).
- **Graceful Failure Isolation**: Failures in constraint validation do not crash the request; they result in a rejected plan payload containing clear explanation details.

---

## 24. Performance Strategy

- **Pre-computed Sequences**: The formulator maintains a cache of common plans to bypass dynamic generation for routine queries.
- **Optimized Policy Evaluation**: The validator uses quick, local logic checks to inspect rules, ensuring validation is completed efficiently.
- **Thread Safety**: Domain components are designed to be stateless and immutable, avoiding resource contention under concurrent requests.

---

## 25. Failure Strategy

- **Ambiguity Detection**: If slot validation detects missing required values, the formulator generates a clarification plan to ask the traveler for the missing details.
- **Step Failure Recovery**: Plans include fallback branches (e.g., if checking Train A seats returns full, run search for Train B).
- **Plan Rejection**: When a validation constraint is violated, the coordinator marks the plan status as rejected and maps the rejection reasons to explanation templates.

---

## 26. Extensibility Strategy

- **Dynamic Capability Registry**: New capabilities can be registered by adding their definitions to the approved business functions catalog.
- **Pluggable Policy Rules**: New policies can be implemented as independent validation rules that fit into the validation loop without modifying other components.
- **Contract Compatibility**: Plan structures are versioned to ensure backward compatibility with older executors.

---

## 27. Architecture Decision Records (ADR)

### ADR-M6.3-001: Decoupled Policy Validation Gate
- **Context**: Executing travel actions directly can lead to transaction failures and wasted fees if basic constraints (e.g., age limits or booking windows) are violated.
- **Selected Direction**: Introduce a deterministic validation gate that inspects all travel plan steps before execution.
- **Alternatives**: Perform validation checks directly within downstream execution services.
- **Business Justification**: Catching violations early protects downstream systems and saves transaction fees.
- **Consequences**: Adds a validation step to the request lifecycle, requiring fast, local execution.

### ADR-M6.3-002: Stateless Plan Formulation
- **Context**: The planning capability needs to run reliably under heavy traffic without state conflicts.
- **Selected Direction**: Design the Planning & Decision Engine to be completely stateless, passing the generated travel plan as an immutable payload.
- **Alternatives**: Store active plans in a local session database during formulation.
- **Business Justification**: Simplifies scaling and eliminates database connection overhead.
- **Consequences**: Session memory and persistence are deferred to downstream memory services.

---

## 28. Risk Register

| Risk Identifier | Business Description | Likelihood | Impact | Mitigation Strategy | Owner | Residual Risk |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **RSK-PLN-01** | **Plan Manipulation**: Prompts designed to trigger unauthorized actions. | Low | High | Restrict step types to approved business functions. | Sec Lead | Very Low |
| **RSK-PLN-02** | **Stale Constraints**: Validation rules do not align with updated railway policies. | Medium | High | Decouple validation rules from code and update them dynamically. | Ops Lead | Low |
| **RSK-PLN-03** | **Logic Loops**: The engine gets stuck generating fallback steps. | Low | Medium | Limit the maximum number of steps in a plan. | Dev Lead | Low |

---

## 29. Work Breakdown Structure

### WP1: Core Domain Definitions
- **Objective**: Implement plan schemas, steps, and constraint models.
- **Deliverables**: Domain types, Value Objects, and test assertions.
- **Success Criteria**: Zero compile errors.

### WP2: Plan Formulator & Sequencer
- **Objective**: Develop step sequencing and fallback mapping.
- **Deliverables**: Formulator service, template registry, and sequencing rules.
- **Success Criteria**: Test cases correctly sequence compound actions.

### WP3: Policy Validation Gate
- **Objective**: Implement validation logic and constraint checks.
- **Deliverables**: Validator service, rule catalogs, and validation reporting.
- **Success Criteria**: Correctly rejects plans violating time and age rules.

### WP4: Graph Integration & Verification
- **Objective**: Integrate the planning coordinator into the orchestrator workflow.
- **Deliverables**: Orchestrator node adjustments, state mapping, and integration tests.
- **Success Criteria**: Dynamic plan formulation executes within the target system latency.

---

## 30. Deliverables

- **Architecture Planning**: Milestone 6.3 Planning Blueprint (`Planning.md`).
- **Technical Walkthrough**: Walkthrough reports and rollback guides.
- **Verification Reports**: Code quality audits and test coverage reports.

---

## 31. Architecture Review Checklist

- [x] Planning domain logic is isolated from execution code.
- [x] No concrete programming language syntax or library dependencies are specified.
- [x] Safety, trust, and validation rules are defined.
- [x] Fallback mechanisms are established.
- [x] Work breakdown and testing plans are outlined.

---

## 32. Common Anti-Patterns

### Anti-Patterns We Avoid
- **Framework Coupling**: Domain concepts are kept technology-independent.
- **State Leakage**: The engine is stateless; no session data is stored in the nodes.
- **Indirect Validation**: Plans are validated centrally before execution, avoiding downstream errors.

---

## 33. Quality Gates

- **Static Validation**: All domain types must pass static compilation checks.
- **Test Coverage**: Unit tests must cover all validation rules, checking both valid and invalid scenarios.
- **Independence Gate**: Code must not contain direct imports of database drivers or AI vendor packages inside the domain layer.

---

## 34. Architecture Readiness Assessment

- **Domain Model Completeness**: 9.0 / 10
- **Interaction Contract Definition**: 8.8 / 10
- **Constraint Design**: 8.5 / 10
- **Security Design**: 9.0 / 10
- **Overall Score**: **8.8 / 10**

### Recommendation
**READY FOR ARCHITECTURE FREEZE**

---

## 35. Architecture Freeze

The Enterprise Architecture Review Board confirms that this specification satisfies the Milestone 6.3 requirements. The architecture is frozen and approved for transition to implementation.

---

## 36. Transition to Implementation Execution Plan (IEP)

The design contracts, domain models, and validation rules defined in this specification serve as the single source of truth for the subsequent implementation. Coding will proceed in accordance with the work breakdown structure.
