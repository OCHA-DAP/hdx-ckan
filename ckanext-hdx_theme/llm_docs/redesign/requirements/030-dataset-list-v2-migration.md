# Task 030: Dataset list v2 migration — layout + dataset-card integration

## Goal

Migrate the search results dataset list to the v2 layout system and replace individual dataset list items with the existing `c-dataset-card` component. Filters, sorting, pagination, and ordering are explicitly out of scope for this task.

---

## Scope

**In:**
- Page/layout base: wrap the results section in v2 layout (`hdx-v2-container`, no Bootstrap grid)
- Dataset listing: replace current `<ul>` item loop with `c-dataset-card` snippet calls
- Data mapping layer: new Jinja2 snippet that maps `package` object → `dataset-card` parameters
- Any required extensions to `c-dataset-card` identified during mapping
- LESS for the v2 dataset list layout section

**Out (explicitly deferred):**
- Filters sidebar (`.col-3` / `#search-page-filters`)
- Sorting controls (`package_search_order.html`)
- Pagination (`c-pagination` or existing paginator)
- Items-per-page selector
- Archived tabs
- Results count / "no results" state
- Admin view (`package_item_admin.html`)
- Light/mobile theme (`light/snippets/package_list.html`)

---

## Files Affected

| File | Change |
|---|---|
| `templates/search/search.html` | Extends `v2/page.html` |
| `templates/search/snippets/package_list.html` | Results `<ul>` replaced with `<div class="c-dataset-card-list">`; routes to `package_item_v2.html` for non-admin view |
| `templates/search/snippets/package_item_v2.html` | **New.** Maps `package` → `c-dataset-card` params; calls `v2/components/dataset-card.html` |
| `templates/v2/components/dataset-card.html` | Extended: `query` param for highlight support; `requestdata` format type |
| `less/v2/components/dataset-card.less` | Owns the `.c-dataset-card-list` wrapper layout and its `.highlight` rule |
| `helpers/helpers.py` | New `render_date_range_label()` helper |
| `plugin.py` | Registered `render_date_range_label` |

`package_item.html` is **untouched** — migration is progressive. No new webassets bundle needed; `v2/styles.css` is already included in `v2-page-styles`.

**Referenced (read-only):**
- `hdx-styles/src/common/less/v2/components/dataset-card.less` — no changes needed
- `fanstatic/v2/components/clamped-text.js`
- `templates/home/index.html` — migration pattern reference

---

## Current Implementation Analysis

### Templates
- **Main entry:** `search/snippets/package_list.html` — renders the filter form, filter sidebar (`col-3`), and results column (`col-9`) using Bootstrap grid
- **Item:** `search/snippets/package_item.html` — renders a single `<li class="dataset-item">` per package
- **Icons/metadata:** `search/snippets/package_icons.html` and `package_icons_cod.html` — subnational label, COD badge, download count, trending indicator, page/link lists

### Data available on `package` in search results

| Field | Type | Notes |
|---|---|---|
| `package.id`, `package.name` | string | |
| `package.title` | string | |
| `package.notes` | string | raw markdown |
| `package.organization.name`, `.title` | string | |
| `package.groups` | list of dicts | `[{name: 'tur', title: 'Türkiye', ...}]` — location countries |
| `package.subnational` | string | `'1'` if subnational |
| `package.dataset_date` | string | concat date range (e.g. `'01012023-31122023'`) |
| `package.resources` | list | each resource has `format` key |
| `package.cod_level` | string | `'cod'`, `'cod-enhanced'`, or absent |
| `package.private` | bool | |
| `package.archived` | bool | |
| `package.is_requestdata_type` | bool | metadata-only / by-request |
| `package.approx_total_downloads` | int | |
| `package.pageviews_last_14_days` | int | |
| `package.batch_length` | int | stacked datasets count |
| `package.batch_url` | string | URL for stacked datasets |
| `package.page_list` | list | showcases this dataset belongs to |
| `package.links_list` | list | linked pages |

