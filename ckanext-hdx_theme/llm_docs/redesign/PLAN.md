# Plan: Progressive Migration to New HDX Design

## Summary

HDX has three layout bases (`page.html`, `page_light.html`, `landing_pages/page.html`) all inheriting from `base.html`, plus a library of BEM blocks. The new Figma design introduces new building blocks (buttons, links, tabs, etc.) and makes every page responsive. Because we cannot migrate everything at once, the strategy is to **build the new design system as a parallel layer** — a new base layout, new BEM blocks, and new asset bundles — then **migrate pages one-by-one** by switching their `{% extends %}` to the new layout, leaving unmigrated pages untouched on the old stack.

---

## Steps

### 1. Create a new design-system foundation alongside the old one

Create new files that live **next to** the existing ones — never modify the old layouts or BEM blocks during this step.

- **New layout template**: `templates/v2/page.html` extending `base.html`.
  - New responsive header/footer snippets (`header-v2.html`, `footer-v2.html`).
  - Loads a new set of asset bundles (see step 2) instead of `page-styles` / `page-scripts`.
  - Provides the same Jinja blocks (`styles`, `scripts`, `content`, `breadcrumb_content`, etc.) so page templates can switch parent with minimal changes.
- **New component library**: `templates/v2/components/` and `less/v2/components/`.
  - One HTML snippet + one LESS stylesheet per Figma building block: `button.html`, `link.html`, `tabs.html`, `tag.html`, etc.
  - Compiled CSS committed to `fanstatic/v2/components/` for webassets bundling.
  - Keep the existing `bem.blocks/` untouched; old pages keep using them.
- **New design tokens file**: `hdx-styles/src/common/less/v2/foundation.less` holding the new Figma colours, spacing, typography, and breakpoints as variables. Both v2 blocks and page-level CSS reference this single source of truth.

### 2. Register new webasset bundles in `webassets.yml`

Add bundles in [webassets.yml](../../ckanext/hdx_theme/fanstatic/webassets.yml) that are loaded **only** by the new layout:

- `hdx_theme/page-v2-styles` — new base CSS (design tokens, reset/normalise, responsive grid, new header/footer styles).
- `hdx_theme/page-v2-scripts` — new base JS (responsive header behaviour, any shared new-design JS).
- `hdx_theme/v2-components-styles` / `hdx_theme/v2-components-scripts` — compiled from `templates/v2/components/`.

Old bundles (`page-styles`, `page-light-styles`, `bem-blocks-styles`, etc.) remain unchanged, so unmigrated pages are unaffected.

### 3. Migrate pages one-by-one, starting with the simplest

For each page migration:
1. Change `{% extends "page.html" %}` (or `page_light.html`) → `{% extends "templates/v2/page.html" %}`.
2. Replace old snippet calls (`bem.blocks/card.html`) with v2 equivalents (`templates/v2/components/card.html`).
3. Swap old page-specific asset bundles for new ones (e.g., `homepage-styles` → `homepage-v2-styles`), or inline the new CSS into the v2 bundle if the page is simple enough.
4. Remove any old CSS classes/markup that the new design no longer needs.

**Suggested migration order** (least coupling → most coupling):
1. **Landing pages** (`/signals`, `/hapi`) — only 2 templates, self-contained, already BEM-heavy. Create a landing page wrapper (for example `landing_pages/v2.html`) extending `templates/v2/page.html` with `v2-components-*` bundles.
2. **Homepage** (`/`) — single template, custom layout, few shared snippets.
3. **Dataset list light** (`/dataset` light version) — moderate complexity, shared search snippets.
4. **Dataset list desktop** (`/dataset` desktop version) — heavier, facets/sidebar.
5. **Remaining pages** (org pages, user pages, dataset read, contribute flow, etc.).

### 4. Handle the header and footer transition

The header (`header-mobile.html`) and footer (`footer-wide.html`, `footer.html`) are shared across all pages. During the transition:

- Old layout (`page.html`, `page_light.html`) keeps including the **old** header/footer.
- New layout (`templates/v2/page.html`) includes the **new** `header-v2.html` / `footer-v2.html`.
- This avoids breaking unmigrated pages when the new header/footer ships.
- Once every page is migrated, delete the old header/footer files and the old layouts.

### 5. Unify `page.html` and `page_light.html` into a single responsive layout

Today two layouts exist because the old design was not responsive (`page.html` = desktop, `page_light.html` = mobile/light). Since the new design is fully responsive:

- `templates/v2/page.html` should be **one template** that replaces both.
- Pages that currently have a desktop *and* light variant (e.g., dataset search) can be **collapsed into a single template** during migration, eliminating the dual-template maintenance.
- The view functions in Python (e.g., `light_dataset.py` → `search()`) can be updated to render the single new template once the migration for that page is done.

### 6. Clean up after all pages are migrated

- Delete old layout templates (`page.html`, `page_light.html`, `landing_pages/page.html`).
- Delete old header/footer files, old BEM blocks (`bem.blocks/`, `less/bem.blocks/`).
- Remove old asset bundles from `webassets.yml` and delete the corresponding CSS/JS source files from `fanstatic/`.
- Rename `templates/v2/page.html` → `page.html`, `templates/v2/components/` → `templates/components/`, etc., so the codebase is clean.
- Update [`LLM_CONTEXT_HDX_DESIGN.md`](../LLM_CONTEXT_HDX_DESIGN.md) to reflect the final structure.

---

## Further Considerations

1. **LESS vs CSS custom properties for design tokens?** The current BEM blocks use LESS. The new design system could stay with LESS for consistency, or adopt CSS custom properties (`:root` vars) so tokens are runtime-switchable and don't need a build step. Recommendation: use CSS custom properties for tokens, LESS for block-level styles that reference them.
2. **Should `templates/v2/page.html` extend `base.html` directly or introduce a new base?** `base.html` contains analytics/GTM boilerplate that all pages need regardless of design. Extending it directly keeps the chain short. Only create a `base_v2.html` if the new design requires different `<head>` content (e.g., new font loading, meta viewport changes).
3. **Automated visual regression testing.** Since old and new pages coexist, consider adding screenshot-based tests (e.g., Cypress + Percy, or Playwright snapshots) to catch unintended bleed between old and new styles during the transition.

