# 073 — User Dashboard: My Datasets (v2 Migration)

**Scope:** `/dashboard/datasets` (HDX `hdx_user_dashboard.datasets`, which shadows core `dashboard.datasets` on
the same URL), on the shared v2 dashboard base from 072. Also in scope:
- a generic right-hand column block in `v2/page.html`;
- an Update status filter in the v2 filters;
- `labels` and actions extensions to `c-dataset-card`;
- a hash-open for the dataset page's group message drawer.

**Excluded:**
- Figma's Time period and Data type filters, deferred everywhere (031, 056 D12, 065).
- Figma's Advanced-filters chips: the shipped dropdown stays (065).
- Bulk actions, mark-as-fresh, and an archive endpoint.
- Downloads/trending, time period, location, formats and COD/COD+ badges on the card.
- Figma's white side panels and fixed 14rem widths.
- New tests.
- The remaining dashboard/settings siblings.

**Figma sources:** `xl-user-dashboard-my-datasets.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`.

---

## Context

The page still renders the v1 chain:
- `user/dashboard_datasets.html` → `user/dashboard.html` (BS5 tab bar) → core `user/edit_base.html` → v1 `page.html`;
- each row is the v1 admin row.

Figma moves it onto the 072 shell, with three changes:
- the filter panel moves to the **right** of the list, because the left column holds the dashboard menu;
- each dataset becomes a card with freshness chips and management actions;
- two actions are new: Archive and Send a group message.

Decisions confirmed with the user are listed in §8.

---

## 1. Audit Summary

### 1.1 Route and data
- Route: `datasets()` in `ckanext-hdx_users/.../views/dashboard.py`.
  - Login gate only: anonymous users get a flash and a redirect to `home.index`.
  - Passes `user_dict` and `search_data`.
- `DashboardDatasetLogic._fetch_dataset_search_results` (`controller_logic/dashboard_dataset_logic.py`):
  - `fq=maintainer:"<user id>"`, so the page lists datasets the user **maintains**, not ones they created. The
    `hdx_find_package_maintainer` validator accepts any org member (any role) or a sysadmin.
  - Default sort is `due_date asc`.
  - Private datasets are included (permission labels); drafts and deleted are excluded.
  - Archived datasets are hidden unless `ext_archived=1`. `ArchivedUrlHelper.redirect_if_needed` switches to the archived
    view when only archived results exist.
- `DashboardSearchLogic` (`controller_logic/dashboard_search_logic.py`) adds the `ext_update_status` facet
  (Needing update / Up to date / Unknown) and moves it first. Its items have the standard
  `name` / `display_name` / `count` / `selected` shape.
- Page size defaults to 10 (10/25/50/100).
- **Inbound link:** the expired-datasets notification (`notification_service.py`) links to
  `?ext_update_status=needs_update`.

### 1.2 Rendering (v1)
- `dashboard_datasets.html` calls `search/snippets/package_list.html` (v1 branch, `admin_view=True`, no
  `packages_count`), then `page.pager()`.
- **Row:** the v1 admin row, which extends `package_item.html`.
  - **Content:** private/archived/by-request icons, title, org link, downloads, time period.
  - **Due-date label:**
    - date from `h.hdx_get_due_overdue_date`, grey when `is_fresh`, orange when overdue;
    - hidden when `update_status == 'unknown'` or the date is ongoing (`h.hdx_is_ongoing_dataset_date`);
    - followed by "The dataset is up to date." / "…is due for update. Please edit dataset."
  - **Edit dataset:** `contributeAddDetails(id, 'dataset')`, with no permission check (the contribute view redirects
    unauthorised users).
  - **Delete dataset:**
    - gated on `check_access('package_delete')`, which core delegates to `package_update`;
    - the v1 `hdx_confirm-action` modal POSTs to `/dataset/delete/<id>` (`hdx_dataset.delete`);
    - that runs `hdx_dataset_purge`, a **hard purge** (files, datastore, DB row);
    - then flashes "Dataset has been deleted." and redirects to `dashboard.datasets`.
- v1 has no archive, group message, mark-fresh or bulk actions. Its "Add Dataset" block is dead.
- **Analytics:**
  - the generic Mixpanel page view (`pageTitle` "Manage – {name} – Users");
  - the `search` event: `number of results` is always 0 because `packages_count` isn't passed, and `ext_update_status` is unmapped;
  - no row tracking.

