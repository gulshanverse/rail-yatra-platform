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
| 2026-07-21 | 3.1.0 | Redesigned structure compliant with Enterprise Planning Standard v3.1 Parts 2A and 2B. | ARB Board |

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

## 26. Application Service Architecture

### 1. PlanningCoordinator
- **Purpose**: Orchestrates the plan creation and verification workflow.
- **Business Responsibility**: Coordinates the steps needed to turn raw requests into validated travel plans.
- **Orchestration Responsibility**: Calls the formulator, passes the plan to the validator, and returns the final signed travel plan.
- **Inputs**: `IntentDescriptor` containing resolved slots.
- **Outputs**: Validated `Structured Travel Plan` DTO.
- **Collaborating Domains**: Planning domain, Governance domain.
- **Consumed Policies**: Lockout Policy, Identity Safety Policy.
- **Produced Outcomes**: Triggering execution workflows on validation success, or returning error maps on validation failure.
- **Ownership**: Planning Context.
- **Future Evolution**: Will evolve to coordinate multi-turn conversational updates.
- **Layer Justification**: Belongs to the Application Layer because it coordinates orchestration and delegates policy checks to the domain services, keeping domain concepts decoupled from execution boundaries.

### 2. ClarificationHandler
- **Purpose**: Handles plan generation when traveler inputs are insufficient.
- **Business Responsibility**: Resolves ambiguous travel inputs.
- **Orchestration Responsibility**: Maps missing slots and generates a step sequence to prompt the user.
- **Inputs**: Missing slot list and confidence metrics.
- **Outputs**: Clarification plan sequence.
- **Collaborating Domains**: Planning domain.
- **Consumed Policies**: Concession Validation Policy.
- **Produced Outcomes**: An interactive confirmation step for the traveler.
- **Ownership**: Planning Context.
- **Future Evolution**: Will support dynamic slot recovery across complex multi-turn dialogs.
- **Layer Justification**: Belongs to the Application Layer because it maps dialogue states and structures alternative workflows based on external interaction rules.

---

## 27. Use Case Architecture

### Use Case: Formulate Multi-Leg Travel Sequence
- **Business Goal**: Turn compound traveler requirements into a coordinated travel plan.
- **Trigger**: Traveler inputs a compound request.
- **Preconditions**: The intent descriptor is parsed and slots are extracted.
- **Primary Flow**:
  1. The coordinator ingests the intent descriptor.
  2. The sequencer checks step prerequisites and determines the logical execution path.
  3. The validator checks layovers, dates, and ticket rules.
  4. The validated plan is signed and marked as ready.
- **Alternate Flow**: If layovers are invalid, the sequencer inserts alternative search steps.
- **Failure Flow**: If the departure window is closed, the plan is rejected with validation warnings.
- **Post Conditions**: A validated travel plan is ready for execution.
- **Success Criteria**: The plan is sequenced without time conflicts or double-bookings.
- **Business Rules**: Connection layover must be $\ge 45\text{ minutes}$.
- **Dependencies**: Intent Understanding Context.

---

## 28. Command Responsibility Model

### Command: FormulateTravelPlan
- **Purpose**: Request the generation of a structured travel plan.
- **Business Intent**: Sequence and validate steps to achieve the traveler's goal.
- **Initiator**: Gateway API.
- **Owning Context**: Planning Context.
- **Validation Policies**: PII Integrity Policy.
- **Business Constraints**: Execution time must meet the system responsiveness budget.
- **Expected Outcome**: An immutable `Structured Travel Plan` aggregate root.
- **Collaboration**: Planning Context and Governance Context.

---

## 29. Query Responsibility Model

### Query: GetActivePlanStatus
- **Purpose**: Retrieve the current verification status of the traveler's plan.
- **Ownership**: Planning Context.
- **Business Meaning**: Checks if the plan is approved, rejected, or requires clarification.
- **Data Responsibility**: Tracks validation states and constraint reports.
- **Consistency Expectations**: Read-only projection matching the latest coordinator state.
- **Consumers**: Presentation layer and support teams.
- **Security Considerations**: Passenger ID must be validated before status is exposed.
- **Evolution**: Will support real-time updates as downstream steps execute.

---

## 30. Interaction Architecture

