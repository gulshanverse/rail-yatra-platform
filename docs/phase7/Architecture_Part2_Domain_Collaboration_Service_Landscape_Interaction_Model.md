# RAILYATRA AI PLATFORM
## Phase 7 – Predictive Intelligence Platform
### ENTERPRISE ARCHITECTURE — PART 2: ENTERPRISE DOMAIN COLLABORATION, SERVICE LANDSCAPE & INTERACTION MODEL

```
================================================================================
Document Type:      Enterprise Architecture (Domain Collaboration & Service Landscape)
Phase:              7 – Predictive Intelligence Platform
Version:            1.0
Status:             BASELINE APPROVED
Domain:             Service Landscape, Collaboration Models, Event Models, Responsibility Matrix
Target Audience:    Enterprise Architects, Solution Architects, Program Managers, PMO
================================================================================
```

---

# SECTION 1 — ENTERPRISE COLLABORATION INTRODUCTION

## 1.1 Purpose of Enterprise Collaboration
Enterprise collaboration defines how autonomous business domains coordinate to fulfill complex travel flows. Rather than constructing a monolithic prediction system that spans all responsibilities, the RailYatra platform distributes ownership among specialized domains. This document defines the collaboration rules, shared interfaces, and communication flows required to keep domains decoupled yet highly collaborative.

## 1.2 Preservation of Domain Autonomy
To prevent coordination friction and technical lock-in, domains must remain autonomous. They hide their internal logic and data implementation, exposing only clean, contract-bound interfaces. This means changes within the prediction algorithms or profile architectures do not propagate errors or require modifications in dependent domains.

## 1.3 Domain Ownership Philosophy
We establish a "service-first" ownership model. Each domain owner is responsible for the design, execution, compliance, and accuracy of the services they expose. If a service fails to meet its SLA (e.g., latency or accuracy threshold), the domain owner must remediate it without relying on downstream adjustments.

## 1.4 Enterprise Scalability Principles
*   **Asynchronous Communication**: Long-running or heavy operations must coordinate asynchronously via events to prevent service blockages.
*   **Contractual Enforcement**: All interactions must validate against predefined schemas.
*   **Data Decoupling**: Domains must not directly query another domain's data stores. All data exchange is handled through service calls or event structures.

## 1.5 Relationship with Enterprise Architecture Part 1
Part 1 defined the core capabilities and domain boundaries. Part 2 details the interactions and collaborations between these domains, translating static capability definitions into active enterprise services and value flows.

---

# SECTION 2 — DOMAIN COLLABORATION MODEL

The following diagram illustrates how the nine core enterprise domains collaborate to process passenger requests and update predictions:

```
                  +-----------------------------------+
                  |        Passenger Domain           |
                  +-----------------------------------+
                    /             ^             \
                   /               \             \ (Captures Feedback)
                  v                 \             v
  +------------------+     +------------------+     +------------------+
  |  Journey Domain  |     |Prediction Domain |     | Learning Domain  |
  +------------------+     +------------------+     +------------------+
          \                     /        \               /
           v                   v          v             v
  +----------------------------------+   +-----------------------------+
  |         Risk Domain              |   |    Recommendation Domain    |
  +----------------------------------+   +-----------------------------+
                   \                                    /
                    v                                  v
  +--------------------------------------------------------------------+
  |                         Governance Domain                          |
  +--------------------------------------------------------------------+
```

### 2.1 Collaboration Specification

1. **Passenger and Prediction Domain Collaboration**:
   *   *Purpose*: Authorizes the personalization of forecasts.
   *   *Business Value*: Customizes delay warnings and booking odds based on user risk profiles.
   *   *Responsibilities*: Passenger Domain manages user consent and validation; Prediction Domain runs customized forecasting routines.
   *   *Ownership*: Passenger Domain owns traveler consent registry; Prediction Domain owns logic execution.
   *   *Expected Outcomes*: Personalized, policy-compliant predictions.

2. **Journey and Prediction Domain Collaboration**:
   *   *Purpose*: Feeds operational live runs into prediction models.
   *   *Business Value*: Generates up-to-date arrival and delay estimates.
   *   *Responsibilities*: Journey Domain pushes live train coordinates and transit statuses; Prediction Domain executes prediction models.
   *   *Ownership*: Journey Domain owns data feed quality; Prediction Domain owns forecast accuracy.
   *   *Expected Outcomes*: Highly accurate, real-time delay predictions.

