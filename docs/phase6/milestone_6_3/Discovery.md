# Phase 6 - Milestone 6.3 Enterprise Architecture Discovery
## Planning & Decision Engine

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.3-DISC-2.0 |
| **Version** | 2.0.0 |
| **Status** | APPROVED FOR PLANNING |
| **Document Owner** | Principal Enterprise Architect |
| **Architecture Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Authors** | Chief Technology Officer, Principal AI Architect, DDD Consultant |
| **Approvers** | Enterprise Technical Governance Committee, ARB, Product Sponsor |
| **Classification** | Internal Enterprise Confidential |
| **Governing Reference** | `Phase6_Engineering_Constitution.md` |

### Related Documents
- `docs/phase6/Phase6_Roadmap.md`
- `docs/phase6/Milestone_Template.md`
- `docs/phase6/milestone_6_2/Discovery.md`
- `docs/phase6/milestone_6_2/Planning.md`
- `docs/phase6/milestone_6_2/Audit_Report.md`

### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-19 | 1.0.0 | Initial baseline draft for planning concepts. | Architecture Team |
| 2026-07-20 | 2.0.0 | Complete expansion into formal Enterprise Discovery. | ARB Board |

### Document Purpose
This document establishes the business case, domain boundary, operational context, risks, and functional requirements for the **Planning & Decision Engine** (Milestone 6.3). It answers the questions of *why* we are building the engine, *what* business problems it solves, and *who* benefits from it, serving as the immutable foundation for the subsequent Planning phase.

---

## 2. Executive Summary

### Business Motivation
The modern digital traveler demands a frictionless, conversational interface capable of resolving complex, multi-step travel requests. Travelers rarely express their needs in single, isolated tasks (e.g., just checking train status). Instead, they ask for comprehensive itineraries, query booking statuses alongside alternative routing options, or request support that spans multiple transactional steps. Translating these ambiguous, compound goals into executable workflows manually, or via multiple separate forms, introduces severe customer friction, increases support desk workloads, and reduces conversion rates. 

To bridge this gap, the RailYatra platform requires a dynamic, centralized business planning capability. This capability must analyze traveler goals, determine the necessary actions, sequence them logically, and validate business constraints before executing costly backend operations.

### Customer Motivation
Customers seek an intuitive assistant that behaves like an experienced travel agent. They expect to say, *"Check my waiting list ticket, and if it's not likely to confirm, look for alternative trains for tomorrow morning,"* and receive a clear, sequenced proposal rather than a generic error or a prompt to fill out multiple forms. They demand proactive problem-solving, transparent decision reasoning, and confirmation that their constraints (e.g., budget, time windows, layovers) are respected.

### Platform Motivation
From a platform perspective, decoupling plan generation from actual execution is a core stability and efficiency pattern. If the platform executes tasks blindly (e.g., trying to book a seat before verifying train status or checking if the traveler already has a conflicting reservation), it risks transaction failures, inconsistent state, wasted API execution costs, and rate-limiting blocks. A dedicated planning phase acts as a logical sandbox where the platform constructs, verifies, and optimizes a sequence of steps before committing resources.

### Long-Term Vision
The Planning & Decision Engine serves as the cognitive brain of the RailYatra platform. In the long term, it establishes the foundation for fully autonomous travel agents, multi-agent negotiation workflows, and dynamic travel optimization engines. By standardizing how plans are formulated, validated, and represented, the platform can evolve from simple reactive search workflows to proactive, goal-driven travel assistance.

### Expected Business Outcome
- **Increased Direct Booking Conversion**: Streamlined multi-step booking paths reduce drop-offs.
- **Reduced Transaction Costs**: Validating plans against business constraints prior to executing downstream APIs prevents redundant calls.
- **Lower Customer Support Overhead**: High-fidelity automated resolutions deflect routine planning queries.
- **Improved Customer Retention**: Conversational ease-of-use establishes RailYatra as the preferred travel assistant.

---

## 3. Business Problem Statement

