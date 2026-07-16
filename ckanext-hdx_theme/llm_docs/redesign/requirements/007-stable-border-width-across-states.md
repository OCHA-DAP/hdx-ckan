# Task 007: Constant border-width across component states

Every v2 component keeps a constant `border-width` (normally 1px) across all states
(default / hover / active / focus). State changes are conveyed by `border-color` only.

## What to update

For each component with border states, state rules use `border-color:` — never the
`border:` shorthand, which silently re-declares the width. Reference pattern
(`less/v2/components/signal-card.less`):

```less
.c-example {
    border:     1px solid var(--hdx-neutral-1);
    transition: border-color 0.15s ease;

    &:hover { border-color: var(--hdx-neutral-8); }
}
```

Where a state needs extra emphasis beyond a color change (e.g. `.c-search-input` focus),
use a layout-safe `outline`:

```less
&:focus-within {
    outline:        1px solid var(--hdx-neutral-8);  // reads as a 2px ring with the 1px border
    outline-offset: 0;
}
```

Error variants recolor the ring (`outline-color: var(--hdx-error-5)`).

## Rules

- Border-width must never change between states; transitions target `border-color`,
  not `border`.
- Fixed component heights (`@c-input-*-h`, `@c-sel-*-h`, `@c-dropdown-m-h`,
  `@c-button-*-dim`, …) are Figma size specs — keep them, and describe them as such
  in comments.
- Do **not** use `box-shadow` to simulate or replace borders.
- Constant-width borders of other thicknesses are fine (e.g. `.c-step-pager`'s static
  2px, `.c-nav-item`'s 4px underline with a `transparent` default — the correct way to
  reserve space for an active-state border).
- Components that use `outline` for focus states (e.g. `.c-checkbox`, `.c-text-link`) are
  already layout-safe — no changes needed.

## Why

Border-width changes move the border box (uncompensated) or squeeze the content box
(compensated), causing visible reflow or content shift on hover and focus. A constant
width with color-only state changes keeps every box pixel-stable in all states.