3. **Prediction and Risk Domain Collaboration**:
   *   *Purpose*: Checks predictions for travel plan impact.
   *   *Business Value*: Evaluates whether a projected delay will break a connection.
   *   *Responsibilities*: Prediction Domain supplies delay thresholds; Risk Domain maps the journey chain and flags connection alerts.
   *   *Ownership*: Prediction Domain owns raw output; Risk Domain owns calculation of missed connection risk.
   *   *Expected Outcomes*: Real-time identification of traveler risk points.

4. **Risk and Recommendation Domain Collaboration**:
   *   *Purpose*: Triggers mitigating fallback plans.
   *   *Business Value*: Presents alternate trains or routes when a connection risk is identified.
   *   *Responsibilities*: Risk Domain sends risk metrics and context; Recommendation Domain evaluates alternative train options and returns them.
   *   *Ownership*: Risk Domain owns the risk alarm; Recommendation Domain owns alternative optimization logic.
   *   *Expected Outcomes*: Proactive fallback options for affected passengers.

---

# SECTION 3 — ENTERPRISE SERVICE LANDSCAPE

The enterprise services represent the functional interfaces exposed by each domain.

| Service ID | Service Name | Purpose | Business Responsibilities | Consumers | Enterprise Dependencies | Business Owner |
|---|---|---|---|---|---|---|
| **SRV-1** | **Passenger Profile Service** | Exposes traveler profile, risk index, and historical preferences. | Retrieves and updates profile parameters; enforces privacy compliance. | Recommendation Service, Risk Service. | None. | Chief Passenger Officer |
| **SRV-2** | **Live Ingestion Service** | Ingests live railway tracking data and schedules. | Coordinates external feeds; formats timetable entries. | Prediction Service. | External Railway Feeds. | Director of Journey Ops |
| **SRV-3** | **Waitlist Forecast Service** | Generates seat confirmation probabilities. | Computes booking odds based on historical and current trends. | Recommendation Service. | Passenger Profile Service. | Chief Prediction Officer |
| **SRV-4** | **Delay Forecast Service** | Estimates expected delays and arrival deviations. | Predicts train statuses along route segments. | Risk Service, Recommendation Service. | Live Ingestion Service. | Chief Prediction Officer |
| **SRV-5** | **Risk Evaluation Service** | Evaluates journey connection risks. | Identifies potential connection failures in multi-segment travel. | Recommendation Service. | Delay Forecast Service. | Chief Risk Officer |
| **SRV-6** | **Alternative Finder Service** | Resolves alternative routing paths. | Selects optimal backup routes when risk limits are breached. | Passenger App, Partner API. | Risk Evaluation Service, Profile Service. | VP Product (Monetization) |
| **SRV-7** | **Responsible AI Service** | Inspects outputs for compliance and bias. | Enforces explainability, confidence scoring, and model fairness. | All prediction endpoints. | Governance Policy Registry. | Head of AI Ethics |
| **SRV-8** | **Outcome Tracking Service** | Registers actual travel outcomes. | Logs actual confirmation statuses and arrival times. | Learning models, Audit loggers. | Delay Forecast Service, Live Ingestion. | Director of Learning Systems |

---

# SECTION 4 — SERVICE INTERACTION MODEL

The Service Interaction Model describes how services orchestrate their actions to fulfill the predictive value flow.

```
Passenger App        Passenger Profile      Delay Forecast       Risk Evaluation      Alternative Finder
     |                       |                    |                     |                     |
     |---[1. Request Trip]-->|                    |                     |                     |
     |                       |---[2. Get Profile]->                     |                     |
     |                       |------------------[3. Get Delay]--------->|                     |
     |                                            |---[4. Live Delay]-->|                     |
     |                                                                  |--[5. Connection?]-->|
     |                                                                  |                     |---[6. Get Alts]-->|
     |<---------------------------------[7. Return Risk & Alternatives]-----------------------------------|
```

### 4.1 Interaction Sequence Specification
1. **Trip Registration**: The Passenger App registers a trip path. The Passenger Profile Service verifies consent parameters.
2. **Delay Lookup**: The Passenger App requests delay forecasts. The Delay Forecast Service pulls live status updates from the Journey Domain's Live Ingestion Service.
3. **Risk Evaluation**: The Risk Evaluation Service compares delay forecasts against connection windows. If risk exceeds the traveler's threshold, it triggers the Alternative Finder Service.
4. **Alternative Optimization**: The Alternative Finder Service queries passenger preferences to identify alternative trains with high confirmation probability and safe connection windows.
5. **Calibrated Handoff**: The results are wrapped in explainable context and sent back to the Passenger App.

