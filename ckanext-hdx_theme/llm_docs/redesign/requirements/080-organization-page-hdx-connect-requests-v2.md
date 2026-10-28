# 080 — Organization Page: HDX Connect Requests (v2 Migration)

**Scope:** the org page "Requested Data" tab, `/organization/requested_data/<id>`
(`requestdata_organization_requests.requested_data`), moved onto the v2 org shell (056–059). Also in scope:
- a shared body snippet extracted from the 074 user page and used by both HDX Connect pages;
- a `show_controls` param on `v2/filter-overlay.html`;
- `filter_by_maintainers` in `search.js` `FILTER_PARAMS`, and a `null` value deleting the param in `url-nav.js` `setNavParam`;
- the heading count (new + open + archived) and the empty-state class on the 074 user page;
- 3-level breadcrumbs on the org Activity and Stats tabs, the full org name in the Members crumb, and no hero
  counts on the Stats tab.

**Excluded:**
- The sysadmin HDX Connect Dashboard (`requestdata_ckanadmin.requests_data`), which stays v1.
- Any change to the `ckanext-requestdata` repo (view, actions, auth, model).
- Pagination, new analytics events and new tests.
- An HDX-side guard against the EXT view's 500s (D19, deferred).

**Figma sources** (in `ckanext-hdx_theme/llm_docs/redesign/figma_exports/`):
- Primary: `xl-org-page-loggien-in-request-data.html`, `sm-org-page-requested-data.html`.
- `xl-org-page-loggien-in-request-data.html` is identical to `xl-org-page-requested-data.html` (074's
  reference), except that the older file also holds a Search "Format" overlay. There is no MD export.

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `EXT` = `src/ckanext-requestdata/ckanext/requestdata` (separate repo `OCHA-DAP/ckanext-requestdata`, pinned tag `3.0.42`)

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `requestdata_organization_requests.requested_data` (`/organization/requested_data/<id>`). Reached from the org hero tab "Requested Data", the request-access emails to org admins and the sysadmin bell notifications |
| Objective | v2 page on `v2/page.html` + `v2/org-hero.html` with Figma's layout, keeping every v1 behaviour: endpoints, payloads, auth, the `filter_by_maintainers` and `order_by` URLs, reload on success |
| Strategy | **Direct replacement** of the HDX override `requestdata/organization_requested_data.html` (no `?v2` gate, as 056–059 and 074). The EXT view is untouched |
| Shared work | The 074 page body becomes one snippet used by both HDX Connect pages; the Maintainer filter reuses the Search filter column, Filter button and overlay |

---

## 2. Repository Audit Findings (v1 vs v2)

### 2.1 Routes and auth

| Endpoint | URL | Notes |
|---|---|---|
| `requestdata_organization_requests.requested_data` | `/organization/requested_data/<id>` (GET) | EXT `views/organization.py` `requested_data`. `<id>` is a name or UUID (the admin emails use the UUID) |
| `hdx_requestdata_user.handle_new_request_action_reply` / `_reject` | `/user/my_requested_data/<username>/reply`, `.../reject` (POST) | Reply / Decline, shared with 074. The `<username>` segment is ignored |
| `requestdata.handle_open_request_action_shared` | `/user/my_requested_data/<username>/shared` (POST) | Yes / No, shared with 074 |
| `hdx_light_org.light_fake` (mobile) | `/m/organization/requested_data/<id>` | Redirects to the mobile org page (`hdx_light_org.light_read`). Unchanged |

- **Page auth:** `requestdata_request_list_for_organization` (EXT `logic/auth.py` `request_list_for_organization`)
  passes org **admins**; sysadmins pass through the CKAN bypass. Everyone else gets 403 "Not authorized to see
  this page.".
- **Tab gate:** `h.check_access('organization_update', …)` (`can_edit` in `v2/org-hero.html`), which is the org
  admin role in core: the same people as the page auth.
- **Action auth:** `_user_has_access_to_request` (package creator, maintainer, org admin, sysadmin), as in 074.

### 2.2 Data passed to the template

| Variable | Shape |
|---|---|
| `requests_new`, `requests_open` | Request dicts as in 074 §2.2. Each also carries `maintainers = [user]`, where `user` is `{id, name, username, fullname, count}` (`name` = fullname or username) |
| `requests_archive` | Per-dataset groups: `package_id`, `title`, `maintainers` (the raw maintainer id), `requests_archived`, and the **lifetime** counters `requests`, `replied`, `declined`, `shared` |
| `maintainers` | `{id, name, username, fullname, count}` per dataset maintainer, sorted by `count` (requests in any state, counted before the filter) |
| `org_name` | Org slug |
| `current_order_name` | Label of the archive sort |
| `org_meta` | `OrgMetaDao` after `fetch_all()`; `org_meta.org_dict` is the light group dict the hero needs. No `org_dict` is passed |
| `counters` | Org totals per counter. Not displayed |