```
[Traveler] ──▶ [Gateway API] ──▶ [PlanningCoordinator] ──▶ [PlanValidator]
                                                                  │
                                      ┌───────────────────────────┴───────────────────────────┐
                                      ▼                                                       ▼
                          [Approved Business Functions]                            [Configuration Services]
```

- **Gateway and PlanningCoordinator**: The gateway sends the parsed intent descriptor to the coordinator.
- **PlanningCoordinator and PlanValidator**: The coordinator passes the generated steps to the validator to run constraint checks.
- **PlanValidator and Approved Functions**: The validator matches planned steps against secure, approved business functions to check compatibility.
- **Error Behavior**: If validation fails, the coordinator rejects the plan and returns a detailed report, blocking execution.

---

## 31. Integration Architecture

### Integration: Railway Ticketing Services (IRCTC)
- **Business Purpose**: Search seat availability, confirm ticket status, and process bookings.
- **Responsibilities**: Map platform plan steps to ticketing workflows.
- **Ownership**: Downstream Execution Context.
- **Failure Behavior**: If ticketing services fail, the executor triggers fallback planning steps (e.g., search alternative classes).
- **Business Constraints**: Bookings must comply with IRCTC quota limits and timing rules.
- **Evolution**: Will expand to integrate with flight and bus ticketing services.

---

## 32. AI Orchestration Architecture

- **AI Responsibilities**: Analyze compound intent segments and predict slot parameters.
- **Reasoning Responsibilities**: Evaluate alternative schedules and classify traveler intents.
- **Planning Responsibilities**: Select planning templates or suggest step sequences for complex requests.
- **Validation Responsibilities**: The AI output must pass through the deterministic domain validation layer, ensuring it conforms to business rules.
- **Memory Collaboration**: The engine reads conversation history to resolve relative dates or referential slots.
- **Safety Responsibilities**: Filter out policy violations and prompt injection inputs.
- **Governance**: AI-generated plans must comply with the approved business functions catalog.

---

## 33. Prompt Architecture

- **Prompt Categories**: Intent classification templates, slot extraction instructions, planning sequence templates.
- **Prompt Ownership**: Product and AI Teams.
- **Prompt Governance**: Changes to prompts must undergo safety review and validation testing.
- **Prompt Lifecycle**: Prompts are version-controlled and tested in staging environments before release.
- **Prompt Security**: Inputs are sanitized to prevent system prompts from being altered or bypassed.
- **Prompt Traceability**: Logging system captures which prompt version was used for each planning request.

---

## 34. Memory Architecture

- **Short-Term Memory**: Stores active travel plans and parameters during the active conversation turn.
- **Long-Term Memory**: Stores traveler preferences, frequent routes, and discount eligibility.
- **Conversation Memory**: Tracks conversational context across turns.
- **Memory Ownership**: Deferred to the Memory Context (Milestone 6.5).
- **Retention Philosophy**: Personal data is expired after a short inactivity window.
- **Privacy Considerations**: Memory data is encrypted and scrubbed of sensitive fields.

---

## 35. Tool Collaboration Architecture

- **Business Functions**: Core services like PNR checks, seat availability searches, and meal orders.
- **Business Services**: Expose internal capabilities to the planning engine.
- **Capability Collaboration**: Steps are sequenced based on dependencies (e.g., PNR status must be checked before a refund is calculated).
- **Invocation Responsibility**: Downstream execution layer calls services exactly as specified in the plan.
- **Validation Responsibility**: The validator checks all parameters before services are called.

---

## 36. Configuration Architecture

- **Business Configuration**: Manage operational parameters like booking fees, support contacts, and partner registries.
- **Policy Configuration**: Contains rules for connection windows, passenger age thresholds, and safety filters.
- **AI Configuration**: Manages model paths, confidence cutoffs, and feature flags.
- **Versioning**: Configurations are versioned and can be rolled back without modifying code.

---

## 37. Security Architecture

- **Trust Boundaries**: The Planning Engine operates within a secure environment behind the presentation gateway.
- **Identity Concepts**: The passenger ID is verified before any booking modifications are planned.
- **Authorization Philosophy**: Access controls ensure users can only plan modifications for their own bookings.
- **Threat Protection**: Parameter checks sanitize slots to prevent code injection.
- **Fraud Prevention**: Overlapping or duplicate plans for the same passenger are blocked.

