# HDX design context (templates, CSS, JS)

Purpose: This file gives LLMs a quick map of how HDX (CKAN-based) pages are structured and where the current HTML, CSS, and JS live, so future tasks can recreate or refactor existing designs safely.

---

## ⚠️ Mandatory Rules for V2 Work

These rules apply to every task that touches the V2 redesign. Violating them introduces regressions or duplicate code.

### 1 — Never compile LESS files

The IDE compiles LESS to CSS automatically whenever a `.less` file is saved. **Do not run `lessc`, `gulp`, `npm run build`, or any other LESS compilation command.** Just edit the source `.less` file and the compiled `.css` output in `fanstatic/v2/` will update on its own.

If a `.css` output appears out of date, that is an environment issue for the developer to resolve — do not attempt to fix it by running compilation tools.

### 2 — Always reuse existing V2 components

Before writing any new HTML, CSS, or JS for a V2 feature, check whether an existing component already covers the requirement.

**Component parameters are documented in the snippet's header comment.** Read those before using a component.

**Do not duplicate links, routes, or section content** that is already rendered by an existing snippet. If you need the same content in a second context (e.g. a mobile panel reusing desktop menu sections), extract a shared body snippet and include it in both places.

### 3 — Always update STATUS.md when task state changes

Whenever a task is created, moved to `in_progress`, or `implemented`, update the status table in [`redesign/requirements/STATUS.md`](redesign/requirements/STATUS.md). Status must always reflect the current state.

---

## Design V2 Migration

HDX is undergoing a progressive redesign using a Figma-driven, responsive component system. For progress, architecture, and implementation status, see [**redesign/PROGRESS.md**](redesign/PROGRESS.md).

### Figma extraction process

Export components from Figma using **Locofy Lightning** with `Units: rem`, `Styling: CSS`, `File naming: Pascal Case`, `CSS Variables: ON`. Merge the plugin output (HTML + `global.css` + `index.css`) into a single reference HTML file (`global.css` content first, then `index.css`, all inside one `<style>` block). Use that merged file as input with the prompt in [**redesign/COMPONENT_IMPLEMENTATION_PROMPT.md**](redesign/COMPONENT_IMPLEMENTATION_PROMPT.md).

---

## Template roots and overrides

- Core CKAN templates: `ckan/templates/`
- HDX theme templates (overrides + new pages): `ckanext-hdx_theme/ckanext/hdx_theme/templates/`
- BEM component templates (legacy): `ckanext-hdx_theme/ckanext/hdx_theme/templates/bem.blocks/`
- V2 component templates: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/`
- V2 component styles: `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/`
- Compiled V2 CSS: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/components/`

HDX overrides CKAN by adding its template directories in `ckanext-hdx_theme/ckanext/hdx_theme/plugin.py` via `toolkit.add_template_directory(...)`. When a template name matches a core CKAN template, the HDX one takes precedence.

## Core layout templates (HDX theme)

There are three active layout base templates. The goal is to maintain exactly these three variants during the migration period, then converge to `v2/page.html` alone.

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/base.html`
  - Base HTML skeleton for all pages.
  - Renders global analytics snippets and includes `{{ h.render_assets('style') }}`.
  - Sets the main `page` block where layout templates plug content.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/page.html`
  - Main full layout. Extends `base.html`.
  - Loads asset bundles: `hdx_theme/page-styles`, `hdx_theme/page-scripts`, `hdx_theme/search-scripts`, and onboarding bundles.
  - Assembles header, toolbar, flash messages, two-column layout, and footer.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/page_light.html`
  - "Light" layout variant for simplified pages.
  - Loads `hdx_theme/page-light-styles` and `hdx_theme/page-light-scripts`.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/page.html`
  - New v2 layout. Extends `base.html` directly.
  - Loads Google Fonts and `hdx_theme/v2-page-styles`; legacy onboarding and `page-scripts` bundles commented out.
  - `{% block toolbar %}` renders the breadcrumb row; pages override only `{% block breadcrumb_items %}` inside it. Set `breadcrumb_row_class` to add modifier classes on the row div (e.g. `'hdx-v2-breadcrumb-row--white'` for white background, no bottom border).
  - Flash messages use `hdx-v2-flash {{ category }}` class (no Bootstrap `.alert`).
  - Includes `v2/header.html` and `v2/footer.html` via `{% snippet %}`.
  - Target base for all pages once the v2 redesign is complete.

## Header and footer composition (HDX theme)

### Legacy header/footer (used by `page.html` and `page_light.html`)

- Header templates:
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header_base.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header-global.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header-mobile.html`
- Footer templates:
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/footer.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/footer-wide.html`

