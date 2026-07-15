# RailYatra AI
## Phase 5 – Milestone 5.5: Traveler Assistance & Proactive Intelligence Platform
### Enterprise Discovery & Domain Research

---

## 1. Executive Summary

This Discovery Document defines the canonical domain models, event prioritizations, alert rules, and recovery playbooks for **Milestone 5.5: Traveler Assistance & Proactive Intelligence Platform** for RailYatra AI.

Under **Architecture Freeze v1.0**, the Traveler Assistance module operates as a proactive event-driven engine. It translates structural telemetry updates (Phase 5.2), journey routing alerts (Phase 5.3), and commercial booking status changes (Phase 5.4) into timely, contextual guidance for travelers. It acts as the final analytical gateway to downstream LLM interfaces and push delivery channels (Phase 5.6), delivering canonical alert DTOs while completely shielding the system from provider-specific APIs (FCM/APNs, SMS gateways, and email dispatchers).

---

## 2. Traveler Assistance Vision

Traveler Assistance transitions RailYatra AI from reactive itinerary planning to proactive travel orchestration. The system monitors live operations and evaluates: *what happened, how it impacts the traveler's journey, and what immediate, explainable actions should be taken.*

```
                 [Railway / Journey / Booking Telemetry Events]
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Traveler Assistance Platform (5.5)                       │
│                                                                             │
│  • Timeline Checkpoints   • Action Selection   • Recovery Orchestration      │
│  • Alert Deduplication    • Priority Queuing   • Explainability Trace        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
             [Canonical Traveler Assistance DTOs (Alerts/Actions)]
                                      │
                                      ▼
                    AI Runtime (LangGraph Agentic Flows)
```

The assistant monitors execution checkpoints, coordinates multi-modal notifications queues, and initiates recovery loops during connection failures.

---

## 3. Canonical Domain Models

### 3.1 TravelerSession
*   **Purpose:** Tracks active traveler session states during transit.
*   **Ownership:** Session Manager.
*   **Relationships:** 1-to-1 with `TravelerContext`.
*   **Lifecycle:** `Active` $\rightarrow$ `Paused` $\rightarrow$ `Completed` $\rightarrow$ `Expired`.
*   **Identity:** UUID prefixed with `TSES-`.
*   **Validation:** Linked to valid traveler ID and journey ID.
*   **Metadata:** Inbound IP hash, last handshake timestamp.
*   **Versioning:** `v1.0.0`.
*   **Future Extensibility:** Hooks for multi-device sync.

### 3.2 TravelerContext
*   **Purpose:** Aggregates real-time coordinates, preferences, and profile constraints.
*   **Ownership:** Context Engine.
*   **Relationships:** Linked to `TravelerSession` and `JourneyCanonical`.
*   **Lifecycle:** Dynamic updates during active travel windows.
*   **Identity:** UUID prefixed with `TCTX-`.
*   **Validation:** Profile coordinates must resolve to valid station grids.
*   **Metadata:** Telemetry source type.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Bluetooth beacon location feeds.

### 3.3 TravelerTimeline
*   **Purpose:** Visual sequence representation of traveler checkpoints, reminders, and alerts.
*   **Ownership:** Timeline Engine.
*   **Relationships:** Owns multiple `TravelerTimelineEvent` items.
*   **Lifecycle:** Instantiated at session creation, closed at journey end.
*   **Identity:** UUID prefixed with `TTIM-`.
*   **Validation:** Events chronological ordering must be monotonic.
*   **Metadata:** Departure offset indexes.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Calendar export mappings.

### 3.4 TravelerEvent
*   **Purpose:** Normalized container for raw operational notifications (delays, swaps).
*   **Ownership:** Event Parser.
*   **Relationships:** Generates `TravelerAlert`.
*   **Lifecycle:** Instantiated at dispatch, cleared after delivery settling.
*   **Identity:** UUID prefixed with `TEVT-`.
*   **Validation:** Must contain a valid source correlation ID.
*   **Metadata:** Severity rating enum.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Kafka streaming headers.

