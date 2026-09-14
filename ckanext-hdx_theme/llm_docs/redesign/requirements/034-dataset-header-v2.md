# 034 — Dataset List Header (v2)

**Scope:** Dataset search results page only (`v2=true`)
**Related tasks:** 031 (filtering), 033 (pagination)

---

## 1. Context

The search results page header needs to be redesigned for v2. It sits above the dataset list and contains the page title, dataset count, results-per-page control, and sort-by control. Pagination and dataset-card are handled separately.

The **search input** is explicitly excluded from this task.

Existing functionality (query params, backend logic, analytics) must remain intact.

---

## 2. Audit — Existing Implementation

### 2.1 Template location

The current header lives entirely in:

`ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/package_list.html` **lines 36–76**

It is wrapped in `<form id="dataset-filter-form">` / `<div id="dataset-filter-start">` and contains:

| Element | Notes |
|---------|-------|
| "Data" title + archived tabs | Static label "Data", not "Datasets" |
| Header search input (`#headerSearch`) | **Out of scope** |
| Show filter toggle switch | LG only, v1 Bootstrap switch |
| Sort dropdown | Via `{% snippet 'search/snippets/package_search_order.html' %}` |
| Results per page dropdown | Inline in `package_list.html` lines 52–74 |

The v2 block (`{% if v2 %}`) currently starts at **line 80** of `package_list.html`, covering the filter overlay, filter button row, and two-column layout. The header at lines 36–76 is v1 and shared unconditionally.

The page entry point for v2 is `search/search.html` → `search_results_wrapper.html` → `package_list.html`.

### 2.2 Dataset count

| Detail | Value |
|--------|-------|
| Template param | `packages_count` (= `my_c.full_facet_info.get('num_of_total_items')`, set in `search_results_wrapper.html`) |
| Current display | `search/snippets/search_result_text.html` — sentence format: "X results found" / "X results for 'query'" |
| Figma format | Raw number only (e.g., "19,819") |
| Archived/unarchived split | `full_facet_info.num_of_unarchived` / `num_of_archived` available for tab counts |
| Formatting helper | `h.localised_number(count)` (comma-separated) |

### 2.3 Sort

| Detail | Value |
|--------|-------|
| Snippet | `search/snippets/package_search_order.html` |
| Options | 7 hardcoded — see table below |
| Admin-only option | "Due for Update" (`due_date asc`) — added when `admin_view=True` |
| Query param | `sort` |
| Selected value | `c.sort_by_selected` (passed as `sorting_selected` to snippet) |
| Default | `h.HDX_CONST('DEFAULT_SORTING')` = `metadata_modified desc` ("Last Modified") |
| Default detection | `used_default_sort_by=True` → hidden `sort` input is NOT emitted in the form |
| JS handler | `fanstatic/order-by-dropdown.js` → `replaceParam('sort', value)` + resets `page=1` |

**Sort options:**

| Label | Value | Short label |
|-------|-------|-------------|
| Last Modified | `metadata_modified desc` (DEFAULT) | Last Modified |
| Last Added | `metadata_created desc` | Last Added |
| Relevance | `score desc, metadata_modified desc` | Relevance |
| Name Ascending | `title_case_insensitive asc` | Name Asc |
| Name Descending | `title_case_insensitive desc` | Name Desc |
| Trending | `pageviews_last_14_days desc` | Trending |
| Most Downloads | `total_res_downloads desc` | Most Downloads |

The v1 snippet renders a Bootstrap dropdown with class `control-order-by orderDropdown`. The "Trending" and "Due for Update" labels have tooltips in v1.

### 2.4 Results per page

| Detail | Value |
|--------|-------|
| Options | `[10, 25, 50, 100]` (hardcoded in `package_list.html` line 52) |
| Default | `10` |
| Query param | `ext_page_size` |
| Template var | `c.ext_page_size` (set in `search_logic.py` line 222) |
| Backend | `ckanext-hdx_search/…/search_logic.py` line 222: `int(request.args.get('ext_page_size', num_of_items))` |
| UI | Radio-button Bootstrap dropdown, class `control-items-per-page control-order-by` |
| JS handler | `fanstatic/datasets/list-header.js` line 109 (`getFilterUrlNew()`) |

### 2.5 Analytics

