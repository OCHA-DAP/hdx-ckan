# Design V2 Implementation Progress

**Status**: In-progress
**Started**: 2026-04-16
**Last Updated**: 2026-05-04

---

## Overview

This document tracks the implementation of the HDX redesign (v2), a progressive migration from the legacy design system to a new BEM-component-based, fully responsive design sourced from Figma.

The migration strategy follows the plan outlined in [PLAN.md](PLAN.md): build the new design system as a parallel layer, then migrate pages one-by-one, leaving unmigrated pages untouched on the old stack.

> Task definitions, requirements, and implementation checklists are tracked in `llm_docs/redesign/requirements/`.
> Implementation status for each task is tracked in [`requirements/STATUS.md`](requirements/STATUS.md) — a markdown table mapping each requirement file to one of `not_started`, `in_progress`, or `implemented`. Update that file when a task changes state.

---

## Architecture

### Design Token Foundation

**Location**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)

**Status**: ✅ **Complete**

The foundation file contains all design tokens from Figma "Visual Redesign / Foundations":

#### 1. **Color Palettes** (6 palettes, 75+ color variables)
- `@hdx-brand-*` — Brand green (15 steps: 0–10)
- `@hdx-primary-*` — Primary blue (13 steps: 0–9)
- `@hdx-neutral-*` — Neutral grey (16 steps: 0–10)
- `@hdx-success-*` — Feedback success (11 steps: 0–9)
- `@hdx-warning-*` — Feedback warning (11 steps: 0–9)
- `@hdx-error-*` — Feedback error (11 steps: 0–9)

Each palette is documented with Figma step mappings and usage guidance for data visualization.

#### 2. **Layout Tokens**
- **Spacing scale**: 9 steps (4px base unit): `@hdx-space-1` to `@hdx-space-12`
- **Corner radius**: 2 levels: `@hdx-radius-sm` (2px), `@hdx-radius-md` (4px)
- **Elevation (shadows)**: 4 levels: `@hdx-shadow-none`, `@hdx-shadow-sm`, `@hdx-shadow-md`, `@hdx-shadow-lg`

#### 3. **Typography Tokens**
- **Font families**: `@hdx-font-display` (Merriweather, serif), `@hdx-font-body` (Roboto, sans-serif)
- **Font size scale**: 9 steps: `@hdx-fs-xs` (12px) to `@hdx-fs-5xl` (48px)
- **Font weights**: regular (400), medium (500), semibold (600), bold (700)
- **Line heights**: tight (120%), normal (130%)
- **Named type-style mixins** (reusable, composable):
  - Display styles: `.hdx-display-xl()` through `.hdx-display-xs()`
  - Heading styles: `.hdx-heading-h1()` through `.hdx-heading-h4()`
  - Body styles: `.hdx-body-l/m/s/xs()` × regular/medium/semibold
  - Link styles: `.hdx-link-xl()` through `.hdx-link-xs()`
  - Lead text: `.hdx-lead()`

**Naming Convention**: Variables follow `@hdx-<category>-<step>` pattern. Decimals use digit-only notation (0.1→01, 1.5→15).

**Structure**: Organized into logical sections with clear headers and Figma cross-references, making it easy to track updates back to design source.

---

### Layout Templates

**Location**: [`templates/v2/page.html`](../ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/page.html)

**Status**: ✅ **Complete**

`templates/v2/page.html` extends `base.html` directly and is a proper v2 layout base. It is no longer a thin wrapper over `page_light.html`.

**Current structure**:
- Extends `base.html` directly
- Loads Google Fonts (Merriweather + Roboto) in `{% block styles %}`
- Loads `hdx_theme/v2-page-styles` and conditionally loads onboarding bundles
- Sets `{% block bodyclassname %}hdx-v2{% endblock %}` for grid scoping
- Overrides `{% block page %}` with: header block → page_content block (toolbar + flash + content) → footer block
- `{% block header_core %}` includes `v2/header.html` via `{% snippet %}` (top-bar + navbar, fully implemented)
- `{% block footer %}` includes `v2/footer.html` via `{% include %}` (fully implemented)
- Loads `hdx_theme/v2-components-scripts` in `{% block scripts %}`

**Current usage**:
- `templates/v2/components.html` renders the v2 component demo page
- Ready to receive page-level template migrations once header/footer stubs are implemented

---

## Pages Migrated to V2

No pages are currently on `v2/page.html`. All previously migrated pages were reverted to `page_light.html` as part of the structural reorganisation that upgraded `v2/page.html` into a real layout base. They are now in a holding state on the legacy stack, ready to be re-migrated once the v2 header/footer are implemented.

### Pages in holding state (on `page_light.html`)

Each page below:
- Extends `page_light.html` directly
- Manually overrides `{% block styles %}` to load `hdx_theme/page-extra-light-styles` and `hdx_theme/bem-blocks-styles`
- Manually loads `hdx_theme/bem-blocks-scripts` in `{% block scripts %}`
- Overrides `{% block header_core %}` to include `header-mobile.html`

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

**Location**: `templates/v2/components/`, `less/v2/components/`

**Status**: 🔄 **In Progress** (Buttons and core component styles implemented)

The v2 component library uses the current `templates/v2/components/` directory with matching styles in `less/v2/components/`.
- HTML snippets: `templates/v2/components/*.html`
- LESS styles: `less/v2/components/*.less`
- Compiled CSS: `fanstatic/v2/components/*.css`

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

