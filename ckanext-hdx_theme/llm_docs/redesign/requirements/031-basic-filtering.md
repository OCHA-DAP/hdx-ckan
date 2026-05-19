# Dataset List / Search Page: Basic Filtering (Responsive)

**Scope:** Search results page only (`/dataset` or `/search` route, `v2=true` gate)

---

## Context

The v2 redesign search page has a dataset list and card layout but no filter UI.
This task adds the filter sidebar (LG) and filter button + overlay (MD/SM),
using the existing `c-dropdown`, `c-checkbox`, and `c-button` component system.

---

## Scope

### Included

- Location filter → `groups` CKAN facet param
- Organisation filter → `organization` CKAN facet param
- Format filter → `res_format` CKAN facet param
- Topics filter → `vocab_Topics` CKAN facet param
- Advanced filters dropdown → `featured` CKAN facet (fully wired):
  - Boolean ext_* items: `ext_subnational`, `ext_geodata`, `ext_p_coded`, `ext_tabular_data`, `ext_hdx_hapi`
  - COD levels: `cod_level` facet (multi-value, each level is a separate checkbox; parent "CODs" row selects/deselects all)
  - HPC topics: `vocab_Topics` facet (same param as Topics filter; parent "HPC" row selects/deselects all)
  - "Clear selection" inside advanced filter panel clears `ext_*` + `cod_level` only (not `vocab_Topics`)
- Multi-select per filter (checkbox-based)
- Real-time filtering: each checkbox click updates URL immediately (no confirm step)
- Responsive layout: LG inline sidebar, MD/SM button + full-page overlay
- Filter open/close interactions (dropdown panels, overlay)
- Active count badge on MD/SM filter button (total selected items across all filters including advanced)
- "Clear selection" per-filter (inside panel, center-aligned)
- "Clear filters" global (MD/SM overlay footer, clears all params including advanced)
- Search within filter option list — shown only when a filter has > 8 items (MiniSearch + `toNormalForm`)

### Excluded

- Tags filter — removed; Topics (`vocab_Topics`) is the correct filter
- Show more / Show less within filter panels — removed (all values shown directly)
- Advanced filters toggle button — removed (replaced by the advanced filters dropdown)
- Data type filter (separate task)
- Show only / Archived controls
- Sorting
- Pagination
- Results per page
- Time period filter

---

## Architecture Constraints

### No duplicated or conditional Jinja blocks

`package_list.html` defines blocks at the **top level** (outside `{% if v2 %}`).
`facet_list` is set before the block so both the sidebar and the overlay can access it:

### Preserve backend logic strictly

- Do NOT modify query params, URL structure, or facet selection logic
- All filter changes go through `updateUrl()` / `clearFacet()` / `clearAdvancedFilters()` / `clearAllFilters()`
- `clearAllFilters()` removes both `FILTER_PARAMS` and `ADVANCED_FILTER_PARAMS`

### Decision-first workflow

Ambiguous decisions (data mapping, behavior differences between v1/v2, URL param semantics)
must be confirmed with the user **before** implementation. Do not silently choose.

---

## Figma Reference

| Breakpoint | Files |
|---|---|
| LG | `filter-no-scroll.html`, `filter-dropdown-open.html` |
| MD / SM | `filter-md.html`, `filter-md-button.html`, `filter-md-button-active.html`, `filter-active-filters.html` |

SM behaves identically to MD.

---

## Breakpoints

Defined in `breakpoints.less`:

- **XL** ≥ `80rem` (1280px): inline sidebar (`@hdx-bp-xl`)
- **MD / SM** < `80rem` (1280px): button + overlay

---

## Responsive Layout

### LG — Inline Sidebar

```
┌──────────────────────────────────────────────────┐
│  [Page title]                                    │
├──────────────┬───────────────────────────────────┤
│ Filter by    │  Dataset cards                    │
│              │                                   │
│ [Location ▾] │  [Card]                           │
│ [Org      ▾] │  [Card]                           │
│ [Format   ▾] │  [Card]                           │
│ [Topics   ▾] │                                   │
│ [Advanced ▾] │                                   │
└──────────────┴───────────────────────────────────┘
```