### V2 header/footer (used by `v2/page.html`)

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/header.html` — top-bar + responsive navbar (fully implemented)
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/footer.html` — dark-teal footer panel (fully implemented)

Pages in holding state on `page_light.html` (landing pages, signup, org/join, etc.) manually override `{% block header_core %}` to include the legacy `header-mobile.html`. The homepage, dataset search, dataset, and resource pages have already been migrated to `v2/page.html`. See [**redesign/PROGRESS.md**](redesign/PROGRESS.md) for the full holding-state and migrated-pages lists.

## BEM components (HDX custom UI blocks)

HDX uses Block-Element-Modifier (BEM) components as reusable UI building blocks, layered on Bootstrap defaults.

- BEM LESS sources: `ckanext-hdx_theme/ckanext/hdx_theme/less/bem.blocks/`
  - Examples: `card.less`, `input_field.less`, `checkbox_field.less`, `select2_field.less`, `textarea_field.less`.
- BEM HTML snippets: `ckanext-hdx_theme/ckanext/hdx_theme/templates/bem.blocks/`
  - Examples: `card.html`, `input_field.html`, `checkbox_field.html`, `select2_field.html`, `textarea_field.html`.

When building or refactoring UI, prefer these BEM blocks and keep naming consistent.

## Static asset roots

- HDX theme public assets: `ckanext-hdx_theme/ckanext/hdx_theme/public/`
  - Images, fonts, site icons.
- HDX fanstatic assets (bundled by webassets): `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/`
  - Main CSS and JS sources referenced by the HDX webassets bundles.
- CKAN core public assets: `ckan/public/base/`
  - Core JS, vendor JS, images, and base styles.

## Webassets (CSS/JS bundling)

HDX and CKAN both use webassets. Bundles are referenced in templates via `{% asset 'bundle-name' %}` and compiled/served by CKAN.

### HDX theme bundles

- Bundle definitions: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml`
- Common bundles used in layout templates:
  - `hdx_theme/page-styles`, `hdx_theme/page-scripts`
  - `hdx_theme/page-light-styles`, `hdx_theme/page-light-scripts`
  - `hdx_theme/bem-blocks-styles`, `hdx_theme/bem-blocks-scripts`
  - `hdx_theme/search-scripts`, `hdx_theme/search-styles`
- Bundles reference files from `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/` and also from CKAN core paths (for select2, etc.).

### CKAN core bundles

- Core JS bundles: `ckan/public/base/javascript/webassets.yml`
  - Main bundles include `main` and `ckan`.
- Core vendor bundles: `ckan/public/base/vendor/webassets.yml`
  - Vendor bundles include `jquery`, `vendor`, `bootstrap`, `select2-css`, etc.

## How assets are loaded in templates

- `base.html` uses `{{ h.render_assets('style') }}` and expects pages to contribute styles via `{% asset %}` blocks.
- `page.html` loads `hdx_theme/page-styles` and `hdx_theme/page-scripts` plus search and onboarding bundles.
- `page_light.html` loads `hdx_theme/page-light-styles` and `hdx_theme/page-light-scripts` plus onboarding bundles.

Example page-specific template (light search):
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/search/search.html`
  - Adds `dataset-search-styles`, `dataset-styles`, `search-light-styles`, and corresponding scripts.

## Practical guidance for design changes

- Start from the layout template (`page.html`, `page_light.html`, or `v2/page.html`) and identify the specific page template that extends it.
- Check which asset bundles are loaded in that page and trace them back in `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml`.
- For UI elements (forms, cards, tables), inspect or reuse BEM blocks in `templates/bem.blocks` and styles in `less/bem.blocks`.
- Use CKAN core templates and assets as a baseline; HDX overrides live under the HDX theme path.

## Key pages

### Homepage (`/`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/home/index.html`
  - Extends `v2/page.html`. Adds `hdx_theme/v2-home-page-styles` (hero, intro, highlights, bar-chart) and `hdx_theme/v2-home-page-scripts` (Hammer.js, highlights-carousel.js, bar-chart.js).

---

### Dataset list page (`/dataset` or `/search`)

#### V2 version (active)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/search.html`
  - Extends `v2/page.html`. Uses `v2=true` gate to switch UI inside shared snippets.
  - Two-column layout: `hdx-v2-search-sidebar` (filter panel) + `hdx-v2-search-content` (results).
- **Core assets**: `hdx_theme/v2-search-page-styles`, `hdx_theme/v2-search-page-scripts` (highlight.js + search-page.js). MiniSearch/feature-index libs auto-loaded via `v2-search-scripts` (preloaded by `v2-page-scripts`).

