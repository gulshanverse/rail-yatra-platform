# Phase 6 - Milestone 6.4 Enterprise Business Discovery
## Execution Engine

---

## 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.4-DISC-3.1 |
| **Version** | 3.1.0 |
| **Status** | APPROVED FOR PLANNING |
| **Document Owner** | Principal Business Architect |
| **Architecture Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Authors** | Chief Product Officer, Principal Business Architect, Enterprise Business Analyst |
| **Approvers** | Enterprise Governance Committee, Technical Design Authority, Product Sponsor |
| **Classification** | Internal Enterprise Confidential |
| **Governing References** | `Phase6_Engineering_Constitution.md`, `Enterprise Discovery Standard v3.1` |
| **Related Documents** | `Phase6_Roadmap.md`, `M6.3/Discovery.md`, `M6.3/Planning.md`, `M6.3/IEP.md` |

### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-21 | 1.0.0 | Initial baseline draft for execution concepts. | Product Team |
| 2026-07-21 | 2.0.0 | Expanded business capabilities and customer journeys. | Business Analyst Group |
| 2026-07-21 | 3.0.0 | Compliance alignment with Enterprise Discovery Standard v3.1. | Governance Committee |
| 2026-07-21 | 3.1.0 | Final ARB refinement for Milestone 6.4. | ARB Board |

### Purpose
This document establishes the business case, strategic drivers, operational workflows, risk parameters, and success metrics for the **Execution Engine** (Milestone 6.4). It answers the questions of *why* this execution coordination function is necessary, *what* business and customer problems it addresses, and *who* is affected, serving as the official business input for the subsequent Planning phase.

---

## 2. Executive Summary

### Business Motivation
The RailYatra platform has successfully implemented intent parsing, intent classification, and structured travel plan formulation. However, formulating a plan is only half the journey. To realize actual business value and drive transactions, the platform must safely and reliably execute these plans. The Execution Engine is the operational engine that bridges the gap between digital planning and real-world execution.

Without a dedicated execution controller, the platform cannot handle complex, multi-step actions (such as booking a ticket, checking seat updates, and coordinating alternatives) in a safe, transactionally consistent manner. If one step fails, the customer is left with half-completed itineraries, which destroys brand trust and inflates operational support costs.

### Customer Motivation
Customers expect conversational travel assistants to act as competent human concierge agents. When a traveler approves a travel plan, they expect the system to handle the operations behind the scenes. They demand real-time transparency, safety guarantees (e.g., no double-billing), and graceful recovery when external systems fail.

### Operational Motivation
Handling failed transactions manually is a massive burden on the customer support team. If a booking fails halfway through, support agents must manually cancel the successful legs, issue refunds, and rebook passengers. The Execution Engine automates recovery and rollback procedures, drastically reducing manual support interventions.

### Platform Motivation
External railway reservation systems (like IRCTC) have strict operational constraints, including rate limits, booking windows, and transactional fees. An intelligent Execution Engine protects downstream services by batching requests, preventing duplicate actions, and verifying state transitions before calling external business partners.

### Strategic Motivation
This milestone completes the transactional lifecycle of the conversational agent. By moving from "suggesting plans" to "reliably executing plans," RailYatra shifts from a discovery tool to a complete transactional marketplace, unlocking new commission structures and premium subscription tiers.

### Long-Term Vision
The Execution Engine provides the blueprint for executing cross-provider travel itineraries (buses, flights, metro) and automated auxiliary bookings (hotels, cabs) in later phases of the RailYatra roadmap.

### Expected Business Outcome
* 25% reduction in manual booking reconciliation overhead.
* 35% decrease in customer churn caused by partial journey failures.
* 15% increase in gross booking value via successful multi-leg conversions.

---

## 3. Business Vision
The vision for the Execution Engine is to establish a secure, fault-tolerant, and state-aware operations coordinator that can fulfill any validated travel plan while maintaining absolute transparency and customer trust. The engine guarantees that either a plan is successfully completed in its entirety, or the traveler is safely returned to a consistent state with no orphan bookings or unresolved financial transactions.

---

