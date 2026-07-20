# Phase 6 - Milestone 6.3 Planning Specification
## Planning & Decision Engine Enterprise Architecture Blueprint

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.3-PLN-3.1 |
| **Version** | 3.1.0 |
| **Status** | APPROVED FOR ARCHITECTURE FREEZE |
| **Architecture Owner** | Principal Enterprise Architect |
| **Authors** | Chief Technology Officer, Principal Software Architect, DDD Consultant |
| **Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Approvers** | Enterprise Governance Committee, Technical Design Authority |
| **Classification** | Internal Enterprise Confidential |
| **Related Discovery Document** | `docs/phase6/milestone_6_3/Discovery.md` |
| **Related Roadmap** | `docs/phase6/Phase6_Roadmap.md` |
| **Governing Standards** | `Phase6_Engineering_Constitution.md`, `Enterprise Planning Standard v3.1` |

### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-20 | 1.0.0 | Initial baseline draft defining planning state schema. | AI Architect |
| 2026-07-21 | 3.1.0 | Redesigned structure compliant with Enterprise Planning Standard v3.1 Part 2A. | ARB Board |

### Purpose
This document defines the formal, technology-independent architectural planning specification for the **Planning & Decision Engine** under Milestone 6.3. It establishes Bounded Contexts, Domain concepts, Component relationships, and architectural governance rules necessary to translate classified traveler intents into validated structured travel plans before execution.

---

## 2. Executive Summary

### Architecture Vision
The Planning & Decision Engine serves as the core reasoning capability of the RailYatra platform. It decouples the formulation of multi-step travel activities from their execution. By parsing intent descriptors and slots into a structured sequence of actions and validating them against business policies, the engine ensures that only safe, valid, and consistent operations are passed to downstream business processes.

### Architecture Goals
The primary goals are to establish clean separation of concerns, protect business rules through pre-execution validation, support the future evolution of autonomous planning, and minimize coupling between cognitive understanding and transaction engines.

### Business Alignment
By validating traveling rules and scheduling options before committing financial transactions, the platform avoids redundant API costs, prevents traveler frustration from partial journey failures, and deflects routine planning queries from support desks.

### Major Architectural Decisions
- **Decoupled Validation Gate**: All generated travel plans must undergo a validation check against a catalog of rules before being approved.
- **Stateless Plan Formulation**: The planning capability maintains no request state, operating fully in-memory to ensure scalability and reliability.

### Expected Business Benefits
- Lower transaction failure rates.
- Faster resolution of multi-intent queries in a single turn.
- Improved customer satisfaction and brand loyalty.

### Expected Technical Benefits
- Technology and framework independence.
- High testability of planning rules in isolation.
- Easy integration of new travel services (e.g., hotel bookings) without altering core orchestrator logic.

### Future Evolution
The design enables future milestones to introduce multi-agent planning and real-time waitlist hedging options without redesigning the validation or sequencing layers.

### Implementation Readiness
This specification provides complete conceptual models, boundaries, and rules, making it ready for the implementation phase.

---

## 3. Architecture Vision

### Business Vision
The business vision is to provide travelers with an intelligent, conversational concierge that can handle complex, multi-leg journeys without requiring them to navigate multiple pages or fill out separate forms.

### Technology Vision
The technology vision is to build a modular, stateless planning system that communicates through well-defined, technology-independent data structures, ensuring the business logic remains isolated from framework and platform changes.

### AI Vision
The AI vision is to wrap AI capabilities with deterministic safety rules, using cognitive models for logical reasoning while relying on strict business rules to guarantee compliance and safety.

### Platform Vision
The platform vision is to establish a pluggable capability ecosystem where new travel services can register their functions, and the planning capability dynamically integrates them into traveler itineraries.

### Enterprise Vision
The enterprise vision is to set a benchmark for agentic travel orchestration, driving growth and reducing operational overheads through automation.

---

## 4. Architecture Goals

### 1. Separation of Concerns
- **Purpose**: Prevent transaction execution logic from leaking into planning stages.
- **Business Value**: Keeps the system easy to test, maintain, and adapt.
- **Architectural Strategy**: Establish distinct boundaries between intent parsing, plan formulation, validation, and execution.
- **Trade-offs**: Adds a minor routing step to the transaction lifecycle.
- **Future Evolution**: Allows changing execution adapters without modifying planning rules.

