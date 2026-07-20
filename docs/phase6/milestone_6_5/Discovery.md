# Phase 6 — Milestone 6.5 Enterprise Business Discovery
## AI Memory Platform

---

## PART 1 — Enterprise Discovery Foundation

### 1. Document Control

| Metadata Field | Value |
| :--- | :--- |
| **Document Reference** | RY-P6-M6.5-DISC-3.1 |
| **Version** | 3.1.0 |
| **Status** | APPROVED FOR PLANNING |
| **Document Owner** | Chief Product Officer |
| **Architecture Review Authority** | Enterprise Architecture Review Board (ARB) |
| **Authors** | Chief Product Officer, Principal Business Architect, Enterprise Business Analyst |
| **Approvers** | Enterprise Governance Committee, Technical Design Authority, Product Sponsor |
| **Classification** | Internal Enterprise Confidential |
| **Governing References** | `Phase6_Engineering_Constitution.md`, `Enterprise Discovery Standard v3.1` |
| **Related Documents** | `Phase6_Roadmap.md`, `M6.4/Discovery.md`, `M6.4/Planning.md`, `M6.4/IEP.md` |

#### Revision History
| Date | Version | Description | Authors |
| :--- | :---: | :--- | :--- |
| 2026-07-21 | 1.0.0 | Initial baseline draft for memory capability concepts. | Product Team |
| 2026-07-21 | 2.0.0 | Expanded business capabilities and customer journeys. | Business Analyst Group |
| 2026-07-21 | 3.0.0 | Compliance alignment with Enterprise Discovery Standard v3.1. | Governance Committee |
| 2026-07-21 | 3.1.0 | Final ARB refinement for Milestone 6.5. | ARB Board |

#### Purpose
This document establishes the business case, strategic drivers, operational workflows, risk parameters, and success metrics for the **AI Memory Platform** (Milestone 6.5). It answers the questions of *why* this memory function is necessary, *what* business and customer problems it addresses, and *who* is affected, serving as the official business input for the subsequent Planning phase.

---

### 2. Executive Summary

#### Business Motivation
In the digital travel market, user experience is the primary driver of customer retention. The RailYatra platform has successfully implemented intent parsing, classification, planning, and execution. However, the current assistant lacks long-term context: it has "session amnesia." Every time a traveler interacts with the assistant, they are treated as a complete stranger. 

This lack of persistent memory results in high conversational friction (users must repeatedly enter passenger details, seating preferences, and frequent routes) and limits personalization capabilities. The AI Memory Platform is required to establish a secure, compliant, and structured memory engine that retains intelligence across multiple sessions.

#### Customer Motivation
Travelers demand a personalized assistant that remembers their preferences (e.g., lower berth preference for senior citizens, window seats, vegetarian food choices, and preferred departure times). They expect the assistant to recognize their repeat journeys (e.g., "NDLS to PUNE commute on Fridays") and resume interrupted booking workflows without forcing them to re-enter information.

#### Operational Motivation
A large portion of customer support requests stem from travelers dropping out of booking flows due to friction, or contacting support to modify passenger details they had entered incorrectly. By remembering verified passenger profiles and preferences, the platform prevents input mistakes, streamlines booking completions, and reduces the support burden.

#### Strategic Motivation
This milestone transitions the platform from a transactional travel agent tool into a proactive travel companion. Persistent intelligence drives customer loyalty, builds trust, and allows RailYatra to offer premium subscription services based on automated, context-aware travel coordination.

#### Expected Business Outcome
* 30% reduction in average conversational steps required to complete a booking.
* 25% increase in repeat passenger booking conversions.
* 40% reduction in customer drop-off rates during multi-step booking workflows.

---

### 3. Business Vision
The vision for the AI Memory Platform is to build a secure, transparent, and persistent intelligence layer that acts as the long-term memory of the RailYatra platform. It enables the assistant to remember, learn, and dynamically adjust to each traveler's behavior while respecting customer privacy, consent, and data ownership.

---

### 4. Strategic Motivation
The competitive landscape of travel assistants is moving from generic query engines to hyper-personalized concierges. A persistent memory platform is a strategic necessity to secure RailYatra's market position, drive long-term traveler engagement, and prepare the enterprise for upcoming multi-agent booking networks.

---

### 5. Business Objectives
1. **Friction Reduction**: Eliminate repetitive data entry for passengers, preferences, and routes.
2. **Context Persistence**: Enable travelers to resume interrupted booking workflows across different sessions and devices.
3. **Hyper-Personalization**: Formulate plans tailored to traveler behavior, class preferences, and demographic concessions.
4. **Privacy First**: Implement strict consent gates, allowing users to view, edit, or delete their remembered profiles at any time.

