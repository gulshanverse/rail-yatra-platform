# UI-2 — Application Shell & Navigation

## Scope

UI-2 establishes the responsive application chrome without changing backend contracts, SSE behavior, or page-specific product workflows.

## Implemented

- Responsive desktop sidebar with collapse/expand behavior
- Mobile drawer navigation
- Mobile bottom navigation with safe-area support
- Sticky responsive top bar
- Command palette opened by `Cmd/Ctrl + K`
- Keyboard navigation inside command palette
- Route-aware active navigation
- User/account surface in the sidebar
- Shared application-shell exports
- Reduced reliance on page-local navigation styling

## Navigation model

Home → AI Workspace → Plan Journey → My Journeys → PNR & Live Status

Account → Settings

## Boundary

The shell does not replace or rewrite existing page logic. UI-3 will progressively adopt the shell around the Home experience, followed by AI Workspace and journey surfaces.

## QA targets

- 390px mobile
- 768px tablet
- 1280px desktop
- keyboard navigation
- focus visibility
- reduced motion
- no horizontal overflow
- mobile safe-area inset
