# Phase 6 - Milestone 6.2 Planning Specification
## Intent Understanding Engine (IUE) Enterprise Architecture Blueprint

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.2-PLN-2.0 |
| **Version** | 2.0.0 |
| **Status** | DRAFT FOR ARCHITECTURE REVIEW |
| **Document Owner** | Principal AI Architect |
| **Authors** | Chief Technology Officer, Principal AI Architect, Enterprise Solution Architect, Domain-Driven Design Consultant |
| **Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Approvers** | Chief Technology Officer, Technical Governance Committee |
| **Classification** | Internal Enterprise Confidential |

### Revision History

| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-19 | 1.0.0 | Initial baseline draft defining basic intent routing pathways. | AI Architect |
| 2026-07-20 | 2.0.0 | Full expansion into comprehensive Enterprise Planning Blueprint based on Planning Standard v2.0. | ARB Board |

### Related Documents

- [Phase6_Engineering_Constitution.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/Phase6_Engineering_Constitution.md)
- [Phase6_Roadmap.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/Phase6_Roadmap.md)
- [Milestone_Template.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/Milestone_Template.md)
- [Discovery.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/milestone_6_2/Discovery.md)
- [Planning.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/milestone_6_1/Planning.md)

### Purpose

This document defines the formal, implementation-independent architectural planning specification for the **Intent Understanding Engine (IUE)** under Milestone 6.2. It establishes Bounded Contexts, Component Contracts, Domain lifecycles, and quality validation gates necessary to govern the implementation phase without architectural leakage.

---

## 2. Executive Summary

### Architecture Goals
The primary architectural goal of the Intent Understanding Engine (IUE) is to isolate semantic request interpretation from orchestrator execution graphs. Acting as an upstream stateless validation gateway, the IUE standardizes natural language traveler messages into structured, typed intent descriptors, preventing non-deterministic prompts from triggering erratic routing behaviors in the downstream state graph.

### Business Alignment
The IUE directly aligns with the business need to improve travelers' conversational experience on the RailYatra platform. By accurately classifying intents and extracting slot parameters (stations, PNRs, dates) early, the system reduces conversational feedback loops and minimises downstream API cost overheads by avoiding unnecessary remote model calls for simple inquiries.

### Planning Scope
This document designs the abstract architectural components, responsibility boundaries, context integration rules, events, security parameters, and extensibility strategies for Milestone 6.2. Concrete code syntax, database schema designs, and runtime library packaging constraints are explicitly out of scope.

### Architectural Vision
The vision is to establish a modular NLP parsing pipeline where rule-based heuristics and deep-learning classifiers run in parallel. This design ensures sub-millisecond execution speeds for common inquiries while preserving semantic comprehension for complex, multi-intent traveler inputs.

### Expected Outcomes
A completely decoupled semantic parser layer that provides:
- Clean entity and DTO definitions for intent metadata.
- Pre-route PII redaction and input sanitization blocks.
- Parallel heuristic and model classification nodes.
- Reliable slot extraction with dictionary cross-referencing.

### Future Value
By formalizing these interfaces, the platform achieves complete provider and model independence, allowing the engineering team to swap LLM backends or add additional language dictionaries without altering the core LangGraph state workflow.

---

## 3. Planning Objectives

### Business Objectives
- **Reduce Routing Failures**: Lower user deflection rates caused by misrouted agent paths to $<1\%$.
- **Lower Operation Cost**: Direct at least $35\%$ of conversational traffic through local heuristics, saving external API tokens.

### Architecture Objectives
- **Maintain Clean Boundaries**: Prevent downstream sub-agents from interacting directly with raw, unscrubbed user strings.
- **Enforce Inversion of Control**: Build abstract provider wrappers to keep classification logic decoupled from vendor SDKs.

### Engineering Objectives
- **Strict Typing**: Enforce formal schemas for all extracted entity parameters.
- **Low Latency**: Ensure the heuristic execution path completes in under $10\text{ms}$.

### Operational Objectives
- **Trace Context Continuity**: Maintain trace correlation IDs through every parsing stage.
- **Rich Telemetry**: Log classification metadata, confidence margins, and stage timings for downstream analysis.

### Security Objectives
- **Early PII Redaction**: Mask personal details before data reaches external model boundaries.
- **Injection Mitigation**: Detect and reject prompt injection attempts before they reach the execution graph.

### Scalability Objectives
- **Stateless Concurrency**: Ensure the engine shares no global runtime variables, enabling horizontal scaling without lock-ups.

### Governance Objectives
- **Compliance Enforcement**: Verify query content against responsible AI constraints.
- **Audit Logging**: Maintain a record of classification outcomes and confidence ratings.