- The view renders `requestdata/custom_organization_requested_data.html` when `org_meta.is_custom`.
- New / Open are ordered `modified_at desc`. The list is capped at `ckan.search.rows_max` (1000), with no
  pagination.

### 2.3 Filter and sort URLs

| Param | Format | Server |
|---|---|---|
| `filter_by_maintainers` | `org:<org_name>\|maintainers:<u1,u2>` (usernames), or `…\|maintainers:*all*` | The org part is ignored; `*all*` means no filter. Requests are removed before grouping, so all three sections shrink |
| `order_by` | `<value>\|org:<org_name>` (v1 links) or `<value>` | Only the part before `\|` is read. Values and labels as 074 §2.2. Archive only |

- v1's sort links (`order_requests.html`) rebuild the URL from scratch, so they drop an active maintainer filter.
- v1's filter (`filter-requests` module) keeps the other params.

### 2.4 v1 rendering

| Part | v1 |
|---|---|
| Chrome | `organization/read_v1_base.html` → `read_base.html` → v1 `page.html`: v1 org header, BS5 tabs |
| Breadcrumb | Organizations / {org} / Dataset Requests |
| `<title>` | "{org} Humanitarian Data \| Dataset Requests" |
| Header | `requests_header.html`: "Dataset Requests [N]", N = new + open + archived requests. The org counters row is commented out |
| Filter | EXT `filter_requests.html`: "Filter by: Maintainer" BS dropdown with "{name} ({count})" checkboxes, Apply / Reset. Shown only when `maintainers` is non-empty |
| Sections | EXT `section_base.html`: "New [n]", "Open [n]", "Archive [n]" (groups), "No requests found." when empty |
| Items | HDX `section_item_new.html` / `_open.html` / `_archive.html`; "Maintained by {fullname}" (linked) on New items only; Reply / Decline BS modals; Yes / No AJAX |
| Sort | EXT `order_requests.html` "Order by:" BS dropdown above Archive, only when Archive is non-empty |

### 2.5 Custom orgs

`THEME/templates/requestdata/custom_organization_requested_data.html` extends the main template and overrides:
- `item_title_contrib` (the v1 custom org header), which renders nothing on a v2 page that overrides
  `primary_content`;
- `custom_styles` (a `base.html` block), which loads the v1 `hdx_theme/custom-org-styles` bundle and inline
  highlight / logo-background CSS.

### 2.6 Assets

- **Styles:** `requestdata/main-styles`, `hdx_theme/requestdata-styles`.
- **Scripts (per item):** `requestdata/modal-form-scripts`, `hdx_theme/requestdata-scripts`,
  `requestdata/section-item-scripts`, `requestdata/handle-open-req-scripts`, `requestdata/modules-scripts`.
- Bootstrap modal, collapse and dropdown JS.

### 2.7 Analytics and tests

- **Analytics:** nothing page-specific. `read_v1_base.html` fills `analytics_org_name` / `analytics_org_id`
  (`analyticsInfo`, GTM `org_name`). The Mixpanel page view sends `pageTitle` "{org} Humanitarian Data \| Dataset
  Requests". No action fires an event.
- **Entry links:** the org tab, the request-access emails to org admins (owner org UUID) and the sysadmin bell
  notifications (`light/notifications/requestdata_snippet.html`, org name). Their URLs are unchanged.
- **Tests:** no test loads this page. Action-level tests exist in EXT and in `ckanext-hdx_package`.

### 2.8 Reusable v2 pieces

| Piece | Fit |
|---|---|
| `v2/page.html` + `v2/org-hero.html` | Hero, tabs, actions. `active_tab='requested_data'` is already supported; the tab shows on `can_edit` |
| `organization/read.html` (056) | Left filter column: `outer_row_class='hdx-v2-search-row'`, XL-only sticky `hdx-v2-search-sidebar`, `<form id="search-page-filters-form"><aside class="hdx-v2-search-filters">`, `v2-search-page-styles` / `-scripts` |
| `organization/members.html` (059) | 3-level breadcrumb: Organisations / {org} linked to `hdx_org.read` / Members |
| `requestdata/my_requested_data.html` (074) `primary` block | The whole body: header, New / Open grouping per dataset, Archived grid + sort, empty states, shared-error `c-alert`, the two drawers |
| `c-request-card` | `maintainer_label` / `maintainer_href` render the "Maintained by" line when set |
| `v2/hdx-connect-request.html`, `v2/hdx-connect-drawers.html`, `fanstatic/v2/pages/hdx-connect.js` | No user-specific logic; the Yes / No URL comes from `data-hdx-connect-shared-url` |
| `v2/list-header.html` | Title + count, `show_filters` (MD/SM Filter button with `total_selected`) |
| `v2/filter-overlay.html` + `search.js` "FilterOverlay init" | Overlay, focus trap, Escape; moves `#search-page-filters-form` into the overlay below XL. The overlay always renders `v2/search-nav-controls.html`, which without `sorting_options` falls back to the dataset-search sorts |
| `search.js` facet handlers | `clear-filter` (dropdown "Clear selection") deletes one param; `clear-filters` (overlay) deletes `FILTER_PARAMS`. Checkbox changes write repeated `?facet=a&facet=b` params, which don't fit `filter_by_maintainers` |
| `v2/components/dropdown.html` checklist | `state='filter'`, `has_clear`, `clear_facet`, per-item `attrs` |

