# 086 — Sysadmin Dashboard: HDX Connect Dashboard (v2 Migration)

**Scope:** `/ckan-admin/requests_data` (`requestdata_ckanadmin.requests_data`), moved onto the 084 sysadmin shell.
Also in scope:
- per-item permission gating of the sysadmin menu (resolves 084 D3), with `v2/header.html` computing the user menu
  sections once per page;
- a `groups` param on the shared `v2/hdx-connect-sections.html`, so one page can render one New / Open /
  Archived set per organisation;
- a `title_tag` param on `c-request-card`;
- a `caller()` actions slot on `v2/list-header.html`;
- an organisation filter handler in `hdx-connect.js` and `filter_by_organizations` in `search.js` `FILTER_PARAMS`.

**Excluded:**
- Any change to the `ckanext-requestdata` repo (view, actions, auth, model, download endpoint).
- The other sysadmin pages (Homepage Highlights, Custom Pages, Products Menu, Package Links) and the Email /
  Config pages, which stay on v1 `admin/base.html`.
- A maintainer filter, an archive sort, pagination, new analytics events and new tests.

**Figma source:** `xl-sysadmin-hdx-connect-dashboard.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`.

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `EXT` = `src/ckanext-requestdata/ckanext/requestdata` (separate repo `OCHA-DAP/ckanext-requestdata`, pinned tag `3.0.42`)

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `requestdata_ckanadmin.requests_data` (`/ckan-admin/requests_data`). Reached from the sysadmin menu, the header user menu and v1's admin tabs |
| Objective | v2 page on `v2/sysadmin-base.html` (`nav_active='hdx_connect_dashboard'`, `page_label=_('HDX Connect Dashboard')`) with Figma's layout, keeping the endpoints, payloads, auth, the `filter_by_organizations` URL and reload on success |
| Strategy | **Direct replacement** of the HDX override `THEME/templates/admin/all_requests_data.html` (no `?v2` gate, as 074 / 080 / 084 / 085). The EXT view is untouched |
| Shared work | The 074 / 080 body snippet renders one set per organisation; the organisation filter follows the 080 Maintainer-filter pattern |

---

## 2. Repository Audit Findings

### 2.1 Routes and auth

| Endpoint | URL | Notes |
|---|---|---|
| `requestdata_ckanadmin.requests_data` | `/ckan-admin/requests_data` (GET) | EXT `views/admin.py` `requests_data` |
| `requestdata_ckanadmin.download_requests_data` | `/ckan-admin/requests_data/download?format=csv\|json` (GET) | Every request as an attachment (`data_requests.csv` / `.json`). Ignores the org filter. Any other `format` → 404 |
| `hdx_requestdata_user.handle_new_request_action_reply` / `_reject` | `/user/my_requested_data/<username>/reply`, `.../reject` (POST) | Reply / Decline, as 074 / 080 |
| `requestdata.handle_open_request_action_shared` | `/user/my_requested_data/<username>/shared` (POST) | Yes / No, as 074 / 080 |

- **Page auth:** the view calls `requestdata_request_list_for_sysadmin`, whose action checks HDX
  `hdx_request_data_admin_list` (`THEME/helpers/auth.py`): `Permissions(user).has_permission(
  PERMISSION_VIEW_REQUEST_DATA)` ("View Request Data Dashboard", granted on the 076 User Permission page).
  Sysadmins pass through the CKAN bypass. Everyone else gets 403 "Not authorized to see this page.".
- **Action auth:** EXT `logic/auth.py` `request_patch` → `_user_has_access_to_request`: the dataset creator, its
  maintainer or an org admin; sysadmins bypass. A permission holder acting on another org's request gets a 403.
- **2FA:** `THEME/plugin.py` `_before_request` matches `protected_urls` by exact rule; `/ckan-admin/requests_data`
  is not listed, so no redirect (unchanged).

### 2.2 Data passed to the template

