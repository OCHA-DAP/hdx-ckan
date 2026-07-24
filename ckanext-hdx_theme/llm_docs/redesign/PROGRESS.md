# Design V2 Implementation Progress

**Status**: In-progress
**Started**: 2026-04-16
**Last Updated**: 2026-07-13

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
  - `mixins.less` — all mixin definitions: private parametric cores (`.-hdx-body`, `.-hdx-display`, etc.), named type-style mixins (`.hdx-body-m()`, `.hdx-heading-h4()`, etc.), base-style mixins, and layout mixins (`.v2-sidebar-flex()`, `.v2-content-flex()`, `.v2-sidebar-sticky()`)

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
- `{% block header_core %}` includes `v2/header.html` via `{% snippet %}`; `v2/header.html` takes an optional `minimal=True` param (logo-only navbar, no top-bar/search/nav items/actions/hamburger/offcanvas) used by the login/forgot-password pages
- `{% block toolbar %}` renders `<div class="hdx-v2-breadcrumb-row">` with a `{% block breadcrumb_items %}` sub-block; page templates override only `{% block breadcrumb_items %}`; set `breadcrumb_row_class` variable for modifier classes on the row div (e.g. `'hdx-v2-breadcrumb-row--white'`)
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
| `mixins.less` | **Single compile-time entry point** — imports `breakpoints.less` + `typography.less`, then defines all mixins: layout (`.v2-sidebar-flex()`, `.v2-content-flex()`, `.v2-sidebar-sticky()`), typography cores, named type-style mixins, and base-style mixins. Import with `@import "mixins.less"` (or `"../mixins.less"` from `components/`). |
| `breakpoints.less` | Breakpoint variables (`@hdx-bp-md`, `@hdx-bp-xl`, `@hdx-bp-xxl`); pulled in automatically by `mixins.less` |
| `layout.less` | Container, breadcrumb row (`hdx-v2-breadcrumb-row` + `--white` modifier), generic sidebar/content column classes on `.hdx-v2-content-columns` (`--gap`, `--gap-xl`, `--stack`, `__sidebar` [+ `--xl-only`, `--sticky`, `--right`], `__content`); compiled to `v2-page-styles` |
| `search-page.less` | Search page layout + `.hdx-v2-dataset-list`; imports `mixins.less` |
| `dataset-page.less` | Dataset page sections; imports `mixins.less` |
| `resource-page.less` | Resource page sections; imports `mixins.less` |
| `contact-contributor-page.less` | Contact Contributor page sections; imports `mixins.less` |
| `signup-page.less` | Signup flow page layout (tiers + form pages); imports `mixins.less` |
| `hapi-landing-page.less` | HAPI landing page styles (hero row, sidebar, sections, iframe, cards, partner grid); imports `mixins.less` |
| `signals-landing-page.less` | Signals landing page styles (hero row, carousel, form card, map iframe, partner grid); imports `mixins.less` |
| `home-page.less` | Homepage-only sections (hero, intro, highlights); compiled to `v2-home-page-styles`; imports `mixins.less` |
| `error-page.less` | 404 / 403 / Server Error page layout (centered logo/heading/body/CTA column); compiled to `v2-error-page-styles`; imports `mixins.less` |
| `components/divider.less` | `.c-divider` — standalone component; compiled to `divider.css` and registered in `v2-components-styles` |
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
| All Locations | `light/group/index.html` | Extends `v2/page.html`; sidebar + sort JS in `v2/all-locations-page.js` |
| All Organisations | `organization/index.html` | Extends `v2/page.html`; org card with clamped-text, KPI row, url-nav.js |
| Contact Contributor | `package/contact_contributor.html` | Extends `v2/page.html`; single-column; native dropdown + textarea; `breadcrumb_row_class` white; see `requirements/050-contact-contributor-v2.md` |
| Signup — value-proposition | `onboarding/signup/value-proposition.html` | Extends `v2/page.html`; `c-signup-tier` cards; `hdx_click_stopper` analytics preserved |
| Signup — user-info | `onboarding/signup/user-info.html` | Step 1 form; `c-step-pager`; `c-search-input` + `c-checkbox`; `data-hdx-v2-form-validator` |
| Signup — verify-email | `onboarding/signup/verify-email.html` | Step 2; `c-step-pager`; legacy `hdx-verify-email-scripts` bundle kept |
| Signup — change-email | `onboarding/signup/change-email.html` | Step 2b form; `c-step-pager`; `data-hdx-v2-form-validator` |
| Signup — account-validated | `onboarding/signup/account-validated.html` | Step 3; `c-step-pager`; `analytics_account_type` block preserved |
| HAPI landing page | `landing_pages/hapi.html` | Extends `v2/page.html`; `c-anchor-links` sticky sidebar; `c-accordion` FAQ; `c-content-card` Be Inspired; CSS Grid partner logos; `c-page-header` with subtitle; see `requirements/053-hdx-hapi-landing-page.md` |
| Signals landing page | `landing_pages/signals.html` | Extends `v2/page.html`; `c-page-header` with bell-icon CTA; featured signals carousel (Hammer.js + `carousel.js`, dots-only, SM/MD); Mailchimp signup form with v2 buttons; signals map iframe; `c-accordion` FAQ; partner logos; see `requirements/054-signals-landing-page.md` |
| Organization page | `organization/read.html`, `organization/activity_stream.html`, `organization/stats.html`, `organization/members.html` | Extend `v2/page.html`; shared `v2/org_hero.html` (page-header + `c-tabs`); tasks 056–059 (Datasets / Activity / Stats / Members); HDX Connect tab postponed |
| Crisis / Event pages | `pages/read_page.html` (serves `/event/<name>` + `/dashboards/<name>`) | Extends `v2/page.html`; `page-header.html` (description sourced from the first `description`-type CMS section, not the page's own keywords field); new `v2/crisis-section.html` dispatcher + `crisis-page.less`/`crisis-page.js`; dataset list reuses `search_results_wrapper.html` like the org Datasets tab; `/m/` light routes untouched; see `requirements/060-crisis-event-pages-v2.md` |
| Error page (404/403/Server Error) | `error_document_template.html` | Extends `v2/page.html` with `{% block header %}`/`{% block footer %}`/`{% block scripts %}` emptied out (no nav chrome, no JS) and `{% block main_content %}` replaced with the centered logo/heading/body/CTA layout; 500/503/anything-else collapses into one "Server Error" copy, 403 keeps its own copy; see `requirements/062-error-pages-v2.md` |
| Login | `user/signin.html` | Extends `v2/page.html`; `{% block header %}` uses `v2/header.html` with new `minimal=True` param (logo-only navbar, no top-bar/search/nav/actions/offcanvas); real page content, no popup/widget indirection (no longer renders `widget/onboarding/login.html`); "remember me" cookie prefill/gravatar-style swap now shows initials only via `c-avatar`; see `requirements/064-auth-pages-v2.md` |
| Forgot password | `user/forgot_password.html` | Extends `v2/page.html`; same `minimal=True` header; confirmation is a same-route swap between two sibling cards toggled via the `hidden` attribute (no more `widget/onboarding/recoverSuccess.html`/loading-screen widget); invisible reCAPTCHA still bound to the submit button; see `requirements/064-auth-pages-v2.md` |

### Pages in holding state (on `page_light.html`)

Each page below extends `page_light.html`, manually overrides `{% block styles %}` to load `hdx_theme/page-extra-light-styles` and `hdx_theme/bem-blocks-styles`, loads `hdx_theme/bem-blocks-scripts` in `{% block scripts %}`, and overrides `{% block header_core %}` to include `header-mobile.html`. Ready to migrate to `v2/page.html`.

| Page | Template(s) | Notes |
|------|-------------|-------|
| Org join — find org | `org/join/find_organisation.html` | |
| Org join — confirm org | `org/join/confirm_organisation.html` | |
| Org join — reason request | `org/join/reason_request.html` | |
| Org join — completed | `org/join/completed.html` | |
| Org request — new request | `org/request/org_new_request.html` | |
| Org request — completed | `org/request/completed_request.html` | |
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
- [x] Anchor links — extended with `heading`, `with_mobile_dropdown` params; mobile sticky dropdown (`c-anchor-links-mobile`) styles in `components/anchor-links.less`; wrapper always renders (no heading required for sticky); supports `external` flag for new-tab links with icon
- [x] Info icon — `info-icon.html` snippet encapsulating the `c-tooltip-anchor` + `c-info-icon` button + tooltip pattern; HTML-only (no dedicated LESS/CSS)
- [x] KPI card — `kpi-card.html` / `kpi-card.css`; label + optional info icon + bold value; used on All Locations and All Organisations pages
- [x] Org list card — `org-list-card.html` / `org-list-card.css`; title + date + expandable description + dataset/member counts; used on All Organisations page
- [x] Step pager — `step-pager.html` / `step-pager.css`; horizontal 3-step progress indicator; pure CSS (no JS); used on all signup form pages
- [x] Signup tier — `signup-tier.html` / `signup-tier.css`; tier selection card for value-proposition page; default and primary (blue) variants; numbered feature badges or checkmark icons
- [x] Content card — `content-card.html` / `content-card.less`; title + description + `c-text-link`; used in HAPI Be Inspired section
- [x] Accordion — `accordion.html` / `accordion.less`; CSS-only `<details>`/`<summary>`; first item open by default via `open` attr; used in HAPI and Signals FAQ
- [x] Page header — `page-header.html` / `page-header.less`; hero section with logo, title (omitted when empty), optional `state_label_text`/`state_label_color` chip after the title, subtitle, description, optional CTA button + icon; used on HAPI and Signals landing pages, dataset/org/resource pages, and crisis/event pages
- [x] Signal card — `signal-card.html` / `signal-card.less`; featured signal with location label, date, type label, description/image, source + CTA buttons; used in Signals carousel
- [x] Notification item — `notification-item.html` / `notification-item.less`; title + optional sysadmin bracket tag + meta row (date + arrow link); `.c-notification-item--sysadmin` highlight modifier; used in the navbar notifications dropdown
- [x] Stats card — `stats-card.html` / `stats-card.less`; KPI figure + label card; used on the org page Stats tab
- [x] Member list card — `member-list-card.html` / `member-list-card.less`; avatar + profile links + role/registered line + counters, `caller()` actions body, `--stacked` variant; used on the org page Members tab

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
  - Contents: `v2/foundation.css`, then component CSS files: `divider`, `activity-card`, `dataset-card`, `resource-card`, `org-list-card`, `member-list-card`, `avatar-badge`, `buttons`, `checkbox`, `copy-button`, `dropdown`, `input-field`, `label`, `letter-anchor`, `list-item`, `nav-item`, `notification-item`, `anchor-links`, `pagination`, `breadcrumb`, `page-header`, `selection`, `showcase-card`, `text-link`, `highlight-card`, `overlay`, `signup-tier`, `step-pager`, `content-card`, `accordion`, `stats-card`
  - Kept separate for non-page contexts (component previews, embedded widgets)
- `hdx_theme/v2-page-styles` ✅ Full page bundle: preloads `v2-components-styles`, then adds:
  - `vendor/bootstrap5/css/bootstrap.css`
  - `v2/layout.css` — Bootstrap container overrides aligned to Figma grid specs, scoped to `.hdx-v2`
  - `v2/top-bar.css` — top-bar styles (OCHA services dropdown, documentation link)
  - `v2/footer.css` — footer styles
  - `v2/navbar.css` — main navbar styles (logo, search, nav items, actions, offcanvas)
- `hdx_theme/v2-components-scripts` ✅ Contains: `input-field.js` (password toggle, renamed from `password-toggle.js`), `clamped-text.js` (show-more/less), `dropdown.js`, `page-header.js`, `anchor-links.js` (smooth scroll + mobile dropdown + active tracking), `copy-button.js`
- `hdx_theme/v2-page-scripts` ✅ Contains `v2/navbar.js` (navbar + offcanvas, FocusTrap inlined) + `v2/search-autocomplete.js`; preloads `v2-search-scripts` (MiniSearch/feature-index)
- `hdx_theme/v2-search-scripts` — global lib bundle: MiniSearch, normalize.js, feature-index; auto-loaded via `v2-page-scripts` preload
- `hdx_theme/v2-search-page-styles` — search page: adds `v2/search-page.css`
- `hdx_theme/v2-search-page-scripts` — search page: adds `highlight.js` + `v2/url-nav.js` + `v2/search-page.js` (`url-nav.js` is a shared nav-param module also used by the org list page and the org members page)
- `hdx_theme/v2-dataset-page-styles` — dataset page: adds `v2/dataset-page.css`
- `hdx_theme/v2-dataset-page-scripts` — dataset page: adds `v2/dataset-page.js` (section accordion)
- `hdx_theme/v2-resource-page-styles` — resource page: adds `v2/resource-page.css`
- `hdx_theme/v2-home-page-styles` — homepage: adds `v2/home-page.css` + `v2/bar-chart.css`
- `hdx_theme/v2-home-page-scripts` — homepage: adds Hammer.js, `v2/highlights-carousel.js`, `v2/bar-chart.js`
- `hdx_theme/v2-all-locations-page-styles` — All Locations page: adds `v2/all-locations-page.css`
- `hdx_theme/v2-all-locations-page-scripts` — All Locations page: adds `v2/all-locations-page.js` (HRP filter + A-Z/Z-A sort)
- `hdx_theme/v2-org-list-page-styles` — All Organisations page: adds `v2/org-list-page.css` (org-list-card styles come from the preloaded `v2-components-styles` bundle)
- `hdx_theme/v2-org-list-page-scripts` — All Organisations page: adds `v2/url-nav.js` + `v2/org-list-page.js`
- `hdx_theme/v2-org-page-styles` — Organization page (all tabs, 056–059): adds `v2/org-page.css` (hero band, activity/stats sections, members layout incl. the invite tags widget)
- `hdx_theme/v2-org-members-page-scripts` — Organization page Members tab: adds `v2/url-nav.js` + `v2/org-members-page.js` (change-role/approve dropdown wiring, drawers + invisible reCAPTCHA, invite tags-autocomplete)
- `hdx_theme/v2-chart-scripts` — Chart.js lib bundle (`chartjs/*` + `v2/charts.js`); loaded by the org page Stats tab
- `hdx_theme/v2-contact-contributor-page-styles` — Contact Contributor page: adds `v2/contact-contributor-page.css`
- `hdx_theme/v2-signup-page-styles` — Signup flow pages: adds `v2/signup-page.css`; loaded on all 5 signup pages
- `hdx_theme/v2-hapi-landing-page-styles` — HAPI landing page: adds `v2/hapi-landing-page.css`
- `hdx_theme/v2-carousel-scripts` — shared carousel lib: `vendor/hammer/hammer.js` + `v2/carousel.js`; loaded explicitly by each page template that uses the carousel (no preload)
- `hdx_theme/v2-signals-landing-page-styles` — Signals landing page: adds `v2/signals-landing-page.css` + `v2/components/signal-card.css`
- `hdx_theme/v2-signals-landing-page-scripts` — Signals landing page: adds `v2/signals-landing-page.js` + `landing_pages/hdx_signals.js`; requires `v2-carousel-scripts` loaded first in the template
- `hdx_theme/v2-signup-scripts` — Signup scripts: `onboarding/came-from-input.js` (vanilla JS rewrite in place) + `onboarding/confirm-page-leave.js` (vanilla JS rewrite in place); loaded on user-info and change-email pages
- `hdx_theme/v2-form-validator-scripts` — Form validation: vanilla JS validator (`v2/form-validator.js`); activated by `data-hdx-v2-form-validator` on `<form>` elements; loaded by notification platform templates and signup form pages (user-info, change-email)
- `hdx_theme/v2-error-page-styles` — 404/403/Server Error page: adds `v2/error-page.css`; no scripts bundle (page has no interactive behavior)
- `hdx_theme/v2-auth-page-styles` — Login + forgot-password pages: adds `v2/auth-page.css` (shared card/navbar-shell styling, loaded by both templates)
- `hdx_theme/v2-login-page-scripts` — Login page: adds `v2/login-page.js` (lockout/MFA pre-checks, required-field gating, remember-me cookie prefill)
- `hdx_theme/v2-forgot-password-page-scripts` — Forgot-password page: adds `v2/forgot-password-page.js` (AJAX submit, invisible reCAPTCHA, recover/confirmation card swap)

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

### Phase 3: Page Migrations ✅ (Complete)
- [x] Signup page
- [x] Landing page — HAPI (`/hapi/`)
- [x] Landing page — Signals (`/signals/`)
- [x] Contact contributor page
- [ ] Find/join org page
- [x] Homepage
- [x] Dataset list (light + desktop — unified in v2 search template)
- [x] Dataset page
- [x] Resource page
- [x] All Locations page
- [x] All Organisations page
- [x] Organization page (Datasets / Activity / Stats / Members tabs — 056–059; HDX Connect tab postponed)
- [ ] Remaining pages (user pages, org join, onboarding, etc.)

### Phase 4: Cleanup 🔲 (Final)
- [ ] Delete old layout templates (`page.html`, `page_light.html`)
- [ ] Delete old BEM blocks (`bem.blocks/`)
- [ ] Remove old asset bundles from `webassets.yml`
- [ ] Rename `templates/v2/page.html` → `page.html`, `templates/v2/components/` → `templates/components/`
- [ ] Update [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md) to reflect final structure

---

## Next Steps

1. **Migrate remaining holding-state pages** from `page_light.html` — org/join pages.
2. **Build page-specific components** as needed during individual page migrations.
3. **Organization page HDX Connect tab** — postponed.

---

## References

- **Design Source**: 2055_HDX_delivery (HDX Internal)
- **Migration Strategy**: [PLAN.md](PLAN.md)
- **Design Context**: [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)
- **Foundation Tokens**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)
