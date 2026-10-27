# 083 — Global Nav: "On" State (v2)

**Scope:** the v2 header's main navigation items Data, Locations, Organisations and Products. The item
for the section the user is in shows an "On" state that looks the same as hover, on the section's own
page and on every page under it. The state is exposed with `aria-current`. The MD/SM offcanvas menu
gets `aria-current` only.

**Excluded:** the top-bar, the user menu, the notifications panel and the v1 header. No new visual
design for the offcanvas.

**Figma source:** none. The navbar exports (`navbar.html`, `navbar-open.html`) have no On variant. The
On look is the existing hover.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`.

---

## 1. Audit Findings

### 1.1 Header and component
- **Header:** `THEME/templates/v2/header.html` renders Data, Locations and Organisations with
  `v2/components/nav-item.html` and never passes `status`. Products is a nav-item too: an
  `<a href="#">` with `aria-expanded` that opens `#hdx-v2-panel-products` (a disclosure, not a link to
  a page). Its panel lists `quick_links`.
- **Offcanvas (MD/SM):** bespoke `hdx-v2-offcanvas__nav-item` links (Home, Data, Locations,
  Organisations) plus an expandable Products `<button>` with sub-links. Hover makes no visible change.
- **nav-item:** `status='active'` adds `c-nav-item--active` and always outputs `aria-current="page"`.
  `active-dropdown` has no navbar styling (base royalblue underline, chevron-up), so it does not fit.
- **Styling already exists:** `navbar.less` styles `.hdx-v2-navbar__nav .c-nav-item.c-nav-item--active`
  with white text and a 2px white underline, the same as its `:hover` rule. It overrides the base
  4px royalblue `--active` rule. The two rules can share one selector list.
- **Callers of the header:** `v2/page.html` (`header_core`) and the `minimal=True` auth pages, which
  have no nav items. The error template empties the header block. v1 pages render the v1 header, which
  has no active state.

### 1.2 Detecting the current page
- **CKAN core:** `h.build_nav_main()` and `h.build_nav_icon()` mark an item active through
  `_link_active()`, which compares the blueprint from `toolkit.get_endpoint()` with a
  `highlight_controllers` list. They output `<li class="active"><a>` markup, so they can't drive
  `c-nav-item`. There is no public `h.get_endpoint` or `h.is_url_for`. No v2 template uses the core nav
  helpers.
- **v2 precedents:** both are template-declared: `nav_active` in `v2/dashboard-base.html` and
  `active_tab` in `v2/org-hero.html`. `c-anchor-links` already uses `aria-current="true"`.
- **Jinja context:** Flask's Jinja globals expose `request` inside `{% snippet %}`; the header already
  branches on `request.path`. CKAN strips the locale prefix from `PATH_INFO` before routing, so
  `request.path` never carries it.
- **Endpoints differ from the header links:** `/dataset` resolves to `hdx_dataset.search`, `/group` to
  `hdx_group.index`, `/organization` to `hdx_org.index`. `request.endpoint == 'dataset.search'` is never
  true on HDX.

### 1.3 Pages per section
Measured against the live URL map; "v2" means the template extends a v2 base.

| Section | v2 pages | Endpoints |
|---|---|---|
| Data | search, `/search`, dataset page (and its custom/HXL/shape variants), contact contributor, request access, resource page, resource history | `hdx_dataset.*`, `hdx_search.search`, `dataset_resource.read`, `activity.resource_history` |
| Locations | locations list, location page | `hdx_group.index`, `hdx_group.read` |
| Organisations | list, create, org page tabs (datasets, activity, stats, members, requested data), edit, join flow (find, confirm, reason, completed), request flow (new, completed) | `hdx_org.*`, `hdx_members.members`, `requestdata_organization_requests.requested_data`, core `organization.edit`, `hdx_org_join.*`, `hdx_org_request.*` |
| Products | dataviz gallery, Signals, crisis pages list, crisis/event pages, dashboards | `hdx_dataviz_gallery.index`, `hdx_landing_pages.signals`, `hdx_crisis_pages.show`, `hdx_event.read_event`, `hdx_dashboard.read_dashboard` |

- **Breadcrumbs:** Locations, Organisations and Products pages start with their section crumb. This
  includes the org join/request flows and every `pages/read_page.html` page (crisis and dashboards).
  Dataset and resource pages start with the **organisation** crumb.
- **No collisions:** user pages live under `/user` and `/dashboard`; `/dataset-changes` is v1.
- **Products list:** `h.hdx_get_quick_links_list()` reads sysadmin-edited DB settings, fetched once
  in `v2/page.html`. The header drops crisis items (`exclude_crisis=True`). Items are mostly
  relative URLs; some leave the app (`/hapi` redirects to the docs, and some paths are not CKAN
  routes).

---

## 2. Options Considered

| | A Path prefixes | B Endpoint/blueprint sets | C Template variable |
|---|---|---|---|
| Rules | 10 prefixes | 15 blueprints + 1 endpoint | a `main_nav_active` set in 26 templates |
| New sub-page in a section | automatic | automatic if same blueprint | must set the variable |
| Fails silently on | a public top-level URL change | an internal blueprint rename/split | a forgotten variable |
| Own page vs sub-page | same comparison | needs list endpoints | still needs a path comparison |
| Precedent | the header's `request.path` check | core `build_nav_main` | Jinja docs recipe; `nav_active`, `active_tab` |