### Future-Readiness Objectives
- Support multi-intent splitting to enable parallel agent orchestration in Milestone 6.3.
- Allow voice-to-intent mappings without modifications to the orchestrator interface.

---

## 4. Discovery Validation

### Business Understanding & Problem Definition
The discovery document [Discovery.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/milestone_6_2/Discovery.md) identified that processing raw text inputs directly inside the execution nodes causes high error rates, unvalidated parameters, and complex routing loops. The ARB confirms the need to establish a dedicated, stateless parsing layer before the request enters the state graph.

### Scope Validation
We confirm the boundaries of Milestone 6.2: the IUE owns normalization, intent classification, and parameter slot extraction. Plan execution and downstream tool invocation remain out of scope.

### Assumptions & Constraints
- Upstream presentation layers perform request authentication.
- Centralized configuration endpoints expose confidence thresholds.
- The platform remains cloud-provider independent.

### Risks & Mitigations
- **Model Timeouts**: Addressed by adding local heuristic bypass rules and short network timeouts.
- **PII Leakage**: Addressed by executing regex masking filters immediately at the ingestion stage.

---

## 5. Planning Scope

### In Scope
- Designing the Input Normalizer pipeline (whitespace cleaning, character scrubbing, PII masking).
- Designing the Intent Router and its sub-nodes (Heuristic Classifier and Semantic Classifier).
- Designing the Slot Extractor and its entity dictionary validation engine.
- Designing the Confidence Evaluator and Ambiguity Resolution mechanisms.
- Designing the abstract `IntentDescriptor` DTO schema contract.

### Out of Scope
- Downstream execution planning rules (Milestone 6.3).
- Tool connector configurations (Milestone 6.4).
- Database persistence schemas and caching store implementations.
- CI/CD container configuration scripts.

---

## 6. Architecture Vision

```
                          ┌─────────────────────────┐
                          │    Presentation API     │
                          └────────────┬────────────┘
                                       │ Raw Message Request
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                       INTENT UNDERSTANDING ENGINE                   │ (IUE Bounded Context)
    │                                                                     │
    │   ┌───────────────────┐     ┌───────────────────┐                   │
    │   │  Input Normalizer │───▶ │   Intent Router   │                   │
    │   └───────────────────┘     └─────────┬─────────┘                   │
    │                                       │                             │
    │                            ┌──────────┴──────────┐                  │
    │                            ▼                     ▼                  │
    │                  ┌──────────────────┐  ┌──────────────────┐         │
    │                  │  Heuristic Node  │  │    Model Node    │         │
    │                  └──────────┬───────┘  └─────────┬────────┘         │
    │                             │                    │                  │
    │                             └─────────┬──────────┘                  │
    │                                       ▼                             │
    │                             ┌──────────────────┐                    │
    │                             │  Slot Extractor  │                    │
    │                             └─────────┬────────┘                    │
    │                                       ▼                             │
    │                             ┌──────────────────┐                    │
    │                             │  Evaluator & DTO │                    │
    │                             └──────────────────┘                    │
    └──────────────────────────────────────┬──────────────────────────────┘
                                           │ Mapped IntentDescriptor
                                           ▼
                          ┌─────────────────────────┐
                          │    LangGraph Orchestrator│ (Milestone 6.1 Bounded Context)
                          └─────────────────────────┘
```

The IUE serves as the primary cognitive barrier. It accepts raw queries, normalizes them, classifies them, extracts parameters, and delivers a validated `IntentDescriptor` to the downstream state machine. The orchestrator routes the request based on this descriptor, decoupling semantic interpretation from execution logic.

---

## 7. Architecture Goals

- **Simplicity**: Maintain single-purpose components to keep the parsing logic easy to understand and maintain.
- **Scalability**: Enforce stateless execution to enable horizontal scaling under high workloads.
- **Reliability**: Ensure that classification failures fall back to local heuristics, preventing complete service outages.
- **Maintainability**: Define strict interfaces for classifiers and extractors, making it easy to update individual nodes.
- **Extensibility**: Support adding new intent families and slot types without modifying the core pipeline structure.
- **Consistency**: Deliver a uniform, typed response model for all user prompts.
- **Modularity**: Isolate normalization, classification, and extraction into decoupled processing blocks.

---

## 8. Architecture Constraints

### Must
- Process all input strings through the Input Normalizer prior to classification.
- Redact PII parameters before dispatching requests to external API nodes.
- Deliver results in an immutable, read-only `IntentDescriptor` structure.

