# 074 — User Dashboard: HDX Connect Requests (v2 Migration)

**Scope:** `/user/my_requested_data/<id>` (`requestdata.my_requested_data`), moved onto the shared v2 dashboard base
from 072. Also in scope:
- new shared request components (`c-request-card`, `c-request-item`, `c-request-archive`);
- shared list-header and filter-overlay snippets extracted from the Search list;
- a `sort_key` param on `v2/search-nav-controls.html`;
- the bell-notification link copy;
- shared `window.hdxV2.setDisabled()` / `showAlert()` helpers and a `.hdx-clamp-toggle()` mixin, replacing every
  local copy (Q66, Q67).

**Excluded:**
- The org "Requested Data" tab and the sysadmin HDX Connect Dashboard. Their Figma exports are reference only, and both
  pages stay v1 (§3.4 records how they will reuse this work).
- Any change to the `ckanext-requestdata` repo (view, actions, auth, model), and any other backend change.
- Pagination, filters on this page, new analytics events and new tests.
- The requester-side "Request data access" flow (task 061).

**Figma sources** (in `ckanext-hdx_theme/llm_docs/redesign/figma_exports/`):
- Primary: `xl-user-dashboard-hdx-connect-requests.html`, `sm-user-dashboard-hdx-connect.html`.
- Reference only: `xl-org-page-requested-data.html`, `sm-org-page-requested-data.html`,
  `xl-sysadmin-hdx-connect-dashboard.html`.

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `EXT` = `src/ckanext-requestdata/ckanext/requestdata` (separate repo `OCHA-DAP/ckanext-requestdata`, pinned tag `3.0.42`)
- `USERS` = `ckanext-hdx_users/ckanext/hdx_users`

---

## Context

**This page is the maintainer's inbox, not the requester's list of sent requests.**
- `request_list_for_current_user` (EXT `logic/actions.py`) lists every request on public, active HDX Connect datasets
  whose `maintainer` is the current user (`fq=maintainer:{user_id} extras_is_requestdata_type:true`).
- The Figma subtitle says the same: "Respond to or decline restricted dataset access requests from other users".
- Requesters cannot see their own outgoing requests anywhere in HDX.

**The page still renders the v1 chain:**
- HDX core's override `THEME/templates/requestdata/my_requested_data.html` → `user/dashboard.html` (BS5 tab bar) →
  core `user/edit_base.html` → v1 `page.html`.
- Reply and Decline open Bootstrap modals; Yes / No and the archive collapse depend on Bootstrap JS.

**Figma moves the page onto the 072 shell:**
- New / Open / Archive sections of request cards grouped per dataset.
- A per-request footer bar with the actions.
- A compact Archive grid.

Every decision in this document was confirmed with the user; see §8.

---

## 1. Overview & Scope

| | |
|---|---|
| Target | `requestdata.my_requested_data` (`/user/my_requested_data/<id>`). The page is reached from the 072 left nav item `hdx_connect_requests`, the header user menu, the v1 dashboard tab and the bell notification |
| Objective | v2 page on `v2/user-dashboard-base.html` with Figma's layout, with every v1 behaviour preserved: endpoints, payloads, auth, `order_by` URLs and reload-on-success |
| Strategy | **Direct replacement** of the HDX core override (no `?v2` gate, as in 072/073). The extension repo and its view are untouched |
| Shared work | The request components and the list-header and filter-overlay snippets are built so the org and sysadmin requests pages can adopt them later |
| Reference exports | The org and sysadmin exports confirm that the card, request row, footer, chips and Archive grid are identical across the three views (§3.4) |

---

## 2. Audit Findings & Current State

### 2.1 Routes, blueprints and auth

**Which code wins:**
- Templates are searched hdx_users → hdx_theme → requestdata (`IConfigurer` uses reverse plugin order), so the HDX
  overrides win.
- The blueprints don't clash. The extension's `requestdata` blueprint and HDX's `hdx_requestdata_user` blueprint
  register different routes.

| Endpoint | URL | Notes |
|---|---|---|
| `requestdata.my_requested_data` | `/user/my_requested_data/<id>` (GET) | EXT `views/user.py` `my_requested_data`. Reads only `order_by` |
| `hdx_requestdata_user.handle_new_request_action_reply` / `_reject` | `.../<username>/reply`, `.../<username>/reject` (POST) | USERS `views/requestdata_user_view.py` `handle_new_request_action`. Returns JSON |
| `requestdata.handle_open_request_action_shared` | `.../<username>/shared` (POST) | EXT `handle_open_request_action`. Returns JSON. Serves both Yes and No |
| `requestdata_organization_requests.requested_data` | `/organization/requested_data/<id>` | Org page (reference). Filter `filter_by_maintainers=org:<org>\|maintainers:<u1,u2>` |
| `requestdata_ckanadmin.requests_data` | `/ckan-admin/requests_data` | Sysadmin page (reference). Filter `filter_by_organizations=<o1,o2>` |

- The `<username>` path segment is ignored by every action handler. Authorisation comes from `requestdata_request_patch`.
- **Page auth:**
  - Anonymous users get **403** "Not authorized to see this page." (no login redirect).
  - Another user's id gets the same 403, and so does a sysadmin viewing someone else (`g.is_myself = id == g.user`).
- **Side effect:** each page view calls `requestdata_notification_change`. Nothing visible in HDX reads the flag it sets.

### 2.2 Data passed to the template

The view passes `requests_new`, `requests_open`, `requests_archive` and `current_order_name`. It does **not** pass
`user_dict`.

**Request item fields:**
- `id`, `sender_name`, `sender_user_id`, `email_address`, `message_content`, `package_id`, `state`, `data_shared`,
  `rejected`, `created_at`, `modified_at`
- `extras`: a JSON string, read in v1 with `h.load_json(item.extras)`. Keys: `country`, `organization_id`,
  `organization_name`, `organization_member`, `organization_type`, `intend`.
- Added by the view: `title`, `maintainers`.

**Archive group fields** (one per dataset):
- `package_id`, `title`, `requests_archived`
- `requests`, `replied`, `declined`, `shared`: **lifetime** per-dataset counters from `ckanext_requestdata_counters`, not
  counts of the archived items.

**Sort:** `find_archived_sorting_params` + `sort_archived` (EXT `view_helper.py`) sort the Archive groups only. New and
Open are always `modified_at desc`.

| `order_by` | Label |
|---|---|
| `most_recent` (default) | Most Recent |
| `asc` | Alphabetical (A-Z) |
| `desc` | Alphabetical (Z-A) |
| `requests` | Requests Rate |
| `shared` | Sharing Rate |

- Any other value gives a 500 when archived groups exist.

**Limits:**
- No pagination and no filtering.
- The underlying `package_search` is silently capped at `ckan.search.rows_max` (1000).

### 2.3 State machine and actions

| Transition | Trigger | Who | Side effects |
|---|---|---|---|
| → `new` | Requester submits `/dataset/<id>/request-access/` | Any logged-in user | `requests` +1. Emails to the maintainer / org admins and to the requester |
| `new` → `open` | **Reply** | Package creator, maintainer or org admin; sysadmins bypass (`_user_has_access_to_request`) | Approval emails. `replied` +1 |
| `new` → `archive`, `rejected=True` | **Decline** | Same | Rejection emails. `declined` +1 |
| `open` → `archive`, `data_shared=True` | **Yes** | Same | `shared` +1 |
| `open` → `archive`, `data_shared=False` | **No** | Same | `declined` +1 ("No" is counted as Denied) |
| `new` / `open` → `archive`, shared | Dataset made public | `package_update` | Auto-approval emails |

- Reopen exists in the extension but is commented out in the HDX archive snippet, so the UI can't reach it.

**POST payloads** (from `section_item_new.html` / `section_item_open.html`); these must be sent unchanged:

| Action | Fields |
|---|---|
| Reply | `id`, `package_id`, `state='open'`, `send_to`, `package_name`, `maintainers`, `requested_by`, `sender_id` + `message_content` + `email` |
| Decline | `id`, `package_id`, `state='archive'`, `rejected=True`, `send_to`, `package_name`, `maintainers`, `requested_by`, `sender_id` + `message_content` |
| Yes / No | `id`, `package_id`, `state='archive'`, `data_shared=True` / `False` |

**JSON responses:**
- Success: `{success: true}`.
- Failure: `{success: false, error: {fields: {...}}}`. A missing message returns `{error: {message_content: 'Missing value'}}`.
- An invalid reply email gives `fields.email` = "The email you provided is invalid."

### 2.4 v1 rendering

| Part | v1 |
|---|---|
| Chrome | Breadcrumb Home > Dashboard, "User Dashboard" heading, BS5 `nav-tabs` (Newsfeed, My Datasets, My Organisations, My Locations, HDX Connect Requests) plus a sysadmin "More" dropdown |
| Header | `requests_header.html`: "My Requests [N]", where N = new + open only (`total_archived_requests` is undefined) |
| Sections | EXT `section_base.html`: "New [n]", "Open [n]", "Archived [n]" (n = dataset groups for Archived), with "Requested by:" / "Actions" column labels. Empty section: "No requests found." |
| Requested-by | `requested_by_container.html`: name linked to `user.read`; "located in {country}, from {org} - {org type}" (org linked when `organization_id != organization_name`; type from `h.hdx_organization_type_get_value`); "(Unverified ⚠ - this user is not a member of this organization on HDX)"; "Intended use: {intend}"; "Requested on {created_at}"; the message |
| New item | Dataset title link, requested-by, **Reply** (`hdx-modal-form` → `ajax_snippets/reply_request_form.html`) and **Decline** (`reject_request_form.html`) |
| Reply modal | Request summary (dataset, requested by, maintainer, "{name} wrote:" + message), "Reply to this request", guidance copy, "Your response" textarea, email prompt, "Your email" (prefilled), Cancel / "Send reply". Submit stays disabled until the fields are filled |
| Decline modal | "Decline the request", "Explain why you can't share the requested data", the tracking note, "Your message", Cancel / "Send" |
| Open item | "Keep track of who you share data with. Did you share the data?" with **Yes** / **No** (`handle-open-request`, AJAX, then reload) |
| Archive group | Title link; "{n} Requests / Replied / Denied / Shared" counters; chevron + BS collapse. Each archived request shows "Request Denied ({modified_at})", or "Request Replied ({modified_at})" followed by "Data Shared" / "Data Not Shared" |
| Order | EXT `order_requests.html` BS dropdown "Order by:", shown only when Archive is non-empty |

**v1 defects that disappear with the rewrite:**
- `handle-open-request` errors are hidden behind `d-none`.
- The archive chevron never rotates.
- Modals stay in the DOM after use.

### 2.5 Assets

- **Styles:** `requestdata/main-styles` and `hdx_theme/requestdata-styles`.
- **Scripts:** `requestdata/modal-form-scripts`, `hdx_theme/requestdata-scripts`, `requestdata/section-item-scripts`
  and `requestdata/handle-open-req-scripts`, loaded per item.
- **Bootstrap:** the modal, collapse and dropdown JS plus grid classes.
- None of these are needed on the v2 page.

### 2.6 Analytics, entry points, tests

- **Analytics:** nothing page-specific. The generic Mixpanel page view sends `pageTitle` `' None '` (the subtitle block is
  empty). No action fires an event.
- **Entry links:**
  - 072 nav item `hdx_connect_requests` (`h.hdx_get_user_dashboard_nav_sections`), also used by the v2 header user menu;
  - the v1 `user/dashboard.html` tab and `header-global.html`;
  - `light/notifications/requestdata_snippet.html` ("...by visiting the My Requests page", in both the v2 and the v1
    branch).
- **Tests:** no test loads this page, and `test_page_load.py` has no requestdata rows.

### 2.7 Reusable v2 pieces