| Variable | Shape |
|---|---|
| `organizations` | Per-org dicts sorted by `title`: `title`, `name`, `id`, `requests_new`, `requests_open`, `requests_archive`, `maintainers` (always `[]`), `counters` (always `{}`), `packages`, `requests` (count, §2.3) |
| `organizations_for_filters` | Namedtuples `(id, org)` for **every** org with requests (built before the filter), sorted by `org['requests']` descending |
| `total_requests` | `len()` of every request, including those whose dataset `package_search` doesn't return; not affected by the filter |

- **Requests:** EXT `request_list_for_sysadmin` returns `as_dict()` rows ordered `created_at desc`, with the raw
  `extras` JSON string (what `v2/hdx-connect-request.html` parses) plus flattened copies. The view adds `title`
  (dataset title), `name` (org name) and `maintainers = [{id, name, username, fullname}]` or `[]`.
- **Archive groups:** one per dataset: `package_id`, `title`, `maintainers`, `requests_archived` and the lifetime
  counters `requests`, `replied`, `declined`, `shared` (EXT `fetch_counters_for_packages_as_map`). Their order is
  `package_search`'s.
- **Filter:** `filter_by_organizations` is read with `request.args.get()` (first value only) and split on `,`;
  unknown names leave no organisation. There is no `filter_by_maintainers` and no `order_by` handling (the
  per-org sort code is commented out).

### 2.3 Data quirks (EXT view, unchanged)

| Quirk | Effect |
|---|---|
| For every dataset after an org's first one, an archive group is appended even when it has no archived requests | Empty groups: `requests_archived = []`, `requests = 0`, `shared = None`, no `replied` / `declined` |
| `org['requests']` = sum of the groups' lifetime `requests` counters + new + open | The lifetime counter grows on every new request (`flag='request'`), so New / Open requests on datasets with archived ones are counted twice |
| Maintainers are looked up by user id only, and `fullname` has no username fallback | Missing line when the dataset's `maintainer` isn't an id; empty label when the user has no full name |
| `archived_counters_map[package_id]` with no counters row | KeyError → 500 |
| `package_search` with `rows: 2000` | Requests on datasets beyond the cap, or not returned (deleted / private), are dropped from the org lists but still in `total_requests` |

### 2.4 v1 rendering

| Part | v1 |
|---|---|
| Chrome | v1 `page.html` + `admin/base.html`: "Sysadmin Dashboard" heading, BS5 tab bar, `col-3` / `col-9` |
| `<title>` | "Administration" |
| Header | "Download" BS dropdown (CSV / JSON), shown when `organizations` is non-empty; "Data Requests [`total_requests`]" |
| Filter | EXT `filter_requests.html` "Filter by: Organization" BS checklist, "{title} ({org.requests})", Apply / Reset; shown when `organizations` is non-empty |
| Per org | `requests_header.html` `type='admin'`: title truncated to 27 characters + `[org.requests]`; no maintainer filter, counters or sort |
| Sections | EXT `section_base.html`: "New [n]", "Open [n]", "Archive [n]" (groups, empty ones included), "No requests found." |
| Items | HDX `section_item_*.html` with `template_type='admin'`: "Maintained by {fullname}" (or "Not found") on New items, Reply / Decline BS modals, Yes / No AJAX — for every viewer |

### 2.5 Assets

`requestdata/main-styles`, `hdx_theme/requestdata-styles`, `hdx_theme/dataset-search-styles`,
`hdx_theme/requestdata-remove-class-scripts`, plus the per-item v1 bundles listed in 080 §2.6 and Bootstrap JS.

### 2.6 Analytics and tests

- **Analytics:** nothing page-specific. The Mixpanel page view sends `pageTitle` "Administration".
- **Tests:** no HDX test loads this page.

### 2.7 Menus and permission holders

- `h.hdx_get_sysadmin_nav_sections()` (084 D2) feeds the sysadmin base and the header user menu
  (`h.hdx_get_user_menu_sections()`); it returns `[]` for non-sysadmins (084 D3).
- `h.hdx_get_user_menu_sections()` runs twice per v2 page: the desktop menu (`v2/navbar-user-menu.html`) and the
  offcanvas (`v2/header.html`).
- v1's admin tabs and v1 `header-global.html` showed permission holders the items they can open.