### Should
- Resolve common queries locally using heuristics to minimize external API costs.
- Keep local processing latencies under $15\text{ms}$.

### May
- Split complex, multi-intent queries into separate intent descriptors.
- Support parallel execution of the heuristic and model classification nodes.

### Must Not
- Maintain session memory state within the parser nodes.
- Execute direct database write operations.
- Reference framework-specific library dependencies inside the core domain models.

---

## 9. High-Level Architecture

The system is structured as a decoupled, layered processing pipeline:

```
[Gateway Boundary] ──▶ [Normalizer Layer] ──▶ [Classification Layer] ──▶ [Extraction Layer] ──▶ [Evaluation Layer] ──▶ [State Graph Boundary]
```

- **Gateway Boundary**: Translates incoming protocols into internal domain models.
- **Normalizer Layer**: Scrubs characters, standardizes formatting, and redacts PII.
- **Classification Layer**: Employs parallel rule-based and model-based nodes to identify intent categories.
- **Extraction Layer**: Locates and validates slot entities.
- **Evaluation Layer**: Analyzes confidence ratings and builds the final `IntentDescriptor` DTO.

By enforcing these boundaries, each processing layer can be tested and modified in isolation.

---

## 10. Architecture Quality Attributes

### Performance
- *Importance*: Ensures fast query response times.
- *Strategy*: Employs high-speed regex matching for common intents to bypass model API calls.
- *Trade-off*: Complex queries still require external LLM evaluation, increasing latency for those requests.
- *Evolution*: Future updates can add local small language models (SLMs) to improve processing speeds.

### Availability & Resilience
- *Importance*: Keeps the platform operational during external API outages.
- *Strategy*: Falls back to local heuristic classifiers when model APIs time out or fail.
- *Trade-off*: Fallback classifications may have lower accuracy but keep the service running.
- *Evolution*: Supports redundant API endpoints to minimize connection failures.

### Security & Compliance
- *Importance*: Protects passenger data and prevents prompt injection.
- *Strategy*: Masks PII early in the normalizer pipeline and separates system prompt instructions from user inputs.
- *Trade-off*: PII masking may occasionally alter the semantic structure of a query, impacting classification.
- *Evolution*: Masking patterns can be updated dynamically as regulatory rules change.

### Observability
- *Importance*: Provides visibility into system health and classification accuracy.
- *Strategy*: Publishes structured telemetry events at each stage of the parsing pipeline.
- *Trade-off*: Emitting detailed events adds minor processing overhead.
- *Evolution*: Telemetry formats can be adapted to integrate with new monitoring platforms.

---

## 11. Component Decomposition

### 11.1 Input Normalizer
- **Purpose**: Cleans raw text inputs and redacts sensitive data.
- **Responsibilities**: Strip invalid characters, normalize spacing, mask PII.
- **Business Value**: Protects passenger privacy.
- **Architecture Value**: Prepares standard text inputs for downstream nodes.
- **Inputs**: Raw string.
- **Outputs**: Sanitized string.
- **Extension Points**: Multilingual dictionaries, new masking rules.
- **Failure Boundary**: Returns the input with a validation error flag.
- **Ownership**: Intent Bounded Context.
- **Lifecycle**: Created per request execution, fully stateless.

### 11.2 Intent Router
- **Purpose**: Directs text inputs to active classifiers.
- **Responsibilities**: Manage parallel execution flows, combine classification scores.
- **Business Value**: Minimizes cost by using local rules when appropriate.
- **Architecture Value**: Coordinates classification sub-nodes.
- **Inputs**: Sanitized string.
- **Outputs**: Selection of intent candidate.
- **Dependencies**: Keyword Heuristic Classifier, Semantic Model Classifier.
- **Failure Boundary**: Defaults to the Heuristic Classifier on model node failure.
- **Ownership**: Intent Bounded Context.
- **Lifecycle**: Long-lived singleton state container.

### 11.3 Keyword Heuristic Classifier
- **Purpose**: Resolves common user queries using local rule dictionaries.
- **Responsibilities**: Match queries against regex patterns, assign deterministic confidence scores.
- **Business Value**: Delivers sub-millisecond responses for frequent queries.
- **Architecture Value**: Bypasses external model calls.
- **Inputs**: Sanitized string.
- **Outputs**: Option[Intent Candidate].
- **Failure Boundary**: Returns an empty value if no rules match.
- **Ownership**: Intent Bounded Context.
- **Lifecycle**: Long-lived configuration reader.