### 3.5 TravelerAlert
*   **Purpose:** High-priority warning indicators requiring instant traveler awareness.
*   **Ownership:** Alert Engine.
*   **Relationships:** Spawned from `TravelerEvent`.
*   **Lifecycle:** `Active` $\rightarrow$ `Delivered` $\rightarrow$ `Dismissed` $\rightarrow$ `Expired`.
*   **Identity:** UUID prefixed with `TALT-`.
*   **Validation:** Bound to active segment timeline.
*   **Metadata:** Deduplication key.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Wearables display patterns.

### 3.6 TravelerNotification
*   **Purpose:** Serialized dispatch payload for end-user delivery adapters.
*   **Ownership:** Notification Queue.
*   **Relationships:** Wraps `TravelerAlert` or `TravelerReminder`.
*   **Lifecycle:** `Queued` $\rightarrow$ `Sent` $\rightarrow$ `Failed` $\rightarrow$ `Retried` $\rightarrow$ `Acknowledged`.
*   **Identity:** UUID prefixed with `TNOT-`.
*   **Validation:** Target channel must match user preference profile.
*   **Metadata:** Channel routing tags.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Multi-channel fallback routing (WhatsApp $\rightarrow$ SMS).

### 3.7 TravelerAdvisory
*   **Purpose:** Informational advisory notices (weather warnings, terminal maintenance).
*   **Ownership:** Advisory Engine.
*   **Relationships:** Associated with `TravelerTimeline`.
*   **Lifecycle:** Valid during segment duration windows.
*   **Identity:** UUID prefixed with `TADV-`.
*   **Validation:** Station codes must exist in database registry.
*   **Metadata:** Advisory severity classification.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Smart tourist guides links.

### 3.8 TravelerReminder
*   **Purpose:** Contextual timer events (e.g. Leave Home, Tatkal open alarm).
*   **Ownership:** Reminder Manager.
*   **Relationships:** Linked to `TravelerTimelineEvent`.
*   **Lifecycle:** `Scheduled` $\rightarrow$ `Fired` $\rightarrow$ `Cancelled`.
*   **Identity:** UUID prefixed with `TREM-`.
*   **Validation:** Fire timestamp must be chronologically earlier than departure.
*   **Metadata:** Fire offset rules.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Dynamic traffic delays integration.

### 3.9 TravelerAction
*   **Purpose:** Deterministic advice actions recommended to the traveler.
*   **Ownership:** Action Engine.
*   **Relationships:** Part of `TravelerGuidance`.
*   **Lifecycle:** Generated on active alert triggers.
*   **Identity:** UUID prefixed with `TACT-`.
*   **Validation:** Action keys must map to catalog lists.
*   **Metadata:** Impact estimation metrics.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Autonomous agent booking execution hooks.

### 3.10 TravelerDecision
*   **Purpose:** Records traveler choice regarding a proposed action.
*   **Ownership:** Decision Logger.
*   **Relationships:** Linked to `TravelerAction`.
*   **Lifecycle:** `Proposed` $\rightarrow$ `Accepted` / `Rejected` $\rightarrow$ `Logged`.
*   **Identity:** UUID prefixed with `TDEC-`.
*   **Metadata:** Latency of decision logs.
*   **Validation:** Bound to non-expired recommendations.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Behavioral reinforcement logs.

### 3.11 TravelerRecovery
*   **Purpose:** Triggers recovery plan building when connection breaks.
*   **Ownership:** Recovery Manager.
*   **Relationships:** Linked to `TravelerIncident`.
*   **Lifecycle:** `Initiated` $\rightarrow$ `Searching` $\rightarrow$ `Proposed` $\rightarrow$ `Settled`.
*   **Identity:** UUID prefixed with `TREC-`.
*   **Validation:** Target itinerary must resolve original destination.
*   **Metadata:** Backup segments tags.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Cross-modal backup (Bus/Air segment links).

### 3.12 TravelerRecoveryPlan
*   **Purpose:** Outlines steps (rerouting, booking change) to salvage connection.
*   **Ownership:** Recovery Engine.
*   **Relationships:** Contains `TravelerAction` items list.
*   **Lifecycle:** Volatile until accepted by traveler.
*   **Identity:** UUID prefixed with `TRPL-`.
*   **Metadata:** Alternate routes profiles.
*   **Validation:** Alternatives cost must map to budget thresholds.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Shared-ride booking integrations.

