# 095 — Sysadmin QA Dashboard Enhancements

**Scope:** QA tooling on two v2 pages. This is not a migration of the v1 QA dashboard.
- Search: a sysadmin-only "Sysadmin filters" block on v2 `/dataset` with a "QA filters" dropdown and a "Methodology"
  dropdown. The QA list follows the Figma, including "HDX Connect" and "Datasets with Showcase", both backed by existing
  search params. Sysadmin searches on `/dataset` include private datasets (D4).
- Dataset page:
  - a public dataset-level "Under review" label;
  - a sysadmin-only dataset-level CTA that switches between "Put all resources under review" and "Make all resources
    public", behind a confirmation drawer;
  - a sysadmin-only per-resource "QA actions" menu: "Put under review", and once under review "Make public" plus
    "Download for review".

  No backend change on the dataset page (D8, D10).

**Excluded:**
- the v1 QA dashboard (`/qa_dashboard`) page, its dataset/resource rows, PII widget and `qa-package.js` (D1);
- the Figma's "Datasets with Interactive Data" filter. No backend exists (on the dataset page, "Interactive data" is
  `pkg.customviz`), and new filter implementations are out of scope (D6);
- QA controls for non-sysadmin QA officers (D7);
- the v2 resource page (`resource_read.html`);
- the broken-link, QA-completed and PII-sensitivity actions;
- the notification emails for quarantined datasets (055).

**Figma sources:** `xl-dataset-page-qa-resource.html`, `xl-dataset-page-one-resource-under-review.html`,
`xl-dataset-page-qa-all-resources-under-review.html`, `xl-search-qa-filters.html`, `xl-search-qa-filters-panel.html`.
All are XL only; there are no MD or SM exports.

Terms used below:
- **QA officer:** a user holding the per-user `Manage QA` permission.
- **Under review:** a resource with `in_quarantine` set. The UI says "Under review"; the code says "quarantine".

---

## 1. Existing Implementation Audit

### Permissions

| Who | How | Where |
|---|---|---|
| Sysadmin | CKAN auth bypass: every auth function passes unless it is decorated `auth_sysadmins_check` | core |
| QA officer | `Permissions.PERMISSION_MANAGE_QA` (`'permission_manage_qa'`, label "Manage QA", comment "QA Complete and quarantine"), stored in the `hdx_permissions` user extra and granted on the User Permission page (076) | `ckanext-hdx_users` `helpers/permissions.py` |

Only two auth functions honour `Manage QA`: `hdx_mark_qa_completed` and `hdx_mark_resource_in_quarantine`
(`ckanext-hdx_package` `actions/authorize.py`). The rest of the QA surface is sysadmin-only:
- `qa_dashboard_show` always returns False, even though its message says "sysadmins/qa officers";
- `hdx_qa_resource_patch`;
- `hdx_qa_package_revise_resource`, which reuses the `hdx_qa_resource_patch` auth;
- `hdx_qa_hapi_report_view`.

"QA officer" otherwise appears only in that message string, one test name and the Figma comments.

### Quarantine actions (`ckanext-hdx_package` `actions/patch.py`)

| Action | Auth | Effect |
|---|---|---|
| `hdx_mark_resource_in_quarantine` `{id, in_quarantine}` | `Manage QA` (or sysadmin) | Sets `ignore_auth`, then calls `hdx_qa_resource_patch`. Template code and JS never call it today; it is API-only. |
| `hdx_qa_resource_patch` `{id, in_quarantine, …}` | sysadmin only | Runs `package_revise` on `update__resources__<id>` and `_do_quarantine_related_processing_if_needed`, which does three things: the QA quarantine analytics event (`QAQuarantineAnalyticsSender`), S3 "sensitive" tagging of uploads, and, when quarantining, removal of `shape_info` and the geopreview layer. |
| `hdx_qa_package_revise_resource` `{id, key, value}` | sysadmin only | The existing bulk action: one `package_revise` with `{key: value}` on every resource position. It **skips** all three side effects above. |

Notes:
- **String values.** The side-effect code compares the string `'true'`. A JSON boolean `true` is handled as a release:
  the wrong analytics event, the wrong S3 tag, and geopreview is kept. Callers must send `'true'` / `'false'`.
- **Implicit changes.** Normal dataset edits keep the previous value (`hdx_keep_unless_allow_resource_qa_script_field`).
  `hdx_reset_on_file_upload` and `hdx_update_in_quarantine_by_microdata` force new and microdata resources into
  quarantine.