## 4. Business Objectives
1. **Transaction Integrity**: Ensure that multi-leg journeys are completed atomically from a business perspective, eliminating partial states.
2. **Automated Compensation**: Automatically trigger reversal processes (e.g., cancellations or refund claims) when a plan step fails midway and cannot be resolved.
3. **Conversational Feedback**: Provide real-time, human-understandable progress updates to travelers during long-running execution sequences.
4. **Partner Protection**: Minimize API overhead and rate-limit violations on downstream partner networks through state checking and request throttling.

---

## 5. Business Scope
The scope of this business initiative includes:
* Coordinating sequential and parallel execution of approved travel plan steps (e.g., search, check availability, book, cancel).
* Evaluating execution results and determining business-level next steps (complete, retry, fallback, or cancel).
* Generating customer-facing progress updates and recovery prompts.
* Coordinating rollback workflows for failed multi-step bookings.
* Emitting execution metrics and audit logs for customer support visibility.

---

## 6. Out of Scope
The following areas are explicitly excluded from this milestone:
* **Direct Integration**: The implementation of actual network connections to IRCTC or external payment gateways (delegated to Infrastructure Layer).
* **Payment Processing**: The collection and handling of credit card data or merchant banking integration.
* **Customer UI**: The visual design of progress bars or chat bubbles on the web or mobile applications.
* **Non-Railway Execution**: Fulfilling bookings for ancillary services like hotels, cabs, or food delivery.

---

## 7. Business Assumptions
* Downstream railway services and internal database catalogs are available and return standardized responses.
* The traveler has provided valid payment authorizations and credentials before execution begins.
* The Planning & Decision Engine (Milestone 6.3) produces fully validated plan structures that do not contain business rule violations.

---

## 8. Stakeholders
* **Travelers**: The end-users who trust the platform to book their journeys.
* **Support Operations Team**: Staff who handle customer escalations when bookings go wrong.
* **Product Management**: Stakeholders focused on conversion rates, engagement, and customer satisfaction.
* **Finance Department**: Team tracking booking commissions, refund windows, and transactional costs.
* **External Business Partners (IRCTC/Ticketing Providers)**: Partners whose systems receive the booking requests.

---

## 9. Stakeholder Responsibilities
* **Product Management**: Define the tone of communication for progress updates and fallback proposals.
* **Support Operations**: Provide historical data on common execution failures to guide retry and rollback rules.
* **Finance**: Audit the engine's compensation rules to ensure no leakage of platform funds occurs during reversals.
* **Partners**: Maintain uptime and share updated rate-limiting guidelines.

---

## 10. Target Users
The target users are active railway passengers who utilize conversational interfaces to coordinate their travel. This includes business travelers, daily commuters, vacationing families, and senior citizens who may require assistance with multi-step itineraries.

---

## 11. User Personas

### Persona A: "The Multi-Leg Commuter" (Rajesh, 34)
* **Behavior**: Rajesh frequently travels between tier-2 cities for sales meetings. His journeys often require connecting trains.
* **Need**: Rajesh needs to know that if his second train booking fails due to sudden availability drops, the system will immediately notify him and suggest an alternative before finalizing the first ticket.
* **Pain Point**: Rajesh has previously been stuck with a confirmed outbound ticket but no return ticket, forcing him to spend hours on support calls.

### Persona B: "The Leisure Traveler" (Ananya, 28)
* **Behavior**: Ananya plans family vacations months in advance. She is sensitive to price and waitlist risk.
* **Need**: She wants clear, reassuring updates during the booking process.
* **Pain Point**: Ananya is anxious when systems go silent during execution, leading her to double-click buttons or close the app, which results in duplicate bookings.

---

## 12. Business Problems
* **Orphan Bookings**: Booking the first leg of a journey succeeds, but the second leg fails. The traveler is left with a useless ticket and must pay cancellation fees to revert it.
* **Silent Failures**: When downstream services time out, the system fails silently or displays a raw error code. The traveler does not know if their money was deducted or if they should try again.
* **Duplicate Actions**: Due to slow partner responses, users submit the same booking multiple times, resulting in duplicate ticket allocations and credit card charges.

---