| Piece | Fit |
|---|---|
| `v2/user-dashboard-base.html` (072) | Shell, nav (`user_nav_active`), breadcrumb, `subtitle` from `page_label`. Its `subtitle` block reads `user_dict.display_name`, which this view doesn't pass |
| `c-avatar` size `md` | 40px, brand-15 background / brand-7 initials: an exact Figma match |
| `c-label` size `xs` | `grey` / `cyan` / `yellow` / `dark` match Figma's chips. `attrs` / `extra_classes` let a chip act as a tooltip trigger |
| `c-button` primary size `s` | 4/8px padding, 12px text, 14px icon: an exact match for Reply |
| `c-text-button` size `s` | 12px with underline: an exact match for Decline |
| `c-drawer` + `.c-drawer-form` | Focus trap, Escape, `window.hdxV2Drawer(id)`. `v2/group-message-drawer.html` and `group-message-drawer.js` are the closest AJAX drawer precedent |
| `c-tooltip-anchor` + `c-tooltip` | Composition pattern of `v2/components/info-icon.html`. Non-button triggers: focusable spans (`tabindex="0"` + `aria-describedby`) in 063's `v2/completeness-item.html` and `data-grid-status.html` |
| `clamped-text.js` | Show more / Show less clamp used by the dataset and org cards |
| `v2/search-nav-controls.html` + `url-nav.js` | Navigate-on-select sort. Its URL key is hard-coded to `sort` |
| `hdx-v2-list-header` | Markup inline in the v2 branch of `search/snippets/package_list.html`: title + count (073's `--dashboard` modifiers), XL `__controls`, MD/SM `__filter-btn`, `__subtitle` |
| `#hdx-filter-overlay` | Markup inline in `search/snippets/package_list.html`. The "FilterOverlay init" block in `fanstatic/v2/pages/search.js` only needs the overlay element and `[data-module="filter-btn"]` |
| `<details>/<summary>` row | `v2/completeness-item.html` (063): a summary row with per-column values, plus a native disclosure |

---

## 3. Figma Design Export Analysis

### 3.1 XL (`xl-user-dashboard-hdx-connect-requests.html`)

**Breadcrumb and left nav:**
- Breadcrumb: Home / "Account and Settings" / HDX Connect Requests. The middle label is an export inconsistency; the SM
  export says "Activity & Content", which is the item's 072 group.
- Left nav: white 14.063rem column with the 072 groups. "HDX Connect Requests" is active (4px primary-5 underline).

**Header:**
- `content` padding 32 / 48 / 48 / 40.
- H1 "HDX Connect Requests": Merriweather 24px bold.
- A count "28" exists but is hidden (`display:none`).
- Subtitle: 14px, neutral-85, 6px below the title.
- Right side: "Sort by" (14px, neutral-8) and a select: 12px medium, padding 6/8/6/10, neutral-2 border, shadow-sm,
  radius 2, label "Most Recent".

**Sections:**
- 24px apart. Each heading is "New" / "Open" / "Archive" (Merriweather 18px bold) plus a count (Roboto 16px, neutral-8),
  8px apart.
- 16px from heading to list; 24px between cards.

**Dataset group card:**
- 1px neutral-1 border, white background.
- Header padding 16: title (Roboto 18px semibold, neutral-95), then "Maintained by **username**" (14px; username medium,
  underlined), 8px gap.

**Request row** (border-top neutral-1, padding 16, 16px gap):

| Part | Spec |
|---|---|
| Avatar | 40px circle, initials |
| Requester line | Name (14px medium, underlined) + "· West Yangon Technological University · Myanmar" (neutral-85) |
| Chips | 12px, radius 4, padding 2/4, 8px gap. Org type (neutral-1 bg, neutral-95). Verified (brand-1 / brand-85 + `info-circle` 12px). Unverified (warning-1 / warning-8 + `info-circle`) |
| Date | "Requested date: 4 May 2026" (12px, neutral-8) |
| Message | Quote with a 2px neutral-1 left border, padding 8/24, 14px, neutral-85 |

**Footer bar** (neutral-1 background, padding 12, 16px gap, 12px neutral-8 text):

| Section | Content |
|---|---|
| New | "Intended use: Academic" (semibold, flexible), **Reply** (primary, 4/8px, 14px icon), **Decline** (12px medium, underlined, neutral-95) |
| Open | "Did you share the data?" + **Yes** / **No** (neutral-01 background, 1px neutral-95 border, 4/8px, 12px medium), 8px gap |

**Archive:**
- Bordered box with a header row (padding 8/16, 12px neutral-8): Dataset (32rem) | Requests | Replied | Denied | Shared.
- Rows: border-top, padding 8/16. Title 14px medium underlined with ellipsis; counts 16px medium neutral-8.
- The expanded state (an `open-card`, hidden in the export) lists archived requests on neutral-05.
  - Footer: "Intended use: Academic" "(25 March 2026)" plus one chip.
  - "Data Shared": brand-1 / brand-85.
  - "Request Denied": warning-1 background / error-5 text. That is **4.12:1**, which fails WCAG AA for 12px text.

**Hidden in the export:** a "Closed 12" section, "Results per page", the title count and a collapse chevron.

### 3.2 SM (`sm-user-dashboard-hdx-connect.html`)

- **Breadcrumb:** padding 8/16; "Home / Activity & Content / HDX Connect Reque…" (ellipsised).
- **Content:** padding 24/16, 24px gap. Title (24px) + subtitle.
- **Extra block:** a "Requested Data 13" heading (Merriweather 20px) and a "Filter (10)" button (neutral-01 background,
  1px neutral-95 border, 16px icon, blue count). This block is structurally identical to `sm-org-page-requested-data.html`.
- **New section only:** full-width cards (22.687rem frame). The footer bar stays on one row.
- **Pager:** 1 2 3 … 31.
- **Hidden:** a dashboard sub-menu dropdown (`anchor-nav`) and a "You might also like" block.

### 3.3 XL vs SM differences

| Aspect | XL | SM |
|---|---|---|
| Left nav | Visible | None (the sub-menu is hidden) |
| Sort | "Sort by" in the header | None visible; a "Filter (10)" button instead |
| Extra heading | — | "Requested Data 13" (copied from the org SM) |
| Sections shown | New, Open, Archive | New only (the export is truncated) |
| Pagination | None | 1 2 3 … 31 |
| Cards | Fixed 60.563rem | Full width; same internals and footer row |

### 3.4 Cross-page consistency (reference exports)

| View | Layout | Filters | Sort |
|---|---|---|---|
| User XL | 072 nav, header, sections | None | Header "Sort by" |
| Org XL (`xl-org-page-requested-data.html`) | Org hero + tabs (Requested Data active), "Requested Data 13" | Left "Filter by": Organisation (fixed to the current org, disabled look) + Maintainer ("All maintainers") | Header "Sort by" |
| Org SM | Hero + tabs, "Requested Data 13" + "Filter (10)", New cards, pager | In the Filter button | — |
| Sysadmin XL (`xl-sysadmin-hdx-connect-dashboard.html`) | Sysadmin nav, "HDX Connect Dashboard 2801" + "Review and manage HDX Connect requests across all organisations" + a "Download" dropdown; one block per organisation ("i3S 13", "CCCM Cluster Somalia 26"), each with sections | Right "Filter by": Organisation + Maintainer | Per organisation block |

- The dataset card, request row, chips, footer bar, Yes / No prompt and Archive grid are **identical** in all three
  views (only the widths differ), so they are built as shared components (§5).
- **Non-binding note for the future org and sysadmin tasks:**
  - Their filters (Maintainer, Organisation) should reuse Search's Filter pattern: an XL filter column, the MD/SM Filter
    button, the shared `v2/filter-overlay.html`, and checklist dropdowns.
  - They should keep v1's `filter_by_maintainers` / `filter_by_organizations` URLs.
  - Their own requirements decide the details.

### 3.5 Token mapping (every Figma value has an exact token)

| Figma | Token | Used for |
|---|---|---|
| `#fafbfb` | `--hdx-neutral-01` | Canvas |
| `#f5f7f7` | `--hdx-neutral-05` | Archived request rows |
| `#ebeff0` | `--hdx-neutral-1` | Borders, footer bar, org-type chip (`c-label` grey) |
| `#d8e0e1` | `--hdx-neutral-2` | Select border; `c-label` dark |
| `#3f4748` | `--hdx-neutral-8` | Meta text, counts |
| `#2f3536` | `--hdx-neutral-85` | Subtitle, org/country, message |
| `#101212` | `--hdx-neutral-95` | Titles, names |
| `#1862d8` | `--hdx-primary-5` | Reply button, active nav |
| `#d4eae4` / `#0b2d24` | `--hdx-brand-1` / `--hdx-brand-85` | Verified, Data Shared (`c-label` cyan) |
| `#bee0d6` / `#18614c` | `--hdx-brand-15` / `--hdx-brand-7` | Avatar (`c-avatar`) |
| `#f6e9d4` / `#553911` | `--hdx-warning-1` / `--hdx-warning-8` | Unverified (`c-label` yellow) |
| `#c44536` | `--hdx-error-5` | Figma's "Request Denied" text (not used: Q10) |

---

## 4. Current vs Target Gap Analysis

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, "User Dashboard" heading | 072 base + left nav (XL) | Q1 |
| Breadcrumb | Home > Dashboard | Home / Activity and Content / HDX Connect Requests (from the base) | derived |
| `<title>` | "HDX" (empty subtitle) | "HDX Connect Requests \| {name} \| Users" | derived |
| Title | "My Requests [N]" | H1 "HDX Connect Requests" + count (New + Open) + Figma subtitle | Q24, Q40 |
| Section names | New / Open / Archived | New / Open / Archived, each with a count | Q38 |
| Empty section | "No requests found." | Same copy, v2 styling | Q23 |
| Dataset group | `h4` link + inline-styled BS rows | `c-request-card` per dataset (New / Open grouped in the template); title link kept; "Maintained by" hidden here | Q2, Q20, Q35, Q45 |
| Requester block | Sentence "located in…, from… - type" | `c-request-item`: avatar, "Name · Org · Country", chips, "Requested date: …", clamped quote | Q21, Q22, Q25, Q46 |
| Verification | "(Unverified ⚠ …)" sentence | Verified / Unverified chips with a tooltip | Q21, Q41 |
| Reply / Decline | BS5 modals loaded via `api/1/util/snippet` | Two shared `c-drawer`s + page JS, same endpoints and payloads | Q3, Q26 |
| Yes / No | `a.btn` + `handle-open-request` | `c-button` tertiary s + page JS, same endpoint and payloads | Q28 |
| Archive | Counters + chevron + BS collapse | `c-request-archive` `<details>/<summary>` grid; no title link | Q4–Q10, Q42, Q43 |
| Sort | BS dropdown above Archive | Inline in the Archive heading row at every width | Q11, Q62 |
| Assets | v1 requestdata bundles, Bootstrap JS | Components + `v2-hdx-connect-page-styles` / `-scripts` (with `url-nav.js`) | Q17, Q65 |
| Notification copy | "My Requests page" | "HDX Connect Requests page" | Q33 |

- **Preserved:** every endpoint, POST field, auth rule and 403; the `order_by` URLs; reload on success; the
  "No requests found." copy; the lifetime counters; the 1000-row cap; the notification side effect.
- **Removed:** the BS markup and inline styles, `fa` icons, Bootstrap modal / collapse / dropdown usage, the v1 bundles
  on this page, and the "Requested by:" / "Actions" column labels.
- **New:** the Verified chip, the message clamp, the request summary in the drawers, and the title count (computed in the
  template).

---

## 5. Component System Mapping

### 5.1 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, nav, breadcrumb, `<title>` | `v2/user-dashboard-base.html`, `user_nav_active='hdx_connect_requests'`, `page_label=_('HDX Connect Requests')` | Reuse | Q1 |
| Header | **New shared snippet** `v2/list-header.html`, extracted from `package_list.html`'s v2 header; here `title_tag='h1'`, `title_size='dashboard'`, no controls | Share (extraction) | Q24, Q40 |
| Dataset group | `v2/components/request-card.html` → `c-request-card` | **Share (new)** | Q2 |
| Requester row | `v2/components/request-item.html` → `c-request-item` | **Share (new)** | Q2 |
| Archive grid | `v2/components/request-archive.html` → `c-request-archive` + `request-archive-row.html` | **Share (new)** | Q34 |
| Avatar | `c-avatar` `md` | Reuse | — |
| Chips | `c-label` `xs`, existing colours only (§5.3) | Reuse | Q10, Q21 |
| Tooltip | `c-tooltip-anchor` + dark `c-tooltip` around a `c-label` span made focusable via `attrs` (`tabindex='0'`, `aria-describedby`) + `extra_classes='c-tooltip-trigger'` (063 pattern) | Reuse | Q21, Q41 |
| Reply | `c-button` primary `s`, `icon_src='v2/icons/reply.svg'` | Reuse | Q27 |
| Decline | `c-text-button` secondary `s`, `tag='button'` | Reuse | — |
| Yes / No | `c-button` tertiary `s` | Reuse | Q28 |
| Reply / Decline forms | `c-drawer` + `.c-drawer-form`, `text-field` (`multiline=True`), `c-alert` (hidden until error), `c-button` | Reuse | Q3, Q26 |
| Message clamp | `clamped-text.js` contract (`data-module="clamped-text"`, `[data-clamped-content]`, `[data-clamped-toggle]` text-button), 3 lines. Inside a closed `<details>` (Archive) the script measures on the first open | Reuse + extend | Q25, Q49, Q50 |
| Sort | `v2/search-nav-controls.html` with a **new `sort_key` param** | Extend | Q29 |
| Section headings, Archive heading row | `v2/list-header.html` with `title_tag='h2'`; its default `title_size='section'` is `.hdx-section-title()` + `.hdx-section-title-count()` (not Figma's 18px bold heading and Roboto count). Archived passes the sort as its controls | Reuse | Q39, Q47 |
| Mapping and drawers markup | Flat in `THEME/templates/v2/`, like `v2/group-message-drawer.html` | New page snippets | Q44 |

**Why new components.** No existing card fits:
- `c-member-list-card` (avatar + name + actions) has no chips, message, date or footer bar.
- `c-dataset-card` is a search result.
- `c-accordion` takes plain-text questions and FAQ styling (Q5).

The three Figma views render the same request UI, so components (not page markup) avoid three copies.

### 5.2 Proposed component APIs

Each snippet gets the standard header comment, takes
`extra_classes`, and is added to `v2/components.html`.

**`request-card.html` → `c-request-card`** (dataset group)

| Param | Type | Notes |
|---|---|---|
| `title` | string | Dataset title (`<h3>`) |
| `title_href` | string | Dataset URL. The title is a link styled like the `c-dataset-card` title link: no underline at rest, underline on `:hover`, focus ring (Q35) |
| `maintainer_label`, `maintainer_href` | string | "Maintained by {label}" line (`c-text-link` secondary `s`), rendered only when `maintainer_label` is set. This page doesn't pass it (Q20, Q48) |
| `caller()` | block | One or more `c-request-item`s |

The list wrapper is `c-request-card-list` (24px gap), in the component's own LESS.

**`request-item.html` → `c-request-item`** (one request)

| Param | Type | Notes |
|---|---|---|
| `avatar_initials` | string | From `sender_name` (the first letters of its first two words) |
| `name`, `profile_url` | string | The name links to `user.read` (`sender_user_id`); `c-text-link` secondary `s` |
| `org_name`, `org_href` | string | `org_href` only when `organization_id != organization_name` (v1 rule). The link is styled like the name (underlined), Q46 |
| `country` | string | |
| `org_type` | string | Label from `h.hdx_organization_type_get_value(extras.organization_type)`. `grey` chip |
| `verified` | bool / None | `True` → Verified (`cyan`), `False` → Unverified (`yellow`), `None` → no chip |
| `tooltip_id` | string | Unique id for the Verified / Unverified tooltip |
| `requested_date` | string | Pre-formatted `created_at` |
| `message` | string | Clamped `<blockquote>` (3 lines, “ ” quote marks via CSS, Q58), Show more / Show less |
| `intended_use` | string | "Intended use: {intend}" |
| `status`, `status_date` | dict / string | Archived rows only: `{text, color}` chip plus "({modified_at})" after the intended use |
| `variant` | string | `'default'` (white) or `'archived'` (neutral-05 body) |
| `caller()` | block | Optional footer actions (Reply / Decline, or the Yes / No prompt) |

- The footer bar renders the intended use on the left (archived: then "({modified_at})" and the status chip, the Figma layout of Q42) and the `caller()` actions on the right. `__actions-group` holds controls that sit 8px apart (the Open prompt + Yes / No).
- When `extras` is missing (older requests), the org / country part, the chips and the intended use are omitted, as in v1.

**`request-archive.html` → `c-request-archive`** (grid container) and **`request-archive-row.html`** (one dataset row)

| Part | Spec |
|---|---|
| Container | Bordered box with a visual column header row "Dataset · Requests · Replied · Denied · Shared" (`aria-hidden="true"`); `caller()` holds the rows |
| Row | Native `<details>` (collapsed by default, rows independent) |
| `<summary>` | Leading `chevron-right.svg` (`aria-hidden`, rotates 90° on `[open]`) + **plain-text** title (no link, no underline, Q9, Q55) + 4 counts. Its `aria-label` reads "{title}, 10 requests, 9 replied, 1 denied, 3 shared" (Q60). The count labels show below MD only (§7.1, Q43) |
| Row params | `title`, `requests`, `replied`, `declined`, `shared`; `caller()` = the archived `c-request-item`s (`variant='archived'`) |

- This reuses the `<details>/<summary>` mechanism, not the `c-accordion` component (Q5). The precedent is
  `v2/completeness-item.html` (063).

### 5.3 Chip colour map (no new `c-label` variant, Q10)

| Chip | Variant | Where |
|---|---|---|
| Org type | `grey` | Request body |
| Verified | `cyan` + `info-circle.svg` | Request body |
| Unverified | `yellow` + `info-circle.svg` | Request body |
| Data Shared | `cyan` | Archived footer bar |
| Data Not Shared | `dark` (neutral-2: visible on the neutral-1 footer bar, unlike `grey`) | Archived footer bar |
| Request Denied | `yellow` (Figma's error-5-on-warning-1 is dropped because it fails AA) | Archived footer bar |

**Status rule** (v1 logic):
- `rejected` → Request Denied.
- Otherwise `data_shared` → Data Shared, else Data Not Shared.
- The date is `modified_at`.
- Status chips have no icon: Figma's ⓘ is dropped because no tooltip copy exists (Q42).

### 5.4 Shared changes outside the new components

| Change | Detail |
|---|---|
| `v2/search-nav-controls.html` | New optional `sort_key` (default `'sort'`, mirroring `page_size_key`) used for the sort dropdown's `data-nav-key`. Existing callers are unchanged |
| `v2/filter-overlay.html` (new) | `#hdx-filter-overlay` markup moved verbatim out of `package_list.html`: header "Filters" + close, body with `search-nav-controls` (`panel_suffix='ovl'`) + `[data-filter-panel-slot]`, footer "Clear filters" / "Show results". Params forward the nav-controls arguments (`sorting_selected`, `sorting_options`, `ext_page_size`, `admin_view`, `show_page_size`, `sort_key`) and `total_selected` (Clear button state). The id stays `hdx-filter-overlay` (`search.js` looks it up). `package_list.html` calls the snippet, and Search's HTML must stay byte-identical. Not used on this page (Q62); kept for the future org / sysadmin requests pages (§3.4) |
| `v2/list-header.html` (new) | `package_list.html`'s v2 header moved out: title + count, controls (`search-nav-controls`; `__controls--xl-only` when the Filter button renders, every width otherwise, Q63), MD/SM Filter button, subtitle. Params forward package_list's (`list_title`, `list_subtitle`, `title_tag`, `title_size`, `count`, the nav-controls arguments, `show_filters`, `total_selected`), plus `show_controls` to omit the controls. `package_list.html` calls the snippet; Search's HTML stays identical apart from the `--xl-only` class (Q40) |
| `fanstatic/v2/utils.js` | `window.hdxV2.setDisabled(el, disabled)` (button.html's disabled contract: `is-disabled`, `aria-disabled`, plus `[disabled]` on form controls or `tabindex="-1"` on links) and `window.hdxV2.showAlert(alertEl, text)`. They replace the local copies in `hdx-connect.js`, `group-message-drawer.js` (whose enabled Submit kept a stale `aria-disabled="true"`), `login.js`, `forgot-password.js`, `perform-reset.js`, `form-validator.js` and `locations-list.js` (Q66) |
| `LESS/mixins.less` | `.hdx-clamp-toggle(@toggle: ~'.c-text-button')`: hides the clamp toggle until `.is-clamped`, rotates its chevron on `.is-open`. Replaces the copies in `dataset-card`, `page-header`, `dataviz-card`, `org-list-card`, `resource-card` (scoped to its footer toggle, so the "Access via API" icon no longer rotates), `pages/dataset.less` and `request-item` (Q67) |

---

## 6. Functional & Business Rule Requirements

### 6.1 Backend

- **No view, action, auth or model change** in `ckanext-requestdata` or `ckanext-hdx_users`.
- The template gets exactly `requests_new`, `requests_open`, `requests_archive` and `current_order_name`.

### 6.2 Template

- Full replacement of `THEME/templates/requestdata/my_requested_data.html`, extending `v2/user-dashboard-base.html`.
- It sets `user_dict` from `g.userobj` (the base's `subtitle` needs `display_name`) along with `user_nav_active` and
  `page_label`.
- The shared v1 snippets (`requestdata/snippets/*`) and `ajax_snippets/*` are **not modified**: the org and sysadmin v1
  pages still use them.

**Layout, top to bottom:**
1. Header (`v2/list-header.html`): H1 + count (`requests_new|length + requests_open|length`) + subtitle "Respond to
   or decline restricted dataset access requests from other users".
2. New: heading "New" + request count; one `c-request-card` per dataset, holding one `c-request-item` per request with
   its Reply and Decline (Q45).
3. Open: heading "Open" + request count; cards grouped the same way, each request with "Intended use" (Q57) and
   "Did you share the data?" + Yes / No.
4. Archived: heading "Archived" (Q38) + group count, plus the inline sort (§6.5); then `c-request-archive`.

- New / Open grouping is done in the template by `package_id`, in first-appearance order: the card with the most recent
  request comes first, and requests keep the view's `modified_at desc` order. Jinja's `groupby` is not used (it sorts
  by key).
- An empty section keeps its heading (count 0) and shows "No requests found." in 072's `hdx-v2-user-dashboard-empty`
  (Q54).
- The two action drawers render once per page (from `templates/v2/`, Q44).

### 6.3 Copy

| Element | Copy |
|---|---|
| Requester line | "{name} · {org} · {country}" |
| Date | "Requested date: {created_at}" via `h.render_datetime(..., date_format='%-d %B %Y')` |
| Footer | "Intended use: {intend}" (New, Open); archived: "Intended use: {intend} ({modified_at})" + status chip |
| Message | The requester's text in “ ” (CSS, Q58) |
| Open prompt | "Did you share the data?" (Figma) |
| Verified tooltip | "This user is a member of this organization on HDX." |
| Unverified tooltip | "This user is not a member of this organization on HDX." |
| Empty | "No requests found." |
| Reply drawer | Title "Reply to this request". Request summary (dataset title, requester, quoted message). v1 guidance copy verbatim. "Your response" (`message_content`, required). Email prompt. "Your email" (`email`, required, prefilled with `c.userobj.email`). Cancel / "Send reply" |
| Decline drawer | Title "Decline the request". Request summary. "Explain why you can't share the requested data". The tracking note. "Your message" (`message_content`, required). Cancel / "Send" |

All strings go through `_()`.

### 6.4 Actions (new page script `fanstatic/v2/pages/hdx-connect.js`)

**Reply / Decline:**
- The buttons carry the v1 payload in `data-*` attributes (§2.3) plus the summary text. `maintainers` is sent as a
  JSON string (v1's FormData sent "[object Object]"; the handlers ignore it, Q52).
- The script fills the matching drawer (hidden inputs + summary) and opens it with `window.hdxV2Drawer(id).open()`.
- Submit stays disabled until the required fields are filled (v1 parity).
- On submit it POSTs `FormData` (payload + fields) with the CSRF header from
  `window.hdxUtil.net.getCsrfTokenAsObject()`, the one pattern across v2 JS (Q61):
  - Reply → `hdx_requestdata_user.handle_new_request_action_reply` (`username=c.userobj.name`)
  - Decline → `hdx_requestdata_user.handle_new_request_action_reject` (`username=c.userobj.name`)
- `success: false` shows the server messages (`error.fields.*`, `error.message_content`) in the drawer's `c-alert`.
- `success: true` reloads the page with no extra feedback (Q30).
- On `drawer:close`, the form and the alert reset.

**Yes / No:**
- POST `{id, package_id, state:'archive', data_shared}` to `requestdata.handle_open_request_action_shared`, then
  reload.
- On failure, show the page's one hidden `c-alert`, moved by JS under the failed request (v1's alert was invisible,
  Q53).
- No confirmation step (v1 parity).

**Shared rules:**
- Buttons are disabled while a request is in flight.
- No new analytics events (Q32).

### 6.5 Sort

- **Render condition:** sort renders **only when Archive has rows** (v1).
- **Sort control:**
  - `search-nav-controls.html` with `show_page_size=False` and `sort_key='order_by'`.
  - `sorting_selected = request.args.get('order_by') or 'most_recent'`.
  - `sorting_options` = the five v1 options (§2.2) as the snippet's `(label, value, short_label)` tuples, with labels
    and values unchanged (v1's label is also the trigger text). The control label is the snippet's "Sort by", not v1's
    "Order by" (Q51).
  - Selecting an option reloads with `?order_by=` (`url-nav.js`), so v1 URLs and bookmarks keep working.
- **Placement:** rendered once, in the Archived heading row, at every width (Q11, Q62). Narrow rows wrap it under the
  title, right-aligned (Q64). No Filter button or overlay on this page, as on the other sort-only pages.
- **No filters on this page** (Q12).

### 6.6 Assets

| Bundle | Contents | Notes |
|---|---|---|
| `hdx_theme/v2-hdx-connect-page-scripts` (new) | `v2/url-nav.js` (sort) + `v2/pages/hdx-connect.js` | As the other sort-only pages (`v2-org-list-page-scripts`, `v2-org-members-page-scripts`) (Q17, Q65) |
| `hdx_theme/v2-hdx-connect-page-styles` (new) | `pages/hdx-connect.css` (from `LESS/pages/hdx-connect.less`) | `<<: *common-css`, no preload |
| Component LESS | `request-card.less`, `request-item.less`, `request-archive.less` | Registered in `v2-components-styles` like every component |

- No v1 requestdata bundle and no Bootstrap JS dependency.

### 6.7 Analytics and notification

- **Analytics:**
  - No new events.
  - The generic Mixpanel page view's `pageTitle` changes from `' None '` to "HDX Connect Requests | {name} | Users"
    (accepted, as in 072 D13).
- **Notification:** in `light/notifications/requestdata_snippet.html`, the link text "My Requests" becomes "HDX Connect
  Requests" in **both** branches (the translated v2 branch and the untranslated legacy branch). The URL is unchanged.

---

## 7. Responsive & Accessibility Specifications

### 7.1 Breakpoints

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Nav | 072 sidebar (25%, sticky, `--xl-only`) | None (072 D15) | None |
| Content | Fluid column, Search content padding (no fixed Figma widths, 073 D3) | Full width, `space-8` vertical padding | Full width, `space-6` vertical padding |
| Header | H1 + count, subtitle | Same | Same |
| Sort | Inline in the Archive heading row | Same; wraps under the title, right-aligned, when narrow | Same as MD |
| Request card | Full column width | Same | Same. The footer row wraps (actions under the intended use) only when it doesn't fit (073 D20 precedent) |
| Archive grid | Title column flexible, 4 count columns | Same | Header row hidden; title on its own line (truncates), then the counts with visible labels: "10 Requests · 9 Replied · 1 Denied · 3 Shared" (Q43) |
| Pager / "Requested Data" / the "Filter (10)" button | — | — | Not rendered (not in v1; copied from the org export; Q62) |

### 7.2 Accessibility

**Structure:**
- One `<h1>` (the page title).
- `<h2>` for New / Open / Archived; `<h3>` for dataset titles in cards.
- The message renders in a `<blockquote>`.

**Archive rows:**
- Native `<details>/<summary>` gives the expanded / collapsed state for free.
- The `<summary>` contains no interactive content (Q9).
- The `<summary>`'s `aria-label` names the title and the labelled counts (Q60); the header row is `aria-hidden`; the
  chevron is `aria-hidden`.

**Chips and controls:**
- Verified / Unverified chips are focusable `<span>`s (`tabindex="0"`, browser-default focus ring, as on 063) with
  `aria-describedby` pointing at the tooltip (Q41). No colour-only meaning: the chip text carries it.
- Controls are native `<button>` / `<a>`, with the component focus rings (`.hdx-focus-ring()`).
- Hover uses CSS `:hover` only (no `is-hovered`). The clamp toggle exposes `aria-expanded`.

**Dialogs:**
- Drawers: `role="dialog"`, `aria-modal`, title-labelled, focus trap and Escape (`c-drawer`).
- Error messages use `c-alert` (`role="alert"`).

**Contrast:** all chip and text pairs pass AA:

| Pair | Ratio |
|---|---|
| warning-8 on warning-1 | 8.85:1 |
| brand-85 on brand-1 | 11.79:1 |
| neutral-8 on neutral-1 | 8.22:1 |

**Bootstrap:** no Bootstrap classes or data attributes anywhere on the page.

---

## 8. Open Questions & Recommendations

All questions were resolved with the user. The **User choice** column records each decision.

| # | Question | Options considered | Recommendation | User choice |
|---|---|---|---|---|
| Q1 | How to integrate with the separate extension | Core override (direct replacement) / template in the extension repo / `?v2`-gated copy | Core override | **Core override**: HDX templates already win the search path; the extension repo is untouched |
| Q2 | Where the request card UI lives | New shared components / page snippets + shared page LESS / extend `c-member-list-card` | New shared components | **New shared components** (`c-request-card`, `c-request-item`) |
| Q3 | Reply / Decline mechanism (endpoints return JSON) | Two shared drawers + page JS / one drawer per request / keep v1 BS modals | Two shared drawers | **Two shared drawers + page JS** |
| Q4 | Archive layout | Table + row disclosure / table only / v1 cards restyled | Table + disclosure | **Divs as in Figma, with a per-row disclosure** revealing archived requests with status chip + date |
| Q5 | Reuse the accordion? | Same mechanism, own markup / extend `c-accordion` / `c-accordion` as-is | Same mechanism, own markup | **Same mechanism, own markup** (063 precedent; `c-accordion` untouched) |
| Q6 | Disclosure control position | Leading chevron / trailing chevron / title as toggle | Leading chevron | **Leading chevron** |
| Q7 | Toggle mechanism | Native `<button>` + JS / `<details>/<summary>` / `div role=button` | `<button>` + JS | **`<details>/<summary>`** (CSS-only) |
| Q8 | Chevron icon | `chevron-right` rotated 90° / `chevron-down` rotated 180° | `chevron-right` | **`chevron-right`, rotated 90°** |
| Q9 | Dataset link in Archive rows (a `<summary>` can't contain links) | "View dataset" link in the panel / no link / keep the link (needs a JS button) | "View dataset" in the panel | **No dataset link** (accepted loss of v1's archive title link) |
| Q10 | Archive status chip colours | New `red` variant / Figma-exact variant (fails AA) / no new variant | New `red` | **No new variant**: Shared `cyan`, Not Shared `dark` (refined from `grey`, which is invisible on the bar), Denied `yellow` |
| Q11 | Sort placement at XL | Archive heading row / page header (Figma) / header + backend sort for all sections | Archive heading row | **Archive heading row**, only when Archive has rows |
| Q12 | Filters on this page | Sort only / add an Organisation filter | Sort only | **Sort only** |
| Q13 | MD/SM panel | Reuse `c-drawer` / Search filter overlay | `c-drawer` | **None**: the sort stays inline (Q62) |
| Q14 | MD/SM button | "Filter" in the page header / "Sort" in the Archive heading / "Filter" in the Archive heading | "Filter" in the header | **None** (Q62) |
| Q15 | Inline sort below XL | Hide / keep at all widths | Hide | **Keep at all widths** (Q62) |
| Q16 | Sort below XL, after clarifying Sort ≠ Filter | Inline in the Archive heading, no overlay / keep Filter button + overlay / "Sort" button → overlay | Inline | **Inline in the Archive heading, no overlay** (Q62) |
| Q17 | Script loading | Location / Crisis pattern / one own bundle / Org Members pattern | Location / Crisis | **Org Members pattern**: own bundle with `url-nav.js` (Q65) |
| Q18 | Overlay markup sharing | Extract a shared snippet / own markup with the same classes | Extract | **Extract `v2/filter-overlay.html` now** |
| Q19 | Overlay footer on this page | Omit / keep Search's footer | Omit | **n/a**: no overlay on this page (Q62) |
| Q20 | "Maintained by" (always the viewer here) | Hide on this page / show per Figma | Hide | **Hide on this page** (no `maintainer_label`, Q48) |
| Q21 | Verification rendering | Both chips + tooltip / both chips + hidden explanation / Unverified only | Both + tooltip | **Both chips + tooltip**; copy mirrors v1's sentence for each state |
| Q22 | Requester line and date wording | "Name · Org · Country" / "Name · Country, from Org" / v1 wording | "Name · Org · Country" | **"Name · Org · Country" + "Requested date: …"** |
| Q23 | Empty states | Sections + v1 copy / hide empty sections / headings only | Sections + v1 copy | **Sections + "No requests found."** |
| Q24 | Title count | None (Figma) / New + Open (v1) / total | None | **New + Open** |
| Q25 | Message length | Clamp + Show more / full text | Clamp | **Clamp + Show more** |
| Q26 | Drawer content | Summary + v1 copy + fields / v1 copy + fields | Summary + v1 copy + fields | **Summary + v1 copy + fields** |
| Q27 | Reply icon | `reply.svg` / `mail.svg` / none | `reply.svg` | **`reply.svg`** |
| Q28 | Yes / No style | Tertiary s / secondary s / new style | Tertiary s | **`c-button` tertiary s** |
| Q29 | Keeping `?order_by=` | `sort_key` param on `search-nav-controls` / direct `c-dropdown` | `sort_key` | **`sort_key` param** |
| Q30 | Success feedback | Silent reload / alert in the drawer then reload / alert after reload | Silent reload | **Silent reload** (v1 parity) |
| Q31 | Tests | Two page-load rows / none | Two rows | **No new tests** |
| Q32 | Analytics | No new events / add action events | No new events | **No new events** |
| Q33 | Notification copy "My Requests page" | Update / leave | Update | **Update to "HDX Connect Requests"** |
| Q34 | Archive grid location | Shared component / page markup | Shared | **Shared component** (`c-request-archive`) |
| Q35 | Card dataset title | Keep the link / plain text | Keep the link | **Keep the link** (`c-dataset-card` title style) |
| Q36 | Open prompt copy | "Did you share the data?" / v1 sentence | Figma | **"Did you share the data?"** |
| Q37 | Note on future org / sysadmin filters | Record a non-binding note / leave out | Record | **Record** (§3.4) |
| Q38 | Archived section heading (Figma "Archive" vs v1 "Archived") | "Archived" (v1) / "Archive" (Figma) | "Archived" | **"Archived"** (v1) |
| Q39 | Section heading type (Figma: 18px bold + Roboto 16px count) | `.hdx-section-title()` family / Figma exact | Section-title family | **`.hdx-section-title()` + `.hdx-section-title-count()`** (as Search / Org / Members) |
| Q40 | Header with the MD/SM Filter button beside the title | Extract `v2/list-header.html` / list-header classes inline / 072 header + `__count` | Extract | **Extract `v2/list-header.html`** from `package_list.html` (Search byte-identical), `title_size='dashboard'` |
| Q41 | Verified / Unverified tooltip trigger | Focusable span (063 pattern) / hover and tap only / native `title` | Focusable span | **Focusable `c-label` span** (`tabindex="0"`, `aria-describedby`, `c-tooltip-trigger`); not a `<button>`, no component change |
| Q42 | Figma's ⓘ on archived status chips | No ⓘ / ⓘ + tooltip with v1 wording / no ⓘ, date beside the chip | No ⓘ | **Figma layout, no ⓘ**: "Intended use: {intend} ({modified_at})" + plain status chip |
| Q43 | Archive grid at SM (no Figma) | Stack below MD / grid at all widths | Stack | **Stack below MD**: header row hidden, title line, then labelled counts |
| Q44 | Location of the page partials | Flat `templates/v2/` / `_v2` suffix beside v1 / `requestdata/snippets/v2/` | Flat `templates/v2/` | **Flat `templates/v2/`** (drawer precedent) |
| Q45 | New / Open card granularity | Group per dataset (Figma) / one card per request (v1) | Group | **Group per dataset** in the template, first-appearance order; heading counts stay request counts |
| Q46 | Requester org link style | Dataset-card org style (plain, underline on hover) / like the name / plain text | Dataset-card style | **Link styled like the requester name** (underlined) |
| Q47 | Section heading mechanism | Reuse `v2/list-header.html` / bespoke page-LESS heading rows | Reuse | **Reuse `v2/list-header.html`** (`h2`, Archived gets the sort) |
| Q48 | `show_maintainer` param on `c-request-card` | Drop it (line renders when `maintainer_label` is set) / keep | Drop | **Drop** |
| Q49 | Clamp inside a closed Archive `<details>` (measures 0×0 on load) | Extend `clamped-text.js` / no clamp on archived items / re-measure in page JS | Extend | **Extend `clamped-text.js`**: measure on the first open |
| Q50 | Message clamp length | 3 / 4 / 2 lines | 3 | **3 lines** |
| Q51 | Sort label (Figma / v2 "Sort by" vs v1 "Order by:") | "Sort by" / "Order by" | "Sort by" | **"Sort by"** |
| Q52 | `maintainers` POST value (v1 sends "[object Object]", unused) | JSON string / omit / literal v1 value | JSON | **JSON string** |
| Q53 | Yes / No failure alert position | One alert moved by JS / fixed under the Open heading / one per request | Moved by JS | **One alert, moved under the failed request** |
| Q54 | Empty section styling | 072's `hdx-v2-user-dashboard-empty` / compact page-LESS line | Reuse | **Reuse `hdx-v2-user-dashboard-empty`** |
| Q55 | Archive title underline (Figma underlines; Q9 made it plain text) | No underline / underlined | No underline | **No underline** |
| Q56 | Quote styling shared by the request item and the drawer summary | `.hdx-quote()` mixin / duplicate / plain text in the drawer | Mixin | **`.hdx-quote()`** (+ `.hdx-quote-marks()`) in `mixins.less` |
| Q57 | Open footer (Figma omits "Intended use") | Show intended use (v1) / omit (Figma) | Show | **Show "Intended use"** |
| Q58 | Quote marks around the message (Figma) | None (v1) / “ ” (Figma) | None | **“ ” via CSS** |
| Q59 | One Archive snippet instead of two | `rows` + `caller(row)` / keep two files | One file | **Keep two files** (`request-archive.html` + `request-archive-row.html`) |
| Q60 | Screen-reader text for the Archive counts, labels hidden from MD | `aria-label` on `<summary>` / `.sr-only` + un-hide / `.hdx-sr-only()` mixin | `aria-label` | **`aria-label` on `<summary>`**; labels `display: none` from MD |
| Q61 | CSRF header helper | Direct `hdxUtil` call / promote to `utils.js` / third local copy | Direct call | **Direct `window.hdxUtil.net.getCsrfTokenAsObject()`**, also replacing the copies in `group-message-drawer.js` and `org-members.js` |
| Q62 | Archived sort below XL (every other sort-only page keeps its sort beside its list) | Inline in the Archived heading at every width / second copy above the grid / "Sort" button → overlay / keep "Filter" in the header | Inline | **Inline at every width**; no Filter button or overlay on this page |
| Q63 | Keeping list-header controls visible below XL | Derive from `show_filters` / explicit param / CSS `:has()` | Derive | **Derive**: `__controls` visible at every width, `__controls--xl-only` when the Filter button renders |
| Q64 | Wrapped sort alignment on narrow screens | Right / left | Right | **Right-aligned** (`margin-left: auto`) |
| Q65 | Script bundles without the overlay | `url-nav.js` in the page bundle / keep `v2-search-page-scripts` | Page bundle | **`v2-hdx-connect-page-scripts` = `url-nav.js` + `hdx-connect.js`** |
| Q66 | Disabled-state and alert-message JS, copied in `hdx-connect.js` and 6 other v2 files | Promote to `utils.js` and use it in 074's two drawer scripts / leave as is / promote and replace every copy | Two drawer scripts | **Promote and replace every copy** (§5.4); the v1-bundled `hdx_signals.js` and `org-members.js`' variant-swapping alert stay as they are |
| Q67 | Clamp-toggle LESS block, copied in 7 files | Leave as is / `.hdx-clamp-toggle()` at every site / mixin for `request-item` only | Leave as is | **`.hdx-clamp-toggle()` at all 7 sites** (§5.4) |
| Q68 | `v2/filter-overlay.html` forwards `sorting_options`, `show_page_size`, `sort_key`, which no caller passes since Q62 | Keep / trim to `package_list.html`'s params | Keep | **Keep**: same set as `v2/list-header.html`, ready for the org / sysadmin pages |

**Derived decisions.** These were not asked separately; each follows a preservation rule or an existing precedent.
Raise any of them before implementation if they should change.

| Item | Resolution | Basis |
|---|---|---|
| `user_dict` | Set from `g.userobj` in the template | The base needs it; the view stays untouched (Q1) |
| Breadcrumb | Home / Activity and Content / HDX Connect Requests | The 072 base (072 D7); Figma SM |
| Archive heading count | Number of dataset groups | v1 and Figma |
| Archive rows | Collapsed by default, independent | v1 |
| Status date | `modified_at` | v1 |
| Reply / Decline submit | Disabled until required fields are filled | v1 |
| Page LESS / bundles | `pages/hdx-connect.less`, `v2-hdx-connect-page-styles`, `v2-hdx-connect-page-scripts` | Naming allows org / sysadmin reuse |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/requestdata/my_requested_data.html` | Full replacement: base, header, sections, archive, drawers, assets (Q1) |
| `THEME/templates/v2/hdx-connect-request.html`, `hdx-connect-drawers.html` (new) | Request-item mapping from the raw request dict (`h.load_json(item.extras)`) with the action buttons; the two drawers. The per-dataset grouping is in the page template (Q44, Q45) |
| `THEME/templates/v2/components/request-card.html` (new) | `c-request-card` (§5.2) |
| `THEME/templates/v2/components/request-item.html` (new) | `c-request-item` (§5.2) |
| `THEME/templates/v2/components/request-archive.html`, `request-archive-row.html` (new) | `c-request-archive` (§5.2) |
| `LESS/components/request-card.less`, `request-item.less`, `request-archive.less` (new) | Component styles, compiled to `fanstatic/v2/components/` |
| `LESS/pages/hdx-connect.less` (new) | Section stack, drawer request summary, Yes / No alert margin |
| `LESS/mixins.less` | `.hdx-quote()`, `.hdx-quote-marks()` (Q56, Q58); `.hdx-clamp-toggle()` (Q67) |
| `LESS/components/dataset-card.less`, `page-header.less`, `dataviz-card.less`, `org-list-card.less`, `resource-card.less`, `LESS/pages/dataset.less` | Clamp-toggle block replaced by `.hdx-clamp-toggle()` (Q67) |
| `LESS/pages/search.less` | `.hdx-v2-list-header__controls` visible at every width, right-aligned when wrapped; `--xl-only` modifier (Q63, Q64) |
| `LESS/components/dataset-card.less` | Title uses `.hdx-body-m-semibold()` like `c-request-card` (same output) |
| `THEME/fanstatic/v2/pages/hdx-connect.js` (new) | Drawers, Reply / Decline / Yes / No (§6.4) |
| `THEME/fanstatic/v2/components/clamped-text.js` | Measures inside a closed `<details>` on its first open (Q49) |
| `THEME/fanstatic/v2/group-message-drawer.js`, `THEME/fanstatic/v2/pages/org-members.js` | Local `csrfHeaders()` replaced by the direct `hdxUtil` call (Q61) |
| `THEME/fanstatic/v2/utils.js` | `window.hdxV2.setDisabled()`, `window.hdxV2.showAlert()` (Q66) |
| `THEME/fanstatic/v2/group-message-drawer.js`, `form-validator.js`, `pages/login.js`, `pages/forgot-password.js`, `pages/perform-reset.js`, `pages/locations-list.js` | Local disabled-state / alert code replaced by the `utils.js` helpers (Q66) |
| `THEME/fanstatic/webassets.yml` | Component CSS in `v2-components-styles`; new `v2-hdx-connect-page-styles` and `v2-hdx-connect-page-scripts` |
| `THEME/templates/v2/search-nav-controls.html` | `sort_key` param + header comment |
| `THEME/templates/v2/list-header.html` (new) | Header markup extracted from `package_list.html` (Q40) |
| `THEME/templates/v2/filter-overlay.html` (new) | Overlay markup extracted from `package_list.html` |
| `THEME/templates/search/snippets/package_list.html` | Calls `v2/list-header.html` and `v2/filter-overlay.html` (identical output apart from the `__controls--xl-only` class, Q63) |
| `THEME/templates/light/notifications/requestdata_snippet.html` | "My Requests" → "HDX Connect Requests" (both branches) |
| `THEME/templates/v2/components.html` | Demos for the three new components |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated-pages entries; PROGRESS bundle lists (component CSS, `utils.js` helpers) |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | `sort_key`; shared list-header and filter-overlay snippets; `c-request-card-list`; `setDisabled()` / `showAlert()` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/029-implement-dataset-card-component.md`, `038-resource-card.md` | Clamp-toggle CSS now via `.hdx-clamp-toggle()` (Q67) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/072-user-dashboard-my-organisations-v2.md` | HDX Connect Requests no longer listed as staying v1 |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/031-basic-filtering.md`, `034-dataset-header-v2.md`, `073-user-dashboard-my-datasets-v2.md`, `ckanext-hdx_theme/llm_docs/search-performance-plan.md` | The header and overlay now live in the shared snippets (Q18, Q40); 034's sort-panel anchoring note corrected |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 074 → `in_progress` / `implemented` |

---

## 10. Risks & Edge Cases

| Case | Handling |
|---|---|
| Header and overlay extraction touch the Search list (heavily crawled) | Pure moves; diff the rendered `/dataset` HTML before and after (identical apart from the `__controls--xl-only` class, Q63), as AGENTS.md requires for listing pages |
| `sort_key` change | Defaults to `'sort'`; Search, the org datasets tab, Members and My Datasets are unchanged |
| Invalid `order_by` | 500 when archived groups exist (v1 behaviour, view untouched) |
| Request without `extras` (older data) | No org / country / chips / intended use, as in v1 |
| Missing maintainer lookup (`maintainers` = `[None]`) | Irrelevant here: "Maintained by" is hidden |
| Up to 1000 requests, no pagination | Accepted (v1 parity). Only two drawers exist regardless of count (Q3) |
| Long dataset titles | Card title wraps; Archive summary title truncates with ellipsis |
| Long messages | Clamped with Show more (Q25). `clamped-text.js` labels are untranslated today (existing limitation) |
| Email or server error after the state change (v1 reply path) | Same as v1: the state may already be patched. Show whatever JSON or HTTP error comes back in the drawer `c-alert` |
| Counters incremented before the auth check; `organization_member` computed with an always-true generator in EXT `process_extras_fields` | Pre-existing EXT issues, out of scope. "Verified" shows whenever the chosen org resolves (normally one of the requester's own orgs) |
| Anonymous users | 403 (v1), not a login redirect. Unchanged |
| Chip semantics | Unverified and Request Denied share `yellow`; the text disambiguates (Q10) |

---

## Verification

**Access and rendering:**
- `/user/my_requested_data/<own name>` renders for a maintainer and for a sysadmin. Another user's id → 403; anonymous →
  403.
- Title count = New + Open. Sections show their counts, and "No requests found." when empty.
- New / Open requests are grouped per dataset, the card with the most recent request first.

**Actions:**
- Reply and Decline open the drawer with the request summary. Submit is disabled until the fields are valid.
- The POST fields match v1 exactly (§2.3). On success the page reloads and the request has moved (New → Open / Archive).
- Validation errors (empty message, invalid email) appear in the drawer `c-alert`.
- Yes / No archive the request with `data_shared` true / false.

**Archive:**
- Rows expand and collapse with the keyboard and mouse. Screen readers announce "{title}, N requests, N replied,
  N denied, N shared".
- Status chips follow §5.3.
- At SM the counts sit under the title with visible labels.

**Sort:**
- At every width the Archived heading's sort sets `?order_by=` and reorders the Archive; on narrow screens it wraps
  under the title, right-aligned.
- It doesn't render when Archive is empty.

**Regressions:**
- The rendered HTML of `/dataset`, the org datasets tab, Location and Crisis is unchanged.
- The Members tab and My Datasets sort still use `?sort=`.
- The bell notification link reads "HDX Connect Requests".
- No v1 requestdata bundle or Bootstrap JS loads on the page. There are no console errors at SM, MD, XL and XXL.