### Downloads of quarantined resources
- The `hdx_resource_download` auth fails whenever `in_quarantine` is set ("Only sysadmins can download quarantined
  resources"), so only sysadmins pass, through the bypass.
- `download_wrapper.py` runs `resource_download_with_quarantine_check` (`helpers/quarantine.py`), which 404s for HDX
  uploads.
- `_process_url` (`actions/get.py`) strips `url`, `alt_url`, `download_url` and `hdx_rel_url` from quarantined
  resources for users without `package_update`.
- There is no "download for review" route, action or parameter. Sysadmins download through the normal `hdx_rel_url`.
  The v2 resource page already shows them Download for quarantined resources (`can_dl` has no review filter).

### v1 QA dashboard (`/qa_dashboard`)
- **Route and access:** `hdx_qa` blueprint (`ckanext-hdx_search` `views/qa.py`), `dashboard()`. It returns 404 unless
  `hdx.qadashboard.enabled` is set (default true) and 403 unless `qa_dashboard_show` passes, which in practice means
  sysadmins only.
- **Template and entry point:** renders `qa_dashboard/qa_dashboard.html` (`extends "page.html"`, v1). It is linked only
  from the v1 header for sysadmins. The v2 menus leave it out (084, 087, 088).
- **Search logic:** `QASearchLogic` (`controller_logic/qa_search_logic.py`) uses `ignore_capacity_check=True`, so
  private datasets are included. Its `qa_only` group ("QA only"), in order: New datasets, Updated datasets, Bulk upload,
  Non-bulk upload, Private datasets, Public datasets, QA Completed, QA Not Completed, Broken links, Under review, then
  Unconfirmed Sensitivity Classification. It also adds a `{!ex=methodology,batch}methodology` facet.
- **Sidebar:** the v1 `search/snippets/package_search_facets.html` renders every facet group, `qa_only` included, in
  list order.
- **Row actions:**
  - per dataset (`qa_package_item.html`): Quarantine all resources / Remove from quarantine, through
    `updateAllResourcesQuarantine`, which calls `hdx_qa_package_revise_resource`;
  - per resource (`qa_resource_item.html`): Add to / Remove from Quarantine (`updateQuarantine`, which calls
    `hdx_qa_resource_patch`), and Download when `hdx_resource_download` passes.

  All of them run straight away with a loading overlay and then `location.reload()`; there is no confirmation.

### Search backend (all searches)
- **Existing params.** `before_dataset_search` (`ckanext-hdx_search` `plugin.py`) `adapt_solr_fq` already maps the
  following on every search, `/dataset` included:

  | Param | Solr filter |
  |---|---|
  | `ext_showcases` | `has_showcases:true` |
  | `ext_requestdata` | `extras_is_requestdata_type:true` |
  | `ext_in_quarantine` | `res_extras_in_quarantine:true` |
  | `ext_broken_link` | `res_extras_broken_link:true` |
  | `ext_private_datasets` | `capacity:private` |

  The same hook also handles `ext_qa_completed`, `ext_new_datasets`, `ext_updated_datasets`, `ext_bulk_datasets` and
  `ext_pii_is_sensitive`. A `0` value negates each filter.
- **Showcase.** `has_showcases` is computed in `_additional_hdx_package_show_processing` (`hdx_package/actions/get.py`)
  at index time, declared as a boolean in `hdx-solr/schema.xml`, and faceted in `dataset_facets` as
  `{!ex=batch}has_showcases` ("Datasets with Showcases"). `SearchLogic` counts it (`num_of_showcases`), but its
  "Datasets with Showcase" Advanced-filters item is commented out. Adding or removing a showcase does not refresh
  `has_showcases` until the dataset is reindexed (094).

### v2 `/dataset` filters (031, 065)
- **Templates.** `search/search.html` places `v2/search-filters.html` inside `#search-page-filters-form`. In order, it
  renders:
  1. the hard-coded `filter_defs` (status, locations, organisations, formats, topics), each a
     `v2/components/dropdown.html` checklist;
  2. "Advanced filters", from `facet_list['featured']`;
  3. the archived "Show only" radios.

  Any other facet group (e.g. `qa_only`) is ignored.
- **JS.** `fanstatic/v2/pages/search.js` (`FILTER_PARAMS`, `ADVANCED_FILTER_PARAMS`) navigates on each checkbox
  change; there is no Apply button. It also drives clear-all, the filter count and the pills in
  `search/snippets/package_list.html`, all of which know only these params.
- **Smaller layouts.** Below XL, the form moves into the `v2/filter-overlay.html` slot.
- **No sysadmin branch.** `/dataset` always uses `SearchLogic` (`views/light_dataset.py` `generic_search`) with
  `ignore_capacity_check=False`. `package_search` therefore adds `+capacity:public`, so private datasets never appear,
  even for sysadmins.
- **Analytics.** The passive Mixpanel `search` event (`google-analytics.js`) serialises the filters form and already
  knows `ext_showcases` and `ext_requestdata` (035).

### v2 dataset page
- **Header.** `hdx_read.html` calls `v2/components/page-header.html`.
  - Labels row (`.c-page-header__labels`, above the title): Deleted (red), Archived (dark + archive), Request only data
    (yellow + lock), COD+ (grey) and the Part of links. The row renders only when one of those applies.
  - Right card: Contact the contributor, Edit Dataset, Group message, then the `header_actions` list
    (`{label, href, icon_src, attrs, show}`, rendered as tertiary `size='m'` text-buttons with `tag='a'` forced).
    `hdx_read.html` doesn't pass `header_actions`.
  - There is no under-review indicator anywhere on the page.
- **Resource cards.** `resource_item_v2.html` feeds `v2/components/resource-card.html` (038).
  - When `in_review` (`res.in_quarantine`) is set:
    - the Download slot becomes a hard-coded `<a class="c-button c-button--secondary c-button--size-m">Under Review</a>`;
    - `title_href`, "More information" and "Access via API" all point at the QA-process docs (`faq_review_url`), not the
      resource page.

    This is the same for every user, sysadmins included, because `show_download` also requires `not in_review`.
  - There is no QA menu. `.c-resource-card__actions` holds More information plus one of Under Review, Request data or
    Download.
- **JS.** There is no v2 QA JS. `fanstatic/v2/pages/dataset.js` handles only the accordions and the customviz tabs.
  The available building blocks are:
  - `window.hdxV2.post` (`fanstatic/v2/utils.js`, CSRF header; pass `FormData` / `URLSearchParams`);
  - `hdxV2.showAlert`, `hdxV2.setDisabled`;
  - `c-dropdown` + `dropdown.js` (custom-`attrs` action items, as in `org-members.js`);
  - `c-drawer` for confirmations (059 D9).
- **Download tracking (must be preserved).** The Download button carries
  `resource-url-analytics ga-download resource-download-button` plus `data-resource-*` / `data-dataset-*` attributes.
  These are read by:
  - GA / Mixpanel "resource download" (`google-analytics.js`);
  - the notification prompt (`notification_platform/subscribe.js`);
  - the data-use survey drawer (`v2/data-use-survey-drawer.js`);
  - core tracking.

---

## 2. Figma Analysis

### Dataset page — three states

```
.dataset-page-header
├── left
│   ├── [label "Under review"]          eye icon · bg #f6e9d4 · 4px radius · 2/6 padding · 22px — states 2, 3
│   ├── title (+ hidden label row) · description · Get notified · downloads
└── right card (white, 24px padding, gap 16)
    ├── logo
    └── text-buttons (gap 10): Contact organisation · Group message ·
        "Put all resources under review"   — states 1, 2   <!-- Only visible to QA officers(sysadmin) -->
        "Make all resources public"         — state 3       <!-- …This button make all resources public again -->
Data and resources (2)
└── resource card × 2
    footer: Show more · [QA actions ▾] · More information · [Download (14.2K)] | [Under Review]
            QA actions trigger = leading icon + "QA actions" + chevron
            state 1 open menu (detached popover): "Put under review"  <!-- Only visible to QA officers -->
```

| State | Export | Dataset label | Header CTA | Resource footer |
|---|---|---|---|---|
| 1. Nothing under review | `xl-dataset-page-qa-resource` | — | Put all resources under review | Download (size); menu: Put under review |
| 2. One of two under review | `xl-dataset-page-one-resource-under-review` | Under review | Put all resources under review | that card: "Under Review" (secondary, white, 1px #1862d8 border, #0e3b82 text, no icon); the other: Download |
| 3. All under review | `xl-dataset-page-qa-all-resources-under-review` | Under review | Make all resources public | every card: Under Review |

### Search — Sysadmin filters (`xl-search-qa-filters`, `xl-search-qa-filters-panel`)

```
Filter by sidebar
  Location · Organisation · Time period · Data type · Format · Topics
  Advanced filters (chips + Show more)
  ┌ Sysadmin filters ─────────────────────────┐  bg #f5f7f7, 15px side bands, gap 8
  │ [lock] Sysadmin filters                   │  ("Visible to sysadmins" hint: display:none)
  │ QA filters      [ All filters        ▾ ]  │
  │ Methodology     [ All methodologies  ▾ ]  │
  └───────────────────────────────────────────┘
  Show only (Actively maintained / Archived)
```

QA filters panel, in order:
1. Public datasets
2. Private datasets
3. HDX Connect
4. Datasets with Showcase
5. Datasets with Interactive Data (excluded, D6)
6. Under review
7. Broken links

Six more rows are present but hidden. Each row is a checkbox, the label and `(count)`. The Search field and the
Apply/Clear footer are hidden. Methodology panel: Census, Direct Observational Data/Anecdotal Data, Other, Registry,
Sample Survey (the dropdown lists every Solr value, D34).

### Token map

| Figma | Token / component |
|---|---|
| Under review label bg `#f6e9d4`, 22px, eye icon | `--hdx-warning-1` → `c-label color='yellow' size='s'` + `v2/icons/eye.svg` (warning-1 / warning-8, the same pair as "Request only data") |
| Under Review button | existing `c-button--secondary c-button--size-m` |
| Right-card CTAs | `c-text-button` tertiary `size='m'` (as Contact / Group message) |
| Sysadmin block bg `#f5f7f7`, 15px side bands | `--hdx-neutral-05`, `--hdx-space-4` side padding |
| QA / Methodology selects + panels | existing filter `c-dropdown` + `dropdown-panel` checklist |
| QA actions menu: white, shadow `0 4px 12px rgba(0,0,0,.08)`, min-width 15.125rem, right-aligned to the trigger | `c-dropdown--link` as is: left-aligned, `min-width: 11rem` (D13) |

### Artefacts and inconsistencies
- **Hidden in-card menu.** Every resource card in all three exports holds a hidden menu with "Release from quarantine"
  and "Download for review<br>(7.0M)". The visible state-1 menu is a separate popover holding "Put under review". The
  release label is "Make public" (D9). Download for review is a menu item carrying the size (D10). That matches the
  brief's "sized similarly to the standard download button", which follows the "Download (14.2K)" format.
- **Hidden "1 of 2 files is in quarantine"** next to the Data and resources heading. Not planned.
- **State 3 is missing content.** It omits the description and Get notified. Treated as export variance; the page keeps
  both.
- **Unreliable icon names.** "Show more" swaps its icon between exports, and the QA actions leading icon is unnamed
  (the export has no sources). `lock.svg` is used (D13).
- **Contact link label.** The Figma says "Contact organisation"; the page keeps "Contact the contributor" (out of scope).

### Breakpoints
XL only. MD/SM follow D14.

---

## 3. Current vs Target

| Element | Current | Target | Basis |
|---|---|---|---|
| Sysadmin filter block on `/dataset` | none | below Advanced filters, sysadmins only | D1, D2 |
| QA filter list | v1 `/qa_dashboard` sidebar, 11 items, no Showcase or HDX Connect | Public datasets, Private datasets, HDX Connect, Datasets with Showcase, Under review, Broken links | D3, D5, D6 |
| Methodology filter | v1 QA dashboard only | dropdown in the block | D1 |
| Private datasets on `/dataset` | always excluded | included for sysadmins | D4 |
| Dataset "Under review" label | none | yellow + eye, first in the labels row, everyone, at least one resource under review | D11, D29 |
| Dataset QA CTA | none | Put all… (eye-off) / Make all resources public (eye), sysadmins, drawer confirmation | D7, D8, D12, D28 |
| Resource QA actions | none on v2 | QA actions menu (lock icon, item icons), sysadmins | D7, D9, D13, D36 |
| Download for review | none; sysadmins use the resource page | menu item with size, new tab | D10, D16, D21 |
| "Under Review" button | matches Figma | unchanged | — |
| Quarantined title / More information links | QA docs, for everyone | unchanged | D15 |

---

## 4. Component Mapping

| UI | Component | Change |
|---|---|---|
| Dataset "Under review" label | `c-label` (`yellow`, `s`, `eye.svg`) | `page-header.html`: new `under_review` param, added to the labels-row condition |
| Put all / Make all public | `c-text-button` via `header_actions` | none: `href='#'` + `attrs.onclick` opens the drawer (D18) |
| Bulk confirmation | `c-drawer` (`c-drawer-form` text + Cancel / Confirm, as the remove-member drawer in 059) | none |
| QA actions menu | `c-dropdown` + `c-dropdown--link`, `icon=True, icon_src='v2/icons/lock.svg'` (existing params), left-aligned panel as is | `resource-card.html`: a `caller()` slot at the start of `.c-resource-card__actions` (D19); `dropdown.less` sizes the leading-icon svg in the base `__trigger-icon` rule (D32); `list-item.html` gains `icon`/`icon_src` + `c-list-item--has-icon`, and `dropdown-panel.html` passes `item.icon_src` (D37) |
| Download for review | dropdown menu item with `href` + `target="_blank"` | `dropdown-panel.html` passes `item.href` to `list-item.html` (D21); no tracking classes (§8) |
| Sysadmin filters block | new page section `.hdx-v2-search-filters__sysadmin` in `v2/search-filters.html` (LESS in the search-page bundle) | not a component; one consumer |
| QA filters / Methodology | existing filter `c-dropdown` checklist | none; same `items` / `attrs` contract as `filter_defs` |
| Error feedback | `c-alert` (`hdxV2.showAlert`), in the drawer and at the top of Data and resources (D27) | none |

No new `c-*` component is needed.

---

## 5. Flow & States

Let N = resource count and Q = resources with `in_quarantine`.

| Condition | Dataset label (everyone) | Header CTA (sysadmins) | Resource footer (sysadmins) | Resource footer (others) |
|---|---|---|---|---|
| N = 0 | — | none | — | — |
| Q = 0 | — | Put all resources under review | QA actions: Put under review · More information · Download | More information · Download |
| 0 < Q < N | Under review | Put all resources under review | released cards: as above; quarantined cards: QA actions: Make public, Download for review (size) · More information · Under Review | More information · Under Review on quarantined cards |
| Q = N | Under review | Make all resources public | quarantined cards as above | Under Review on every card |

Flow:
1. A per-resource menu action runs directly. The header CTA first opens a `c-drawer` (D12):
   - title: the CTA label;
   - text: "All N resources of this dataset will be put under review." or "All N resources of this dataset will be made
     public." (singular for N = 1, D30);
   - buttons: Cancel / Confirm.

   Confirm disables itself; a menu click disables the QA actions trigger (`hdxV2.setDisabled`).
2. It POSTs `{id, in_quarantine: 'true' | 'false'}` (strings) to `hdx_mark_resource_in_quarantine`. The header CTA
   loops over the resources whose value differs, one request at a time (D8).
3. On success, `location.reload()` (label, CTA and every card change together).
4. On error, the loop stops, the trigger is re-enabled and a `c-alert` reports it, in the drawer (which stays open) or
   at the top of Data and resources (D27, copy D31). Resources already changed stay changed; a reload shows the real
   state.

---

## 6. Responsive Behaviour

There are no MD or SM exports. Same controls at every breakpoint (D14):
- **Dataset header and cards.** The label, CTA and QA menu render at every breakpoint. The right card already stacks
  below the description at SM. The QA dropdown wraps with the existing `.c-resource-card__actions` row.
- **Search.** The Sysadmin filters block sits inside `#search-page-filters-form`, so it moves into the filter overlay
  below XL with no extra work.

---

## 7. Template Strategy

- **Dataset page.** All template changes are in v2-only files: `hdx_read.html`, `resource_item_v2.html`,
  `v2/components/page-header.html`, `v2/components/resource-card.html`, `v2/components/dropdown-panel.html`. v1
  `resource_item.html` and `light/dataset/resource_item.html` stay untouched.
  - Gate: `h.check_access('sysadmin') and not pkg.is_requestdata_type`, dataset not deleted (D7, D17, D24). It is
    evaluated in `hdx_read.html` for the CTA and again in `resource_item_v2.html` per card, because
    `resources_list.html` forwards only `pkg`, `res` and `supports_notifications` (D20). The card checks
    `current_user.is_authenticated and current_user.sysadmin`, which needs no query (D35).
  - Counts: from `pkg.resources` (`selectattr('in_quarantine')`); no new helper.
- **Search.**
  - `v2/search-filters.html` gets the block after Advanced filters, rendered only when the search logic returned the
    QA groups. The view decides; the template does not re-check sysadmin.
  - The QA dropdown uses the same `data-filter-checkbox` / `data-facet` / `name` contract, so `search.js` needs only
    the new params in its lists, and sets `ext_private_datasets` instead of appending it (D22).
- **JS.** The QA code extends `fanstatic/v2/pages/dataset.js`, already in `v2-dataset-page-scripts` (D25). It is inert
  without its `data-*` hooks. No v1 bundle is loaded or edited.
- **Backend:** search only.
  - The `/dataset` view `generic_search` (`ckanext-hdx_package` `views/light_dataset.py`) gets a sysadmin branch.
  - A sysadmin flag on `SearchLogic` adds only the private facet query and the broken-link, under-review and
    methodology facet fields, and builds the D3 group itself; `QASearchLogic` stays untouched (D23). QA params skip the
    batch collapse (D26).
  - No quarantine, auth or download action changes (D8, D10).

---

## 8. Functionality & Analytics Preservation

- **Download tracking.** The Download button, its classes and its `data-*` attributes are unchanged. "Download for
  review" carries none of `ga-download`, `resource-download-button` or `resource-url-analytics`, and sends no event of
  its own (D16). It is not a public download, and it must not trigger the notification prompt or the data-use survey.
- **Quarantine analytics.** The QA analytics event fires only through `hdx_qa_resource_patch`, which
  `hdx_mark_resource_in_quarantine` calls, so it fires once per changed resource (D8).
- **Search analytics.** The passive Mixpanel `search` event is unchanged. QA params serialise with the form but aren't
  in its trigger list.
- **`/qa_dashboard`** is untouched (D1).
- **Search performance.** Anonymous and non-sysadmin `/dataset` requests get no new facets. Measure the sysadmin request
  before and after (`profiling/`).

---

## 9. Accessibility

- The header CTA is an `<a href="#">` with an `onclick`, like the other right-card actions (D18). The `c-drawer`
  handles focus on open and close. While requests are
  running, Confirm or the QA actions trigger is disabled; on error it is re-enabled and gets focus back.
- The QA actions menu uses `c-dropdown` (`aria-haspopup`, `aria-expanded`, `role="menu"` / `menuitem`, arrow keys,
  Esc). Its accessible name includes the resource name, e.g. `aria-label="QA actions for CERF Allocations.json"`. The
  lock icon and the menu-item icons are `aria-hidden`.
- "Under review" is text, not colour alone; the eye icon is `aria-hidden`.
- The Sysadmin filters block is a `role="group"` with `aria-labelledby` pointing at its heading. The dropdown labels
  are the same `c-dropdown__label` spans as in `filter_defs`.

---

## 10. Risks & Edge Cases

| Risk | Handling |
|---|---|
| Boolean vs string `in_quarantine` | JS sends the strings `'true'` / `'false'` |
| Partial bulk failure | the loop stops at the first error and alerts (§5) |
| Bulk on a dataset with many resources | N sequential requests, each a `package_revise` + reindex; measure on a large dataset |
| `has_showcases` stale after showcase add/remove | v1 parity (094); the count catches up on reindex |
| Private datasets surfacing in a sysadmin's normal `/dataset` results | intended behaviour change (D4) |
| `{!ex=batch}` tagging | new facet queries follow the existing `ex=batch` pattern so the batch collapse doesn't hide counts |
| QA officers without sysadmin | no dataset-page controls (D7); `Manage QA` keeps its API-only use |
| Org editors (`package_update`) keep URLs but not Download | unchanged |
| Dataset with 0 resources | no CTA, no label |
| Deleted dataset | QA controls hidden; the label still shows (D24) |
| HDX Connect (request-data) dataset | no header CTA and no QA actions menu (D17); cards keep "Request data" |

---

## 11. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | Where the QA filters live | v2 `/dataset` block (Figma; sysadmin-only facet cost) · v1 `/qa_dashboard` only (add two items, no Figma UI) · both (two lists to sync) | v2 `/dataset` block; `/qa_dashboard` untouched |
| D2 | Sysadmin filters audience | sysadmins only · sysadmins + `Manage QA` | Sysadmins only |
| D3 | QA list content | the Figma items only · the Figma items, then the remaining v1 QA items | Figma items only: Public datasets, Private datasets, HDX Connect, Datasets with Showcase, Under review, Broken links. New / Updated / Bulk / Non-bulk / QA Completed / Not Completed / Unconfirmed Sensitivity Classification stay on `/qa_dashboard` only |
| D4 | Private datasets on `/dataset` | include for sysadmins (as `/qa_dashboard`) · public only, drop Private / Public items · include only while a QA filter is active | Include for sysadmins; sysadmins' default `/dataset` results include private datasets |
| D5 | QA item labels | Figma ("HDX Connect", "Datasets with Showcase") · existing titles ("Datasets on request (HDX Connect)", "Datasets with Showcases") | Figma wording in the QA list; the existing facet titles elsewhere unchanged |
| D6 | "Datasets with Interactive Data" | facet.query on `extras_customviz__0__url` · new `has_customviz` Solr field + reindex · another meaning | Excluded: new filter implementations are out of scope |
| D7 | Dataset-page QA audience | sysadmins + `Manage QA` (`check_access('hdx_mark_resource_in_quarantine')`) · sysadmins only | Sysadmins only (`h.check_access('sysadmin')`) |
| D8 | Bulk backend | new `Manage QA` bulk action (one request, side effects kept) · JS loop over `hdx_mark_resource_in_quarantine` (no backend change, side effects kept, N requests) · existing `hdx_qa_package_revise_resource` (sysadmins, no side effects) | JS loop over `hdx_mark_resource_in_quarantine`, one request at a time, string values |
| D9 | Resource release label | "Make public" (brief) · "Release from quarantine" (hidden Figma layer) · "Remove from quarantine" (v1) | "Make public" |
| D10 | Download for review | menu item for users who can download (sysadmins) · also widen download auth / URL stripping to `Manage QA` · button in the Download slot | Menu item "Download for review (size)" linking to `res.hdx_rel_url` on every under-review card (sysadmins always pass `hdx_resource_download`); no file-access change |
| D11 | Dataset "Under review" label | everyone, at least one under review · QA users only · everyone, all under review | Everyone, when at least one resource is under review |
| D12 | Header CTA behaviour | the Figma states, direct · the Figma states + confirmation drawer · both CTAs in the mixed state | Figma states ("Put all resources under review" until every resource is under review, then "Make all resources public") behind a `c-drawer`: title = CTA label, text "All N resources of this dataset will be put under review." / "All N resources of this dataset will be made public.", Cancel / Confirm. Per-resource actions act directly |
| D13 | QA actions menu look | `c-dropdown--link` as is · right-aligned panel modifier · leading icon `shield.svg` / `lock.svg` | `c-dropdown--link` as is (left-aligned, 11rem) with a leading `lock.svg` icon |
| D14 | MD/SM | the same controls at every breakpoint · hide QA controls below XL | The same controls at every breakpoint (§6) |
| D15 | Quarantined resource links for sysadmins | keep the QA docs link · the resource page for sysadmins | Unchanged |
| D16 | Analytics for Download for review | none · a separate QA event | None |
| D17 | QA actions on HDX Connect (request-data) datasets | QA menu with the quarantine actions · no QA actions | No QA actions: no header CTA, no QA actions menu |
| D18 | Header CTA element | optional `tag` key on `header_actions` (`<button>`) · `href='#'` + `onclick` | `header_actions` entry with `href='#'` and `attrs.onclick` opening the drawer, as org-hero's Add dataset; no page-header change for it |
| D19 | QA menu slot in `resource-card.html` | `caller()` slot · menu-items param | `caller()` slot at the start of `.c-resource-card__actions`, rendered only when non-empty (as c-dataset-card) |
| D20 | Gate in the cards | recompute in `resource_item_v2.html` · pass-through kwarg in `resources_list.html` | Recomputed per card in `resource_item_v2.html`; `resources_list.html` unchanged |
| D21 | Download for review link | `dropdown-panel.html` passes `item.href` to `list-item.html` · navigate item (`data-nav-value`, same tab) | `href` pass-through: a real `<a>` with `target="_blank"`, like Download |
| D22 | Public + Private both ticked | mutually exclusive · as is (v1) | Mutually exclusive: `search.js` sets `ext_private_datasets` instead of appending |
| D23 | Search logic | shared builders moved up from `QASearchLogic` · run `QASearchLogic` on `/dataset` · duplicate in `SearchLogic` | A sysadmin flag on `SearchLogic` adds only the private facet query and the broken-link, under-review and methodology facet fields, and builds the D3 group with its own builders (the flag items share one true-count builder); `QASearchLogic` untouched |
| D24 | QA controls on deleted datasets | hide · show | Hidden; the label still shows |
| D25 | QA JS location | extend `pages/dataset.js` · new `pages/dataset-qa.js` · new `v2/qa-actions.js` | Extends `pages/dataset.js` |
| D26 | Batch collapse with QA filters | QA params skip it · keep it | `ext_private_datasets`, `ext_in_quarantine` and `ext_broken_link` skip the collapse like the featured params |
| D27 | Error feedback placement | drawer + section alert · one section alert · per card | Bulk: a hidden `c-alert` in the drawer, which stays open. Menu actions: one hidden `c-alert` at the top of Data and resources |
| D28 | Header CTA icon (unnamed in the Figma) | `shield.svg` on both · `eye-off.svg` / `eye.svg` · none | `eye-off.svg` on "Put all resources under review", `eye.svg` on "Make all resources public" |
| D29 | "Under review" position in the labels row | first · after Deleted · after COD+ | First, before Deleted |
| D30 | Drawer text for N = 1 | singular variant · D12 text for every N · "1 resource of this dataset…" | `ungettext` singular: "The only resource of this dataset will be put under review." / "…will be made public." |
| D31 | Error copy | generic + reload hint · generic + CKAN `error.message` · one shared sentence | Menu: "The resource could not be updated. Please try again." Bulk: "Not all resources could be updated. Reload the page to see their current state." No CKAN message |
| D32 | Leading-icon svg size in `c-dropdown` | base `__trigger-icon` rule · `--link` only | Base rule, 16px (`--hdx-space-4`); the `--link` chevron stays 16px |
| D33 | Zero-count QA items | hide unless selected (filter rule) · always show all six | Hidden unless selected, like every other filter dropdown |
| D34 | Methodology list | the 5 standard values · every Solr value · 5 values with legacy under "Other" | Every Solr value (v1 parity), legacy free text included |
| D35 | Sysadmin check in the card gate | `current_user` · `h.check_access('sysadmin')` per card (+1 user query per card for logged-in users) · kwarg via `resources_list.html` | `current_user.is_authenticated and current_user.sysadmin`, no query; `hdx_read.html` keeps `h.check_access('sysadmin')` |
| D36 | QA menu item icons (16px, 8px gap per the Figma) | `eye-off.svg` / `lock.svg` on "Put under review" | `eye.svg` on "Make public", `download.svg` on "Download for review", `eye-off.svg` on "Put under review" (as the D28 header CTA) |
| D37 | Item icon API in `list-item.html` | `icon` + `icon_src` · `icon_src` only | `icon` + `icon_src` (type `list` only) + `c-list-item--has-icon`, as `selection-item.html`; navigate items take an `icon_src` key |

---

## 12. Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/…/templates/package/hdx_read.html` | sysadmin gate, counts, `under_review`, `header_actions`, confirmation drawer |
| `ckanext-hdx_theme/…/templates/package/snippets/resource_item_v2.html` | sysadmin gate; QA menu in the card's `caller()` slot |
| `ckanext-hdx_theme/…/templates/v2/components/page-header.html` | `under_review` label |
| `ckanext-hdx_theme/…/templates/v2/components/resource-card.html` | `caller()` actions slot |
| `ckanext-hdx_theme/…/templates/v2/components/dropdown-panel.html` | navigate items pass `href` and `icon_src` to `list-item.html` |
| `ckanext-hdx_theme/…/templates/v2/components/list-item.html` + `…/v2/components/list-item.less` | optional leading icon (`icon`, `icon_src`, `c-list-item--has-icon`) |
| `ckanext-hdx_theme/…/hdx-styles/…/v2/components/dropdown.less` | leading-icon svg size in the base `__trigger-icon` rule |
| `ckanext-hdx_theme/…/hdx-styles/…/v2/pages/dataset.less` | spacing under the Data and resources alert (`hdx-v2-dataset-section__qa-error`) |
| `ckanext-hdx_theme/…/fanstatic/v2/pages/dataset.js` | QA actions, bulk loop |
| `ckanext-hdx_theme/…/templates/v2/search-filters.html` + search-page LESS | Sysadmin filters block |
| `ckanext-hdx_theme/…/fanstatic/v2/pages/search.js`, `search/snippets/package_list.html` | QA params, single-value `ext_private_datasets`, pills, count |
| `ckanext-hdx_search/…/controller_logic/search_logic.py`, `ckanext-hdx_package/…/views/light_dataset.py` | sysadmin QA facets and D3 group, private datasets for sysadmins, QA params skip the batch collapse |
| `ckanext-hdx_theme/…/templates/v2/components.html` | demo entries for visual changes only: `--link` dropdown with a leading icon and item icons, resource card with a `caller()` QA menu, List Item with a leading icon (`c-page-header` has no demo) |
| `ckanext-hdx_package/…/tests/test_pages/test_dataset.py`, `ckanext-hdx_search/…/tests/test_qa_controller.py` | QA controls / Sysadmin filters for sysadmins only; label for everyone; private datasets for sysadmins only |