### 1.3 Reusable v2 pieces
- **072 base:** `v2/user-dashboard-base.html`.
  - The nav fills `secondary_content`, the **only** sidebar slot in `v2/page.html`.
  - Item id `my_datasets` already exists in `h.hdx_get_user_dashboard_nav_sections()`.
  - The base has no `scripts` block.
- **Search stack:**
  - `search_results_wrapper.html` (c-pagination);
  - `package_list.html` v2 branch: header plus `v2/search-nav-controls.html`, which already lists "Due for Update" under `admin_view`; also the search bar, chips, `#hdx-filter-overlay` and empty state;
  - `v2/search-filters.html` (its `filter_defs` are hard-coded) and `fanstatic/v2/pages/search.js`.
  - The Org, Location and Crisis pages use the same contract.
- **Card:** `c-dataset-card`, reached via `package_item_v2.html`.
  - Two columns: org, title and description on the left; location, date and formats on the right.
  - The description is hidden until "Show more" is clicked.
  - It has no chips slot and no actions slot.
- **Chips:** `c-label` `light`/`xs` and `yellow`/`xs` are an exact token match for Figma's chips.
- **Confirm pattern:** the org Members tab's per-item `c-drawer` + `.c-drawer-form` POST with `h.csrf_input()`, opened by
  `window.hdxV2Drawer(id).open()`.
- **Edit popup:** `contributeAddDetails(id, type, '#anchor')` (`fanstatic/v2/contribute.js`, on every v2 page) opens
  the contribute iframe at an anchor. The archive select is `#field_archived` in `contribute_flow/create_edit.html`.
- **Dataset group message:** `v2/group-message-drawer.html`, rendered by `page-header.html` as `gm-header-drawer` when
  `membership.display_group_message`. `group-message-drawer.js` (in `v2-page-scripts`) opens it from
  `#contact-members` and POSTs to `/membership/contact_members`; the server checks org membership.

---

## 2. Figma Design Analysis (XL)

- **Breadcrumb:** Home / Activity and Content / My Datasets.
- **Columns:** nav (14.063rem, white) | list | filters (14.063rem, white, padding 20/32/80).
- **Header:**
  - "My Datasets" (Merriweather 24px bold) + count "28" (Roboto 16px, `#3f4748`);
  - on the right: Results per page "10", Sort by "Last added";
  - below: "Datasets you own or manage" (14px, `#2f3536`), then a search input.
- **Card:** a `resource-card` layer, 736px, padding 16, gap 16.
  - **Top row:** the org name on the left. On the right, a light chip "Daily expected frequency update" and a yellow
    chip with a clock, "Update by Jun 1 2026".
  - **Body:** the title (16px semibold, 1 line), then "Show more" with a chevron.
  - **Footer:**
    - left: "Delete" (with icon) and "Archive" text-buttons;
    - right: "Send a group message" (secondary, size s, with icon) and "Update" (primary, size s);
    - the row wraps.
- **Pager:** 1 2 3 … 31.
- **Filters:** Location, Organisation, Time period, Data type, Format, Topics, Advanced filters (chips), Show only.
  There is no Update status filter.

---

## 3. Current vs Target

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar | 072 base + nav (D1) |
| Filters | Left facet sidebar | Right column via `tertiary_content` (D2, D3, D22) |
| Header | Archived tabs + search + sort + page-size radios | "My Datasets" h1 + count + controls, subtitle, search (D6, D7) |
| Update status | First facet | First v2 filter dropdown + chip (D5) |
| Sort | Due for Update default | Unchanged (D8) |
| Row | v1 admin row | Extended `c-dataset-card` (D9–D14) |
| Edit | "Edit dataset" link | "Update" button (D15, D19) |
| Delete | v1 modal | Per-card `c-drawer` (D16) |
| Archive | — | Edit popup at `#field_archived` (D17) |
| Group message | — | Link to the dataset page's drawer (D18, D19) |
| Pager | `page.pager()` | `c-pagination` via the wrapper (D4) |
| `<title>` | Manage \| {name} \| Users | My Datasets \| {name} \| Users (inherited from the base) |

---

## 4. Component & System Mapping