---

### 6. Business Scope
* Conceptual definition of traveler profile and preference memory.
* Continuous learning of route preferences and trip frequencies.
* Resuming interrupted conversations and workflows across sessions.
* Transparent controls allowing travelers to view, edit, or delete memories.
* Consent management and policy compliance rules for memory retention.

---

### 7. Out of Scope
* Technical databases, schemas, indexes, or vector indexing strategies.
* Large Language Model (LLM) selection or prompt formatting.
* Visual interface designs for memory dashboards.
* Storing payment data, credit card details, or banking authentication.

---

### 8. Business Assumptions
* Travelers are willing to share preferences and booking history in exchange for a streamlined booking experience.
* The Intent Understanding and Planning engines can consume stored memory parameters to personalize recommendations.
* Internal security systems protect stored customer profiles against unauthorized access.

---

### 9. Business Constraints
* **Privacy Compliance**: The platform must comply with the Digital Personal Data Protection Act (DPDP) and national privacy mandates.
* **Consent Control**: Travelers must explicitly opt-in before their behavior is analyzed or stored.
* **Actionable Expiry**: Stored preferences that remain unused for over 12 months must be flagged for review or automated deletion.

---

### 10. Stakeholders
* **Travelers**: End-users who share preferences and expect a seamless journey.
* **Customer Support Operations**: Staff managing escalated booking and profile problems.
* **Product & Personalization Teams**: Stakeholders tracking user retention and booking conversion metrics.
* **Privacy & Compliance Officer**: Governance lead reviewing regulatory compliance.
* **Marketing & Loyalty Team**: Stakeholders designing promotional packages based on traveler behavior.

---

### 11. Stakeholder Responsibilities
* **Product & Personalization Teams**: Define preferences mapping rules and conversion optimization goals.
* **Privacy & Compliance Officer**: Define DPDP opt-in guidelines and auditing requirements.
* **Support Operations**: Provide feedback on frequent traveler profile mistakes.
* **Loyalty Team**: Guide marketing capability constraints.

---

### 12. Target Users
Target users are business professionals, family vacation coordinators, daily commuters, and senior citizens who frequently purchase railway tickets and value a personalized, low-friction booking experience.

---

### 13. User Personas

#### Persona A: "The Senior Commuter" (Mr. Sharma, 67)
* **Profile**: Retired government employee traveling to visit family.
* **Needs**: Needs a lower berth seat due to mobility constraints and senior concession booking automatically applied.
* **Pain Point**: Finds typing on small phone keyboards tedious. Gets frustrated entering his age, concession status, and berth preferences on every booking.
* **Memory Value**: Assistant remembers his birth date and berth preference, applying them automatically.

#### Persona B: "The Weekend Consultant" (Priya, 31)
* **Profile**: Management consultant commuting weekly between Delhi and Mumbai.
* **Needs**: Prefers fast express trains departing after 18:00, booking CC class.
* **Pain Point**: Frequently gets interrupted by work calls during booking and has to restart the plan from scratch.
* **Memory Value**: Assistant resumes her booking exactly where she left off and prioritizes late evening express options.

---

## PART 2 — Business Problem Analysis

### 14. Existing Challenges
The current RailYatra platform operates as a stateless transaction engine. Each interaction is isolated. This results in:
* Repeated collection of identical passenger details.
* Resetting context when a user drops out of a session.
* Under-utilization of historical data.

---

### 15. Customer Pain Points
* **Cognitive Load**: Retyping multi-passenger details (names, ages, IDs) is tedious and error-prone.
* **Friction on Interruption**: If the network drops or the traveler gets interrupted, they must rebuild their multi-leg itinerary.
* **Generic Recommendations**: High-budget business travelers are shown slow passenger trains, and price-sensitive travelers are shown expensive premium classes by default.

---

### 16. Operational Pain Points
* **Profile Errors**: Travelers frequently mistype their names or ages, causing invalid ticket bookings. Correcting these errors requires manual support team intervention and cancellation fees.
* **Session Drops**: Drop-offs are high during multi-passenger booking steps due to the time required to compile all information manually.

---

### 17. AI Memory Problem Statement
The assistant lacks the ability to link past context with current sessions. Without a memory platform, the agent cannot learn user habits, personalize routes, or support long-running workflows, remaining a reactive utility instead of an intelligent companion.