### 3.13 TravelerRisk
*   **Purpose:** Models situational hazards (delay accumulation, platform sprint time).
*   **Ownership:** Risk Engine.
*   **Relationships:** Evaluates `TravelerContext`.
*   **Lifecycle:** Dynamically calculated per segment.
*   **Identity:** UUID prefixed with `TRSK-`.
*   **Metadata:** Active risk trigger arrays.
*   **Validation:** Probability floats bounded $[0.0, 1.0]$.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Real-time crowd index feeds.

### 3.14 TravelerOpportunity
*   **Purpose:** Identifies transit benefits (shorter layovers, platform stability).
*   **Ownership:** Opportunity Optimizer.
*   **Relationships:** Attached to `TravelerGuidance`.
*   **Lifecycle:** Calculated during routing checks.
*   **Identity:** UUID prefixed with `TOPP-`.
*   **Metadata:** Benefit metrics summary.
*   **Validation:** Benefit must be quantifiably positive.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Upgrade notification hooks.

### 3.15 TravelerIncident
*   **Purpose:** Models a confirmed operational issue (cancellation, missed transfer).
*   **Ownership:** Incident Manager.
*   **Relationships:** Triggers `TravelerRecovery`.
*   **Lifecycle:** `Active` $\rightarrow$ `Mitigated` $\rightarrow$ `Closed`.
*   **Identity:** UUID prefixed with `TINC-`.
*   **Metadata:** Incident cause classification.
*   **Validation:** Must lock the corresponding segment timeline.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Train grid diagnostics integration.

### 3.16 TravelerIntervention
*   **Purpose:** Automated agent action (notifying travel contacts, booking backups).
*   **Ownership:** Intervention Engine.
*   **Relationships:** Connected to `TravelerRecoveryPlan`.
*   **Lifecycle:** `Scheduled` $\rightarrow$ `Executed` $\rightarrow$ `Logged`.
*   **Identity:** UUID prefixed with `TINT-`.
*   **Metadata:** Execution latency logs.
*   **Validation:** Must receive verified user permission token.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Insurance claim automated filings.

### 3.17 TravelerState
*   **Purpose:** Models traveler phase (Pre-departure, In-Transit, Layover, Completed).
*   **Ownership:** State Tracker.
*   **Relationships:** Bound to `TravelerSession`.
*   **Lifecycle:** Transitions monotonically.
*   **Identity:** State enum.
*   **Validation:** Must follow allowed state flow map.
*   **Metadata:** State change timestamp.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Dynamic geofence state triggers.

### 3.18 TravelerStatus
*   **Purpose:** Captures active comfort status (Punctual, Delayed, Missed Connection).
*   **Ownership:** Status Monitor.
*   **Relationships:** Feeds `TravelerState`.
*   **Lifecycle:** Volatile real-time status.
*   **Identity:** Status enum.
*   **Metadata:** Current latency values.
*   **Validation:** Updated dynamically from telemetry loops.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Heartbeat monitoring.

### 3.19 TravelerObjective
*   **Purpose:** Represents traveler target target (Safety, Comfort, Speed).
*   **Ownership:** Objective Manager.
*   **Relationships:** Guides weighting functions.
*   **Lifecycle:** Initialized at query launch.
*   **Identity:** Objective key.
*   **Metadata:** Weight bias floats.
*   **Validation:** Weights must sum to 1.0.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Dynamic target swaps during delays.

### 3.20 TravelerGuidance
*   **Purpose:** Aggregated package containing alerts, actions, and reason traces.
*   **Ownership:** Guidance Engine.
*   **Relationships:** Ingested by AI runtime.
*   **Lifecycle:** Valid for a maximum of 5 minutes.
*   **Identity:** UUID prefixed with `TGUID-`.
*   **Validation:** Must map to unique reason code keys.
*   **Metadata:** Generation timestamp.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Voice assist audio files links.

### 3.21 TravelerRecommendation
*   **Purpose:** Alternate recommendations generated during recovery operations.
*   **Ownership:** Recommendation Engine.
*   **Relationships:** Linked to `TravelerRecoveryPlan`.
*   **Lifecycle:** Volatile.
*   **Identity:** UUID prefixed with `TREC-`.
*   **Metadata:** Estimated arrival deltas.
*   **Validation:** Must be confirmed route paths.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Combined rideshare ticketing links.