- Mixpanel tracking for sort and results-per-page changes is currently **not active** — commented out in `fanstatic/google-analytics.js` lines 65–74.
- v2 filter tracking is also commented out in `fanstatic/v2/pages/search.js`.

### 2.6 v2 dropdown component

`templates/v2/components/dropdown.html`

| Parameter | Notes |
|-----------|-------|
| `size` | `'m'` (34px) or `'s'` (24px) |
| `label` | Optional text above the trigger |
| `placeholder` | Default text when nothing selected |
| `selected` | Currently selected value label |
| `state` | `enabled` / `active` / `disabled` / `filter` |
| `icon` | Boolean, leading icon |
| `panel_id` | aria-controls target |
| `items` | Unified panel items list |
| `navigate` | `True` → navigate-on-select; `False` → checklist |
| `has_search` | Show search input in checklist panel |
| `has_clear` | Show clear-selection footer in checklist panel |
| `clear_facet` | Facet key for clear button; `'advanced'` clears all advanced params |

Size S specs: 12px font, 24px height, padding 6/8/6/10px, gap 4px. Panel rendering delegated to `dropdown-panel.html`.

### 2.7 Filter overlay (already implemented)

`package_list.html` lines 103–128 / `v2/search-filters.html` / `search.less`

- Fixed full-screen, `z-index: 500`, shown on MD/SM (< `@hdx-bp-xl` = 80rem/1280px)
- Structure: header ("Filters" + close) → scrollable body (filter dropdowns) → footer ("Clear filters" + "Show results")
- Sort/limit controls are present in the overlay body above the filter groups (added by this task)

---

## 3. Figma Design — XL / MD / SM Comparison

### 3.1 XL layout

