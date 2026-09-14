# 035 — Dataset Search Bar (v2)

**Scope:** Dataset search results page only (`v2=true`)
**Related tasks:** 031 (filtering), 033 (pagination), 034 (dataset list header)

---

## 1. Context

The secondary search bar on the dataset search results page allows users to filter results by keyword. It is distinct from the global navigation search bar and must remain visible at **all breakpoints** (XL, MD, SM).

This task adds a v2-styled version of the search bar inside the `{% if v2 %}` block of `package_list.html`. The existing v1 search bar (lines 33–77) is left untouched. Full functionality, query behavior, and analytics must be preserved without modification.

---

## 2. Audit — Existing Implementation

### 2.1 Template location

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/package_list.html`

The v1 search input lives in the unconditional header section:

- **Line 29:** `{% set searchValue = h.hdx_get_request_param('q', '') %}` — reads current `q` param
- **Line 33:** `<form id="dataset-filter-form" style="display: inline;">`
- **Line 42:** `<input autocomplete="off" id="headerSearch" name="q" class="header-search" type="text" placeholder="Search all datasets ..." value="{{searchValue}}">`

The v2 block starts at **line 80** (`{% if v2 %}`). It currently renders the list header, filter overlay, and two-column layout — but **no search bar**.

### 2.2 Form and query behavior

| Detail | Value |
|--------|-------|
| Form ID | `dataset-filter-form` |
| Method | GET (implicit; page reloads on submit) |
| Action | Implicit — submits to current page (`/dataset`) |
| Query param | `q` |
| All other params | Preserved via `replaceParam()` in JS |
| Page reset | YES — `replaceParam()` resets `page` to 1 (`order-by-dropdown.js:27–29`) |
| Sort preservation | NO — `sort` excluded by `get_filtered_params_list()` (`helpers.py:170`) |
| Submit trigger | Enter key only — no auto-submit on typing, no debounce |

### 2.3 JavaScript behavior

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/organization_/organizations.js`

```js
$("#headerSearch").on("keydown", function(event){
    if (event.keyCode == '13'){
        var value = $(this).val();
        window.location.href = replaceParam("q", value) + "#headerSearch";
        event.preventDefault();
    }
});
```

Key behaviors:
- Triggered by Enter key only (`keyCode == 13`)
- Calls `replaceParam("q", value)` (`order-by-dropdown.js:21–35`) — builds new URL preserving all current params, resets `page` to 1
- Appends `#headerSearch` to anchor-scroll back to the input after reload
- No `form.submit()` call — the `<input>` does not need a `<form>` parent for the JS to work
- No debounce logic

**`replaceParam()` is shared** with sort and results-per-page dropdowns. No changes needed.

### 2.4 Analytics (Mixpanel)

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/google-analytics.js`

| Detail | Value |
|--------|-------|
| Trigger | **Passive — fires on page load**, not on form submit |
| Mechanism | Serializes `#search-page-filters-form` + `#dataset-filter-form` via `.serializeArray()` |
| Event name | `"search"` |
| Fires if | At least one of: `q`, `vocab_Topics`, `res_format`, `organization`, `groups`, `license_id`, `cod_level`, `ext_subnational`, `ext_tabular_data`, `ext_geodata`, `ext_requestdata`, `ext_hxl`, `ext_sadd`, `ext_showcases`, `ext_administrative_divisions`, `ext_p_coded` has a value |
| Properties | `page title`, `number of results`, `result type`, `search term`, `tag/format/org/location filters`, `search box location` |
| `search box location` | Reads `ext_search_source` URL param; falls back to `"in-page"` |

**Critical:** Analytics depends on `id="dataset-filter-form"` on the wrapping form and `name="q"` on the input. Both must be preserved in v2.

Because the trigger is passive (page load), the v2 search bar does NOT need to fire any new events. The `google-analytics.js` code is unchanged.

### 2.5 Current styling (v1)

| Element | Identifier |
|---------|-----------|
| Input | `id="headerSearch"`, `class="header-search"` |
| Container | `#dataset-filter-start`, `.list-header` |

Uses Bootstrap classes (`d-inline-block`, `float-end`, `text-uppercase`). No v2 design tokens.

### 2.6 Asset loading

`organizations.js` is bundled in `dataset-search-scripts` (`webassets.yml`), loaded unconditionally at `package_list.html:24`. The `#headerSearch` handler will apply to the v2 input as long as the `id` is preserved.

---

## 3. Audit — Figma Design

### 3.1 XL breakpoint (`figma_exports/dataset-results-xl.html`)

**Placement:** Own full-width row (`.wrapper6`) between the list header and the first dataset card.

**Structure:**
```html
<div class="search">
  <div class="value">Search for datasets</div>
  <img class="chevron-down-icon" alt="">
</div>
```