- Sidebar is a fixed-width left column inside the v2 search layout
- Each filter = `c-dropdown--size-m` with label above, trigger below
- Dropdown panel opens downward, contains `c-checkbox` list + optional "Clear selection" text link (left-aligned)
- Panel closes on outside click
- Only one panel open at a time

### MD / SM — Filter Button + Overlay

```
┌──────────────────────────────────────────────────┐
│  [Page title]                      [⚙ Filter (3)]│
├──────────────────────────────────────────────────┤
│  Dataset cards (full width)                      │
│  [Card]                                          │
│  [Card]                                          │
└──────────────────────────────────────────────────┘

On button click → full-page overlay:
┌──────────────────────────────────────────────────┐
│  Filters                                    [✕]  │
│  ─────────────────────────────────────────────── │
│  [same filter UI as LG — reused template]        │
│                                                  │
│  ─────────────────────────────────────────────── │
│  [Clear filters]          [Show results]         │
└──────────────────────────────────────────────────┘
```

---

## Interaction Model

### Checkbox click (both breakpoints)

1. User checks/unchecks a filter option
2. JS reads current URL, adds or removes the facet param value
3. Navigate to new URL (preserving all other params; reset `page` to 1)
4. Active count badge on MD/SM button recalculates on next render

### Group "select all" (advanced filters)

- Parent checkbox (CODs / HPC) has `data-group-toggle` + `data-group="<facet_key>"`
- Click → add or remove ALL child values for that group
- Parent state (checked / indeterminate / unchecked) is server-rendered via template logic
- JS sets `.indeterminate = true` on elements with `data-indeterminate` attribute on DOMContentLoaded

### Dropdown open/close (LG)

- Click trigger → toggle `c-dropdown--open` on wrapper, panel becomes visible
- Click outside → close (document click listener with `[data-filter-key]` guard)
- Only one panel open at a time (close others on open)

### Filter button click (MD/SM)

- Click → add `hdx-v2-search-filter-overlay--open` to overlay, trap focus, prevent body scroll
- Click ✕ or "Show results" → remove modifier, restore scroll, return focus to trigger
- "Clear filters" → remove all filter params (main + advanced) from URL, navigate

---

## Component Reuse and Extension

### Reuse as-is

| Component | Usage |
|---|---|
| `c-dropdown` | Wrap each filter (label + trigger + panel) |
| `c-dropdown--size-m` | All filter dropdowns |
| `c-dropdown--filter` | Active state on trigger when any option is selected |
| `c-dropdown--open` | Panel visible state |
| `c-dropdown__trigger-count` | Selected count in trigger (e.g., `(2)`) |
| `c-checkbox` | Each option inside the panel |
| `c-button--primary --size-l` | "Show results" footer button (`style='primary', size='l'`) |
| `c-button--tertiary --size-l` | "Clear filters" footer button (`style='tertiary', size='l'`; `state='disabled'` when no filters selected) |
| `c-text-button` | "Clear selection" inside panel (`style='tertiary'`, `size='m'`, `tag='button'`) |

### Component API notes

- **`checkbox.html`**: params `id`, `checked`, `disabled`, `name`, `value`, `attrs`, `extra_classes`. No `wrapper_tag` — always renders `<span>`.
- **`list-item.html`**: params `type`, `label`, `size`, `state`, `checked`, `value`, `count`, `href`, `attrs`, `extra_classes`. No `tag` — checklist always renders `<label>`.
- **`dropdown.html`**: full-wrapper component. States: `'enabled'` | `'active'` (open) | `'disabled'` | `'filter'`. Trigger params: `size`, `label`, `placeholder`, `selected`, `count`, `state`, `icon`, `icon_src`, `chevron_src`, `extra_classes`, `attrs`, `panel_id`, `button_attrs`. Panel params: `items` (unified list), `navigate` (bool), `has_search`, `filter_search_key`, `has_clear`, `clear_facet`. Panel rendering is delegated to `dropdown-panel.html`.
- **`list-item.html`**: `type='list'` supports `attrs` (rendered on outer `<div>`/`<a>`), `state='active'` (adds `is-active`), and `tooltip` (renders as `title` attribute). `type='checklist'` always renders `<label>`; `attrs` applied to inner `<input>`.

