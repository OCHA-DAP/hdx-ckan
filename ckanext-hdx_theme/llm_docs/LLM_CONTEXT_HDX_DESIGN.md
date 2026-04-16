# HDX design context (templates, CSS, JS)

Purpose: This file gives LLMs a quick map of how HDX (CKAN-based) pages are structured and where the current HTML, CSS, and JS live, so future tasks can recreate or refactor existing designs safely.

## Template roots and overrides

- Core CKAN templates: `ckan/templates/`
- HDX theme templates (overrides + new pages): `ckanext-hdx_theme/ckanext/hdx_theme/templates/`
- BEM component templates: `ckanext-hdx_theme/ckanext/hdx_theme/templates/bem.blocks/`

HDX overrides CKAN by adding its template directories in `ckanext-hdx_theme/ckanext/hdx_theme/plugin.py` via `toolkit.add_template_directory(...)`. When a template name matches a core CKAN template, the HDX one takes precedence.

## Core layout templates (HDX theme)

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

## Header and footer composition (HDX theme)

- Header templates:
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header_base.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header-global.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/header-mobile.html`
- Footer templates:
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/footer.html`
  - `ckanext-hdx_theme/ckanext/hdx_theme/templates/footer-wide.html`

These are included from `page.html` or `page_light.html`, so changes to header/footer should start here.

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

- Start from the layout template (`page.html` or `page_light.html`) and identify the specific page template that extends it.
- Check which asset bundles are loaded in that page and trace them back in `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml`.
- For UI elements (forms, cards, tables), inspect or reuse BEM blocks in `templates/bem.blocks` and styles in `less/bem.blocks`.
- Use CKAN core templates and assets as a baseline; HDX overrides live under the HDX theme path.

## Key pages

### Homepage (`/`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/home/index.html`
  - Extends `page.html` (full layout with header, footer, and global asset bundles).
  - Overrides the `header_core` block to use `header-mobile.html` (no desktop nav bar).
  - Removes the toolbar block entirely.
- **Core assets**:
  - `hdx_theme/homepage-styles` — homepage-specific CSS (`homepage/homepage.css`, `homepage/homepage-responsive.css`); preloads `hdx_theme/adaptive-page-styles`.
  - `hdx_theme/homepage-scripts` — homepage JS (`homepage/count.js`, `homepage/homepage-responsive.js`, `vendor/hammer/hammer.js`); preloads `hdx_theme/homepage-styles`.
  - Inherits the full `page.html` stack: `hdx_theme/page-styles`, `hdx_theme/page-scripts`, `hdx_theme/search-scripts`.

---

### Dataset list page (`/dataset` or `/search`)

There are **two versions** of this page that share some assets but use different layouts.

#### Desktop version

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/search.html`
  - Extends `page.html` (full layout with header, sidebar, footer).
  - Renders facet filters via `snippets/facet_list_new.html` and results via `snippets/package_list.html`.
  - Uses the two-column layout inherited from `page.html` (primary + secondary blocks).
- **Core assets**:
  - `hdx_theme/dataset-styles` — general dataset CSS (`datasets/dataset.css`, `datasets/datasets.css`); preloads `dataset-search-styles`, `requestdata-styles`, `charting-styles`.
  - `hdx_theme/dataset-search-styles` — styles for the multiple-select filter widget (`vendor/multiple-select-1.1.0/multiple-select.css`).
  - Inherits the full `page.html` stack: `hdx_theme/page-styles`, `hdx_theme/page-scripts`, `hdx_theme/search-scripts`.

#### Light version

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/search/search.html`
  - Extends `page_light.html` (lightweight layout, no sidebar).
  - Renders the result listing via `light/snippets/package_list.html`.
- **Core assets**:
  - `hdx_theme/dataset-search-styles` — styles for the multiple-select filter widget (`vendor/multiple-select-1.1.0/multiple-select.css`).
  - `hdx_theme/dataset-styles` — general dataset list/detail CSS; preloads `dataset-search-styles`, `requestdata-styles`, `charting-styles`.
  - `hdx_theme/search-light-styles` — light search-specific CSS (`light/search/search-light.css`).
  - `hdx_theme/search-scripts` — common search JS (preloaded by `page_light.html`).
  - `hdx_theme/dataset-search-scripts` — filter/list-header JS (`datasets/list-header.js`, `vendor/multiple-select`); preloads `hdx_theme/ckan` and `dataset-search-styles`.
  - `hdx_theme/dataset-scripts` — additional dataset JS (loaded in the scripts block).

---

### Signals page (`/signals`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/signals.html`
  - Extends `page_v2.html`, which itself extends `page_light.html`.
  - `page_v2.html` loads `hdx_theme/page-extra-light-styles`, `hdx_theme/bem-blocks-styles`, and `hdx_theme/bem-blocks-scripts`.
  - Uses BEM blocks heavily: `bem.blocks/hero.html`, `bem.blocks/card.html`, `bem.blocks/paragraph.html`.
  - UI copy comes from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE']`.
- **Core assets**:
  - `hdx_theme/hdx-signals-scripts` — signals-specific JS (`landing_pages/hdx_signals.js`).
  - `hdx_theme/hdx-signals-styles` — signals-specific CSS (`landing_pages/hdx_signals.css`).
  - `hdx_theme/bem-blocks-styles` and `hdx_theme/bem-blocks-scripts` — shared BEM component styles and JS (from `page_v2.html`).

---

### HAPI page (`/hapi`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/hapi.html`
  - Extends `page_v2.html` (same landing-page layout as Signals above).
  - Uses BEM blocks: `bem.blocks/hero.html`, `bem.blocks/card.html`.
  - Embeds an iframe (`/visualization/hapi-availability/`) for data-availability visualisation.
  - UI copy comes from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['HAPI_LANDING_PAGE']`.
  - No dedicated styles bundle — relies entirely on the inherited `bem-blocks-styles` and `page-extra-light-styles`.
- **Core assets**:
  - `hdx_theme/hdx-hapi-scripts` — HAPI-specific JS (`landing_pages/hdx_hapi.js`).
  - `hdx_theme/bem-blocks-styles` and `hdx_theme/bem-blocks-scripts` — shared BEM component styles and JS (from `page_v2.html`).

---

## Quick path index

- HDX templates: `ckanext-hdx_theme/ckanext/hdx_theme/templates/`
- HDX BEM HTML: `ckanext-hdx_theme/ckanext/hdx_theme/templates/bem.blocks/`
- HDX LESS: `ckanext-hdx_theme/ckanext/hdx_theme/less/`
- HDX BEM LESS: `ckanext-hdx_theme/ckanext/hdx_theme/less/bem.blocks/`
- HDX fanstatic (CSS/JS sources): `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/`
- HDX webassets bundles: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml`
- CKAN core templates: `ckan/templates/`
- CKAN core JS bundles: `ckan/public/base/javascript/webassets.yml`
- CKAN core vendor bundles: `ckan/public/base/vendor/webassets.yml`

