# Milestone 6.3 Technical Walkthrough
## Planning & Decision Engine

This document provides a detailed overview of the package structure, execution flows, and engineering decisions implemented for the Planning & Decision Engine under Milestone 6.3.

---

## 1. Codebase Overview and Package Maps

All new capability files reside under `apps/ai-service/app/planner/`. 

### Module Descriptions
- [errors.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/errors.py): Custom domain exception hierarchy mapping formatting, sequencing, and policy errors.
- [interfaces.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/interfaces.py): Python `Protocol` interfaces mapping `IStepSequencer`, `IPlanValidator`, `ISpecification`, `IClarificationHandler`, and `IPlanningCoordinator` implementations.
- [models.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/models.py): Canonical domain entities (`PlanStep`), value objects (`Constraint`, `Decision`, `ValidationReport`), and aggregate root (`StructuredTravelPlan`) modeled using Pydantic. Implements Pydantic model validation checks for aggregate invariants (minimum step count, ordered steps, and double-booking checks).
- [registry.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/registry.py): Whitelisted registry of approved functions preventing execution injection vectors.
- [factory.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/factory.py): Factory orchestrating UUID generation, default status flags, and timestamps for new aggregates.
- [events.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/events.py): Domain event schemas (`PlanFormulated`, `PlanVerified`, `PlanConflictDetected`) mapping trace correlation IDs.
- [specifications.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/specifications.py): Isolated rules checking age concession thresholds, 45-minute connection layovers, and same-day travel overlaps.
- [policies.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/policies.py): Platform guardrails evaluating lockout times (4 hours before departure) and identity safety proxy checks.
- [sequencer.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/sequencer.py): StepSequencer matching classified intents to pre-built multi-step templates.
- [validator.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/validator.py): PlanValidator reviewing plans against specifications and logging decision logs.
- [clarification.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/clarification.py): Handler mapping missing intent slots to request clarification steps.
- [coordinator.py](file:///c:/Users/Gulshan%20Kumar/OneDrive/Documents/Desktop/Rail-Yatra/apps/ai-service/app/planner/coordinator.py): Facade entry service managing step sequencer, factory, validator, and events publication.

---

## 2. Control and Data Flow Paths

```
       [IntentDescriptor] (Input)
               │
               ├───► [needs_clarification == True] ──► [ClarificationHandler]
               │                                               │
               │                                               ▼
               │                                    [StructuredTravelPlan]
               │                                 (Status: NEEDS_CLARIFICATION)
               │
               └───► [needs_clarification == False]
                               │
                               ▼
                        [StepSequencer]  ──► (Verify whitelists)
                               │
                               ▼
                   [StructuredTravelPlanFactory]
                               │
                               ▼ (Draft Plan)
                         [PlanValidator] ──► (Run specifications & policies)
                               │
                               ▼
                     [StructuredTravelPlan] (Output)
                  (Status: VALIDATED | REJECTED)
```

### Execution Flow Details
1. **Intake Gate**: Callers submit `IntentDescriptor` containing slots and user context.
2. **Ambiguity Gate**: If `needs_clarification` is set, `ClarificationHandler` is called. It wraps missing slots in a single `request_clarification` step.
3. **Sequencing Gate**: If slots are sufficient, `StepSequencer` translates the intent family to step chains (`plan_travel`, `check_pnr`, or `journey_intelligence`).
4. **Safety Filter**: Every step function name is verified against the registry.
5. **Aggregate Construction**: Factory instantiates `StructuredTravelPlan` with random UUID, trace ID, status `DRAFT`, and timestamps.
6. **Validation Gate**: `PlanValidator` runs specification rules (age limits, layout buffers, overlapping times) and domain policies (4-hour lockout limits, authorization matching).
7. **Sign-off**: Plan is signed as `VALIDATED` or `REJECTED` and validation logs are populated.
8. **Event Publication**: Coordinator publishes `PlanFormulated`, `PlanVerified`, or `PlanConflictDetected` events to the platform context.

---

## 3. Design Decisions and Core Rationale

### 1. Stateless Plan Formulation (ADR-M6.3-002)
* **Decision**: Complete database-independent, in-memory processing inside the planner package.
* **Rationale**: Eliminates transactional locking overheads and scaling limits. Session database serialization is decoupled and delegated to downstream memory modules.

### 2. Decoupled Policy Validation Gate (ADR-M6.3-001)
* **Decision**: All plans must clear a centralized validation gate before execution, returning validation reports mapping Decisions and Constraints.
* **Rationale**: Prevents calling downstream APIs or initiating financial booking flows for requests that violate rules, protecting the platform from cost waste.

---

## 4. Known Boundaries and Extension Limits

### Service whitelists
The registry provides a secure boundary limit. To allow new capabilities (e.g. cab booking or hotel reservation), the service must be explicitly registered in `ApprovedFunctionRegistry` at startup, and templates must be updated in `StepSequencer` to include the new capability.

### Memory coordination
State modification across dialog turns is deferred to Milestone 6.5 (Memory Platform). The planner relies strictly on the caller providing complete intent parameters per execution cycle.
