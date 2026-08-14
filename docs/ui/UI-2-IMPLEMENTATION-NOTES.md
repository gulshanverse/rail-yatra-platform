# UI-2 Implementation Notes

## Application shell

`AppShell` provides the desktop sidebar, mobile drawer, sticky top bar, route-aware navigation, and collapse state.

## Command palette

`CommandPalette` listens for the `railyatra:command-palette` event. The shell emits this event from the desktop search affordance and from Cmd/Ctrl+K.

## Mobile navigation

`MobileBottomNav` is mounted globally and provides five high-frequency destinations. It respects the device safe-area inset.

## Adoption strategy

Existing routes remain behaviorally intact. UI-3 and UI-4 will wrap the relevant authenticated pages with `AuthenticatedShell` as their visual surfaces are redesigned.
