# TDE Preview + Data Dictionary (v2 Migration)

**Scope:** The resource page (`ckanext-hdx_theme/ckanext/hdx_theme/templates/package/resource_read.html`,
already v2 per task `040-resource-page.md`) and the CSV/HXL preview it embeds (`ckanext-hdx_office_preview`,
already styled to v2 per task `047-resource-preview-table-v2.md`). No backend redesign, no API contract
changes, no removal of existing preview functionality.

---

## Context

The originating brief framed this as a "controlled enhancement" of two partially-built features — an
existing Data Dictionary and an existing datastore-backed ("TDE") preview that just needed v2 styling and
a CSRF fix. Auditing the live code, the three resource-page Figma exports
(`resource-page-xl.html`/`-md.html`/`-sm.html`), and the git history of the auth layer surfaced several
mismatches between that framing and reality — the same failure mode already documented in
`066-archived-dataviz-v2.md` and `067-dataviz-gallery-v2.md`, where a brief's assumptions didn't match the
actual page:

- **Data Dictionary does not exist anywhere in HDX**, v1 or v2. It was explicitly logged as out of scope
  when the resource page was migrated (`040-resource-page.md:281-284`, "❌ OUT OF SCOPE — not
  implemented"). This is net-new construction, not a migration.
- **There is no existing datastore-backed preview to migrate.** Today's "Data Explorer" preview
  (`hdx_office_preview` plugin, `view_type: recline_view`) is chosen purely by file format
  (`plugin.py:28-32`, checks `resource['format'].lower()` against a fixed list) and always fetches from an
  **external HXL-proxy service** (`GET /hxl/api/data-preview.json?rows=0&sheet=0&url={resourceUrl}`,
  `hdx_csv_preview.js:1-27`) — never from `datastore_search`, regardless of `res.datastore_active`. The
  one resource view that genuinely is datastore-gated, `HDXChartViewsPlugin` ("Line / Bar Chart",
  `ckanext-hdx_package/ckanext/hdx_package/plugin.py:769-853`, `can_view` checks
  `resource.get('datastore_active')`), is dead code: its declared templates
  (`new_views/chart_view.html`, `new_views/chart_view_form.html`) don't exist anywhere in the repository,
  and `ckanext-hdx_package` has no `templates/` directory at all. It is not a usable precedent.
- **The CSV/HXL preview was already migrated and styled to v2** under task `047-resource-preview-table-v2.md`
  (status: implemented) — DataTables 2.x rendering inside an isolated iframe
  (`hdx_csv_preview_view.html` + `hdx_csv_preview.js` + `hdx_csv_preview.css`, all in
  `ckanext-hdx_office_preview`), hand-styled with CSS that duplicates the real `c-table` component's design
  tokens rather than consuming `v2/components/table.html` directly — because DataTables renders inside an
  iframe document (`extends base.html`) that cannot reach the parent page's Jinja partials. This is the
  pipeline TDE Preview branches inside (see Decisions, D1).
- **The "See documentation" button misalignment has a confirmed root cause that is a CSS-loading bug, not
  a missing style.** `resource_read.html`'s "API access" section markup
  (`resource_read.html:143-154`) depends on `.hdx-v2-dataset-section__header`'s
  `display:flex;justify-content:space-between` rule to push the button right — but that rule lives in
  `dataset-page.less:19-88`, compiled into `dataset-page.css`, bundled only as `v2-dataset-page-styles`
  (`webassets.yml:1596-1600`). `resource_read.html` never loads that bundle (`resource_read.html:48-51`
  only loads `v2-resource-page-styles`, i.e. `resource-page.css`, which defines no
  `.hdx-v2-dataset-section*` rules at all). Figma's export confirms intent:
  `.api-access-parent { justify-content: space-between; ... }` in `resource-page-xl.html` (the accompanying
  `gap: -9.5rem` on the same rule is a static-export artifact of Figma's absolute-position-to-flex
  conversion — the same class of noise flagged in prior docs, not a value to carry over).
- **CSRF turned out to be a red herring, then a genuine access-control question.** Flask-WTF's
  `CSRFProtect` (wired in `ckan/config/middleware/flask_app.py:31,65,255-268`) only guards unsafe HTTP
  methods (`WTF_CSRF_METHODS` defaults to POST/PUT/PATCH/DELETE) — GET requests are exempt from CSRF
  checking entirely, and CKAN core's own `datastore_search`/`datastore_info`/`datastore_search_sql` auth
  functions (`ckanext/datastore/logic/auth.py:50-73`) are decorated `@auth_allow_anonymous_access` and
  delegate to `resource_show`/`package_show`, which succeed for anonymous users on public resources.
  However, **HDX deliberately overrides this**: a chained auth function in
  `ckanext-hdx_package/ckanext/hdx_package/actions/authorize.py:186-229` — added under ticket **HDX-10974**
  ("only authenticated users should be allowed to access the datastore_search\* actions") — unconditionally
  rejects any anonymous caller (`context.get('auth_user_obj').is_authenticated` false) with
  `{'success': False, 'msg': 'Action {name} requires an authenticated user'}` **before** CKAN core's own
  (anonymous-permissive) check ever runs. This is intentional, ticketed, site-specific policy, not a bug.
  The user confirmed — after being shown the trade-off directly — that they want the brief's literal ask:
  treat "holds a valid CSRF token" as the exception to this gate for anonymous visitors on the resource
  preview / data dictionary AJAX calls specifically (see D2 and §6 for the accepted trade-off this implies).

These were resolved directly with the user in two rounds of clarifying questions before finalizing this
doc — see Decisions below.

---

## Decisions Taken

- **D1 — TDE Preview architecture (confirmed): branch inside the existing preview, not a new
  section/view.** Figma shows exactly one "Resource preview" table/section on the page (`resource-page-xl.html`
  lines ~207-235 header, ~230-960 table), not two toggleable variants — so the existing
  `hdx_office_preview` plugin/iframe/DataTables pipeline from task 047 stays the single "Resource preview"
  section. Inside it, branch on `resource.datastore_active` (already computed server-side and already
  available wherever `resource_read.html` renders the preview): if datastore-active, fetch from
  `datastore_search` (see D12 for the actual pagination mechanism shipped); otherwise keep today's
  HXL-proxy fetch completely unchanged. No new `IResourceView` plugin, no change to `resource_read.html`'s
  "first non-`hdx_hxl_preview` view" selection logic (`resource_read.html:12-19`) — there is still exactly
  one `ResourceView` row per resource, so no view-selection ambiguity is introduced.
- **D2 — Anonymous access mechanism (confirmed, per brief, accepted trade-off): CSRF token as the
  anonymous-access exception to HDX-10974.** Modify the chained auth override in `authorize.py` so that,
  for `datastore_search` and `datastore_info` only, the anonymous branch validates a CSRF token from the
  incoming request (via Flask-WTF's `validate_csrf()`, called explicitly/manually — this works regardless
  of HTTP method since it does not rely on `CSRFProtect`'s automatic before-request enforcement, which only
  triggers for unsafe methods) and falls through to `next_auth` (core's anonymous-permissive
  `resource_show`-based check) only if the token is valid; otherwise keeps the existing rejection message
  unchanged. `datastore_search_sql` is **not** in the brief's "Affected Endpoints" list and is **not**
  touched — it keeps HDX-10974's authenticated-only behavior exactly as today. **This is a security
  trade-off, not a neutral fix, and must not be understated**: every visitor — including anonymous ones —
  already receives a valid, working CSRF token simply by loading any HDX page
  (`ckan/templates/base.html:27-28`, `ckanext-hdx_theme/.../templates/base.html:107-108` render the CSRF
  meta tags unconditionally, session-bound, regardless of login state). So this change does not require
  "being a logged-in user," only "having loaded a page on the site first" — a materially weaker bar than
  HDX-10974's original intent. The user was shown this trade-off explicitly (alongside a safer alternative
  — a new server-side proxy endpoint that would leave HDX-10974 completely untouched) and chose this
  option anyway, matching the brief's literal wording. See §6 for the full mechanism and §9 for the risk
  this carries forward.
