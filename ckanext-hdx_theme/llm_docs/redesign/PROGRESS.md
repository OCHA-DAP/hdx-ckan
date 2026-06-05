# Design V2 Implementation Progress

**Status**: In-progress
**Started**: 2026-04-16
**Last Updated**: 2026-06-05

---

> Task definitions live in `llm_docs/redesign/requirements/`. Task status is tracked in [`requirements/STATUS.md`](requirements/STATUS.md). **Update STATUS.md whenever a task is created, moved to `in_progress`, or `implemented`.**

---

## Architecture

### Design Token Foundation

**Location**: `less/v2/foundation.less` (+ `colors.less`, `spacing.less`, `radius.less`, `elevation.less`, `typography.less`)
**Status**: ✅ Complete

All design tokens from Figma "Visual Redesign / Foundations":
- **Colors**: 6 palettes, 75+ variables (`@hdx-brand-*`, `@hdx-primary-*`, `@hdx-neutral-*`, `@hdx-success-*`, `@hdx-warning-*`, `@hdx-error-*`)
- **Layout**: 9-step spacing scale (4px base), 2 corner radii (sm/md), 4 elevation levels
- **Typography**: 2 font families, 9-step size scale (xs–5xl), 4 weights, 2 line heights. Split across two files:
  - `typography.less` — **variable declarations only** (`@hdx-fs-*`, `@hdx-fw-*`, `@hdx-font-*`, `@hdx-lh-*`). Imported by `foundation.less` to emit CSS custom properties. Never import this directly for mixins.
  - `mixins.less` — all mixin definitions: private parametric cores (`.-hdx-body`, `.-hdx-display`, etc.), named type-style mixins (`.hdx-body-m()`, `.hdx-heading-h4()`, etc.), base-style mixins, and layout mixins (`.v2-sidebar-flex()`, `.v2-content-flex()`)

Variable naming: `@hdx-<category>-<step>` (e.g. `@hdx-brand-5`, `@hdx-space-4`). Decimals: digit-only (0.1→01).
CSS custom property equivalents (`--hdx-*`) are defined in `v2/foundation.css` (task 001).

---

### Layout Templates

**Location**: [`templates/v2/page.html`](../ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/page.html)

**Status**: ✅ **Complete**

`templates/v2/page.html` extends `base.html` directly and is a proper v2 layout base. It is no longer a thin wrapper over `page_light.html`.

**Current structure**:
- Extends `base.html` directly
- Loads Google Fonts (Merriweather + Roboto) in `{% block styles %}`
- Loads `hdx_theme/v2-page-styles`; legacy onboarding and `page-scripts` bundles are commented out pending v1 retirement
- Sets `{% block bodytag %}hdx-v2{% endblock %}` for scoping v2 styles to the body class
- Overrides `{% block page %}` with: header block → main content (toolbar + flash + two-column layout) → footer block
- `{% block header_core %}` includes `v2/header.html` via `{% snippet %}`
- `{% block toolbar %}` renders `<div class="hdx-v2-breadcrumb-row">` with a `{% block breadcrumb_items %}` sub-block; page templates override only `{% block breadcrumb_items %}`
- `{% block flash %}` renders flash messages using `hdx-v2-flash {{ category }}` class (Bootstrap `.alert` removed)
- `secondary_right_side` feature removed; sidebar always renders on the left
- `{% block footer %}` includes `v2/footer.html` via `{% snippet %}`
- `{% block primary %}` (v1 fallback, never reached by v2 pages) annotated with TODO for removal on v1 retirement
- Loads `hdx_theme/v2-page-scripts` in `{% block scripts %}`

**Current usage**: `templates/v2/components.html` renders the v2 component demo page.

---

### LESS Infrastructure

**Source root**: `hdx-styles/src/common/less/v2/`

| File | Purpose |
|---|---|
| `foundation.less` | Exports all design tokens as CSS custom properties (imports colors, spacing, radius, typography) |
| `typography.less` | **Variable declarations only** — font families, size scale, weights, line heights. Imported by `foundation.less` for CSS custom-property output. Do not import this directly from components. |
| `mixins.less` | **Single compile-time entry point** — imports `breakpoints.less` + `typography.less`, then defines all mixins: layout (`.v2-sidebar-flex()`, `.v2-content-flex()`), typography cores, named type-style mixins, and base-style mixins. Import with `@import "mixins.less"` (or `"../mixins.less"` from `components/`). |
| `breakpoints.less` | Breakpoint variables (`@hdx-bp-md`, `@hdx-bp-xl`, `@hdx-bp-xxl`); pulled in automatically by `mixins.less` |
| `layout.less` | Container, breadcrumb row, content-columns base flex; compiled to `v2-page-styles` |
| `search.less` | Search page sections; imports `mixins.less` |
| `dataset.less` | Dataset page sections; imports `mixins.less` |
| `resource-page.less` | Resource page sections; imports `mixins.less` |
| `styles.less` | Hero, page-header, dataset-list, flash messages; compiled to `v2-page-styles`; imports `mixins.less` |
| `components/divider.less` | `.c-divider` — extracted from `navigation.less`; compiled to `divider.css` and registered in `v2-components-styles` |
| `components/*.less` | One file per component; each imports `"../mixins.less"` for tokens and mixins |

