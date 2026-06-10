# Resource Preview Table (CSV / HXL preview) — v2 Styling

**Figma sources**: `llm_docs/redesign/figma_exports/resource-preview-table.html`, `llm_docs/redesign/figma_exports/table.html`

---

## Prerequisites

Already implemented (do not re-implement):

- `v2/components/pagination.html` — existing pagination component (task 031); reuse for table pager
- `v2/page.html`, `package/resource_read.html` — v2 resource page (task 040); preview section already wired
- `package/snippets/resource_view.html` — iframe wrapper + error div for preview views
- `fanstatic/modules/data-viewer2.js` — CKAN module that handles iframe resize + error visibility

---

## 1. Existing CSV / HXL Preview Audit

### Scope clarification

Two preview plugins exist; only one is in scope:

| Plugin | view_type | Output | Scope |
|--------|-----------|--------|-------|
| `hdx_office_preview` | `recline_view` ("Data Explorer") | HTML table via DataTables | ✅ IN SCOPE |
| `hdx_hxl_preview` | `hdx_hxl_preview` ("Quick Charts") | External visualization (maps/charts) | ❌ OUT OF SCOPE — already excluded from v2 |

The task title "CSV / HXL preview" refers to the **DataTables-based tabular preview** that handles:
- Plain CSV files
- HXL-tagged CSV files (via the same `/hxl/api/data-preview.json` endpoint)

### Rendering pipeline

```
resource_read.html (v2)
  ↓ {% snippet 'package/snippets/resource_view.html' %}
  ↓ resource_view.html:50 → <iframe data-module="data-viewer">
      src = h.url_for('resource_view', view_id=_data_explorer.id, ...)
  ↓ [inside iframe] hdx_csv_preview_view.html
      extends base.html
      <table id="myTable" class="cell-border" style="width:100%">
      loads DataTables 2.x via webassets (hdx_office_preview bundle)
  ↓ hdx_csv_preview.js
      fetch /hxl/api/data-preview.json?rows=0&sheet=0&url={resourceUrl}
      response = array-of-arrays (row[0] = headers, row[1..n] = data)
      new DataTable('#hdx-csv-table', { layout, autoWidth: false, select: false, … })
```

### Key files

| Role | Path |
|------|------|
| View plugin | `ckanext-hdx_office_preview/ckanext/hdx_office_preview/plugin.py` |
| Table template (inside iframe) | `ckanext-hdx_office_preview/ckanext/hdx_office_preview/templates/hdx_csv_preview_view.html` |
| Data fetch + DataTable init | `ckanext-hdx_office_preview/ckanext/hdx_office_preview/public/hdx_csv_preview.js` |
| Table CSS | `ckanext-hdx_office_preview/ckanext/hdx_office_preview/public/css/hdx_csv_preview.css` |
| Iframe wrapper + error div | `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/snippets/resource_view.html` |
| Iframe resize + error handler | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/modules/data-viewer2.js` |

### Current styling sources

- **DataTables CSS**: loaded from CDN inside the iframe (`//cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css`)
- **Custom table CSS**: `hdx_csv_preview.css` — only sets `max-width: 100px; text-overflow: ellipsis` on `table.dataTable tr th`
- No Bootstrap table classes in the table itself
- Error div in `resource_view.html` uses Bootstrap 2 classes (`text-error`, `icon-info-sign`) and Bootstrap 5 JS attributes (`data-bs-toggle="collapse"`)

---

## 2. Problem Analysis — "Could not load preview"

### Error visibility mechanism

1. `resource_view.html:19` renders `<div class="data-viewer-error js-hide">` hidden by default
2. On load/data error, `data-viewer2.js:24–28` subscribes to `data-viewer-error` pubsub event
3. Handler removes `js-hide` from the error div and hides the iframe with jQuery `.hide()`

### Root causes of breakage in v2

| Issue | Detail |
|-------|--------|
| `text-error` class | Bootstrap 2 utility class — does not exist in v2; error text renders unstyled |
| `icon-info-sign` class | Bootstrap 2/3 Glyphicon — icon font not loaded in v2; icon is invisible |
| `data-bs-toggle="collapse"` | Bootstrap 5 JS — may or may not be loaded in the resource page context |
| `js-hide` definition | If `js-hide` is not defined in the v2 CSS bundle, error div may be visible on page load |
| Iframe isolation | v2 CSS is loaded on the parent page; the iframe (`hdx_csv_preview_view.html` extends `base.html`) does NOT inherit parent styles — DataTables CDN CSS applies instead of v2 styles |