- **D3 — Data Dictionary loading (confirmed, per brief): AJAX, client-loaded.** `GET
  /api/3/action/datastore_info?id={resource_id}` with the same CSRF header as D2 attached. Unlike the
  CSV/TDE preview, this new section is **not** inside an iframe (it renders directly in the parent
  resource page's own DOM), so it both *can* and *must* reuse the real `v2/components/table.html`
  (`c-table`) component structure directly — there is no iframe-isolation reason to duplicate its CSS the
  way `047` had to for the DataTables preview. The JS renderer produces markup matching `c-table`'s class
  contract (`.c-table-container` / `.c-table__scroll` / `table.c-table` / `<thead>`/`<tbody>`, per
  `table.html:37-63`) — the same "snippet defines the class contract, JS produces matching markup" pattern
  `047` already established for the iframe case, just without the iframe problem here.
- **D4 — API access button fix (confirmed): factor the shared section-header properties into
  `mixins.less`.** `resource-page.less` carries its own `.hdx-v2-resource-section` block (own
  `display:flex;justify-content:space-between` rule on `&__header`), fixing the alignment bug without
  depending on `dataset-page.less`/`v2-dataset-page-styles` at all. The padding/scroll-margin/`&__header`/
  `&__title`/`&__body` properties shared between `.hdx-v2-dataset-section` and `.hdx-v2-resource-section`
  are factored into mixins in `mixins.less` (`.hdx-page-section-wrapper()`,
  `.hdx-page-section-header()`, `.hdx-page-section-body()`), called from each page's own BEM block —
  matching the existing "List header pattern" precedent for page-owned, verbatim-duplicated styling
  (`CONVENTIONS.md`). The section title itself calls the broader-scope `.hdx-section-title()` mixin
  (also used by org/HAPI/Signals/country/Locations). `dataset-page.less` keeps its extra `&__title-row`,
  `&__chevron`, and `&--collapsible` variant layered on top of the mixin calls.
- **D5 — Resource-type detection / conditional logic (confirmed): reuse `res.datastore_active`, no new
  detection.** It is already computed by CKAN core and already gates the existing "API access" section
  (`resource_read.html:100,117,142`, `{% if res.datastore_active %}`). The same flag gates: (a) the
  TDE-vs-CSV branch inside the preview JS (D1), and (b) whether the new Data Dictionary section and its
  anchor-nav entry render at all (a Data Dictionary is only meaningful for a datastore-active resource —
  `datastore_info` on a non-datastore resource returns an empty/error schema).
- **D6 — Analytics (confirmed): add none, matching existing parity.** Confirmed via `google-analytics.js`
  that the only instrumented interaction anywhere on the resource page today is the download button
  (`.ga-download`/`resource-url-analytics`, read by `setUpResourcesTracking()`); neither the "Resource
  preview" section nor the "API access" section carries any `data-ga`/tracking attribute today. Following
  the same precedent already set in `066-archived-dataviz-v2.md` (D4) and `067-dataviz-gallery-v2.md`
  (D3): strict parity, add nothing new to preview loads, Data Dictionary loads, or API-access interactions.
  This is stated as an explicit decision, not a silent assumption, per the brief's own "Analytics
  (CRITICAL)" mandate to identify and preserve — there is nothing on this page's preview/API-access areas
  to preserve.
- **D7 — Data Dictionary column set (confirmed): drop "Unit of measure" entirely, build the remaining 4
  from a column-definition list, not hardcoded duplicated markup.** No source for "Unit of measure" exists
  anywhere in `datastore_info`'s schema (§3), so the column is dropped rather than always rendered "-". The
  JS renderer still targets the same 4 clean-mapped columns (Title, Column name, Data type, Description),
  but derives each header/cell from a single column-definition list (e.g. `[{header: 'Title', get: f =>
  f.info.label || f.id}, ...]`) iterated once to build `c-table`'s markup, rather than duplicating the same
  4 field accesses inline wherever the table is assembled — one source of truth if the response shape needs
  revisiting later, not a fully dynamic per-resource column set.
- **D8 — Data type column content (confirmed): `field.type` verbatim, no friendly-label mapping.** Figma's
  sample row showing "Year (YYYY)" is not replicated; the column always shows the raw Postgres-ish type
  (`text`, `numeric`, `timestamp`, ...) exactly as `datastore_info` returns it. No mapping table is built.
- **D9 — TDE Preview column sort: client-side, not server-side.** The datastore-active branch fetches all
  rows in one `datastore_search` call (D12) and hands them to DataTables as in-memory object-array data;
  column-header sort is DataTables' own client-side sort over that already-loaded data, not a re-issued
  `datastore_search` call with a `sort` param. Sort remains a working feature on both branches of the
  "Resource preview" section, just via a different mechanism than originally decided. A true server-side
  `sort`-param implementation (re-fetching with `offset` reset to 0) is deferred.
- **D10 — `datastore_search_sql` scope (confirmed, permanent): stays excluded, not revisited.** The
  CSRF-anonymous-access exception (D2/§6) never extends to `datastore_search_sql` — raw SQL-like querying is
  a materially bigger exposure than `datastore_search`/`datastore_info`. This closes the question
  permanently rather than leaving it flagged for a future revisit.
- **D11 — Loading state: built.** A reusable `c-spinner` component now exists (`v2/components/spinner.html`)
  and is shown while the Data Dictionary AJAX load and the TDE branch's fetch are in flight, hidden on
  success. Error state remains unbuilt — an empty/malformed response still silently no-ops, same gap that
  existed before this task (§1.2); this gap is accepted as-is.
- **D12 — TDE Preview page size: `limit=10` per DataTables page, fetched via one `limit=32000`
  `datastore_search` call.** The datastore-active branch issues a single `datastore_search` request with
  `limit=32000` (`DATASTORE_FETCH_ALL_LIMIT` in `hdx_csv_preview.js`) and hands all returned rows to
  DataTables, which paginates client-side at `pageLength: 10` — so the visible page size still matches
  today's UI exactly, but the fetch mechanism is fetch-everything-once, not server-side `limit`/`offset`
  pagination per page turn. True server-side pagination is deferred.

---

## 1. Existing Implementation Audit

### 1.1 Resource page template

`ckanext-hdx_theme/ckanext/hdx_theme/templates/package/resource_read.html` (216 lines, the only
resource-read template HDX ships — it fully overrides CKAN core's, `ckanext.datastore`'s, and
`ckanext.tabledesigner`'s same-named templates via a hard `{% extends "v2/page.html" %}`, not
`{% ckan_extends %}`, so none of those extensions' own additions ever render). Sections, in DOM order:

| Block | Lines | Content |
|---|---|---|
| Breadcrumb | 54-61 | Org → Dataset → Resource |
| Page header (`pre_primary`) | 64-92 | `v2/components/page-header.html` — icon, title, description, download button, export-metadata dropdown, 3-item metadata strip |
| Anchor-nav sidebar (`secondary`) / mobile dropdown (`primary`, top) | 95-122 | Built from `_data_explorer` and `res.datastore_active` (see 1.4) |
| Resource preview | 124-139 | `{% if _data_explorer and h.check_access('hdx_resource_download', res) %}` → `package/snippets/resource_view.html` |
| API access | 141-213 | `{% if res.datastore_active %}` → token link, resource ID + copy, example query, "See documentation" button |

Data Dictionary and "Other Resources" are both absent — both explicitly logged out of scope in
`040-resource-page.md:281-289`.

### 1.2 CSV/HXL preview pipeline ("Data Explorer")

Two distinct preview plugins exist; only one is the "CSV/HXL preview" in scope here (the other, Quick
Charts, is explicitly excluded from v2 via the `_v.view_type != 'hdx_hxl_preview'` filter,
`resource_read.html:15`):

| Plugin | `view_type` | Title | `can_view` | `requires_datastore` |
|---|---|---|---|---|
| `ckanext-hdx_office_preview/plugin.py:16-25` | `recline_view` | "Data Explorer" | format in `{xls, xlsx, doc, docx, ppt, pptx, odt, ods, odp, csv}` (`plugin.py:28-32`) | `False` |
| `ckanext-hdx_hxl_preview/plugin.py` | `hdx_hxl_preview` | "Quick Charts" | always `True` | `False`, excluded from v2 |

Rendering pipeline for the in-scope preview:

```
resource_read.html:132  → {% snippet 'package/snippets/resource_view.html' %}
resource_view.html:52   → <iframe data-module="data-viewer" src=...>
  (module: fanstatic/modules/data-viewer2.js — iframe resize + `data-viewer-error` pubsub handler)
[inside iframe] hdx_csv_preview_view.html  (extends v2/page.html, loads DataTables 2.x)
  <table id="hdx-csv-table"></table>
hdx_csv_preview.js:
  fetch('/hxl/api/data-preview.json?rows=0&sheet=0&url=' + encodeURIComponent(resourceUrl))
    .then(r => r.json())
    .then(response => {
      columns = response[0].map(h => ({ title: h }))     // row 0 = headers
      new DataTable('#hdx-csv-table', { data: response.slice(1), columns, pageLength: 10, ... })
    })
```

- `previewUrl`'s `resourceUrl` comes from a hidden div (`hdx_csv_preview_view.html:10`) rendering
  `h.url_for('resource.download', ...)` — the resource's own download URL, not a datastore reference.
- `/hxl/api/data-preview.json` is proxied to an **external HXL Proxy service**
  (`ckanext-hdx_theme/ckanext/hdx_theme/hxl/proxy.py:16`, `config.get('hdx.hxlproxy.url')`), fetching and
  parsing the raw resource file on the fly — this works for any CSV/XLS regardless of
  `datastore_active` and never touches `datastore_search`.
- All rows are fetched in one call (`rows=0` = unlimited); pagination (`pageLength: 10`) is client-side,
  DataTables-built-in.
- Table CSS: `hdx_csv_preview.css`, hand-styled to match `c-table`'s tokens (confirmed 1:1 against
  `.c-table-th-styles()`/`.c-table-td-styles()` mixins in `table.less`) because the iframe is a separate
  document that can't consume the parent page's `v2/components/table.html` snippet directly.
- **Error handling today is effectively none**: no `.catch()` on the fetch chain, no loading state, and
  `if (!response || !response[0]) return;` silently no-ops on empty/malformed payloads (blank table, no
  message).

### 1.3 Dead code note: `HDXChartViewsPlugin`

`ckanext-hdx_package/ckanext/hdx_package/plugin.py:769-853` — `view_type: hdx_chart_view`, title
"Line / Bar Chart", `can_view` gated on `resource.get('datastore_active') or resource.get('url') ==
'_datastore_only_resource'` (`plugin.py:795-798`), `requires_datastore: True`. This is the only
genuinely datastore-gated view in the codebase, but its declared templates
(`new_views/chart_view.html`, `new_views/chart_view_form.html`) do not exist anywhere in the repo, and
`ckanext-hdx_package` has no `templates/` directory at all — invoking this view would 500. It is still
declared in `ckan.plugins` (`hdx_chart_views`). **Not a usable precedent for TDE Preview** — flagged so
implementation doesn't assume it's a working reference.

### 1.4 Resource-type detection

No `resource.formatted_format` anywhere in this codebase. Format-to-preview mapping is entirely per-plugin
`can_view(data_dict)`, keyed on raw `resource['format'].lower()` (§1.2/1.3). The one flag genuinely
signaling "this resource has queryable tabular data in the datastore" is
**`res.datastore_active`**, already used to gate the API access section
(`resource_read.html:100,117,142`) and the anchor-nav "API" entry. `_data_explorer`
(`resource_read.html:12-19`) is computed independently — "first `resource_views` entry whose `view_type` is
not `hdx_hxl_preview`" — and is unrelated to `datastore_active`; a CSV resource that later becomes
datastore-active still has exactly one `ResourceView` row (the office-preview one), so there's no
"two eligible views" ambiguity to resolve (D5).

### 1.5 Table component (`c-table`)

- Snippet: `templates/v2/components/table.html` (37 lines) — renders
  `.c-table-container > .c-table__scroll > table.c-table` from `headers`/`rows` params.
- LESS: `hdx-styles/src/common/less/v2/components/table.less`, compiled to
  `fanstatic/v2/components/table.css`, part of the `v2-components-styles` bundle (already loaded on every
  v2 page, §D4).
- **Only current consumer**: the `/components` live component-library demo page. The CSV preview does
  **not** call this snippet (iframe isolation, §1.2) — it duplicates the same tokens in
  `hdx_csv_preview.css` instead. The new Data Dictionary section (not iframe-isolated) is the first real
  page-level consumer of this component (D3).

### 1.6 AJAX handling

No shared "call the action API" wrapper exists anywhere in the codebase — every call site hand-rolls its
own `$.ajax()`/`fetch()`. What is shared is a CSRF-token-lookup helper:
`ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/base/hdx-util-lib.js:113-133` —
`hdxUtil.net.getCsrfFieldName()`, `getCsrfToken()`, `getCsrfTokenAsObject()` (returns
`{'X-CSRFToken': token}`), reading the two meta tags rendered in `base.html`. Loaded on every page,
referenced by ~20 other JS files (v2 dataset-page.js, org-members-page.js, etc.) for their own POST calls.
Two other, independent implementations of the same meta-tag lookup exist in CKAN core
(`ckan.Client` in `public/base/javascript/client.js`, and `htmx-csrf.js`) but are not used by any v2/HDX
preview code.

### 1.7 CSRF handling

CKAN's stock Flask-WTF `CSRFProtect`, unmodified in mechanism by HDX (`flask_app.py:31,65,255-268`,
config defaults `WTF_CSRF_ENABLED=True`, `WTF_CSRF_FIELD_NAME=_csrf_token`,
`WTF_CSRF_METHODS=[POST,PUT,PATCH,DELETE]`, `WTF_CSRF_HEADERS=[X-CSRFToken, X-CSRF-Token]`). Token is
delivered via two meta tags rendered unconditionally in `base.html` (both CKAN core's and HDX theme's
copy), regardless of login state. HDX's only prior CSRF-adjacent changes are unrelated to this feature: a
config toggle (`ckan.csrf_protection.ignore_extensions`, currently `false` in this deployment) that could
bulk-exempt plugin blueprints, and a server-side CSRF-field stripper for form dicts
(`ckan/logic/__init__.py:158-172`, `ckanext-hdx_package/.../csrf_field_remover.py`). Neither is relevant to
D2's mechanism, which calls Flask-WTF's `validate_csrf()` directly inside a chained auth function rather
than relying on `CSRFProtect`'s automatic enforcement.