### Helpers used
- `h.url_for('dataset.read', id=package.name)` — package URL
- `h.url_for('organization.read', id=package.organization.name, ...)` — org URL
- `h.markdown_extract(package.notes, extract_length=truncate)` — plain-text description
- `h.render_date_from_concat_str(package.dataset_date)` — formatted date string
- `h.dict_list_reduce(package.resources, 'format')` — deduplicated format list
- `h.hdx_show_singular_plural(n, singular, plural)` — batch label text

### JS preserved (no changes)
- `google-analytics.js` — Mixpanel `search` event fired on filter change; do not touch
- `list-header.js` — filter header interactions; out of scope for this task
- `search-facets.js` — facet click handling; out of scope
- `v2/components/clamped-text.js` (shared module)

---

## Figma Analysis (dataset-list.html)

The Figma export shows:
- **Outer wrapper:** full-width flex column, `gap: 2rem` (card list + pagination block)
- **Card list:** flex column, `gap: 1rem`
- **Card body:** flex row, left column fixed `30.688rem` / right fills remaining, `gap: 2.5rem`
- **Left column:** org name → title (18px, 600, single-line ellipsis) → "Show more" button
- **Right column:** location badges (cyan) + sub-national badge (grey) → date → format badges

No filters, no sort controls, no results header are shown in the Figma export (confirmed out of scope).

---

## Figma vs Current — Key Differences

| Aspect | Current | Figma (v2)                                         | Action |
|---|---|----------------------------------------------------|---|
| **Location labels** | NOT shown | Shown (cyan badges)                                | **New field** — map from `package.groups` |
| **Layout** | Bootstrap `col-3 / col-9` grid | Flex + `.hdx-v2-container`                            | Replace grid wrapper |
| **List element** | `<ul class="dataset-list unstyled">` | `<div>` flex column                                | Replace with div |
| **Title overflow** | Up to 2 lines (JS `hdx_show_more_lines`) | Up to 2 lines (LESS `dataset-card.less`)           | v2 CSS handles this |
| **Trending indicator** | Icon + text shown | Not shown | Dropped |
| **Download count** | Text shown | Not shown | Dropped |
| **"By Request Only"** | Appended to title text | Title suffix + `requestdata` badge (`unlock.svg`) | Implemented |
| **Private lock icon** | Icon in title area | Lock badge in formats row | Remapped to `private` format type |
| **Archived icon** | Folder icon in title area | Badge in formats row | Implemented with `placeholder.svg` |
| **Format badges** | Text-only, no icons | Icon + text | Implemented with icon mapping |
| **COD/COD+** | Text via `package_icons_cod.html` | Dark label badge in formats | Merged into formats list |
| **Query highlighting** | `data-module="highlight"` on title/desc | No hook shown in Figma | Preserved via `query` param on component |
| **Batch / "show others"** | `stacked-info` section with `batch_url` | `c-dataset-card__footer` | Maps directly |
| **page_list / links_list** | "Part of [showcase]" text | Not shown | Dropped from list view |

---

## Data Mapping: `package` → `c-dataset-card` params

The new `package_item_v2.html` snippet computes these values before calling `dataset-card.html`.

```
org_name          = package.organization.title or package.organization.name
                    → '' if no organization

org_href          = h.url_for('organization.read', id=package.organization.name,
                               sort='metadata_modified desc')
                    → '' if no organization

title             = package.title or package.name
                    → See Open Question #2 for is_requestdata_type suffix

title_href        = h.url_for('dataset.read', id=package.name)

description       = h.markdown_extract(package.notes, extract_length=0)
                    → full first paragraph, markdown stripped
                    → '' if no notes (omits description section entirely)

location          = (computed)
                    if len(package.groups) == 1  → package.groups[0].title
                    if len(package.groups) > 1   → "Multiple locations"
                    if len(package.groups) == 0  → ''
                    → See Open Question #5 on availability in search results

subnational       = (package.subnational == '1')

date_range        = h.render_date_range_label(package.dataset_date)
                    → "Data from 22 Jan 2020 to 09 Mar 2023" (abbreviated month)
                    → '' if no date (omits date section)

formats           = (computed — see Format Mapping below)

formats_overflow  = max(0, total_format_count - MAX_VISIBLE)
                    → See Open Question #6 on MAX_VISIBLE

show_others_label = h.hdx_show_singular_plural(package.batch_length,
                      'other recently updated dataset',
                      'other recently updated datasets')
                    + ' from ' + (package.organization.title or package.organization.name)
                    → '' if package.batch_length is 0 or None

show_others_href  = package.batch_url
                    → '#' if not batch
```

