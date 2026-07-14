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

Pages in holding state on `page_light.html` (org/join, etc.) manually override `{% block header_core %}` to include the legacy `header-mobile.html`. The following pages have been migrated to `v2/page.html`: homepage, dataset search, dataset page, resource page, all locations, all organisations, organization page (Datasets / Activity / Stats / Members tabs; HDX Connect tab postponed), contact contributor, signup flow (all five pages), HAPI landing page, and Signals landing page. See [**redesign/PROGRESS.md**](redesign/PROGRESS.md) for the full holding-state and migrated-pages lists.

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

### Dataset page (`/dataset/<name>`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/hdx_read.html`
  - Extends `v2/page.html`.
  - Includes `notification_platform/modals.html` (renders subscribe/unsubscribe drawers) and `notification_platform/buttons.html` (via `page-header.html`).
- **Core assets**: `hdx_theme/v2-dataset-page-styles`, `hdx_theme/v2-dataset-page-scripts` (section accordion).

---

### Resource page (`/dataset/<name>/resource/<id>`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/resource_read.html`
  - Extends `v2/page.html`.
- **Core assets**: `hdx_theme/v2-resource-page-styles`.

---

### All Locations page (`/group`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/group/index.html`
  - Extends `v2/page.html`. Single-column layout.
- **Core assets**: `hdx_theme/v2-all-locations-page-styles`, `hdx_theme/v2-all-locations-page-scripts` (HRP filter + A-Z/Z-A sort toggle).

---

### All Organisations page (`/organization`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/index.html`
  - Extends `v2/page.html`. Single-column layout (`content_class = 'hdx-v2-org-list-content'`).
- **Core assets**: `hdx_theme/v2-org-list-page-styles`, `hdx_theme/v2-org-list-page-scripts` (`url-nav.js` + `org-list-page.js`).

---

### Organisation page (`/organization/<name>`)

- **Templates** (one per tab, all extend `v2/page.html` and share the `v2/org_hero.html` hero — `c-page-header` + `c-tabs`):
  - Datasets: `organization/read.html` (reuses the search-page list/filters)
  - Activity: `organization/activity_stream.html`
  - Stats: `organization/stats.html` (Chart.js via `hdx_theme/v2-chart-scripts`)
  - Members: `organization/members.html` (role-grouped `c-member-list-card` list, right-side sidebar, one-click `c-dropdown--link` change-role/approve dropdowns, remove/leave + group-message drawers)
- **Core assets**: `hdx_theme/v2-org-page-styles` on every tab; plus per tab: `v2-search-page-styles`/`-scripts` (Datasets), `v2-chart-scripts` (Stats), `hdx_theme/v2-org-members-page-scripts` (Members: `url-nav.js` + `org-members-page.js`).
- The HDX Connect tab is postponed; the Requested Data tab remains v1.

---

### Contact Contributor page (`/dataset/<name>/contact-contributor`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/contact_contributor.html`
  - Extends `v2/page.html`.
- **Core assets**: `hdx_theme/v2-contact-contributor-page-styles`.

---

### Signup flow (`/signup/`)

- **Templates**: Five pages in `ckanext-hdx_theme/ckanext/hdx_theme/templates/onboarding/signup/`:
  `value-proposition.html` (tier selection), `user-info.html` (step 1 form),
  `verify-email.html` (step 2), `change-email.html` (step 2b), `account-validated.html` (step 3).
  All extend `v2/page.html`. Layout vars set on every page: `outer_row_class='hdx-v2-signup-outer-row'`,
  `breadcrumb_row_class='hdx-v2-breadcrumb-row--white'`, `content_class='hdx-v2-signup-content'`.
- **New components**: `v2/components/signup-tier.html` (`c-signup-tier`) — tier selection card with
  default (gray) and primary (blue) variants, numbered feature badges; `v2/components/step-pager.html`
  (`c-step-pager`) — horizontal 3-step progress bar, pure CSS (no JS).
- **Core assets**:
  - `hdx_theme/v2-signup-page-styles` — page layout (`v2/signup-page.css`) — all 5 pages
  - `hdx_theme/v2-signup-scripts` — `onboarding/came-from-input.js` + `onboarding/confirm-page-leave.js` (both converted to vanilla JS in place) — user-info and change-email pages
  - `hdx_theme/v2-form-validator-scripts` — `v2/form-validator.js` — user-info and change-email pages
  - Legacy `hdx-verify-email-scripts` — verify-email page only
- **Constants**: string copy in `ckanext/hdx_theme/helpers/ui_constants/onboarding/` (one file per page).
- **Analytics**: `hdx_click_stopper` modules on tier CTA buttons preserved; `analytics_account_type` block in account-validated preserved.

---

### Signals page (`/signals`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/signals.html`
  - Extends `v2/page.html`. Full v2 implementation — see `requirements/054-signals-landing-page.md`.
  - Two-column layout at XL: sticky `c-anchor-links` sidebar (5 items) + main content.
  - Hero via `c-page-header` with bell-icon CTA (`cta_icon_src='v2/icons/bell.svg'`); off-white hero row with border-bottom at SM/MD.
  - Featured signals carousel: 3 `c-signal-card` slides in `.hdx-v2-signals-cards`; dots-only nav; Hammer.js swipe; static 3-column flex at XL.
  - Sections: Sign up (Mailchimp form with v2 buttons + `info-icon.html` for HRP tooltip), Data Coverage (`c-content-card` grid), Signals Map (600px iframe), Resources (`c-content-card` grid), FAQ (`c-accordion`), Partners (flex-wrap `<img>` logos).
  - UI copy from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE']`.