### 1.8 Datastore auth (HDX-10974)

Covered in Context above and §6 in full. Key file: `ckanext-hdx_package/ckanext/hdx_package/actions/authorize.py:186-229`.

### 1.9 API access section markup + the button-alignment bug

`resource_read.html:143-154`:

```jinja
<section class="hdx-v2-dataset-section" id="api-access">
  <div class="hdx-v2-dataset-section__header">
    <h2 class="hdx-v2-dataset-section__title">{{ _('API access') }}</h2>
    {% snippet 'v2/components/button.html', style='tertiary', size='m', label=_('See documentation'), ... %}
  </div>
  ...
```

`.hdx-v2-dataset-section__header` (`display:flex; justify-content:space-between`) is defined only in
`dataset-page.less:32-37`, bundled only as `v2-dataset-page-styles` (`webassets.yml:1596-1600`), which
`resource_read.html` never loads (`resource_read.html:48-51` loads only `v2-resource-page-styles` /
`resource-page.css`, which has no `.hdx-v2-dataset-section*` rules). Net effect: the flex rule never
applies on a live resource page, so the header falls back to block flow (h2, then the button anchor
stacked below it) instead of a flex row with the button pushed right. Fix: D4.

### 1.10 Analytics

Confirmed absent on preview/API-access areas; only the download button is instrumented. Full detail in D6.

