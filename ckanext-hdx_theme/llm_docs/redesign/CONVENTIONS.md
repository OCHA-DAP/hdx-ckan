# v2 Redesign — Implementation Conventions

Single source of truth for general rules. Update here; do not duplicate in task files.

---

## BEM class prefixes

| Prefix | Used for | Example |
|--------|----------|---------|
| `c-` | Reusable components | `c-button`, `c-autocomplete` |
| `hdx-v2-` | Non-reusable v2 sections and layouts | `hdx-v2-hero`, `hdx-v2-grid` |

---

## Media queries — nest inside element blocks

```less
// Do
&__inner {
    padding: 2rem;
    @media (min-width: @hdx-bp-md) { padding: 4rem; }
}

// Don't
&__inner { padding: 2rem; }
@media (min-width: @hdx-bp-md) { &__inner { padding: 4rem; } }
```

Exception: a single `@media` block may group multiple unrelated elements when there is no per-element responsive logic.

---

## Breakpoints

Defined **once** in `breakpoints.less`. Any file that uses breakpoints imports it. No local redefinitions.

| Variable | Value | px |
|----------|-------|----|
| `@hdx-bp-md` | `48rem` | 768px |
| `@hdx-bp-xl` | `80rem` | 1280px |
| `@hdx-bp-xxl` | `87.5rem` | 1400px |

---

## Bootstrap classes — prohibited in v2

Do **not** use Bootstrap grid classes (`row`, `col-*`, `gx-*`, `gy-*`, `g-*`) or utility classes (`d-*`, `gap-*`, `pt-*`, `mt-*`, `align-items-*`, `justify-content-*`, etc.) in v2 templates.

All layout, spacing, and responsive behaviour must be implemented in LESS using `@hdx-bp-*` breakpoints and design tokens.

---

## Container and full-bleed sections

Full-bleed sections (background spans full viewport width) use a two-layer pattern:

- **Outer element** — sets `background-color`, vertical padding only
- **Inner element** — add `hdx-v2-container` class for horizontal padding and max-width; set flex/grid layout here

```html
<section class="hdx-v2-hero">
  <div class="hdx-v2-hero__inner hdx-v2-container">...</div>
</section>
```

`.hdx-v2-container` is defined in `layout.less`. It provides:
- 1rem side padding at SM
- 3rem side padding at MD through XL
- `max-width: 1320px` centered at XXL (≥ 87.5rem)

Do **not** use Bootstrap's `.container` class in v2 templates.

---

## Preserve analytics and functional logic

When redesigning or replacing an existing template or element, carry over all non-presentational logic from the original:

- Analytics blocks (`{% block analytics_* %}`, `data-module`, `data-module-*` attributes)
- SEO blocks (`{% block meta %}`, `{% block subtitle %}`, `structured_data`)
- Functional Jinja blocks (`{% block scripts %}`, `{% block head_extras %}`, etc.) that load page-specific assets or set page state
- Conditional snippets tied to runtime data (e.g. `alert_bar`)

Only the visual structure (HTML elements, BEM classes, CSS) changes. Logic is not optional.

---

## Interaction states: pseudo-classes vs. state classes

Use CSS pseudo-classes for transient, user-triggered states.
Use `is-*` classes only for persistent states set by the server or JavaScript.

| State | Correct approach |
|-------|-----------------|
| Hover | `:hover` in LESS |
| Focus | `:focus-visible` in LESS |
| Pressed | `:active` in LESS |
| Selected / current | `is-active` class (server or JS) |
| Unavailable | `is-disabled` class (server or JS) |
| Expanded | `is-open` class (JS only) |

Do **not** add `is-hovered`, `--hovered`, `is-focus`, or similar classes to templates or JavaScript. If a JS controller must replicate hover visuals (e.g. keyboard navigation), use a clearly named parent-class such as `c-component--keyboard-active` and add a comment in the LESS file explaining why the class exists.

---

## Layout widths

Do **not** use fixed `rem` or `px` for layout column widths. Use flex ratios (`flex: 1`, `flex: 2`) or `width: 100%` instead.

Exceptions: global container cap (1320px), fixed-height elements (buttons, inputs), icon dimensions.

---

## Design tokens

- CSS custom properties: `--hdx-<category>-<step>` (e.g. `--hdx-brand-5`, `--hdx-space-3`)
- LESS variables: same name with `@` (e.g. `@hdx-brand-5`) — LESS-only, not used in media queries
- No hardcoded hex colors, `rgba(...)` overlays, or box-shadow values in component LESS — use the corresponding token (`var(--hdx-neutral-1)`, `var(--hdx-overlay-white-10)`, `var(--hdx-shadow-md)`)
- Component-level LESS variables use `@c-*` prefix and are **not** exported as CSS custom properties

---

## Accessibility (WCAG 2.1 AA) — mandatory for all v2 tasks

These constraints apply to every component, template, and JS file in the v2 redesign. See `llm_docs/redesign/requirements/041-accessibility-wcag-audit.md` for the full rationale.

### Keyboard interactions

Every interactive element must be fully operable by keyboard. For custom interactive elements:

- Use `<button>` for actions, `<a href>` for navigation — never `<div>`/`<span>` as interactive targets
- `click` handlers on buttons/links already fire on Enter; add a `keydown` handler for `Space` if needed for `<button>` elements used as toggles
- Dropdowns and panels: `Escape` closes and returns focus to the trigger

### ARIA state attributes

Update ARIA attributes whenever state changes:

| State | Attribute |
|-------|-----------|
| Panel open/closed | `aria-expanded="true/false"` on the trigger |
| Widget hidden/visible | `aria-hidden="true/false"` |
| Current nav item | `aria-current="true"` |
| Tooltip association | `aria-describedby` on trigger, `id` + `role="tooltip"` on tooltip element |

### Focus management

Overlays that block page content (offcanvas drawer, modal, full-screen overlay) must:
1. Move focus inside on open (use `window.FocusTrap` from `focus-trap.js`)
2. Trap Tab/Shift+Tab within the overlay
3. Close on Escape
4. Return focus to the triggering element on close

Dropdowns (non-modal): move focus to first item on keyboard-triggered open; return focus to trigger on close.

### SVG icons

All inline SVG icons must carry `aria-hidden="true" focusable="false"`. Icon-only interactive elements require an `aria-label` on the parent `<button>` or `<a>`.

```html
<!-- decorative icon inside labeled button -->
<button aria-label="Close menu">
  <svg aria-hidden="true" focusable="false" ...></svg>
</button>
```

### prefers-reduced-motion

**CSS**: A global `@media (prefers-reduced-motion: reduce)` override in `foundation.less` disables all transitions and animations. Do not add per-component wrappers — the global rule covers everything.

**JS**: Guard any programmatic animation before starting:

```js
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    // instant fallback
    return;
}
// animated path
```

### Screen-reader utilities

`.sr-only` and `.sr-only--focusable` are defined in `foundation.less`. Use for:
- Skip-to-main-content link (first focusable element in `<body>`)
- `aria-live` status regions (copy success, form feedback)
- Any text needed by AT but not visible on screen

### Status messages

Any user action that produces a success/error state must announce via a live region already in the DOM:

```html
<span class="sr-only" aria-live="polite" data-copy-status></span>
```

```js
statusEl.textContent = 'Copied to clipboard';
setTimeout(function () { statusEl.textContent = ''; }, 2000);
```