---

## Format Mapping Logic

Build the `formats` list in priority order. The component renders them left-to-right.

**Step 1 — Package-level flag badges (before resource formats):**

```
if package.private:
    append {type: 'private', text: '', icon_src: 'v2/icons/lock.svg'}

if package.archived:
    append {type: 'archived', text: '', icon_src: ???}
    → See Open Question #3

if package.cod_level == 'cod':
    append {type: 'cod', text: 'COD', icon_src: ''}

if package.cod_level == 'cod-enhanced':
    append {type: 'cod_plus', text: 'COD+', icon_src: ''}
```

**Step 2 — Resource format badges:**

```
for format_str in h.dict_list_reduce(package.resources, 'format'):
    icon_src = format_to_icon(format_str)    ← helper / lookup dict
    append {type: 'extension', text: format_str, icon_src: icon_src}
```

**Step 3 — Truncation and overflow:**

```
total            = len(all_formats_before_truncation)
MAX_VISIBLE      = 3
formats          = formats[:MAX_VISIBLE]
formats_overflow = max(0, total - MAX_VISIBLE)
```

**Format → icon mapping** (implement as Jinja2 lookup dict or Python helper):

| Format strings (case-insensitive) | Icon SVG |
|---|---|
| CSV, XLSX, XLS, ODS, TSV | `v2/icons/tabular-format.svg` |
| SHP, GEOJSON, KML, KMZ, GEOPACKAGE, GPKG, GEOTIFF, GEODATABASE, GDB | `v2/icons/geographic-format.svg` |
| PDF, DOC, DOCX | `v2/icons/document-format.svg` |
| All others | `v2/icons/other-format.svg` |

**Note:** Jinja2 for-loop scoping requires a `namespace` object to accumulate resource badges inside the loop before merging into `formats_val` after `{% endfor %}`.

---

## Layout Requirements

### Page Base
- Extends `v2/page.html` (same pattern as homepage)
- CSS lives in `v2/styles.css` — already bundled in `v2-page-styles`. No new bundle needed.

### Results Section Structure

```html
<section class="hdx-v2-dataset-list">
  <div class="hdx-v2-container">
    <div class="c-dataset-card-list">
      {# loop: package_item_v2.html per package #}
    </div>
  </div>
</section>
```

Structure:

```
.hdx-v2-dataset-list
  .hdx-v2-container
    .c-dataset-card-list          ← flex column, gap: var(--hdx-space-4) [1rem]
      .c-dataset-card              ← repeated
      .c-dataset-card
      …
```

The `.c-dataset-card-list` wrapper (layout + `.highlight` rule) lives in `less/v2/components/dataset-card.less`, owned by the component.

Do NOT introduce Bootstrap `row`/`col-*` classes.

---

## Component Extension Requirements

The following gaps exist between the current `package` data and the existing `c-dataset-card` parameters.

### Gap 1 — Query text highlighting
**Current behavior:** `data-module="highlight" data-module-text="{{ query }}"` applied to `.dataset-heading` and `.dataset-description` activates JS text highlighting.
**v2 component:** No `data-module` attribute on title or description elements.
**Required extension (pending D7):** Add optional `query` parameter. When non-empty, add `data-module="highlight" data-module-text="{{ query }}"` to `.c-dataset-card__title` and `.c-dataset-card__desc-text`.
**Risk:** Low — additive only. No attribute rendered when `query` is empty.

### Gap 2 — Multiple locations
**Current behavior:** Location not shown in current list items.
**v2 component:** `location` accepts a single string → one cyan label.
**Handling:** Compute the display string in the mapping layer (single name, "Multiple locations", or empty). No component extension required unless per-country labels are needed — see Open Question #5.