| Item | Page access check |
|---|---|
| All Sysadmins (`admin.index`) | `sysadmin` |
| All Users (`user.index`) | Core; the v1 tab was sysadmin-only |
| Homepage Highlights (`hdx_carousel.show`) | `hdx_carousel_update` |
| HDX Connect Dashboard | `hdx_request_data_admin_list` |
| Custom Pages (`hdx_custom_pages.index`) | `admin_page_list` |
| Products Menu (`hdx_quick_links.show`), Package Links (`hdx_package_links.show`) | `hdx_quick_links_update` |

Each `Permissions` check costs a user lookup and a user-extra read. v1's header ran up to 4 checks per page for a
regular user and up to 8 for a permission holder.

### 2.8 Reusable v2 pieces

| Piece | Fit |
|---|---|
| `v2/sysadmin-base.html` → `v2/dashboard-base.html` | Menu, breadcrumb, `<title>`, sticky XL-only right column via `{% block tertiary_content %}` (073) |
| `v2/hdx-connect-sections.html` (080) | Header, New / Open grouping per dataset, Archived grid, empty states, shared-error `c-alert`, drawers — for **one** set of requests, with a single wrapper, alert and drawer pair |
| `v2/hdx-connect-request.html`, `v2/hdx-connect-drawers.html`, `hdx-connect.js` | Consume the EXT `as_dict()` rows unchanged; Yes / No URL from `data-hdx-connect-shared-url` |
| `c-request-card` | `<h3>` title (hard-coded), `maintainer_label` / `maintainer_href` |
| 080 Maintainer filter | Checklist `c-dropdown` in `#search-page-filters-form`, handler in `hdx-connect.js` writing one param through `window.hdxSetNavParam`, `FILTER_PARAMS` entry for "Clear filters" |
| `v2/list-header.html` | Title + count, subtitle, MD/SM Filter button; no slot for other controls |
| `v2/filter-overlay.html` | `show_controls=False` (080) |
| `c-dropdown` navigate | Items with `data-nav-value` URLs; `dropdown.js` navigates on click / Enter |

### 2.9 Default Search filters (My Datasets)

- `v2/search-filters.html` hard-codes its filters (Location, Organisation, Format, Topics, Advanced); each is a
  checklist `c-dropdown` with counts, a MiniSearch box above 8 items and "Clear selection".
- `search.js` writes **repeated** params (`?f=a&f=b`) on checkbox change; the pills row and the overlay clear them.
- The EXT view reads one comma-joined value, so the default writer would apply only the first organisation.

---

## 3. Figma Design Analysis (XL)

**Shell:** as 084: left "Sysadmin" menu (14.063rem), "HDX Connect Dashboard" active; breadcrumb
Home / Sysadmin / HDX Connect Dashboard.

**Header** (padding 40 / 48):
- "HDX Connect Dashboard" (Merriweather 24px bold) + count "2801" (Roboto 16px, neutral-8), 8px apart.
- 6px below: "Review and manage HDX Connect requests across all organisations" (14px, neutral-85).
- Right, top-aligned, 12px from the text: a 10.313rem "Download" select (14px medium, padding 8 / 8 / 8 / 10,
  1px neutral-2 border, 2px radius, drop shadow, chevron-down).

**Organisation blocks** (one per org):
- 1px neutral-1 top border; padding 32 / 48 / 48 / 40; 24px between the header row and the sections.
- Header row: org name (Merriweather 24px bold) + count (16px), 8px apart; "Sort by" + "Most Recent" select on the
  right, 32px away.
- Sections "New 3", "Open 1", "Archive 3": 18px bold heading + count, 16px to the list, 24px between cards.
- Cards, request rows, chips, footer, Yes / No prompt and Archive grid: identical to 074 §3; "Maintained by
  **username**" under New and Open card titles (as 080 §3.1).

**Right column** (14.063rem, padding 40 / 32 / 0, 28px gap):
- "Filter by" (16px semibold).
- "Organisation" (14px) + select "3iS"; "Maintainer" (14px) + select "All maintainers" (14px medium, padding
  8 / 8 / 8 / 10, border, shadow), 8px label gap.

**Hidden in the export (`display:none`):** a search field; the header "Results per page" and "Sort by"; the
per-org "Results per page"; a per-org chevron; a "Closed 12" section.