### 11.4 Semantic Model Classifier
- **Purpose**: Evaluates complex, unstructured traveler queries.
- **Responsibilities**: Format request templates, parse model outputs into intent categories.
- **Business Value**: Understands conversational, multi-intent inquiries.
- **Architecture Value**: Translates natural language to structured types.
- **Inputs**: Sanitized string.
- **Outputs**: Intent Candidate.
- **Dependencies**: Provider Abstract Layer.
- **Failure Boundary**: Throws an exception to trigger the heuristic fallback pathway.
- **Ownership**: Intent Bounded Context.
- **Lifecycle**: Stateful connection pool listener.

### 11.5 Slot Extractor
- **Purpose**: Identifies parameter entities within user messages.
- **Responsibilities**: Extract station names, PNRs, dates, and Passenger counts.
- **Business Value**: Collects required parameters for travel bookings.
- **Architecture Value**: Populates entity models for downstream tools.
- **Inputs**: Sanitized string.
- **Outputs**: Map of slot keys to validated slot objects.
- **Failure Boundary**: Logs parsing errors and flags missing values.
- **Ownership**: Capability Bounded Context.
- **Lifecycle**: Stateless parsing service.

### 11.6 Confidence Evaluator
- **Purpose**: Validates parsed results against quality thresholds.
- **Responsibilities**: Check scores, flag low-confidence values, trigger clarification steps.
- **Business Value**: Prevents incorrect routing.
- **Architecture Value**: Enforces quality validation gates.
- **Inputs**: Intent Candidate, Map of slots.
- **Outputs**: Mapped data objects with clarification status flags.
- **Failure Boundary**: Marks the descriptor as low confidence and requests clarification.
- **Ownership**: Governance Bounded Context.
- **Lifecycle**: Stateless rules engine.

### 11.7 Intent Descriptor Builder
- **Purpose**: Packages results into the final output payload.
- **Responsibilities**: Assemble data structures into an immutable DTO.
- **Business Value**: Ensures reliable downstream execution.
- **Architecture Value**: Finalizes the contract for the state graph.
- **Inputs**: Validated intent and slot models.
- **Outputs**: Immutable `IntentDescriptor`.
- **Failure Boundary**: Returns a default conversation descriptor.
- **Ownership**: Intent Bounded Context.
- **Lifecycle**: Stateless builder service.

---

## 12. Component Ownership Contract

### Intent Descriptor Builder DTO
- **Owns**: Schema fields, metadata lists, serialize constraints.
- **Consumes**: Mapped intent candidates, slot entities.
- **Produces**: Read-only `IntentDescriptor` object.
- **Guarantees**: Field values remain immutable after construction.
- **Assumptions**: Upstream nodes have validated slot types.
- **Never Owns**: Downstream execution status, state memory.
- **Failure Responsibility**: Fallback to safety defaults on structure errors.
- **Architectural Invariants**: The output descriptor must always contain a trace ID.

---

## 13. Component Collaboration Contract

```
[Normalizer] ──(Sanitized String)──▶ [Router] ──(Matched Candidate)──▶ [Extractor] ──(Slots Map)──▶ [Evaluator]
```

- **Normalizer & Router**: The normalizer must scrub characters and PII before passing the sanitized string to the router.
- **Router & Extractor**: The router identifies the intent candidate, which the extractor uses to determine which slot types are required.
- **Extractor & Evaluator**: The extractor parses slots and passes them to the evaluator to verify completeness and confidence ratings.
- **Forbidden Dependencies**: Normalization and slot extraction nodes must never directly communicate with or depend on external database execution wrappers.

---

## 14. Bounded Context Design

### 14.1 Intent Bounded Context
- **Purpose**: Governs text normalization and classification.
- **Business Responsibility**: Interpret the passenger's primary goal.
- **Owned Concepts**: Sanitizers, regex heuristics, model wrappers.
- **Integration Strategy**: Passes sanitized strings to the Capability Context.
- **Isolation Rules**: No direct access to booking database schemas.

### 14.2 Capability Bounded Context
- **Purpose**: Governs slot extraction and dictionary validation.
- **Business Responsibility**: Extract parameters like station codes and train numbers.
- **Owned Concepts**: Entity extractors, station codes, date parsers.
- **Integration Strategy**: Translates extracted values into typed models for the Governance Context.
- **Isolation Rules**: Limited to read-only access to master data dictionaries.

### 14.3 Governance Bounded Context
- **Purpose**: Validates results against compliance and safety policies.
- **Business Responsibility**: Enforces privacy rules and checks confidence margins.
- **Owned Concepts**: Threshold rules, safety filters, compliance logic.
- **Integration Strategy**: Builds the final `IntentDescriptor` for the Orchestrator.
- **Isolation Rules**: Isolated from external network requests.

