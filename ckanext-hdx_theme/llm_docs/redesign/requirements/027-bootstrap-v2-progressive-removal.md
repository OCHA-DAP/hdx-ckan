# Task 027: Bootstrap progressive removal in v2

Remove all Bootstrap layout and utility class usage from v2 HTML templates. Bootstrap JS components (Modal, Tooltip, Popover, Tab, Dropdown) and legacy (non-v2) pages are **out of scope** for this task.

This follows the Bootstrap audit (task 022) and implements decision **B1 — progressive removal of Bootstrap class usage in v2**, replacing every Bootstrap grid/utility class with custom LESS or design-system patterns.

---

## Scope

**In scope:**
- All Bootstrap grid classes in v2 templates: `row`, `col-*`, `gx-*`, `gy-*`, `g-*`, `align-items-*` (on grid rows), `col-auto`
- All Bootstrap utility classes in v2 templates: `d-md-none`, `pt-*`, `gap-*`, `justify-content-*`
- Container class handling (see decision below)
- CONVENTIONS.md update to ban Bootstrap classes in v2

**Out of scope:**
- Bootstrap JS components (Modal, Tooltip, Popover, Tab, Dropdown) — no change
- Legacy (non-v2) templates and JS files — no change
- `bootstrap.css` bundle inclusion — not removed from `v2-page-styles` in this task
- Breadcrumb — remains unchanged pending its own v2 migration

---

## Files Affected

| File | Bootstrap usage present |
|------|------------------------|
| `templates/v2/footer.html` | `row`, `col-*`, `gx-*`, `gy-*`, `g-*`, `align-items-*`, `justify-content-*`, `col-auto`, `gap-*` |
| `templates/v2/header.html` | `d-md-none`, `container` |
| `templates/v2/page.html` | `container`, `pt-3` |
| `hdx-styles/src/common/less/v2/layout.less` | `.hdx-v2 .container` override — may be removed or repurposed |
| `llm_docs/redesign/CONVENTIONS.md` | References Bootstrap `.container` — must be updated |

---

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| 1 | Container handling — keep Bootstrap `.container` with `.hdx-v2` override, replace with `hdx-v2-container`, or inline per BEM element? | Option 2 adopted: `hdx-v2-container` custom class introduced in `layout.less`. All v2 templates (`header.html`, `footer.html`, `page.html`, `home/index.html`, etc.) use `.hdx-v2-container` on `__inner` elements. The `.hdx-v2 .container` override was removed. |

---

## Migration steps

Steps must be executed in this order. Steps 1–2 must be completed and agreed before any implementation work starts.

### Step 1 — Decide container approach

Review the three options above. The decision determines whether step 3 involves a simple rename or more significant LESS restructuring.

### Step 2 — Audit and document all Bootstrap class occurrences

Before touching any file, produce a complete list of every Bootstrap class used in v2 templates and the LESS rule that will replace each one. This becomes the implementation checklist.

Grep targets:
- `templates/v2/footer.html`
- `templates/v2/header.html`
- `templates/v2/page.html`

For each class, document: current class → replacement strategy (LESS rule, BEM element, or design token).

### Step 3 — Resolve container (based on Step 1 decision)

**If Option 2 (`hdx-v2-container`):**
- Add `.hdx-v2-container` to `layout.less` with the same rules as `.hdx-v2 .container`
- Replace `.container` with `.hdx-v2-container` in `header.html`, `page.html`, and all section templates that use the two-layer pattern (e.g., `home/index.html`)
- Remove or keep `.hdx-v2 .container` override depending on whether any non-v2 templates still rely on it within `.hdx-v2` scope

**If Option 1 (status quo):**
Skip template changes; document in CONVENTIONS.md that `.container` is intentionally kept under `.hdx-v2` override.

### Step 4 — Replace footer Bootstrap grid

`templates/v2/footer.html` is the primary Bootstrap grid consumer. All `row`, `col-*`, gutter, and alignment classes must be moved to `footer.less`.

Approach:
- Replace Bootstrap column classes with BEM elements already present (`hdx-v2-footer__newsletter`, `hdx-v2-footer__social`, `hdx-v2-footer__nav-col`, etc.)
- Implement the grid/flex layout in `footer.less` using LESS `@hdx-bp-*` breakpoints
- Use `flex-wrap`, `flex: 0 0 <width>`, or CSS Grid depending on what the layout requires — no single approach is mandated, but the result must match the existing visual output
- The `col-md-9` / `col-md-3` newsletter–social split and the three-column nav grid must be reproduced exactly

### Step 5 — Replace header Bootstrap utilities

`templates/v2/header.html` uses `d-md-none` to hide the search icon at MD and above.

Replacement:
- Add a display-hiding rule to `navbar.less` (or a header-specific block in `styles.less`) scoped to the relevant BEM element, using `@media (min-width: @hdx-bp-md) { display: none; }`
- Remove `d-md-none` from the template

No other utility classes in `header.html` need replacing at this stage (dropdown structure uses Bootstrap JS only; class names there are Bootstrap data-attribute hooks, not layout/utility classes).

### Step 6 — Replace page.html Bootstrap utilities

`templates/v2/page.html` uses:
- `pt-3` on the flash-message wrapper — replace with a LESS-driven spacing rule using `var(--hdx-space-4)` (equivalent 16px), scoped to the flash wrapper class or element
- `.container` — handled in Step 3

### Step 7 — Update CONVENTIONS.md

Rewrite the **Container and full-bleed sections** section based on the Step 1 decision. Regardless of which option is chosen, add a clear rule:

> **Do not use Bootstrap grid classes (`row`, `col-*`) or utility classes (`d-*`, `gap-*`, `pt-*`, etc.) in v2 templates. Layout, spacing, and responsive behavior must be implemented in LESS using `@hdx-bp-*` breakpoints and design tokens.**

Remove the existing reference to Bootstrap `.container` class if Option 2 is adopted.

---

## Risks and considerations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Footer layout regression — the Bootstrap 12-column grid is replaced by hand-written flex/CSS grid; pixel-level differences are possible | Medium | Verify at every breakpoint against current screenshots before and after |
| `hdx-v2-container` rename misses an occurrence — a template with `.container` not caught in the audit keeps the Bootstrap name | Low | Grep `templates/v2/` for `\bcontainer\b` as part of step 8 verification |
| `layout.less` `.hdx-v2 .container` override retained after rename — creates dead CSS | Low | Remove the old rule in the same PR if all occurrences are renamed |
| Section templates outside `templates/v2/` that use the two-layer pattern (e.g. `home/index.html`) are not updated | Medium | Extend the grep in step 2 to cover all templates that render inside `.hdx-v2` scope |
| Future page migrations add Bootstrap classes before CONVENTIONS.md is updated | Medium | Merge CONVENTIONS.md update in the same PR as the first file change |

---

## Out of scope (explicitly)

- Bootstrap JS (Modal, Tooltip, Popover, Tab, Dropdown) — not touched
- `vendor/bootstrap5/css/bootstrap.css` bundle inclusion — not removed
- Legacy JS files using Bootstrap 4 jQuery API — not touched
- Alert component redesign — `.alert` styling is a separate future task
- Breadcrumb migration — explicitly deferred per task brief