**Typography mixin usage:**
- Full 4-property block: `.hdx-body-m-semibold()`, `.hdx-display-l()`, `.hdx-heading-h4()`, etc.
- Component base class (size controlled by modifier): `.hdx-body-medium-base()`, `.hdx-body-semibold-base()`.
- All files using mixins import `mixins.less` only — no separate `typography.less` or `breakpoints.less` imports needed.

---

## Pages Migrated to V2

| Page | Template | Notes                                                                                     |
|------|----------|-------------------------------------------------------------------------------------------|
| Homepage | `home/index.html` | Extends `v2/page.html`                                                                    |
| Dataset search | `search/search.html` | Extends `v2/page.html`; uses `v2=true` gate for v2 UI                                     |
| Dataset page | `package/hdx_read.html` | Extends `v2/page.html`; full page implemented — see `requirements/038-dataset-page.md` |
| Resource page | `package/resource_read.html` | Extends `v2/page.html`; full page implemented — see `requirements/040-resource-page.md` |

### Pages in holding state (on `page_light.html`)

Each page below extends `page_light.html`, manually overrides `{% block styles %}` to load `hdx_theme/page-extra-light-styles` and `hdx_theme/bem-blocks-styles`, loads `hdx_theme/bem-blocks-scripts` in `{% block scripts %}`, and overrides `{% block header_core %}` to include `header-mobile.html`. Ready to migrate to `v2/page.html`.

| Page | Template(s) | Notes |
|------|-------------|-------|
| Landing — Signals | `landing_pages/signals.html` | Also loads `hdx_theme/hdx-signals-styles` / `hdx-signals-scripts` |
| Landing — HAPI | `landing_pages/hapi.html` | Also loads `hdx_theme/hdx-hapi-scripts` |
| Signup — user info | `onboarding/signup/user-info.html` | |
| Signup — value proposition | `onboarding/signup/value-proposition.html` | |
| Signup — verify email | `onboarding/signup/verify-email.html` | |
| Signup — change email | `onboarding/signup/change-email.html` | Also loads `hdx_theme/hdx-form-validator` |
| Signup — account validated | `onboarding/signup/account-validated.html` | |
| Org join — find org | `org/join/find_organisation.html` | |
| Org join — confirm org | `org/join/confirm_organisation.html` | |
| Org join — reason request | `org/join/reason_request.html` | |
| Org join — completed | `org/join/completed.html` | |
| Org request — new request | `org/request/org_new_request.html` | |
| Org request — completed | `org/request/completed_request.html` | |
| Contact contributor | `package/contact_contributor.html` | |
| Request access | `package/request_access.html` | |
| Create/edit dataset | `contribute_flow/create_edit.html` | Also loads `hdx_theme/contribute-flow-styles` |

---

## Component Library (V2 Components)

**Location**: `templates/v2/components/`, `less/v2/components/`, `fanstatic/v2/components/`

**Status**: ✅ **Complete**

**Implemented components**:
- [x] Buttons
- [x] Label
- [x] Avatar + badge
- [x] Dropdown
- [x] Input field
- [x] Navigation
- [x] Selection
- [x] Text link
- [x] Breadcrumb
- [x] Checkbox
- [x] List item
- [x] Letter anchor
- [x] Divider
- [x] Search + autocomplete
- [x] File type indicators
- [x] Tooltips
- [x] Dataset card (with shared clamped-text.js toggle)
- [x] Resource card
- [x] Showcase card
- [x] Anchor links — extended with `heading`, `with_mobile_dropdown` params; mobile sticky dropdown (`c-anchor-links-mobile`) styles in `navigation.less`
- [x] Info icon — `info-icon.html` snippet encapsulating the `c-tooltip-anchor` + `c-info-icon` button + tooltip pattern; HTML-only (no dedicated LESS/CSS)

Each component file should have:
1. **HTML template** (`templates/v2/components/component-name.html`) — reusable snippet with BEM markup
2. **LESS styles** (`less/v2/components/component-name.less`) — styles referencing foundation tokens
3. **Compiled CSS** (`fanstatic/v2/components/component-name.css`) — pre-compiled CSS for webassets

Exception: `info-icon.html` has no dedicated LESS/CSS — it composes existing `c-tooltip-anchor`, `c-info-icon`, and `c-tooltip` styles.

---

## Asset Bundles & Webassets

**Location**: [`fanstatic/webassets.yml`](../ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml)

