# Milestone 6.4 Technical Walkthrough
## Execution Engine

This document provides a detailed overview of the package structure, execution flows, and engineering decisions implemented for the Execution Engine under Milestone 6.4.

---

## 1. Codebase Overview and Package Maps

All new capability files reside under `apps/ai-service/app/execution/`. 

### Module Descriptions
- [errors.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/errors.py): Custom domain exception hierarchy mapping formatting, transition, idempotency, and compensation errors.
- [interfaces.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/interfaces.py): Python `Protocol` interfaces mapping `IRailwayAdapter`, `IExecutionSessionRepository`, `IEventPublisher`, `ISpecification`, and `IExecutionCoordinator`.
- [models.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/models.py): Canonical domain entities (`ExecutionStepTracker`), value objects (`ExecutionToken`, `RetryPolicy`), and aggregate root (`ExecutionSession`) modeled using Pydantic. Implements Pydantic model validation and state transition guards for aggregate invariants (terminal state immutability, single active state transition validation).
- [adapters.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/adapters.py): Mock implementation of the railway adapter capability contracts mapping abstract Reservation, Cancellation, and Availability Verification calls.
- [events.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/events.py): Domain event schemas (`ExecutionStarted`, `ExecutionPaused`, `ExecutionResumed`, `ExecutionCancelled`, `ExecutionTimedOut`, `StepExecutionSucceeded`, `StepExecutionFailed`, `ReversalInitiated`, `CompensationCompleted`, `ManualInterventionRequested`, `ExecutionRecovered`, `ExecutionAborted`, `ExecutionFinalized`) mapping session details.
- [policies.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/policies.py): Platform guardrails evaluating Controlled Retry Policies (progressive delay and jitter) and Strict Reversal Sequence Policies (exact reverse chronological order of step execution).
- [specifications.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/specifications.py): Specifications assessing if execution is authorized and if compensation rollbacks are required.
- [compensation.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/compensation.py): CompensationOrchestrator managing backward rollbacks when a step fails.
- [coordinator.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/execution/coordinator.py): Saga orchestrator coordinator managing execution session lifecycle, step dispatches, retries, and events.

---

## 2. Control and Data Flow Paths

```
    [Validated StructuredTravelPlan] (Input) + [ExecutionToken]
                       │
                       ▼
            [ExecutionCoordinator]  ◄──► (Verify Idempotency)
                       │
                       ▼
          [ExecutionSessionFactory] (Aggregate instantiation)
                       │
                       ▼ (Verification Specifications check)
       [ReadyToExecuteSpecification]  ──► [False] ──► [Aborted]
                       │
                       ▼ [True]
              [ExecutionSession]
             (Status: PROCESSING)
                       │
                       ▼
            [Saga Execution Loop]
                       │
                       ├──► [Get Runnable steps] (Prerequisites met)
                       ├──► [Dispatch to Adapters] (Mock API calls)
                       ├──► [Success] ──► Loop next step
                       │
                       └──► [Failure] ──► (Controlled Retry Policy)
                                             │
                                             ▼ (Retries Exhausted)
                              [CompensationRequiredSpecification]
                                             │
                                             ├─► [True] ─► [CompensationOrchestrator]
                                             │                    │
                                             │                    ▼
                                             │             [Reverted/Aborted]
                                             │
                                             └─► [False] ─► [Failed]
```

---

## 3. Design Decisions and Core Rationale

### 1. Stateful Saga Orchestration (ADR-M6.4-001)
* **Decision**: Implement a stateful Saga coordinator utilizing explicit transitions rather than stateless loops.
* **Rationale**: Sagas allow precise tracking of partial executions, enabling correct trigger matching for reverse rollback sequences.

### 2. Idempotency Gate (ADR-M6.4-002)
* **Decision**: Validate execution session creations using an ExecutionToken value object.
* **Rationale**: Completely eliminates double-booking or double-billing risk when conversational interfaces submit duplicate actions.

### 3. Reversal Sequence Policy (ADR-M6.4-003)
* **Decision**: Compensation steps run in exact reverse sequence order of successful completions.
* **Rationale**: Reverting bookings in reverse order guarantees that dependent legs are canceled before parent bookings, complying with IRCTC travel rules.

---

## 4. Testing Summary

Comprehensive pytest coverage was implemented in [test_execution.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/tests/test_execution.py) verifying happy paths, transient failures, retry limits, reverse rollback ordering, and double-booking specification integrations.
