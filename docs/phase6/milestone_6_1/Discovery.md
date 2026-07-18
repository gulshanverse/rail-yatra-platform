# Phase 6 - Milestone 6.1 Discovery
## AI Gateway & Orchestration Foundation

---

## Document Control
- **Document Reference**: RY-P6-M6.1-DISC-1.0
- **Version**: 1.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: APPROVED / ACTIVE
- **Governing Reference**: `Phase6_Engineering_Constitution.md`

---

## Executive Summary
Milestone 6.1 introduces the core conversational orchestration entrypoint, the **AI Gateway & Orchestration Foundation**. In Phase 5, RailYatra AI implemented decoupled, highly specialized analytical engines (Railway, Journey, Booking, Assistance, Personalization). However, these engines lack a centralized entrypoint, session manager, context validator, or cognitive flow runner. 

Milestone 6.1 establishes the foundation to coordinate all future cognitive tasks (intent parsing, multi-step planning, tool adapter executes, conversation memory caches, and response composition) by defining a LangGraph state graph runner and API Gateway facade.

---

## Table of Contents
1. [Business Context](#1-business-context)
2. [Technical Context](#2-technical-context)
3. [Objectives](#3-objectives)
4. [Scope Boundaries](#4-scope-boundaries)
5. [Out of Scope](#5-out-of-scope)
6. [Dependencies](#6-dependencies)
7. [Risks and Mitigations](#7-risks-and-mitigations)
8. [Assumptions](#8-assumptions)
9. [Constraints](#9-constraints)
10. [Success Criteria](#10-success-criteria)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Future Considerations](#12-future-considerations)
13. [Architecture Context](#13-architecture-context)
14. [Review Checklist](#14-review-checklist)
15. [Approval Sign-off](#15-approval-sign-off)
16. [Discovery Freeze Declaration](#16-discovery-freeze-declaration)

---

## 1. Business Context

### 1.1 Current Limitations
Currently, downstream user interfaces interact with individual, disconnected domain API endpoints. There is no conversational workflow orchestrator that can accept a natural language request, run multiple steps in the background, aggregate results, and output a friendly answer.

### 1.2 Strategic Value of Orchestration
- **Scale**: Enables adding conversational modules without modifying the core NestJS backend server or exposing raw domain databases.
- **Developer Velocity**: Establishes a standard routing baseline, decoupling the prompt engineering cycle from API endpoint modifications.
- **User Agency**: Serves as the single cognitive coordinator that translates multi-criteria preferences and constraints into structured operations.

---

## 2. Technical Context

### 2.1 Core Problems Solved
- **No Unified Request Lifecycle**: Requests lack lifecycle tracking, correlation IDs, or timeout controls.
- **No Context Verification**: No boundary validation checks traveler profile consent before dispatching query details.
- **No Session Context Caching**: App calls execute statelessly without retaining conversation history.
- **No Heartbeat Monitors**: No health checking checks the readiness of the graph executors before routing traffic.

---

## 3. Objectives

### 3.1 Primary Objectives
- Establish the `AI Gateway` entrypoint controller.
- Initialize the baseline LangGraph state graph layout schema.

### 3.2 Secondary Objectives
- Define session extraction pipelines and metadata parameters.
- Expose basic status health checks.

### 3.3 Business & Operational Objectives
- Standardize developer interfaces for NLP and planning plugins.
- Log latency, invocation metrics, and errors.

---

## 4. Scope Boundaries

### 4.1 In Scope
- **AI Gateway Interface**: Single HTTPS entrypoint receiving chat prompt requests.
- **LangGraph State initialization**: Defines the schema context (traveler_id, raw_prompt, current_intent, plan_steps, session_history, error_logs).
- **Session Identification**: Standard headers checks for extracting user tokens.
- **Correlation ID Injection**: Ensuring trace propagation across downstream calls.
- **Latency Budgeting**: Gateway monitoring bounds sync pipelines to $\le 100\text{ms}$ overhead (excluding LLM execution time).
- **Observability Logging**: Logging gateway error boundaries and metric counts.

---

## 5. Out of Scope
- **Intent Parsing & NER**: Classifying prompt actions is deferred to Milestone 6.2.
- **Planning Engines**: Creating plan step objects is deferred to Milestone 6.3.
- **Tool Adaptations**: Invoking Phase 5 engines is deferred to Milestone 6.4.
- **Redis Memory Cache**: Persisting state across sessions is deferred to Milestone 6.5.
- **Response Composers**: Formatting final responses is deferred to Milestone 6.6.

---

## 6. Dependencies
- **Phase 5 Gateways**: Exposes read-only adapters matching canonical schemas (e.g. `PersonalizationGateway`, `TravelerAssistanceGateway`).
- **Milestone 6.2 through 6.6**: Consumes the LangGraph state schema and router initialized in this milestone.

---

## 7. Risks and Mitigations

| Identified Risk | Severity | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **Pipeline Latency Bottleneck** | Medium | High | Restrict gateway validations to basic headers checks. |
| **State Jitter** | Low | Medium | Enforce strict schema constraints in the base Graph layout. |

---

## 8. Assumptions
- The Python virtual environment runtime uses Python 3.14.
- Security tokens (JWT) are validated by NestJS before routing calls to the AI Service.

---

## 9. Constraints
- The codebase must be 100% compliant with **Architecture Freeze v1.0**.
- The FastAPI orchestrator must run statelessly to support container scaling.

---

## 10. Success Criteria
- The LangGraph state model is compiled without syntax errors.
- The AI Gateway exposes `/chat` routing paths.
- All testing checks pass.

---

## 11. Acceptance Criteria
- [ ] The `AIReadyPersonalizationContext` is read-only.
- [ ] Heartbeat checks verify baseline FastAPI gateway status.
- [ ] All Ruff, MyPy, and PyTest checks are green.

---

## 12. Future Considerations
The baseline Graph state layout is structured to support slot extraction (6.2), planning schemas (6.3), adapter tool wrappers (6.4), memory sync (6.5), and renderer composers (6.6) without refactoring the gateway controller.

---

## 13. Architecture Context

```
[User Chat Request]
      │
      ▼
┌──────────────┐
│  AI Gateway  │  ◄── [M6.1 ENTRYPOINT]
└──────┬───────┘
       │ Extracts session, validates token
       ▼
┌──────────────┐
│  LangGraph   │  (Manages State, executes Intent/Planning/Tool stages)
└──────────────┘
```

---

## 14. Review Checklist
- [ ] Does this document omit planning/API signatures? (Yes)
- [ ] Are GDS/external systems decoupled? (Yes)
- [ ] Are out-of-scope boundaries respected? (Yes)

---

## 15. Approval Sign-off
- **Lead Architect**: Core ARB Committee
- **Timestamp**: 2026-07-19T01:38:05Z
- **Status**: APPROVED

---

## 16. Discovery Freeze Declaration
This Discovery specification is formally **FROZEN** and serves as the baseline for Milestone 6.1.
