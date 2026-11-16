# 090 — Sysadmin Dashboard: Custom Pages (v2 Migration)

**Scope:** the Custom Pages listing (`/ckan-admin/pages/show`, `hdx_custom_pages.index`) and its Add/Edit form
(`/page/new`, `/page/edit/<id>`, `hdx_custom_page.new` / `.edit`), moved onto the 084 sysadmin shell. Also in scope:
the delete confirmation (listing and form), the component extensions the form needs (D6, D7, D9, D14, D15, D20), and
four v1 server fixes with their tests (D12, D19, D27).

**Excluded:**
- The read pages (`/event/<id>`, `/dashboards/<id>`, 060), the `/m/` light pages, `/crisis-pages` (071) and
  `/archive` (066).
- The `page` model, its tables and the actions' contract (`page_create` / `_update` / `_delete` / `_show`,
  `admin_page_list`), apart from the D19 message fix.
- Search, pagination, page-size controls and a count on the listing (§3.3).
- Section reordering, a preview or review step, a success message, new analytics events.

**Figma source:** `xl-sysadmin-custom-pages.html` (listing, XL only) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. There is no export for the form; §3.4 derives it from the v2
sysadmin and dashboard forms (079, 082, 087–089).

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `PAGES` = `ckanext-hdx_pages/ckanext/hdx_pages`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `hdx_custom_pages.index` and `hdx_custom_page.new` / `.edit`. Reached from the sysadmin menu (`custom_pages`), the header user menu, v1's admin tabs ("Custom/Event Pages") and the v1 header / dashboard links |
| Objective | Listing: v2 page on `v2/sysadmin-base.html` (`nav_active='custom_pages'`, `page_label=_('Custom Pages')`) with Figma's header and table. Form: v2 page on the same shell with the v1 fields, sections and buttons. Both keep the routes, the POST contract, auth, redirects and the Lunr rebuild |
| Strategy | **Direct replacement** of `THEME/templates/admin/pages.html` and `THEME/templates/pages/edit_page.html` (no `?v2` gate, as 084–089) |
| Shared work | `c-config-item` + `config-item.js` gain a form mode (D6); `select.html` / `select.js` gain multi-select and a tag source (D7); `c-radio` follows `:checked` (D9); `c-slug-preview` gets a prefix hook (D14); `text-field.html` gets a `hint` (D15); `table.html` header cells get `scope="col"` (D23); the `table.less` DataTables adapter fits inside `c-table-container` (D33). Defaults keep the other pages' output unchanged except where §6.6 says |

---

## 2. Repository Audit Findings

### 2.1 Routes and auth

| Endpoint | URL | View | Renders |
|---|---|---|---|
| `hdx_custom_pages.index` | `/ckan-admin/pages/show` (GET) | `THEME/views/custom_pages.py` `index` | `admin/pages.html` with `page_list` |
| `hdx_custom_page.new` | `/page/new` (GET, POST) | `PAGES/views/light_page.py` `CreateView` | `pages/edit_page.html`; a save redirects to the read page |
| `hdx_custom_page.edit` | `/page/edit/<id>` (GET, POST) | `EditView` | Same |
| `hdx_custom_page.delete_page` | `/page/delete/<id>` (POST) | `DeleteView` | Redirect to the listing |
| `hdx_event.read_event` / `hdx_dashboard.read_dashboard` | `/event/<id>` / `/dashboards/<id>` | `PAGES/views/light_page.py` (060) | Listing links and redirect targets |

- **Auth:** `admin_page_list`, `page_create`, `page_update` and `page_delete` all resolve to
  `has_permission()` (`PAGES/helpers/helper.py`: `Permissions.PERMISSION_MANAGE_CRISIS`); sysadmins pass through the
  CKAN bypass. Every view aborts 404 "Page not found" on `NotAuthorized`. `CreateView.post` / `EditView.post` log any
  other `check_access` exception and carry on (unchanged).
- **Listing rows:** `admin_page_list` (`PAGES/actions/get.py`) returns every row, no ORDER BY, each filtered through
  `page_show` auth. Non-active rows pass only the sysadmin bypass, so a permission holder sees active pages only,
  even drafts they saved.
- **Entry points:** `hdx_get_sysadmin_nav_sections()` already lists `custom_pages` under the `admin_page_list` check,
  after HDX Connect Dashboard; the header user menu shares it. `find_first_global_settings_url()`
  (`ckanext-hdx_users`) returns it for a user whose first matching permission is manage-crisis. v1 `admin/base.html`, `header-global.html` and
  `user/dashboard.html` link to it (unchanged).
- **2FA:** neither URL is in `_before_request` `protected_urls` (unchanged).
- **CSRF:** the v1 form and the delete modal post `h.csrf_input()`.

### 2.2 Stored data and the POST contract

- **`page` table** (`PAGES/model.py`): `id`, `name` (unique slug), `title`, `description` (edited as "Keywords"),
  `type` (`event` | `dashboards`), `state` (`active` | `draft`), `status` (`ongoing` | `archived`), `sections` (JSON
  string), `extras` (JSON string, `{"show_title": "on" | "off"}`), `modified`. Locations and tags live in
  `page_group_association` / `page_tag_association`.
- `page_show` returns `extras` parsed, `keywords` = `description`, `tags`; `admin_page_list` returns raw rows
  (`as_dict()`).
- **Local data:** 9 pages (event / archived 4, event / ongoing 3, dashboards / ongoing 2), all `active`; section
  types in use: data_list 8, interactive_data 1, key_figures 1, description 1. Figma's hidden count says 28.
- **POST contract** (built by `_populate_sections()`; the tests post it; unchanged):

| Name | Value | Notes |
|---|---|---|
| `title`, `name` | Text | Validated: "Page title cannot be empty", "Page name cannot be empty", "Page name already exists". The slug's characters are not validated |
| `show_title` | `on` when checked | Stored as `extras`, `off` when absent |
| `type` | `event` \| `dashboards` | |
| `status` | `ongoing` \| `archived` | |
| `groups` | Location names, repeated | `_process_groups()` takes a string or a list |
| `description` | Comma text | Labelled "Keywords" |
| `tag_string` | Comma string | `_process_tags()` → tag dicts; a tag missing from the Topics vocabulary and the free tags fails "Tag X not found" |
| `hdx_counter` | Int | Sections are read for indices `0 … hdx_counter − 1`; a missing index is skipped |
| `field_section_<i>_type` | `empty`, `description`, `map`, `key_figures`, `interactive_data`, `data_list` | `empty` sections are skipped |
| `field_section_<i>_{data_url, section_title, section_description, section_long_description, max_height, m_max_height}` | Text | Fields the chosen type doesn't use are `disabled`, so they don't post |
| `save_custom_page=active` \| `save_as_draft_custom_page=draft` | Submit button | Becomes `state` |

- **Section type → fields** (v1 `custom_pages.js` `field_config`):