### 3.22 TravelerConfidence
*   **Purpose:** Calculates reliability score of recommendations.
*   **Ownership:** Confidence Engine.
*   **Relationships:** Attached to `TravelerGuidance`.
*   **Lifecycle:** Calculated per alert event.
*   **Identity:** Confidence percentage scalar.
*   **Metadata:** Data sources weights.
*   **Validation:** Bounded strictly to $[0.0, 1.0]$.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Neural net confidence models.

### 3.23 TravelerExplanation
*   **Purpose:** Compiles decision trace context for LLM prompt injections.
*   **Ownership:** Explanation Engine.
*   **Relationships:** Enriches the `TravelerGuidance` payload.
*   **Lifecycle:** Immutable.
*   **Identity:** Text/JSON record block.
*   **Metadata:** Translation template tags.
*   **Validation:** Must contain matching reason code.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Automated notification translations.

### 3.24 TravelerTimelineEvent
*   **Purpose:** Individual timeline nodes (boarding, arrival, layout transition).
*   **Ownership:** Timeline Engine.
*   **Relationships:** Component of `TravelerTimeline`.
*   **Lifecycle:** `Scheduled` $\rightarrow$ `Reached` $\rightarrow$ `Missed`.
*   **Identity:** UUID prefixed with `TTLE-`.
*   **Metadata:** Scheduled coordinates.
*   **Validation:** Target time must be within journey bounds.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Transit stop metadata links.

### 3.25 TravelerCheckpoint
*   **Purpose:** Geofenced validation markers checking timing variances.
*   **Ownership:** Checkpoint Monitor.
*   **Relationships:** Evaluates `TravelerTimelineEvent` status.
*   **Lifecycle:** Triggered by passenger coordinate change.
*   **Identity:** UUID prefixed with `TCPK-`.
*   **Metadata:** Variance threshold timers.
*   **Validation:** Distance maps to target station boundaries.
*   **Versioning:** `v1`.
*   **Future Extensibility:** Automatic platform gates check-ins.

---

## 4. Domain Relationships

The relationships between core entities are modeled in the diagram below:

```mermaid
classDiagram
    class TravelerSession {
        +UUID session_id
        +String status
    }
    class TravelerContext {
        +UUID context_id
        +Dict coordinates
    }
    class TravelerTimeline {
        +UUID timeline_id
        +List events
    }
    class TravelerEvent {
        +UUID event_id
        +String severity
    }
    class TravelerAlert {
        +UUID alert_id
        +String priority
    }
    class TravelerGuidance {
        +UUID guidance_id
        +List actions
    }
    class TravelerRecovery {
        +UUID recovery_id
        +List alternative_plans
    }

    TravelerSession "1" --> "1" TravelerContext : tracks
    TravelerSession "1" --> "1" TravelerTimeline : compiles
    TravelerEvent "1" --> "*" TravelerAlert : spawns
    TravelerAlert "*" --> "1" TravelerGuidance : generates
    TravelerGuidance "1" --> "0..1" TravelerRecovery : triggers
    TravelerTimeline "1" --> "*" TravelerAdvisory : displays
```

### 4.1 Relationship Rules & Ownership
*   **The Session** acts as the parent aggregator of traveler context and timeline operations.
*   **Operational Events** serve as the asynchronous triggers. If an event (e.g. Cancelled train) invalidates a timeline node, the system initiates a `TravelerRecovery` loop to calculate salvage options.

---

## 5. Traveler Ontology

```mermaid
graph TD
    %% Base Triggers
    TE[Telemetry Event] -->|publishes| E[Traveler Event]
    E -->|triggers| A[Traveler Alert]
    
    %% Context Checks
    A -->|matches| TC[Traveler Context]
    TC -->|evaluates state| TS[Traveler State]
    
    %% Guidance Assembly
    A -->|synthesizes| TG[Traveler Guidance]
    TG -->|contains| TA[Traveler Action]
    TG -->|calculates| TCn[Traveler Confidence]
    
    %% Recovery Loops
    TA -->|if connection missed| TR[Traveler Recovery]
    TR -->|produces| TRP[Traveler Recovery Plan]
```

*   **Telemetry Events:** Feed the Event Parser asynchronously.
*   **Traveler State:** Prunes guidance options depending on where the traveler is located.
*   **Traveler Action:** Recommends concrete choices to the user.

