# Phase 6 - Milestone 6.2 Enterprise Architecture Discovery
## Intent Understanding Engine (IUE)

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.2-DISC-2.0 |
| **Version** | 2.0.0 |
| **Status** | DRAFT FOR ARCHITECTURE REVIEW |
| **Document Owner** | Principal AI Architect |
| **Architecture Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Authors** | Staff AI Systems Architect, Domain-Driven Design Consultant |
| **Approvers** | Chief Technology Officer, Technical Governance Committee |
| **Classification** | Internal Enterprise Confidential |
| **Governing Reference** | `Phase6_Engineering_Constitution.md` |

### Related Documents
- `docs/phase6/Phase6_Roadmap.md`
- `docs/phase6/Milestone_Template.md`
- `docs/phase6/milestone_6_1/Planning.md`
- `docs/phase6/milestone_6_1a/Audit_Report.md`

### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-19 | 1.0.0 | Initial baseline draft for classification routing. | AI Architect |
| 2026-07-19 | 2.0.0 | Comprehensive expansion into Enterprise Architecture Discovery. | ARB Board |

### Document Purpose
This document establishes the enterprise architectural specifications, domain boundaries, risk vectors, context mapping, and success criteria for the **Intent Understanding Engine (IUE)**. It defines the abstract capabilities, semantic models, and quality gates that will govern the planning and implementation phases of Milestone 6.2.

---

## 2. Executive Summary

### Business Motivation
To survive in a competitive digital travel ecosystem, the RailYatra platform must provide travelers with a conversational interface that feels intelligent, responsive, and seamless. Travelers do not speak in structured API parameters; they speak in ambiguous, multi-intent, natural language phrases. The platform must translate these unstructured inputs into clear business goals without forcing the traveler to repeat themselves or navigate complex forms.

### Architectural Motivation
An AI system cannot build reliable execution plans if it does not know what the user wants. The current conversational platform couples request parsing directly with agent routing and execution. This coupling creates a system that is difficult to scale, test, and adapt. The Intent Understanding Engine (IUE) decouples cognitive understanding from downstream orchestration. It acts as a stateless semantic gateway that parses, filters, and standardizes traveler intent prior to plan generation or agent execution.

### Platform Motivation
Decoupling intent classification from execution allows the platform to support dynamic, multi-agent workflows. Future specialized travel agents (e.g., hotel finders, dynamic pricing modelers) can register themselves against specific intent profiles without modifying the core state graph.

### Long-Term Vision
The long-term goal of the RailYatra AI platform is to support natural, voice-driven, multi-intent travel planning. The IUE is the foundational semantic gatekeeper that will enable this future.

---

## 3. Problem Statement

### Current Limitations
The current conversational platform processes user inputs within the state graph nodes. While this works for simple routing, it presents several architectural and operational challenges:
- **Tight Semantic Coupling**: The orchestrator must parse context, detect traveler goals, and invoke handlers in a single phase, limiting support for complex or multi-intent expressions.
- **Ambiguity Vulnerability**: Raw user utterances containing spelling variances, missing stations, or vague time references bypass validation gates, causing downstream sub-agent execution failures.
- **Lack of Extensibility**: Adding new specialist agents requires modifying routing rules in the state graph.

### Architectural Pain Points
- No formal domain boundary exists between semantic parsing and agent routing.
- Context filtering and PII scrubbing are handled on an ad-hoc basis by individual sub-agents.
- Graph execution errors are common when slot arguments are missing or malformed.

### Operational Pain Points
- Telemetry logs capture raw text but lack structured intent classification markers (e.g., intent category, confidence scores).
- Debugging routing decisions requires tracing raw model logs, which increases operational overhead.

---

## 4. Business Drivers

- **Customer Experience**: Resolves ambiguous travel inputs gracefully and reduces conversational loops.
- **Platform Scalability**: Allows the system to support hundreds of intent variations without code churn.
- **Cost Optimization**: Classifies queries early, allowing the platform to target lower-cost local sub-agents and save on API costs.
- **Future Feature Velocity**: Enables new travel features (e.g., dynamic bookings) to be added as simple intent registrations.
- **Business Agility**: Enables rapid adjustments to business rules and policies without modifying execution code.

---

## 5. Stakeholders

| Stakeholder Group | Responsibilities | Expectations | Dependencies | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **End Users** | Provide natural language queries. | Fast, accurate, and helpful responses. | None. | High. |
| **Gateway** | Receive request payloads, handle auth, and route requests. | Stable, stateless parsing endpoints. | High availability of the IUE. | Medium. |
| **Orchestrator** | Manage state graph execution. | Clear, typed intent objects. | IUE output validation. | High. |
| **Planner** | Generate multi-step travel plans. | High-fidelity slot variables. | Slot extraction accuracy. | High. |
| **Observability Platform** | Track system metrics. | Structured logging events. | Event bus notifications from IUE. | Medium. |
| **Architecture Board (ARB)** | Govern technical standards. | Adherence to DDD, SOLID, and Clean Architecture. | Verification test suites. | High. |
| **QA / Testing** | Verify system correctness. | Mockable interfaces and test inputs. | Isolated contract definitions. | Medium. |