- In B, `activity` serves three sections, so it needs full endpoint names, and Organisations spans
  six blueprints.
- **Rejected:** deriving the section from the breadcrumb (dataset crumbs start with the org, and the
  header renders before the crumb block) and client-side JS (no state until the script runs; the rules
  would be duplicated).

---

## 3. Behavior and Logic

### 3.1 Section map (D1, D3)

| Section | URL prefixes (the first is the item's own URL; Products has none) |
|---|---|
| `data` | `/dataset`, `/search` |
| `locations` | `/group` |
| `organisations` | `/organization`, `/org` |
| `products` | `/dataviz-gallery`, `/signals`, `/crisis-pages`, `/event`, `/dashboards` |
| `home` | exactly `/` |

- A path matches a prefix when it equals it or continues with `/`, after stripping a trailing `/`.
  `/dataset-changes` does not match `/dataset`.
- The first matching section wins. Any other path has no section, and no item is On.

### 3.2 Helper (D2, D7)
`h.hdx_v2_main_nav_state(quick_links)` returns `{'section', 'aria_current', 'product_url'}`.
- **`aria_current`:**
  - `'page'` on the section's own URL, and on `/`.
  - `'true'` on other pages of the section, which is every page for Products.
- **`product_url`:** the first quick link whose path equals the current path, comparing paths with
  the fragment, the query and a trailing `/` stripped. Links to another host or with no path (`#`) are
  skipped.
- **Failure:** any error logs a warning and returns an empty state, so no item is On. The page never
  fails because of it.

### 3.3 Header (D4, D6)
- **Navbar:**
  - Data / Locations / Organisations / Products trigger: `status='active'` and `aria_current` from the
    helper.
  - The Products panel link equal to `product_url` gets `aria-current="page"`.
- **Offcanvas:** no visual change.
  - The Home link gets `aria-current="page"` on `/`.
  - The section's link, or the expandable Products `<button>`, gets the helper's `aria-current`.
  - The Products sub-link equal to `product_url` gets `"page"`.
- **Minimal header:** has no nav items and does not call the helper.
- Analytics attributes and links are unchanged.

### 3.4 nav-item (D5)
New optional `aria_current` param: the `aria-current` value when `status='active'` (`'page'` or
`'true'`, default `'page'`). Existing callers don't change.

### Risks & Edge Cases

| Case | Handling |
|---|---|
| `/dataset?q=…` | Own page: Data On, `aria-current="page"` |
| Dataset or resource page | Data On, `"true"` (D3) |
| `/search` | Data On, `"true"` |
| Org edit, join or request flow | Organisations On, `"true"` |
| Crisis/event page (not in the Products panel) | Products On, `"true"`; no panel link is current |
| A Products panel page (e.g. Signals) | Products On, `"true"`; its panel link `"page"` |
| Home, user dashboard, user pages, signup | No item On |
| 404/500 | The error template has no header |

---

## 4. Responsive Behavior & Accessibility

- **XL:** the On state is the hover look (white text, 2px white underline).
- **MD/SM:** the offcanvas exposes the same state through `aria-current` only.
- `aria-current="page"` marks only a link to the page being shown. `"true"` marks the current section
  on its other pages. This includes the Products disclosure, which has no page of its own.
- No colour-only cue: the underline carries the state at XL.

---

## 5. Decisions Taken

| # | Decision |
|---|---|
| D1 Detection | URL path prefixes, segment-aware (option A). `/hapi` is left out: it only redirects. |
| D2 Logic home | One Python helper in `THEME/helpers/helpers.py`; no page override param. |
| D3 Membership | Products = every page with a "Products" crumb. Dataset and resource pages = Data. |
| D4 aria-current | `"page"` on the item's own URL, `"true"` on its other pages (including `/search` and every Products page, on the trigger). Matching Products panel link `"page"`. |
| D5 nav-item | New optional `aria_current` param (`'page'` default, or `'true'`). |
| D6 Offcanvas | `aria-current` only, including Home on `/`, the Products `<button>` and its sub-links; no visual change. |
| D7 Helper API | `h.hdx_v2_main_nav_state(quick_links)` → `{section, aria_current, product_url}`, called once per header. |
| D8 Tests | Render check only; no committed tests. |

---

## 6. Files Affected

| File | Change |
|---|---|
| `THEME/helpers/constants.py` | `V2_MAIN_NAV_SECTIONS` in `CONSTANTS` (D1, D3) |
| `THEME/helpers/helpers.py` | `hdx_v2_main_nav_state()` (D2, D7) |
| `THEME/plugin.py` | Register `hdx_v2_main_nav_state` |
| `THEME/templates/v2/components/nav-item.html` | `aria_current` param (D5) |
| `THEME/templates/v2/header.html` | Navbar, Products panel and offcanvas states (D4, D6) |
| `THEME/hdx-styles/src/common/less/v2/navbar.less` | One selector list for the nav item `:hover` and `--active` rules |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | Extend the `aria-current="true"` row to the current nav section |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Navbar On state |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 083 status |
