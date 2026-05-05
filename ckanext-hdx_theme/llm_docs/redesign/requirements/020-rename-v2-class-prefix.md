# 020 — Rename v2 CSS Class Prefix: `hdx-` → `hdx-v2-`

## Goal

All v2 layout components currently use the `hdx-` CSS class prefix. This conflicts with the global `hdx-` namespace used by design tokens, LESS variables, and non-v2 components. Rename the prefix to `hdx-v2-` across all v2-specific templates, styles, and scripts to make the boundary explicit and prevent future naming collisions.

---

## Scope

### In scope — rename `hdx-` → `hdx-v2-` for these components

| Component | Example class before | After |
|---|---|---|
| Header wrapper | `hdx-header` | `hdx-v2-header` |
| Top bar | `hdx-top-bar`, `hdx-top-bar__inner` | `hdx-v2-top-bar`, `hdx-v2-top-bar__inner` |
| Navbar | `hdx-navbar`, `hdx-navbar__logo` | `hdx-v2-navbar`, `hdx-v2-navbar__logo` |
| Footer | `hdx-footer`, `hdx-footer__top` | `hdx-v2-footer`, `hdx-v2-footer__top` |
| Offcanvas | `hdx-offcanvas`, `hdx-offcanvas__body` | `hdx-v2-offcanvas`, `hdx-v2-offcanvas__body` |
| User menu | `hdx-user-menu`, `hdx-user-menu__section-toggle` | `hdx-v2-user-menu`, `hdx-v2-user-menu__section-toggle` |
| Notifications | `hdx-notifications` | `hdx-v2-notifications` |

The rename follows BEM: `hdx-v2-{block}__{element}--{modifier}`.

### Out of scope — do NOT rename

- **Design tokens**: LESS variables (`@hdx-brand-*`, `@hdx-neutral-*`, `@hdx-space-*`, etc.) and CSS custom properties (`--hdx-brand-7`, `--hdx-neutral-0`, etc.) are global — leave untouched.
- **`c-` prefix components**: `c-button`, `c-checkbox`, `c-text-link`, `c-search-input`, etc. use a separate prefix and are not v2 layout components.
- **Non-v2 templates**: Any template not under `templates/v2/` or not in the v2 fanstatic bundle.
- **`hdx-` classes in non-v2 context**: Legacy styles in the main stylesheet that happen to use `hdx-` for other purposes.

---

## Files to Update

### HTML Templates — `ckanext/hdx_theme/templates/v2/`

Update every `class="hdx-..."` attribute and every `id="hdx-..."` attribute that belongs to a v2 layout component. Files:

- `header.html`
- `footer.html`
- `navbar-offcanvas.html`
- `navbar-notifications.html`
- `navbar-user-menu.html`
- `page.html`
- `components.html`
- All files under `components/` that reference v2 layout component classes

### LESS Sources — `hdx-styles/src/common/less/v2/`

Rename selectors in:

- `navbar.less`
- `top-bar.less`
- `footer.less`
- Any component LESS file that defines a selector starting with `.hdx-` (not `.c-`)

Update comments that reference the old class names.

### JavaScript — `fanstatic/v2/navbar.js`

Update all references to affected class names and IDs:

- `getElementById('hdx-offcanvas')` → `getElementById('hdx-v2-offcanvas')`
- `getElementById('hdx-panel-' + name)` → `getElementById('hdx-v2-panel-' + name)`
- `getElementById('hdx-offcanvas-level-' + levelId)` → `getElementById('hdx-v2-offcanvas-level-' + levelId)`
- `querySelector('[data-hdx-panel="..."]')` → `querySelector('[data-hdx-v2-panel="..."]')`
- `querySelector('[data-hdx-close="..."]')` → `querySelector('[data-hdx-v2-close="..."]')`
- `querySelector('[data-hdx-offcanvas-level]')` → `querySelector('[data-hdx-v2-offcanvas-level]')`
- `querySelector('[data-hdx-offcanvas-back]')` → `querySelector('[data-hdx-v2-offcanvas-back]')`
- Class selectors: `.hdx-offcanvas__primary` → `.hdx-v2-offcanvas__primary`, etc.

The HTML data attributes (`data-hdx-panel`, `data-hdx-close`, `data-hdx-offcanvas-level`, `data-hdx-offcanvas-back`) must be updated in both the JS selectors and the corresponding HTML templates in the same pass.

### LLM Docs — `llm_docs/`

- `LLM_CONTEXT_HDX_DESIGN.md`: Update all class name examples and any rules that reference the `hdx-` prefix for v2 components.
- `redesign/PROGRESS.md`: Update any class references if present.
- `redesign/requirements/STATUS.md`: Add this task.

---

## Acceptance Criteria

1. All selectors in v2 LESS/CSS files that previously started with `.hdx-` now start with `.hdx-v2-`.
2. All HTML attributes (`class`, `id`, `data-*`) in `templates/v2/` that previously used `hdx-` for v2 layout components now use `hdx-v2-`.
3. All JS selectors and string literals in `fanstatic/v2/navbar.js` match the renamed HTML.
4. No `hdx-` class or ID belonging to a v2 layout component remains unrenamed.
5. Design tokens (`@hdx-*`, `--hdx-*`) and `c-` prefix component classes are untouched.
6. Non-v2 templates compile and render without regression.
7. LLM docs reflect the new naming convention.

---

## Notes

- Perform the rename as a single atomic pass (search-and-replace scoped to `templates/v2/`, `less/v2/`, and `fanstatic/v2/`) to avoid partial states.
- Verify by grepping for `.hdx-` in the v2 directories after the rename — only design-token variable references should remain.
- The `c-` component prefix is intentionally different and should not be touched.