### Dropdown panel structure

Panels are rendered via `dropdown.html` (which delegates to `dropdown-panel.html`). `search-filters.html` builds `items` lists and passes them to `dropdown.html` — no inline panel HTML in `search-filters.html`.

`dropdown-panel.html` renders one of two modes:

**`navigate=False`** (default — used for all filter dropdowns):
```
c-dropdown__panel  [role=listbox aria-multiselectable=true]
  ├─ c-search-input  (optional; has_search=True when filter has > 8 items;
  │                   attrs: {data-filter-search: facet_key};
  │                   MiniSearch + toNormalForm for diacritic-insensitive filtering)
  └─ c-dropdown__list-wrap
       └─ c-dropdown__list  [role=group]
            │   items + children are flattened into a single loop
            │
            ├─ [regular item]   — list-item.html (type='checklist')
            │      attrs: {data-filter-checkbox, data-facet}
            │
            ├─ [parent group item — advanced filters only]
            │    extra_classes='c-list-item--parent'
            │      attrs: {data-group-toggle, data-group, data-indeterminate?}
            │
            └─ [child item — advanced filters, indented]
                 extra_classes='c-list-item--child'
                   attrs: {data-filter-checkbox, data-facet}
  └─ c-dropdown__footer  (visible when has_clear=True)
       └─ text-button.html  (style='tertiary', size='m', tag='button',
                             data-action='clear-filter', data-facet=clear_facet)
```

**`navigate=True`** (used for sort/results-per-page; see task 034):
```
c-dropdown__panel
  └─ c-dropdown__list-wrap
       └─ c-dropdown__list
            └─ list-item.html (type='list', attrs={data-nav-value}, state='active' when selected)
```

No "Show more / Show less" — all values always visible.

---

## Advanced Filters Dropdown

Data source: `full_facet_info['facets']['featured']['items']`

Each item in that list is one of:
- **Flat item** (ext_* boolean): `{category_key: 'ext_subnational', name: '1', display_name, count, selected}`
- **Category item** (COD): `{category_key: 'cod_level', name: 'ALL', display_name: 'CODs', items: [{category_key: 'cod_level', name: 'cod', ...}]}`
- **Category item** (HPC): `{category_key: 'vocab_Topics', name: 'ALL', display_name: 'HPC', items: [...]}`

Template renders hierarchy — parent "select all" row + indented children for category items.

"Clear selection" in the Advanced filters panel:
- Clears: all `ADVANCED_FILTER_PARAMS` (`ext_subnational`, `ext_geodata`, `ext_p_coded`, `ext_tabular_data`, `ext_hdx_hapi`, `cod_level`)
- Does NOT clear: `vocab_Topics` (HPC items use this shared param; clearing it would also remove Topics filter selections)

---

## Files

| File | Role |
|---|---|
| `templates/v2/search-filters.html` | Shared filter panel — all 5 dropdowns inlined (no separate composite component) |
| `templates/search/snippets/package_list.html` | Top-level v2/v1 layout branch: v2 block computes `total_selected` once, renders filter overlay + button, and wraps sidebar + dataset list; v1 uses `row`/`col-3` |
| `templates/search/snippets/search_results_wrapper.html` | Thin wrapper — passes `full_facet_info` + `v2` flag into `package_list.html` via `h.snippet`; no filter logic |
| `templates/v2/components/dropdown.html` | Full-wrapper component: trigger + panel delegation; single `items` list + `navigate` bool; delegates panel rendering to `dropdown-panel.html` |
| `templates/v2/components/dropdown-panel.html` | Panel overlay; `navigate=False` for checklist filters, `navigate=True` for navigate-on-select (sort/limit); items + children flattened before render |
| `templates/v2/components/list-item.html` | `type='list'`: `<div>`/`<a>` with `attrs`, `tooltip`, `is-active`; `type='checklist'`: always `<label>`; no `tag` param |
| `templates/v2/components/checkbox.html` | Always `<span>` wrapper; no `wrapper_tag` param |
| `less/v2/search.less` | Layout styles (search-layout, sidebar, overlay, filter-btn-row); overlay footer button overrides |
| `less/v2/components/dropdown.less` | `c-dropdown` trigger + panel structural styles; `c-dropdown__list-item*` removed (use `c-list-item` from list-item.less) |
| `less/v2/components/list-item.less` | `c-list-item--parent` (bold) and `c-list-item--child` (24px indent) modifiers |
| `fanstatic/v2/search.js` | All filter/overlay JS (dropdown open/close, checkbox→URL, group toggle, MiniSearch, overlay open/close) |
| `fanstatic/webassets.yml` | `v2-search-styles` bundle (`v2/search.css`) + `v2-search-scripts` bundle (`v2/search.js`) — separate from `v2-components-*` |