**Artefacts:** "i3S" heading vs "3iS" filter value; counts that don't add up (13 vs 3 + 1 + 3); repeated demo rows.

**Tokens:** every value maps to an existing token (074 §3.5); `#ebeff0` = `--hdx-neutral-1`.

---

## 4. Current vs Target Comparison Matrix

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 admin tabs, `col-3` / `col-9` | `v2/sysadmin-base.html`, three columns at XL | Derived |
| Menu for permission holders | v1 tabs / header items they can open | Same items, gated per check | D1 |
| Breadcrumb / `<title>` | None / "Administration" | Home / Sysadmin / HDX Connect Dashboard / "HDX Connect Dashboard \| Sysadmin" | Derived |
| Heading | "Data Requests [N]" | `<h1>` "HDX Connect Dashboard" + count + subtitle | D9, derived |
| Download | BS dropdown above the heading | `c-dropdown` navigate in the header row | D4 |
| Filter | BS checklist, Apply / Reset | XL right column; MD/SM Filter button + overlay; instant apply; "Clear selection" | D5, D6 |
| Org header | Truncated title + v1 count | `<h2>` full name + count | D9, D13 |
| Sections | New / Open / Archive (empty groups included) | New / Open / Archived; empty groups dropped | D10, derived |
| Maintainer line | New items; "Not found" | New and Open cards; username fallback; none when unresolved | Derived |
| Request rows, actions, Archive grid | BS markup, modals | 074 components and drawers; actions for every viewer | D2, D14 |
| Maintainer filter, archive sort | None | None | D7, D8 |
| Pagination | None | None | D11 |
| Assets | v1 requestdata bundles, Bootstrap JS | `v2-hdx-connect-page-styles`, `v2-search-page-scripts`, `v2-hdx-connect-scripts` | Derived |

---

## 5. Component & System Reuse Strategy

### 5.1 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, menu, crumb, `<title>` | `v2/sysadmin-base.html` | Reuse | Derived |
| Menu gating | `h.hdx_get_sysadmin_nav_sections()` per-item checks | Extend | D1 |
| Body | `v2/hdx-connect-sections.html` with **new `groups`** | Extend | D2 |
| Org header | `v2/list-header.html` (`title_tag='h2'`, `title_size='dashboard'`) inside the snippet | Reuse | D2, D13 |
| Dataset title level | `c-request-card` **new `title_tag`** | Extend | D3 |
| Download | `v2/list-header.html` **new `caller()` slot** + navigate `c-dropdown` | Extend + reuse | D4 |
| Filter column | `tertiary_content` > `#search-page-filters-form` > `aside.hdx-v2-search-filters` + checklist `c-dropdown` | Reuse | D5 |
| Filter JS | Organisation handler in `hdx-connect.js`; `FILTER_PARAMS` in `search.js` | Extend | D5 |
| MD/SM | `v2/list-header.html` `show_filters` + `v2/filter-overlay.html` `show_controls=False` | Reuse | D6 |
| Rows, drawers, actions | `v2/hdx-connect-request.html`, `v2/hdx-connect-drawers.html`, `hdx-connect.js` | Reuse | D2 |
| Group separators | `.hdx-v2-hdx-connect__group` in `LESS/pages/hdx-connect.less` | New class | Derived |
| Not reused | `v2/search-filters.html` + `search.js` writer (repeated params, §2.9); the pills row (D12) | | D5, D12 |

### 5.2 Shared changes