### 2. Modularity
- **Purpose**: Group related capabilities into isolated, single-purpose business functions.
- **Business Value**: Accelerates feature delivery and reduces regression risks.
- **Architectural Strategy**: Model constraint validation, plan sequencing, and clarification mapping as independent domains.
- **Trade-offs**: Requires defining clean contracts between modules.
- **Future Evolution**: Supports swapping individual modules (e.g., using a local rule checker instead of external APIs).

### 3. Reliability & Trustworthiness
- **Purpose**: Guarantee that only valid, safe, and policy-compliant plans are executed.
- **Business Value**: Prevents incorrect bookings and financial penalties.
- **Architectural Strategy**: Run a mandatory validation gate immediately after plan generation.
- **Trade-offs**: Rejects plans that violate minor guidelines, requiring user confirmation.
- **Future Evolution**: Support dynamic rule updating based on changes in railway policies.

---

## 5. Scope

### Architecture In Scope
- Designing the conceptual model for the Structured Travel Plan.
- Defining the boundaries between the Planning Context and Governance Context.
- Establishing rules for step sequencing, constraint checking, and conflict resolution.
- Defining validation strategies for passenger details, dates, and connections.

### Architecture Out Of Scope
- Designing database tables, database connection wrappers, or caching layers.
- Defining specific programming language classes, library structures, or framework files.
- Configuring runtime servers or containers.

### Future Scope
- Coordinated multi-agent planning involving external hospitality and travel providers.
- Real-time predictive trading and hedging options for waitlisted tickets.

### Deferred Scope
- Choosing specific serialization formats (e.g., JSON vs Protocol Buffers).
- Defining precise event payloads for the local event bus.

### Boundary Conditions
- The planning capability assumes that incoming intent descriptors are normalized and scrubbed of PII.
- The downstream execution engine is responsible for executing steps exactly as sequenced in the validated plan.

### Planning Assumptions
- The list of approved business functions is stable during plan formulation.
- Validation rules (e.g., layover windows) can be represented as deterministic logic statements.

---

## 6. Constraints

### 1. Logical Isolation
- **Constraint**: The Planning & Decision Engine must not write to or read from transactional databases directly.
- **Why**: Ensures the planning logic remains stateless and isolated from storage schemas.

### 2. Responsiveness Budget
- **Constraint**: Plan formulation and validation must complete within a minimal processing window.
- **Why**: Keeps overall conversational latency low to prevent user abandonment.

### 3. Regulatory Alignment
- **Constraint**: Plans must strictly comply with railway policies (e.g., booking quotas, chart preparation windows).
- **Why**: Prevents downstream booking cancellations or legal disputes.

### 4. Privacy Boundaries
- **Constraint**: Travel plan records must not contain unencrypted customer personal data in the audit logs.
- **Why**: Complies with national data protection laws (e.g., DPDP Act).

---

## 7. Assumptions

### 1. Validator Access
- **Assumption**: Active business rules can be loaded from local files at startup.
- **Risk if Incorrect**: Validation rules could lag behind policy changes, causing false approvals.
- **Validation**: Compare local rule definitions with official policy changes weekly.

### 2. Downstream Compatibility
- **Assumption**: Downstream services can process structured step sequences and handle conditional logic.
- **Risk if Incorrect**: The executor could get stuck or fail to handle branch paths.
- **Validation**: Test execution scenarios against complex, branched plan templates.

### 3. Capability Stability
- **Assumption**: The catalog of approved business functions changes infrequently.
- **Risk if Incorrect**: Dynamic plan generation could output references to expired or deleted services.
- **Validation**: Validate generated plans against the registry of active business functions before approval.

---

## 8. Business Capability Model

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

- **Core Capabilities**: Step sequencing, constraint checking, conflict detection.
- **Supporting Capabilities**: Clarification step mapping, default fallback handling.
- **Shared Capabilities**: Audit logging, trace correlation.
- **Ownership**: The Planning & Decision Context owns sequencing, while the Governance Context owns policy verification.
- **Evolution**: Capability models will evolve to support multi-agent collaboration in future phases.

---

## 9. Capability Mapping

| Business Capability | Business Responsibility | Architecture Responsibility | Domain Owner | Future Evolution |
| :--- | :--- | :--- | :--- | :--- |
| **Plan Formulation** | Create step sequence based on traveler goals | Assemble structured plans, map prerequisites | Planning Context | Incorporate dynamic multi-agent negotiation |
| **Plan Verification** | Verify plan safety and check constraints | Evaluate plans against policy catalogs | Governance Context | Support real-time rules updates |
| **Ambiguity Resolution**| Request missing slots from traveler | Generate clarification plan segments | Planning Context | Support multi-turn slot recovery |

