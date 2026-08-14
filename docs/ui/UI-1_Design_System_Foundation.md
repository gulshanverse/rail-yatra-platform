# RailYatra AI — UI-1 Design System Foundation

Status: Implementation complete for UI-1
Branch: `feat/ui-design-system-foundation`

## Goal

Establish the reusable visual foundation for the frontend redesign without changing page behavior, backend contracts, conversation APIs, or SSE behavior.

## Design tokens

The global theme now exposes semantic tokens for:

- Canvas/background
- Surface and elevated surfaces
- Interactive surfaces
- Foreground and muted text
- Rail Blue
- AI Violet
- Signal Cyan
- Success / Warning / Danger
- Borders, inputs and focus rings
- Radius scale
- Typography scale
- Card/elevated shadows
- Motion durations and easing

Dark mode is the product's primary visual direction; light mode remains supported.

## Primitive components

Located under `apps/frontend/src/components/ui/`:

- `Button`
- `IconButton`
- `Input`
- `Textarea`
- `Badge`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- `Avatar`
- `Tabs`
- `Skeleton`
- `Divider`

`apps/frontend/src/lib/cn.ts` provides the shared `clsx` + `tailwind-merge` composition utility.

## Accessibility contract

- Interactive controls use a minimum 44px touch target.
- Inputs use 16px text to avoid mobile browser zoom behavior.
- Visible focus rings are part of the primitive styles.
- Tabs implement arrow/Home/End keyboard navigation.
- Disabled states remain visibly distinguishable.
- Reduced-motion preferences are respected globally.

## Compatibility boundary

Existing legacy classes such as `.glass`, `.shadow-premium`, and `.btn-hover` remain temporarily supported so current routes do not require a behavioral rewrite in UI-1.

Feature code should use the new semantic tokens and primitives for all new work.

## Definition of done

- [x] Semantic design tokens established.
- [x] Dark/light themes preserved.
- [x] Motion and reduced-motion contract established.
- [x] Primitive components created.
- [x] Keyboard/focus behavior included where applicable.
- [x] Existing application routes left behaviorally unchanged.
- [ ] CI lint/build verification completed by GitHub Actions.
- [ ] UI-2 application shell may begin after CI is green.