---

# SECTION 5 — ENTERPRISE RESPONSIBILITY MATRIX

The RACI matrix below defines the ownership and responsibilities for capabilities, domains, services, policies, and decisions.

| Functional Area / Artifact | Executive Steering Committee | Architecture Review Board | Responsible AI Board | Passenger Domain Owner | Prediction Domain Owner | Risk Domain Owner |
|---|---|---|---|---|---|---|
| **Capability Definition** | **A** | **R** | **C** | **R** | **R** | **R** |
| **Domain Interface Contracts** | **C** | **A** | **I** | **R** | **R** | **R** |
| **SRV-1 (Passenger Profile)** | **I** | **C** | **I** | **A/R** | **I** | **I** |
| **SRV-3 & SRV-4 (Predictions)** | **I** | **C** | **C** | **I** | **A/R** | **I** |
| **SRV-5 (Risk Evaluation)** | **I** | **C** | **I** | **I** | **I** | **A/R** |
| **Ethics & Explainability Policy**| **A** | **C** | **R** | **C** | **C** | **I** |
| **DPDP Compliance Auditing** | **A** | **C** | **I** | **R** | **R** | **I** |
| **Model Retraining Approvals** | **I** | **C** | **C** | **I** | **A/R** | **I** |

*Legend: R = Responsible, A = Accountable, C = Consulted, I = Informed*

---

# SECTION 6 — VALUE FLOW ARCHITECTURE

Value Flow Architecture models the sequential steps that transform raw passenger intent into continuous system learning.

### 6.1 Flow Path: Connection Protection Assurance

```
[Passenger Intent] -> [Live Prediction] -> [Risk Assessment] -> [Fallback Recommendation] -> [Learning Optimization]
       |                      |                    |                      |                        |
User books connected   Timetable deviations   Missed connection      Alternate seat found;    Actual train arrival
tickets                calculated             risk calculated        alert sent to user       logged to retrain model
```

*   **Step 1: Ingest Intent**: Traveler books a multi-segment journey. Passenger Profile captures risk tolerance and consent.
*   **Step 2: Generate Prediction**: Timetable fluctuations and weather anomalies are analyzed by Prediction Services.
*   **Step 3: Evaluate Risk**: Risk Evaluation computes the probability of a missed connection. If probability > 15%, the risk is flagged.
*   **Step 4: Formulate Recommendation**: Alternative Finder matches alternate trains with high seat availability.
*   **Step 5: Present Guidance**: Traveler receives an alert with an explanation ("Connection risk is 34%; Duronto alternative has 94% confirmation probability").
*   **Step 6: Capture Learning**: Actual arrival times and traveler decisions are tracked by the Outcome Tracking Service to update historical data models.

---

# SECTION 7 — ENTERPRISE EVENT MODEL (CONCEPTUAL)

Events are business-meaningful occurrences that trigger downstream domain actions. They are modeled here conceptually without technology reference.

*   **Event 1: Journey Planned**
    *   *Business Meaning*: Passenger registers a new travel booking.
    *   *Trigger*: Booking transaction completion.
    *   *Business Impact*: Initiates tracking in Journey and Prediction domains.
    *   *Affected Domains*: Passenger, Journey, Prediction.
*   **Event 2: Prediction Generated**
    *   *Business Meaning*: A new or updated forecast is computed.
    *   *Trigger*: Schedule updates or live telemetry updates.
    *   *Business Impact*: Prompts Risk Domain to re-evaluate journey chains.
    *   *Affected Domains*: Prediction, Risk.
*   **Event 3: Risk Identified**
    *   *Business Meaning*: Missed connection probability exceeds acceptable limits.
    *   *Trigger*: Risk Evaluation Service calculation.
    *   *Business Impact*: Triggers Recommendation Domain to find fallback routes.
    *   *Affected Domains*: Risk, Recommendation, Passenger.