Bundle configuration:
- `hdx_theme/v2-components-styles` — standalone design system bundle (tokens + components), no Bootstrap
  - Contents: `v2/foundation.css`, then 17 component CSS files: `divider`, `activity-card`, `dataset-card`, `resource-card`, `avatar-badge`, `buttons`, `checkbox`, `copy-button`, `dropdown`, `input-field`, `label`, `letter-anchor`, `list-item`, `navigation`, `selection`, `showcase-card`, `text-link`
  - Kept separate for non-page contexts (component previews, embedded widgets)
- `hdx_theme/v2-page-styles` ✅ Full page bundle: preloads `v2-components-styles`, then adds:
  - `vendor/bootstrap5/css/bootstrap.css`
  - `v2/layout.css` — Bootstrap container overrides aligned to Figma grid specs, scoped to `.hdx-v2`
  - `v2/top-bar.css` — top-bar styles (OCHA services dropdown, documentation link)
  - `v2/footer.css` — footer styles
  - `v2/navbar.css` — main navbar styles (logo, search, nav items, actions, offcanvas)
  - `v2/styles.css` — shared global v2 styles
- `hdx_theme/v2-components-scripts` ✅ Contains: `focus-trap.js`, `password-toggle.js`, `clamped-text.js` (show-more/less), `dropdown.js`, `page-header.js`, `anchor-links.js` (smooth scroll + mobile dropdown + active tracking), `copy-button.js`
- `hdx_theme/v2-page-scripts` ✅ Contains `v2/navbar.js` (navbar panel + offcanvas, tasks 018 + 019) + `v2/search-autocomplete.js` (global search autocomplete, task 045)
- `hdx_theme/v2-search-styles` — page-specific: preloads `v2-page-styles`, adds `v2/search.css`
- `hdx_theme/v2-search-scripts` — page-specific: preloads `v2-page-scripts`, adds `v2/search.js`
- `hdx_theme/v2-dataset-styles` — page-specific: preloads `v2-page-styles`, adds `v2/dataset.css`
- `hdx_theme/v2-dataset-scripts` — page-specific: preloads `v2-page-scripts`, adds `v2/dataset.js` (section accordion)
- `hdx_theme/v2-resource-styles` — page-specific: preloads `v2-page-styles`, adds `v2/resource-page.css` (independent of dataset styles by design)

---


## Implementation Checklist

### Phase 1: Foundation ✅ (Complete)
- [x] Create `less/v2/foundation.less` with all design tokens
- [x] Export design tokens from Figma for reference
- [x] Set up `templates/v2/page.html` to extend `base.html` (not `page_light.html`)
- [x] Create `v2/header.html` and `v2/footer.html` snippets (fully implemented)
- [x] Register v2 asset bundles in `webassets.yml` (`v2-components-styles`, `v2-components-scripts`)
- [x] Test foundation tokens in a simple test page

### Phase 2: Component Library ✅ (Complete)
- [x] Create `templates/v2/components/` directory ✓
- [x] Create `less/v2/components/` directory ✓
- [x] Create `fanstatic/v2/components/` directory ✓
- [x] Build Button component (primary, secondary, tertiary) ✓
- [x] Build Label component (3 sizes × 6 colors) ✓
- [x] Build Badge component (indicator dot) ✓
- [x] Build Divider component (horizontal separator) ✓
- [x] Build Avatar component ✓
- [x] Build Dropdown component ✓
- [x] Build Input field component ✓
- [x] Build Navigation component ✓
- [x] Build Selection component ✓
- [x] Build Text link component ✓
- [x] Build remaining components (File type indicator, Tooltip)
- [x] Register `v2-components-styles` bundle in webassets.yml ✓
- [x] Create `v2-components-scripts` bundle ✓
- [x] Create `v2-page-styles` bundle with Bootstrap + grid layout overrides ✓
- [x] Add placeholder demo page with all components ✓

### Phase 3: Page Migrations 🔲 (Sequential)
- [ ] Signup page
- [ ] Landing pages (signals, hapi)
- [ ] Contact contributor page
- [ ] Find/join org page
- [ ] Homepage
- [ ] Dataset list (light)
- [ ] Dataset list (desktop)
- [ ] Remaining pages (org, user, dataset read, etc.)

### Phase 4: Cleanup 🔲 (Final)
- [ ] Delete old layout templates (`page.html`, `page_light.html`)
- [ ] Delete old BEM blocks (`bem.blocks/`)
- [ ] Remove old asset bundles from `webassets.yml`
- [ ] Rename `templates/v2/page.html` → `page.html`, `templates/v2/components/` → `templates/components/`
- [ ] Update [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md) to reflect final structure

---

## Next Steps

1. **Migrate pages** from `page_light.html` holding state to `v2/page.html` — landing pages, then signup/onboarding, then org/join.
2. **Build page-specific components** as needed during individual page migrations.

---

## References

- **Design Source**: 2055_HDX_delivery (HDX Internal)
- **Migration Strategy**: [PLAN.md](PLAN.md)
- **Design Context**: [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)
- **Foundation Tokens**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)