Each component file should have:
1. **HTML template** (`templates/v2/components/component-name.html`) — reusable snippet with BEM markup
2. **LESS styles** (`less/v2/components/component-name.less`) — styles referencing foundation tokens
3. **Compiled CSS** (`fanstatic/v2/components/component-name.css`) — pre-compiled CSS for webassets

---

## Asset Bundles & Webassets

**Location**: [`fanstatic/webassets.yml`](../ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml)

Bundle configuration:
- `hdx_theme/v2-components-styles` — standalone design system bundle (tokens + components), no Bootstrap
  - Contents: `v2/foundation.css`, `v2/components/avatar-badge.css`, `v2/components/buttons.css`, `v2/components/checkbox.css`, `v2/components/dropdown.css`, `v2/components/input-field.css`, `v2/components/label.css`, `v2/components/letter-anchor.css`, `v2/components/list-item.css`, `v2/components/navigation.css`, `v2/components/selection.css`, `v2/components/text-link.css`
  - Kept separate for non-page contexts (component previews, embedded widgets)
- `hdx_theme/v2-page-styles` ✅ Full page bundle: preloads `v2-components-styles`, then adds:
  - `vendor/bootstrap5/css/bootstrap.css`
  - `v2/layout.css` — Bootstrap container overrides aligned to Figma grid specs, scoped to `.hdx-v2`
  - `v2/top-bar.css` — top-bar styles (OCHA services dropdown, documentation link)
  - `v2/footer.css` — footer styles
  - `v2/navbar.css` — main navbar styles (logo, search, nav items, actions, offcanvas)
- `hdx_theme/v2-components-scripts` ✅ Contains `v2/components/password-toggle.js`

Still needed (pending task 018/019):
- `hdx_theme/page-v2-scripts` — navbar panel/offcanvas JS (`v2/navbar.js`)

Page-specific bundles will be created as pages are migrated (e.g., `hdx_theme/homepage-v2-styles`).

---

## Design Token References

**Location**: implemented directly in `less/v2/` and `less/v2/components/`

**Status**: ✅ **Released into the current v2 implementation**

The current Figma-derived foundation and component tokens are implemented in the `less/v2/` files.

Use the design foundations in `less/v2/foundation.less`, `less/v2/colors.less`, `less/v2/spacing.less`, `less/v2/radius.less`, `less/v2/elevation.less`, and `less/v2/typography.less` as the source of truth for the redesign.

---

## Implementation Checklist

### Phase 1: Foundation ✅ (Complete)
- [x] Create `less/v2/foundation.less` with all design tokens
- [x] Export design tokens from Figma for reference
- [x] Set up `templates/v2/page.html` to extend `base.html` (not `page_light.html`)
- [x] Create `v2/header.html` and `v2/footer.html` snippets (stubs — content TBD)
- [x] Register v2 asset bundles in `webassets.yml` (`v2-components-styles`, `v2-components-scripts`)
- [x] Test foundation tokens in a simple test page

### Phase 2: Component Library 🔄 (Next Priority)
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

## Quality Checklist — Before Continuing

✅ **foundation.less**
- [x] Proper file location: `less/v2/foundation.less` ✓
- [x] Descriptive section headers with Figma references ✓
- [x] Consistent naming convention (`@hdx-<category>-<step>`) ✓
- [x] All color palettes documented with usage guidance ✓
- [x] Layout tokens (spacing, radius, elevation) complete ✓
- [x] Typography tokens as reusable mixins ✓
- [x] Line count: 460 lines (reasonable size) ✓

✅ **templates/v2/page.html**
- [x] Extends `base.html` directly
- [x] Loads `v2-page-styles` (Bootstrap + grid + components) and `v2-components-scripts` bundles
- [x] Sets `bodyclassname` to `hdx-v2` for grid scoping
- [x] Includes `v2/header.html` (top-bar + responsive navbar, fully implemented)
- [x] Includes `v2/footer.html` (fully implemented)
- [ ] Pages previously on this template (signup, landing, org/join, etc.) are on `page_light.html` holding state — ready for re-migration now that header/footer are real

---

## Next Steps

1. **Implement task 018** — navbar dropdowns: user menu panel, notifications panel (Products dropdown done in 017). Requires creating `navbar-user-menu.html`, `navbar-notifications.html`, and `v2/navbar.js`
2. **Implement task 019** — offcanvas mobile/tablet menu (`navbar-offcanvas.html` is currently a stub)
3. **Register `hdx_theme/page-v2-scripts`** bundle with `v2/navbar.js` once task 018/019 are complete; load from `v2/page.html`
4. **Re-migrate pages** from `page_light.html` holding state back to `v2/page.html`, starting with the simplest (landing pages, then signup/onboarding, then org/join, etc.)
5. **Continue building component library** as needed for page migrations
6. **Iterate** through remaining pages (homepage, dataset list, etc.)

---

## Notes for Developers

- **Use foundation tokens** in all v2 component styles — never hardcode colors, spacing, or typography values
- **Test on multiple breakpoints** — v2 is fully responsive (desktop, tablet, mobile)
- **Keep old stack untouched** during migration — unmigrated pages should not be affected by v2 changes
- **Update [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)** as architecture evolves
- **Use BEM naming** for all v2 components: `.component__element--modifier`

---

## References

- **Design Source**: 2055_HDX_delivery (HDX Internal)
- **Migration Strategy**: [PLAN.md](PLAN.md)
- **Design Context**: [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)
- **Foundation Tokens**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)