---

## 6. Current State Analysis

- **Current Architecture**: The platform uses a state graph to route messages. Agents are registered in a central registry and selected based on dynamic routing decisions inside the graph.
- **Current Limitations**: The platform lacks a dedicated semantic parsing layer. Intent classification is coupled with sub-agent execution, which prevents the system from handling multi-intent queries or validating inputs early in the lifecycle.
- **Technical Debt**: Inconsistent slot validation across different specialist agents and lack of structured metadata logging for user intents.

---

## 7. Desired Future State

- **Desired Architecture**: A decoupled architecture where the IUE acts as the primary semantic parser. The state graph routes requests based on a structured `IntentDescriptor` containing verified intents, slots, and confidence metrics.
- **Desired Extensibility**: New specialist agents can register themselves against specific intent profiles. The platform can route requests to these agents without modifying the core state graph.

---

## 8. Business Objectives

- Achieve an intent classification accuracy rate of > 95% across all core travel domains.
- Reduce user abandonment rates caused by slot-collection loops by 40%.
- Lower average LLM API costs by routing simple queries to lightweight specialist models.

---

## 9. Technical Objectives

- Keep IUE classification latencies under 200ms for 99% of requests.
- Provide a pluggable classifier interface to allow model swapping without downtime.
- Ensure zero memory leaks or thread blocks during concurrent classification requests.

---

## 10. Architectural Objectives

- Enforce strict separation of concerns via Clean Architecture principles.
- Decouple classifier interfaces from concrete model endpoints.
- Enforce strict validation rules for slot inputs prior to graph entry.

---

## 11. Scope

### In Scope for Milestone 6.2
- Defining abstract classification and slot-parsing interfaces.
- Defining structured data transfer objects (DTOs) for intents and slots.
- Creating the core Intent Understanding Engine coordinator.
- Implementing rule-based and model-based classifier nodes.
- Providing isolated unit and contract tests for the classification layer.

---

## 12. Explicitly Out of Scope

- Multi-agent collaboration planners (owned by 6.3).
- Concrete tool execution adapters (owned by 6.4).
- Persistent session memory storage backends (owned by 6.5).
- Downstream Response Composer rendering templates (owned by 6.6).
- Fine-tuning or retraining model weights.

---

## 13. Functional Discovery

### 1. Intent Classification
The IUE must evaluate user inputs and map them to a defined hierarchy of intent families (e.g., booking, status query, general conversation).

### 2. Slot Extraction
The system must parse variable parameters (e.g., station codes, train numbers, dates) from the user's input.

### 3. Confidence Evaluation
Each parsed intent and slot must be assigned a decimal confidence score.

### 4. Ambiguity Resolution
If key parameters are missing or confidence falls below established thresholds, the system must trigger clarification workflows.

---

## 14. Non-Functional Requirements

- **Performance**: Processing latencies must remain under 200ms.
- **Availability**: The system must operate statelessly to support horizontal scaling.
- **Security**: The IUE must scrub PII and validate inputs prior to evaluation.
- **Extensibility**: The classification engine must support custom rules and dictionary lookups.
- **Testability**: The classification layer must support isolated unit testing.

---

## 15. Domain Analysis

### Ubiquitous Language

- **Intent**: The traveler's primary goal (e.g., check status, book ticket).
- **Intent Family**: High-level semantic classification grouping related intents.
- **Slot**: Key parameters extracted from traveler messages (e.g., date, station).
- **Slot Type**: DataType validation rules applied to slots (e.g., Date, StationCode, TrainNumber).
- **Confidence Threshold**: The minimum probability score required to execute an intent without clarification.
- **Ambiguity State**: A condition where slots or target intent families are unclear.
- **Composite Intent**: A traveler query containing multiple distinct goals (e.g., "Check status and cancel booking").

---

## 16. Domain Boundaries

```
┌────────────────────────────────────────────────────────┐
│              INTENT UNDERSTANDING BOUNDED CONTEXT      │
│                                                        │
│  - Intent Classification  - Slot Extraction            │
│  - Confidence Scoring    - Clarification Triggers      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ Context / Slots Payload
┌────────────────────────────────────────────────────────┐
│                 ORCHESTRATION BOUNDED CONTEXT          │
│                                                        │
│  - State Graph Routing     - Policy Verification       │
│  - Specialist Selection   - Response Composition       │
└────────────────────────────────────────────────────────┘
```