### 2.9 Navigation

- Org pages have no left navigation menu. Navigation is the hero `c-tabs`, an inline item list in
  `v2/org-hero.html`: the active tab comes from the `active_tab` string, visibility from each item's `show`.
- Figma's left column on this page is a filter panel, not a menu.
- The user-dashboard sidebar (`v2/user-dashboard-base.html`, `h.hdx_get_user_dashboard_nav_sections`) belongs to
  the user area. No shared navigation shell is needed; each area keeps its own.

---

## 3. Figma Design Analysis

### 3.1 XL (`xl-org-page-loggien-in-request-data.html`)

**Hero and tabs:** the 056 hero; tabs Datasets / Activity / Members / Requested Data / Stats, "Requested Data"
active (4px primary-5 underline).

**Left column** (21.875rem, white, right border):
- Padding 20 / 40 / 80 / 48, 24px gap.
- "Filter by": 16px semibold.
- "Organisation" select fixed to the org name in a disabled look (lighter border and text, no shadow).
- "Maintainer" select "All maintainers" (14px medium, padding 8 / 8 / 8 / 10, border, shadow-sm).

**Content** (58.125rem, padding 32 / 48 / 48 / 40, 24px gap):
- Header row: "Requested Data" (Merriweather 24px bold) + count "13" (Roboto 16px, neutral-8), 8px apart; right
  side "Sort by" (14px, neutral-8) + select "Most Recent" (padding 6 / 8 / 6 / 10). "Results per page" is
  `display:none`.
- Sections "New 3", "Open 1", "Archive 3": heading 18px bold + count, 16px to the list, 24px between cards.
- Cards: as 074 §3.1, plus "Maintained by **username**" (14px neutral-8, username medium underlined, single line
  with ellipsis) under the title on New and Open cards.
- Request rows, chips, footer bar, Yes / No prompt and the Archive grid: identical to 074 §3.1.

**Hidden in the export:** a "Closed 12" section, a title chevron, the expanded `open-card`.

### 3.2 SM (`sm-org-page-requested-data.html`)

- Hero + tabs.
- "Requested Data 13" with a "Filter (10)" button (neutral-01 background, 1px neutral-95 border, 16px icon,
  count in primary).
- New section only (truncated export), full-width cards, footer bar on one row.
- Pager 1 2 3 … 31.
- Hidden: a "You might also like" block.

### 3.3 Breakpoint deltas

| Aspect | XL | SM |
|---|---|---|
| Filters | Left "Filter by" column | "Filter (n)" button beside the title |
| Sort | Header row | Not shown |
| Pagination | "Results per page" hidden | Pager |
| Cards | Fixed 58rem column | Full width |

MD is not exported. v2 breakpoints give MD the SM pattern (no column below `@hdx-bp-xl`, Filter button + overlay),
as on Search and the org Datasets tab.

### 3.4 Tokens

Every value maps to an existing token; the 074 §3.5 table applies unchanged.

---

## 4. Current vs Target Comparison Matrix

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 org header + BS5 tabs | `v2/org-hero.html`, `active_tab='requested_data'` | D1 |
| Breadcrumb | Organizations / {org} / Dataset Requests | Organisations / {org} / Requested Data | D9, D12 |
| `<title>` | "{org} Humanitarian Data \| Dataset Requests" | "{org} Humanitarian Data \| Requested Data" | D9 |
| Heading | "Dataset Requests [N]" | "Requested Data" + count (`list-header`, `title_size='dashboard'`) | D9, D10, D14 |
| Filter | BS checklist, Apply / Reset | XL left column; MD/SM Filter button + overlay; instant apply; "Clear selection" | D4, D6, D7, D8 |
| Sort | "Order by:" above Archive; drops the filter | Archived heading row at every width; keeps the filter | D5 |
| Sections | New / Open / Archive | New / Open / Archived | D11 |
| Dataset group | v1 rows | `c-request-card` per dataset | D2 |
| Maintainer line | New items only | New and Open cards | D13, D17 |
| Request rows, actions, Archive grid | BS markup, modals, collapse | 074 components and drawers | D2 |
| Empty section | "No requests found." | Same copy, `hdx-v2-hdx-connect__empty` | D15 |
| Custom orgs | Custom header + custom CSS | Same v2 page as every org | D3 |
| Pagination | None | None | D16 |
| Assets | v1 requestdata bundles, Bootstrap JS | `v2-search-page-*`, `v2-org-page-styles`, `v2-hdx-connect-page-styles`, `v2-hdx-connect-scripts` | D6 |