## 13. Existing Challenges
* Internal systems currently lack a centralized coordinator to track the state of a multi-step execution.
* Reversal actions must be performed manually by support agents, creating an operational bottleneck during peak travel seasons.
* Partner APIs have high latency fluctuations, making traditional synchronous execution models unreliable.

---

## 14. Opportunity Analysis
Automating execution coordination presents a major opportunity to establish RailYatra as the most reliable conversational concierge in the Indian railway ecosystem. By guaranteeing transactional consistency and proactive failure handling, the platform can charge a premium convenience fee, knowing that customers will pay for peace of mind.

---

## 15. Customer Journey
1. **Approval**: The customer reviews a formulated travel plan and says, "Go ahead and book this."
2. **Initiation**: The system displays an execution startup confirmation: "Starting your booking process. Checking seats now..."
3. **Execution Updates**: The customer receives dynamic progress updates: "Seat checked successfully. Initiating ticket reservation with IRCTC..."
4. **Success/Failure handling**:
   * *Success*: Customer receives the PNR and ticket confirmation.
   * *Failure*: Customer is notified immediately: "The return seat is no longer available. Reverting your outbound ticket to prevent extra fees. Would you like to search for an alternative date?"

---

## 16. Business Capabilities
* **Atomic Step Coordination**: The ability to step through a sequence of actions, evaluating outcomes before proceeding.
* **Compensation Workflows**: The ability to trigger undo actions (e.g., ticket cancellation) for previously completed steps if a downstream failure occurs.
* **State Preservation**: The ability to persist the execution state across long timeouts.
* **Rate-Limit Management**: The ability to space out request dispatches to prevent overloading external partner systems.

---

## 17. Business Scenarios
* **Scenario A: Standard Connecting Booking** — Searching, checking availability on two connecting trains, and booking both.
* **Scenario B: Waitlist Recovery** — Checking PNR status; if still waitlisted, checking seat updates; if confirmation probability drops, proposing alternative bookings.
* **Scenario C: Multi-Passenger Cancellation** — Canceling tickets for multiple passengers simultaneously, verifying refund calculations before finalizing.

---

## 18. Primary Use Cases
* **UC-01: Fulfill Validated Travel Plan**: Coordinate the sequential execution of search, check, and booking steps to deliver a final PNR.
* **UC-02: Manage Partial Failure**: Detect a failure at step 2 of a 3-step plan, attempt localized retries, and if unsuccessful, execute reversals for step 1.
* **UC-03: Inform Traveler Progress**: Generate customer-facing status messages for each execution milestone.

---

## 19. Secondary Use Cases
* **UC-04: Throttling Outbound Traffic**: Delay step dispatch if partner response times exceed safety thresholds.
* **UC-05: Manual Support Escalation**: Route the execution context to a human operator if automated rollback fails.

---

## 20. Exceptional Scenarios
* **External Outage**: The partner ticketing system becomes entirely unresponsive midway through booking.
* **Inconsistent State**: A step reports success, but the verification step fails to find the ticket record.
* **User Interruption**: The user explicitly requests a cancel command while a booking step is in progress.

---

## 21. Business Rules
* **BR-EXEC-001 (Atomic Connecting Journeys)**: Connecting leg bookings must be treated as a single business transaction. If any leg fails and cannot be substituted, all legs must be reverted.
* **BR-EXEC-002 (Maximum Retries)**: No step may be retried more than three times against partner APIs to avoid account lockouts.
* **BR-EXEC-003 (Refund Protection)**: Reversal actions must occur within the partner's free cancellation window if possible.

---

## 22. Business Constraints
* **IRCTC Operating Hours**: No execution actions can be dispatched during daily system maintenance hours (typically 23:30 to 00:30 IST).
* **Payment Hold Limits**: Temporary holds on passenger credit cards must not exceed 15 minutes before the booking is completed or cancelled.

---

## 23. Business Risks
* **Financial Exposure**: If a cancellation step fails during a rollback, the platform may absorb the cost of the ticket to protect the customer.
* **Partner Penalties**: High frequency of retries may lead to temporary IP blocklisting by partner networks.
* **Loss of Trust**: Confusing progress updates during failures can cause panic and brand damage.

---