*   **Event 4: Recommendation Accepted**
    *   *Business Meaning*: Traveler chooses the suggested alternative.
    *   *Trigger*: Traveler click/consent action.
    *   *Business Impact*: Updates passenger journey itinerary and tracks offering utility.
    *   *Affected Domains*: Passenger, Recommendation, Journey.
*   **Event 5: Journey Completed**
    *   *Business Meaning*: Traveler reaches destination.
    *   *Trigger*: Live train arriving at destination station.
    *   *Business Impact*: Initiates the learning loop and stores outcome telemetry.
    *   *Affected Domains*: Journey, Learning, Prediction.

---

# SECTION 8 — ENTERPRISE INTEGRATION PRINCIPLES

1. **Domain Autonomy**: No database sharing. Data must remain inside domain silos, exposed only through services or events.
2. **Business Ownership**: Services must align with business owners who manage budgets, features, and SLAs.
3. **Information Consistency**: Key attributes (e.g., traveler ID, train number) must use identical definitions across domains.
4. **Loose Organizational Coupling**: Domain teams design their service schedules independently, matching external interface contracts.
5. **Trust Preservation**: All external outputs must have explainable rationale and confidence values.
6. **Governance First**: Consent checks must run before passenger data is consumed by prediction algorithms.
7. **Business Event Driven**: Changes in operational status are published as events, allowing decoupled systems to react.

---

# SECTION 9 — CROSS-DOMAIN GOVERNANCE

Cross-domain governance coordinates policies and resolves boundary conflicts.

### 9.1 Shared Ownership Policies
When multiple domains interact (e.g., Passenger and Prediction), ownership is governed by a **Service Level Agreement (SLA)**. The SLA specifies data formats, latency limits, and verification requirements.

### 9.2 Conflict Resolution & Decision Forums
If domains disagree on responsibilities (e.g., whether platform crowding belongs to Journey or Operations), the dispute is escalated to the **Architecture Review Board (ARB)**. The ARB evaluates against the Enterprise Capability Architecture and makes a final binding decision.

---

# SECTION 10 — TARGET COLLABORATION MODEL

```
+---------------------------------------------------------------------------------+
|                         COLLABORATION MATURITY LEVELS                           |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   [Level 1: Siloed] ---------> [Level 3: Contractual] -------> [Level 5: Event] |
|   - Direct db access            - API Contracts established    - Async Event Mesh|
|   - Hard dependencies           - Synchronous request/reply    - Fully autonomous|
|                                                                                 |
+---------------------------------------------------------------------------------+
```

*   **Current Maturity**: Level 2 (Inconsistent contracts, direct data queries, overlapping domain boundaries).
*   **Target Maturity**: Level 4 (Contractual APIs, asynchronous event integration, clean domain boundaries).
*   **Expected Evolution**: Phased removal of direct database queries, replacing them with event-driven architectures.

---

# SECTION 11 — ARCHITECTURE SUMMARY

This baseline establishes:
*   A formal **Domain Collaboration Model** that specifies how autonomous domains coordinate.
*   The **Enterprise Service Landscape** defining SRV-1 to SRV-8, including business owners and consumers.
*   The **Service Interaction Model** mapping sequence flows.
*   An **Enterprise Responsibility Matrix (RACI)** aligning capability owners.
*   The **Conceptual Event Model** triggering cross-domain actions.

---

# SECTION 12 — ARCHITECTURE EXIT CRITERIA

Before entering Enterprise Architecture Part 3, the following conditions must be met:
*   *Domain Contracts Validated*: Interface parameters for SRV-1 to SRV-8 must be approved by the ARB.
*   *Service Landscape Approved*: The business owners and consumers for all services must be confirmed.
*   *RACI Sign-off*: All domain owners must sign the Responsibility Matrix (Section 5).
*   *Event Model Validated*: The event triggers must cover all target travel scenarios.

---

# SECTION 13 — PHASE TRANSITION

With Part 2 approved, the architecture team transitions into **Enterprise Architecture Part 3 – Enterprise Information Architecture, Governance Framework & Transformation Roadmap**.

*   *Part 2 Outputs*: Approved service definitions, interaction patterns, and event models.
*   *Part 3 Inputs*: Service landscapes, domain boundaries, and conceptual events.
*   *Expected Deliverables for Part 3*: Information lifecycles, reference architecture layers, governance structures, compliance frameworks, and the transformation roadmap.

================================================================================
END OF ENTERPRISE ARCHITECTURE PART 2
================================================================================
