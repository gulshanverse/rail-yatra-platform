# UI-04A implementation notes

The first implementation is intentionally presentation-only. It adds the Journey Decision Workspace without changing authentication, conversation persistence, SSE, billing, or AI-service contracts.

The workspace accepts structured decision data when available and safely falls back to an analysis surface for the current text response contract. This avoids fabricating train numbers, fares, timings, or availability before the backend exposes verified structured fields.

Next UI-04A integration work should map any existing structured AI response metadata into `JourneyDecisionWorkspaceData` and keep the current Markdown response as the source of truth until that mapping is verified.