**CSS:**
```css
.search {
  align-self: stretch;          /* full width */
  border-radius: 2px;
  background-color: #fff;
  border: 1px solid #ebeff0;    /* whitesmoke-200 */
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  gap: 0.5rem;
  min-width: 7.5rem;
}
```

- Icon: right-aligned (img with no src — placeholder for search icon)
- Placeholder: `"Search for datasets"`
- Width: full-width (stretch)

### 3.2 MD breakpoint (`figma_exports/dataset-results-md.html`)

**Placement:** Inside `.header-parent > .header`, in a flex row alongside Datasets title/count. An empty `.search-autocomplete` div (`z-index: 3`) sits above it, suggesting an autocomplete dropdown layer is anticipated.

**Structure:**
```html
<div class="search">
  <div class="value">Search for datasets</div>
  <img class="filter-icon" alt="">
</div>
```

**CSS:**
```css
.search {
  width: 43.5rem;               /* fixed */
  border-radius: 2px;
  background-color: #fff;
  border: 1px solid #d8e0e1;   /* gainsboro */
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  gap: 0.5rem;
  min-width: 7.5rem;
  z-index: 2;
}
```

- Width: 43.5rem fixed
- `z-index: 2` — positioned above content, below the autocomplete overlay

### 3.3 SM breakpoint (`figma_exports/dataset-results-sm.html`)

**Placement:** Inside `.wrapper-sort2`, a flex row that also contains Results per page and Sort by dropdowns.

> ⚠️ **Structural note:** The SM Figma shows sort/limit controls rendered **outside** the filter overlay (alongside the search bar). In the current v2 implementation, sort/limit at MD/SM appear only inside the filter overlay (`search-nav-controls.html` comment: "Shared between the XL inline header and the MD/SM filter overlay"). See **Open Question §9.4**.

**Structure:**
```html
<div class="search">
  <div class="value">boundaries</div>   <!-- filled state, not placeholder -->
  <img class="filter-icon" alt="">
</div>
```

**CSS:**
```css
.search {
  width: 22.563rem;             /* fixed, narrower */
  border-radius: 2px;
  background-color: #fff;
  border: 1px solid #d8e0e1;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  gap: 0.5rem;
  min-width: 7.5rem;
}
```

### 3.4 Comparison across breakpoints

| Property | XL | MD | SM |
|----------|----|----|----|
| Placement | Own row (below header) | Row with title/count | Row with sort/limit |
| Width | Full-width (stretch) | 43.5rem fixed | 22.563rem fixed |
| Border | `1px solid #ebeff0` | `1px solid #d8e0e1` | `1px solid #d8e0e1` |
| Padding | 0.5rem 0.75rem | 0.5rem 0.75rem | 0.5rem 0.75rem |
| Border-radius | 2px | 2px | 2px |
| z-index | — | 2 | — |
| Autocomplete hint | No | Yes (empty overlay div present) | No |

---

## 4. Gap Analysis — Existing vs Figma

### 4.1 Visual mismatches

| Item | Current (v1) | Figma (v2) |
|------|-------------|-----------|
| Placeholder | `"Search all datasets ..."` | `"Search for datasets"` |
| Border | Bootstrap-derived | `1px solid #ebeff0` (XL) / `#d8e0e1` (MD/SM) |
| Padding | Bootstrap-derived | `0.5rem 0.75rem` |
| Border-radius | Unknown | 2px |
| Right icon | Not present | Search icon (right-aligned) |
| Width | Inline in header row | Full-width row (XL), fixed (MD/SM) |
| Styling | Bootstrap classes | v2 design tokens only |

### 4.2 Structural mismatches

| Item | Current (v1) | Figma (v2) |
|------|-------------|-----------|
| v2 presence | Not in v2 block | Required in v2 block |
| Placement | Inline in header row (with sort/limit) | Own row (XL), or row with title/count (MD), or row with sort/limit (SM) |
| v2 component | Raw `<input>` | `c-search-input` snippet |

### 4.3 What must stay the same

- `name="q"` on the input
- `id="headerSearch"` on the input (JS handler + analytics both depend on it)
- `id="dataset-filter-form"` on the wrapping form (analytics serialization)
- GET submission behavior (navigate, not form.submit)
- Enter-key trigger only (no debounce, no auto-submit)
- `#headerSearch` anchor on URL after submit (scroll-back behavior)
- No changes to `google-analytics.js`, `organizations.js`, or `helpers.py`

---

## 5. Integration Strategy

### Option A: Restyle v1 input in v2 wrapper

Suppress the v1 search bar with `{% if not v2 %}` and re-render just the `<input id="headerSearch" name="q">` inside a v2-styled container div inside the v2 block.