| File | Change |
|---|---|
| `v2/hdx-connect-sections.html` | **`groups`** `{list}`: `[{title, requests_new, requests_open, requests_archive}]`; when set, `requests_new` / `requests_open` / `requests_archive` are not required. Each group renders in `<section class="hdx-v2-hdx-connect__group">`: a list-header (`count` = the group's new + open + archived requests, `title_tag='h2'`, `title_size='dashboard'`, `show_controls=False`, `show_filters=False`), then its New / Open / Archived sections with `<h3>` headings, `title_tag='h4'` cards and no Archived sort (D19). The page header count is the sum over groups; an empty `groups` renders one "No requests found." under the page header. Without `groups` the output is unchanged. Maintainer label: `fullname or username`. A `caller()` is forwarded to the page list-header through an alias (`{% set header_actions = caller %}`; a bare `caller` inside a call body is the body's own) |
| `v2/list-header.html` | Optional `caller()`: rendered in `<div class="hdx-v2-list-header__actions">` on the title row, at every width, after the controls and the Filter button; omitted when its output is blank. Spaced by a `--hdx-space-3` `column-gap` on the row (every list header, `LESS/pages/search.less`) |
| `v2/components/request-card.html` | `title_tag` `{string}` default `'h3'` |
| `fanstatic/v2/pages/hdx-connect.js` | Delegated `change` on `[data-hdx-connect-organization]`: the checked values inside the closest `[data-hdx-connect-organization-filter]` → `window.hdxSetNavParam('filter_by_organizations', values.join(','))`, or `null` when none |
| `fanstatic/v2/pages/search.js` | `FILTER_PARAMS` += `'filter_by_organizations'` |
| `THEME/helpers/helpers.py` | `hdx_get_sysadmin_nav_sections()` per-item gating (D1) |
| `v2/header.html`, `v2/navbar-user-menu.html` | `h.hdx_get_user_menu_sections()` called once in the header; the desktop menu reads it from a new `sections` param (D20) |
| `LESS/pages/hdx-connect.less` | `&__group` rules (§6.4) |

---

## 6. Functional Requirements

### 6.1 Backend

No change in `ckanext-requestdata`. The template uses `organizations` and `organizations_for_filters`;
`total_requests` is no longer displayed (D9).

### 6.2 Page template

Full replacement of `THEME/templates/admin/all_requests_data.html`, extending `v2/sysadmin-base.html`:

| Part | Content |
|---|---|
| Top-level sets | `nav_active='hdx_connect_dashboard'`, `page_label=_('HDX Connect Dashboard')`; the parsed filter (§6.3); `groups` from `organizations`, each with `requests_archive = org.requests_archive \| selectattr('requests_archived') \| list` |
| `styles` | `v2-hdx-connect-page-styles` |
| `scripts` | `v2-search-page-scripts`, then `v2-hdx-connect-scripts` |
| `tertiary_content` | Only when `organizations_for_filters` is non-empty: the filter column (§6.3) |
| `primary` | The shared snippet with `groups`, `list_title=page_label`, `list_subtitle=_('Review and manage HDX Connect requests across all organisations')`, `title_tag='h1'`, `show_filters`, `total_selected`, `show_maintainer=True`; its `caller()` body holds the Download dropdown when `organizations_for_filters` is non-empty. Then, with the filter, `v2/filter-overlay.html` with `total_selected` and `show_controls=False` |

**Download:** `c-dropdown` `size='m'`, `placeholder=_('Download')`, `navigate=True`,
`panel_id='hdx-connect-download-panel'`, items "CSV" / "JSON" with `value` =
`h.url_for('requestdata_ckanadmin.download_requests_data')` + `?format=csv` / `?format=json`.

### 6.3 Organisation filter

- **Parsing** (template): `request.args.get('filter_by_organizations')` split on `,`, empty entries dropped;
  `total_selected` = the number left, so an unknown name still shows the filtered state and "Clear selection".
- **Options:** one per `organizations_for_filters` entry: `value` = `org.name`, `label` = `org.title`, `count` =
  "({n})" with n = the D9 per-org count, `checked` / `active` when selected,
  `attrs={'data-hdx-connect-organization': ''}`. Ordered by n descending, then title (D15).
- **Dropdown:** label "Organisation"; placeholder "All organisations"; trigger text = the selected titles joined by
  ", "; `state='filter'` when anything is selected; `panel_id='hdx-filter-panel-organizations'`;
  `attrs={'data-hdx-connect-organization-filter': ''}`; `has_clear` when selected,
  `clear_facet='filter_by_organizations'`. No `data-filter-checkbox`, no `name`, no search box.
- **Layout:** `<form id="search-page-filters-form" autocomplete="off"><aside class="hdx-v2-search-filters">`,
  heading `hdx-v2-search-filters__heading` "Filter by", one `hdx-v2-search-filters__item`.