### Gap 3 — Trending / download count *(OPEN)*
No field in `c-dataset-card`. Resolution depends on Open Question #1.
- If kept: add optional `trending: bool` and/or `download_count: int` parameters.
- If dropped: no change needed.

### Gap 4 — `is_requestdata_type` *(OPEN)*
If shown: requires a new `requestdata` format type (distinct from `private`) or a separate bool param.
If mapped to `private` or dropped: no change needed. Depends on Open Question #2.

### Gap 5 — `page_list` / `links_list` *(OPEN)*
No equivalent field. Resolution depends on Open Question #8.

---

## Functionality Preservation

| Behavior | Source | How preserved |
|---|---|---|
| Mixpanel `search` event | `google-analytics.js` — fires on filter/search change | No JS change; event is tied to the filter form, not the card |
| Description expand/collapse | `v2/components/clamped-text.js` via `data-module="clamped-text"` (updated task 038) | Shared module |
| Query text highlighting | `data-module="highlight"` JS module | Add `query` param to component (Gap 1) |
| Dataset URL routing | `h.url_for('dataset.read', id=package.name)` | Preserved in `title_href` |
| Org URL routing | `h.url_for('organization.read', ...)` | Preserved in `org_href` |
| Edit link (admin view) | `show_edit_link` → `package_item_admin.html` | Out of scope; handled by existing admin snippet |

---

## Edge Cases

| Case                                                    | Expected behavior                                                                           |
|---------------------------------------------------------|---------------------------------------------------------------------------------------------|
| Very long title                                         | LESS two-lines ellipsis (already in `c-dataset-card`)                                       |
| No description                                          | Pass `description=''`; component omits description section                                  |
| No organization                                         | Pass `org_name=''`; component omits org line                                                |
| No locations                                            | Pass `location=''`; component omits location row                                            |
| No date                                                 | Pass `date_range=''`; component omits date                                                  |
| No resources / no formats                               | Pass `formats=[]`; component omits formats row                                              |
| Only special badges (private/COD), no extension formats | Render only those badges; `formats_overflow=0`                                              |
| Many formats (10+)                                      | Show up to MAX_VISIBLE, then `+N` overflow badge                                            |
| Unknown format string                                   | Map to fallback `document-format.svg` icon                                                  |
| `batch_length` = 0 or None                              | Pass `show_others_label=''`; component omits footer                                         |
| `package.private = True`                                | Lock badge as first format item                                                             |
| `package.archived = True`                               | Archived badge after private (if both present)                                              |
| `package.is_request_datatype`                           | Request data badge after archived and private (if present)                                  |
| `subnational == '1'` but `location == ''`               | Sub-national label shown alone; `subnational` is independent of `location` in the component |

---

## Decisions Taken

| # | Question | Decision |
|---|---|---|
| D1 | Trending indicator / download count | **Dropped** — not shown in v2 card |
| D2 | `is_requestdata_type` treatment | **Distinct** — `requestdata` badge (`unlock.svg`) + ` [By Request Only]` title suffix |
| D3 | Archived icon | **`placeholder.svg`** |
| D4 | Date string format | **New helper** `render_date_range_label` → `"Data from 22 Jan 2020 to 09 Mar 2023"` |
| D5 | Location availability and display | `package.groups` is reliably present; `"Multiple locations"` for >1 group |
| D6 | Max visible format badges | **3**; remainder shown as `+N` |
| D7 | Query highlighting | **Preserved** — `query` param added to `c-dataset-card`; `.highlight` CSS added to `v2/styles.css` |
| D8 | `page_list` / `links_list` | **Dropped from list view** — visible on dataset detail page only |

---

## Constraints

- BEM: section-level uses `hdx-v2-*` prefix; reused component keeps `c-*`
- All colors, spacing, radius, shadow via design tokens — no hardcoded hex or pixel values
- No Bootstrap `row`, `col-*`, `d-*`, `container` classes in the v2 results area
- No inline styles
- Hover states via CSS `:hover` pseudo-class only — no JS-toggled state classes
- LESS: nest `@media` queries inside element blocks (per CONVENTIONS.md)
- Reuse `c-dataset-card` as-is; extend only for confirmed gaps listed above