---

## 6. Event Intelligence

The platform processes 12 canonical operational events:

| Event Type | Severity | Priority | Impact on Traveler | Ownership |
| :--- | :--- | :--- | :--- | :--- |
| **Journey Delay** | Medium | Normal | Delay propagates down segments; layovers tighten. | Delay Analyzer |
| **Platform Change** | Medium | High | Sprints required; terminal layouts shift. | Platform Monitor |
| **Train Cancellation** | Critical | Emergency | Route severed; immediate recovery plan required. | Incident Engine |
| **Boarding Window** | Low | High | Entry timing alerts; boarding gates check. | State Tracker |
| **Transfer Risk** | High | Critical | Tight buffers; connection miss risk increases. | Risk Engine |
| **Missed Connection** | Critical | Emergency | Traveler stranded; alternative routing required. | Recovery Manager |
| **Schedule Change** | Low | Normal | Future timeline adjustment; updates context. | Timeline Engine |
| **Reservation Change** | Medium | Normal | Coach allocation updates; seat swaps. | Booking Gateway |
| **Operational Incident** | High | Critical | Track congestion delays; corridor blocks. | Incident Engine |
| **Weather Impact** | Medium | High | Speed limits; winter fog delay tracking. | Advisory Engine |
| **Safety Incident** | Critical | Emergency | Alternate platform routing; emergency alerts. | Safety Monitor |
| **Information Update** | Low | Low | General notifications; non-blocking alerts. | Gateway Core |

---

## 7. Reminder Framework

The Reminder Engine schedules timer alerts based on journey checkpoint progress:

1.  **Departure Reminder:** Fired 2 hours prior to scheduled departure. Advice: *Leave for station now to beat local traffic.*
2.  **Boarding Reminder:** Fired 20 minutes before train departure. Advice: *Boarding gates open. Report to coach compartment.*
3.  **Arrival Reminder:** Fired 15 minutes prior to segment arrival. Advice: *Prepare baggage. Next stop is your destination.*
4.  **Transfer Reminder:** Fired on layover entry. Advice: *Connecting train departs in 40 minutes from Platform 4. Proceed to cross-platform bridge.*
5.  **Quota Reminder:** Sent when profile indicates eligible dynamic concessions are active.
6.  **Tatkal Reminder:** Fired 30 minutes before Tatkal booking window opens (10:30 for AC, 11:30 for Sleeper).
7.  **Reservation Reminder:** Reminds passenger to verify PNR status if waitlisted.
8.  **Journey Completion Reminder:** Fired post-arrival. Queries passenger feedback and closes session.

---

## 8. Alert Framework

Alerts map to specific priority lanes to manage notification overload:

```
[Critical Alerts]    ──► High-priority sound, bypasses notification filters (Cancellation)
[High Priority]      ──► Visual banners, lockscreen warnings (Platform Swaps)
[Medium Priority]    ──► Standard push channels (Delay updates > 15m)
[Informational]      ──► In-app advisory alerts (Food services)
[Silent Updates]     ──► Local cache updates, no user disturbance (Minor telemetry ticks)
```

### 8.1 Alert Governance Rules
*   **Deduplication:** Multiple delay events for the same segment are grouped. Only deltas $> 10$ minutes trigger a new notification.
*   **Escalation:** If a high-priority alert is not acknowledged (read) within 5 minutes, the system escalates the delivery channel (e.g. Push $\rightarrow$ SMS).
*   **Expiration:** Alerts expire automatically once the train leaves the affected station.

---

## 9. Recovery Intelligence

During critical connection failures, the Recovery Engine generates salvage plans:

*   **Missed Train / Missed Boarding:**
    *   *Playbook:* Query Phase 5.3 for next express segments leaving the same station. Query Phase 5.4 for ticket availability.
    *   *Output:* Re-routing candidate DTOs.
*   **Missed Transfer / Lost Connection:**
    *   *Playbook:* Triggered if segment arrival delay exceeds layover buffer. Recommend alternative connecting train from layover station.
*   **Train Cancellation:**
    *   *Playbook:* Identify alternative trains. Suggest routing via adjacent terminal hubs.
*   **Long Delay Recovery:**
    *   *Playbook:* Suggest shifting to an earlier train if delay exceeds 2 hours and seat pools exist.