---

## Data Flow

```
CKAN controller
  → full_facet_info (facet names, items with counts, selected values)
       ↓
search_results_wrapper.html
  → passes full_facet_info + v2 flag into package_list.html
       ↓
package_list.html  (top-level v2/v1 branch)
  v2:
    ① compute total_selected once (main filters + ext_* flat + cod_level children;
       HPC children excluded — already captured by vocab_Topics)
    ② hdx-v2-list-header (title, count, nav-controls at XL, filter-btn at MD/SM)
         ├── __left  (title + count)
         ├── __controls  (sort + results-per-page; hidden at MD/SM)
         └── __filter-btn  (filter button; hidden at XL)
    ③ hdx-v2-search-filter-overlay#hdx-filter-overlay  (fixed, MD/SM; sibling of layout)
         ├── header (title + close btn)
         ├── body > hdx-v2-overlay-nav-controls (sort + results-per-page)
         │         > div.hdx-v2-search-filters > search-filters.html
         └── footer (Clear filters [tertiary/disabled-when-0] + Show results [primary])
    ④ hdx-v2-search-layout (flex row)
         ├── form > aside.hdx-v2-search-filters  (LG sidebar)
         │     └── search-filters.html + hidden passthrough inputs
         └── div.hdx-v2-dataset-list (flex: 1)
               └── {% block package %} → package_item_v2.html loop
  v1:
    div.row
      ├── div.col-3 > form > package_search_facets.html
      └── div.col-9 > {% block package %} → package_item.html loop
```

Facet → URL param mapping:

| UI Label | CKAN facet key | URL param | Notes |
|---|---|---|---|
| Location | `groups` | `groups` | |
| Organisation | `organization` | `organization` | |
| Format | `res_format` | `res_format` | |
| Topics | `vocab_Topics` | `vocab_Topics` | |
| Subnational | `ext_subnational` | `ext_subnational=1` | advanced |
| Geodata | `ext_geodata` | `ext_geodata=1` | advanced |
| P-Codes | `ext_p_coded` | `ext_p_coded=1` | advanced |
| Tabular Data | `ext_tabular_data` | `ext_tabular_data=1` | advanced |
| HDX HAPI | `ext_hdx_hapi` | `ext_hdx_hapi=1` | advanced |
| COD levels | `cod_level` | `cod_level=<value>` | advanced, multi-value, parent toggle |
| HPC topics | `vocab_Topics` | `vocab_Topics=<tag>` | advanced, shared with Topics, parent toggle |

---

## JavaScript Constants

```javascript
var FILTER_PARAMS = ['groups', 'organization', 'res_format', 'vocab_Topics'];

var ADVANCED_FILTER_PARAMS = [
  'ext_subnational', 'ext_geodata', 'ext_p_coded',
  'ext_tabular_data', 'ext_hdx_hapi',
  'cod_level'
];
```

`clearAllFilters()` removes both `FILTER_PARAMS` and `ADVANCED_FILTER_PARAMS`.
`clearAdvancedFilters()` removes only `ADVANCED_FILTER_PARAMS`.

Dropdown JS identification: `[data-filter-key]` attribute (replaces former `c-dropdown--checklist` class selector).