| Type | Data URL | Title of Section | Description | Long Description | Max Height / Mobile Max Height |
|---|---|---|---|---|---|
| empty | | | | | |
| description | | ✓ | | ✓ | ✓ |
| map | ✓ | ✓ | | | ✓ |
| key_figures, interactive_data | ✓ | ✓ | ✓ | | ✓ |
| data_list | ✓ | ✓ | | | |

- **After a save:** redirect to the read page (`_generate_action_name`); `_update_lunr()` rebuilds the feature
  search index (skipped on the test site id). Delete also rebuilds it and redirects to the listing.
- **Re-render on a validation error:** the view calls its own `post()` again with the posted dict, errors and
  `error_summary`; the template reads `data`.

### 2.3 v1 listing

`admin/pages.html` extends v1 `admin/base.html` (`<title>` "Administration"):
- a float-right "Create New Page" link to a hard-coded `/page/new`;
- a Bootstrap `table table-header table-hover table-bordered`: Title (link `/<type>/<id>`), Slug (link
  `/<type>/<name>`), Type, Archived/Ongoing, Status, Actions ("Edit" link to `/page/edit/<id>` | "Delete" opening a
  per-row `snippets/confirmation_post.html` modal: "Confirm" / "Are you sure you want to delete this page?" /
  Cancel, Confirm);
- Title and Slug carry `data-module="hdx_click_stopper" data-module-link_type="main nav"`;
- a leftover `data-module="hdx_custom_pages"` wrapper;
- a side "Event/Custom Pages" help panel: how to create, edit, delete and archive; archived pages move to `/archive`;
  location pages should be deleted rather than archived.

### 2.4 v1 form