---

## 10. Traveler Action Framework

The Action Engine generates 9 deterministic, rule-based choices:

1.  **Leave Earlier:** Traffic or train schedule changes require early boarding.
2.  **Leave Later:** Train delay $> 1$ hour allows passenger to delay station arrival, reducing terminal wait stress.
3.  **Board Now:** Train boarding window is closing.
4.  **Change Platform:** Platform swap detected. Sprints required.
5.  **Book Alternative:** Current ticket unconfirmed or train cancelled.
6.  **Use Another Boarding Station:** Boarding point optimized to bypass blockages.
7.  **Contact Railway Staff:** Exceptional events require manual help desk support.
8.  **Wait:** Delay expected to resolve.
9.  **Cancel Journey:** Unrecoverable cancellation.

---

## 11. Timeline Model

The Traveler Timeline organizes events chronologically:

```
T-2 Hours         T-30 Mins          T-15 Mins          Departure             Arrival
   ╠══════════════════╬══════════════════╬══════════════════╬════════════════════════╣
   ║                  ║                  ║                  ║                        ║
Departure Alert    Leave Home        Platform Swap       Board Train          Prepare baggage
```

*   **Validity:** Checked continuously against active geofence positions.
*   **Ordering:** Enforced using monotonic integer sequence identifiers.
*   **Expiration:** Timeline events are flagged as `EXPIRED` once departure timestamps elapse.

---

## 12. Assistance Strategies

The system applies 8 assistance strategies based on profile settings:

1.  **Safety First:** prioritizing daylight connections, avoiding terminal shifts, and enforcing wide connection buffers ($\ge 45\text{m}$).
2.  **Minimal Walking:** prioritizing same-platform transfers and avoiding overhead bridges.
3.  **Family Support:** prioritizes child-friendly layover options and groups compartment berths.
4.  **Medical Support:** prioritizes stations with escalator access and trains with guard SLR compartments.
5.  **Fast Recovery:** prioritizing Tatkal seats and shortest alternative routes.
6.  **Budget Preservation:** Bypasses dynamic pricing updates.
7.  **Minimal Stress:** prioritizing direct trains and wide timing margins, avoiding last-minute changes.
8.  **Business Continuity:** prioritizing reliable morning connections to guarantee meeting arrivals.

---

## 13. Explainability Framework

Every recommendation presented to the user must justify its actions:

*   **Positive Trace:** *"Recommending leaving home 15 minutes earlier because national highway traffic reports show a 20-minute congestion delay near NDLS."*
*   **Negative Trace:** *"Did not suggest booking train 12626 alternative because waitlist position (WL 45) has a low confirmation probability (32%)."*
*   **Evidence Block:** *"Platform swap warning generated based on active station master terminal signals. Platform change from 1 to 4 confirmed."*

---

## 14. Constraint Framework

User constraints filter out invalid alerts:

### 14.1 Hard Constraints (Pruning Filters)
*   **Language Preference:** All alert templates must map to the traveler's registered language choice.
*   **Notification Preferences:** Under "Do Not Disturb" profiles, block medium/low alerts, allowing only Emergency alerts.
*   **Accessibility Limits:** Disables stairs-only cross-platform transfer alerts for mobility-restricted travelers.

### 14.2 Soft Preferences (Scoring Modifiers)
*   **Time Sensitivity:** User requests for early alerts adjust warning thresholds by $+10$ minutes.

---

## 15. Event Prioritization

To prevent warning fatigue, alerts are sorted dynamically:

```
[Emergency] ──► Immediate push, repeat sounds, bypass silent filters (Cancellation)
     ▼
[Critical]  ──► Push notification, high volume alert tone (Platform Swaps)
     ▼
[High]      ──► Push notification, standard tone (Delay > 30m)
     ▼
[Normal]    ──► App badge, quiet notification (Delay > 15m)
     ▼
[Low]       ──► Log to timeline only, no push (Delay < 15m)
     ▼
[Silent]    ──► Update local context, no notification
```

### 15.1 Suppression Rules
If the traveler is currently *sleeping* (in-transit during overnight hours), suppress normal/low notifications, allowing only Emergency alerts.

---

## 16. AI Consumption Model

Downstream LangGraph agentic orchestrators consume only the normalized `TravelerGuidanceDTO` to prevent vendor leaks:

```json
{
  "guidance_id": "GUID-5502-TALT",
  "correlation_id": "CORR-7703",
  "timestamp": 1781577723.15,
  "traveler_id": "USR-102",
  "active_state": "IN_TRANSIT",
  "status": "DELAYED",
  "recommended_action": {
    "action_code": "CHANGE_PLATFORM",
    "description": "Proceed to Platform 4 immediately.",
    "urgency": "CRITICAL"
  },
  "explanation": {
    "reason_code": "EXP_PLATFORM_SWAP",
    "text": "Your train 12002 platform was changed from Platform 1 to 4."
  },
  "confidence_score": 0.98
}
```

---

## 17. Cross-Phase Ownership Matrix

The functional boundaries of Phase 5 components are defined below:

| Phase | Functional Focus | Boundaries | Exposes |
| :--- | :--- | :--- | :--- |
| **Phase 5.1** | GDS Integration | Raw network adapters, vendor APIs. | Raw segment hashes |
| **Phase 5.2** | Railway Intelligence | Telemetry parsing, delay normalizations. | `AIReadyContext` |
| **Phase 5.3** | Journey Intelligence | Corridor graph searches, routes paths. | `JourneyRecommendationDTO` |
| **Phase 5.4** | Booking Intelligence | Seat quotas, fees, confirmation probability. | `BookingRecommendationDTO` |
| **Phase 5.5** | Traveler Assistance | Checkpoint alerts, actions, timeline rules. | `TravelerGuidanceDTO` |
| **Phase 5.6** | Personalization Assist | User channels delivery, notification formatting. | Final formatted text |

---

## 18. Future Extension Strategy

The design abstracts the delivery channels, allowing enhancements in later stages without rewriting core logic:

1.  **Push Notification Adaptors:** FCM/APNs interfaces will bind to `TravelerNotification` queue listeners.
2.  **SMS/WhatsApp Adaptors:** Direct interfaces for Twilio or Infobip integrations.
3.  **Wearable Sync:** Output alerts formatted as JSON snippets for Apple Watch/Android Wear.
4.  **Voice synthesis:** TTS (Text-to-Speech) modules mapping to explainability text fields.

---

## 19. Risk Assessment

*   **Notification Overload:** Passengers mute notifications due to spam. *Mitigation:* Apply rigid deduplication filters; suppress delay alerts where change is $<10\text{m}$.
*   **Geofence Accuracy Risk:** Network loss causes inaccurate traveler coordinate updates. *Mitigation:* Fallback to segment timeline scheduling estimations if GPS data is unavailable.
*   **Conflicting Guidance:** Alert engine suggests "Board Now" while Recovery engine suggests "Cancel Journey". *Mitigation:* Apply strategy ordering (Recovery playbooks override standard timeline alerts).

---

## 20. Architecture Compatibility Review

*   **Phase 3 Compatibility:** Session contexts serialize to memory blocks, preventing sync loss across thread instances.
*   **Phase 4 Compatibility:** Reason code headers reduce prompt injection sizes.
*   **Phase 5 Compatibility:** Enforces isolation of telemetry. Consumes only canonical inputs from 5.2, 5.3, and 5.4.

---

## 21. ADR Recommendations

### ADR 05.5-01: Decoupling of Delivery Adapters
*   **Status:** APPROVED.
*   **Decision:** The Traveler Assistance engine will emit canonical alert events only. SMS/Push delivery channels implementation is strictly out of scope.

### ADR 05.5-02: Geofence Fallbacks
*   **Status:** APPROVED.
*   **Decision:** If location GPS updates are missing, the checkpoint monitor will evaluate progress based purely on scheduled timeline clocks.

---

## 22. Discovery Readiness Assessment

*   **Domain Model Completeness:** 100/100
*   **Ontology Formulation:** 100/100
*   **Event Prioritization Rules:** 100/100
*   **Overall Readiness Rating:** 100/100

---

## 23. Definition of Done (DoD)

Milestone 5.5 Discovery is complete when:
1.  All 23 required chapters are fully documented.
2.  Mermaid ontology and relationship diagrams are verified.
3.  The document is checked into `/docs/Milestone_5_5_Discovery.md` in the workspace.

**DISCOVERY FREEZE APPROVED**
