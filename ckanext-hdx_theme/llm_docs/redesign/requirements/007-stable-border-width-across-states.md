# Task 007: Stable component dimensions when border width changes across states

Ensure that changing `border-width` between component states (default / hover / active / focus)
does not shift the component's outer dimensions. The border must grow inward only.

## What to update

For each component below, verify or add an explicit `height` / `min-height` so that
`box-sizing: border-box` absorbs the border change inward. Do not alter border-width values.

- `less/v2/components/input-field.less`
  - `.c-search-input`: 1px → 1.5px (hover) → 2px (focus)
  - `.c-ac-search-input`: same progression

- `less/v2/components/buttons.less`
  - `.c-button--tertiary`: 1px → 1.5px (hover) → 1px (active)
  - `.c-button--text`: 1px → varies across states

Scan all other v2 component files for additional `border-width` state changes and apply
the same fix.

## Rules

- `box-sizing: border-box` must be set on every affected element (already in place; verify it stays).
- Each affected element must have an explicit `height` or `min-height` that matches the
  intended Figma height for that component. Without a fixed dimension, the browser uses
  content height and border changes push layout outward.
- Do **not** use `box-shadow` to simulate or replace borders.
- Do **not** change the Figma-specified border-width values.
- Components that use `outline` for focus states (e.g. `.c-checkbox`, `.c-text-link`) are
  already layout-safe — no changes needed.

## Why

Border-width changes on auto-height elements shift surrounding layout, causing visible reflow
on hover and focus. Anchoring the element to a fixed height makes `box-sizing: border-box`
effective and keeps the outer box pixel-stable across all states.

## Verification

In browser DevTools, select each affected component, toggle between default / hover / focus
states, and confirm the element's bounding box (height and width) does not change.