| Need | Mapping |
|---|---|
| Shell, nav, breadcrumb, `<title>` | Reuse `v2/user-dashboard-base.html` (`user_nav_active='my_datasets'`, `page_label=_('My Datasets')`) |
| Right column | **Extend** `v2/page.html` with `tertiary_content` + `tertiary_class`. The base sets `tertiary_class` (D2) |
| List, header, chips, overlay, pagination | Reuse `search_results_wrapper.html` → `package_list.html` v2 with new params (D4, D6) |
| Filters | Reuse `v2/search-filters.html` (+ Update status, D5) in `#search-page-filters-form` |
| Card | **Extend** `c-dataset-card` (`labels`, `caller()` actions) via `package_item_v2.html` under `admin_view` (D9–D11) |
| Chips | `c-label`: dark icon-only status badges, `light` frequency, `yellow`/`light` due with `v2/icons/time-clock.svg` |
| Actions | `c-text-button` (Delete with `delete.svg`, Archive/Unarchive); `c-button` tertiary s (`mail.svg`, `tag='a'`) and primary s |
| Delete confirm | `c-drawer` + `.c-drawer-form` (D16) |
| Group message | The dataset page's existing `gm-header-drawer` (D18) |

---

## 5. Functional & Preservation Rules

- **No view or backend change.** The following stay as they are:
  - the URL, login gate and maintainer `fq`;
  - the `due_date asc` default and the archived redirect;
  - every `ext_*` parameter and the 10/25/50/100 page sizes.
- **Deep link:** `?ext_update_status=needs_update` shows a checked dropdown and a removable chip.
- **Edit:** the same `contributeAddDetails(id, 'dataset')` call.
- **Delete:** the same `hdx_dataset.delete` POST, purge, flash and redirect. The flash renders as a v2 `c-alert`.
- **Analytics:** no new tracking. Two values change:
  - Mixpanel `pageTitle` (from the base, as in 072 D13);
  - the `search` event's `number of results`, which becomes correct now that `packages_count` is passed.
- **Assets:** the page adds `v2-search-page-scripts` in its own `scripts` block. No v1 bundle is added. The
  `dataset-search-scripts` load inside `package_list.html` already happens on every v2 search page and is unchanged.
- **Other pages:** every new param defaults off, so /dataset and the Org, Location and Crisis pages render as before
  (see §7 for the one card edge case).

---

## 6. Responsive & Accessibility

- **XL (≥ 80rem):**
  - Nav | list | filters, both side columns at 25% (D3).
  - Both side columns are sticky (`--sticky`), as on Search.
- **MD/SM (< 80rem):**
  - No nav (072 D15). The filter column is `--xl-only`.
  - `search.js` moves the form into `#hdx-filter-overlay`, opened by the list header's Filter button, which also
    carries sort and page size.
  - **Cards:** at every width, the chips wrap under the org name, left-aligned, when the top row doesn't fit (usual
    at XL, rare at MD). At SM the actions row also wraps, with the buttons on a second line, left-aligned (D20).
- **Accessibility:**
  - One `<h1>` (the list title). The filters sit in an `<aside>`.
  - Icon-only badges keep their `aria-label`.
  - Actions are native `<button>`/`<a>` elements with the component focus rings.
  - Focus handling and Escape come from `c-drawer`.

---

## 7. Risks & Edge Cases

| Case | Handling |
|---|---|
| Sysadmin maintainer who isn't an org member | "Send a group message" opens the dataset page, where no drawer renders. Accepted with D18 |
| Member-role maintainer | Update, Archive and Delete are hidden (D15) |
| Unknown frequency, ongoing date or no due date | No due chip (v1 parity). The frequency chip shows whenever a frequency is set |
| Archived view (Show only: Archived) | The Archive action reads "Unarchive" (D17) and there is no due chip (D13) |
| Search card with no location, date or formats | `__right` is no longer rendered, so the left column fills the card. This is the only visible change on /dataset (D10) |
| Page size 100 | Up to 100 delete drawers, matching the org Members precedent |
| Narrow list column | About 512px at 1280 and 568px at ≥ 1400 (D3) |

---

## 8. Decisions Taken

