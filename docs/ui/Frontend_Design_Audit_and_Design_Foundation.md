# RailYatra AI — Frontend Design Audit & Design Foundation

Status: UI-0 Design Audit / Foundation Specification
Branch: `feat/ui-design-foundation-audit`
Target baseline: `main`

## 1. Purpose

This document is the source of truth for the RailYatra frontend redesign. It intentionally separates design-system and UX decisions from implementation so future UI work is incremental, reviewable, and production-safe.

The product direction is **AI-native travel decision workspace**, not a conventional railway dashboard with a chatbot attached.

### Design north star

> Tell RailYatra what matters. RailYatra understands the journey, investigates options, compares trade-offs, explains the recommendation, and helps the user act.

---

## 2. Current frontend audit

### 2.1 Current application surfaces

The current frontend contains these primary routes/surfaces:

- `/` — dashboard/home + decision engine + billing/features
- `/chat` — full AI workspace
- `/login`
- `/register`
- `/subscription`
- `/settings`
- `/admin`

### 2.2 Current architectural strengths

- Next.js App Router is already in use.
- Geist and Geist Mono are already loaded globally.
- Tailwind CSS v4 is already configured.
- Framer Motion is available and should be used selectively.
- Lucide is available for consistent iconography.
- AI streaming and conversation persistence already exist.
- The `/chat` surface already contains useful primitives such as conversation history, pinning, search, rename/delete, streaming messages, and journey options.
- Authentication and theme state are already centralized through Zustand.

### 2.3 Current UX problems

1. **The home page is dashboard-first rather than task-first.**
   Infrastructure status, validation instructions, billing, and agent-directory content compete with the actual travel task.

2. **The AI experience is duplicated.**
   There is a decision-engine experience on `/` and a separate floating/full chat experience. These should share one interaction model and one visual language.

3. **The floating assistant is a weak mobile pattern.**
   A nested floating chat window creates competing scroll regions and reduces usable viewport space. Mobile should use a dedicated full-screen AI workspace.

4. **Technical information is exposed in the consumer surface.**
   Database/provider/service health belongs in `/admin`, not the main travel experience.

5. **The visual system is under-specified.**
   Existing tokens cover basic semantic colors/radii, but there is no formal spacing, elevation, motion, typography, component, or responsive interaction contract.

6. **The current CSS uses broad visual effects.**
   `.glass`, `.shadow-premium`, and `.btn-hover` are useful prototypes but need to become deliberate design tokens/components. In particular, avoid blanket `transition: all` and overusing blur/glass effects.

7. **AI output is too document-like.**
   The product needs structured recommendation cards, comparison surfaces, follow-up controls, context indicators, evidence/provenance, and recoverable streaming states.

8. **Trust is weakly represented.**
   A numeric `Confidence: 100%` style is inappropriate as a default for probabilistic travel intelligence. Prefer qualitative confidence and explainable recommendation factors.

9. **Async failure states are not product-grade.**
   A raw "AI response stream ended unexpectedly" message should become a recoverable interruption state with Resume/Retry actions and preserved context.

10. **Mobile needs a first-class interaction model.**
    Desktop layout patterns must not simply collapse into smaller columns. Chat composer, keyboard behavior, navigation, and journey cards need mobile-specific composition.

11. **Home-page code is too monolithic.**
    `apps/frontend/src/app/page.tsx` currently contains authentication, conversation creation, SSE parsing, billing simulation, theme controls, navigation, and a large JSX tree. UI redesign must extract feature components instead of increasing this file's complexity.

---

## 3. Product information architecture

### Consumer navigation

```text
RailYatra
├── Home
├── AI Workspace
├── Plan Journey
├── My Journeys
├── PNR / Live Status
└── Profile
```

### Admin navigation

```text
Operations
├── System Health
├── AI Providers
├── Requests & Latency
├── Failures
├── Users / Plans
└── Audit / Logs
```

