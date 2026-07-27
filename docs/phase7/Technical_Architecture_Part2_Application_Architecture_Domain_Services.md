# RailYatra AI Platform
## Phase 7 – Predictive Intelligence Platform
### Technical Architecture Part 2 – Application Architecture, Domain Services & Interaction Architecture

```
================================================================================
Document Type:      Technical Architecture (Application Architecture & Interaction)
Phase:              7 – Predictive Intelligence Platform
Version:            1.0
Status:             TECHNICAL BASELINE APPROVED
Domain:             Application Architecture, Domain Services, Orchestration, Event Patterns
Target Audience:    Solution Architects, Software Engineering Leads, Platform Architects
================================================================================
```

---

# SECTION 1 — APPLICATION ARCHITECTURE OVERVIEW

## 1.1 Overview
The Application Architecture for Phase 7 defines the structure, behavior, and interfaces of the application layer. It focuses on how individual domain services interact synchronously and asynchronously to support predictive travel scenarios.

## 1.2 Architectural Objectives
*   **Decoupled Operation**: Ensure domain services can be updated and redeployed independently.
*   **High Cohesion**: Align system service responsibilities with specific business domains.
*   **Resiliency**: Enforce circuit breaking and fallback rules across all inter-service queries.

## 1.3 Decomposition Strategy
Services are isolated by domain. The architecture uses an **API Gateway** as the single entry point, orchestrating requests through a central **Journey Orchestration Service** or dispatching events through an **Event Mesh**.

```
+---------------------------------------------------------------------------------+
|                                   CLIENTS                                       |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                                  API GATEWAY                                    |
+---------------------------------------------------------------------------------+
      |                                                                     |
      | (Sync Orchestration)                                                | (Async Events)
      v                                                                     v
+-----------------------------+                                     +-------------+
| Journey Orchestrator Service|                                     |  Event Mesh |
+-----------------------------+                                     +-------------+
      |               |                                                     |
      v               v                                                     v
+-----------+   +-----------+                                         +-----------+
| Passenger |   | Journey   |                                         | Learning  |
| Service   |   | Service   |                                         | Service   |
+-----------+   +-----------+                                         +-----------+
      |               |                                                     |
      v               v                                                     v
+-----------+   +-----------+                                         +-----------+
| Prediction|   | Risk      |                                         | Analytics |
| Service   |   | Service   |                                         | Service   |
+-----------+   +-----------+                                         +-----------+
```

---

# SECTION 2 — DOMAIN SERVICE ARCHITECTURE

The core domain services are defined below:

1. **Passenger Service**:
   *   *Purpose*: Manages passenger preferences, context, and privacy records.
   *   *Responsibilities*: Retrieves passenger state, evaluates trip-day context.
   *   *Capabilities Supported*: Passenger Profile, Consent registry.
   *   *Logical Dependencies*: Identity Service.
   *   *Service Ownership*: Passenger Team.
   *   *Interaction Boundaries*: Exposes sync RPC for profile data.

2. **Journey Service**:
   *   *Purpose*: Manages live schedules and transit telemetry.
   *   *Responsibilities*: Coordinates timetable schedules, tracks active train coordinates.
   *   *Capabilities Supported*: Timetable management, telemetry tracking.
   *   *Logical Dependencies*: Ingestion Service.
   *   *Service Ownership*: Journey Team.
   *   *Interaction Boundaries*: Publishes schedule change events.

3. **Prediction Service**:
   *   *Purpose*: Generates confirmation probabilities and arrival estimations.
   *   *Responsibilities*: Executes ML models, evaluates confidence ranges.
   *   *Capabilities Supported*: Waitlist forecasting, delay estimation.
   *   *Logical Dependencies*: Journey Service, Passenger Service.
   *   *Service Ownership*: Prediction Team.
   *   *Interaction Boundaries*: Exposes forecasting endpoints.

4. **Recommendation Service**:
   *   *Purpose*: Selects alternative travel paths.
   *   *Responsibilities*: Screens fallback paths, optimizes ticket conversions.
   *   *Capabilities Supported*: Fallback routing, offer optimization.
   *   *Logical Dependencies*: Risk Service, Passenger Service.
   *   *Service Ownership*: Growth & Monetization Team.
   *   *Interaction Boundaries*: Exposes alternate offer interfaces.

5. **Risk Service**:
   *   *Purpose*: Evaluates journey path reliability.
   *   *Responsibilities*: Calculates connection risk index.
   *   *Capabilities Supported*: Risk evaluation.
   *   *Logical Dependencies*: Prediction Service.
   *   *Service Ownership*: Platform Operations Team.
   *   *Interaction Boundaries*: Publishes connection danger alarms.

---

# SECTION 3 — APPLICATION COMPONENT COLLABORATION

The following collaboration diagram illustrates the sequence of service calls during a connection risk scenario:

```
Passenger App      Orchestrator      Journey Service      Prediction Service      Risk Service      Recommendation
     |                   |                  |                     |                    |                   |
     |--[1. Search]-->   |                  |                     |                    |                   |
     |                   |--[2. Fetch Live]-|                     |                    |                   |
     |                   |------------------[3. Estimate Delay]-->|                    |                   |
     |                                                            |--[4. Risk Score]-->|                   |
     |                                                                                 |--[5. Alts Request]|
     |<-----------------[6. Return Calibrated Offer Package]-----------------------------------------------|
```

