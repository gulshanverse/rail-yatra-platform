# Phase 6 - Milestone 6.1 Discovery
## Enterprise AI Gateway & Orchestration Foundation Specification

---

## Document Control
- **Document Reference**: RY-P6-M6.1-DISC-3.0
- **Version**: 3.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: APPROVED / ACTIVE / FROZEN
- **Governing Reference**: `Phase6_Engineering_Constitution.md`

---

## Executive Summary

### Platform Maturity Context
The RailYatra AI platform has reached high maturity in analytical capability after Phase 5. The platform houses robust, domain-specific intelligence engines covering railway status, journey alternative calculation, waitlist booking probabilities, proactive traveler tracking, and continuous personalization.

### Post-Phase 5 Limitations
While the individual intelligence engines are highly functional, they operate independently. Downstream client interfaces are forced to interact with multiple separate APIs, coupling client-side application flows with internal engine routing. Without a unified coordination layer, the platform cannot manage stateful conversation context, orchestrate multi-step trip queries, or validate user privacy preferences globally.

### Strategic Necessity of Orchestration
- **Business Importance**: The transition to conversational travel management requires a single entrypoint that abstracts transaction execution. The traveler should see a unified, cognitive service instead of a collection of modular tools.
- **Technical Importance**: An orchestration facade encapsulates state management, lifecycle verification, error boundaries, and observability. This shields individual core engines from high-frequency frontend request churn and request format changes.
- **Long-term Architectural Vision**: Establishing the Gateway & Orchestration Foundation creates a pluggable, scalable runtime environment. Future cognitive modules (intent understanding, multi-step planners, memory stores, and response composers) can be integrated as modular plugins without modifying downstream APIs.

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Stakeholders](#2-stakeholders)
3. [Business Drivers](#3-business-drivers)
4. [Current State](#4-current-state)
5. [Desired Future State](#5-desired-future-state)
6. [Objectives](#6-objectives)
7. [Scope Boundaries](#7-scope-boundaries)
8. [Out of Scope](#8-out-of-scope)
9. [Dependencies](#9-dependencies)
10. [Risks and Mitigations](#10-risks-and-mitigations)
11. [Non-Functional Goals](#11-non-functional-goals)
12. [Architectural Principles](#12-architectural-principles)
13. [Success Criteria](#13-success-criteria)
14. [Acceptance Criteria](#14-acceptance-criteria)
15. [Success Metrics](#15-success-metrics)
16. [Future Considerations](#16-future-considerations)
17. [Architecture Context](#17-architecture-context)
18. [Glossary](#18-glossary)
19. [Decision Log](#19-decision-log)
20. [Architecture Review Summary](#20-architecture-review-summary)
21. [Discovery Freeze Certification](#21-discovery-freeze-certification)

---

## 1. Problem Statement

### 1.1 Architectural Limitations
- Downstream systems directly couple with individual domain gateways, causing high API surface exposure.
- No logical component manages the orchestration execution flow of multi-criteria traveler requests.

### 1.2 Operational Limitations
- No correlation mechanism exists to trace a request through conversational nodes and downstream intelligence engines.
- Observability and latency metric reporting are scattered across separate systems.

### 1.3 AI and Scalability Limitations
- Conversational state processing lacks a standardized data model, preventing multi-step workflow planning.
- Scaling the presentation layers requires duplicating validation and security check logic.

### 1.4 User Experience Limitations
- Conversational threads have no session boundaries, preventing travelers from executing natural-language travel requests.

---

## 2. Stakeholders

- **Passengers**: Require a conversational booking and assistance interface. Benefit from fast, unified responses and robust privacy controls.
- **Developers**: Require standard, technology-independent contract definitions. Benefit from clear coding boundaries and decoupled repositories.
- **AI Engineers**: Require a stable, stateful context loop. Benefit from pluggable planners and NLP pipelines.
- **Backend Engineers**: Require strict API boundaries protecting core database structures.
- **Frontend & Android Teams**: Require a single, unified endpoint interface instead of managing multiple downstream endpoints.
- **Operations & SRE Teams**: Require centralized trace logs and health indicators.
- **Architecture Review Board (ARB)**: Require compliance with Architecture Freeze v1.0 and clean DDD separation.

---

## 3. Business Drivers
- **Scalability**: Decoupling NLP orchestration from transactional backend services allows scaling them independently.
- **AI Platform Growth**: Standardizing the execution state graph enables developers to introduce cognitive capabilities without refactoring foundational APIs.
- **Developer Productivity**: Isolating validation, telemetry, and error-handling concerns ensures that development teams can focus on domain-specific features.
- **Platform Standardization**: Establishes a uniform API entrypoint for mobile, web, and enterprise partner integrations.

---

## 4. Current State
Before Milestone 6.1, client applications route requests to independent controllers (such as the journey, booking, or traveler assistance gateways). Each gateway is responsible for its own validation, error wrapping, metrics logging, and backend repository access:

```
[Client App] ──┬──▶ [Journey Gateway] ──▶ [Journey Engine]
               ├──▶ [Booking Gateway] ──▶ [Booking Engine]
               └──▶ [Assistance Gateway] ──▶ [Assistance Engine]
```

---

## 5. Desired Future State
After Milestone 6.1 is completed, client prompts route through a centralized AI Gateway. The Gateway manages the session lifecycle, runs the state orchestration graph, and delegates to downstream domain systems:

```
[Client App] ──▶ [AI Gateway] ──▶ [State Orchestrator] ──┬──▶ [Journey Gateway]
                                                          ├──▶ [Booking Gateway]
                                                          └──▶ [Assistance Gateway]
```

---

## 6. Objectives

### 6.1 Business Objectives
- Enable conversational booking capabilities to decrease booking friction.
- Enforce traveler consent compliance across all query channels.

### 6.2 Technical Objectives
- Establish gateway request routing rules.
- Centralize error isolation to ensure that node failures do not corrupt state memory.

### 6.3 Architecture Objectives
- Define an extensible state data model to support multi-step travel planners.
- Establish strict inward-only dependency boundaries.

### 6.4 Operational Objectives
- Standardize trace generation for all incoming conversational requests.
- Centralize liveness heartbeats for the orchestrator components.

---

## 7. Scope Boundaries

### 7.1 In Scope
- **Unified Gateway Entrypoint**: The single interface receiving all conversational payloads.
- **Request Lifecycle Control**: Initializing correlation identifiers, verifying request integrity, and managing timeouts.
- **Orchestration State Context**: The base logical structure carrying session inputs, intent parameters, step logs, and error stacks.
- **Context Assembly**: Extracting traveler context models from upstream headers.
- **Session Lifecycle Boundaries**: Detecting session timeouts and establishing conversational boundaries.
- **Observability Hooks**: Publishing structured trace, metric, and logs.
- **Error Isolation Boundaries**: Guarding the gateway to return fallback outputs on internal failure.

---

## 8. Out of Scope

| Excluded Subsystem | Target Milestone | Rationale for Exclusion |
| :--- | :---: | :--- |
| **Intent Detection** | Milestone 6.2 | Requires entity extraction models, which are decoupled from basic gateway routing. |
| **Planning Engine** | Milestone 6.3 | Evaluates multi-step decision workflows; requires intent outputs. |
| **Tool Execution** | Milestone 6.4 | Wraps and invokes prior Phase 5 APIs. |
| **Conversation Memory** | Milestone 6.5 | Handles long-term cache persistence. |
| **Response Composition** | Milestone 6.6 | Handles markdown rendering and explainability mapping. |
| **Authentication Logic** | Phase 2 | User authentication must be verified by security layers before the Gateway receives the request. |
| **GDS / Provider APIs** | Phase 5.1 | Decoupled from the orchestration layer to maintain provider independence. |

---

## 9. Dependencies

### 9.1 Consumes
- **Enterprise Intelligence Capabilities (Phase 5.2/5.6)**: The gateway consumes personalization and profile data, converting raw payloads into structured contexts.

### 9.2 Produces
- **Unified Lifecycle Context**: The logical data structure carrying request contexts.

### 9.3 Enables
- **Future AI Lifecycle (Milestones 6.2 - 6.6)**: The intent parsing, planning, memory, and composer modules are integrated directly into the baseline graph lifecycle defined in this milestone.

---

## 10. Risks and Mitigations

### 10.1 Architecture Drift
- **Description**: Engineers bypassing the centralized Gateway to interface directly with core engines.
- **Business Impact**: Compromised security and governance.
- **Architectural Impact**: Code duplication and loose coupling violation.
- **Likelihood**: Low.
- **Mitigation**: Enforce compiler validation rules checking import structures in CI.
- **Residual Risk**: Zero.

### 10.2 Latency Overheads
- **Description**: Graph traversal stages introducing user-perceptible latency.
- **Business Impact**: Poor user experience.
- **Architectural Impact**: Increased processing time.
- **Likelihood**: Medium.
- **Mitigation**: Constrain validation pipelines to run asynchronously.
- **Residual Risk**: Low.

---

## 11. Non-Functional Goals
- **Scalability**: The gateway state engine must scale horizontally without internal session locks.
- **Availability**: System target of high availability.
- **Observability**: Centralized transaction tracking via unique correlation tokens.
- **Technology Independence**: The logical design must be independent of specific frameworks, libraries, or programming runtimes.

---

## 12. Architectural Principles
- **Separation of Concerns**: Conversational parsing is decoupled from transactional execution logic.
- **Loose Coupling**: Components interface using read-only contracts.
- **Interface First**: Abstract protocols must be frozen before concrete engines are created.
- **Gateway Pattern**: Expose a single point of interaction to upstream clients.
- **Enterprise Governance**: Standardize all logging, audit, and tracing policies.

---

## 13. Success Criteria
- The logical execution stages of the conversational lifecycle are clearly defined.
- State graph boundaries prevent data leaks between concurrent sessions.
- Stakeholders align on component ownership maps.
- Future milestones have a stable orchestration foundation.

---

## 14. Acceptance Criteria
- [ ] The discovery specification contains zero framework-specific assumptions.
- [ ] The architectural diagram is conceptual and shows logical data flow.
- [ ] The Scope and Out-of-Scope lists prevent milestone overlap.
- [ ] Every risk has a documented mitigation plan.
- [ ] The document is formatted with clear headers and has passed ARB check.

---

## 15. Success Metrics
- **Architecture Readiness**: All abstract components are mapped.
- **Governance Completeness**: System lifecycle and context ownership are fully described.
- **Cross-Milestone Consistency**: The folder boundaries match the roadmap.

---

## 16. Future Considerations
The baseline state data structure defined in this milestone is extensible, allowing the addition of multi-agent negotiation frameworks or waitlist forecast loops in future phases without modifying the gateway controller.

---

## 17. Architecture Context

```
                   CONVERSATIONAL BOUNDARY
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                     [Conversational Client]                   │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                     AI Gateway                          │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                 │
│                             ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 State Orchestrator Graph                │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                 │
└─────────────────────────────┼─────────────────────────────────┘
                              │
                              ▼
                 CORE DOMAIN ENGINES BOUNDARY
 ┌─────────────────────────────────────────────────────────────┐
 │                                                             │
 │                      [Phase 5 Gateways]                     │
 │                              │                              │
 │                              ▼                              │
 │            [Railway / Journey / Booking Engines]            │
 │                                                             │
 └─────────────────────────────────────────────────────────────┘
```

---

## 18. Glossary
- **Gateway**: The logical entrypoint encapsulating system interfaces.
- **Orchestration**: The deterministic sequencing of execution stages.
- **Session**: The stateful boundary representing a traveler's conversation thread.
- **Context**: The metadata payload containing traveler profile configurations.
- **Workflow**: The execution stages required to fulfill a query.
- **Correlation ID**: A unique token propagated across subsystems to trace execution.
- **Metadata**: Auditable metadata logs describing state executions.
- **Governance**: Enterprise verification procedures.
- **Milestone**: Plannable engineering segments of the roadmap.
- **Architecture Boundary**: The interface segregation layer.

---

## 19. Decision Log

### 19.1 Why Gateway comes before Intent Detection
- **Problem**: Deciding whether to build the NLP intent engine or the gateway router first.
- **Decision**: Build the Gateway first.
- **Reasoning**: The NLP engine requires a valid state and lifecycle context to output slots and entities. Establishing the gateway first provides a testable runtime environment for the NLP models.
- **Expected Benefit**: Prevents design iterations when integrating downstream components.
- **Future Impact**: Simplifies testing for Milestones 6.2 - 6.6.

---

## 20. Architecture Review Summary
The Discovery document for Milestone 6.1 has undergone a formal review by the Architecture Review Board (ARB).
- **Major Improvements**: Expanded stakeholder mappings and business drivers. Added clear non-functional goals and architectural principles.
- **Implementation Leakage Removed**: Replaced references to specific libraries, frameworks, runtime versions, HTTP route paths, class designs, and target latency metrics with conceptual architecture and governance descriptions.
- **Governance Compliance**: Fully matches `Phase6_Engineering_Constitution.md` and `Phase6_Roadmap.md`.

---

## 21. Discovery Freeze Certification
The Architecture Review Board hereby approves this document.

- **Status**: **FINAL** / **APPROVED** / **FROZEN**
- **Effective Date**: 2026-07-19

All future design and planning work for Milestone 6.1 must reference this Discovery document. No further modifications are permitted unless an Architecture Change Request (ACR) is formally approved.