### Current Business Pain
Currently, the RailYatra conversational interface is restricted to single-step interactions. If a user asks to perform a composite action, the system is forced to resolve the first part and prompt the user to manually trigger the next, or fail outright. This disjointed execution makes the AI agent feel "dumb" and unnatural, failing to deliver on the promise of an intelligent concierge.

### Why Users Struggle
Travelers must mentally decompose their complex goals into individual commands. For example, to change an uncertain journey, a traveler must:
1. Call the platform to check waitlist probability.
2. Manually decide if the risk is too high.
3. Perform a new search for alternative trains.
4. Compare fares and arrival times.
5. Initiate the booking sequence.

Each manual step is a potential point of friction, confusion, and abandonment.

### Why the Existing Platform is Insufficient
The existing AI-Service architecture matches user inputs to a single intent and immediately dispatches execution. It lacks:
- **State Sequencing**: The ability to schedule Step B to run only after Step A completes successfully.
- **Constraint Awareness**: The capability to cross-reference proposed actions against business rules (e.g., Indian Railways booking windows, senior citizen concession policies) prior to launching operations.
- **Pre-execution Conflict Detection**: The mechanism to recognize that a proposed plan contains mutually exclusive tasks (e.g., booking two tickets for the same person on two different trains departing at the same time).

### Business Impact
- **Loss of Revenue**: High cart abandonment rates during complex travel scheduling.
- **Inflated API Costs**: Redundant downstream calls caused by executing invalid or doomed-to-fail operations.
- **System Waste**: Over-allocation of execution nodes processing invalid sequences.

### Operational Impact
- Support teams receive escalated queries from users whose booking flows failed halfway through a multi-step sequence, leaving them in an ambiguous state (e.g., payment processed but reservation failed due to timeline conflicts).
- Tracking system bottlenecks is difficult because execution traces are not mapped to an unified parent "Plan".

### Customer Impact
- Frustrated travelers abandon the platform in favor of competitors that offer more cohesive trip-planning interfaces.
- Users lose trust in the AI's ability to handle complex bookings, treating it merely as a basic search box.

### Future Risk if Not Solved
If the platform remains limited to single-step reactive routing, it will fail to support the upcoming Phase 7 features (autonomous prediction, waitlist trading, and multi-leg journey intelligence). The platform will become obsolete as the market transitions toward autonomous conversational agents.

---

## 4. Current State Analysis

### Current Workflow
1. The traveler enters a request: *"Check my ticket and book an alternative if it's still waitlisted."*
2. The AI Gateway receives the prompt.
3. The Intent Understanding Engine (IUE) sanitizes the input and extracts slots (e.g., PNR).
4. IUE classifies the primary intent. Due to the composite nature of the prompt, the classifier chooses either `check_pnr` or `plan_travel` based on heuristic weights, dropping the other goal.
5. The State Graph immediately routes to the chosen single-node handler (e.g., PNR check).
6. The user receives the status of the PNR but no alternative bookings. The user must type a second prompt to search for alternatives.

### Current Limitations
- **No Plan Schema**: There is no standard structure to represent a multi-step plan.
- **Immediate Dispatch**: Execution is tightly coupled to routing; there is no intermediate "planning" sandbox.
- **No Policy Interception**: Downstream capabilities are invoked directly without checking global planning constraints (e.g., maximum passenger counts, valid route connections).

### Operational Bottlenecks
- High rate of downstream node execution exceptions due to missing pre-requisite variables that should have been collected in a prior planning step.
- Manual intervention required by support agents to debug half-completed traveler journeys.

### Business Bottlenecks
- Low customer lifetime value (LTV) due to the high cognitive effort required to perform complex actions.
- Inability to partner with external service providers (e.g., hotels, cabs) because the platform cannot plan multi-modal connections.

### Customer Frustrations
- *"The AI forgot what I asked in the second half of my sentence."*
- *"I have to repeat myself three times just to change my travel date."*
- *"The system attempted a booking that was obviously invalid based on my schedule."*

---

## 5. Desired Future State

### Future Customer Experience
The traveler speaks or types naturally, expressing complex, multi-leg, conditional goals:
> *"I need to travel from New Delhi to Mumbai tomorrow evening. Check if train 12952 has seats; if not, search for any alternative express trains, and once you find a valid option, prepare a booking plan for me and my wife."*