- **Apply:** instant, through `hdx-connect.js` (§5.2). "Clear selection" and the overlay's "Clear filters" delete
  the param through `search.js`.

### 6.4 Group styles

`.hdx-v2-hdx-connect__group` in `LESS/pages/hdx-connect.less`: a column with the 074 section gap, a 1px
`--hdx-neutral-1` top border and `--hdx-space-8` padding-top, the first group included (D18); consecutive groups
`--hdx-space-12` apart.

### 6.5 Copy

| Element | Copy |
|---|---|
| Heading, crumb, menu item, `<title>` | "HDX Connect Dashboard" (`<title>` "HDX Connect Dashboard \| Sysadmin") |
| Subtitle | "Review and manage HDX Connect requests across all organisations" |
| Download | "Download"; items "CSV", "JSON" |
| Filter | "Filter by"; "Organisation" / "All organisations"; option "{title}" + "({n})" |
| Sections | "New", "Open", "Archived" |
| Empty | "No requests found." |
| Everything else | As 074 §6.3 / 080 §6.5 |

All strings go through `_()`.

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Sysadmin / permission-holder access, 403 for others | Unchanged (EXT view, HDX auth) |
| Reply / Decline / Yes / No endpoints, payloads, reload on success | 074 drawers and `hdx-connect.js` |
| Actions on every request for every viewer | Unchanged (D14) |
| `filter_by_organizations=a,b` | Same string; bookmarked URLs parse |
| CSV / JSON download URLs | Unchanged |
| Org order (title), New / Open order (`created_at desc`), archive group order | Unchanged |
| No pagination | Unchanged (D11) |
| "No requests found." | Same copy |
| Mixpanel page view | Still fires; `pageTitle` "HDX Connect Dashboard \| Sysadmin" |
| Header link for permission holders (v1 header) | Restored in the v2 header user menu (D1) |

**Intentional differences:** counts (D9), "Archived" (D10), instant filter apply with "Clear selection", the filter
and Download staying visible when the filter empties the page, the maintainer line on Open cards with a username
fallback, full org names, empty archive groups dropped.

---

## 8. Responsive & Accessibility Considerations

### 8.1 Breakpoints (MD/SM inferred)

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Menu | Sticky left column (25%) | Header user menu only | Same as MD |
| Filter | Sticky right column (25%) | Filter (n) button → full-screen overlay | Same as MD |
| Header row | Title + count; Download on the right | Title + count; Filter button + Download | Same as MD, wrapping per list-header |
| Org blocks, cards, Archive grid | 074 §7.1 | 074 §7.1 | 074 §7.1 |

Without requests there is no filter column, Filter button, overlay or Download.

### 8.2 Accessibility

- **Headings:** `<h1>` page; `<h2>` org; `<h3>` New / Open / Archived; `<h4>` dataset (D3). The active menu item
  carries `aria-current="page"`.
- **Download:** `c-dropdown` trigger with `aria-expanded` / `aria-controls`; `role="menu"` panel; arrow keys,
  Enter / Space (`dropdown.js`).
- **Filter:** native checkboxes labelled by their list items; each change reloads the page, as on Search.
- **Overlay:** `role="dialog"`, `aria-modal`, focus trap, Escape, focus back to the Filter button.
- **Rows, chips, drawers, Archive `<details>`:** as 074 §7.2.
- CSS `:hover` / `:focus-visible` only; no Bootstrap classes or data attributes.

---

## 9. Options, Recommendations & Decisions Taken