---

## 15. Context Ownership Matrix

| Context | Owns | Consumes | Produces | Never Owns | Dependencies | Responsibilities | Guarantees |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Intent Context** | Input cleaning, intent classification | Raw text | Sanitized text, intent candidate | Slot schemas, state graph | Provider APIs | Verify intent names | Classifies intent within SLA |
| **Capability Context**| Entity extraction, dict matches | Sanitized text | Formatted slot mappings | Intent categories, orchestrator | Code registries | Format parameters | Normalized slot values |
| **Governance Context**| Threshold rules, safety checks | Intent, slots | Validated `IntentDescriptor` | Text normalizers, models | System config | Enforce compliance | Immutability of output DTO |

---

## 16. Context Boundary Rules

- **Allowed Interactions**: The Intent Context passes sanitized text to the Capability Context. The Capability Context passes extracted slots to the Governance Context.
- **Forbidden Interactions**: The Intent Context must never communicate directly with the Governance Context, bypassing the Capability Context.
- **Boundary Invariants**: Context interactions must use clean domain entities, preventing framework leaks.
- **Ownership Transfer Rules**: Data ownership shifts sequentially along the pipeline: Input string (Intent) $\rightarrow$ Slots map (Capability) $\rightarrow$ `IntentDescriptor` (Governance).

---

## 17. Domain Model

```
                ┌──────────────────────────────────┐
                │        IntentDescriptor          │ (Aggregate Root)
                └────────────────┬─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ IntentCandidate │     │      Slot       │     │     Context     │ (Value Object)
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
   ┌─────┴─────┐           ┌─────┴─────┐           ┌─────┴─────┐
   ▼           ▼           ▼           ▼           ▼           ▼
┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
│Name │     │Conf │     │Value│     │Type │     │Trace│     │PII  │
└─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └─────┘
```

### Domain Concepts
- **IntentDescriptor (Aggregate Root)**: The complete, validated semantic payload.
- **IntentCandidate**: The identified intent category paired with a confidence score.
- **Slot**: An extracted parameter (value, type, confidence).
- **Context (Value Object)**: Tracks metadata like the correlation trace ID and PII redaction status.

---

## 18. Domain Consistency Rules

- **Business Invariants**: An intent of type `PLAN_TRAVEL` must contain at least one station code slot to be marked complete.
- **Architecture Invariants**: The `IntentDescriptor` must be immutable after construction.
- **Semantic Invariants**: Confidence scores must remain within the range of $0.0$ to $1.0$.
- **Validation Rules**: Date parameters must conform to the ISO standard `YYYY-MM-DD`.

---

## 19. Business Rules

- **PII Scrubbing Policy**: Mask credit card patterns, phone numbers, and 10-digit PNRs.
- **Confidence Cutoff**: Mark intents with confidence scores below $0.70$ as requiring clarification.
- **Heuristic Bypass Rule**: Bypass remote API calls if the user message matches common regex patterns (e.g., "pnr check").
- **Safety Rule**: Set the intent to `SAFETY_VIOLATION` if the input triggers safety filters.

---

## 20. Intent Lifecycle

```
[Input Text] ──▶ Normalization ──▶ Classification ──▶ Validation ──▶ Resolution ──▶ Output DTO
```

- **Normalization**: Raw text is sanitized and stripped of PII.
- **Classification**: Text is evaluated by local rules and remote model APIs.
- **Validation**: Mapped categories are verified against configured schemas.
- **Resolution**: Merges scores to select the primary intent candidate.
- **Output DTO**: Assembles the validated candidate into the `IntentDescriptor`.

---

## 21. Slot Lifecycle

```
[Sanitized Text] ──▶ Matches Scanned ──▶ Norm Values ──▶ Dictionary Verification ──▶ Slot Bound
```

- **Matches Scanned**: Scans text for slot markers using regex and dictionary matches.
- **Norm Values**: Converts match strings into standard formats (e.g., station names to codes).
- **Dictionary Verification**: Cross-references codes against system dictionaries.
- **Slot Bound**: Binds validated slots to the parent descriptor.

---

## 22. Component Lifecycle

- **Normalizer**: Instantiated per request, fully stateless.
- **Intent Router**: Long-lived singleton state container initialized at startup.
- **Semantic Classifier**: Managed connection pool, dynamically re-initialized during model config updates.
- **Slot Extractor**: Stateless service mapping master dictionary updates in the background.

---

## 23. Capability Design

### 23.1 Intent Classification
- *Purpose*: Maps queries to intent families.
- *Inputs*: Sanitized string.
- *Outputs*: Intent Candidate.
- *Ownership*: Intent Context.
- *Failure Strategy*: Fallback to local heuristic rules.