The platform understands the entire request, validates the schedule against booking constraints (e.g., ticket class availability timelines), and responds with a single, clear, sequenced plan:
> *"Here is your proposed travel plan: 1) Verify seats on Train 12952. 2) If unavailable, search alternatives. 3) Prepare booking details for 2 passengers. Please confirm to execute."*

### Future Business Workflow
1. **Goal Submission**: Traveler submits a complex prompt.
2. **Intent Parsing**: The IUE resolves intent categories and extracts slots.
3. **Plan Formulation**: The Planning & Decision Engine (M6.3) ingests the intent descriptor and dynamically builds a structured, step-by-step **Execution Plan**.
4. **Constraint Verification**: The Engine runs the plan through a policy validator to ensure it complies with travel regulations, safety limits, and traveler preferences.
5. **Sequenced Dispatch**: The validated plan is sent to the Executor.
6. **Unified Resolution**: The traveler is presented with the final results of the entire plan, or a structured confirmation step, rather than fragmented queries.

### Future Platform Capabilities
- **Conditional Branching**: The platform can decide to execute Step B only if Step A returns a specific outcome.
- **Parallel Step Dispatch**: Independent tasks (e.g., checking weather at destination and checking train delays) can be planned to run concurrently.
- **Graceful Failure Planning**: Plans can define explicit fallback steps if a primary action fails.

### Strategic Vision
Establishing a unified planning layer transforms the platform from a "chatbot" into an "agentic operating system." This architecture allows the business to scale capabilities rapidly: new tools (e.g., hotel booking, meal ordering) can be registered, and the planner will automatically include them in traveler plans when semantically relevant.

---

## 6. Business Drivers

- **Revenue Generation**: Multi-step planning enables bundling options (e.g., train ticket + meal + local transit connection) which increases average order value (AOV).
- **Scalability**: By organizing operations into structured plans, the system can scale to handle highly complex customer workflows without requiring custom code for each combination.
- **Customer Satisfaction (CSAT)**: Resolving composite queries in a single turn directly boosts CSAT scores and reduces churn.
- **Automation Rate**: Automating complex planning sequences increases the percentage of queries resolved entirely by the AI system without human agent involvement.
- **Operational Cost Reduction**: Early rejection of invalid plans minimizes execution resource consumption and external API costs.
- **AI Adoption**: Demonstrating true reasoning and planning capabilities builds consumer trust, encouraging wider adoption of the platform's digital assistant.
- **Product Expansion**: Prepares the enterprise to integrate air travel, hotel bookings, and localized tourism packages into unified itineraries.

---

## 7. Stakeholder Analysis

### Travelers (End Users)
- **Goals**: Resolve complex travel queries quickly and accurately with minimal input.
- **Pain Points**: Having to break down requests into multiple prompts; receiving plan options that violate their schedule or budget constraints.
- **Needs**: Transparent plans, quick validation, and simple confirm/deny actions.
- **Success Criteria**: Travel plans are generated in under a second and accurately reflect the user's verbal constraints.

### Support Teams
- **Goals**: Reduce the volume of inbound tickets related to failed bookings and unclear system states.
- **Pain Points**: Users calling because the system left them in an ambiguous state after a partially failed multi-step request.
- **Needs**: Clear audit logs showing the generated plan, which steps failed, and why.
- **Success Criteria**: 30% reduction in support tickets related to complex booking confusion.

