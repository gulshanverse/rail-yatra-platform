# Milestone 6.2 Technical Walkthrough
## Intent Understanding Engine (IUE)

This document details the code organization, component interactions, and semantic parsing pipeline implemented for Milestone 6.2.

---

## 1. Package Structure & Code Map

All IUE files reside in `app/orchestrator/`:

### New Modules (Milestone 6.2)
- **`normalizer.py`**: `InputNormalizer` — sanitizes raw text, normalizes whitespace, and redacts PII (phone numbers, emails, PNR codes, credit cards) using compiled regex patterns.
- **`slot_extractor.py`**: `SlotExtractor` — extracts travel entity parameters (station codes, train numbers, PNR numbers, dates, passenger counts) from sanitized user messages.
- **`evaluator.py`**: `ConfidenceEvaluator` — validates classification confidence against configurable thresholds, checks for missing required slots, and constructs the final `IntentDescriptor`.
- **`types.py`** (extended): Added `IntentCandidate`, `Slot`, and `IntentDescriptor` Pydantic models as the core domain DTOs.

### Modified Modules
- **`classifier.py`**: Rewritten to integrate the full semantic parsing pipeline — normalization → heuristic classification → model classification → slot extraction → confidence evaluation.
- **`nodes.py`**: Updated `ClassifierNode` to map `IntentDescriptor` fields (slots, confidence, needs_clarification) into the LangGraph `AIState` context for downstream consumption.

### Test Modules
- **`tests/test_iue.py`**: Comprehensive unit test suite covering all new IUE components — normalizer sanitization, PII redaction, slot extraction, confidence evaluation, and end-to-end pipeline execution.

---

## 2. Semantic Parsing Pipeline

```
[Raw User Message]
        │
        ▼
┌───────────────────────┐
│   InputNormalizer      │  1. Strip non-printable chars
│                        │  2. Collapse whitespace
│                        │  3. Redact PII (phone, email, PNR, CC)
└───────────┬───────────┘
            │ Sanitized Text
            ▼
┌───────────────────────┐
│   IntentClassifier     │  1. Try Keyword Heuristics (fast path)
│                        │  2. If no match → LLM Model Classification
│                        │  3. Returns IntentCandidate
└───────────┬───────────┘
            │ Intent Candidate
            ▼
┌───────────────────────┐
│   SlotExtractor        │  1. Extract station codes (NDLS, HWH, etc.)
│                        │  2. Extract train numbers (5-digit)
│                        │  3. Extract PNR (10-digit, from original text)
│                        │  4. Extract dates (ISO & relative)
│                        │  5. Extract passenger counts
│                        │  6. Map station names → codes
└───────────┬───────────┘
            │ Slot Map
            ▼
┌───────────────────────┐
│  ConfidenceEvaluator   │  1. Check intent confidence vs threshold (0.70)
│                        │  2. Check required slots for intent family
│                        │  3. Check individual slot confidence (0.65)
│                        │  4. Build IntentDescriptor DTO
└───────────┬───────────┘
            │ IntentDescriptor
            ▼
┌───────────────────────┐
│   ClassifierNode       │  Maps descriptor into AIState context:
│   (LangGraph Node)     │  - state["intent"]
│                        │  - state["context"]["intent_descriptor"]
│                        │  - state["context"]["slots"]
│                        │  - state["context"]["needs_clarification"]
└───────────────────────┘
```

---

## 3. Domain Model

### IntentDescriptor (Aggregate Root)
The immutable output DTO containing:
- **`intent`** (`IntentCandidate`): Name, confidence score, and classification reason.
- **`slots`** (`Dict[str, Slot]`): Parsed travel parameters with types and confidence ratings.
- **`context`** (`Dict`): Trace ID, PII redaction status, original query.
- **`metadata`** (`Dict`): Execution time, classifier type (heuristic/model), model version.
- **`needs_clarification`** (`bool`): Flag indicating ambiguous or incomplete inputs.

### IntentCandidate (Value Object)
- `name`: Intent category (e.g., `plan_travel`, `check_pnr`, `conversation`).
- `confidence`: Decimal score between 0.0 and 1.0.
- `reason`: Explanation for the classification decision.

### Slot (Value Object)
- `name`: Parameter key (e.g., `origin`, `destination`, `pnr`).
- `value`: Parsed value.
- `type`: Validation label (e.g., `StationCode`, `Date`, `PNR`).
- `confidence`: Extraction confidence score.

---

## 4. Heuristic Classification Rules

The fast-path classifier matches user queries against local keyword sets:

| Intent | Trigger Keywords |
| :--- | :--- |
| `check_pnr` | pnr, ticket status, booking status |
| `plan_travel` | train, route, schedule, go to, travel to, from, to |
| `journey_intelligence` | waitlist, delay, confirm, forecast, prediction |
| `knowledge` | policy, luggage, refund, faq, rules |
| `recommendation` | recommend, better, compare, score, comfort, rate |

Heuristic matches return confidence `1.0` and skip the LLM API call entirely.

---

## 5. PII Redaction Patterns

| PII Type | Pattern | Replacement |
| :--- | :--- | :--- |
| Credit Card | 13-16 consecutive digits (with optional spaces/dashes) | `[REDACTED_CC]` |
| Phone Number | Indian mobile format (optional +91 prefix, starts with 6-9) | `[REDACTED_PHONE]` |
| PNR Code | Exactly 10 consecutive digits | `[REDACTED_PNR]` |
| Email | Standard email format | `[REDACTED_EMAIL]` |

Redaction order: CC → Phone → PNR → Email (to avoid cross-pattern conflicts).

---

## 6. Backward Compatibility

- The `IntentClassifier.classify()` method is preserved as the legacy entry point used by existing `ClassifierNode` tests and mock infrastructure.
- Internally, `classify()` delegates to `classify_and_parse()` and maps the `IntentDescriptor` back into a plain dictionary format.
- The `ClassifierNode` in `nodes.py` invokes `classify()` and reconstructs the `intent_descriptor` dict in the state context, preserving full backward compatibility with the Milestone 6.1 test suite.

---

## 7. Design Decisions

- **Heuristic-First Classification**: Common queries bypass the LLM entirely, reducing latency and API costs.
- **PII Redaction Before Model Dispatch**: PII is masked before text reaches any external API, ensuring data privacy compliance.
- **Slot Extraction from Original Text**: PNR codes are extracted from the pre-redaction text to preserve values that would otherwise be masked.
- **Pydantic DTOs**: All domain objects use Pydantic `BaseModel` for strict validation, serialization, and immutability.
- **Stateless Components**: All pipeline stages are stateless, enabling safe concurrent execution.