#### Legacy desktop version

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/search.html`
  - Extends `page.html`. Uses Bootstrap two-column layout.
- **Core assets**: `hdx_theme/dataset-styles`, `hdx_theme/dataset-search-styles`; inherits `page.html` stack.

#### Legacy light version

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/search/search.html`
  - Extends `page_light.html`. No sidebar.
- **Core assets**: `hdx_theme/search-light-styles`, `hdx_theme/dataset-styles`, `hdx_theme/dataset-search-scripts`, `hdx_theme/dataset-scripts`.

---

### Signals page (`/signals`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/signals.html`
  - Extends `page_light.html` directly (holding state — ready to migrate to `v2/page.html`).
  - Overrides `{% block header_core %}` to include legacy `header-mobile.html`.
  - Manually loads `hdx_theme/page-extra-light-styles` and `hdx_theme/bem-blocks-styles` in `{% block styles %}`.
  - Uses BEM blocks heavily: `bem.blocks/hero.html`, `bem.blocks/card.html`, `bem.blocks/paragraph.html`.
  - UI copy comes from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE']`.
- **Core assets**:
  - `hdx_theme/hdx-signals-scripts` — signals-specific JS (`landing_pages/hdx_signals.js`).
  - `hdx_theme/hdx-signals-styles` — signals-specific CSS (`landing_pages/hdx_signals.css`).
  - `hdx_theme/bem-blocks-styles` and `hdx_theme/bem-blocks-scripts` — shared BEM component styles and JS (loaded directly by this template).

---

### HAPI page (`/hapi`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/hapi.html`
  - Extends `page_light.html` directly (holding state — ready to migrate to `v2/page.html`).
  - Overrides `{% block header_core %}` to include legacy `header-mobile.html`.
  - Manually loads `hdx_theme/page-extra-light-styles` and `hdx_theme/bem-blocks-styles` in `{% block styles %}`.
  - Uses BEM blocks: `bem.blocks/hero.html`, `bem.blocks/card.html`.
  - Embeds an iframe (`/visualization/hapi-availability/`) for data-availability visualisation.
  - UI copy comes from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['HAPI_LANDING_PAGE']`.
- **Core assets**:
  - `hdx_theme/hdx-hapi-scripts` — HAPI-specific JS (`landing_pages/hdx_hapi.js`).
  - `hdx_theme/bem-blocks-styles` and `hdx_theme/bem-blocks-scripts` — shared BEM component styles and JS (loaded directly by this template).

---

## Quick path index

- HDX templates: `ckanext-hdx_theme/ckanext/hdx_theme/templates/`
- HDX BEM HTML (legacy): `ckanext-hdx_theme/ckanext/hdx_theme/templates/bem.blocks/`
- HDX V2 component templates: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/`
- HDX LESS (legacy): `ckanext-hdx_theme/ckanext/hdx_theme/less/`
- HDX V2 component styles: `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/`
- HDX design tokens (v2): `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less`
- HDX V2 compiled CSS: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/components/`
- HDX fanstatic (CSS/JS sources): `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/`
- HDX webassets bundles: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml`
- CKAN core templates: `ckan/templates/`
- CKAN core JS bundles: `ckan/public/base/javascript/webassets.yml`
- CKAN core vendor bundles: `ckan/public/base/vendor/webassets.yml`

---

### V2 Component Demo (`/components`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components.html`
  - Extends `templates/v2/page.html` (v2 layout scaffold).
  - **Purpose**: Demo page rendering all v2 components side-by-side for development verification.
- **Core assets**:
  - `hdx_theme/v2-components-styles` — all v2 component styles (loaded by `v2/page.html`).
  - `hdx_theme/v2-components-scripts` — all v2 component JS (loaded by `v2/page.html`).

---

## Guidance for V2 Development

1. **CSS/BEM conventions** — See [**redesign/CONVENTIONS.md**](redesign/CONVENTIONS.md) for BEM prefixes, media query nesting, breakpoints, container usage, and token rules.

2. **Build in pairs** — Every component needs an HTML snippet (`templates/v2/components/component-name.html`) and LESS styles (`less/v2/components/component-name.less`).

3. **Page migrations** — Migrate pages by switching `{% extends %}` to `v2/page.html`, removing the holding-state `header_core`/`styles`/`scripts` overrides, replacing `bem.blocks/` snippets with `templates/v2/components/` equivalents, and registering any new bundles in `webassets.yml`.

4. **Keep old stack untouched** — Old templates and assets stay in place until all pages are migrated.

5. **Update LLM docs** — When architecture changes, update [**redesign/PROGRESS.md**](redesign/PROGRESS.md) and [**redesign/requirements/STATUS.md**](redesign/requirements/STATUS.md).