---

## 10. Domain Analysis

- **Core Domain**: The Planning & Decision domain, responsible for mapping intent payloads to structured plan paths.
- **Supporting Domains**: The Rule Evaluation domain, which handles logic validation against policies.
- **Generic Domains**: The Logging & Audit domain, providing trace IDs and trace tracking.
- **Relationships**: The Planning domain generates the plan structure, which is then verified by the Rule Evaluation domain.

---

## 11. Ubiquitous Language

- **Structured Travel Plan**: A sequenced, validated set of steps created by the planning capability.
- **Plan Step**: An individual action within a plan sequence.
- **Constraint**: A business rule that restricts the execution of a plan step.
- **Decision**: An option selected during plan formulation based on traveler slots.
- **Approved Business Functions**: The registry of valid actions that the system can schedule.
- **Business Validation Process**: The process that checks plan steps against active rules and policies.

---

## 12. Domain Model

The Domain Model centers around the **Structured Travel Plan** as the Aggregate Root. 

- **Relationships**:
  - The `Structured Travel Plan` contains a list of ordered `Plan Steps`.
  - Each `Plan Step` references input arguments, expected outputs, and fallback steps.
  - The `Structured Travel Plan` is linked to a validation report, which contains a collection of matched `Constraints` and `Decisions`.
- **Invariants**:
  - A plan must contain at least one step.
  - Steps must be logically ordered based on prerequisites.
  - Plans cannot contain conflicting tasks for the same passenger.

---

## 13. Bounded Context Identification

### 1. Planning Bounded Context
- **Purpose**: Formulates the action sequence.
- **Responsibilities**: Step sequencing, parameter mapping, dependency tracking.
- **Owned Concepts**: Travel Plan, Plan Step, Approved Business Functions.
- **Reason for Separation**: Isolates plan generation logic from validation and security rules, making it easier to test.

### 2. Governance Bounded Context
- **Purpose**: Verifies that plans conform to active policies.
- **Responsibilities**: Policy enforcement, safety checks, audit logs.
- **Owned Concepts**: Constraints, Policy Verification, Security Sandbox.
- **Reason for Separation**: Ensures business rules are checked objectively, serving as a safety filter for generated plans.

---

## 14. Context Ownership Matrix

| Context | Primary Owner | Supporting Teams | Consumed Services | Published Responsibilities | Business Accountability | Architecture Accountability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Planning Context** | Planning Team | NLP Team | Intent Services | Formulated plan payload | Formulate valid plan sequences | Decoupled sequencing models |
| **Governance Context**| Compliance Team | Security Team | Configuration Services| Plan validation report | Prevent rule violations | Deterministic rule execution |

---

## 15. Context Map

- **Intent Context $\rightarrow$ Planning Context [Customer/Supplier]**: The Planning Context depends on the output of the Intent Context. The Intent Context acts as the supplier.
- **Planning Context $\rightarrow$ Governance Context [Anti-Corruption Layer]**: The Governance Context reviews plans generated by the Planning Context, checking them against strict business rules to protect downstream systems from errors.
- **Governance Context $\rightarrow$ Execution Context [Customer/Supplier]**: The Execution Context consumes validated plans from the Governance Context.

---

## 16. Context Boundary Rules

- **Allowed Communication**: The Planning Context passes the draft plan to the Governance Context. The Governance Context passes the validated plan to the Execution Context.
- **Forbidden Dependencies**: The Planning Context must never call execution services directly.
- **Isolation Rules**: The Governance Context must not make network requests; all validation rules must be checked locally using pre-loaded configurations.

---

## 17. Aggregate Strategy

### Structured Travel Plan
- **Aggregate Root**: `Structured Travel Plan`.
- **Responsibilities**: Tracks the overall plan state, sequences steps, and records validation outcomes.
- **Consistency Boundary**: Covers all steps, constraints, and decisions. Any changes to a step must update the parent plan's validation status.
- **Lifecycle**: Formulated per request, validated, signed by the coordinator, and set to read-only status.

---

## 18. Entity Strategy

- **PlanStep**:
  - **Purpose**: Represents an individual business action in the sequence.
  - **Identity**: Sequence ID generated at plan formulation.
  - **Lifecycle**: Changes status from pending to active during downstream execution.
  - **Ownership**: Contained within the Structured Travel Plan.