Infrastructure details must not dominate the consumer experience.

---

## 4. Design principles

1. **Calm first. Intelligent second. Beautiful third.**
2. The primary user task must visually dominate the page.
3. AI should be an orchestration layer, not merely a message box.
4. Prefer progressive disclosure over dense dashboards.
5. Motion explains state changes; it does not decorate every element.
6. Every asynchronous state needs a visible status and a recovery path.
7. Live data, simulated data, and AI-generated predictions must be distinguishable.
8. No arbitrary colors, spacing, radii, or shadows in feature code.
9. Mobile is a first-class experience, not a compressed desktop.
10. Accessibility is part of the component contract, not a final polish pass.

---

## 5. Visual foundation

### Dark-first palette

```text
Canvas          #070A12
Surface         #0C111D
Elevated        #111827
Interactive     #151D2D
Rail Blue       #3B82F6
AI Violet       #8B7CFF
Signal Cyan     #38BDF8
Success         #22C55E
Warning         #F59E0B
Danger          #EF4444
```

Use semantic tokens rather than raw hex values inside components.

### Typography

Primary: Geist.

```text
Display XL      64px
Display L       48px
Display M       36px
Heading XL      30px
Heading L       24px
Heading M       20px
Body L          17px
Body M          15px
Body S          14px
Caption         12px
```

Responsive typography must scale down without destroying hierarchy.

### Radius

```text
sm       8px
md       12px
lg       18px
xl       24px
pill     999px
```

### Motion

```text
micro       120–160ms
standard    180–240ms
emphasis    280–400ms
complex     400–600ms
```

Use transform/opacity where possible. Support `prefers-reduced-motion`.

---

## 6. Core component taxonomy

### Foundation

- Button
- IconButton
- Input
- Textarea
- Select
- Badge
- Avatar
- Tooltip
- Dialog
- Sheet
- Tabs
- Skeleton
- Toast
- Divider

### AI

- AIComposer
- AIMessage
- AIMessageActions
- AIThinking
- AIStreaming
- AIError
- AIContext
- AIFollowups
- AIRecommendation
- AIEvidence
- AIStatus

### Journey

- JourneyComposer
- JourneyHeader
- JourneySummary
- StationChip
- TrainCard
- JourneyLeg
- ConnectionCard
- TrainTimeline
- AvailabilityBadge
- ComfortScore
- ReliabilityScore
- DecisionScore
- JourneyComparison

### Navigation

- AppSidebar
- MobileHeader
- MobileBottomNav
- CommandPalette
- UserMenu

---

## 7. AI interaction model

The core loop is:

```text
Understand
   ↓
Investigate
   ↓
Compare
   ↓
Recommend
   ↓
Explain
   ↓
Act
```

High-level AI activity may be shown as:

```text
✓ Understanding journey
✓ Checking route options
● Evaluating confirmation signals
○ Preparing recommendation
```

Do not expose private chain-of-thought.

### Context indicator

```text
🧠 Context preserved
```

Opening it should show the active journey context: origin, destination, date, class, constraints, and preferences.

### Follow-up actions

Use contextual chips such as:

- Cheapest
- Fastest
- Highest confirmation
- Most comfortable
- Different date

These are shortcuts, not replacements for free-form input.

---

## 8. Journey recommendation pattern

A recommendation card should be scannable:

```text
⭐ BEST MATCH

Train number + name
BSP 18:40 → NDLS 08:10
13h 30m · 3A · ₹1,245

Confirmation   ████████░░ 87%
Comfort        █████████░ 91%
Reliability    ████████░░ 86%

Why this one?
✓ Direct route
✓ Meets arrival constraint
✓ Strong confirmation signal
✓ Matches preferred class

[View journey] [Select]
```

Do not force users to read a long paragraph to compare options.

---

## 9. Trust and data freshness

Every recommendation should have enough context to answer:

- Is this live data or simulated data?
- When was the underlying data updated?
- Is this a prediction or a factual schedule?
- Why was this option recommended?

Preferred labels:

```text
● Live data
Simulation
High confidence
87% match
Updated 2m ago
```

Avoid presenting probabilistic output as certainty.

---

## 10. Streaming state contract

The frontend must explicitly model:

```text
IDLE
SUBMITTING
CONNECTING
STREAMING
FINALIZING
COMPLETE
INTERRUPTED
FAILED
```

An interrupted stream must never leave the user at a dead end.

Preferred interruption UI:

```text
⚡ Connection interrupted
Your journey context is safe.
We can continue from where we stopped.

[Resume] [Retry]
```

---

## 11. Responsive contract

Target widths:

```text
360 / 390 / 430
768
1024
1280
1440
1920+
```

Mobile requirements:

- dedicated full-screen AI workspace
- single primary scroll region
- composer remains above the software keyboard
- no nested floating chat window
- touch targets at least 44px
- mobile text inputs use at least 16px text
- bottom navigation for top-level sections

Desktop requirements:

- calm sidebar
- command palette
- keyboard shortcuts
- wide but bounded content area
- optional journey intelligence side panel

---

## 12. Page-level redesign

### Home

Replace the current dashboard-heavy layout with:

1. brand/navigation
2. AI journey composer
3. quick optimization choices
4. recent journeys
5. a concise explanation of RailYatra's intelligence
6. optional trust/system status, kept secondary

### AI Workspace

Primary product surface:

```text
Conversation history | Active journey intelligence
                    | recommendation/results
                    | composer
```

### My Journeys

Saved and recent journeys, resumable conversations, status snapshots.

### PNR / Live Status

Focused operational workflow rather than generic dashboard cards.

### Subscription

Clear plan comparison, current usage, and upgrade path. Do not interrupt core journey planning with billing UI.

### Admin

Move system health, provider diagnostics, metrics, logs, and operational controls here.

---

## 13. Implementation boundaries

Do not redesign backend contracts during the UI foundation phase.

Do not rewrite working SSE/conversation logic merely for visual reasons.

Extract UI components around the existing behavior first. Behavioral changes must be isolated into separate PRs when possible.

Do not add a new UI framework when the current stack already provides:

- Next.js
- Tailwind CSS v4
- Geist
- Lucide
- Framer Motion
- Zustand

---

## 14. Quality gates

Every UI PR must pass:

```text
pnpm --filter frontend lint
pnpm --filter frontend build
pnpm --filter frontend typecheck (when available)
```

Then verify:

- desktop 1280px+
- mobile 390px
- keyboard navigation
- reduced motion
- focus visibility
- loading state
- empty state
- error state
- streaming interruption/retry
- no horizontal overflow
- no nested scroll traps

Production PRs are not complete until the relevant Vercel preview is manually checked.

---

## 15. UI implementation sequence

```text
UI-0  Audit + foundation specification       ← this document
UI-1  Design tokens + primitive components
UI-2  Application shell + navigation
UI-3  Home / journey composer
UI-4  AI workspace redesign
UI-5  Journey decision cards + comparison
UI-6  Mobile-first pass
UI-7  Motion + streaming states
UI-8  Trust / provenance surfaces
UI-9  Admin operations redesign
UI-10 Production accessibility/performance QA
```

Each phase should be a separate focused PR with green CI before merge.

---

## 16. Definition of done for UI-0

- [x] Current frontend structure inspected.
- [x] Current home and AI workspace inspected.
- [x] Existing CSS/theme system inspected.
- [x] Existing frontend dependency stack inspected.
- [x] Design direction defined.
- [x] Information architecture defined.
- [x] Design tokens defined.
- [x] Component taxonomy defined.
- [x] AI interaction model defined.
- [x] Responsive and accessibility requirements defined.
- [x] Implementation sequence defined.
- [ ] UI-1 implementation started in a follow-up PR.