*   **Trigger**: Passenger searches for segment details.
*   **Flow**: Journey Orchestrator pulls live train statuses, queries Prediction Service for delay spreads, feeds delay outputs to Risk Service, and queries Recommendation Service for fallbacks if risk is high.
*   **Responsibility**: Each service computes its specific domain output (e.g., Risk Service owns threshold calculations).
*   **Outcome**: The client receives an explainable delay forecast with recommended fallback plans.

---

# SECTION 4 — ORCHESTRATION ARCHITECTURE

The application uses a **hybrid orchestration and choreography pattern**:
*   *Synchronous Orchestration*: Used during passenger search queries. The **Journey Orchestration Service** coordinates Passenger, Journey, and Prediction services to return real-time forecasts within low latency boundaries.
*   *Asynchronous Choreography*: Used for updates and continuous learning. When a train arrives at a station, the Journey Domain publishes a `JourneyCompleted` event. The Learning Service reacts asynchronously to retrain models without blocking the active operational services.

---

# SECTION 5 — EVENT INTERACTION ARCHITECTURE

The conceptual flow of events across the platform is defined below:

*   **Passenger Request**: Triggers profile context lookup.
*   **Journey Context Updated**: Schedules are checked for current deviations.
*   **Prediction Requested**: Ingests schedule metrics to run forecasting models.
*   **Prediction Generated**: Publishes confirmation and delay estimations to the Event Mesh.
*   **Risk Evaluated**: Evaluates delay impacts on traveler routes.
*   **Recommendation Produced**: Generates fallback suggestions.
*   **Decision Recorded**: Logs passenger accept/reject choices.
*   **Learning Triggered**: Integrates outcomes to retrain prediction weights.

---

# SECTION 6 — QUALITY ATTRIBUTE REALIZATION

*   **Scalability**: Services scale horizontally. The Prediction Service runs stateless instances behind a load balancer, allowing the system to handle travel rushes.
*   **Reliability**: Handled by caching delay states. In case of telemetry loss, the system degrades gracefully to static schedules.
*   **Availability**: Realized through hot-warm component replication. Logical services must deploy redundant instances across distinct failure regions.
*   **Explainability**: Achieved by forcing all prediction responses to contain explanation metadata. No raw numbers are sent directly to clients.
*   **Privacy**: Enforced by auditing DPDP consent records inside the API Gateway layer.

---

# SECTION 7 — ARCHITECTURAL PATTERNS

*   **Layered Architecture**: Isolates client interactions from business logic and database queries.
*   **Domain-Driven Design (DDD)**: Defines bounded contexts around Passenger, Journey, and Prediction domains, keeping models focused and clean.
*   **Event-Driven Collaboration**: Integrates subsystems using asynchronous events, reducing tight coupling.
*   **Orchestration Pattern**: Centralizes client query flows to guarantee low latency.

---

# SECTION 8 — CROSS-CUTTING ARCHITECTURE

*   **Identity & Authorization**: Every request carries an identity token asserting client scopes. Only authorized roles can trigger predictions.
*   **Observability**: Tracked via correlation IDs. Every passenger flow inherits a unique ID to trace execution paths across domains.
*   **Error Management**: Service faults must map to standardized logical exceptions (e.g., `PredictionUnavailable`, `ConsentNotGiven`).

---

# SECTION 9 — ARCHITECTURE DECISION RECORD

*   **ADR-02: Synchronous Orchestrator for Queries**
    *   *Decision*: Use a dedicated Journey Orchestration Service for passenger query paths.
    *   *Context*: Passengers require real-time forecasts. Async choreography would introduce too much latency.
    *   *Alternatives*: Event-driven choreography for search paths (rejected due to latency overheads).
    *   *Rationale*: Centralizing orchestration for sync flows ensures we meet the 200ms latency targets.

---

# SECTION 10 — APPLICATION TARGET STATE

*   *Current State*: Shared backend databases, synchronous API calls across all domains.
*   *Target State*: Decoupled application domains; API gateway layers; event-driven learning models.
*   *Evolution Path*: Move database layers into domain silos in Wave 1. Establish event mesh in Wave 2. Enable real-time feedback loops in Wave 3.

---

# SECTION 11 — TECHNICAL ARCHITECTURE SUMMARY

This baseline defines the logical composition of the platform:
*   Decoupled **Platform Decomposition** boundaries to prevent data lock-in.
*   A **Component Model** establishing the context managers and engines.
*   **Reference Layer Models** isolating interface concerns from intelligence logic.
*   An **Interaction Model** detailing request flows and event-driven learning paths.

---

# SECTION 12 — EXIT CRITERIA

Before entering Technical Architecture Part 3, the following criteria must be satisfied:
*   *Service Definitions Approved*: Service responsibilities and dependencies must be signed off by the ARB.
*   *Interaction Patterns Validated*: Orchestration and event collaboration patterns must be approved.
*   *RACI Sign-off*: Tech leads must agree on service ownership boundaries.

---

# SECTION 13 — PHASE TRANSITION

With Part 2 approved, we transition to **Technical Architecture Part 3 – AI Architecture, Integration, Communication & Runtime Architecture**.

*   *Part 2 Outputs*: Unified application architecture, domain service specifications, sequence diagrams, and orchestration patterns.
*   *Part 3 Inputs*: System decomposition metrics, domain boundaries.
*   *Expected Deliverables for Part 3*: AI platform subsystems, context management, integration boundaries, communication patterns, and runtime environment specifications.

================================================================================
END OF TECHNICAL ARCHITECTURE PART 2
================================================================================