- **Core assets**:
  - `hdx_theme/v2-carousel-scripts` — Hammer.js + `carousel.js`; loaded explicitly in template before page scripts.
  - `hdx_theme/v2-signals-landing-page-scripts` — `v2/signals-landing-page.js` (carousel init) + `landing_pages/hdx_signals.js` (form logic: vanilla JS, `is-disabled` class for submit button).
  - `hdx_theme/v2-signals-landing-page-styles` — `v2/signals-landing-page.css` + `v2/components/signal-card.css`.

---

### HAPI page (`/hapi`)

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/hapi.html`
  - Extends `v2/page.html`. Full v2 implementation — see `requirements/053-hdx-hapi-landing-page.md`.
  - Two-column layout at XL: sticky `c-anchor-links` sidebar + main content.
  - Hero via `c-page-header` with `subtitle` param; grey background on hero row only (`hdx-v2-hapi-hero-row`); body row white.
  - Sections: Data Availability (iframe), Be Inspired (`c-content-card` grid 2×2), FAQ (`c-accordion`), Partners (CSS Grid `repeat(5,1fr)` of `<img>` logos).
  - UI copy from `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['HAPI_LANDING_PAGE']`.
- **Core assets**: `hdx_theme/v2-hapi-landing-page-styles`.

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

## V2 JavaScript Patterns

All v2 JavaScript is vanilla — no jQuery. Follow these patterns consistently.

### No jQuery

| jQuery | Vanilla |
|--------|---------|
| `$('#id')` | `document.getElementById('id')` |
| `$('.cls')` | `document.querySelector('.cls')` / `querySelectorAll` |
| `el.on('event', fn)` | `el.addEventListener('event', fn)` |
| `$.ajax(...)` | `fetch(url, { method, headers, body: new URLSearchParams(data) })` |
| `el.trigger('event')` | `el.dispatchEvent(new CustomEvent('event'))` |
| `el.attr('hidden', '')` | `el.setAttribute('hidden', '')` |
| `el.removeAttr('hidden')` | `el.removeAttribute('hidden')` |

### Show / hide

Use the `hidden` attribute, not Bootstrap `d-none`:
```js
element.setAttribute('hidden', '');   // hide
element.removeAttribute('hidden');    // show
```

### Drawer factory

```js
var handle = window.hdxV2Drawer('drawerId');
handle.open();
handle.close();
```

The factory is in `fanstatic/v2/components/drawer.js` (part of `v2-components-scripts`). Drawers dispatch `drawer:close` as a `CustomEvent`; listen with `addEventListener('drawer:close', fn)`.

### Form validation (v2)

Add `data-hdx-v2-form-validator` to a `<form>` element. The validator (`fanstatic/v2/form-validator.js`) auto-inits on `DOMContentLoaded`. Load `hdx_theme/v2-form-validator-scripts` on the page. Do **not** use `data-module="hdx-form-validator"` on v2 pages.

**Error display — `c-search-input` fields**: the validator adds `c-search-input--error` to the input wrapper; a sibling `<span class="c-search-input__error">` (always rendered by the snippet, empty by default) is revealed via the CSS sibling rule `&--error ~ &__error { display: block }`. Server-side errors pre-populate the span and pre-add the modifier class from the template. No `style.display` manipulation — CSS drives visibility entirely.

**Error display — `c-checkbox` fields**: same pattern — `c-checkbox--error` on the `.c-checkbox` wrapper drives a sibling `<span class="c-checkbox__error">` via CSS. The snippet always renders the empty span after the label.

Pass `data-validation-error="…"` (via `input_attrs` / `attrs`) for the inline error text. Fields using `data-live-feedback` use the `c-form-validator__live-feedback` panel as the primary error UI and may omit `data-validation-error`.

---

## Guidance for V2 Development

1. **CSS/BEM conventions** — See [**redesign/CONVENTIONS.md**](redesign/CONVENTIONS.md) for BEM prefixes, media query nesting, breakpoints, container usage, and token rules.

2. **Build in pairs** — Every component needs an HTML snippet (`templates/v2/components/component-name.html`) and LESS styles (`less/v2/components/component-name.less`).

3. **Page migrations** — Migrate pages by switching `{% extends %}` to `v2/page.html`, removing the holding-state `header_core`/`styles`/`scripts` overrides, replacing `bem.blocks/` snippets with `templates/v2/components/` equivalents, and registering any new bundles in `webassets.yml`.

4. **Keep old stack untouched** — Old templates and assets stay in place until all pages are migrated.

5. **Update LLM docs** — When architecture changes, update [**redesign/PROGRESS.md**](redesign/PROGRESS.md) and [**redesign/requirements/STATUS.md**](redesign/requirements/STATUS.md).