**Pros:** Zero behavior change. Same DOM structure.
**Cons:** Manual CSS duplication — not using the `c-search-input` component.

### Option B: Use `v2/components/search-input.html` snippet *(recommended)*

Inside the v2 block, render a `<form id="dataset-filter-form">` wrapping:
```jinja
{% snippet 'v2/components/search-input.html',
    name='q',
    id='headerSearch',
    size='m',
    placeholder=_('Search for datasets'),
    value=searchValue,
    autocomplete='off' %}
```

**Pros:**
- Clean v2 component reuse. Consistent with other v2 elements.
- Snippet already supports `name`, `id`, `value`, `placeholder`, `size`, `autocomplete`.
- Right-aligned search icon included by default (`v2/icons/search.svg`).

**Cons:**
- The `dataset-filter-form` form must be re-declared in the v2 block (the v1 form at line 33 is in the non-v2 section). A separate `<form id="dataset-filter-form">` in the v2 block is safe since the analytics code only needs the form to be present in the DOM.

**Why `<form>` is required:** The `organizations.js` handler does NOT call `form.submit()` — it uses `replaceParam()` and navigates directly. So the `<input>` technically does not need a form for the JS to work. **However**, `google-analytics.js` serializes `#dataset-filter-form` via `.serializeArray()` to extract the `q` value for the Mixpanel event. Without the form wrapper, the `q` field would not be captured and the analytics event might not fire.

**Recommendation: Option B.**

---

## 6. Component Considerations

### Available v2 components

| Component | File | Notes |
|-----------|------|-------|
| `c-search-input` | `templates/v2/components/search-input.html` | Sizes `l` (40px) / `m` (34px). Default icon `v2/icons/search.svg` right-aligned. Supports `name`, `id`, `value`, `placeholder`, `autocomplete`. |

Use `size='m'` to match the height of existing v2 header controls (dropdowns at 34px).

**No new components needed.** The existing `c-search-input` covers all required params.

---

## 7. Template Strategy

- **Gate with `{% if v2 %}`**: Search bar markup lives inside the v2 block in `package_list.html` (after line 80)
- **v1 untouched**: The v1 search bar (lines 33–77) remains unchanged; no `{% if not v2 %}` wrapper needed
- **Placement within v2 block**: A new search row inserted after `hdx-v2-list-header` (line 105–129), before the filter overlay (line 131)
- **Form wrapper**: New `<form id="dataset-filter-form">` wraps the v2 search input (required for analytics serialization)
- **CSS**: New class `hdx-v2-search-bar` (or similar) scoped to the v2 search row; breakpoint rules in `v2/search.less`

---

## 8. Constraints

- No Bootstrap classes
- v2 design tokens only
- Hover = CSS pseudo-class only (`:hover`)
- No new JavaScript — reuse existing `#headerSearch` keydown handler in `organizations.js`
- Must preserve `id="headerSearch"` and `name="q"`
- Must be inside a `<form id="dataset-filter-form">` for analytics
- No regression on non-v2 pages

---

## 9. Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| D9.1 | Placeholder text | `"Search for datasets"` — Figma text used; v1 `"Search all datasets ..."` retained only in the v1 bar |
| D9.2 | Search icon | `v2/icons/search.svg` — `c-search-input` default used; no custom icon |
| D9.3 | Autocomplete overlay (MD only) | Deferred — out of scope for this task; no autocomplete component implemented |
| D9.4 | SM layout conflict — sort/limit outside overlay | Sort/limit remains inside the filter overlay only at MD/SM; Figma SM view treated as a design artifact; `hdx-v2-search-bar-row` is full-width standalone row at all breakpoints |
| D9.5 | Border token — XL vs MD/SM | Single consistent token — `c-search-input` component handles its own border via design tokens; no per-breakpoint border override added |
| D9.6 | Width at MD/SM | `width: 100%` stretch — Figma fixed widths treated as canvas sizes; `.hdx-v2-search-bar-row` and `.c-search-input` both set to `width: 100%` |
| D9.7 | Sort not preserved on search | Preserved as-is — existing `helpers.py` behavior unchanged; sort reset on new search is intentional |
| D9.8 | `#headerSearch` anchor scroll | Preserved — `organizations.js` unchanged; anchor scroll kept as-is |

---

## 10. Files Affected

| File | Change |
|------|--------|
| `templates/search/snippets/package_list.html` | Add v2 search bar inside `{% if v2 %}` block, after `hdx-v2-list-header`, before filter overlay |
| `hdx-styles/src/common/less/v2/pages/search.less` | Add CSS for search row container and breakpoint layout |

**No changes to:**
- `fanstatic/organization_/organizations.js`
- `fanstatic/google-analytics.js`
- `helpers/helpers.py`
- `templates/v2/components/search-input.html`