| # | Decision |
|---|---|
| D1 Strategy | **Direct replacement** of `user/dashboard_datasets.html`, extending `v2/user-dashboard-base.html` with `user_nav_active='my_datasets'` and `page_label=_('My Datasets')`. No `?v2` gate. |
| D2 Right column | New `{% block tertiary_content %}` plus a `tertiary_class` layout var in `v2/page.html`. It is captured like `secondary_content` and rendered as a third div **after** the content column, only when non-empty, so the DOM order is nav → list → filters. The base sets `tertiary_class` to `hdx-v2-content-columns__sidebar --xl-only --sticky hdx-v2-search-sidebar hdx-v2-search-sidebar--right`. |
| D3 Widths | Both side columns are 25% (`.v2-sidebar-flex()`), not Figma's 14.063rem. |
| D4 List render | `search_results_wrapper.html` with `my_c=search_data` and `v2=true`, as on the Org/Location/Crisis pages. The wrapper forwards `admin_view`, `list_title`, `list_subtitle`, `title_tag`, `title_size` and `show_filters` to `package_list.html`. |
| D5 Update status | When the `ext_update_status` facet is present, `search-filters.html` renders it as the **first** dropdown, labelled "Update status" with the placeholder "All statuses". Only this page's search logic returns that facet. `search.js` `FILTER_PARAMS` and package_list's selected-count/chip keys gain `ext_update_status`. |
| D6 Header | Reuse the v2 list header (`v2/list-header.html`, rendered by `package_list.html`) with new params: `list_title` (default "Datasets"), `list_subtitle` (default none; here Figma's "Datasets you own or manage", verbatim, although the list is maintainer-only), `title_tag` (default `strong`; `h1` here), and `title_size` (`'section'` default, `'page'` on /dataset, `'dashboard'` here; the CSS modifier is the value itself). Controls, Filter button, search bar, chips and overlay are reused unchanged. |
| D7 Header fonts | Match the My Datasets Figma. Title: `.hdx-display-s()` (24px bold, fixed). Count: `.hdx-body-m()`, neutral-8. Subtitle: `.hdx-body-s()`, neutral-85, `space-13` below the title row, full width. The header row wraps, so in the narrow XL column the controls drop under the title. Implemented as `hdx-v2-list-header__title--dashboard` / `__count--dashboard` plus a `__subtitle` element. Title and subtitle type come from new shared mixins `.hdx-dashboard-title()` / `.hdx-dashboard-subtitle()` in `mixins.less`, which 072's `.hdx-v2-user-dashboard-header__title` / `__subtitle` also switch to. |
| D8 Sort | Keep "Due for Update" (`due_date asc`) as the default, shown via `admin_view`. Figma's "Last added" is placeholder content. |
| D9 Card | **Extend `c-dataset-card`** with new optional params. No modifier class. |
| D10 Card API | Two new optional params: `labels` (a list of `c-label` dicts) and `caller()`, which renders an `__actions` row below the body. When `labels` is passed, the org line becomes a `__top` row: org on the left, `__labels` on the right. `__right` is rendered only when location, date or formats exist. The header comment is updated. The title keeps the card's 2-line clamp (18px at MD+). |
| D11 Card content | Single column: no location, date, formats or COD/COD+ badges. The private/archived/by-request dark icon-only badges move into `labels`. The "[By Request Only]" title suffix, the org link, the description and "Show more" stay as `package_item_v2.html` maps them. |
| D12 Frequency chip | `light`/`xs`: "Expected update frequency: {h.hdx_get_frequency_by_value(pkg.data_update_frequency)}", using the dataset page's wording. Omitted when there is no frequency. |
| D13 Due chip | `xs` with `time-clock.svg`: "Update by {h.hdx_get_due_overdue_date(pkg)}". `yellow` when not `is_fresh`, `light` when fresh. Hidden when `update_status == 'unknown'`, the date is ongoing, there is no date, or `pkg.archived`. v1's sentence is dropped. |
| D14 Chip order | Status badges, then frequency, then due. |
| D15 Permissions | One `h.check_access('package_delete', {'id': pkg.id})` per card (v1's existing check) gates Update, Archive and Delete together. "Send a group message" is always shown. |
| D16 Delete | One `c-drawer` per card (`delete-dataset-<id>`), rendered after the card. A `.c-drawer-form` POSTs to `hdx_dataset.delete` with `h.csrf_input()`. It opens via `onclick="window.hdxV2Drawer('delete-dataset-<id>').open()"`. v1 copy is used verbatim: title "You are deleting a dataset", text "Are you sure you want to delete this dataset?", buttons Cancel / Delete. No new JS. |
| D17 Archive | `contributeAddDetails(id, 'archive', '#field_archived')`, the quick-edit anchor pattern. The label is "Archive", or "Unarchive" when `pkg.archived`. No backend change. |
| D18 Group message | A same-tab link to the dataset page with `#group-message`. `group-message-drawer.js` opens `gm-header-drawer` on load when the hash is `#group-message` and the drawer exists, then drops the hash with `history.replaceState`. No drawers and no membership lookups on the dashboard. |
| D19 Action labels | "Update" (Figma) as a primary s `c-button`. "Send a group message" (Figma) as a tertiary s `c-button` with `mail.svg`. |
| D20 MD/SM | The Search pattern (§6). The card's top row wraps at any width when it doesn't fit, with the chips under the org name (§6). |
| D21 Empty state | When there are no items and no filters are selected (the `organization/read.html` condition), `tertiary_content` renders nothing and `show_filters=False` hides the Filter button and overlay (the header's sort then shows at every width, 074 Q63). package_list's existing empty-state copy stays. |
| D22 Right column CSS | In `search.less`, generic: `.hdx-v2-search-sidebar--right` (at XL: `border-left: 1px solid var(--hdx-neutral-1)`, padding `space-5` 0 `space-20` `space-10`), and `.hdx-v2-search-content:not(:last-child)` (at XL: padding-right `space-10`), next to the existing `:only-child` rule. |
| D23 Tests | No new tests. The `hdx_user_dashboard.datasets` rows in `test_page_load.py` cover the page load. |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/v2/page.html` | `tertiary_content` block + `tertiary_class` (D2) |
| `THEME/templates/v2/user-dashboard-base.html` | Sets `tertiary_class`; header comment documents the block (D2) |
| `THEME/templates/user/dashboard_datasets.html` | Full replacement: base, filter form in `tertiary_content`, wrapper call, `scripts` block (D1, D4, D21) |
| `THEME/templates/search/snippets/search_results_wrapper.html` | Forward the new params (D4) |
| `THEME/templates/search/search.html` | `title_size='page'` (D6) |
| `THEME/templates/search/snippets/package_list.html` | Header params + subtitle (D6, D7); `ext_update_status` in count/chips (D5); `show_filters` (D21). The v2 `admin_view` loop uses `package_item_v2.html` |
| `THEME/templates/search/snippets/package_item_v2.html` | `admin_view` branch: labels, actions, delete drawer (D10–D19) |
| `THEME/templates/v2/components/dataset-card.html` | `labels`, `caller()` actions, conditional `__right`, header comment (D10) |
| `THEME/hdx-styles/src/common/less/v2/components/dataset-card.less` | `__top`, `__labels`, `__actions`; wrapping (D10, D20) |
| `THEME/templates/v2/search-filters.html` | Update status dropdown (D5) |
| `THEME/fanstatic/v2/pages/search.js` | `FILTER_PARAMS` gains `ext_update_status` (D5) |
| `THEME/hdx-styles/src/common/less/v2/pages/search.less` | `--right` sidebar, content padding (D22); list-header `--dashboard` + `__subtitle` (D7) |
| `THEME/hdx-styles/src/common/less/v2/mixins.less` | `.hdx-dashboard-title()` / `.hdx-dashboard-subtitle()` (D7) |
| `THEME/hdx-styles/src/common/less/v2/pages/user-dashboard.less` | 072 header title/subtitle use the shared mixins (D7) |
| `THEME/fanstatic/v2/group-message-drawer.js` | Hash-open (D18) |
| `THEME/templates/v2/components.html` | dataset-card demo with labels and actions |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | List header pattern: `title_size='dashboard'` and the shared dashboard mixins (D7) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated-pages entries |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/029-implement-dataset-card-component.md`, `036-dataset-results-layout-v2.md`, `066-archived-dataviz-v2.md`, `072-user-dashboard-my-organisations-v2.md` | Card params, right column, `title_size`, Excluded list and header mixins |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 073 → `implemented` when done |

---

## Verification

- `/dashboard/datasets` renders for tester and sysadmin and redirects anonymous users; the `test_page_load.py` rows pass.
- `?ext_update_status=needs_update` shows the Update status dropdown checked and a removable chip.
- Sort defaults to "Due for Update". Page size, search, the archived toggle and pagination keep their params.
- Chips follow D12/D13 for fresh, overdue, unknown, ongoing and archived datasets, and the private/archived/by-request badges appear.
- Update and Archive open the contribute popup (Archive at `#field_archived`). A member-role maintainer sees neither.
- The Delete drawer POSTs; the page then shows "Dataset has been deleted." as a `c-alert`.
- "Send a group message" opens the dataset page with the drawer open (for org members).
- XL shows three columns. On MD/SM there is no nav, and the Filter button opens the overlay with filters and sort.
- /dataset and the Org, Location and Crisis pages are visually unchanged.
