# RailYatra AI Platform
# Phase 6 Strategic Roadmap
## AI-Native Orchestration Layer Evolution

---

## Document Control
- **Document Reference**: RY-P6-RDMP-1.0
- **Version**: 1.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: APPROVED / ACTIVE
- **Pre-requisite Reference**: `Phase6_Engineering_Constitution.md`

---

## Executive Summary
This document defines the strategic engineering roadmap for **Phase 6 (AI-Native Orchestration Layer)** of the RailYatra AI Platform. Following the structural isolation constraints of **Architecture Freeze v1.0**, Phase 6 introduces cognitive orchestration, natural intent parsing, multi-step planning, tool invocation workflows, contextual conversation memory, and explainable response composers. 

These milestones compose the cognitive orchestration wrapper sitting on top of the frozen Phase 5 intelligence engines, enabling conversational capabilities without sacrificing deterministic safety boundaries.

---

## Table of Contents
1. [Phase 6 Vision](#1-phase-6-vision)
2. [Phase Objectives](#2-phase-objectives)
3. [Phase Scope](#3-phase-scope)
4. [Milestone Hierarchy (6.1 → 6.6)](#4-milestone-hierarchy-61--66)
5. [Dependency Graph & Critical Path](#5-dependency-graph--critical-path)
6. [Architectural Boundaries](#6-architectural-boundaries)
7. [Cross-Milestone Interaction](#7-cross-milestone-interaction)
8. [System Evolution](#8-system-evolution)
9. [Risk Analysis Matrix](#9-risk-analysis-matrix)
10. [Implementation Order](#10-implementation-order)
11. [Success Metrics](#11-success-metrics)
12. [Phase Completion Criteria](#12-phase-completion-criteria)
13. [Future Phase Preparation](#13-future-phase-preparation)
14. [Visual System Diagrams](#14-visual-system-diagrams)
15. [Glossary](#15-glossary)

---

## 1. Phase 6 Vision
The primary transformation of Phase 6 is to evolve RailYatra AI from an **analytical intelligence engine** into an **AI-native conversational orchestration platform**. 

In Phase 5, the platform implemented deterministic business calculation engines (Railway, Journey, Booking, Assistance, Personalization). In Phase 6, the system wraps these engines inside a cognitive orchestration layer. The conversational engine (LLM planner & LangGraph state workflow) interprets natural language traveler inputs, translates them into structured query parameters, calls the deterministic sub-engines, and translates output decisions back into localized, personalized conversational answers.

---

## 2. Phase Objectives
- **Primary Objective**: Implement the complete cognitive execution wrapper (Gateway, Intent, Planning, Tool, Memory, and Composer).
- **Secondary Objective**: Maintain strict separation between conversational reasoning and transactional booking logic.
- **Business Goal**: Enable natural-language booking and assistance queries, increasing user retention and booking conversion.
- **Technical Goal**: Achieve latency budgets under $\le 500\text{ms}$ for intent parsing and plan orchestration (exclusive of LLM execution).
- **Operational Goal**: Provide 100% trace visibility for every agent action, tool call, and state transition.

---

## 3. Phase Scope

### 3.1 In Scope
- Natural language intent classification and entities extraction.
- LangGraph-based conversational state machine flow.
- Parallel tool invocation mapping for Phase 5 gateways.
- Multi-session short-term and long-term conversation memory context.
- Localized response composition and explainability injection.

### 3.2 Out of Scope
- Neural network fine-tuning or training.
- Dynamic tool generation (only registered tools can be called).
- Direct GDS booking transactions by LLMs (must consume Phase 5.4/5.6 output packages).

---

## 4. Milestone Hierarchy (6.1 → 6.6)

### Milestone 6.1: AI Gateway & Orchestration Foundation
* **Purpose**: Establish the LangGraph state machine structure and endpoint gateway.
* **Responsibilities**: Session token verification, LangGraph state schema definition, input validation.
* **Deliverables**: FastAPI AI Gateway controller, baseline Graph state.
* **Dependencies**: None.
* **Success Criteria**: Integration tests pass; API success rate $\ge 99.5\%$.
* **Out of Scope**: LLM API integration.

### Milestone 6.2: Intent Understanding Engine
* **Purpose**: Parse raw message prompts into semantic intents and parameter entities.
* **Responsibilities**: Intent classification, slot filling (origin, destination, date-time, traveler_id).
* **Deliverables**: NLP Intent Classifier, slot-filling extractor, entity DTOs.
* **Dependencies**: Milestone 6.1.
* **Success Criteria**: Parse validation accuracy $\ge 95\%$.
* **Out of Scope**: Multi-step trip planning.

### Milestone 6.3: Planning & Decision Engine
* **Purpose**: Synthesize multi-step execution plans from parsed intents.
* **Responsibilities**: Plan generation, query parameter building, conflict mapping.
* **Deliverables**: Planning Engine, Plan validation rules.
* **Dependencies**: Milestone 6.2.
* **Success Criteria**: Deterministic constraint safety rules enforced.
* **Out of Scope**: Tool executions.

### Milestone 6.4: Tool & Workflow Orchestrator
* **Purpose**: Execute plans by invoking Phase 5 gateway adapters in proper order.
* **Responsibilities**: Parallel execution routing, pipeline adapter interfaces.
* **Deliverables**: Tool registry, Adapter client layer.
* **Dependencies**: Milestone 6.3.
* **Success Criteria**: Tool call success rates $\ge 99.8\%$.
* **Out of Scope**: Response formatting.

### Milestone 6.5: Conversation Memory Platform
* **Purpose**: Retain state and user session context across multiple prompts.
* **Responsibilities**: Short-term session buffer caching, long-term profile preferences synchronization.
* **Deliverables**: Memory store (Redis/DB adapter), Session context managers.
* **Dependencies**: Milestone 6.4.
* **Success Criteria**: Retrieval latency $\le 5\text{ms}$.
* **Out of Scope**: User profiling.

### Milestone 6.6: Response Composer & Explainability
* **Purpose**: Translate tool decisions into markdown responses injected with explainability logs.
* **Responsibilities**: Text formatting, localization, reason code explanation injection.
* **Deliverables**: Response Composer class, Template renderer.
* **Dependencies**: Milestone 6.5.
* **Success Criteria**: Every response includes explainability links.
* **Out of Scope**: Raw prompt modification.

---

## 5. Dependency Graph & Critical Path

```
   [M6.1: Foundation]
           │
           ▼
   [M6.2: Intent Engine]
           │
           ▼
   [M6.3: Planning Engine]
           │
           ▼
   [M6.4: Tool Orchestrator]
           │
           ▼
   [M6.5: Memory Platform]
           │
           ▼
   [M6.6: Response Composer]
```

- **Critical Path**: Linear milestones execution order (6.1 $\rightarrow$ 6.2 $\rightarrow$ 6.3 $\rightarrow$ 6.4 $\rightarrow$ 6.5 $\rightarrow$ 6.6) to guarantee that state schema, intent objects, tool execution blocks, memory contexts, and output writers are fully validated.

---

## 6. Architectural Boundaries

| Milestone | Owns | Consumes | Exposes | Does Not Own |
| :--- | :--- | :--- | :--- | :--- |
| **6.1** | LangGraph State Schema | Raw HTTP requests | `/chat` endpoint | NLP models |
| **6.2** | Intent Classification DTO | Raw user prompt | `IntentDTO` | State flow |
| **6.3** | Decision Plan sequence | `IntentDTO` | `PlanDTO` | Adapter tools |
| **6.4** | Tool execution client | `PlanDTO` | Sub-engine DTOs | Planning logic |
| **6.5** | Session context cache | Session ID | `MemoryContext` | Core database |
| **6.6** | Markdown template engine | Tool outputs & Memory | User message | Decision traces |

---

## 7. Cross-Milestone Interaction

```
[User Prompt] ──► AI Gateway (6.1) ──► Intent Engine (6.2) ──► Planning (6.3)
                                                                     │
  Response ◄── Composer (6.6) ◄── Memory (6.5) ◄── Tool Orchestration (6.4)
                                                               │
                                                       [Phase 5 Gateways]
```

---

## 8. System Evolution
- **Current State**: Users perform query searches using standard APIs. Personalization is applied via backend adapters.
- **Phase 6 State**: Cognitive state machines manage complex sessions (e.g. "Rebook my train to Bhopal and select a lower berth if available").
- **Future State**: Phase 7 expands capability to autonomous multi-agent cooperation and real-time waitlist predictive trading optimization.

---

## 9. Risk Analysis Matrix

| Identified Risk | Severity | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **LLM Latency Jitter** | High | Medium | Implement aggressive streaming and chunk caching. |
| **State Bloat** | Medium | Low | Restrict short-term memory TTL to 2 hours. |
| **Hallucination** | High | High | Enforce strict schemas and validation on all output variables. |

---

## 10. Implementation Order
1. **Milestone 6.1 & 6.2**: Establish the base router and conversational intent classification.
2. **Milestone 6.3 & 6.4**: Build the planner and map Phase 5 gateways as structured tool plugins.
3. **Milestone 6.5 & 6.6**: Add session memory caching and localized markdown response writing.

---

## 11. Success Metrics
- **NLP Intent Accuracy**: $\ge 95\%$ on mock booking datasets.
- **Latency Overheads**: Plan construction $\le 100\text{ms}$ ($p95$).
- **Explainability coverage**: 100% of personalized recommendations contain reason templates.

---

## 12. Phase Completion Criteria
- [ ] All 6 milestones pass unit, integration, and scenario regression checks.
- [ ] Mypy static typing returns zero typing errors.
- [ ] Architectural boundaries are verified via lint check assertions.
- [ ] All documentation files are signed off and saved under `docs/phase6/`.

---

## 13. Future Phase Preparation
Phase 6 sets the stage for Phase 7 (Prediction & Waitlist Trading Platform) by standardizing state schemas and tool interfaces. The LangGraph orchestration baseline allows adding predictive agent modules without refactoring the core gateway or parser logic.

---

## 14. Visual System Diagrams

### High-Level Execution Lifecycle

```
[User Request]
      │
      ▼
┌───────────┐
│ AI Gateway│ (Validate session, initialize state context)
└─────┬─────┘
      │
      ▼
┌───────────┐
│Intent/NLP │ (Extract intent code, fill slot parameters)
└─────┬─────┘
      │
      ▼
┌───────────┐
│  Planner  │ (Synthesize plan steps and validate constraints)
└─────┬─────┘
      │
      ▼
┌───────────┐
│ Tool Exec │ (Invoke Phase 5 interfaces: Journey/Booking/Assistance)
└─────┬─────┘
      │
      ▼
┌───────────┐
│Memory Sync│ (Store session state to Redis / fetch history)
└─────┬─────┘
      │
      ▼
┌───────────┐
│ Composer  │ (Hydrate explainability templates, render Markdown)
└─────┬─────┘
      │
      ▼
[Response Output]
```

---

## 15. Glossary
- **LangGraph**: Orchestration library utilized to define state graph transitions.
- **Entity Slot Filling**: Process of isolating variables (dates, station codes) from raw text prompts.
- **Explainability Templates**: Dynamic response text strings containing validation audit logs.
- **Tool Registry**: System catalog listing all runnable interfaces from prior phases.
