# 028 — Standardize Hover Interaction States

## Background

The v2 redesign applies hover styles in two conflicting ways: native CSS `:hover` pseudo-classes (~164 instances, already the dominant pattern) and render-time state classes injected via Jinja2 template parameters (`state='hovered'`, `state='active-hovered'`). The class-based approach was introduced to support static showcase variants on the components page — a valid need solved the wrong way.

Hover is a transient, pointer-triggered state. It belongs entirely in CSS. Server-rendered classes for hover state are incorrect by definition: they are set at render time, not in response to user interaction.

Two naming conventions for these classes coexist and must both be addressed:

- `is-hovered`, `is-active-hovered` — used in `activity-card` and `list-item`
- `c-component--hovered`, `c-component--active-hovered` — used in `selection-item`, `dropdown`, `search-input`

See [CONVENTIONS.md](../CONVENTIONS.md) for general naming and token rules.

---

## What to Change

### 1. LESS — replace class selectors with pseudo-classes

| File | Rule to replace | Replacement |
|------|-----------------|-------------|
| `less/v2/components/activity-card.less` | `&.is-hovered { … }` | `&:hover { … }` |
| `less/v2/components/list-item.less` | `&.is-hovered { … }` | `&:hover { … }` |
| `less/v2/components/list-item.less` | `&.is-active-hovered { … }` | `&.is-active:hover { … }` |
| `less/v2/components/selection.less` | `&.c-selection-item--hovered { … }` | `&:hover { … }` |
| `less/v2/components/selection.less` | `&.c-selection-item--active-hovered { … }` | `&.is-active:hover { … }` |
| `less/v2/components/search-input.less` | `&.c-search-input--hovered { … }` | `&:hover { … }` |
| `less/v2/components/dropdown.less` | `.c-dropdown--hovered > &` | See edge case below |

### 2. Templates — remove hover state parameter handling

Remove the Jinja2 conditionals that map `state='hovered'` / `state='active-hovered'` / `state='hover'` to CSS classes. The `state` parameter should no longer accept these values.

| File | Lines to remove |
|------|-----------------|
| `templates/v2/components/activity-card.html` | `{% if state == 'hovered' %}…is-hovered…{% endif %}` |
| `templates/v2/components/list-item.html` | `{% if state == 'hovered' %}…is-hovered…{% endif %}` and `{% if state == 'active-hovered' %}…is-active-hovered…{% endif %}` |
| `templates/v2/components/selection-item.html` | `{% if state == 'hover' %}…c-selection-item--hovered…{% endif %}` and `{% if state == 'active-hovered' %}…c-selection-item--active-hovered…{% endif %}` |
| `templates/v2/components/dropdown.html` | `{% if state == 'hover' %}…c-dropdown--hovered…{% endif %}` |
| `templates/v2/components/search-input.html` | `{% if state == 'hover' %}…c-search-input--hovered…{% endif %}` |

### 3. Showcase page — remove static hover variants

In `templates/v2/components.html`, remove all showcase blocks that pass `state='hovered'` or `state='active-hovered'` to components. Hover is demonstrated by mousing over the default and active variants — no separate static card is needed. Retain all other state variants (`state='active'`, `state='disabled'`, `state='enabled'`).

## State Classes — What to Keep

The following classes represent **persistent states** set by the server or JavaScript. They are correct as classes and must not be replaced with pseudo-classes.

| Class | Set by | Semantics |
|-------|--------|-----------|
| `is-active` | Server / JS | Selected item, current nav link, active tab |
| `is-disabled` | Server / JS | Unavailable action; mirrors `[disabled]` for non-form elements |
| `is-open` | JS | Expanded dropdown, open offcanvas menu |

---

## Edge Cases

### `c-dropdown--hovered` parent selector

`dropdown.less` uses a hybrid rule:

```less
&:hover,
.c-dropdown--hovered > & { … }
```

The parent-class pattern allows a JS controller (e.g. keyboard navigation) to apply the same visual state without a pointer. Before removing it, check whether any JS file sets `c-dropdown--hovered` on a parent element (check `navbar.js` and any keyboard-nav module).

- **If used by JS:** keep the parent-class alongside `:hover`. Rename it to something that communicates intent — e.g. `c-dropdown--keyboard-active` — and document it in `dropdown.less` with a short comment.
- **If not used anywhere:** remove both the class and the LESS rule.

### Focus parity

When replacing a hover rule, check whether the same visual treatment should also apply on keyboard focus. For interactive elements (links, buttons, items acting as links), add `:focus-visible` alongside `:hover`:

```less
&:hover,
&:focus-visible { … }
```

### Touch devices

CSS `:hover` can persist after a tap on iOS/Android. Hover styles in this codebase are purely decorative (color and border changes on stationary elements). Verify no hover rule hides, shows, or repositions content — if it does, gate it with `@media (hover: hover)`.

---

## Convention Addition

Add the following section to [CONVENTIONS.md](../CONVENTIONS.md):

```markdown
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

Do not add `is-hovered`, `--hovered`, `is-focus`, or similar classes to
templates or JavaScript. If a JS controller must replicate hover visuals
(e.g. keyboard navigation), use a clearly named parent-class such as
`c-component--keyboard-active` and add a comment in the LESS file explaining
why the class exists.
```

---

## Out of Scope

- No visual changes — computed styles must be identical before and after
- `is-active`, `is-disabled`, `is-open` are not touched
- No changes to non-v2 templates or LESS files
- No changes to JS state management for structural states

---

## Verification

1. **Grep check** — after changes, this must return zero results (excluding documented keyboard-nav exceptions):
   ```
   grep -r 'is-hovered\|--hovered\|is-active-hovered\|--active-hovered' \
     ckanext/hdx_theme/templates/v2/ \
     ckanext/hdx_theme/hdx-styles/src/common/less/v2/
   ```
2. **Compile check** — LESS build produces zero errors
3. **Visual QA** — in browser, mouse over each affected component (activity card, list item, selection item, dropdown trigger, search input) and confirm hover styles apply correctly
4. **Active+hover QA** — for checklist list items and selection items, set `is-active` then hover; confirm combined styling matches Figma
5. **Showcase page** — components page loads without errors; no broken or missing state variants
6. **Keyboard nav** — tab through the navbar dropdown; confirm focus state renders correctly