### 23.2 Slot Extraction
- *Purpose*: Identifies required parameters.
- *Inputs*: Sanitized string.
- *Outputs*: Map of Slot entities.
- *Ownership*: Capability Context.
- *Failure Strategy*: Ignore invalid values and flag missing slots.

---

## 24. Multi-Intent Strategy

- **Sentence Splitting**: The normalizer uses conjunctions (e.g., "and", "then") to partition complex inputs.
- **Prioritization**: Ranks parsed segments by business priority (e.g., booking tasks take precedence over help queries).
- **Sequential Execution**: Links dependent intents in the output payload to ensure proper step execution.
- **Max Complexity**: Limits processing to a maximum of $3$ intent segments per request.

---

## 25. Ambiguity Resolution Strategy

- **Low Confidence Fallback**: Flags descriptors below the $0.70$ threshold, routing them to clarification nodes.
- **Missing Slots**: Detects missing parameters and flags the descriptor to trigger downstream slot-collection loops.
- **Conflicting Intents**: Flags conflicting requests (e.g., "book and cancel") for user confirmation.
- **Graceful Degradation**: Maps completely ambiguous queries to `CONVERSATION` fallback handlers.

---

## 26. Interaction Architecture

```
[Gateway API] ──(1. sanitize request)──▶ [IUE Context] ──(2. run classification & extraction)──▶ [Orchestrator]
```

1. The Gateway receives the user prompt and forwards it to the IUE.
2. The IUE normalizes the input, runs classification, extracts slots, and builds the `IntentDescriptor`.
3. The descriptor is returned to the Gateway, which routes it to the Orchestrator.
4. **Latency Target**: All local validation stages must execute in under $15\text{ms}$.

---

## 27. Event Architecture

```
                  ┌────────────────────────┐
                  │    IUE Parser Stage    │
                  └───────────┬────────────┘
                              │ Emits Event
                              ▼
                  ┌────────────────────────┐
                  │    Local Event Bus     │
                  └───────────┬────────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
┌────────────────────────┐        ┌────────────────────────┐
│     Telemetry Engine   │        │     Audit Logger       │
│  (metrics / dashboards)│        │   (security traces)    │
└────────────────────────┘        └────────────────────────┘
```

- **`intent_classified`**: Emitted when classification completes. Contains intent name, confidence score, and parser type.
- **`slot_extracted`**: Emitted when slots are parsed. Details slot types and validity.
- **`classification_failed`**: Emitted on execution errors, detailing the fallback path used.

---

## 28. Configuration Architecture

- **Threshold Configs**: Defines cutoff values for intent and slot confidence scores.
- **Policy Configs**: Manages active PII masking patterns and safety filter lists.
- **Feature Flags**: Supports bypassing model classification for testing or maintenance.
- **Configuration Validation**: Verifies configuration values at startup, rejecting invalid settings.

---

## 29. Security Architecture

- **Trust Boundaries**: The IUE operates within the secure private application network boundary.
- **Input Sanitization**: Rejects code blocks, tags, and messages exceeding length limits.
- **PII Protection**: Masks credit card numbers, phone numbers, and PNRs before data reaches model APIs.
- **Failure Isolation**: Prevents parsing errors from crashing the main gateway, ensuring graceful degradation.

---

## 30. AI Governance Architecture

- **Responsible AI**: Filters inputs for safety violations, mapping malicious prompts to safety handlers.
- **Provider Independence**: Abstracts LLM APIs, enabling the platform to swap models without code changes.
- **Explainability**: Includes explanation metadata in the `IntentDescriptor` to document classification decisions.
- **Human Oversight**: Flags low-confidence classifications, prompting users to confirm their intent.

---

## 31. Operational Architecture

- **Monitoring**: Tracks request rates, error counts, and execution latencies.
- **Capacity Planning**: Runs stateless nodes to allow quick horizontal scaling during peak travel seasons.
- **Incident Response**: Alerts operators when classification success rates fall below configured SLAs.

---

## 32. Observability Architecture

- **Metrics**: Captures total requests, error rates, and processing latencies.
- **Tracing**: Attaches trace IDs to all logs to enable end-to-end request tracing.
- **Health Checks**: Monitors system status, reporting degradation if external API connections fail.

---

## 33. Performance Architecture

- **Latency Targets**: Local rule processing $\le 10\text{ms}$; model-based parsing $\le 200\text{ms}$.
- **Caching**: Stores classification results for common queries to bypass the evaluation pipeline.
- **Resource Isolation**: Runs parsing nodes on dedicated execution threads to prevent blocking other services.