---

## 2. Figma Mapping

Files: `resource-page-xl.html`, `resource-page-md.html`, `resource-page-sm.html`, plus the standalone
`resource-preview-table.html` and `table.html` already used as sources for task 047.

- **Section order (consistent across all three breakpoints)**: page header → anchor nav → **Resource
  preview** (generic sortable table + compact pager, same sample-data shape as `resource-preview-table.html`
  — Date/Location/Locality/Activity Type/Beneficiary/IDPs/etc.) → divider → **Data dictionary** (its own
  table, distinct columns) → divider → **API access**.
- **Resource preview table** (`resource-page-xl.html` ~207-960): `.table > .table-header
  (.table-cell-header × N, each with a `.table-sorter` chevron pair) + .wrapper (alternating-background
  `.component-N` rows) + a compact numbered pager (`.pagination-item`, chevrons + page numbers). This is
  the same structure `047` already mapped to `c-table`/DataTables — no new table design needed for the TDE
  branch, it's the same visual output regardless of which data source feeds it (D1).
- **Data dictionary table** (`resource-page-xl.html:963-1002`, `data-scroll-to="dataDictionaryContainer"`):
  same `.table`/`.table-header`/`.table-cell-header` structure as Resource preview, with **5 columns**:
  `Title`, `Column name`, `Data type`, `Unit of measure`, `Description`. Sample rows shown: `Year / year /
  "Year (YYYY)" / - / -` and `University / university / Text / - / -` — "Unit of measure" is dropped and
  "Data type" renders `field.type` verbatim rather than Figma's friendlier sample string (D7, D8).
- **API access** (`resource-page-xl.html:1270-1313`): `.api-access-parent` wraps the "API access" title and
  a "See documentation" button, with `justify-content: space-between` in the export's own CSS — confirming
  the button should be right-aligned (D4). The accompanying `gap: -9.5rem` on the same rule is a Figma
  static-export artifact (absolute-position-to-flex conversion noise), not an intentional value.
- **Responsive**: all three breakpoints keep the same section order and table column set; only the table's
  outer width and horizontal-scroll behavior change (§8). No breakpoint hides the Data Dictionary or Resource
  Preview sections.

---

## 3. Data Dictionary Strategy

**Source**: `GET /api/3/action/datastore_info?id={resource_id}` (D3, D2 for the anonymous-access header).

**Response shape** (CKAN core, unmodified contract — brief's "MUST NOT change API responses" is satisfied
trivially since nothing about the action itself changes): `result.fields[]`, each
`{id, type, info: {label, notes, type_override}}`.

**Mapping to the brief's "Expected Fields (TO VERIFY)"** — confirmed real:

| Brief's expected field | `datastore_info` source | Notes |
|---|---|---|
| field name | `field.id` | raw datastore column name |
| type | `field.type` | raw Postgres-ish type (`text`, `numeric`, `timestamp`, ...) |
| label | `field.info.label` | human-friendly display name, set via CKAN's Data Dictionary edit form; may be empty if never set |
| description | `field.info.notes` | free-text description; may be empty |

**Mapping to Figma's 5 columns** — 4 columns are shipped; "Unit of measure" is dropped (D7):

| Figma column | Mapping | Confidence |
|---|---|---|
| Title | `field.info.label` (fallback to `field.id` if empty) | clean |
| Column name | `field.id` | clean |
| Description | `field.info.notes` | clean |
| Data type | `field.type`, rendered verbatim (D8) — Figma's friendlier "Year (YYYY)" sample string is not replicated | clean |
| ~~Unit of measure~~ | **dropped (D7)** — no counterpart in `datastore_info`'s schema at all (vanilla CKAN's Data Dictionary has no "unit of measure" field) | n/a |

**Rendering**: reuse `v2/components/table.html`'s class contract directly (D3) — the JS fetch handler
builds `.c-table-container > .c-table__scroll > table.c-table` markup from a single column-definition list
(header + per-field accessor for each of the 4 columns above, D7) iterated once, rather than duplicating
the same 4 field accesses inline wherever the table is assembled.

**Behavior**: gated on `res.datastore_active` (D5) — both the section itself and its anchor-nav entry
(inserted between "Resource preview" and "API" in `resource_read.html`'s `secondary`/mobile `primary`
blocks, §1.4). Empty/missing schema (`result.fields` is empty or absent) → `initDataDictionary()` returns
without appending anything, so the section renders with no table and no message (not a broken table, but
also not an explicit empty-state message). A `c-spinner` shows while the AJAX call is in flight (D11); a
failed/malformed response is still handled the same way as before — silently renders nothing (§10).

---

## 4. TDE Preview Strategy

**Source**: `GET /api/3/action/datastore_search?resource_id={resource_id}&limit={n}&offset={m}` (D2 for
the anonymous-access header).

**Integration** (D1): same `hdx_office_preview` plugin, same iframe, same DataTables 2.x instance as
today's CSV preview — not a new resource view or section. `hdx_csv_preview_view.html` needs
`resource.datastore_active` and `resource.id` made available to the iframe (currently it only exposes the
resource's download URL via a hidden div, `hdx_csv_preview_view.html:10`) so `hdx_csv_preview.js` can
branch:

- **`datastore_active` true**: call `datastore_search`. Response `result.fields[]`/`result.records[]` feed
  DataTables **natively as object-array data** — `columns: result.fields.map(f => ({data: f.id, title:
  f.id}))`, `data: result.records` — no reshaping into the HXL-proxy's array-of-arrays format is needed
  (DataTables 2.x supports object-keyed row data directly).
- **`datastore_active` false**: keep today's HXL-proxy fetch exactly as-is, unchanged.

**Pagination — shipped as fetch-everything-once, not server-side (D12).** CKAN core defaults to
**100 rows per request** and hard-caps at **32000** unless `ckan.datastore.search.rows_max` is configured
higher (`ckanext/datastore/logic/action.py:566-570,674`, confirmed; not set in this deployment's config
files). The datastore-active branch requests `limit=32000` in a single `datastore_search` call
(`DATASTORE_FETCH_ALL_LIMIT`) and hands all rows to DataTables, which paginates client-side at
`pageLength: 10` — visually identical to today's HXL-proxy behavior, just pointed at `datastore_search`
instead of the HXL proxy. This still front-loads the full dataset into the browser on first load; genuine
server-side `limit`/`offset` pagination per page turn is deferred.
Column **sorting** on this branch is DataTables' own client-side sort over the already-loaded rows (D9),
not a server-side `sort` param. A `c-spinner` shows while the initial fetch is in flight (D11); there is
still no error handling — a failed or malformed response silently no-ops, same as the pre-existing gap in
the non-datastore branch (§1.2).

**Table rendering / styling**: identical DataTables instance and CSS (`hdx_csv_preview.css`) as the
non-datastore branch — no new visual component, matching the brief's "MUST reuse existing table component"
and Figma showing one visual design for "Resource preview" regardless of data source.

---

## 5. Conditional Logic Strategy

Per D5: `res.datastore_active` — already computed by CKAN core, already consumed by
`resource_read.html` to gate the API access section — is the single detection flag for:

1. Which data source the "Resource preview" iframe's JS fetches from (§4).
2. Whether the new Data Dictionary section + anchor-nav entry render at all (§3).

No new server-side detection logic is introduced. No ambiguity between "two eligible resource views"
arises, because the branch lives **inside** the single existing `recline_view` `ResourceView` row's
rendering, not in `resource_read.html`'s view-selection logic (`_data_explorer`,
`resource_read.html:12-19`), which is untouched.

---

## 6. CSRF Strategy

Per D2. This section states the mechanism precisely because it is a security-relevant change accepted by
the user with an explicit trade-off — it must not be softened or generalized in implementation.

- **How the token is obtained (client)**: the existing shared helper,
  `hdxUtil.net.getCsrfTokenAsObject()` (`hdx-util-lib.js:113-133`) — no new client-side CSRF mechanism.
- **How it is passed**: as an `X-CSRFToken` request header on the `fetch`/`$.ajax` **GET** calls to
  `datastore_search` and `datastore_info` (§3, §4). GET is used deliberately (matching the existing
  anonymous-GET precedent in CKAN core's `resource-view-filters.js` select2 dropdowns) — this call does
  not depend on `CSRFProtect`'s automatic method-based enforcement at all, since validation happens
  explicitly inside the auth function, not via Flask-WTF's request lifecycle hook.
- **How it is validated (server)**: inside the two modified chained auth functions in
  `authorize.py` (`datastore_search`, `datastore_info` only — **not** `datastore_search_sql`, which stays
  untouched). Where today's `_datastore_search_only_for_authenticated_users` immediately returns
  `{'success': False, ...}` for any non-authenticated `context['auth_user_obj']`, the modified version
  first attempts `flask_wtf.csrf.validate_csrf(token)` (token read from
  `flask.request.headers.get('X-CSRFToken')` / `X-CSRF-Token`) — on success, falls through to
  `next_auth(context, data_dict)` (CKAN core's own anonymous-permissive `resource_show`-delegating check,
  `ckanext/datastore/logic/auth.py:50-73`); on failure or missing token, returns the existing rejection
  message unchanged. Authenticated calls are entirely unaffected — the `is_authenticated` branch still
  short-circuits straight to `next_auth` exactly as today.

**Security trade-off — stated explicitly, not glossed over (D2)**: CSRF tokens are issued to **every**
visitor, authenticated or not, simply by loading any HDX page (`base.html:27-28`,
`hdx_theme/.../base.html:107-108`). So this change does not require authentication, only "has loaded a
page on this site" — a materially weaker bar than HDX-10974's original, ticketed intent
("only authenticated users should be allowed to access the datastore_search\* actions"). It does **not**
open these actions to arbitrary third-party/anonymous API scraping in the way *removing* HDX-10974
entirely would — a bare `curl` with no valid session-bound token is still rejected — but a trivial script
that first performs one GET of any HDX page to harvest a token, then replays it, fully bypasses the
intended restriction. This is the accepted cost of matching the brief's literal ask; §9 carries it forward
as a standing risk to monitor. `datastore_search_sql` is permanently excluded from this exception (D10) —
not a candidate for future extension.

---

## 7. Component Strategy

**Reuse as-is:**

| Component | Usage |
|---|---|
| `hdxUtil.net.getCsrfTokenAsObject()` (`hdx-util-lib.js`) | CSRF header on both new AJAX calls (§3, §4, §6) |
| `v2/components/table.html` (`c-table`) | Data Dictionary table markup contract (§3) — first real page-level consumer |
| Existing DataTables 2.x + iframe pipeline (`hdx_office_preview`) | TDE Preview — branched, not forked (§4) |
| `v2/components/anchor-links.html` | New "Data dictionary" nav entry, same pattern as existing "Resource preview"/"API" entries |
| `v2/components/button.html` / `text-button.html` | API access section — untouched except for the alignment fix (D4), no new button variants needed |

**Extend only if needed:**

| What | Why |
|---|---|
| `dataset-page.less`'s `.hdx-v2-dataset-section` block → new shared components partial (D4) | Fixes the button-alignment bug without shipping unrelated dataset-page-only CSS to the resource page |
| `hdx_csv_preview.js` / `hdx_csv_preview_view.html` | Add the `datastore_active` branch (§4) — same files task 047 already touched, no new files needed for TDE itself |

**Built:** a `c-spinner` component (D11), used for the Data Dictionary AJAX load and the TDE branch's fetch
(§3, §4, §10). Error handling for either is still not built; this gap is accepted as-is.

**Do not:**

- Do not create a new table/grid system for either feature — both consume `c-table`'s existing class
  contract (directly for Data Dictionary, via the already-established CSS-duplication pattern for the
  iframe-bound TDE/CSV preview).
- Do not register a new `IResourceView` plugin for TDE Preview (D1).
- Do not introduce a new CSRF mechanism beyond calling the existing `hdxUtil.net` helper client-side and
  Flask-WTF's own `validate_csrf()` server-side (D2/§6).
- Do not touch `datastore_search_sql`'s auth behavior (§6).

---

## 8. Responsive Strategy

Per the Figma exports (§2), section order and table column sets are identical across breakpoints — only
table width/overflow handling changes:

- **XL**: full-width table, all columns visible without scrolling in the sample data shown.
- **MD**: same table structure; narrower viewport means more columns are likely to require horizontal
  scroll depending on the resource's actual schema/data — apply the same `overflow-x: auto` wrapper
  pattern task 047 already established for the CSV preview table (`.c-table__scroll` /
  `.dt-layout-row.dt-layout-table > .dt-layout-cell`).
- **SM**: same structure, same horizontal-scroll fallback; no column-hiding behavior is shown in any
  export — all columns remain present, just scrollable, consistent with 047's decision for the existing
  preview table.
- This applies identically to both the Resource Preview table (DataTables, either data source) and the new
  Data Dictionary table (`c-table`) — same `.c-table__scroll`/DataTables horizontal-scroll mechanism, no
  divergent responsive behavior between the two.

---

## 9. Risks

- **Breaking the existing CSV preview** ❗ — mitigated by construction: D1 makes the datastore branch
  strictly additive (`if datastore_active { ... } else { <unchanged existing code> }`); the non-datastore
  path is not touched.
- **Incorrect data rendering** — resolved: the Data Dictionary drops "Unit of measure" entirely (D7) and
  renders "Data type" as `field.type` verbatim, no friendly mapping (D8). No open mapping questions remain.
- **Security regression** ❗ — D2/§6's CSRF-as-anonymous-gate is a confirmed, accepted weakening of
  HDX-10974's original authenticated-only intent for `datastore_search`/`datastore_info` specifically.
  Risk to actively guard against during implementation: scope creep that accidentally extends the same
  exception to `datastore_search_sql` or to any other caller of these two actions beyond the resource
  preview/data dictionary AJAX calls (e.g. if the modified auth function is later reused elsewhere without
  re-reading this trade-off).
- **Performance** ❗ — live exposure, not just a hypothetical: the datastore-active branch requests
  `limit=32000` in a single `datastore_search` call (D12) and loads every row into the browser before
  DataTables paginates client-side, same "fetch everything" shape as the HXL-proxy path it replaces for
  this branch. A resource near the 32000-row cap makes this one call slow and front-loads a large payload;
  server-side `limit`/`offset` pagination (originally decided) would have avoided this and remains deferred.
- **Analytics regression** ❗ — none possible per D6 (nothing exists on this page's preview/API-access
  areas today); risk is limited to accidentally adding untracked-elsewhere instrumentation that then
  becomes an inconsistency with the rest of the page.
- **Sort behavior divergence** — column sort on the TDE branch is DataTables' client-side sort (D9) over
  the fully-loaded dataset from the single fetch above, so it stays a working feature on both branches, just
  not via the server-side `sort` param originally decided.

---

## 10. Edge Cases

| Case | Handling |
|---|---|
| Empty datastore schema (`datastore_info` returns no fields) | `initDataDictionary()` returns early — no table, no empty-state message; accepted as-is per D11 |
| Resource is datastore-active but has zero rows | TDE branch: DataTables' own default "No data available in table" message shows in the empty `tbody`, same as the non-datastore branch — no custom empty-state handling added |
| Large dataset (near/at the `rows_max` cap) | Not mitigated — the datastore branch requests `limit=32000` in one call (D12), i.e. it can fetch right up to the cap in a single request rather than one page at a time; server-side pagination remains deferred |
| Missing schema fields (`info.label`/`info.notes` empty for a column) | Fall back to `field.id` for Title, blank/"-" for Description — matches Figma's own sample rows showing "-" for unset cells |
| Slow API responses | Handled via a `c-spinner` (D11), shown for both the Data Dictionary AJAX call and the TDE branch's initial fetch, hidden on success |
| Anonymous/unauthorized access | Governed entirely by D2/§6's CSRF-token exception; authenticated users are unaffected; anonymous users without a valid session-bound token still see the existing "requires an authenticated user" rejection |
| Malformed `datastore_search`/`datastore_info` response | Still silently no-ops, same as today's HXL-proxy fetch (§1.2) — `initDataDictionary()`/`loadFromDatastore()` both return early on a falsy/unsuccessful response with no inline error message; accepted as-is per D11 |

---