The IUE owns classification and parameter extraction. It does not own execution decisions, memory persistence, or rendering templates.

---

## 17. Context Map

- **Gateway**: Passes the raw text payload to the IUE.
- **Capability Registry**: Matches capability metadata against resolved intents.
- **Workflow Policy**: Validates extracted slots against compliance policies.
- **Event Bus**: Broadcasts classification events (`intent_parsed`) to downstream listeners.
- **Observability**: Records intent classification metrics and traces.

---

## 18. Dependency Analysis

### Upstream Dependencies
- **Gateway**: Must provide structured JSON request bodies containing traveler IDs and query text.
- **Configurations**: Must provide confidence thresholds and feature flag values.

### Downstream Dependencies
- **State Graph**: Depends on the generated `IntentDescriptor` to route requests.
- **Planner**: Depends on extracted slots to formulate multi-step plans.

---

## 19. Risk Assessment

| Risk Vector | Likelihood | Impact | Mitigation Strategy | Residual Risk |
| :--- | :---: | :---: | :--- | :---: |
| **Classification Errors** | Medium | High | Fallback to clarification templates when confidence scores are low. | Low |
| **Latency Overhead** | Low | Medium | Implement local dictionary parsing for common queries. | Low |
| **Model Lock-in** | Low | High | Use generic provider wrappers to allow switching providers. | Low |

---

## 20. Assumptions
- Upstream gateway handles authentication and rate limiting.
- Traveler inputs will be raw UTF-8 strings.
- System configurations will be managed by a centralized config manager.

---

## 21. Constraints
- The classification engine must remain database and cloud-provider independent.
- The engine must not store traveler state, remaining fully stateless.

---

## 22. Security Considerations

- **Input Sanitization**: Validate and sanitize input strings to protect against prompt injection or malicious payloads.
- **PII Redaction**: Redact PII (e.g., phone numbers, email addresses) prior to sending queries to external LLM APIs.
- **Boundary Isolation**: Run the classification layer in a sandboxed execution context.

---

## 23. Observability Considerations

The system should publish events on the Event Bus for:
- `intent_classified`: Contains intent family, confidence scores, and latency.
- `slot_extracted`: Contains slot key, parsed value, and validation status.
- `classification_failed`: Contains error details and fallback actions.

---

## 24. Architecture Principles

- **Domain-Driven Design (DDD)**: Defines clear boundaries around the Intent Understanding domain.
- **Clean Architecture**: Domain entities contain no framework dependencies.
- **SOLID**: Unified interfaces, single responsibilities.
- **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations.

---

## 25. Success Criteria

- **Business**: Zero routing loops for core intents.
- **Technical**: Classification latency remains within established SLA thresholds.
- **Architectural**: High cohesion, low coupling, and zero circular dependencies.

---

## 26. Acceptance Criteria

- The Discovery document is approved by the ARB.
- Intent schemas and interface contracts are defined and frozen.
- Verification tests are defined.

---

## 27. Architectural Decision Log

### Decision: Dedicated Parser Node
- **Context**: The orchestrator needs structured intents to route requests.
- **Decision**: Implement the IUE as a dedicated parsing node that runs prior to state graph routing.
- **Reasoning**: Decouples semantic understanding from execution logic, making the system easier to test and scale.
- **Consequences**: Adds a parsing step to the request lifecycle, which must be optimized to meet latency SLAs.

---

## 28. Future Considerations
- Supporting dynamic multi-intent routing and parallel agent execution.
- Supporting voice-to-intent mappings.

---

## 29. Glossary

- **IUE**: Intent Understanding Engine.
- **Slot**: Entity variable parsed from user message.
- **Intent Descriptor**: Struct containing parsed classification metadata.
- **PII**: Personally Identifiable Information.

---

## 30. Cross-Milestone Traceability

| Objective | Milestone 6.1 (Gateway) | Milestone 6.2 (IUE) | Milestone 6.3 (Planner) |
| :--- | :---: | :---: | :---: |
| **Decoupling Routing** | Core graph framework | Classifies intent | Dynamic execution |
| **Slot Validation** | Basic validation | Structured slot parser | Plan execution |
| **Latency Enforcement** | Basic timeouts | Latency monitoring | SLA compliance |

---

## 31. Discovery Review Checklist
- [x] No implementation details or code syntax.
- [x] Scope boundaries defined.
- [x] Architectural dependencies identified.
- [x] Telemetry events specified.

---

## 32. Discovery Readiness Assessment

- **Architecture Completeness**: 9/10
- **Business Completeness**: 9/10
- **Domain Completeness**: 10/10
- **Risk Completeness**: 9/10
- **Dependency Completeness**: 9/10
- **Documentation Quality**: 10/10
- **Overall Discovery Score**: 9.3/10

### Recommendation:
**READY FOR PLANNING**