**074 user page changes:** the heading count adds archived requests (D10); the empty state uses the new class
(D15). Everything else renders unchanged through the shared snippet (D2).

**Org Activity and Stats tabs:** 3-level breadcrumb (D12); the Stats hero drops its Datasets / Members counts.
Nothing else changes.

---

## 5. Component & System Reuse Strategy

### 5.1 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, hero, tabs | `v2/page.html` + `v2/org-hero.html` | Reuse | D1 |
| Layout with filter column | `organization/read.html`'s `outer_row_class` / `sidebar_class` / `content_class` | Reuse | D4 |
| Filter column | `#search-page-filters-form` > `aside.hdx-v2-search-filters`, heading `hdx-v2-search-filters__heading`, one `hdx-v2-search-filters__item` with a checklist `v2/components/dropdown.html` | Reuse | D4, D7 |
| MD/SM Filter button | `v2/list-header.html` `show_filters`, `total_selected` (via the shared snippet) | Reuse | D4 |
| Overlay | `v2/filter-overlay.html` with **new `show_controls`** | Extend | D5 |
| Body | **New shared snippet** `v2/hdx-connect-sections.html`, extracted from `my_requested_data.html` | Share (extraction) | D2 |
| Maintainer line | `c-request-card` `maintainer_label` / `maintainer_href` | Reuse | D13 |
| Request rows, drawers, actions | `v2/hdx-connect-request.html`, `v2/hdx-connect-drawers.html`, `hdx-connect.js` | Reuse | D2 |
| Filter JS | `search.js` (overlay, "Clear selection", "Clear filters") + a maintainer handler in `hdx-connect.js` | Extend | D6, D8 |
| Empty state | `.hdx-v2-hdx-connect__empty` in `LESS/pages/hdx-connect.less` | New class | D15 |
| Breadcrumb | `v2/components/breadcrumb.html`, Members' 3-item list | Reuse | D12 |

### 5.2 Shared snippet `v2/hdx-connect-sections.html`

| Param | Type | Notes |
|---|---|---|
| `requests_new`, `requests_open`, `requests_archive` | list | Required. The view's lists |
| `list_title` | string | Heading text |
| `list_subtitle` | string | default `''` |
| `title_tag` | string | default `'strong'` (the user page passes `'h1'`) |
| `show_filters`, `total_selected` | bool / int | Forwarded to `v2/list-header.html`. default `False` / `0` |
| `show_maintainer` | bool | Fills `c-request-card`'s `maintainer_label` / `maintainer_href` from each group's maintainer. default `False`. The header says it maps to those card params (074 Q48 keeps the component without a `show_maintainer`) |