## 24. Risk Mitigation (Business Perspective)
* Implement a mandatory fallback to human operators if automated compensation steps fail.
* Enforce conservative rate-limiting policies at the platform entry point.
* Utilize clear, non-technical, and empathetic language for customer error messages.

---

## 25. Business Benefits
* Higher successful conversion rates for complex bookings.
* Reduced cost of customer support operations through automation.
* Lower platform operational costs from fewer external API retries.

---

## 26. Customer Benefits
* Peace of mind knowing connecting bookings are safe.
* Real-time transparency during execution.
* Clear options and automatic rollbacks if something goes wrong.

---

## 27. Operational Benefits
* Support queues are freed from routine booking error resolution.
* Automated logging makes it easier to audit transaction histories.

---

## 28. Success Metrics
* **Completion Rate**: 95%+ of initiated execution flows must complete successfully or rollback cleanly.
* **Support Reduction**: 30% reduction in support tickets categorized under "partial booking failures."
* **Customer Satisfaction (CSAT)**: Post-booking CSAT of 4.5/5.0 for multi-leg journeys.

---

## 29. KPIs
* **Mean Time to Reversal (MTTR)**: Average time to complete a cleanup rollback must be under 30 seconds.
* **API Overhead Ratio**: Ratio of API calls to finalized bookings should not exceed 2.2.
* **Orphan Rate**: Number of un-reverted partial bookings per 10,000 transactions must be zero.

---

## 30. Non-Functional Business Expectations
* **Scalability**: The business process must support 100,000 concurrent execution sessions during holiday booking rushes.
* **Auditability**: Every step outcome and decision must be stored in a permanent, immutable ledger for compliance review.

---

## 31. Regulatory Considerations
* **IRCTC Guidelines**: All bookings and cancellations must comply with official Indian Railways commercial rules.
* **Consumer Protection Act**: The platform must clearly state booking fees, refund turnaround times, and cancellation policies before execution starts.

---

## 32. Privacy Considerations
* **Credentials Protection**: Passenger names, ages, and IDs must only be shared with verified ticketing systems during execution.
* **Payment Security**: Card details must never be logged or stored within execution state histories.

---

## 33. Business Glossary
* **Orphan Booking**: A state where one part of a multi-leg journey is confirmed, but another necessary part has failed, leaving the traveler with an unusable ticket.
* **Rollback/Compensation**: An automated business process that cancels or reverts previous successful actions (like booking a ticket) when a downstream failure occurs.
* **Conversational Concierge**: An AI assistant capable of handling multi-turn, multi-action travel tasks on behalf of the customer.

---

## 34. Dependencies (Business Only)
* **Milestone 6.2 (IUE)**: Must correctly classify intent slots.
* **Milestone 6.3 (Planner)**: Must provide a valid Structured Travel Plan to execute.
* **Downstream Providers**: IRCTC booking gates must be active and accessible.

---

## 35. Future Business Evolution
* Supporting automated upgrades (e.g., auto-rebooking if a higher class becomes available at a lower price).
* Coordinating execution across multiple providers (e.g., train + hotel + cab packages).
* Integrating predictive booking execution based on historical rate trends.

---

## 36. Open Questions
* *What is the maximum financial loss the platform is willing to absorb per month for failed rollback adjustments?*
* *How should we handle situations where the user closes the app during a long-running execution?*

---

## 37. Deferred Business Decisions
* *Should we offer a paid premium insurance option that guarantees instant refunds if execution fails?* (Deferred to Phase 7 launch pricing reviews).
* *Integrating bus booking providers into the execution engine.* (Deferred to Milestone 6.6).

---

## 38. Recommendations
1. Establish a clear dashboard for support staff to monitor active execution pipelines and manually intervene if necessary.
2. Develop standard templates for system status messages during high-traffic holidays.

---

## 39. Discovery Readiness Assessment
The business discovery is complete. The business goals, operational bounds, risks, and rules for execution have been clearly articulated. The document is free of technical design specifications or code-level assumptions. It is ready for technical translation.

---

## 40. Discovery Completion Statement
The Discovery phase for Milestone 6.4 (Execution Engine) is officially **COMPLETE**. The business problem is thoroughly understood, requirements are aligned, and the milestone is approved to transition to the **Planning Phase**.