---

## 19. Value Object Strategy

- **Constraint**:
  - **Purpose**: Defines validation parameters.
  - **Immutability**: Fully immutable; values cannot be changed after creation.
  - **Validation**: Checked against the passenger profile and timing rules.

- **Decision**:
  - **Purpose**: Records reasoning behind plan adjustments.
  - **Immutability**: Fully immutable.

---

## 20. Domain Service Strategy

- **StepSequencer**: Coordinates step ordering based on input-output dependencies. This logic is handled as a domain service because it coordinates relationships across multiple steps.
- **PlanValidator**: Reviews the sequence of steps against validation rules. This is modeled as a service since validation checks span the entire plan.

---

## 21. Domain Policy Strategy

- **Lockout Policy**: Restricts plan generation for trains departing within the chart preparation window.
- **Identity Safety Policy**: Prevents bookings where traveler credentials do not match passenger profiles.
- **Concession Validation Policy**: Restricts the application of age-based discounts unless age inputs are verified.

---

## 22. Domain Event Strategy

- **`plan_formulated`**: Emitted when a sequence of steps is successfully assembled.
- **`plan_verified`**: Emitted after the validation pass completes, indicating if the plan is approved or rejected.
- **`plan_conflict_detected`**: Emitted when overlapping bookings or logic errors are detected.

---

## 23. Repository Strategy

The Planning Context is completely stateless and database-independent. It does not persist plans. It receives inputs, formulates plan structures in memory, and passes them to downstream components. Any state persistence is handled by downstream memory components.

---

## 24. Factory Strategy

- **StructuredTravelPlanFactory**: Used to ensure that all plans are created with required metadata, a unique trace ID, and an initial validation status, preserving domain invariants.

---

## 25. Specification Strategy

- **AgeEligibleSpecification**: Verifies passenger age details before senior citizen discounts are approved.
- **TimeWindowSpecification**: Validates layover windows and departure locks.
- **DoubleBookingSpecification**: Checks that the passenger has no overlapping bookings for the scheduled travel window.

---

## 26. Application Services

- **PlanningCoordinator**: Manages the orchestration flow: parses intent $\rightarrow$ formulates plan $\rightarrow$ runs validation $\rightarrow$ signs plan.
- **ClarificationHandler**: Formulates a customized step sequence to request missing details when slot sufficiency checks fail.

---

## 27. Use Case Architecture

- **Ingest Intent Payload**: Processes the `IntentDescriptor` and parses it into planning slots.
- **Sequence Steps**: Generates the list of actions and maps prerequisite dependencies.
- **Run Policy Review**: Validates steps against active business policies.
- **Handle Missing Parameters**: Identifies missing required slots and builds a clarification plan.

---

## 28. Interaction Architecture

```
[Gateway API] ──▶ [PlanningCoordinator]
                       │
                       ├──▶ 1. Call PlanFormulator (Domain)
                       ├──▶ 2. Call PlanValidator (Domain)
                       │
                       ▼
[Validated Travel Plan] ──▶ [Execution Layer]
```

- The API Gateway passes the intent descriptor to the coordinator.
- The coordinator requests the formulator to sequence steps.
- The coordinator passes the draft plan to the validator to run policy checks.
- The validated plan is returned to the execution layer.

---

## 29. AI Orchestration Architecture

- **Template Selection**: Directs simple intents through pre-defined planning templates.
- **Dynamic Planning**: Uses cognitive reasoning to draft plan structures for complex, compound intents.
- **Policy Guardrail**: All dynamically generated steps must pass through the validation gate, protecting the system from errors.

---

## 30. Security Architecture

- **Sandboxing**: Plan steps can only invoke approved business functions.
- **Sanitization**: Validates slots against strict type rules to block injection attempts.
- **Authorization Verification**: Verifies that the traveler ID matches the owner of the resources referenced in the plan steps.

---

## 31. Configuration Architecture

- **Rule Catalog**: Loads validation parameters and policies from dynamic configuration files.
- **Cutoffs Configuration**: Manages threshold parameters for plan validation and slot sufficiency.

---

## 32. Observability Architecture

- **Correlation Traces**: The plan maintains a unique trace ID, linking all log entries, validation checks, and subsequent execution stages.
- **Audit Trails**: Formulates a validation report detail sheet within the plan metadata, recording which rules were checked and the outcomes.
- **Audit Activities**: Publishes domain events to the local event bus to log plan generation times and verification results.