Every decision was asked and confirmed with the user.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Menu for permission holders (084 D3) | Gate every item / gate this item only / keep `[]` | Gate every item | **Gate every item.** `hdx_get_sysadmin_nav_sections()` returns every item to sysadmins; other logged-in users get the items whose page check passes (§2.7; All Sysadmins and All Users stay sysadmin-only); no items → no section; anonymous → `[]`. Feeds the sidebar, the "Sysadmin" crumb (→ the first item listed) and the header user menu |
| D2 | Body reuse | `groups` param / inner per-set snippet | `groups` param | **`groups` on `v2/hdx-connect-sections.html`** (§5.2); one wrapper, alert and drawer pair per page |
| D3 | Dataset title level under h3 sections | `title_tag` on `c-request-card` / keep h3 | `title_tag` | **`title_tag`** (default `'h3'`); `h4` with `groups` |
| D4 | Download placement | `list-header` `caller()` slot / page-specific row | Slot | **`caller()` slot** on `v2/list-header.html`, every width |
| D5 | Organisation filter | Extend `v2/search-filters.html` + comma format in `search.js` / 080 pattern / single-select | Extend search-filters | **080 pattern**: multi-select checklist, handler in `hdx-connect.js`, no search box |
| D6 | MD/SM filter | Filter button + overlay / inline above the list | Button + overlay | **Filter button + overlay** |
| D7 | Maintainer filter (Figma) | Omit / template-side / HDX view override | Omit | **Omit** |
| D8 | Archive sort (Figma, per org) | Omit / template-side per org / one global | Omit | **Omit** |
| D9 | Counts | Rendered requests / v1 page total + 080 per org / v1 values | Rendered requests | **Per org: new + open + archived requests** (also the filter counts); **page: the sum over the organisations shown** |
| D10 | Section label (Figma / v1 "Archive") | Archived / Archive | Archived | **Archived** (080 D11) |
| D11 | Pagination | None / paginate orgs in the template | None | **None** |
| D12 | Applied-filter pills | None / reuse the Search pills row | None | **None** |
| D13 | Org name | Plain / link to its Requested Data tab / link to the org page | Plain | **Plain text**, full name |
| D14 | Actions for permission holders | Everyone / sysadmins only | Everyone | **Everyone** (v1); failures show the shared error alert |
| D15 | Filter option order | Count descending / alphabetical / v1 order | Count descending | **Count descending**, then title |
| D16 | Tests | None / page-load tests | None | **None**; render-level checks |
| D17 | Empty New / Open section in an org block | Show / hide in `groups` mode | Show | **Show**: heading, 0 and "No requests found." (v1, 074 / 080) |
| D18 | Org block border (Figma: every block) | Every block / between blocks only | Every block | **Every block**, the first included (§6.4) |
| D19 | Archived sort with `groups` (the EXT ignores `order_by`) | `groups` implies none / new `show_sort` param | `groups` implies none | **`groups` implies none**; 074 / 080 keep theirs |
| D20 | Menu-check cost (D1; the helper runs twice per page, §2.7) | Compute once in the header / as is / per-request cache on `g` | Compute once | **Compute once** in `v2/header.html`, passed to `v2/navbar-user-menu.html` as `sections` |
| D21 | v1 HDX `requestdata/snippets/*`, `ajax_snippets/reply_request_form.html`, `reject_request_form.html` (no consumer after this task) | Keep / delete | Keep | **Kept on disk** (080 D1 / 079) |
| D22 | Render-time check (≈2.8k requests on prod, few locally) | v1 vs v2 per-item ratio / seed synthetic requests / skip | Ratio | **Skip**: v1 parity (D11) |
| D23 | Org block spacing (Figma: 40 / 24 / 48) | Figma / §6.4 with the list-header's 16px margin / Figma outer only | Figma | **§6.4**: 16px page header → first block, 40px org header → New, 48px between blocks |
| D24 | Download width (Figma 10.313rem) | Natural / Figma | Natural | **Natural width** |
| D25 | Download panel after a click (the file downloads, the page stays) | Stays open / close on item click in `dropdown.js` | Stays open | **Stays open**, as the resource page's "Export metadata" |

**Derived decisions.** Not asked separately; each follows a preservation rule or a precedent. Raise any of them
before implementation if they should change.