---

## 38. Privacy Architecture

- **Privacy Principles**: Data collection is minimized, and passenger data is kept secure.
- **Consent Philosophy**: Travelers must opt-in before their travel history is stored.
- **Retention Philosophy**: Conversation history is expired and deleted after 30 days of inactivity.
- **Customer Rights**: Travelers can request deletion of their saved preferences at any time.

---

## 39. Compliance Architecture

- **Applicable Regulations**: Governed by the DPDP Act and IRCTC terms of service.
- **Responsible AI**: Decisions must be transparent, unbiased, and prioritize customer safety.
- **Audit Requirements**: Validation outcomes and rules checks must be recorded in structured logs for compliance review.

---

## 40. Observability Architecture

- **Business Observability**: Track composite booking conversion rates and planning completion.
- **Operational Observability**: Monitor execution success rates and error rates.
- **Architecture Observability**: Track execution time across the planning, validation, and routing stages.
- **Health Visibility**: Continuous monitoring of connection health to ticketing and validation services.

---

## 41. Reliability Strategy

- **Objectives**: Achieve high uptime for plan generation and validation.
- **Failure Philosophy**: Faults in external APIs must be isolated, allowing local rule checkers to proceed with fallback templates.
- **Graceful Degradation**: If model-based planning fails, the coordinator falls back to pre-defined heuristic templates.

---

## 42. Error Taxonomy

- **Validation Errors**: Caused by missing parameters or rule violations (e.g., layover under 45 minutes); handled by rejecting the plan.
- **Operational Errors**: Caused by database timeouts or system configuration issues.
- **Integration Errors**: Occur when external partners (e.g., IRCTC) are unreachable; handled by triggering alternative plan steps.
- **Security Errors**: Triggered by authorization failures or parameter validation alerts; handled by blocking the request immediately.

---

## 43. Failure Handling Strategy

- **Detection**: Check system outputs against schema validation rules.
- **Classification**: Categorize errors into validation, operational, or integration types.
- **Containment**: Failures in one step do not affect unrelated segments of the plan.
- **Recovery**: Fallback paths automatically redirect the workflow to safe options.

---

## 44. Performance Strategy

- **Goals**: Keep plan formulation and validation times low to ensure a responsive conversational experience.
- **Optimization**: Use pre-defined planning templates for common queries to bypass dynamic generation.
- **Capacity Planning**: Scale planning nodes dynamically during high-traffic holiday seasons.

---

## 45. Scalability Strategy

- **Stateless Design**: All planning components are stateless, enabling quick horizontal scaling under high workloads.
- **Operational Scaling**: Rules validation runs locally, preventing external network calls from slowing down the planning gate.

---

## 46. Extensibility Strategy

- **Service Registry**: New capabilities (e.g., cab bookings) can be registered as approved business functions without modifying core planning logic.
- **Policy Extensions**: New verification rules can be added to the validation loop independently.

---

## 47. Evolution Roadmap

- **Current Milestone (6.3)**: Decoupled plan generation and validation.
- **Next Milestone (6.4)**: Coordinated execution of plan sequences via specialist adapters.
- **Long-Term**: Fully autonomous planning agents and dynamic travel packages.

---

## 48. Architecture Decision Records (ADR)

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

## 49. Architecture Risk Register

| Risk Identifier | Business Description | Likelihood | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **RSK-PLN-01** | **Plan Manipulation**: Prompts designed to trigger unauthorized actions. | Low | High | Restrict step types to approved business functions. | Sec Lead |
| **RSK-PLN-02** | **Stale Constraints**: Validation rules do not align with updated railway policies. | Medium | High | Decouple validation rules from code and update them dynamically. | Ops Lead |

---

## 50. Dependency Analysis

- **Business Dependencies**: Governed by IRCTC booking windows and passenger travel rules.
- **Context Dependencies**: Planning Context depends on the output of the Intent Context.
- **Policy Dependencies**: Validation rules depend on the latest compliance policies.
- **Forbidden Dependencies**: The Planning Context must never call external database wrappers or ticketing APIs directly.