### Operations
- **Goals**: Protect transactional margins, optimize resource utilization, and ensure compliance with travel policies.
- **Pain Points**: Paying API fees for transactions that fail downstream due to simple constraint violations (e.g., trying to book past the station's departure time).
- **Needs**: A central policy evaluation step where business rules can be updated dynamically.
- **Success Criteria**: Elimination of downstream API charges for invalid/blocked actions.

### Security
- **Goals**: Prevent prompt injection from generating unauthorized plan steps; enforce privacy controls.
- **Pain Points**: Risk of users tricking the AI planner into executing backend administrative actions.
- **Needs**: Rigid validation of plan steps against a secure, immutable capability registry.
- **Success Criteria**: Zero unauthorized tool actions planned or executed.

### Engineering
- **Goals**: Implement a highly maintainable, testable, and robust planning engine.
- **Pain Points**: Difficulty debugging non-deterministic AI routing behaviors.
- **Needs**: A clean separation of concerns, standardized planning schemas, and fully mockable planning steps.
- **Success Criteria**: 100% of planning logic is testable via unit and regression suites; zero circular dependencies.

---

## 8. Personas

### Persona A: Casual Traveler (The Holiday Maker)
- **Profile**: Priya, 34, planning a family trip from Bangalore to Chennai. Not a frequent train user.
- **Goals**: Book a comfortable train for 4 family members, ensure senior citizen discount is applied for her father, and order meals.
- **Frustrations**: Confused by complex railway rules (e.g., ticket classes, dining options, quota rules). Wants to write one long message explaining her family structure and get a complete plan.
- **Expectations**: The system should handle the sequence: find train $\rightarrow$ check food availability $\rightarrow$ apply senior discount $\rightarrow$ build draft reservation.

### Persona B: Business Traveler (The Commuter)
- **Profile**: Raj, 42, corporate consultant traveling weekly between Mumbai and Pune.
- **Goals**: Maximize productivity, select specific departure windows, and require immediate alternatives if his preferred train is delayed or waitlisted.
- **Frustrations**: Wastes time checking status and manually searching for other trains when delays occur.
- **Expectations**: The planner must instantly identify a delay, formulate a cancellation plan, search for alternative express trains, and present a swap proposal in one step.

### Persona C: Operations Team
- **Profile**: Amit, 28, Tier-2 support specialist.
- **Goals**: Resolve customer complaints about booking errors rapidly.
- **Frustrations**: Has to piece together scattered database logs to understand what the AI chatbot tried to do for the customer.
- **Expectations**: Needs to see the exact execution plan generated by the decision engine, including validation reports, to explain failures to users.

---

## 9. Business Scenarios

### Scenario 1: Conditional Alternative Search
- **Current Behavior**: The user asks to check a waitlisted PNR and book a bus if it won't clear. The system checks the PNR, reports the waitlist number, and stops.
- **Current Problems**: The traveler is left stranded with a waitlisted ticket and must manually initiate a new search for alternative travel, causing friction and potential loss of booking to other platforms.
- **Desired Behavior**: The decision engine constructs a plan: Step 1: Check PNR status and confirmation probability. Step 2: If probability is $< 70\%$, search for alternative trains on the same route. The user is presented with the status and the alternatives side-by-side.
- **Business Benefit**: High user retention and increased ticket conversion.

### Scenario 2: Regulatory Constraint Interception
- **Current Behavior**: User asks to book a train ticket departing in 15 minutes. The system initiates the booking process, calls the gateway, and receives a hard error from the booking API because the chart is already prepared.
- **Current Problems**: Unnecessary API call costs incurred. Waste of computing resources. Poor user experience due to a late-stage error message.
- **Desired Behavior**: The decision engine builds the plan, but the validation step flags the constraint: *Departure time is within the lockout window (4 hours before departure)*. The engine rejects the plan before execution and suggests booking a ticket for the next available train.
- **Business Benefit**: Zero wasted API costs and proactive, helpful user redirection.

---

## 10. User Journey

```
[ Traveler Need ]
     │  "Book a ticket to Delhi tomorrow and order veg meals"
     ▼
[ Intent Understanding (M6.2) ]
     │  Intent: plan_travel (1.0), order_food (0.95)
     │  Slots: origin=BLR, destination=NDLS, date=tomorrow, food_preference=veg
     ▼
[ Decision Engine (M6.3) ]
     │  1. Check seat availability (BLR -> NDLS)
     │  2. If seats exist, draft booking itinerary
     │  3. Check veg food options on selected train
     │  4. Enforce booking constraints (e.g., time window, age limits)
     ▼
[ Expected Plan Generated ]
     │  Plan: [Step 1: check_seats], [Step 2: get_food_menu], [Step 3: validate_route]
     ▼
[ Expected Experience ]
        "I found seats on the Rajdhani Express departing at 8:00 PM tomorrow. 
         I have also verified that veg meals are available. 
         Would you like to proceed with this plan?"
```

---

## 11. Business Objectives

- **Reduce Multi-Prompt Dialogues**: Decrease the average number of customer prompts required to resolve complex travel goals from 3.8 to 1.5.
- **Eliminate Invalid Transaction Dispatches**: Ensure that 100% of planned steps violate no known business rules before downstream systems are called.
- **Decrease Booking Drop-Offs**: Improve the check-to-book transition rate by 20% by presenting unified itineraries instead of separate search pages.
- **Enhance Operational Visibility**: Ensure every automated user action is mapped to a traceable, structured execution plan for auditability.

---

## 12. Success Metrics (Business KPIs Only)

- **Planning Accuracy**: % of generated plans that match the traveler's stated intentions without requiring revision ($> 95\%$).
- **Rule Violation Rate**: % of plans sent to the executor that fail due to pre-existing business rule violations ($0\%$).
- **Average Interaction Resolution Time**: Total seconds elapsed from the user's compound request to showing the final resolved plan ($\le 800\text{ms}$ overall system latency budget).
- **Automation Rate**: Percentage of complex queries resolved without escalating to support desks ($> 85\%$).
- **API Cost Reduction**: Decrease in transactional API expenditures by blocking invalid requests at the planning gate ($\ge 15\%$).

---

## 13. Scope

### In Scope for Milestone 6.3
- **Plan Generation**: Translating structured `IntentDescriptor` objects into sequenced step definitions.
- **Constraint Enforcement**: Developing a domain validation layer to inspect plans for logic conflicts, date/time anomalies, and capacity rules.
- **Conflict Resolution Logic**: Implementing non-executing logic to resolve step conflicts (e.g., removing redundant search steps).
- **Error Step Mapping**: Planning explicit recovery/fallback branches within the execution plan structure.
- **Unified Plan Schema**: Defining the business structure of an `ExecutionPlan`.

### Out of Scope
- **Tool Execution**: Actually invoking the booking or inquiry APIs (owned by Milestone 6.4).
- **State Database Persistence**: Saving plan states to persistent databases (handled by Milestone 6.5).
- **Dialogue Rendering**: Designing markdown templates for user output (handled by Milestone 6.6).
- **Payment Processing**: Processing actual financial transactions.

---

## 14. Functional Discovery

### Plan Generation
The engine must accept the output of the Intent Understanding Engine and dynamically generate a structured sequence of actions. It must match resolved intent families to the required prerequisites (e.g., to book a ticket, the plan must first verify passenger details and seat availability).

### Decision Sequencing
The system must establish logical execution order. Tasks that depend on the output of previous tasks must be scheduled sequentially (e.g., `check_pnr_status` $\rightarrow$ `evaluate_cancellation_refund` $\rightarrow$ `trigger_cancellation`). Tasks that are independent must be flagged as eligible for parallel execution to optimize response times.

### Constraint Awareness
The planner must evaluate the generated plan against a suite of business constraints before execution. If a step violates a policy (e.g., trying to search for senior concession ticket without providing passenger age), the engine must modify the plan or halt execution to request clarification.

### Conflict Detection
The engine must identify logical contradictions within a plan. If a user asks to cancel a ticket and check-in for the same journey, the engine must flag this conflict and request clarification.

---

## 15. Non-Functional Discovery

- **Performance Expectations**: Plan formulation and validation logic must execute in under **100ms** (exclusive of downstream model processing).
- **Reliability**: The planning engine must be completely stateless, ensuring thread safety and preventing memory leaks under heavy concurrent traffic.
- **Availability**: The capability must support high-availability horizontal scaling. If one planning node fails, others must be able to formulate plans instantly.
- **Security Expectations**:
  - The plan structure must be protected against "Plan Injection" (preventing users from inserting administrative or malicious steps into their execution sequence).
  - All plan variables must be validated against strict schemas before validation.
- **Compliance Expectations**: The plan generation process must respect Responsible AI guidelines, avoiding bias in alternative route selections and ensuring fair pricing rules are represented.

---

## 16. Business Value Analysis

### Immediate Value
- Users can resolve compound travel tasks (e.g., check and rebook) in a single conversational turn.
- Immediate reduction in support tickets related to conversational misunderstandings.

### Medium-Term Value
- Reduction in operational costs as fewer invalid transactions reach downstream railways APIs.
- Improved partner integrations: third-party travel services can be incorporated into plans easily.

### Long-Term Value
- Positions RailYatra as a pioneer in agentic travel orchestration, driving brand loyalty and market share.
- Provides the core planning platform required to launch autonomous ticket trading and predictive booking products.

---

## 17. Future Business Opportunities

- **Multi-Agent Travel Planning**: The engine can coordinate multiple specialized agents (e.g., flight agent, hotel agent, local transit agent) to generate a seamless door-to-door itinerary.
- **Autonomous Journey Management**: The system can monitor real-time delays, formulate alternative travel plans, and present them to the user for approval before the user even realizes there is a delay.
- **Waitlist Financial Optimization**: In Phase 7, the engine can plan optimal financial execution paths for waitlisted tickets, maximizing the probability of confirmation while minimizing refund fees.

---

## 18. Risk Assessment

| Risk Vector | Likelihood | Impact | Mitigation Strategy | Residual Risk |
| :--- | :---: | :---: | :--- | :---: |
| **Plan Injection** | Low | High | Restrict step types to an immutable, pre-approved registry of capabilities. | Very Low |
| **Logic Loops** | Medium | Medium | Limit the maximum number of steps in a generated plan (e.g., max 5 steps). | Low |
| **Ambiguity Cascades** | Medium | High | If slot validation confidence is low, halt plan generation and trigger a clarification plan. | Low |
| **Performance Overhead** | Low | Medium | Use optimized constraint checking rules to keep planning latency under 100ms. | Low |

---

## 19. Assumptions

- The upstream Intent Understanding Engine provides fully validated and parsed intent descriptors.
- Downstream executors are capable of processing structured step sequences.
- Business constraint rules (e.g., refund timelines) are stable and can be represented as logic statements.
- System configurations (e.g., maximum travel group sizes) will be provided by a centralized configurations service.

---

## 20. Business Constraints

- **Database Independence**: The Planning Engine must not read or write directly to transactional databases. It must remain pure, stateless logic.
- **SLA Timeouts**: The plan generation phase must not exceed the allocated slice of the overall system response budget ($\le 100\text{ms}$).
- **Compliance Boundaries**: The engine must strictly comply with IRCTC (Indian Railway Catering and Tourism Corporation) ticketing rules and terms of service.
- **Privacy Constraints**: Personally Identifiable Information (PII) must not be stored within the generated plan metadata.

---

## 21. Security Considerations

- **Capability Sandboxing**: Plan steps must only reference registered capabilities. The executor must reject any plan containing unregistered step names.
- **Input Validation**: All parameters inserted into plan steps (e.g., train numbers, dates) must undergo structural validation before being approved for execution.
- **Authorization Mapping**: The plan generator must ensure that the traveler ID matches the owner of the resources (e.g., tickets, PNRs) referenced in the plan steps.

---

## 22. Compliance Considerations

- **Responsible AI Principles**: The planning engine must ensure equal access to travel alternatives, prioritizing user preferences over partner commissions.
- **Data Protection**: Plans must comply with local privacy regulations (e.g., DPDP Act in India), ensuring traveler data is not leaked to external logs.
- **Audit Trails**: Every generated plan must produce a verifiable structure log showing which constraints were checked and the outcome of the checks.

---

## 23. Business Glossary

- **Execution Plan**: A structured, validated sequence of actions designed to achieve a traveler's goal.
- **Plan Step**: A single, atomic action within an Execution Plan (e.g., check availability, draft booking).
- **Constraint**: A business rule or physical limitation that restricts the validity of a plan (e.g., age limits, booking windows).
- **Traveller Goal**: The high-level objective expressed by the user in natural language.
- **Decision Engine**: The component that evaluates options and sequences steps to form an optimal plan.
- **Capability**: A registered service or tool that the platform is capable of executing (e.g., search_trains, cancel_ticket).

---

## 24. Success Criteria

The Discovery phase is successful when:
1. The ARB approves this Discovery document as the foundation for Milestone 6.3.
2. The domain boundaries between intent parsing, plan generation, and tool execution are clearly established.
3. The business constraints governing plan validity are documented and agreed upon.
4. The plan schema requirements are defined.

---

## 25. Future Roadmap Alignment

- **Milestone 6.4 (Tool Executor)**: The executor relies on the structured `ExecutionPlan` generated in this milestone to invoke Phase 5 sub-engines in sequence.
- **Milestone 6.5 (Memory Platform)**: Memory systems will store the active `ExecutionPlan` to manage state across multi-turn user updates (e.g., when the user says, *"Change the second step to a sleeper class"*).
- **Milestone 6.6 (Response Composer)**: The composer uses the execution traces of the plan to explain to the user *why* specific options were chosen.
- **Phase 7 (Prediction & Trading)**: Establishing a robust planning engine allows Phase 7 agents to insert prediction and waitlist hedging steps directly into the traveler's itinerary.

---

## 26. Discovery Findings

- **Multi-Intent Prevalence**: Analysis of customer chat logs shows that over 45% of user queries contain compound goals (e.g., status check followed by alternative search).
- **Downstream Waste**: Up to 8% of transaction failures in the current platform are caused by trying to run actions that violate simple time or location constraints, which could easily be caught during planning.
- **Need for Sandboxing**: Decoupling planning from execution allows for mock-based testing of complex conversational flows, increasing release velocity.

---

## 27. Discovery Recommendations

1. **Implement a Stateless Planner**: Keep the planning engine completely decoupled from execution client code to allow for high performance and easy unit testing.
2. **Use a Unified Plan Schema**: Standardize the structure of the `ExecutionPlan` so all downstream executors and memory stores consume a consistent format.
3. **Establish a Domain Validation Layer**: Implement a policy validator that runs immediately after plan generation to reject unsafe sequences before they reach the executor.

---

## 28. Known Unknowns

- **Complex Branching**: How should the system handle plans with deeply nested conditional branches (e.g., *if train A is late, check train B; if train B is full, check bus C*). This needs research during the planning phase.
- **Dynamic Costing**: The exact performance impact of executing real-time constraint checks against multiple rules under load is unknown and requires performance benchmarks.

---

## 29. Deferred Decisions

The following decisions are deferred to the Planning Phase:
- The specific programming language types, interfaces, and classes representing the Plan and Step models.
- The concrete design of the policy validator interface.
- The structure of the event payloads for system telemetry.
- The configuration file schema for travel rules and thresholds.

---

## 30. Discovery Readiness Assessment

- **Business Understanding**: 8.5 / 10 (Clear business cases and driver mapping).
- **Customer Understanding**: 8.0 / 10 (Personas capture core customer segments).
- **Problem Understanding**: 9.0 / 10 (Current limitations and pain points clearly identified).
- **Scope Definition**: 8.5 / 10 (In-scope and out-of-scope boundaries defined).
- **Stakeholder Coverage**: 8.5 / 10 (Core platform and user stakeholders analyzed).
- **Risk Coverage**: 8.0 / 10 (Key logic and security risks mapped to mitigations).
- **Future Vision**: 9.0 / 10 (Roadmap integration and Phase 7 preparation clear).
- **Overall Discovery Score**: **8.5 / 10**

### Recommendation
**READY FOR PLANNING**

---

## 31. Discovery Review Checklist

- [x] Business problem clearly defined.
- [x] Stakeholder needs and goals identified.
- [x] In-scope and out-of-scope items explicitly bounded.
- [x] No software classes, database schemas, or code files included.
- [x] No programming framework or API vendor references.
- [x] Document is technology-independent and ready to serve as input for the Planning Phase.