---

### 18. Opportunity Analysis
Persistent memory creates an opportunity to build a high-conversion booking engine. By predicting user choices and auto-filling forms, RailYatra can reduce booking times from 3 minutes to under 30 seconds, driving user retention and market share.

---

### 19. Current Journey Without Memory
1. Traveler initiates chat: "Book ticket to Pune."
2. Assistant asks: "Where are you traveling from?"
3. Traveler answers: "Delhi."
4. Assistant asks: "What date? What class? Who is traveling? What is their age?"
5. Traveler enters details for the tenth time.
6. Connection drops. Traveler re-opens chat and must repeat steps 1–5.

---

### 20. Future Journey With Memory
1. Traveler initiates chat: "Book my usual weekend ticket to Pune."
2. Assistant responds: "Sure, Mr. Sharma. Booking your Delhi-Pune express on Friday, CC class, for yourself (age 67, senior concession, lower berth). Shall I proceed to payment?"
3. Traveler answers: "Yes." (Workflow completed in one turn).
4. Connection drops. Upon return, Assistant states: "I saved your Delhi-Pune booking progress. Say 'resume' to finish payment."

---

## PART 3 — Business Capabilities

### 21. Memory Capability Model

```
                         [AI Memory Capabilities]
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
[Traveler Preferences]      [Context Persistence]      [Privacy & Control]
  - Passenger Profiles        - Workflow Resumption      - Consent Management
  - Route History             - Multi-Session Context    - View/Edit/Delete
  - Dietary/Berth choices                                - Data Expiration
```

---

### 22. Business Scenarios
* **Scenario A: Automated Concession Application** — System remembers a passenger's age and automatically applies senior concessions on relevant plans.
* **Scenario B: Disrupted Workflow Resumption** — Traveler starts booking a return trip, drops off for two hours, and resumes the booking process with full context.
* **Scenario C: Route Preference Optimization** — Traveler frequently travels NDLS-BCT. Assistant automatically prioritizes NDLS-BCT route options during generic "book train" requests.

---

### 23. Customer Journeys
* **Onboarding**: User opts in to memory storage.
* **Recall**: User triggers booking; assistant recalls profiles and preferences.
* **Management**: User opens memory settings, views stored passenger profiles, edits a typo, and deletes an old route preference.

---

### 24. Primary Use Cases
* **UC-MEM-01: Store Passenger Profile**: Remember names, ages, and genders of frequent companions.
* **UC-MEM-02: Auto-Fill Booking Parameters**: Automatically inject remembered seat and food preferences.
* **UC-MEM-03: Resume Interrupted Booking Saga**: Reload pending workflows from the execution context.

---

### 25. Secondary Use Cases
* **UC-MEM-04: Learn Route Frequencies**: Classify and store frequent origin-destination pairs.
* **UC-MEM-05: Audit Memory Consent**: Verify that memory storage actions have active customer consent flags.

---

### 26. Exceptional Scenarios
* **Consent Withdrawal**: User withdraws consent mid-session; system must immediately purge all stored memory.
* **Conflicting Preferences**: User books SL class twice and 1AC class twice; system prompts for preferred class priority.

---

## PART 4 — Business Rules

### 27. Business Rules
* **BR-MEM-001 (Explicit Opt-In)**: No traveler interaction data may be stored in long-term memory without verified user consent.
* **BR-MEM-002 (Immutable Identification)**: Passenger names and government ID categories cannot be updated if linked to an active, uncompleted execution session.
* **BR-MEM-003 (Concession Verification)**: Automatic concession applications must be re-verified against profile age rules before every plan submission.

---

### 28. Business Constraints
* **DPDP Act Compliance**: Memory storage must support "the right to be forgotten."
* **Storage Lifespan**: Inactive travel memories must be purged after 365 days of user inactivity.

---

### 29. Privacy Expectations
Travelers expect that their memory profile is private, is not shared with third-party advertisers, and is used exclusively to improve their experience on the RailYatra platform.

---

### 30. Consent Expectations
Consent must be granular: travelers can consent to remembering passenger profiles while opting out of route tracking.

---

### 31. Data Ownership Principles
* The customer owns their memory data.
* RailYatra acts as the data custodian.
* The customer has the right to export their stored profiles.

---

### 32. Memory Lifecycle (Business Perspective)
* **Birth**: User grants consent, memory is recorded during interaction.
* **Maturity**: Memory is recalled to personalize bookings and updated based on changes.
* **Expiration**: Memory is deleted due to user request, consent withdrawal, or inactivity timeout.