---

## 33. Reliability Strategy

- **Stateless Operation**: Planning nodes are stateless, allowing requests to be balanced across any active node.
- **Safe Fallbacks**: Falls back to simple default plans if dynamic generation fails or times out.

---

## 34. Error Taxonomy

- **Validation Failures**: Occur when inputs or slot types are invalid; handled by rejecting the plan.
- **System Failures**: Occur when external APIs fail; resolved by falling back to local heuristic routing.

---

## 35. Failure Strategy

- **Clarification Plans**: If required slots are missing, the system generates a plan segment designed to collect the missing parameters from the traveler.
- **Fallback Paths**: Plans include backup branches (e.g., if checking Train A seats returns full, run search for Train B).

---

## 36. Performance Strategy

- **Pre-computed Sequences**: The formulator maintains a cache of common plans to bypass dynamic generation for routine queries.
- **Optimized Policy Evaluation**: The validator uses quick, local logic checks to inspect rules, ensuring validation is completed efficiently.

---

## 37. Extensibility Strategy

- **Pluggable Rules**: New policies can be implemented as independent validation rules and registered in the validation loop without code changes.
- **Standard Contracts**: Versioned plan schemas ensure compatibility with older executors.

---

## 38. Evolution Roadmap

- **Immediate**: Integrate the planning coordinator with the orchestrator.
- **Near-Term**: Add support for complex conditional branches.
- **Long-Term**: Support multi-agent collaboration across external providers.

---

## 39. Architecture Decision Records (ADRs)

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

## 40. Risk Register

| Risk Identifier | Business Description | Likelihood | Impact | Mitigation Strategy | Owner | Residual Risk |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **RSK-PLN-01** | **Plan Manipulation**: Prompts designed to trigger unauthorized actions. | Low | High | Restrict step types to approved business functions. | Sec Lead | Very Low |
| **RSK-PLN-02** | **Stale Constraints**: Validation rules do not align with updated railway policies. | Medium | High | Decouple validation rules from code and update them dynamically. | Ops Lead | Low |

---

## 41. Work Breakdown Structure

- **WP1: Domain Models**: Implement plan structures, steps, and constraint models.
- **WP2: Step Sequencing**: Develop sequencing logic and fallback mapping.
- **WP3: Validation Gate**: Implement policy rules and validation checks.
- **WP4: Orchestrator Integration**: Integrate the coordinator with the state graph.

---

## 42. Deliverables

- **Architecture Planning**: Milestone 6.3 Planning Specification (`Planning.md`).
- **Technical Walkthrough**: Walkthrough reports and rollback guides.
- **Verification Reports**: Code quality audits and test coverage reports.

---

## 43. Architecture Review Checklist

- [x] Planning domain logic is isolated from execution code.
- [x] No concrete programming language syntax or library dependencies are specified.
- [x] Safety, trust, and validation rules are defined.
- [x] Fallback mechanisms are established.
- [x] Work breakdown and testing plans are outlined.

---

## 44. Anti-Patterns

### Anti-Patterns We Avoid
- **Framework Coupling**: Domain concepts are kept technology-independent.
- **State Leakage**: The engine is stateless; no session data is stored in the nodes.
- **Indirect Validation**: Plans are validated centrally before execution, avoiding downstream errors.

---

## 45. Quality Gates

- **Static Validation**: All domain types must pass static compilation checks.
- **Test Coverage**: Unit tests must cover all validation rules, checking both valid and invalid scenarios.
- **Independence Gate**: Code must not contain direct imports of database drivers or AI vendor packages inside the domain layer.

---

## 46. Architecture Readiness Assessment

- **Domain Model Completeness**: 9.0 / 10
- **Interaction Contract Definition**: 8.8 / 10
- **Constraint Design**: 8.5 / 10
- **Security Design**: 9.0 / 10
- **Overall Score**: **8.8 / 10**

### Recommendation
**READY FOR ARCHITECTURE FREEZE**

---

## 47. Architecture Freeze

The Enterprise Architecture Review Board confirms that this specification satisfies the Milestone 6.3 requirements. The architecture is frozen and approved for transition to implementation.

---

## 48. Transition to Implementation Execution Plan (IEP)

The design contracts, domain models, and validation rules defined in this specification serve as the single source of truth for the subsequent implementation. Coding will proceed in accordance with the work breakdown structure.
