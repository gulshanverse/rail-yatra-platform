# RAILYATRA AI PLATFORM
## Phase 6 – Milestone 6.6: AI Response Composer & Explainability Platform
### ENTERPRISE ARCHITECTURE — PART 3: TACTICAL DOMAIN DESIGN

```
================================================================================
Document Type:      Tactical Domain Design (Aggregates, Entities, Value Objects)
Milestone:          6.6 – AI Response Composer & Explainability Platform
Version:            1.0
Status:             APPROVED ENTERPRISE ARCHITECTURE BASELINE
Domain:             AI Response Composition, Domain Models & Invariants
Target Audience:    Chief Domain Architect, Lead DDD Engineers, Domain Authors
================================================================================
```

---

## 1. AGGREGATE CATALOG & BOUNDARIES

Tactical domain design models the internal business concepts inside each bounded context.

```
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE AGGREGATE CATALOG                               |
+-----------------------------------------------------------------------------------+
| Aggregate Root         | Owned Entities & Value Objects    | Primary Invariant    |
+------------------------+-----------------------------------+----------------------+
| ResponseComposition    | ComposedSection, ActionChip       | Direct answer first  |
| ExplanationPayload     | JustificationNode, PolicyCitation | 100% evidence backed |
| ConflictArbitration    | TradeOffChoice, ResolutionFactor  | Safety overrides all |
| ConversationSession    | TurnSnapshot, ActiveIntent        | Session continuity   |
| ConfidenceAssessment   | ProbabilityScore, RiskBadge       | Disclose uncertainty |
+-----------------------------------------------------------------------------------+
```

---

## 2. AGGREGATE ROOT SPECIFICATIONS

### 2.1 `ResponseComposition` Aggregate Root
- **Business Purpose**: Encapsulates a complete synthesized response structure ready for user presentation.
- **Owned Elements**: `ComposedSection` (Entities), `ActionChip` (Value Objects), `ResponseSummary` (Value Object).
- **Protected Invariants**:
  1. The response must lead with a concise primary direct answer.
  2. PII must be masked before composition if consent is not verified.
  3. Contains at least one action guidance chip for multi-turn intent continuation.

### 2.2 `ExplanationPayload` Aggregate Root
- **Business Purpose**: Owns multi-tiered reasoning justifications for AI recommendations or predictions.
- **Owned Elements**: `JustificationNode` (Entities), `PolicyCitation` (Value Objects).
- **Protected Invariants**:
  1. Predictions with < 85% probability must include an explicit reasoning node.
  2. Policy statements must reference an active, valid IRCTC policy circular version.

---

## 3. ENTITY & VALUE OBJECT CATALOG

### 3.1 Entities (Identity-Bearing Business Concepts)
- `ComposedSection`: Distinct structural segment (e.g., Summary, Options Table, Warning Banner).
- `JustificationNode`: Individual reasoning factor (e.g., historical chart trend, holiday rush factor).
- `TurnSnapshot`: Single interaction turn in a multi-turn conversation session.

### 3.2 Value Objects (Immutable Attributes & Taxonomies)
- `ConfidenceMetric`: Score (0.00 – 1.00) + Certainty Level (`HIGH`, `MEDIUM`, `LOW`, `UNCERTAIN`).
- `ActionChip`: Label + Intent Payload + Primary/Secondary Priority Flag.
- `PolicyCitation`: Clause Number + Policy Title + Validity Period.
- `PersonaLayoutMode`: Enum (`ULTRA_SHORT`, `SHORT`, `NORMAL`, `DETAILED`, `EMERGENCY`).

---

## 4. DOMAIN SERVICES CATALOG

1. **`ResponseSynthesisService`**: Stateless domain service orchestrating the multi-source composition pipeline.
2. **`ArbitrationDomainService`**: Evaluates trade-offs when upstream engines issue conflicting train recommendations.
3. **`ExplainabilityService`**: Calculates required explanation depth based on user persona and prediction score.
4. **`PrivacyMaskingService`**: Scans and masks PII attributes within composed text payloads.

---

## 5. DOMAIN EVENTS CATALOG

```
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE DOMAIN EVENT CATALOG                            |
+-----------------------------------------------------------------------------------+
| Event Name                        | Business Trigger                              |
+-----------------------------------+-----------------------------------------------+
| ResponseComposedEvent             | Emitted when a response is synthesized        |
| ConflictArbitratedEvent           | Emitted when subsystem discrepancies are resolved|
| ExplanationGeneratedEvent         | Emitted when multi-tier reasoning is attached  |
| LowConfidenceWarningEmittedEvent  | Emitted when prediction odds fall below 60%   |
| PIICompositionMaskedEvent         | Emitted when non-consented PII is scrubbed    |
+-----------------------------------------------------------------------------------+
```

---

## 6. BUSINESS POLICIES & SPECIFICATIONS

- **`SafetyOverridesConveniencePolicy`**: Emergency alerts immediately displace standard recommendation cards.
- **`ConsentAwareCompositionSpecification`**: Verifies `ConsentProfile.is_granted == True` before injecting passenger history into responses.
- **`ScannabilitySpecification`**: Validates that long responses contain headers, bold highlights, and bullet points.

---

## 7. TACTICAL ARCHITECTURE READINESS

```
================================================================================
RAILYATRA ENTERPRISE TACTICAL DESIGN COUNCIL

Aggregates & Invariants:    ✅ FULLY SPECIFIED
Entities & Value Objects:   ✅ FULLY SPECIFIED
Domain Events & Policies:   ✅ FULLY SPECIFIED

FINAL DECISION: 🟢 AUTHORIZED FOR APPLICATION ARCHITECTURE (Part 4)
================================================================================
```