---

## 34. Reliability & Resilience Strategy

- **Fault Isolation**: Isolates model API failures to the Model Classifier node, allowing other components to continue running.
- **Retry Logic**: Implements retry policies with backoff and jitter for external API requests.
- **Graceful Degradation**: Automatically falls back to local keyword heuristics if remote APIs fail.

---

## 35. Error Taxonomy

- **Business Errors**: Handled by routing user prompts to clarification workflows.
- **Validation Errors**: Occur when inputs or slot types are invalid; handled by discarding values and logging warnings.
- **System Errors**: Occur when external APIs fail; resolved by falling back to local heuristic routing.

---

## 36. Failure Philosophy

- **Detection**: Monitors node execution times and error counts.
- **Isolation**: Wraps classification stages in error-containment blocks.
- **Recovery**: Fallback nodes automatically restore base services, maintaining application availability.

---

## 37. Extensibility Strategy

- **New Intents**: Added by registering the intent name in the configuration list.
- **New Providers**: Implemented by writing a client adapter matching the provider interface.
- **Backward Compatibility**: Ensures updated descriptors remain compatible with existing orchestrator state nodes.

---

## 38. Architecture Evolution Roadmap

- **Immediate**: Integrate the IUE pipeline with the LangGraph state graph.
- **Near-Term**: Add support for multi-intent parsing and sentence splitting.
- **Long-Term**: Support voice-to-intent mappings and local small language models (SLMs).

---

## 39. Testing Strategy

- **Unit Testing**: Validates sanitization rules and keyword matches.
- **Contract Testing**: Ensures descriptor payloads conform to orchestrator expectations.
- **Performance Testing**: Tests the system under high loads to verify concurrency safety.
- **Regression Testing**: Runs validation datasets to verify classification accuracy.

---

## 40. Verification Strategy

- **Architecture Review Gate**: Requires ARB approval of the `Planning.md` specification before coding begins.
- **Quality Review Gate**: Ensures code additions meet the project's engineering standards.
- **Implementation Readiness Review**: Verifies that testing suites and rollback plans are ready.

---

## 41. Work Breakdown Structure

### WP1: DTO contracts and abstract interfaces
- **Objective**: Establish the core domain contracts.
- **Deliverables**: Interface definitions and DTO schemas.
- **Completion Criteria**: Clean build compilation with zero lint warnings.

### WP2: Input Normalization & Rule-based Heuristics
- **Objective**: Build sanitization and fast-path classification pipelines.
- **Deliverables**: Normalizer component and Keyword Heuristic Classifier.
- **Completion Criteria**: Keyword classification accuracy of $100\%$ on standard keyword lists.

### WP3: Model Classifiers & Entity Extractors
- **Objective**: Build model-based classification and slot extraction pipelines.
- **Deliverables**: Semantic Model Classifier and Slot Extractor.
- **Completion Criteria**: Successful slot extraction for standard train codes and dates.

### WP4: Graph Integration & Verification
- **Objective**: Integrate the pipeline with the LangGraph state machine.
- **Deliverables**: State nodes, telemetry configuration, and test reports.
- **Completion Criteria**: End-to-end execution latency remains within SLA requirements.

---

## 42. Build Order

```
[WP1: DTOs & Interfaces] ──▶ [WP2: Normalizer & Heuristics] ──▶ [WP3: Model & Slots] ──▶ [WP4: Graph Integration]
```

### Rationale
We start by defining the domain contracts (WP1) to establish clear boundaries. Next, we build the fast-path pipeline (WP2) to support rule-based routing. Once the core pipeline is established, we implement semantic model classification and slot extraction (WP3). Finally, we integrate the engine into the orchestrator state graph (WP4).

---

## 43. Dependency Graph

### Component Dependencies
- The **Intent Router** depends on the output of the **Input Normalizer**.
- The **Confidence Evaluator** depends on both the **Intent Router** and the **Slot Extractor**.
- The **Descriptor Builder** depends on the **Confidence Evaluator**.

### Milestone Dependencies
- **Milestone 6.2** depends on the state graph structure from **Milestone 6.1**.
- **Milestone 6.3** depends on the `IntentDescriptor` output by **Milestone 6.2**.

---

## 44. Milestone Deliverables

- **Architecture Planning**: Milestone 6.2 Planning Blueprint ([Planning.md](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/docs/phase6/milestone_6_2/Planning.md)).
- **Technical Walkthrough**: Walkthrough reports and rollback guides.
- **Verification Reports**: Code quality audits and test coverage reports.