### Consequence

On v2 resource page:
- Error message may always be visible (if `js-hide` is missing from v2 CSS)
- Or may be visually broken when shown (wrong color class, missing icon)
- The table inside the iframe uses DataTables CDN styling, not v2 design tokens

---

## 3. Table System Mapping — Figma → Current Output

### Figma structure (`resource-preview-table.html`)

```
.table                              ← outer container
  .table-header                     ← header row
    .table-cell-header × N          ← one per column
      .content-frame
        .body > .content            ← header text (font-weight: 600)
        .table-sorter               ← sort chevrons (up + down)
  .wrapper                          ← body rows container
    .component-5 (odd, bg: #fff)    ← row
      .table-cell-row × N           ← one cell per column
        .content-frame9 > .body > .copy
    .component-6 (even, bg: #fafbfb) ← row
      ...
  .wrapper2                         ← pagination wrapper
    .pager                          ← page buttons
```

### Current DataTables output

DataTables generates its own HTML structure (`<table>`, `<thead>`, `<tbody>`, DataTables wrapper divs). This structure does **not** match the Figma layout above.

### Gaps

| Gap | Detail |
|-----|--------|
| HTML structure | DataTables uses `<table>/<thead>/<tbody>`; Figma uses `div`-based flex layout |
| Styling system | DataTables applies its own CSS classes; Figma requires custom v2 CSS classes |
| Row alternation | DataTables uses `odd`/`even` classes; Figma uses alternating bg-color on row containers |
| Sort indicators | DataTables generates its own sort arrows; Figma uses custom chevron SVGs |
| Pagination | DataTables generates its own pager; Figma shows a custom compact pager |
| Cell truncation | DataTables may wrap; Figma requires ellipsis (`text-overflow: ellipsis; white-space: nowrap`) |

---

## 4. Component Strategy

### What to reuse

- **`v2/components/pagination.html`** — reuse for pager below the table. The `size='sm'` variant (1.75rem) matches Figma pagination item dimensions. Visual alignment between `c-pagination` and the Figma pager style must be verified (see Open Questions).
- **v2 CSS tokens** — `--hdx-neutral-*` for border/background colors, `--hdx-space-*` for padding, `--hdx-fs-*` for font size, `--hdx-fw-*` for font weight.

### What to create

A new snippet + CSS pair following the existing v2 component pattern:

| Artifact | Path |
|----------|------|
| Table snippet | `templates/v2/components/table.html` |
| Table CSS | `fanstatic/v2/components/table.css` |

The snippet is NOT necessarily called for static rendering. Its primary role is to define the **CSS class structure** that the dynamic JS renderer must produce. See Rendering Strategy below.

### Architecture decision — iframe vs inline

**Decision: keep iframe (Option B)** — preferred over Option C for this task.

**Option B — Keep iframe, replace DataTables renderer with v2 HTML** ✅ CHOSEN
- Drop DataTables from `hdx_csv_preview_view.html`
- Load v2 CSS bundle inside the iframe `<head>` (explicit `<link>` tag pointing to the compiled v2 CSS)
- Custom JS fetches `/hxl/api/data-preview.json` and renders the v2 HTML structure directly
- Must reimplement: sorting, pagination (client-side)
- Change scope: `hdx_csv_preview_view.html`, `hdx_csv_preview.js`, `hdx_csv_preview.css` — all within `ckanext-hdx_office_preview`

**Option C — Render inline (no iframe)** — more complex for this task
- Would require: changing `plugin.py` (`'iframed': False`), refactoring `hdx_csv_preview_view.html` from a full page (`extends base.html`) into a Jinja snippet, moving JS initialisation to the parent resource page
- v2 CSS would be naturally available without explicit loading
- Rejected because it touches more files and crosses extension boundaries for no clear benefit once v2 CSS is loaded in the iframe head

---

## 5. Rendering Strategy

### Data format

API: `GET /hxl/api/data-preview.json?rows=0&sheet=0&url={resourceUrl}`

