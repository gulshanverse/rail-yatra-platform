# UI-04A — Journey Decision Workspace

## Scope

Build the first slice of the Journey Decision Workspace on top of the existing AI decision response contracts.

### In scope

- Journey summary header
- Recommendation hero surface
- Journey timeline
- Journey option cards
- Decision factors / semantic badges
- Verification and confidence states
- Responsive desktop/tablet/mobile layout
- Loading, empty, and recoverable error states

### Out of scope

- Authentication changes
- Billing changes
- AI provider changes
- Backend orchestration rewrites
- New booking/payment flows
- UI-01 token redesign
- UI-02 application-shell redesign
- UI-03 journey composer redesign

## UX goals

1. Turn long AI responses into scannable decision surfaces.
2. Make the recommended option visually obvious without hiding alternatives.
3. Separate AI recommendations from verified/live information.
4. Preserve the existing conversation and SSE/API contracts.
5. Keep the mobile experience first-class.

## Acceptance criteria

- Existing journey queries continue to work.
- Existing AI conversation context remains intact.
- Recommendation and option data render without inventing unavailable facts.
- Loading/error states never discard an existing usable result.
- No horizontal overflow on mobile.
- Frontend lint passes.
- Frontend production build passes.
- Existing backend and AI-service CI remain green.
- Vercel preview deploys successfully.

## Implementation discipline

Use small focused components under the existing frontend component architecture. Prefer derived state over synchronous state-setting effects. Reuse UI-01 primitives and tokens. Do not introduce duplicate API or conversation state.