`pages/edit_page.html` extends v1 `page.html`: a fake two-step stepper ("1 Create custom page – Please fill out all
required fields", "2 Review and Submit", which doesn't exist), then two Bootstrap rows, each with a help column
(`col-3`) beside the fields (`col-9`):
- **Page:** an "invalid entries" alert listing `key: errors`; Title of the page (required class, `field_title`,
  `slug-preview-target`); URL (`field_name`, `/event/` prepend, v1 slug preview with the event prefix whatever the
  type); Display page title (checkbox, checked by default); "This page is located under" radios Event
  (`hdx_event_type`) / Dashboards (`hdx_dashboard_type`), each labelled with its full URL; Status radios Ongoing
  (`hdx_page_ongoing`) / Archived (`hdx_page_archived`); Location (`field_groups`, a native multi-select of
  `h.hdx_location_list()`); Keywords (`field_description`); Tags (`field_tag_string`, `hdx_autocomplete` Select2
  over `/api/2/util/tag/autocomplete`, existing tags only).
- **Sections:** one block per stored section (Section select, the six fields, "Delete this section" link), hidden
  fields shown per type by `custom_pages.js`; "+ Add More Sections" clones a hidden `#section_template` and bumps
  `hdx_counter`. No reordering; no collapse.
- **Help columns:** "How this page works" (preview / draft wording; there is no preview) and "Design a page in
  section" with `/images/new-page-section-sample.png`.
- **Buttons:** "Delete This Page" (edit only, confirmation modal) left; "Save This Page" then "Save As Draft"
  (DOM order) floated right. Enter in a text field submits "Save This Page".
- New page defaults: Event, Ongoing, Display page title on, no sections.
- Locations are preselected on Edit only when the group id equals its name: the select tests location names against
  `page_group_list`'s ids. 13 of 254 local locations differ (e.g. `rou`, `tls`, `xkx`); none is on a page.

### 2.5 v1 bugs

| Bug | Cause | Fix |
|---|---|---|
| Saving a dashboard page lands on `/event/<name>` | `_generate_action_name` checks `'dashboard'`; the stored type is `'dashboards'` | D12 |
| After a validation error, "Display page title" always comes back checked | On the re-render `extras` is the JSON string from `_populate_sections()`, so `data.extras.show_title` is undefined | D12 |
| Creating a page with an unknown tag or location, or any non-validation error, returns 500 | `page_create`'s messages `'Tag % not found'` and `'…request: %'` raise `ValueError` inside the error handler | D19 |
| Saving an edited page drops its Locations whose id differs from the name | They aren't preselected (§2.4) and `page_update` replaces every link | D27 |
| The URL preview says `/event/` for dashboards | Static prefix | D14 |
| "Review and Submit" step and the "see a preview" help don't exist | Leftover copy | Dropped (D10) |

### 2.6 Assets

- Listing: `admin/base.html`'s v1 bundles; `custom_pages/custom_pages.css` is in `admin-styles`.
- Form: `custom-pages-scripts` (`custom_pages/custom_pages.js`, `contribute_flow/form_element_manager.js`; preloads
  `custom-pages-styles` and `hdx-autocomplete`).
- After migration these pages no longer load them; the files and bundles stay (v1 assets untouched, 087 precedent).

### 2.7 Analytics and tests

- Title and Slug links: `hdx_click_stopper`, `link_type` `main nav` (the module is in the v2 base bundle). No other
  Mixpanel or GA events on either page. The `base.html` page view still fires; `pageTitle` changes ("Administration"
  → "Custom Pages | Sysadmin"; the form gains "Create custom page | Sysadmin" / "Edit custom page | Sysadmin").
- `PAGES/tests/test_controller.py`: new/edit GET as a regular user (404) and as a sysadmin (200, body contains
  `Save This Page`, `field_title`, `hdx_event_type`, `hdx_page_ongoing`, `field_name`); read pages.
- `PAGES/tests/test_page_new_controller.py` / `test_page_edit_controller.py`: POST the contract, assert redirects,
  stored values and "Page title cannot be empty" / "Page name cannot be empty" / "Tag some_new_tag not found" (edit).
- No test covers the listing.

### 2.8 Reusable v2 pieces

| Piece | Use here | Gap |
|---|---|---|
| `v2/sysadmin-base.html` (on `v2/dashboard-base.html`) | Shell, menu, crumb, `<title>`, both pages | The form's four-level crumb (D5) |
| `v2/list-header.html` | Both headers; `caller()` holds "Create new page" | — |
| `v2/components/table.html` (`c-table`) | Listing table, Markup cells (API tokens precedent) | `scope="col"` (D23); cell overflow (§6.8); DataTables frame and header focus (D33) |
| `c-text-link`, `button.html`, `text-button.html` | Row links and actions, form buttons | — |
| `c-drawer` + `.c-drawer-form` | Delete confirmation (members / dataset delete precedent) | — |
| `c-config-item` + `config-item.js` | Section cards | AJAX-only, always draggable (D6) |
| `text-field.html`, `c-form-field` | Text fields, Long Description (`multiline`) | No hint slot (D15) |
| `select.html` (+ Select2 `searchable`) | Section type, Location, Tags | Single value only; `select.js` maps user autocomplete only (D7) |
| `c-radio` | Type, Status | Checked look is server-only (D9) |
| `c-checkbox` | Display page title | — |
| `c-slug-preview` | URL | Fixed prefix (D14) |
| `alert.html` | Errors without a field | — |

---

## 3. Figma Design Analysis (XL)

### 3.1 Page

**Shell:** as 084–089: left "Sysadmin" menu in the helper's order, "Custom Pages" active; breadcrumb Home / Sysadmin /
Custom Pages.

**Header** (padding 40 / 48): "Custom Pages" (Merriweather 24px bold); 6px below, "Create and manage crisis pages"
(14px, neutral-85); on the right, 2rem from the text, a primary button "Create new page" (8px padding, 14px medium,
icon slot left).

**Body:** the table, 12px below the header.

### 3.2 Table

| Property | Figma | `c-table` as built |
|---|---|---|
| Box | 60.063rem (961px), 1px `#ebeff0`, radius 2px | `--hdx-neutral-1` border, `--hdx-radius-sm` |
| Header | 40px, `#fafbfb`, 12px semibold, `#2f3536` | `.c-table-th-styles()`: neutral-01, body-xs semibold, neutral-85 |
| Separators | 1px white right / bottom | Same |
| Rows | 40px, 12px regular neutral-85, ellipsis, **all white** | 8px padding, ellipsis, `max-width: 200px`, **striped** (D3) |
| Columns | Title 14.375rem (230px) · Slug flex · Type 6.25rem · Archived / Ongoing flex · Status 6.25rem · Actions flex | Sized by content, full width (D28) |
| Values | Raw stored strings: `event` / `dashboards`, `ongoing` / `archived`, `active` | Same |
| Title / Slug | Plain text | Links (D4) |
| Actions | "Edit": white button, `--hdx-neutral-2` border, drop shadow, 4 / 8px padding, 14px `file-edit` icon; "Delete": underlined text button with an icon, 12px after Edit | `button.html` tertiary s + `file-edit.svg` (D34); `text-button.html` tertiary s + `delete.svg` (the `c-config-item` Delete) |
| Sort chevrons | Two per header on the first five columns | DataTables, the `table.less` chevrons (D1) |

Ten rows are drawn; a 12px horizontal scrollbar layer sits at the bottom of the row group.

### 3.3 Hidden layers and artefacts

- **Hidden (`display:none`):** the count "28", "Results per page" and "Sort by" dropdowns, a search field, a pager,
  a chevron beside the header, the Actions column's sorter, two extra empty columns per row.
- **Artefacts:** the "Create new page" icon layer is `chevron-down-icon`; the Delete icon layer is
  `file-edit-icon`; the first row's type reads "dashboards" (the stored value); "grater-middle-east-crisis" and
  "turkite-syria-earthquakes" are sample-data typos.

### 3.4 Add/Edit form (no export)

Derived from the v2 forms in the dashboard shells:
- **Shell and width:** the Profile form (079): dashboard shell, `list-header`-style h1, form 100% wide at SM and
  80% from MD (`.hdx-v2-user-profile`).
- **Sections and headings:** the org edit form (082): `.hdx-section-title()` h2 per group, `c-form-field` per field,
  `c-slug-preview` URL.
- **Repeatable blocks:** the sysadmin editors (087–089): `c-config-item` cards, a tertiary "New Item" button with
  `plus.svg`.
- **Actions:** the org edit / message forms: right-aligned; destructive action tertiary, opening a `c-drawer`. They
  put the primary last; this form keeps v1's primary-first order (D17).

---

## 4. Current vs Target Comparison Matrix

### 4.1 Listing

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 admin tabs, help panel | `v2/sysadmin-base.html`, menu at XL | D10 |
| Breadcrumb / `<title>` | None / "Administration" | Home / Sysadmin / Custom Pages / "Custom Pages \| Sysadmin" | Derived |
| Heading | None | `<h1>` "Custom Pages" + subtitle, no count | D11 |
| Create | "Create New Page" link, float right | Primary m button "Create new page" in the header | D11, D24 |
| Table | Bootstrap bordered / hover table | `c-table`, striped | D3 |
| Columns | Title, Slug, Type, Archived/Ongoing, Status, Actions | Same, header "Archived / Ongoing" (Figma) | D11 |
| Title / Slug | Links (by id / by name) + analytics | `c-text-link`s, both by name, + analytics | D4 |
| Sorting / order | None / DB order | DataTables on the first five columns / DB order on load | D1, D2 |
| Edit | Text link | Tertiary s button + icon | D34 |
| Delete | Text link → Bootstrap modal | Tertiary s text button + icon → `c-drawer` | D8 |
| No pages | Header-only table | Same | D16 |
| Hard-coded URLs | `/page/new`, `/page/edit/<id>`, `/<type>/<id>` | `h.url_for` (same endpoints) | Derived |

### 4.2 Form

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 `page.html`, no menu | `v2/sysadmin-base.html`, Custom Pages active | D5 |
| Breadcrumb / heading | Fake stepper | Home / Sysadmin / Custom Pages / {h1}; h1 "Create custom page" / "Edit custom page" | D5, D13 |
| Layout | Help column + fields column | One column, 100% / 80% from MD; groups "Page details" / "Sections" | D10, D20 |
| Errors | "Invalid entries" alert + `form.*` errors | Field errors on their fields; the rest in a top `c-alert` | D21 |
| Title, URL | Title asterisk; v1 slug preview, `/event/` prefix | Both required (native + asterisk); `c-slug-preview`, prefix follows Type | D14, D18 |
| Display page title | Checkbox | `c-checkbox` | Derived |
| Type, Status | Radios, no fieldset | `c-radio` in `<fieldset>` / `<legend>` | D9 |
| Location | Native multi-select list box | Select2 multi-select, preselected by name | D7, D27 |
| Keywords | Text input | `text-field` | Derived |
| Tags | v1 Select2 tag autocomplete | Select2 multi-select over the tag autocomplete | D7 |
| Sections | Blocks with "Delete this section", clone template | `c-config-item` cards (collapse, Delete), form mode | D6 |
| Long Description hint | "You can use Markdown formatting here" | Same, through `hint` | D15 |
| Buttons | Delete This Page (left); Save This Page, Save As Draft | Delete This Page (left, tertiary); Save This Page (primary), Save As Draft (v1 order) | D11, D17 |
| Delete confirmation | Bootstrap modal | `c-drawer` | D8 |
| Redirect after saving a dashboard | `/event/<name>` | `/dashboards/<name>` | D12 |
| Assets | `custom-pages-scripts` | v2 component bundles + `v2-custom-page-form-page-scripts` | D31 |

---

## 5. Component & System Reuse Strategy

### 5.1 Listing table: `table.html` fit

`table.html` takes `headers` and `rows` and prints each cell as `{{ cell }}`, so a cell built with
`{% set %}…{% endset %}` renders as HTML (the API tokens page builds its Revoke form this way). Everything the
listing needs fits: Markup cells for the links and the actions row, `extra_classes` for page-level cell rules,
the existing horizontal scroll. The striping stays (D3) and DataTables sorts the rendered table (D1), so the component
is reused with one markup addition, `scope="col"` on header cells (D23).

### 5.2 Sections: `c-config-item` fit (D6)

| Need (v1) | `c-config-item` + `config-item.js` today | Gap |
|---|---|---|
| Card per section with a title and Delete | Header with handle, `<h2>` title, collapse toggle, Delete | Handle and `<h2>` fixed |
| Add a block from a template | `<template data-config-item-template>`, `__index__` → counter, renumbered titles, `config-item:add` | Fits |
| Delete at once | Card removed, saved id queued for Save | Queue and Save don't apply |
| Posted with the page form, indexed names | Each card posts its own AJAX request on Save; names unindexed | Must not run |
| No reordering | Sortable always on | Off |
| Focus on add | First text field | The first enabled control (the Type select) |

**Options:**

| Option | For | Against |
|---|---|---|
| A. Extend: `draggable` / `title_tag` params + a `config-item.js` form mode | One repeatable-card feature across the sysadmin editors; add / collapse / renumber / Delete focus reused | A mode switch in a shared script |
| B. Fieldset blocks + page JS | No shared change; `<fieldset>` grouping | Repeats add / delete / renumber; looks unlike the other sysadmin editors |
| C. Option A plus drag reordering, renaming fields on submit | Reorder | New behaviour; drag-only (no keyboard reorder) |

Chosen: **A** (D6).

### 5.3 Multi-value inputs (D7)

| Need | Today | Gap |
|---|---|---|
| Location: many of ~254 options, searchable | `select.html` single value (`selected == value`); no v2 page uses `multiple` | `multiple` param, list `selected` |
| Tags: chips over `/api/2/util/tag/autocomplete` (`?incomplete=<term>` → `{"ResultSet": {"Result": [{"Name": …}]}}`) | `select.js` AJAX branch sends `q` and maps user replies | A tag source |
| Chips styling | `hdx-v2` Select2 theme styles the single selection only | Multi-selection rules |
| `tag_string` as one comma string | A multi-select posts repeated values | The view joins a list (§6.1) |

No v2 tag input exists; dataset tags are edited through the v1 quick-edit flow.

### 5.4 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, menu, crumb, `<title>` | `v2/sysadmin-base.html` (+ own `breadcrumb_items` on the form) | Reuse | D5 |
| Headers | `v2/list-header.html` (`caller()` on the listing) | Reuse | Derived |
| Table | `table.html` | Reuse + `scope="col"` | D3, D23 |
| Listing sort | `v2-datatable-scripts` + new `fanstatic/v2/pages/custom-pages.js`; `table.less` adapter | Reuse + extend | D1, D33 |
| Row links | `text-link.html` | Reuse | D4 |
| Row / form buttons | `button.html`, `text-button.html` | Reuse | Derived |
| Delete confirmation | `c-drawer` in a new `admin/snippets/custom_page_delete_drawer.html` | New page snippet | D8 |
| Section cards | `c-config-item` + `config-item.js` | Extend | D6 |
| Section fields | New `admin/snippets/custom_page_section_fields.html` | New page snippet | Derived (087–089) |
| Location, Tags | `select.html` + `select.js` + `dropdown.less` | Extend | D7 |
| Type, Status | `c-radio` (`radio.html` + `selection.less`) | Extend | D9 |
| URL | `c-slug-preview` | Extend | D14 |
| Long Description hint | `text-field.html` | Extend | D15 |
| Type → fields, counter, slug prefix | New `fanstatic/v2/pages/custom-page-form.js` | New page script | D6, D14 |
| Errors | `alert.html` | Reuse | D21 |

---

## 6. Functional Requirements

Each requirement cites its decision (§9).

### 6.1 Backend

`PAGES/views/light_page.py`:
- `_generate_action_name()`: `'dashboards'` (and `'dashboard'`) → `hdx_dashboard.read_dashboard` (D12).
- `_init_data()`: when re-rendering posted data whose `extras` is a JSON string, parse it, so the template reads the
  posted `show_title` (D12).
- `_init_extra_vars_edit()`: map `page_group_list`'s group ids to location names (`model.Group.get`), so every stored
  Location is preselected; an id with no group is skipped with a warning, never a 500 (D27).
- `_populate_sections()`: a `tag_string` that arrives as a list (the D7 multi-select) is joined with `,` before
  `_process_tags()`; the stored `tag_string` is the joined string. A single value is unchanged (D7).
- The `checked` constant and the data keys it filled for the v1 template (`data.event` / `.ongoing` defaults, the
  `<type>` / `<status>` keys in `_populate_sections()` and `_init_extra_vars_edit()`) go; the form reads `data.type`
  and `data.status` (D35).
- Everything else (auth, 404s, the contract, redirects, Lunr): unchanged.

`PAGES/actions/create.py`: the two messages become `'Tag %s not found'` and
`'Something went wrong while processing the request: %s'` (D19). An unknown tag on create then re-renders the form
with the `tag_string` error, as update does.

`THEME/views/custom_pages.py`: unchanged.

### 6.2 Listing template (`THEME/templates/admin/pages.html`)

- Extends `v2/sysadmin-base.html`; `nav_active='custom_pages'`, `page_label=_('Custom Pages')`.
- Page-loaded assets: `v2-datatable-scripts`, `v2-custom-pages-page-scripts` (§6.7).
- Header: `v2/list-header.html` with `list_title=page_label`, `list_subtitle` (§6.9), `title_tag='h1'`,
  `title_size='dashboard'`, `show_controls=False`, `show_filters=False`; `caller()` = `button.html` primary m,
  `tag='a'`, `href=h.url_for('hdx_custom_page.new')`, `icon_src='v2/icons/file-plus.svg'` (D24).
- Table: `table.html` with `extra_classes='hdx-v2-custom-pages-table'`, the six headers (§6.9) and one row per
  `page_list` item in the order received (D2). Cells:

| Column | Cell |
|---|---|
| Title | `text-link.html` `secondary` `xs`, label `p.title`, href read endpoint by type (`hdx_dashboard.read_dashboard` for `dashboards`, else `hdx_event.read_event`) with `id=p.name`; attrs `id="custom-page-<p.id>-title"`, `data-module="hdx_click_stopper"`, `data-module-link_type="main nav"` (D4) |
| Slug | Same with label `p.name`, no element id |
| Type / Archived / Ongoing / Status | `p.type` / `p.status` / `p.state` |
| Actions | `button.html` tertiary s (D34), `tag='a'`, label "Edit", `file-edit.svg`, `href=h.url_for('hdx_custom_page.edit', id=p.id)`, `aria-labelledby` = its own id + the title link id; `text-button.html` tertiary s, `tag='button'`, label "Delete", `delete.svg`, `aria-labelledby` the same way, opens the row's drawer |

- After the table: one delete drawer per row (§6.3), `drawer_id="delete-custom-page-<p.id>"`.
- No pages: the header-only table (D16).

### 6.3 Delete drawer snippet (`THEME/templates/admin/snippets/custom_page_delete_drawer.html`)

Params `page` (id) and `drawer_id`, header comment in the `admin/snippets` format. `c-drawer` titled "Confirm"
holding a `.c-drawer-form` POST to `h.url_for('hdx_custom_page.delete_page', id=page.id)` with `h.csrf_input()`,
`.c-drawer-form__text` "Are you sure you want to delete this page?", and `.c-drawer-form__buttons`: Cancel
(tertiary, `data-drawer-close`) then Confirm (primary, submit) (D8). The form renders it after its `</form>`.

### 6.4 Form template (`THEME/templates/pages/edit_page.html`)

- Extends `v2/sysadmin-base.html`; `nav_active='custom_pages'`; `page_label` = "Edit custom page" when `data.id`,
  else "Create custom page" (D13).
- `breadcrumb_items`: Home / Sysadmin (the base's group crumb) / Custom Pages (`hdx_custom_pages.index`) /
  `page_label` (D5; `v2/user-dashboard-base.html` precedent).
- Page-loaded assets: `v2-select2-styles`, `v2-select2-scripts`, `v2-slug-preview-scripts`,
  `v2-config-item-scripts`, `v2-custom-page-form-page-scripts`.
- Header: `v2/list-header.html`, `list_title=page_label`, `title_tag='h1'`, `title_size='dashboard'`, no controls.
- `<form id="create_page_form" class="hdx-v2-custom-page-form" method="post" enctype="multipart/form-data">` with
  `h.csrf_input()`:
  1. Errors (D21): field errors pass `errors=` (`title`, `name`, `tag_string`); any other key (e.g. `message`) shows
     its messages in an error `c-alert` (`dismissible=False`) above the first group.
  2. **Page details** (`<h2>`, D20), each field in a `c-form-field` (ids and names as v1):

| Field | Snippet | Name / id | Value | Notes |
|---|---|---|---|---|
| Title of the page | `text-field` m, `required=True` | `title` / `field_title` | `data.title` | D18 |
| URL | `slug-preview`, `required=True`, `target_id='field_title'`, `preview_placeholder='page_id'` | `name` / `field_name` | `data.name` | Prefix = the qualified read URL of `data.type` without the scheme (082's `slug_prefix` pattern) (D14) |
| Display page title | `checkbox` | `show_title` / `field_show_title` | Checked unless `data.extras.show_title == 'off'` | No `value` → posts `on` (D24) |
| This page is located under | `<fieldset>` + `<legend>`, two `radio.html` | `type`; `hdx_event_type` (`event`), `hdx_dashboard_type` (`dashboards`) | `data.type`, default `event` | Labels carry the full URL (§6.9); each radio carries its slug prefix as a data attribute (D9, D14) |
| Status | Same | `status`; `hdx_page_ongoing`, `hdx_page_archived` | `data.status`, default `ongoing` | D9 |
| Location | `select`, `multiple=True`, `searchable=True` | `groups` / `field_groups` | `selected=data.groups` (names); options `h.hdx_location_list()` (`[{value, text}]`) as the `{value: label}` dict `select.html` takes | D7, D27 |
| Keywords | `text-field` m | `description` / `field_description` | `data.description` | |
| Tags | `select`, `multiple=True`, `searchable=True`, tag source | `tag_string` / `field_tag_string` | Options and selection = `data.tag_string` split on commas | `errors=errors.tag_string` (D7) |

  3. `<hr class="c-divider">`, then **Sections** (`<h2>`): a `c-config-item-list` in form mode (§6.6) with
     `data-title-format` "Section {n}" and the type → fields mapping as JSON (`data-section-fields`), defined once in
     this template (D22). Items: one `c-config-item` per `data.sections` entry (`title_tag='h3'`,
     `draggable=False`, `id="custom-page-section-<i>"`, `i` = `loop.index0`), its body the fields snippet; the
     `<template>` holds the same with `__index__`. Below: "Add More Sections" (`button.html` tertiary, `plus.svg`,
     `data-config-item-add`). Hidden `hdx_counter` = `data.hdx_counter` (number of rendered sections).
  4. Actions row (D17): "Delete This Page" (tertiary, `button_type='button'`, edit only, opens
     `delete-custom-page-<data.id>`) on the left; on the right, shown in DOM order (D29), "Save This Page" (primary,
     submit, `id`/`name="save_custom_page"`, `value="active"`) then "Save As Draft" (secondary, submit,
     `id`/`name="save_as_draft_custom_page"`, `value="draft"`).
- After `</form>`: the delete drawer (§6.3) when `data.id`.

### 6.5 Section fields snippet (`THEME/templates/admin/snippets/custom_page_section_fields.html`)

Params `section` (default `{}`), `index` (int or `'__index__'`), `fields` (the mapping) and `type_options` (the view's
`data_dict.content_type` as a `{value: label}` dict, built once in the form). Names and ids
`field_section_<index>_<field>` (v1). Each text field sits in a `c-form-field` carrying `data-section-field="<field>"`;
a field the section's type doesn't use renders `hidden` with its control `disabled` (D22).

| Field | Snippet | Label (v1) | Placeholder (v1) |
|---|---|---|---|
| `type` | `select` m, `data-section-type`, options `type_options` (v1 order and labels): `empty` "Select content type", `description` "Description/Text", `map` "Map", `key_figures` "Key Figures", `interactive_data` "Interactive Data", `data_list` "Data List" | Section | — |
| `data_url` | `text-field` m | Data URL | Enter URL |
| `section_title` | `text-field` m | Title of Section | Title of Section (optional) |
| `section_description` | `text-field` m | Description (optional) | eg. Description of the section |
| `section_long_description` | `text-field` m, `multiline`, 5 rows, `hint` (§6.9) | Long Description | eg. Long Description of the section |
| `max_height` | `text-field` m | Max Height | 400px recommended |
| `m_max_height` | `text-field` m | Mobile Max Height | 400px recommended |

v1 had two Title of Section placeholders; the existing-section one ("If missing will have the default value")
promised a default that is empty, so the new-section one is used for both.

### 6.6 Component extensions

All new params are optional; with their defaults the output of every other caller is unchanged unless noted.

| Component | Change | Decision |
|---|---|---|
| `v2/components/config-item.html` | `draggable` (default `True`; `False` omits the handle and adds `c-config-item--static`, which drops `cursor: grab`); `title_tag` (default `'h2'`) | D6 |
| `fanstatic/v2/components/config-item.js` | Form mode, set by `data-config-item-form` on the list: no Sortable; Delete removes the card (nothing queued) with today's focus move; no Save handler or AJAX, the page form submits; New Item inserts from the template, renumbers titles, dispatches `config-item:add` and focuses the card's first enabled control. Collapse unchanged. Without the attribute, behaviour is unchanged | D6 |
| `v2/components/select.html` | `multiple` (default `False`): `multiple` on the `<select>`, `selected` may be a list (`value in selected`); a placeholder goes to Select2 (`data-placeholder`) instead of the empty first option, which a multi-select would let users pick | D7 |
| `fanstatic/v2/components/select.js` | Multiple selects: Select2 with `multiple`, no `allowClear`; the label and `aria-*` copy reaches the inline search field users type in. Tag source, marked on the select (e.g. `data-source-type="tag"`): term sent as `incomplete`, results from `ResultSet.Result[].Name` (id = text = name). The user source is unchanged | D7 |
| `LESS/components/dropdown.less` | `hdx-v2` theme rules for the multiple selection: chips in the `c-selection-item` active size S look (chip mixins), remove × (a close-icon mixin shared with the clear button), inline search field | D7, D30 |
| `LESS/mixins.less` | `.hdx-chip()`, `.hdx-chip-active()`, `.hdx-chip-size-s()` | D30 |
| `v2/components/radio.html` | No `c-radio--checked` class; the native `checked` drives the look (as `c-checkbox`). Callers' HTML loses only the class | D9 |
| `LESS/components/selection.less` | Ring / dot rules follow `input:checked ~ .c-radio__input` only (the `--checked` rules go); the disabled ring rule also covers `input:checked`. `c-selection-item` uses the chip mixins | D9, D30 |
| `LESS/components/form-field.less` | `&[hidden]` guard (the section fields toggle `hidden`); `__hint--start` (left-aligned) | D22, D32 |
| `v2/components/slug-preview.html` | The prefix text wrapped in `<span data-slug-preview-prefix>` | D14 |
| `v2/components/text-field.html` | `hint` (default `''`, may be Markup): a `.c-form-field__hint.c-form-field__hint--start` element with an id below the field, referenced by the control's `aria-describedby` | D15, D32 |
| `v2/components/table.html` | `<th scope="col">` | D23 |
| `LESS/components/table.less` | DataTables adapter: no `.dt-container` frame inside `.c-table-container`; `.dt-column-order` covers its header cell, `.hdx-focus-ring()` inset on `:focus-visible` (the CSV preview too) | D33 |

### 6.7 Page scripts

`THEME/fanstatic/v2/pages/custom-pages.js` (bundle `v2-custom-pages-page-scripts`, after `v2-datatable-scripts`):
DataTables on the listing table when it has rows (D16): no paging, search, info or length menu, `autoWidth` off,
`order: []` (DB order on load, D2), Actions not orderable; asc → desc → DB order per header (D1).

`THEME/fanstatic/v2/pages/custom-page-form.js` (bundle `v2-custom-page-form-page-scripts`), vanilla JS, IIFE:
- **Type → fields:** a delegated `change` on `[data-section-type]` shows the card's `[data-section-field]` wrappers
  listed for the type in `data-section-fields` and hides + disables the rest (v1 `field_config`).
- **Counter:** on `config-item:add`, `hdx_counter` becomes at least the new card's index + 1 (indices only grow;
  deleted indices leave gaps the view skips).
- **Slug prefix:** a `change` on the Type radios writes the chosen radio's prefix into `[data-slug-preview-prefix]`
  (D14).

### 6.8 Page LESS (`LESS/pages/sysadmin.less`, `v2-sysadmin-page-styles`)

- `.hdx-v2-custom-pages-table`: no column widths or minimum width, so the browser sizes the columns by content (D28);
  Title, Slug and Actions cells drop `max-width` / `overflow`, so links show in full and focus rings aren't clipped;
  the Actions cell lays out Edit and Delete in a row with a `--hdx-space-3` gap.
- `.hdx-v2-custom-page-form`: width 100%, 80% from MD (Profile precedent); groups and fields with v2 spacing tokens;
  `__section-title` uses `.hdx-section-title()`; the actions row is a wrapping flex row, "Delete This Page" pushed
  left.

### 6.9 Copy

| Element | Text |
|---|---|
| Listing title / subtitle | Custom Pages / Create and manage custom pages (D11, D36) |
| Create button | Create new page (D11) |
| Table headers | Title, Slug, Type, Archived / Ongoing, Status, Actions |
| Row actions | Edit, Delete |
| Delete drawer | Confirm · Are you sure you want to delete this page? · Cancel, Confirm (v1) |
| Form h1 / crumb / `<title>` | Create custom page · Edit custom page (D13) |
| Group headings | Page details · Sections (D20) |
| Labels | Title of the page\*, URL\*, Display page title, This page is located under, Status, Location, Keywords, Tags (v1) |
| Radio labels | Event (URL: {event URL}) · Dashboards (URL: {dashboards URL}) · Ongoing · Archived (v1, a space added after "URL:") |
| Placeholders | eg. A descriptive title · eg. page_id · Keywords with comma separated. e.g covid19, coronavirus · eg. economy, mental health, government (v1) |
| Section card title | Section {n} |
| Long Description hint | You can use [Markdown formatting](https://daringfireball.net/projects/markdown/syntax) here (v1, D15; the link opens a new tab) |
| Buttons | Add More Sections, Delete, Delete This Page, Save As Draft, Save This Page (D11) |

### 6.10 Behaviour

- **Create:** empty form, Event / Ongoing / Display page title on, no sections. Save This Page / Save As Draft post;
  the browser blocks an empty Title or URL (D18) and the c-slug-preview reveals the URL field; a server error
  re-renders the form with the posted values (D12 keeps `show_title`).
- **Edit:** the stored values, sections expanded, Locations (D27) and Tags preselected.
- **Enter in a text field** submits Save This Page, the first submit button in DOM order (D17).
- **Sections:** Add More Sections appends "Section N" (type "Select content type", fields hidden) and focuses its
  Section select; choosing a type reveals its fields; Delete removes the card and moves focus; collapse hides the
  fields (they still post).
- **Listing sort:** a click (or Enter) on one of the first five headers sorts ascending, then descending, then back to
  DB order (D1).
- **Delete:** listing row or form button → drawer → Confirm posts → listing.
- **After saving:** the read page of the stored type (D12).

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Sysadmin / manage-crisis access, 404 for everyone else | Unchanged |
| Listing rows (drafts for sysadmins only), DB order, raw values | Unchanged; DB order on load, headers sort (D1, D2) |
| Title / Slug links to the read page by id / name, `hdx_click_stopper` `main nav` | Both by name; analytics unchanged (D4) |
| Create / Edit / Delete endpoints, POST contract, field ids the tests read | Unchanged |
| Draft vs publish by submit button | Unchanged; Enter still publishes (D17) |
| Type-dependent section fields, disabled when hidden | Unchanged (server-rendered as well, D22) |
| Add / delete sections, skipped `empty` sections | Unchanged; no reordering (D6) |
| Location multi-select, tag autocomplete (existing tags only), comma Keywords | Unchanged behaviour (D7) |
| Delete confirmation, redirect to the listing | `c-drawer` (D8) |
| Redirect to the read page, Lunr rebuild | Unchanged; dashboards fixed (D12) |
| Page view | Still fires; new `pageTitle` (§2.7) |

**Intentional differences:**
- The help panel, help columns, sample image and stepper are dropped (D10).
- The listing headers sort, and Title links by slug (D1, D4).
- Title and URL are required in the browser (D18).
- The URL preview follows Type (D14).
- Sections are cards with a collapse toggle (D6).
- The four server bugs are fixed (D12, D19, D27).

---

## 8. Responsive & Accessibility Considerations

### 8.1 Breakpoints (MD/SM inferred)

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Menu | Sticky left column | Header user menu only | Same as MD |
| Listing header | Title + subtitle, button right | Same | Wraps per list-header |
| Table | Full content width, columns sized by content (D28) | Scrolls horizontally inside `c-table__scroll` when its content is wider | Same |
| Form | 80% of the content column | 80% | 100% |
| Section cards | Form width | Same | Same |
| Actions row | Delete left, saves right | Same | Wraps |

### 8.2 Accessibility

- **Headings:** listing `<h1>`; form `<h1>`, `<h2>` per group, `<h3>` per section card (D20).
- **Table:** a real `<table>` with `<th scope="col">` (D23); the scroll container holds focusable links and buttons,
  so keyboard users reach every cell. Edit / Delete names include the page title through `aria-labelledby`; the
  title link keeps its own name. Sortable headers hold DataTables' `role="button"` control ("… Activate to sort",
  `aria-sort` on the sorted column) with a visible focus ring over the header cell (D1, D33).
- **Labels:** every control has a `<label for>`; Type and Status are `<fieldset>`s with a `<legend>` (D9); Select2
  copies the label and `aria-*` onto its combobox (`select.js`); the markdown hint is referenced by
  `aria-describedby` (D15).
- **Required and errors:** asterisks plus native `required` (D18); server errors under their fields and in a
  non-dismissible `c-alert` (D21).
- **Radios:** the visible state follows `:checked` (D9); focus ring as today.
- **Section cards:** the collapse toggle keeps `aria-expanded` / `aria-controls`; Delete is named "Delete Section N"
  via `aria-labelledby`; focus moves to a new card's Section select, and after a delete to the next card or the add
  button. No drag handle (D6).
- **Drawer:** `role="dialog"`, `aria-modal`, focus trap, Escape and Cancel close it (`drawer.js`).
- CSS `:hover` / `:focus-visible` only; no Bootstrap classes or data attributes.

---

## 9. Decisions Taken

D1–D19, D26 and D27–D36 were asked and confirmed with the user; D20–D25 were written into the approved plan as
defaults.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Listing sorting (Figma chevrons; v1 none) | DataTables client-side / server-side sort links / none | DataTables | **DataTables** on the first five columns, Figma chevrons, no direction cue |
| D2 | Default row order | Title A–Z / last modified first / DB order | Title A–Z | **DB order** (v1) |
| D3 | Row stripes (Figma all white) | `striped` param on `table.html` / keep stripes | `striped` param | **Keep `c-table` stripes** |
| D4 | Title / Slug cells (v1 links, Figma plain) | Both links / Title link only / plain text | Both links | **Both `c-text-link`s**, both to the slug URL, analytics kept |
| D5 | Form shell | Sysadmin shell / standalone form card (082) | Sysadmin shell | **Sysadmin shell**, four-level crumb, 100% / 80% width |
| D6 | Section blocks | Extend `c-config-item` + form mode / fieldsets + page JS / extend + drag reorder | Extend | **Extend** (§5.2, §6.6), no reordering |
| D7 | Location and Tags inputs | Select2 multi for both / Select2 Location + text Tags / native multi + text Tags | Select2 for both | **Select2 for both**; view joins a `tag_string` list |
| D8 | Delete confirmation | `c-drawer` per row / one shared drawer + JS / none | Per row | **`c-drawer` per row**, shared snippet, v1 copy |
| D9 | Type and Status controls (`c-radio` checked look server-only) | Radios + `:checked` CSS / native selects | Radios | **Radios** in fieldsets; the look follows `:checked` only (`c-radio--checked` dropped) |
| D10 | v1 help text | Drop both / `c-info-box` on both / form only with the sample | Drop | **Drop** (087–089 precedent) |
| D11 | Labels | Figma listing + v1 form / sentence case / v1 everywhere | Figma + v1 | **Figma listing + v1 form** (§6.9); tests unchanged |
| D12 | v1 bugs: dashboards redirect, `show_title` re-render | Fix both / fix the re-render only / leave | Fix both | **Fix both** (§6.1), one test each |
| D13 | Form heading | "Create / Edit custom page" / "New page" / page title / "Create / Edit page" | Create / Edit custom page | **Create custom page / Edit custom page** |
| D14 | URL preview prefix | Follow Type / static `/event/` | Follow Type | **Follow Type** via `[data-slug-preview-prefix]` |
| D15 | Markdown hint | `hint` param on `text-field.html` / drop | `hint` | **`hint`**, v1 text and link |
| D16 | Empty listing | Header-only table / shared empty message | Header-only | **Header-only table** (088 D8) |
| D17 | Form button order (Enter submits the first in DOM order; a drafted page leaves the public site and permission holders' reach) | Primary first, Enter publishes / primary last, Enter drafts | Primary first | **Primary first** (v1 order); Enter submits Save This Page |
| D18 | Required Title and URL | Native `required` + asterisk / asterisks only / v1 | Native | **Native `required`** on both (082) |
| D19 | `page_create` 500 on non-validation errors (found while writing) | Fix + test / record only | Fix + test | **Fix + test** (§6.1) |
| D20 | Form headings | — | — | h2 "Page details" / "Sections" (`.hdx-section-title()`); section cards h3 |
| D21 | Error display | — | — | Field errors on title / name / tag_string; other keys in a top error `c-alert` |
| D22 | Section field visibility | — | — | One mapping in the form template: server-rendered `hidden` + `disabled`, read by the page JS; cards expanded; focus to a new card's Section select |
| D23 | Table header semantics | — | — | `scope="col"` in `table.html` (also on the API tokens table) |
| D24 | Small markup choices | — | — | `file-plus.svg` on "Create new page"; `show_title` checkbox without `value` (posts `on`) |
| D25 | Labels and placeholders | — | — | v1's, radio labels keep their URLs |
| D26 | Components demo (two `checked` radios per `name` render one checked after D9) | Fix the radio groups / add entries for the visible new params / unchanged | Fix the radio groups | **Radio groups fixed** (own `name` for the disabled pair); **entries added** for `select.html` `multiple` chips and the `text-field.html` `hint`; no `draggable=False` entry |
| D27 | Locations whose id differs from the name (not preselected, dropped on save; found in review) | Fix in the view / keep v1 | Fix | **Fix** in `_init_extra_vars_edit()` (§6.1), one test |
| D28 | Listing table sizing (Figma's 961px table is wider than the ~840–932px XL content column) | Figma proportions in % / Figma rem widths + fill / browser auto layout | Figma proportions in % | **Browser auto layout**: full width, no column widths or minimum (§6.8) |
| D29 | Visual order of the save buttons (v1's floats showed the primary rightmost) | Visual = DOM / v1 look via `row-reverse` | Visual = DOM | **Visual = DOM**: Save This Page, then Save As Draft |
| D30 | Multi-select chip look (no Figma) | `c-selection-item` active size S / neutral filled chip | `c-selection-item` | **`c-selection-item` look**, shared through chip mixins in `mixins.less` (§6.6) |
| D31 | Page-script bundle name | `v2-custom-page-form-page-scripts` / `v2-custom-page-form-scripts` | The first | **`v2-custom-page-form-page-scripts`** (`v2-{page}-page-scripts`) |
| D32 | Markdown hint alignment (`.c-form-field__hint` is right-aligned) | Left via a modifier / right as is | Left | **Left**: `c-form-field__hint--start` |
| D33 | DataTables on a `table.html` table (double frame; focus on an empty `.dt-column-order`) | Shared `table.less` adapter / page-scoped `sysadmin.less` | Shared | **Shared adapter** (§6.6); the CSV preview gains the focus ring |
| D34 | Edit row action style | `button.html` tertiary s (Figma's white, bordered spec) / `text-button.html` tertiary s | `button.html` | **`button.html` tertiary s** |
| D35 | v1 `checked` data keys in `light_page.py` (dead after the v2 form; found in review) | Remove / keep | Keep | **Remove** (§6.1) |
| D36 | Listing subtitle wording (Figma: "crisis pages"; the list also holds non-crisis pages) | Custom pages / crisis pages | Custom pages | **Custom pages** (§6.9) |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/pages.html` | Full v2 replacement (§6.2) |
| `THEME/templates/pages/edit_page.html` | Full v2 replacement (§6.4) |
| `THEME/templates/admin/snippets/custom_page_delete_drawer.html` | New (§6.3) |
| `THEME/templates/admin/snippets/custom_page_section_fields.html` | New (§6.5) |
| `THEME/templates/v2/components/config-item.html`, `THEME/fanstatic/v2/components/config-item.js`, `LESS/components/config-item.less` | `draggable`, `title_tag`, form mode (D6) |
| `THEME/templates/v2/components/select.html`, `THEME/fanstatic/v2/components/select.js`, `LESS/components/dropdown.less` | `multiple`, tag source, multi chips (D7, D30) |
| `LESS/mixins.less`, `LESS/components/selection.less`, `THEME/templates/v2/components/radio.html` | Chip mixins (D30); `:checked`-only radios (D9) |
| `LESS/components/form-field.less` | `[hidden]` guard, `__hint--start` (D22, D32) |
| `THEME/templates/v2/components/slug-preview.html` | Prefix hook (D14) |
| `THEME/templates/v2/components/text-field.html` | `hint` (D15) |
| `THEME/templates/v2/components/table.html`, `LESS/components/table.less` | `scope="col"` (D23); DataTables adapter (D33) |
| `THEME/fanstatic/v2/pages/custom-page-form.js`, `THEME/fanstatic/v2/pages/custom-pages.js`, `THEME/fanstatic/webassets.yml` | New page scripts + `v2-custom-page-form-page-scripts`, `v2-custom-pages-page-scripts` (§6.7) |
| `LESS/pages/sysadmin.less` | Listing table and form layout (§6.8) |
| `PAGES/views/light_page.py` | D12 and D27 fixes, `tag_string` join, v1 `checked` keys dropped (§6.1) |
| `PAGES/actions/create.py` | D19 messages |
| `PAGES/tests/test_controller.py` | Listing test: sysadmin and permission holder 200, other users 404, row links / Edit / Delete drawer URLs; the existing form asserts keep passing |
| `PAGES/tests/test_page_new_controller.py`, `PAGES/tests/test_page_edit_controller.py` | Dashboard redirect, `show_title` off after an error, list `tag_string`, unknown tag on create, a Location whose id differs from its name preselected on Edit (D12, D19, D27) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md`, `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | Migrated pages; the new component params and the config-item form mode |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 090 status |
| `THEME/templates/v2/components.html` | Radio groups, multi-select and `hint` entries (D26) |

Not changed: `THEME/views/custom_pages.py`, the model, `PAGES/actions/get.py` / `update.py` / `delete.py` /
`auth.py`, the read pages, the sysadmin nav helper, the other config-item editors' templates, and the v1 `custom_pages/*`, `contribute_flow/form_element_manager.js`, `admin-*` and `custom-pages-*` bundles. The
v1 files stay on disk; these pages no longer load them.

---

## 11. Implementation Checklist

1. Apply the §6.1 backend changes and add the §10 tests.
2. Extend `config-item.html` / `config-item.js` / `config-item.less`. Check that the Package Links, Products Menu and
   Homepage Highlights HTML is identical before and after, and that their behaviour is unchanged.
3. Extend `select.html` / `select.js` / `dropdown.less`. Check the All Sysadmins promote picker and the Find
   organisation picker still work.
4. Add the `:checked` radio rules, the slug-preview hook, the text-field `hint` and `scope="col"`; compare the org
   edit / new, search filters and API tokens HTML (expected diffs only: the prefix span, `scope`, no `c-radio--checked`).
5. Replace `admin/pages.html` with the delete drawer snippet and the sort script.
6. Add the section fields snippet, the page script and bundle, and replace `pages/edit_page.html`.
7. Run render-level checks, then hand the visual test to the user.
8. Update the docs in §10 and `STATUS.md`.

---

## 12. Risks & Edge Cases

| Case | Handling |
|---|---|
| A stored section whose type is not one of the six options | The select shows "Select content type" (first option), its fields hide, and a save drops the section, as in v1. None locally |
| A permission holder saves a draft | It disappears from their listing (only sysadmins see drafts, §2.1); unchanged |
| Tags typed that don't exist | Select2 offers only autocomplete results; a crafted post gets "Tag X not found" on create and edit (D19) |
| A failed create after the page row was added to the session | `page_create` doesn't commit on its error path; unchanged |
| Duplicate or edited slug | "Page name already exists" under URL; the slug preview stays revealed |
| Collapsed section with values | Still posts its enabled fields |
| Many rows on prod (28 in Figma) | One drawer per row in the DOM; no pagination (§3.3) |
| Narrow screens | The table scrolls horizontally inside its container; the form is one column |
| Two sysadmins editing the same page | Last save wins (unchanged) |
| JS off | Listing works, unsorted; the form posts its server-rendered sections, but Add More Sections, type switching, Select2 and the drawers need JS (as v1) |