| Item | Resolution | Basis |
|---|---|---|
| Rollout | Direct replacement of the HDX override | 074 / 080 / 084 / 085 |
| Crumb, `<title>`, heading | Home / Sysadmin / HDX Connect Dashboard; "HDX Connect Dashboard \| Sysadmin"; `<h1>` + count + Figma subtitle | 084 D11 |
| Layout | Dashboard base columns (25% / 50% / 25%), not Figma's 14.063rem columns | 073 |
| Hidden elements | No search, "Results per page", collapse chevron or "Closed" | Hidden in the export (080) |
| Empty archive groups | Dropped in the page template | Data quirk §2.3 |
| Maintainer line | New and Open cards; `fullname or username`; none when unresolved | 080 D13 / D17 |
| Empty page | "No requests found."; filter column and Download whenever `organizations_for_filters` is non-empty | A filter that empties the page stays clearable; the export ignores the filter |
| Unknown filter names | Filtered state + "Clear selection" | 080 §6.3 |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/all_requests_data.html` | Full v2 replacement (§6.2, §6.3) |
| `THEME/templates/v2/hdx-connect-sections.html` | `groups`, heading levels, maintainer fallback, `caller()` forwarding, header comment (§5.2) |
| `THEME/templates/v2/list-header.html` | `caller()` actions slot + header comment |
| `THEME/templates/v2/components/request-card.html` | `title_tag` + header comment |
| `THEME/helpers/helpers.py` | `hdx_get_sysadmin_nav_sections()` gating (D1) |
| `THEME/templates/v2/header.html`, `THEME/templates/v2/navbar-user-menu.html` | Menu sections computed once; `sections` param + header comment (D20) |
| `THEME/fanstatic/v2/pages/hdx-connect.js` | Organisation filter handler + header comment |
| `THEME/fanstatic/v2/pages/search.js` | `FILTER_PARAMS` += `'filter_by_organizations'` |
| `LESS/pages/hdx-connect.less`, `LESS/pages/search.less` | `.hdx-v2-hdx-connect__group`; `.hdx-v2-list-header` `column-gap` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/074-user-dashboard-hdx-connect-requests-v2.md`, `080-organization-page-hdx-connect-requests-v2.md` | Shared snippet params, card `title_tag` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/084-sysadmin-all-sysadmins-v2.md`, `085-sysadmin-all-users-v2.md`, `018-navigation-dropdown.md`, `019-navbar-open.md` | Menu gating for permission holders (D1); user menu sections computed once in the header (D20) |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | List-header actions slot |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated page entry, HDX Connect snippet, sysadmin menu |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 086 status |

Not changed: EXT, v1 `admin/base.html`, the `/components` demo (`title_tag` and the slot have no visual effect).

---

## 11. Implementation Checklist

1. Save "before" HTML with the in-container test client: the user HDX Connect page, one org Requested Data page,
   `/dataset`, `/ckan-admin`, `/user`.
2. Gate `hdx_get_sysadmin_nav_sections()` (D1); compute the user menu sections once in `v2/header.html` (D20).
3. Add the `list-header` actions slot and its LESS.
4. Add `title_tag` to `c-request-card`.
5. Add `groups`, the heading levels, the maintainer fallback and the caller forwarding to the shared snippet.
6. Add `.hdx-v2-hdx-connect__group` to `hdx-connect.less` (the IDE compiles it).
7. Add the organisation handler to `hdx-connect.js` and the `FILTER_PARAMS` entry to `search.js`.
8. Replace `admin/all_requests_data.html`.
9. Run render-level checks, then hand the visual test to the user.
10. Update the docs in §10 and `STATUS.md`.

---

## 12. Risks & Edge Cases

| Case | Handling |
|---|---|
| Thousands of requests, no pagination | v1 parity (D11); not measured (D22) |
| Menu checks on every v2 page for logged-in non-sysadmins | Four access checks per page (Products Menu and Package Links share one); eight on a v2 sysadmin page, where the sidebar runs them again; none for sysadmins (D1, D20) |
| Permission holder on All Users | Their gated menu, no active item; crumb Home / All Users |
| Permission holder acting on another org's request | 403 → the shared error alert (D14) |
| Missing counters row, the 2000-row cap, deleted datasets | Pre-existing EXT behaviour, unchanged (080 D19 deferral) |
| Unresolvable or nameless maintainer | No line, or the username (derived) |
| Requests without `extras` | As 074: no org / country / chips / intended use |
| Multiple orgs in a bookmarked URL | Parsed and shown as selected (D5) |