---

### 33. Memory Retention Expectations
* Profiles: Retained until deleted by the user.
* Conversational Context: Retained for 7 days to support workflow resumption.
* Route Analytics: Aggregated and retained for 180 days.

---

### 34. Memory Forgetting Expectations
When a traveler requests "forget my details," all associated profile records and companions must be deleted from active storage within 24 hours.

---

### 35. Conflict Resolution Expectations
If a traveler updates a preference (e.g. changes seat choice from Window to Aisle), the new preference overrides the historical choice.

---

## PART 5 — Business Value

### 36. Business Benefits
* Higher completion rates for compound bookings.
* Improved customer lifetime value (CLV) due to personalization.
* Higher revenue from premium feature adoptions.

---

### 37. Customer Benefits
* Fast, one-click booking experiences.
* Reduced cognitive load during travel planning.
* Reassuring continuity during connection dropouts.

---

### 38. Operational Benefits
* Less support overhead for profile correction claims.
* Fewer failed transactions caused by invalid passenger inputs.

---

### 39. AI Benefits
Enables the assistant to maintain logical continuity, leading to natural and contextually aware travel planning.

---

### 40. Support Benefits
Enables support agents to view traveler preferences, helping them resolve booking issues faster.

---

### 41. Competitive Advantage
RailYatra becomes the only travel platform that remembers passenger profiles and preferences across sessions, setting a new standard for customer loyalty.

---

## PART 6 — Success Measurement

### 42. Success Metrics
* **Task Duration Reduction**: Average booking completion time reduced by 50%.
* **Workflow Resumption Rate**: 80%+ of dropped booking sessions resumed within 24 hours.
* **Consent Rate**: 75%+ of active travelers opt-in to the memory platform.

---

### 43. KPIs
* **Form Auto-Fill Rate**: Percentage of passenger inputs completed automatically.
* **Memory Accuracy**: Percentage of auto-filled inputs completed without manual changes.
* **Support Contact Deflection**: Reduction in profile-related support calls.

---

### 44. Business Risks
* **Regulatory Penalties**: Non-compliance with DPDP rules could lead to fines.
* **Security Breaches**: Unauthorized access to personal traveler profiles.
* **Creep Factor**: Overly proactive personalization that makes users uncomfortable.

---

### 45. Risk Mitigation
* Implement clear opt-in screens during onboarding.
* Keep personal passenger data separate from behavioral analytics.
* Mask sensitive fields by default in conversational displays.

---

### 46. Business Dependencies
* **Milestone 6.3 (Planner)**: Must consume memory parameters to personalize plans.
* **Milestone 6.4 (Execution)**: Must emit step outcomes to update execution histories.

---

## PART 7 — Governance

### 47. Privacy Considerations
All profile data must be encrypted in transit and at rest. Security reviews must validate the memory deletion process.

---

### 48. Regulatory Considerations
Compliant with DPDP Act, railway ticketing terms, and data localization guidelines.

---

### 49. Business Glossary
* **Session Amnesia**: A state where an assistant treats a returning customer as a complete stranger.
* **Opt-In Consent**: Explicit user approval required before data is stored.
* **Right to be Forgotten**: The regulatory requirement to delete all customer records upon request.

---

### 50. Future Business Evolution
* Supporting cross-provider preferences (e.g. hotel room preferences, preferred cab categories).
* Sharing memory profiles with corporate travel desks.
* Predictive booking alerts based on historical commute cycles.

---

### 51. Open Questions
* *How should we handle memory profiles for corporate accounts with multiple travelers?*
* *Should we offer a shared family memory option?*

---

### 52. Deferred Business Decisions
* *Sharing memory details with third-party logistics partners.* (Deferred to Phase 7).
* *Integrating biometric profile verification.* (Deferred to Phase 8).

---

### 53. Recommendations
1. Deploy a simple memory settings dashboard, allowing users to easily view what the assistant remembers about them.
2. Draft clear, conversational privacy prompts that explain the benefits of memory opt-in.

---

### 54. Discovery Readiness Assessment
The business discovery is complete. The motivations, opportunities, target personas, business rules, privacy guidelines, and success metrics have been defined without technical implementation leakage. It is ready for technical translation.

---

### 55. Discovery Completion Statement
The Discovery phase for Milestone 6.5 (AI Memory Platform) is officially **COMPLETE**. The business problem is understood, requirements are aligned, and the milestone is approved to transition to the **Planning Phase**.