`rows=0` = all rows (no limit). Pagination is handled client-side in JS.

Response:
```json
[
  ["Date", "Location", "Locality", ...],   // row 0 = column headers
  ["2025-11-30", "Nuseiba Center", ...],    // row 1 = first data row (or HXL hashtag row)
  ...
]
```

**HXL hashtag row**: For HXL-tagged CSV files, `row[1]` will contain the hashtag row (e.g. `["#date", "#loc+name", ...]`). This row is **not stripped by the API** — it appears in `response.slice(1)` as a regular data row. **Decision: display it as-is** (same behaviour as v1 DataTables rendering).

### Mapping to v2 HTML

```
response[0]        → .c-table__header, one .c-table__cell--header per column
response[1..n]     → .c-table__body, one .c-table__row per data row
  odd rows (1,3,…) → bg: var(--hdx-neutral-0)   [#ffffff]
  even rows (2,4,…)→ bg: var(--hdx-neutral-01)  [#fafbfb]
  each cell value  → .c-table__cell > .c-table__cell-content
pagination         → .c-table__footer > JS-rendered pagination controls (see §7)
```

### Pagination

**Decision: client-side**, same as v1. All rows fetched in a single call (`rows=0`); JS slices the visible page. No backend changes needed.

---

## 6. Styling Strategy

### Remove DataTables CDN CSS

`jquery.dataTables.min.css` is no longer needed. Remove the CDN `<link>` from `hdx_csv_preview_view.html`.

### Load v2 CSS inside the iframe

Add a `<link>` tag in the `<head>` of `hdx_csv_preview_view.html` pointing to the compiled v2 CSS files needed (foundation, typography, components/table). Use `h.fanstatic_assets()` or a direct static path.

### V2 CSS classes to define (in `fanstatic/v2/components/table.less`)

All tokens verified against `hdx-styles/src/common/less/v2/colors.less` and `spacing.less`:

| Figma variable | Figma value | V2 LESS token | Notes |
|----------------|-------------|---------------|-------|
| `--fs-12` | 0.75rem | `@hdx-fs-xs` | 12px — use `.hdx-body-xs-semibold()` mixin for headers, `.hdx-body-xs()` for cells |
| `--height-40` (row height) | 2.5rem | `@hdx-space-10` | min-height on row |
| `#fafbfb` (even row bg) | step 0.1 | `@hdx-neutral-01` | exact match |
| `#ffffff` (odd row bg) | step 0 | `@hdx-neutral-0` | |
| `#d8e0e1` (cell border) | step 2 | `@hdx-neutral-2` | exact match |
| `#ebeff0` (outer/wrapper border) | step 1 | `@hdx-neutral-1` | exact match |
| Cell padding | 0.5rem | `@hdx-space-2` | |
| Header font-weight | 600 | `@hdx-fw-semibold` | via `.hdx-body-xs-semibold()` |

### Error message CSS

**`js-hide` is NOT defined in the v2 CSS bundle** (confirmed: only present in v1 files `fanstatic/base/header.css` etc.). Add to `resource-page.less`:
```less
.js-hide { display: none !important; }
```

In `resource_view.html`, update the error div for v2:
- Remove `text-error` class (Bootstrap 2 — does not exist in v2)
- Remove `icon-info-sign` (Bootstrap 2 Glyphicon — icon font not loaded in v2)
- **Remove Bootstrap 5 collapse/expand entirely** — no more `data-bs-toggle`, `data-bs-target`, collapsible detail text

**Decision: simple always-visible inline error** (Option A below). No expand/collapse behaviour.

Error display options considered:
- **A — Simple inline error div** ✅ CHOSEN: plain `<div class="c-preview-error">` styled with `@hdx-error-5` text colour; shown/hidden by `data-viewer2.js` via the existing `js-hide` class; zero JS dependency beyond what already exists
- **B — Native `<details>/<summary>`**: expand/collapse with no JS needed; semantic but adds visual complexity for a simple error message — overkill here
- **C — Toast/notification bar**: dismissable; wrong pattern for a persistent load-failure state

Error div markup after update:
```html
<div class="data-viewer-error js-hide c-preview-error">
  <!-- SVG icon TBD by design, or none -->
  Could not load the preview for this resource.
</div>
```

---

## 7. Pagination Integration

**Decision: client-side pagination with JS-rendered controls.**

