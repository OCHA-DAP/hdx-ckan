# Design V2 Implementation Progress

**Status**: Cycle 1 complete — shipped as an alpha release
**Started**: 2026-04-16

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
- `{% block header_core %}` includes `v2/header.html` via `{% snippet %}`, passing `quick_links` (fetched once at the top of `page.html`); `v2/header.html` takes an optional `minimal=True` param (logo-only navbar, no top-bar/search/nav items/actions/hamburger/offcanvas) used by the login/forgot-password pages
- `{% block toolbar %}` renders `<div class="hdx-v2-breadcrumb-row">` with a `{% block breadcrumb_items %}` sub-block; page templates override only `{% block breadcrumb_items %}`; set `breadcrumb_row_class` variable for modifier classes on the row div (e.g. `'hdx-v2-breadcrumb-row--white'`)
- `{% block flash %}` renders flash messages using `hdx-v2-flash {{ category }}` class (Bootstrap `.alert` removed)
- `secondary_right_side` feature removed; sidebar always renders on the left
- `{% block footer %}` includes `v2/footer.html` via `{% snippet %}`, passing the same `quick_links`
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
| Dataset search | `search/search.html` | Extends `v2/page.html`; uses `v2=true` gate for v2 UI; Archived toggle + Applied Filters pills (XL) — see `requirements/065-advanced-filters-v2.md` |
| Dataset page | `package/hdx_read.html` | Extends `v2/page.html`; full page implemented — see `requirements/038-dataset-page.md` |
| Resource page | `package/resource_read.html` | Extends `v2/page.html`; full page implemented — see `requirements/040-resource-page.md` |
| All Locations | `light/group/index.html` | Extends `v2/page.html`; sidebar + sort JS in `v2/pages/locations-list.js` |
| All Organisations | `organization/index.html` | Extends `v2/page.html`; org card with clamped-text, KPI row, url-nav.js |
| Contact Contributor | `package/contact_contributor.html` | Extends `v2/page.html`; single-column; `select.html` dropdown + `text-field.html` textarea; `breadcrumb_row_class` white; see `requirements/050-contact-contributor-v2.md` |
| Signup — value-proposition | `onboarding/signup/value-proposition.html` | Extends `v2/page.html`; `c-signup-tier` cards; `hdx_click_stopper` analytics preserved |
| Signup — user-info | `onboarding/signup/user-info.html` | Step 1 form; `c-step-pager`; `c-search-input` + `c-checkbox`; `data-hdx-v2-form-validator` |
| Signup — verify-email | `onboarding/signup/verify-email.html` | Step 2; `c-step-pager`; legacy `hdx-verify-email-scripts` bundle kept |
| Signup — change-email | `onboarding/signup/change-email.html` | Step 2b form; `c-step-pager`; `data-hdx-v2-form-validator` |
| Signup — account-validated | `onboarding/signup/account-validated.html` | Step 3; `c-step-pager`; `analytics_account_type` block preserved |
| HAPI landing page | `landing_pages/hapi.html` | Extends `v2/page.html`; `c-anchor-links` sticky sidebar; `c-accordion` FAQ; `c-content-card` Be Inspired; CSS Grid partner logos; `c-page-header` with subtitle; see `requirements/053-hdx-hapi-landing-page.md` |
| Signals landing page | `landing_pages/signals.html` | Extends `v2/page.html`; `c-page-header` with bell-icon CTA; featured signals carousel (Hammer.js + `carousel.js`, dots-only, SM/MD); Mailchimp signup form with v2 buttons; signals map iframe; `c-accordion` FAQ; partner logos; see `requirements/054-signals-landing-page.md` |
| Organization page | `organization/read.html`, `organization/activity_stream.html`, `organization/stats.html`, `organization/members.html` | Extend `v2/page.html`; shared `v2/org-hero.html` (page-header + `c-tabs`); tasks 056–059 (Datasets / Activity / Stats / Members); HDX Connect tab postponed |
| Crisis / Event pages | `pages/read_page.html` (serves `/event/<name>` + `/dashboards/<name>`) | Extends `v2/page.html`; `page-header.html` (description sourced from the first `description`-type CMS section, not the page's own keywords field); new `v2/crisis-section.html` dispatcher + `crisis-page.less`/`crisis-page.js`; dataset list reuses `search_results_wrapper.html` like the org Datasets tab; `/m/` light routes untouched; see `requirements/060-crisis-event-pages-v2.md` |
| Error page (404/403/Server Error) | `error_document_template.html` | Extends `v2/page.html` with `{% block header %}`/`{% block footer %}`/`{% block scripts %}` emptied out (no nav chrome, no JS) and `quick_links = []` and `{% block main_content %}` replaced with the centered logo/heading/body/CTA layout; 500/503/anything-else collapses into one "Server Error" copy, 403 keeps its own copy; see `requirements/062-error-pages-v2.md` |
| Login | `user/signin.html` | Extends `v2/page.html`; sets `quick_links = []`; `{% block header %}` uses `v2/header.html` with new `minimal=True` param (logo-only navbar, no top-bar/search/nav/actions/offcanvas); real page content, no popup/widget indirection (no longer renders `widget/onboarding/login.html`); "remember me" cookie prefill/gravatar-style swap now shows initials only via `c-avatar`; see `requirements/064-auth-pages-v2.md` |
| Forgot password | `user/forgot_password.html` | Extends `v2/page.html`; sets `quick_links = []`; same `minimal=True` header; confirmation is a same-route swap between two sibling cards toggled via the `hidden` attribute (no more `widget/onboarding/recoverSuccess.html`/loading-screen widget); invisible reCAPTCHA still bound to the submit button; see `requirements/064-auth-pages-v2.md` |
| Archived Dataviz | `archived_quick_links/main.html` | Extends `v2/page.html`; single-column; title+count header, outbound-link row list via `text-button.html` + `c-divider`; see `requirements/066-archived-dataviz-v2.md` |
| Dataviz Gallery | `dataviz/index.html` | Extends `v2/page.html`; single-column; `c-dataviz-card` grid, `search-nav-controls.html` reused for sort/page-size (12/24/36); see `requirements/067-dataviz-gallery-v2.md` |
| Request access | `package/request_access.html` | Extends `v2/page.html`; see `requirements/061-hdx-connect-flow-v2.md` |
| My Organisations (user dashboard) | `user/dashboard_organizations.html` | Extends `v2/user-dashboard-base.html` (shared left menu via `c-nav-item` size s, for the dashboard/settings pages); sibling dashboard/settings pages still v1; see `requirements/072-user-dashboard-my-organisations-v2.md` |

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
- [x] Navigation — nav item `size` m (navbar) / s (vertical menu, user dashboard sidebar)
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
- [x] Org list card — `org-list-card.html` / `org-list-card.css`; title + optional `role`/`member_since`/`last_updated` line + expandable description + dataset/member counts; used on All Organisations and My Organisations pages
- [x] Step pager — `step-pager.html` / `step-pager.css`; horizontal 3-step progress indicator; pure CSS (no JS); used on all signup form pages
- [x] Signup tier — `signup-tier.html` / `signup-tier.css`; tier selection card for value-proposition page; default and primary (blue) variants; numbered feature badges or checkmark icons
- [x] Content card — `content-card.html` / `content-card.less`; title + description + `c-text-link`; used in HAPI Be Inspired section
- [x] Accordion — `accordion.html` / `accordion.less`; CSS-only `<details>`/`<summary>`; first item open by default via `open` attr; used in HAPI and Signals FAQ
- [x] Page header — `page-header.html` / `page-header.less`; hero section with logo, title (omitted when empty), optional `title_count` (count badge) or `title_actions` (XL-only text-button row) next to/under the title, optional `state_label_text`/`state_label_color` chip after the title, subtitle, description, optional CTA button + icon; `__top--no-card` when there's no org card; used on HAPI and Signals landing pages, dataset/org/resource pages, crisis/event pages, Locations, Organisations-list, Dataviz Gallery, and Archived Dataviz
- [x] Signal card — `signal-card.html` / `signal-card.less`; featured signal with location label, date, type label, description/image, source + CTA buttons; used in Signals carousel
- [x] Notification item — `notification-item.html` / `notification-item.less`; title + optional sysadmin bracket tag + meta row (date + arrow link); `.c-notification-item--sysadmin` highlight modifier; used in the navbar notifications dropdown
- [x] Stats card — `stats-card.html` / `stats-card.less`; KPI figure + label card; used on the org page Stats tab
- [x] Member list card — `member-list-card.html` / `member-list-card.less`; avatar + profile links + role/registered line + counters, `caller()` actions body, `--stacked` variant; used on the org page Members tab
- [x] Data grid status — `data-grid-status.html` / `data-grid-status.less`; presentational availability swatch (not a real checkbox); used by the location page Data Grid Availability feature (task 063)
- [x] Dataviz card — `dataviz-card.html` / `dataviz-card.less`; thumbnail + title + clamped description + date/DATA-link footer + gated Edit link; own `c-dataviz-card-grid` wrapper; used on the Dataviz Gallery page (task 067)
- [x] Alert — `alert.html` / `alert.less`; 4 variants (success/warning/info/error), dismissible by default; shared across page-level flash banners and form/drawer messages
- [x] Activity card — `activity-card.html` / `activity-card.less`; used on the org page Activity tab
- [x] Tabs — `tabs.html` / `tabs.less`; used on the org page header
- [x] Table — `table.html` / `table.less`
- [x] Toggle — `toggle.html`; styles in `selection.less` alongside Radio/Graph point
- [x] Copy button — `copy-button.html` / `copy-button.less`; used on the resource page
- [x] Graph point — `graph-point.html`; styles in `selection.less`; chart data-point dot with focus ring
- [x] Radio — `radio.html`; styles in `selection.less`

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
  - Contents: `v2/foundation.css`, `v2/overlay.css`, then component CSS files: `accordion`, `activity-card`, `activity-item`, `alert`, `anchor-links`, `avatar-badge`, `breadcrumb`, `buttons`, `checkbox`, `content-card`, `copy-button`, `data-grid-status`, `dataset-card`, `dataviz-card`, `divider`, `drawer`, `dropdown`, `form-field`, `highlight-card`, `input-field`, `label`, `letter-anchor`, `list-item`, `member-list-card`, `nav-item`, `notification-item`, `org-list-card`, `page-header`, `pagination`, `resource-card`, `selection`, `showcase-card`, `signup-tier`, `spinner`, `stats-card`, `step-pager`, `table`, `tabs`, `signal-card`, `text-link`
  - Kept separate for non-page contexts (component previews, embedded widgets)
- `hdx_theme/v2-page-styles` ✅ Full page bundle: preloads `v2-components-styles`, then adds:
  - `vendor/bootstrap5/css/bootstrap.css`
  - `v2/footer.css` — footer styles
  - `v2/layout.css` — Bootstrap container overrides aligned to Figma grid specs, scoped to `.hdx-v2`
  - `v2/nav-controls.css` — shared sort + results-per-page dropdown pair
  - `v2/navbar.css` — main navbar styles (logo, search, nav items, actions, offcanvas)
  - `v2/top-bar.css` — top-bar styles (OCHA services dropdown, documentation link)
- `hdx_theme/v2-components-scripts` ✅ Contains: `v2/utils.js` (shared `window.hdxV2.*` helpers incl. `FocusTrap`, loaded first), then `alert.js`, `anchor-links.js` (smooth scroll + mobile dropdown + active tracking), `clamped-text.js` (show-more/less), `copy-button.js`, `drawer.js`, `dropdown.js`, `input-field.js` (password toggle), `page-header.js`, `tooltip.js`, `toggle.js`
- `hdx_theme/v2-page-scripts` ✅ Contains `v2/contribute.js` + `v2/group-message-drawer.js` + `v2/navbar.js` (navbar + offcanvas, uses `window.hdxV2.FocusTrap`) + `v2/search-autocomplete.js`; preloads `v2-components-scripts` and `v2-search-scripts` (MiniSearch/feature-index)
- `hdx_theme/v2-search-scripts` — global lib bundle: MiniSearch, normalize.js, feature-index; auto-loaded via `v2-page-scripts` preload
- `hdx_theme/v2-search-page-styles` — search page: adds `v2/pages/search.css`
- `hdx_theme/v2-search-page-scripts` — search page: adds `jquery.highlight.js` + `highlight.js` + `v2/url-nav.js` + `v2/pages/search.js` (`url-nav.js` is a shared nav-param module also used by the org list page, the org members page and the dataviz gallery)
- `hdx_theme/v2-dataset-page-styles` — dataset page: adds `v2/pages/dataset.css`
- `hdx_theme/v2-dataset-page-scripts` — dataset page: adds `v2/pages/dataset.js` (section accordion) + `v2/data-use-survey-drawer.js` (data use survey drawer)
- `hdx_theme/v2-quick-edit-scripts` — dataset page: adds `v2/components/quick-edit.js`
- `hdx_theme/v2-shape-view-scripts` — dataset page, loaded only when the dataset has shapes: preloads `charting-scripts`, adds `v2/pages/shape-view.js`
- `hdx_theme/v2-resource-page-styles` — resource page: adds `v2/pages/resource.css`
- `hdx_theme/v2-resource-page-scripts` — resource page: preloads `v2-datatable-scripts`, adds `v2/pages/resource.js` (Data dictionary AJAX
  load via `datastore_info`; loaded only when `res.datastore_active`)
- `hdx_theme/v2-datatable-scripts` — DataTables lib (`vendor/datatables-2.3.8/dataTables.min.js`); preloaded by `v2-resource-page-scripts`
- `hdx_theme/v2-home-page-styles` — homepage: adds `v2/bar-chart.css` + `v2/pages/home.css`
- `hdx_theme/v2-home-page-scripts` — homepage: adds `v2/highlights-carousel.js`, `v2/bar-chart.js`; requires `v2-carousel-scripts` loaded first in the template
- `hdx_theme/v2-locations-list-page-styles` — All Locations page: adds Leaflet CSS, `browse_/browse.css` + `v2/pages/locations-list.css`
- `hdx_theme/v2-locations-list-page-scripts` — All Locations page: adds Leaflet, `map_base.js`, `browse_/*` + `v2/pages/locations-list.js` (HRP filter + A-Z/Z-A sort)
- `hdx_theme/v2-location-page-styles` / `-scripts` — Location page: adds `v2/pages/location.css` / `v2/pages/location.js`
- `hdx_theme/v2-crisis-page-styles` / `-scripts` — Crisis/event pages: adds `v2/pages/crisis.css` / `v2/pages/crisis.js`
- `hdx_theme/v2-crisis-pages-page-styles` — Crisis Pages page: adds `v2/pages/crisis-pages.css`
- `hdx_theme/v2-user-dashboard-page-styles` — User dashboard/settings pages (via `v2/user-dashboard-base.html`): adds `v2/pages/user-dashboard.css`; loaded after `v2-search-page-styles`, whose sidebar/content classes the base reuses
- `hdx_theme/v2-org-list-page-styles` — All Organisations page: adds `v2/pages/org-list.css` (org-list-card styles come from the preloaded `v2-components-styles` bundle)
- `hdx_theme/v2-org-list-page-scripts` — All Organisations page: adds `v2/url-nav.js` + `v2/pages/org-list.js`
- `hdx_theme/v2-org-page-styles` — Organization page (all tabs, 056–059): adds `v2/pages/org.css` (hero band, activity/stats sections, members layout incl. the invite tags widget)
- `hdx_theme/v2-org-members-page-scripts` — Organization page Members tab: adds `v2/url-nav.js` + `v2/pages/org-members.js` (change-role/approve dropdown wiring, drawers + invisible reCAPTCHA, invite tags-autocomplete)
- `hdx_theme/v2-chart-scripts` — Chart.js lib bundle (`chartjs/*` + `v2/charts.js`); loaded by the org page Stats tab and the dataset page
- `hdx_theme/v2-message-form-page-styles` — Contact Contributor + Request Data Access pages: adds `v2/pages/message-form.css`
- `hdx_theme/v2-contact-contributor-page-scripts` — Contact Contributor page: adds `v2/pages/contact-contributor.js`
- `hdx_theme/v2-request-access-page-styles` / `-scripts` — Request Data Access page: adds `v2/pages/request-access.css` / `v2/pages/request-access.js`
- `hdx_theme/v2-signup-page-styles` — Signup flow pages: adds `v2/pages/signup.css`; loaded on all 5 signup pages
- `hdx_theme/v2-verify-email-page-scripts` — Signup verify-email page: adds `v2/pages/verify-email.js`
- `hdx_theme/v2-hapi-landing-page-styles` — HAPI landing page: adds `v2/pages/hapi-landing.css`
- `hdx_theme/v2-carousel-scripts` — shared carousel lib: `vendor/hammer/hammer.js` + `v2/carousel.js`; loaded explicitly by each page template that uses the carousel (no preload)
- `hdx_theme/v2-signals-carousel-styles` — Signals carousel: adds `v2/signals-carousel.css`; loaded by the homepage and the Signals landing page
- `hdx_theme/v2-signals-landing-page-styles` — Signals landing page: adds `v2/pages/signals-landing.css`
- `hdx_theme/v2-signals-landing-page-scripts` — Signals landing page: adds `v2/signals-carousel.js` + `landing_pages/hdx_signals.js`; requires `v2-carousel-scripts` loaded first in the template
- `hdx_theme/v2-signup-scripts` — Signup scripts: `onboarding/came-from-input.js` (vanilla JS rewrite in place) + `onboarding/confirm-page-leave.js` (vanilla JS rewrite in place); loaded on user-info and change-email pages
- `hdx_theme/v2-form-validator-scripts` — Form validation: vanilla JS validator (`v2/form-validator.js`); activated by `data-hdx-v2-form-validator` on `<form>` elements; loaded by notification platform templates and signup form pages (user-info, change-email)
- `hdx_theme/v2-error-page-styles` — 404/403/Server Error page: adds `v2/pages/error.css`; no scripts bundle (page has no interactive behavior)
- `hdx_theme/v2-auth-page-styles` — Login, forgot-password + perform-reset pages: adds `v2/pages/auth.css` (shared card/navbar-shell styling, loaded by all three templates)
- `hdx_theme/v2-login-page-scripts` — Login page: adds `v2/pages/login.js` (lockout/MFA pre-checks, required-field gating, remember-me cookie prefill)
- `hdx_theme/v2-forgot-password-page-scripts` — Forgot-password page: adds `v2/pages/forgot-password.js` (AJAX submit, invisible reCAPTCHA, recover/confirmation card swap)
- `hdx_theme/v2-perform-reset-page-scripts` — Perform-reset (set new password) page: adds `v2/pages/perform-reset.js`
- `hdx_theme/v2-archived-dataviz-page-styles` — Archived Dataviz page: adds `v2/pages/archived-dataviz.css`; no scripts bundle (page has no interactive behavior)
- `hdx_theme/v2-dataviz-gallery-page-styles` / `-scripts` — Dataviz Gallery page: adds `v2/pages/dataviz-gallery.css` / `v2/url-nav.js`

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

### Phase 3: Page Migrations ✅ (Complete for this cycle)
- [x] Signup page
- [x] Landing page — HAPI (`/hapi/`)
- [x] Landing page — Signals (`/signals/`)
- [x] Contact contributor page
- [x] Homepage
- [x] Dataset list (light + desktop — unified in v2 search template)
- [x] Dataset page
- [x] Resource page
- [x] All Locations page
- [x] All Organisations page
- [x] Organization page (Datasets / Activity / Stats / Members tabs — 056–059; HDX Connect tab postponed)
- [x] Archived Dataviz page
- [x] Dataviz Gallery page

Deferred to next cycle: Find/join org page, org request pages, create/edit dataset page, org page HDX Connect tab, Signals Mailchimp form's Bootstrap-to-v2 CSS cleanup (task 070 B4), `resource_view.html` error-div class cleanup (task 047 Decision 10).

### Phase 4: Cleanup — Next cycle
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