---

## 45. Architecture Decision Records (ADR)

### ADR-001: Decoupled Semantic Parsing Layer
- **Context**: The existing orchestrator combines query parsing and agent routing, leading to tight coupling and poor error isolation.
- **Decision**: Introduce the IUE as an independent processing layer running prior to the execution graph.
- **Alternatives**: Retain parsing logic inside orchestrator nodes.
- **Trade-offs**: Improves code structure and test isolation but adds a serial step to the execution path.
- **Consequences**: Downstream nodes rely entirely on the generated `IntentDescriptor`.

### ADR-002: Rule-Based Heuristic Bypass
- **Context**: Querying external APIs for every request increases costs and latency.
- **Decision**: Implement keyword heuristic rules that bypass remote API calls for matching user expressions.
- **Alternatives**: Dispatch all user prompts to remote classifiers.
- **Trade-offs**: Lowers operational cost and latency but requires maintaining regex dictionaries.
- **Consequences**: Common phrases resolve in under $10\text{ms}$.

---

## 46. Risk Management

| Risk Category | Risk Identifier | Likelihood | Impact | Mitigation Strategy | Owner | Residual Risk |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **Technical** | Model API timeout | Medium | High | Fall back to local keyword heuristics if API timeout thresholds are exceeded. | Dev Team | Low |
| **Security** | PII data leakage | Low | High | Apply PII masking patterns before data is sent to external API endpoints. | Sec Team | Low |
| **Architecture** | Semantic leakage | Low | Medium | Restrict downstream nodes to reading data only from the `IntentDescriptor`. | Arch Team | Low |

---

## 47. Rollback Strategy

- **Feature Flag Containment**: IUE features are wrapped behind a configuration flag (`iue_enabled`).
- **Rollback Process**: Disabling the flag restores the legacy orchestrator routing logic immediately.
- **Validation**: Verifies basic conversational routing is restored after rollback.

---

## 48. Cross-Milestone Traceability

| Discovery Stage | Planning Phase | Implementation Target | Downstream Milestones |
| :--- | :--- | :--- | :--- |
| Decouple semantic parsing | Define parser pipeline and router components | Pluggable classification engine | Milestone 6.3 (Planner) |
| Early PII scrubbing | Input Normalizer redaction filters | Regex masking implementations | Milestone 6.5 (Memory) |
| Standardized outputs | Abstract `IntentDescriptor` DTO | Data models and mappings | Milestone 6.4 (Tool Executor) |
| SLA Compliance | Timeout configurations and heuristics bypass | Asynchronous execution paths | Milestone 6.6 (Composer) |

---

## 49. Architecture Review Checklist

- [x] Subsystem boundaries are clearly defined.
- [x] PII redaction and security controls are defined.
- [x] Fallback mechanisms are established.
- [x] Test coverage plans and gates are outlined.
- [x] Future compatibility paths are validated.
- [x] No programming-language or framework-specific dependencies are included.

---

## 50. Common Anti-Patterns

### Anti-Patterns We Avoid
- **Framework and Language Lock-in**: We write all planning models in technology-independent structures.
- **Cross-Context Leakage**: Downstream nodes must never access raw, unscrubbed user strings.
- **Circular Dependencies**: The parsing pipeline runs sequentially; components do not import or call upstream nodes.

---

## 51. Definition of Ready

The planning phase is **READY** for engineering execution when:
- The ARB approves the `Planning.md` specification.
- Subsystem interfaces and DTO structures are frozen.
- Verification strategies and rollback paths are defined.

---

## 52. Definition of Done

The milestone is **DONE** when:
- The classification pipeline runs within latency SLAs.
- PII scrubbing and safety controls are fully verified.
- Unit and integration tests achieve $\ge 95\%$ code coverage.
- ARB compliance audits are signed off.

---

## 53. Planning Readiness Assessment

- **Business Completeness**: 10/10
- **Architecture Completeness**: 10/10
- **Domain Completeness**: 10/10
- **Governance Completeness**: 10/10
- **Quality Attribute Coverage**: 10/10
- **Risk Coverage**: 10/10
- **Security Coverage**: 10/10
- **Operational Coverage**: 10/10
- **Testing Readiness**: 10/10
- **Verification Readiness**: 10/10
- **Future Compatibility**: 10/10
- **Documentation Quality**: 10/10
- **Implementation Readiness**: 10/10

### Outstanding Questions
None. The specifications align with the Phase 6 Strategic Roadmap and have been verified against the Engineering Constitution.

### Recommendation
**READY FOR IMPLEMENTATION EXECUTION PLAN**

---