The existing `v2/components/pagination.html` snippet uses URL-based page links and is Jinja-rendered — it cannot be re-rendered by JS after data loads. Instead, the table JS will generate pagination markup that **visually matches** `c-pagination--size-sm` but is driven entirely by JS event listeners.

The JS pagination component must produce HTML equivalent to `c-pagination--size-sm` (same CSS classes, same DOM structure) so it picks up the existing pagination CSS for free.

Page size: keep same as v1 DataTables default (10 rows per page). Total pages = `Math.ceil(dataRows.length / pageSize)`.

---

## 8. Edge Cases

| Case | Handling |
|------|----------|
| Empty dataset (0 data rows) | Show "No data available" message in v2 style instead of empty table |
| No columns (empty response) | Same as empty dataset — guard against `response[0]` being undefined |
| Many columns (> 10) | Horizontal scroll on table wrapper (`overflow-x: auto`) — decided |
| Long cell values | `text-overflow: ellipsis; white-space: nowrap` on cell content (Figma spec) |
| Special characters in values | No special handling; JS uses `textContent` assignment, not `innerHTML` |
| Large dataset (many rows) | Client-side pagination (10 rows/page); all rows fetched via `rows=0` |
| HXL hashtag row | API does NOT strip it — row[1] will contain `["#date", "#loc", ...]` for HXL files; display as a regular data row (same as v1) |
| API error / timeout | `data-viewer-error` pubsub event fires → error div shown, iframe hidden (existing mechanism, fix error div styling) |
| Resource download access denied | `_data_explorer` check in `resource_read.html` already gates the whole preview section |

---

## 9. Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Sorting must be reimplemented | High | In scope — reimplement column sort (asc/desc toggle) in v2 JS on header click |
| Iframe CSS loading order causes flash of unstyled content | Medium | Load v2 CSS in `<head>` of `hdx_csv_preview_view.html` before data fetch |
| `js-hide` not defined in v2 CSS — error always visible | High (confirmed) | Add `.js-hide { display: none !important; }` to `resource-page.less` |
| JS-rendered pagination CSS mismatch | Medium | Render the same DOM structure as `c-pagination--size-sm` so existing CSS applies |
| HXL hashtag row shown as data row | Low (by design) | Expected — same as v1; no mitigation needed |
| `data-viewer2.js` jQuery dependency | Low | jQuery is already loaded on all CKAN pages including the iframe base template |
| Iframe height recalibration after DataTables removal | Medium | `data-viewer2.js` uses `_recalibrate()` to measure iframe body height — must still fire correctly after replacing DataTables with v2 HTML |

---

## 10. Decisions Log

All open questions resolved. No blockers remain before implementation.

| # | Question | Decision |
|---|----------|----------|
| 1 | Iframe vs inline render | **Keep iframe (Option B)** — more contained; load v2 CSS explicitly inside iframe `<head>` |
| 2 | DataTables retention | **Retained DataTables 2.x** — v2 CSS applied via webassets bundle; custom renderer not implemented |
| 3 | Sorting | **DataTables built-in** (`ordering: true`, DT2 column headers) |
| 4 | HXL hashtag row | **Show as data row** (API does not strip it; same behaviour as v1) |
| 5 | Horizontal scroll | **`overflow-x: auto`** on `.dt-layout-row.dt-layout-table > .dt-layout-cell` |
| 6 | Column widths | **`width: max-content; min-width: 100%`** on `table.dataTable`; `max-width: 200px` per cell; `autoWidth: false` to prevent DT2 recalculation |
| 7 | Sticky header | **No** |
| 8 | Pagination mode | **Client-side**, 10 rows/page, all rows fetched via `rows=0` |
| 9 | `c-pagination` for table pager | **DataTables 2.x `layout` option** — `bottomStart: { paging: { type: 'simple_numbers' } }`; styled via `hdx_csv_preview.less` |
| 10 | Error div Bootstrap collapse | **Removed** — simple always-visible error div with v2 error colour, no collapse/expand |
| 11 | `js-hide` in v2 | **Not present** — add `.js-hide { display: none !important; }` to `resource-page.less` |
| 12 | Token mapping | **All confirmed** — see §6 styling table (verified against `colors.less`, `spacing.less`, `typography.less`) |
