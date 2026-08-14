# UI-05B — Decision Modes

## Scope

The journey workspace now supports five user-selected optimization modes:

- Best overall
- Fastest
- Cheapest
- Most comfortable
- Lowest risk

## Data safety

`Fastest` requires a parseable duration and `Cheapest` requires a numeric fare. When those fields are unavailable, the mode is disabled rather than inferred. The other modes use only fields already present in the existing journey option model.

The feature is presentation-layer only. It does not change AI orchestration, SSE, authentication, billing, or railway data contracts.

## UX

Selecting a mode immediately re-ranks the existing options locally and updates the recommendation label. No network request is made, so changing a decision mode does not create a new conversation or break conversation continuity.