**Contents:**
1. Header: `v2/list-header.html`, `title_size='dashboard'`, `show_controls=False`, count = new + open +
   archived requests (sum of each group's `requests_archived`).
2. `div.hdx-v2-hdx-connect` with `data-hdx-connect-shared-url`.
3. New / Open grouping as 074 §6.2. With `show_maintainer`, each group also keeps `maintainer = item.maintainers[0]` (may be `None`).
4. Archived section with its sort: `sorting_selected = (request.args.get('order_by') or 'most_recent').split('|')[0]`,
   so v1 links with `|org:<org>` keep their selection.
5. Empty sections: `<p class="hdx-v2-hdx-connect__empty">No requests found.</p>`.
6. The hidden shared-error `c-alert` and `v2/hdx-connect-drawers.html`.

- `request`, `c`, `h` and `_` are Jinja globals inside snippets; page variables arrive as kwargs. No loop
  variable is named `request`.
- Maintainer line: `maintainer_label = maintainer.fullname`, `maintainer_href = h.url_for('user.read',
  id=maintainer.username)`; omitted when `show_maintainer` is off or the maintainer is `None`.

### 5.3 Other shared changes

| Change | Detail |
|---|---|
| `v2/filter-overlay.html` | `show_controls` (default `True`) wraps the `.hdx-v2-overlay-nav-controls` block. Search's HTML stays identical |
| `fanstatic/v2/url-nav.js` | `setNavParam(key, null)` deletes the param (D6) |
| `fanstatic/v2/pages/search.js` | `FILTER_PARAMS` gains `'filter_by_maintainers'`, so the overlay "Clear filters" removes it. "Clear selection" calls `setNavParam(facet, null)`. No Search behaviour changes |
| `fanstatic/v2/pages/hdx-connect.js` | Maintainer filter handler (§6.4) |
| `fanstatic/webassets.yml` | New `v2-hdx-connect-scripts` (`<<: *common-js`, `v2/pages/hdx-connect.js` only). `v2-hdx-connect-page-scripts` (`url-nav.js` + `hdx-connect.js`) stays for the user page; each page loads exactly one of the two |
| `LESS/pages/hdx-connect.less` | `&__empty { .hdx-list-header-empty(); margin: 0; }` inside `.hdx-v2-hdx-connect`. `hdx-v2-dashboard-empty` stays: other dashboard pages use it |

---

## 6. Functional Requirements

### 6.1 Backend

- No view, action, auth or model change in `ckanext-requestdata`.
- The template uses `requests_new`, `requests_open`, `requests_archive`, `maintainers`, `org_name` and `org_meta`.

### 6.2 Org template

Full replacement of `THEME/templates/requestdata/organization_requested_data.html`, extending `v2/page.html`:

| Part | Content |
|---|---|
| Top-level sets | `org_meta = org_meta or c.org_meta`, `org_dict = org_dict or org_meta.org_dict or c.group_dict`; layout classes from `organization/read.html`; the parsed maintainer filter (§6.3) |
| `analytics_org_name` / `analytics_org_id` | `org_dict.name` / `org_dict.id` |
| `subtitle` | `{{ org_dict.display_name }} Humanitarian Data \| {% block subtitle_suffix %}Requested Data{% endblock %}`. No canonical link, no meta description (v1 parity) |
| `styles` | `v2-search-page-styles`, `v2-org-page-styles`, `v2-hdx-connect-page-styles` |
| `scripts` | `v2-search-page-scripts`, then `v2-hdx-connect-scripts` |
| `breadcrumb_items` | Organisations / `org_dict.display_name` → `hdx_org.read` / Requested Data |
| `pre_primary` | `v2/org-hero.html`, `active_tab='requested_data'` (no `header_stats`); no `notification_platform/modals.html`, so "Get notified" stays hidden (D18) |
| `secondary_content` | Only when `maintainers` is non-empty: the filter column (§6.3) |
| `primary_content` | The shared snippet with `list_title=_('Requested Data')`, `show_filters=maintainers \| length > 0`, `total_selected`, `show_maintainer=True`; then, when `maintainers` is non-empty, `v2/filter-overlay.html` with `total_selected` and `show_controls=False` |

`custom_organization_requested_data.html` is reduced to `{% extends "requestdata/organization_requested_data.html" %}` (D3).

### 6.3 Maintainer filter

- **Parsing** (template): from `request.args.get('filter_by_maintainers')`, take the part after `maintainers:` in
  the second `|` segment, split on `,`, and drop `*all*` and empty entries. Missing or unparsable values give an
  empty selection. `total_selected` = the number of entries left, so an unknown username still shows the filtered
  state and "Clear selection".
- **Dropdown:** label "Maintainer"; placeholder "All maintainers"; trigger text = the selected maintainers' names
  joined by ", "; `state='filter'` when anything is selected; `panel_id='hdx-filter-panel-maintainers'`; wrapper
  `attrs={'data-hdx-connect-maintainer-filter': org_name}`; `has_clear` when selected, `clear_facet='filter_by_maintainers'`.
- **Items:** one per `maintainers` entry: `value` = `username`, `label` = `name`, `count` = "({count})",
  `checked` / `active` when selected, `attrs={'data-hdx-connect-maintainer': ''}`. No `data-filter-checkbox` and no
  `name` attribute (a native submit would send a value the view can't parse).
- No Organisation dropdown (D7). No search box in the panel (D16).

### 6.4 JS (`fanstatic/v2/pages/hdx-connect.js`)

**Maintainer filter** (new):
- A delegated `change` handler on `[data-hdx-connect-maintainer]` collects the checked values inside the closest
  `[data-hdx-connect-maintainer-filter]`.
- `window.hdxSetNavParam('filter_by_maintainers', …)` with `'org:' + <org> + '|maintainers:' + values.join(',')`,
  or `null` (deletes the param) when none is checked. It drops `page` and keeps every other param.

**Unchanged:** Reply / Decline / Yes / No as 074 §6.4. The Yes / No URL comes from the snippet's wrapper.

**From `search.js` (as loaded):** "Clear selection" deletes `filter_by_maintainers`; the overlay "Clear filters"
deletes `FILTER_PARAMS`; the overlay open / close / focus handling. The Archived sort uses `url-nav.js` from the
same bundle, so a sort change keeps the filter.

### 6.5 Copy

| Element | Copy |
|---|---|
| Heading, crumb, `<title>` suffix | "Requested Data" |
| Filter heading | "Filter by" |
| Filter label / placeholder | "Maintainer" / "All maintainers" |
| Maintainer option | "{name}" + "({count})" |
| Card maintainer line | "Maintained by {fullname}" |
| Sections | "New", "Open", "Archived" |
| Empty | "No requests found." |
| Everything else | As 074 §6.3 |

All strings go through `_()`.

### 6.6 Activity and Stats breadcrumbs

`organization/activity_stream.html` and `organization/stats.html` get Members' 3-item list: Organisations /
`org_dict.display_name` → `hdx_org.read` / "Activity" or "Stats". The Datasets tab keeps 2 items. No org crumb truncates
the name.

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Org admin / sysadmin access, 403 for others | Unchanged (EXT view) |
| Tab visible on `organization_update` | `v2/org-hero.html` `can_edit` |
| Reply / Decline / Yes / No endpoints and payloads | 074 drawers and `hdx-connect.js` |
| Reload on success | Unchanged |
| `filter_by_maintainers` URL format | Same string from `hdx-connect.js`; bookmarked URLs (including `*all*`) parse |
| `order_by` URLs | Same values; `\|org:` suffixes still read |
| "No requests found." | Same copy |
| Lifetime archive counters, 1000-row cap | Unchanged |
| `analytics_org_name` / `analytics_org_id`, GTM `org_name` | Same blocks |
| Mixpanel page view | Still fires; `pageTitle` "{org} Humanitarian Data \| Requested Data" (D9) |
| Notification and email entry links | Unchanged URLs |
| Mobile `/m/` route | Unchanged redirect to the mobile org page |

**Intentional differences:** labels (D9), the count (D10), "Archived" (D11), the maintainer line on Open (D13),
sorting keeps the filter, instant apply without Apply / Reset (D8), no custom-org header or CSS (D3).

---

## 8. Responsive & Accessibility Considerations

### 8.1 Breakpoints

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Hero, tabs | 056 | 056 | 056 (tabs scroll horizontally) |
| Filter | Sticky left column (`hdx-v2-search-sidebar`) | Filter (n) button → full-screen overlay | Same as MD |
| Content | Search content padding | Full width | Full width |
| Heading | "Requested Data" + count | Same + Filter button | Same + Filter button |
| Sort | Archived heading row | Same; wraps right-aligned when narrow | Same as MD |
| Cards, Archive grid | 074 §7.1 | 074 §7.1 | 074 §7.1 |

No filter column, Filter button or overlay when `maintainers` is empty; the content then takes the full row.

### 8.2 Accessibility

- **Headings:** the hero `<h1>` (org name); "Requested Data" as list-header's default `<strong>`, as on the org
  Datasets tab; New / Open / Archived `<h2>`; dataset titles `<h3>`. No skipped levels. The active tab carries
  `aria-current="page"`.
- **Filter:** native checkboxes labelled by their list items; the dropdown trigger syncs `aria-expanded`
  (`dropdown.js`). Each change reloads the page, as the Search filters do.
- **Overlay:** `role="dialog"`, `aria-modal`, focus trap, Escape, focus returns to the Filter button.
- **Rows, chips, drawers, Archive `<details>`:** as 074 §7.2.
- **States:** CSS `:hover` / `:focus-visible` only; contrast pairs as 074 §7.2.
- No Bootstrap classes or data attributes.

---

## 9. Options, Recommendations & Decisions Taken

Every decision was asked and confirmed with the user.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Rollout | Direct replacement / `?v2=true` gated copy | Direct replacement | **Direct replacement** on `v2/page.html` + `v2/org-hero.html`. `read_v1_base.html` stays on disk with its header comment untouched |
| D2 | Body reuse | Extract a shared snippet / copy into the org template | Extract | **Extract** `v2/hdx-connect-sections.html`, called by both pages |
| D3 | Custom orgs | Bare extends / leave the file | Bare extends | **Bare extends**: same v2 page for every org |
| D4 | Filter layout | Search pattern (XL column, MD/SM button + overlay) / inline dropdown, no column | Search pattern | **Search pattern** |
| D5 | Sort placement | Archived heading / page header (Figma) | Archived heading | **Archived heading** at every width, only with Archive rows; overlay `show_controls=False` |
| D6 | Filter JS | Reuse `search.js` + `FILTER_PARAMS` + handler in `hdx-connect.js` / extract the overlay JS | Reuse `search.js` | **Reuse `search.js`**; new `v2-hdx-connect-scripts` bundle. The handler calls `window.hdxSetNavParam`, where `null` deletes the param; `search.js`'s one-facet clear uses it too |
| D7 | Figma's disabled Organisation select | Omit / disabled dropdown | Omit | **Omit** |
| D8 | Apply behaviour | Instant (Search) / Apply + Reset (v1) | Instant | **Instant**, with "Clear selection" |
| D9 | Label (Figma "Requested Data" vs v1 "Dataset Requests") | Requested Data / Dataset Requests | Requested Data | **Requested Data** (heading, crumb, `<title>`) |
| D10 | Heading count | v1 total / New + Open (074) / none | v1 total | **New + open + archived requests on both pages** |
| D11 | Archive heading (v1 org + Figma "Archive" vs 074 "Archived") | Archived on both / Archive on both / per page | Archived on both | **Archived on both** |
| D12 | Breadcrumb depth | Two levels (Figma, Datasets / Activity / Stats) / three levels (v1, Members) | Two levels | **Three levels**, also on Activity and Stats; only Datasets keeps two. Full org name, no `truncate`, Members included |
| D13 | "Maintained by" line | New + Open (Figma) / New only (v1) | New + Open | **New + Open cards**, org page only |
| D14 | Heading levels | `<strong>` / `<h2>` / `<h3>` / `<h2>` / `<h3>` / `<h4>` (new card param) | `<strong>` | **`<strong>` / `<h2>` / `<h3>`**, no component change |
| D15 | Empty-state styling and markup | Move to `hdx-connect.less` / load dashboard styles / org empty class; single `<p>` / div + `__empty-text` | Move; single `<p>` | **`<p class="hdx-v2-hdx-connect__empty">`** in `hdx-connect.less` |
| D16 | Pagination, panel search box, tests | None / client-side pager; none / `has_search`; none / page-load rows | None for all | **No pagination, no search box, no new tests**; no new analytics events |
| D17 | "Maintained by" name (Figma "username" vs v1 full name) | Full name / username | Full name | **Full name** (`maintainer.fullname`, falling back to the username), as v1 and the filter options |
| D18 | Hero "Get notified" (in Figma; the button needs `notification_platform/modals.html`, which only the Datasets tab includes) | Hidden / this tab / all non-Datasets tabs | Hidden | **Hidden**, as v1 and Activity / Stats / Members |
| D19 | Pre-existing EXT 500s (malformed `filter_by_maintainers`, unknown `order_by` with archive rows, unknown org id) | Follow-up / as-is / HDX-side guard in 080 | Follow-up | **HDX-side guard wanted, deferred**: not in 080; mechanism, response and tests still to be decided |

**Derived decisions.** Not asked separately; each follows a preservation rule or a precedent. Raise any of them
before implementation if they should change.

| Item | Resolution | Basis |
|---|---|---|
| Crumb labels | "Activity", "Stats", "Requested Data" | Tab labels, as Members |
| `title_size` | `'dashboard'` (24px Merriweather bold, 16px count) | Exact Figma match |
| Subtitle | None | Figma |
| Filter trigger text | Selected names joined by ", ", else the placeholder | `v2/search-filters.html` |
| Empty filter | Unchecking the last box removes the param (same result as v1's `*all*`) | Cleaner URL, same server behaviour |
| Filter visibility | Only when `maintainers` is non-empty | v1 |
| "Closed" section | Not rendered | Hidden in the export |
| Bundle name | `v2-hdx-connect-scripts` | `hdx-connect.js` in two bundles, 058 precedent |
| Hero stats | No `header_stats` on any org tab; `stats.html` and the `stats()` view's `datasets_num` fetch comment theirs out | Activity tab; 056 "KPI-style cards?" |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/v2/hdx-connect-sections.html` (new) | Shared body (§5.2) |
| `THEME/templates/requestdata/my_requested_data.html` | `primary` = one snippet call (`title_tag='h1'`, subtitle); page-level sort sets move into the snippet |
| `THEME/templates/requestdata/organization_requested_data.html` | Full v2 replacement (§6.2) |
| `THEME/templates/requestdata/custom_organization_requested_data.html` | Bare extends (D3) |
| `THEME/templates/v2/filter-overlay.html` | `show_controls` + header comment |
| `THEME/templates/v2/org-hero.html` | Header comment |
| `THEME/templates/organization/activity_stream.html`, `organization/stats.html` | 3-level breadcrumb (D12); `stats.html` also comments out `header_stats` |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py` | `stats()`: `fetch_dataset_info()` commented out |
| `THEME/templates/organization/members.html` | Full org name in the breadcrumb (D12) |
| `THEME/fanstatic/v2/url-nav.js` | `setNavParam(key, null)` deletes the param (D6) |
| `THEME/fanstatic/v2/pages/search.js` | `FILTER_PARAMS` += `'filter_by_maintainers'`; "Clear selection" via `setNavParam(facet, null)` |
| `THEME/fanstatic/v2/pages/hdx-connect.js` | Maintainer filter handler + header comment |
| `THEME/fanstatic/webassets.yml` | `v2-hdx-connect-scripts` |
| `LESS/pages/hdx-connect.less` | `.hdx-v2-hdx-connect__empty`, compiled to `fanstatic/v2/pages/hdx-connect.css`; header comment |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Organisation page (Requested Data tab on v2), HDX Connect (shared body snippet) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Org page and HDX Connect entries, bundle list, phase checklist, deferred list (the D19 guard), next steps |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | List-header / overlay pattern: `show_controls` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/074-user-dashboard-hdx-connect-requests-v2.md` | Excluded scope, title count, filter-overlay row, §6.2 layout and empty state, the v1-snippet sentence, the Files Affected grouping sentence, Q24, Q54 |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/057-organization-page-activity-v2.md` | Breadcrumb (D12) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/031-basic-filtering.md`, `034-dataset-header-v2.md`, `040-resource-page.md`, `056-organization-page-datasets-v2.md`, `058-organization-page-stats-v2.md`, `065-advanced-filters-v2.md`, `070-v2-full-audit.md` | `FILTER_PARAMS`, `setNavParam`, `read_v1_base.html` and org-tab status statements |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 080 → `in_progress` → `implemented` |

Not changed: `v2/list-header.html`, `organization/read_v1_base.html`, the v1
`requestdata/snippets/*` and `ajax_snippets/*` (the sysadmin page still uses them), EXT.

---

## 11. Implementation Checklist

1. Save "before" HTML with the in-container test client: the user page (New / Open / Archived data, an empty
   user, `?order_by=desc`), `/dataset`, one org's Activity and Stats tabs.
2. Create `v2/hdx-connect-sections.html` (§5.2).
3. Repoint `my_requested_data.html` to the snippet.
4. Add `.hdx-v2-hdx-connect__empty` to `hdx-connect.less` (the IDE compiles it).
5. Add `show_controls` to `v2/filter-overlay.html`.
6. Add `'filter_by_maintainers'` to `search.js` `FILTER_PARAMS`.
7. Add the maintainer handler to `hdx-connect.js`.
8. Add `v2-hdx-connect-scripts` to `webassets.yml`.
9. Replace `organization_requested_data.html` (§6.2, §6.3).
10. Reduce `custom_organization_requested_data.html`.
11. Update the Activity, Stats and Members breadcrumbs.
12. Run the verification below, then hand the visual test to the user.
13. Update the docs in §10 and `STATUS.md`.

---

## 12. Verification

- **User page:** rendered HTML matches step 1 after whitespace normalisation, apart from the count (D10) and the
  empty-state markup (D15).
- **`/dataset`:** rendered HTML identical to step 1.
- **Activity / Stats / Members:** only the breadcrumb differs, plus the Stats hero counts.
- **Org page:**
  - Org admin 200; non-admin 403; sysadmin 200.
  - No `requestdata/*`, `hdx_theme/requestdata-*` or `custom-org-styles` asset in the page.
  - Filter column, Filter button and overlay present only when `maintainers` is non-empty; the overlay has no
    sort or page-size controls.
  - `?filter_by_maintainers=org:<org>|maintainers:*all*` shows no selection; `?order_by=asc|org:<org>` shows
    "Alphabetical (A-Z)" selected.
  - A custom org renders the same page.
- **Container:** edited files rewritten in place; md5 matches inside the container; restart after the
  `webassets.yml` change.

---

## 13. Risks & Edge Cases

| Case | Handling |
|---|---|
| Malformed `filter_by_maintainers`, unknown `order_by` with archived groups, an unresolvable dataset maintainer, an unknown org | Pre-existing EXT 500s; the HDX-side guard is deferred (D19). The template parsing itself never raises |
| Unknown username in the filter | Every section empties; the filter state and "Clear selection" stay visible |
| Many maintainers | Plain list without a search box (D16) |
| `hdx-connect.js` in two bundles | Each page loads exactly one bundle that contains it |
| Search shared changes (`filter-overlay.html`, `search.js`, `url-nav.js`) | `show_controls` defaults to the current output; `filter_by_maintainers` never appears on Search URLs; no other `setNavParam` caller passes `null`. Verified by the `/dataset` diff |
| Mixpanel `pageTitle` change | Accepted (D9), as 072 / 074 |
| Requests without `extras` | As 074: no org / country / chips / intended use |
| Up to 1000 requests, no pagination | v1 parity (D16); two drawers per page regardless of count |