Full header, all controls visible inline:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Datasets                           Results per page    Sort by     │
│  19,819                             [  10  ∨ ]         [ Last M ∨ ] │
└─────────────────────────────────────────────────────────────────────┘
```

**Element hierarchy:**

```
.frame-parent  (display: flex; width: 100%; align-items: flex-end)
├── .datasets-parent  (flex: 1; display: flex; flex-direction: column; gap: 0.5rem)
│   ├── <b> "Datasets"   (2rem, Merriweather, bold, #101212, line-height 130%)
│   └── <span> "19,819"  (1rem, Roboto, #3f4748, line-height 130%)
└── .wrapper-sort  (display: flex; gap: 1rem; align-items: flex-end)
    ├── .wrapper  (display: flex; flex-direction: column; gap: 0.75rem)
    │   ├── label "Results per page"  (0.875rem, Roboto, #3f4748)
    │   └── .dropdown > .select      (see dropdown spec below)
    └── .wrapper  (display: flex; flex-direction: column; gap: 0.75rem)
        ├── label "Sort by"
        └── .dropdown > .select
```

**Dropdown spec (both XL controls):**

| Property | Value |
|----------|-------|
| Size | S (24px height, 12px font) |
| Background | white (`--hdx-neutral-0`) |
| Border | 1px solid `--hdx-neutral-2` (`#d8e0e1`) |
| Border-radius | 2px (`--hdx-radius-sm`) |
| Shadow | `--hdx-shadow-sm` (0 1px 4px rgba(0,0,0,0.04)) |
| Text weight | 500 (medium) |
| Padding | 6px 8px 6px 10px |
| Icon | Chevron-down, 0.875rem, right-aligned |
| Gap (text → icon) | 0.375rem |
| Label shown | Yes — rendered ABOVE the dropdown trigger, separately in layout |
| Left icon | No |

### 3.2 MD layout

Title + count flex, single filter button (already implemented). Sort and results-per-page controls are hidden from the main header — they move into the filter overlay.

```
┌─────────────────────────────────────────┐
│  Datasets              [ ≡ Filter (10) ]│
│  19,819                                 │
└─────────────────────────────────────────┘
```

- Title: 1.75rem Merriweather bold
- Count: 1rem Roboto #3f4748
- Sort / results-per-page: **not visible in header** — in overlay

### 3.3 SM layout

Same structure as MD, more compact:

- Title: 1.5rem Merriweather bold
- Gap: 0.5rem between title-block and filter button
- Sort / results-per-page: **not visible in header** — in overlay

### 3.4 Responsive summary

| Element | XL (≥ 1280px) | MD / SM (< 1280px) |
|---------|--------------|---------------------|
| "Datasets" heading | Visible, 2rem | Visible, 1.75rem / 1.5rem |
| Dataset count | Visible, 1rem | Visible, 1rem |
| Results per page | Visible inline (right) | Hidden — moved to filter overlay |
| Sort by | Visible inline (right) | Hidden — moved to filter overlay |
| Filter button | Not shown | Existing (implemented in task 031) |

Breakpoint: `@hdx-bp-xl` = `80rem` / `1280px` (same as existing filter responsive logic).

---

## 4. Integration Strategy

### Option A — CSS-only restyle of existing v1 controls

Apply v2 tokens and classes to the existing `orderDropdown` / `control-order-by` HTML inside a `{% if v2 %}` branch. No structural HTML changes.

- **Pros:** Minimal JS risk, single-file CSS change
- **Cons:** Leaks v1 class names into v2; hard to reuse in overlay; couples v1 structure to v2 tokens

### Option B — New v2 header block using `dropdown.html` ✓ Recommended

Add a new `{% if v2 %}` section **above** the existing filter-overlay block in `package_list.html`. Render the title, count, and both controls using the existing `v2/components/dropdown.html` (size=s). Wire to URL-param JS using the existing `replaceParam` pattern. Call the same sort/limit snippets from inside the overlay body for MD/SM.

- **Pros:** Clean v2 HTML, proper tokens, component shared across breakpoints, no v1 coupling
- **Cons:** JS wiring needed for immediate navigation; dropdown panel pattern needs verification for navigate-on-select use case
- **Risk:** `dropdown.html` currently renders a confirm-button panel — sort/limit need immediate navigation; component may need a data attribute/mode for this

### Option C — Extend `dropdown.html` with navigation mode

Add a `navigate_on_select` param to `dropdown.html` emitting a data attribute; JS reads it and navigates immediately on list-item selection instead of waiting for a confirm button.

- **Pros:** Clean component-level separation of "filter" vs "navigate" modes
- **Cons:** Touches a widely-used component; risk of regressions across filter dropdowns

---

## 5. Recommendation

**Use Option B.**

1. Add a new v2 header block in `package_list.html` inside `{% if v2 %}`, placed before the existing filter-overlay block (line 80).
2. Render `<h1>Datasets</h1>` (static) and `packages_count` formatted with `h.localised_number()`.
3. Use `v2/components/dropdown.html` (size=s, no label param, no left icon) for both controls. The labels ("Results per page", "Sort by") are rendered as separate `<span>` elements in the header layout, not as the component's built-in `label` param.
4. Add a new v2-scoped JS handler that reads list-item selection from the dropdown panel and immediately calls `replaceParam('sort', value)` / `replaceParam('ext_page_size', value)` + resets `page=1`.
5. In the filter overlay body, render the same sort/limit controls (above existing filters) with the same JS handler — immediate navigation confirmed.
6. On XL, hide the overlay's sort/limit via CSS; on MD/SM, hide the header's sort/limit via CSS.
7. The v1 header (`#dataset-filter-start`) remains untouched for non-v2.

---

## 6. Functional Constraints

These MUST be preserved:

| Constraint | Detail |
|------------|--------|
| `sort` query param | URL key and values unchanged |
| `ext_page_size` query param | URL key and values unchanged |
| `page` reset | Any sort/limit/filter change deletes the `page` param (returns to page 1 without appending `?page=1`) |
| Backend behavior | `search_logic.py` logic untouched |
| Non-v2 layout | `#dataset-filter-start` block unchanged |
| Admin sort option | "Due for Update" conditional on `admin_view` (open question [D6]) |

---

## 7. Component Constraints

- Use `v2/components/dropdown.html` with `size='s'`
- No label param on dropdown component — labels rendered separately in header layout
- No left icon on dropdown component
- No Bootstrap classes
- Use `--hdx-*` design tokens exclusively
- Hover via CSS pseudo-class only
- No unnecessary JS — reuse `replaceParam` URL-update pattern from existing handlers

---

## 8. Decisions Taken

| ID | Question | Decision |
|----|----------|---------|
| D1 | Count source | Always `packages_count` (full result set) — no tab-conditional count |
| D2 | Sort default when `used_default_sort_by=True` | "Last Modified" shown as default label — `_ns.sort_label` defaults to `_('Last Modified')` when no match found |
| D3 | Overlay position | Sort + results-per-page appear ABOVE filter groups (`hdx-v2-overlay-nav-controls` block) |
| D4 | Zero results | Show "0" — `h.localised_number(0)` renders "0" |
| D5 | Count format | `h.localised_number()` confirmed (comma-separated) |
| D6 | Admin sort option | Admin "Due for Update" preserved — `admin_view` param passed to `search-nav-controls.html` |
| D7 | Tooltips | "Trending" and "Due for Update" tooltips preserved via `tooltip` key in `nav_items` list |
| D8 | Analytics | No Mixpanel events — analytics remain commented-out as in v1 |
| D9 | Dropdown navigation mode | `[data-nav-key]` / `[data-nav-value]` data attributes; `setNavParam()` in `search.js` navigates immediately on click |
| D10 | Results per page options | Options remain `[10, 25, 50, 100]` |
| — | Overlay sort/limit behavior | Immediate navigation on selection — no "Show results" button involvement |
| — | Page heading | Always static **"Datasets"** — no dynamic filter context in the heading |
| — | Search input | Excluded from this task |

---

## 9. Files Affected

**Created (new):**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/search-nav-controls.html` — shared snippet rendering the "Results per page" + "Sort by" control pair; used in both the XL header and the MD/SM filter overlay.

**Modified:**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/package_list.html` — v2 header block added above the overlay; renders `hdx-v2-list-header` (title, count, nav-controls) and `hdx-v2-overlay-nav-controls` inside the overlay body.
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/pages/search.less` — `hdx-v2-list-header`, `hdx-v2-nav-controls`, `hdx-v2-nav-ctrl-pair`, `hdx-v2-nav-ctrl-label`, `hdx-v2-overlay-nav-controls` block; responsive show/hide; nav panel width/anchor overrides.
- `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/pages/search.js` — `[data-nav-key]` / `[data-nav-value]` click handler for immediate URL-param navigation (sort + ext_page_size).
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/dropdown.html` — extended with unified `items`, `navigate`, `has_search`, `filter_search_key`, `has_clear`, `clear_facet` params; panel rendering delegated to `dropdown-panel.html`.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/dropdown-panel.html` — rewritten to support `navigate=True` (navigate-on-select via `list-item.html type='list'`) and `navigate=False` (multi-select checklist with optional search/clear); items + children flattened into single render loop.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/list-item.html` — extended `type='list'` to support `attrs` on outer element, `tooltip` → `title` attr, and `is-active` via `state='active'`.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/search-filters.html` — refactored from inline panel HTML to `dropdown.html` snippet calls using unified `items`; advanced filter builds nested structure with `children`; clear button uses `clear_facet='advanced'`.

**Not created (decided against):**

- `package_list_header_v2.html` — header block inlined directly in `package_list.html` (no separate file needed).
- `list-header.less` — all header/nav-controls styles added to `search.less`.

---

## 10. Implementation Notes

### Labels are external to the c-dropdown wrapper

The `c-dropdown` wrapper uses `flex-direction: column`, so the built-in `label=` param stacks the label ABOVE the trigger. For the nav controls (Figma: label and trigger side by side), labels are rendered as external `.hdx-v2-nav-ctrl-label` spans inside a `.hdx-v2-nav-ctrl-pair` flex-row wrapper. The `label=` param is intentionally NOT passed to the dropdown snippet for sort/limit.

### navigate=True vs navigate=False (unified items list)

`dropdown.html` accepts a single `items` list and a `navigate` boolean, delegated to `dropdown-panel.html`:
- `navigate=True`: navigate-on-select panel; each item is a `list-item.html` (`type='list'`) with `data-nav-value`; JS navigates immediately on click.
- `navigate=False` (default): multi-select checklist panel; items rendered via `list-item.html` (`type='checklist'`); supports `children` for parent/child groups (COD levels, HPC topics).

### Sort panel right-anchored

`[data-nav-key="sort"] .c-dropdown__panel` uses `right: 0; left: auto` so the panel opens to the LEFT and never overflows past the right viewport edge on small screens.
