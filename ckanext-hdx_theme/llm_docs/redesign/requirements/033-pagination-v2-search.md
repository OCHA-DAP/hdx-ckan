# Task 033: Pagination v2 — dataset search results page

## Context

Pagination on the dataset search results page currently renders through `Page.pager()` — a Python method that produces Bootstrap-styled `<ul class="pagination">` markup. This markup is incompatible with the v2 design system.

A complete v2 pagination component (`c-pagination`) already exists, designed to Figma spec, with all styles compiled and bundled. This task wires that component into the dataset search results page under the `v2=true` gate, with no regression for non-v2 pages.

Pagination is explicitly deferred in task 030 (dataset list migration). This task completes that deferred item.

---

## Goal

Replace the Bootstrap pagination output on the v2 search results page with the existing `c-pagination` component. Preserve all query parameters (search query, filters, sort, page size) in pagination URLs.

---

## Scope

**In:**
- v2 conditional rendering of `c-pagination` in the dataset search results page
- LESS for the pagination row wrapper (centering, spacing)

**Out (explicitly deferred):**
- Changes to `ckan/lib/pagination.py` or `ckan/views/dataset.py`
- Non-v2 pagination on any page type (orgs, groups, users, showcases)
- Per-page selector (items per page control)
- Results count text ("Showing 1–25 of 847 datasets")
- Sorting controls
- Mobile-specific pagination layout changes (see Open Question 2)

---

## Audit Findings

### Backend pagination engine

**File:** `ckan/lib/pagination.py`

Two classes:
- `BasePage` — core logic: `page`, `items_per_page`, `item_count`, `first_page`, `last_page`, `page_count`, `first_item`, `last_item`, `previous_page`, `next_page`. `pager()` method generates HTML via a callback.
- `Page` (subclass) — wraps output in Bootstrap `<nav class="pagination-wrapper"><ul class="pagination">`. Outputs `<li class="page-item">` elements.

The `pager()` method accepts `format="~2~"` (radius 2 around current), `symbol_previous="«"`, `symbol_next="»"`. It calls a `url` callback for each link.

**HDX search view setup — `ckanext-hdx_search/ckanext/hdx_search/controller_logic/search_logic.py`:**

The HDX search path uses `SearchLogic` (not `ckan/views/dataset.py` directly). A custom `pager_url` closure is created and wired into the `Page` object:

```python
# search_logic.py:274–279
def _get_pager_function(self, package_type):
    def pager_url(q=None, page=None):
        params = list(self._params_nopage())
        params.append(('page', page))
        return self._search_url(params, package_type)
    return pager_url

# search_logic.py:417–421
def _params_nopage(self):
    params_to_skip = ['_show_filters']
    return [(k, v) for k, v in request.args.items(multi=True)
            if k != 'page' and k not in params_to_skip]
```

`_params_nopage()` reads **all** current request params using `multi=True`, preserving multi-valued params like `?organization=org1&organization=org2`. The `_show_filters` key (sidebar open/closed state) is intentionally excluded. `_search_url` then calls `url_with_params(url, params)` → `url + '?' + urlencode(params)`.

The `Page` object is created with this closure as its `url` argument, so `my_c.page._url_generator` IS this closure.

**Calling `my_c.page._url_generator(page='')` from the template yields the correct `base_url`:** passing an empty string for `page` produces a URL ending in `page=` (e.g. `/dataset?q=water&organization=wfp&page=`), to which the v2 component directly appends the page number.

This mechanism is already tested: `ckanext-hdx_search/tests/test_pages/test_pagination.py::test_pagination_2_valued_filter` verifies that multi-valued org filters survive across pagination links.

### Current template rendering point

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/search_results_wrapper.html:33–35`

```jinja2
{% block page_pagination %}
    {{ my_c.page.pager(q=my_c.q) }}
{% endblock %}
```

This block is reached for every page load (v2 and non-v2). The `v2` variable is available here — it is passed as `v2=true` from `search/search.html:62` via `h.snippet(...)`.

### v2 conditional wiring (confirmed)

```
search/search.html
  └─ extends v2/page.html
  └─ h.snippet('search/snippets/search_results_wrapper.html', ..., v2=true)
       └─ {% block page_pagination %} ← target
       └─ h.snippet('search/snippets/package_list.html', ..., v2=v2)
            └─ {% if v2 %} two-column layout + cards {% endif %}
```

### Existing v2 pagination component

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/pagination.html`

```jinja2
{% snippet 'v2/components/pagination.html',
    size='md', current_page=3, total_pages=12,
    base_url=h.url_for('dataset.search') ~ '?page=' %}
```

Parameters:
| Param | Type | Default | Notes |
|---|---|---|---|
| `size` | string | `'md'` | `'md'` (38px) or `'sm'` (28px) |
| `current_page` | int | 1 | From `my_c.page.page` |
| `total_pages` | int | 1 | From `my_c.page.page_count` |
| `base_url` | string | `'?'` | **Page number is appended directly.** Must include all other params. |
| `prev_icon_src` | string | `'v2/icons/chevron-left.svg'` | |
| `next_icon_src` | string | `'v2/icons/chevron-right.svg'` | |
| `extra_classes` | string | `''` | |

**Critical constraint:** The component builds each page link as `href="{{ base_url }}{{ p }}"`. This means `base_url` must be the complete URL prefix up to and including `page=` — e.g. `/dataset?q=water&organization=wfp&page=`. If `base_url` omits any active params, those params are silently dropped when navigating to the next page.

**Styles:** `fanstatic/v2/components/navigation.css` (compiled from `navigation.less:131–218`). Already bundled in `v2-components-styles`. **No new CSS file needed.**

---

## Design Analysis

### Component visual spec (from `navigation.less`)

| Element | Background | Border | Text | Weight |
|---|---|---|---|---|
| Default page | `var(--hdx-neutral-0)` #fff | `1px solid var(--hdx-neutral-2)` #d8e0e1 | `var(--hdx-neutral-8)` #3f4748 | 400 |
| Active page | `var(--hdx-neutral-0)` #fff | `1px solid var(--hdx-neutral-2)` #d8e0e1 | `var(--hdx-neutral-95)` #101212 | **500** |
| Prev / Next | `var(--hdx-neutral-0)` #fff | `1px solid var(--hdx-neutral-2)` #d8e0e1 | `var(--hdx-neutral-95)` #101212 | 400 |
| Ellipsis | `var(--hdx-neutral-0)` #fff | `1px solid var(--hdx-neutral-2)` #d8e0e1 | `var(--hdx-neutral-8)` #3f4748 | 400 |
| Disabled (prev on p.1, next on last) | Same | Same | Same | — |

Active page differentiation: **darker + bolder text only** — same white background, no accent color. This is the intentional Figma design.

Transition: `background-color 0.15s ease, color 0.15s ease` on all items.

Hover: CSS `:hover` pseudo-class only — no JS toggled state classes.

Cell dimensions:
- MD: 2.375rem × height-by-content (padding 4px 12px for pages; 4px 6px for prev/next)
- SM: 1.75rem × height-by-content (padding 2px 12px / 2px 6px)

### Ellipsis logic

Window = 2. Pages shown: always page 1, always last page, and the ±2 range around current. Ellipsis appears where there is a gap of ≥ 2 pages. Example for page 8 of 20:

```
[‹] [1] […] [6] [7] [8*] [9] [10] […] [20] [›]
```

### Figma layout reference (from task 030 analysis)

"Outer wrapper: full-width flex column, `gap: 2rem` (card list + pagination block)"

Pagination is centered below the card list with a ~2rem (`var(--hdx-space-8)`, 32px) top margin.

### Current vs v2 comparison

| Aspect | Current (Bootstrap) | v2 design |
|---|---|---|
| Container | `<nav><ul class="pagination">` | `<nav class="c-pagination c-pagination--size-md">` |
| Items | `<li class="page-item"><a class="page-link">` | `<a class="c-pagination__item c-pagination__item--page">` |
| Active | `<li class="page-item active">` | `.c-pagination__item--active` + darker text |
| Prev/Next | `<li>` wrapping `<a>` with `«`/`»` text | `<a>` with embedded SVG chevron |
| Ellipsis | `<li class="disabled"><a>...</a>` | `<span class="c-pagination__item--ellipsis" aria-hidden="true">…</span>` |
| Disabled state | Bootstrap `disabled` class | `.is-disabled` + `aria-disabled="true"` + `tabindex="-1"` |
| Styling | Bootstrap `pagination`, `page-item`, `page-link` | Design tokens only, no Bootstrap |

---

## Options Considered

### Option A: Reuse `Page.pager()` output as-is
Keep the existing Bootstrap HTML output and re-skin via CSS overrides.
- **Pros:** Zero template change; no URL concerns
- **Cons:** Bootstrap class dependencies; markup diverges from v2 system; would need complex CSS selector hacks; undermines the migration goal
- **Verdict:** Rejected

### Option B: Conditional rendering — v2 component using existing URL generator *(Recommended)*
In `search_results_wrapper.html`, conditionally render `c-pagination` when `v2=true`. Derive `base_url` by calling the existing `pager_url` closure already on the `Page` object (`my_c.page._url_generator(page='')`) — no new helper required.
- **Pros:** Uses the existing designed component; no new Python code; no registration; correct URL construction for all param combinations (multi-valued, empty, etc.); clean `{% if v2 %}` gate; zero regression for non-v2 pages
- **Cons:** Accesses a nominally-private attribute (`_url_generator`) — acceptable since it is the documented URL callback on the Page object
- **Verdict:** Recommended

### Option C: v2 CSS wrapper over Bootstrap output
Override Bootstrap pagination CSS within `v2` page context to visually match the design without HTML changes.
- **Pros:** No Python code; no template change
- **Cons:** Requires duplicating or overriding Bootstrap styles per-page; active state marker (`<li>` vs `<a>`) is structurally different; brittle; creates hidden CSS coupling
- **Verdict:** Rejected

### Option D: Modify `Page` class to emit v2 HTML
Subclass or modify `ckan/lib/pagination.py` to render `c-pagination` markup directly.
- **Pros:** Unified output for all page types eventually
- **Cons:** Touches a shared engine file; high risk of breaking all paginated pages; Jinja2 template SVG includes not available from Python; premature generalization
- **Verdict:** Rejected (defer until all page types migrate to v2)

---

## Recommended Approach

### 1. Template change

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/search_results_wrapper.html`

Replace lines 33–35:
```jinja2
{% block page_pagination %}
    {{ my_c.page.pager(q=my_c.q) }}
{% endblock %}
```

With:
```jinja2
{% block page_pagination %}
  {% if v2 %}
    {% set base_url = my_c.page._url_generator(page='') %}
    <div class="hdx-v2-pagination-row">
      {% snippet 'v2/components/pagination.html',
          size='md',
          current_page=my_c.page.page,
          total_pages=my_c.page.page_count,
          base_url=base_url %}
    </div>
  {% else %}
    {{ my_c.page.pager(q=my_c.q) }}
  {% endif %}
{% endblock %}
```

`my_c.page._url_generator` is the HDX `pager_url` closure from `SearchLogic._get_pager_function()`. Calling it with `page=''` invokes `_params_nopage()` (which reads all current request args, excluding `page` and `_show_filters`) and returns a URL ending in `page=`. The v2 component then appends each page number directly.

The single-page suppression guard (`total_pages > 1`) lives inside `v2/components/pagination.html` — the component renders nothing when `total_pages <= 1`. This keeps the caller simple and makes the behavior consistent for all future uses of the component.

### 3. LESS — pagination row wrapper

**File:** `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/search.less`

Add after the dataset list section:
```less
.hdx-v2-pagination-row {
    display:         flex;
    justify-content: center;
    margin-top:      var(--hdx-space-8);   // 32px — matches Figma ~2rem gap
}
```

### Data flow summary

```
Request: /dataset?q=water&organization=wfp&page=3

SearchLogic._get_pager_function() wires pager_url closure onto Page object
  → my_c.page._url_generator = pager_url(q=None, page=None) closure
  → my_c.page.page        = 3
  → my_c.page.page_count  = 34

Template: search_results_wrapper.html (v2=True)
  → my_c.page._url_generator(page='')
      → _params_nopage() reads request.args.items(multi=True), skips 'page'
      → url_with_params('/dataset', [('q','water'),('organization','wfp'),('page','')])
      → "/dataset?q=water&organization=wfp&page="

Snippet: v2/components/pagination.html
  → base_url="/dataset?q=water&organization=wfp&page="
  → Page 2 link: href="/dataset?q=water&organization=wfp&page=2"
  → Page 4 link: href="/dataset?q=water&organization=wfp&page=4"
```

---

## Files Involved

| File | Change |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/search/snippets/search_results_wrapper.html` | Conditional v2/legacy in `page_pagination` block |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/search.less` | Add `.hdx-v2-pagination-row` |

**Read-only (no changes):**
| File | Why referenced |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/pagination.html` | Component to be called — no changes needed |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/navigation.less` | Source for component styles |
| `ckanext-hdx_search/ckanext/hdx_search/controller_logic/search_logic.py` | `_get_pager_function` / `_params_nopage` — URL generation origin, no changes |
| `ckan/lib/pagination.py` | `BasePage._url_generator` attribute — no changes |

---

## Functional Considerations

### Query param preservation
`my_c.page._url_generator(page='')` delegates to the HDX `pager_url` closure from `SearchLogic._get_pager_function()`. That closure calls `_params_nopage()`, which reads `request.args.items(multi=True)` — correctly preserving multi-valued params (e.g. `organization=org1&organization=org2`) and excluding `_show_filters` (UI-only state). No new Python code is needed.

### Zero regression for non-v2 pages
The `{% if v2 %}` guard in `search_results_wrapper.html` means the existing `Page.pager()` output is completely unchanged for non-v2 pages. No other page type (orgs, groups, users) is affected.

### Single-page suppression
When `total_pages == 1`, the v2 component renders a nav with prev/next both disabled and a single page number. This is technically functional but visually unnecessary. The `page_count > 1` guard matches the existing `show_if_single_page=False` behavior. (See Open Question 1.)

### No JavaScript required
All navigation is via standard `<a href>` links. No JS needed for pagination interactions.

### Tracking / analytics
No pagination-specific analytics events exist in the current codebase. Mixpanel/GA events fire on filter changes (form interactions), not on page navigation. This task introduces no tracking, and no existing tracking is removed.

### Future: per-page selector
A "Show 25/50/100" control would add `ext_page_size=N` to the URL. Since `_params_nopage()` preserves all existing params, changing `ext_page_size` independently and then navigating pages will work correctly without any changes to the pagination component or URL wiring.

### Future: sorting
Same as above — `sort=field+asc/desc` is already preserved by `_params_nopage()` automatically.

---

## Constraints

- DO NOT introduce Bootstrap classes (`pagination`, `page-item`, `page-link`, etc.) in v2 markup
- All styles via design tokens (`var(--hdx-*)`) — no hardcoded hex values or pixel sizes
- Hover states via CSS `:hover` pseudo-class only — no JS-toggled classes (`is-hovered`, etc.)
- No inline styles
- `c-pagination` component template must not be modified
- Non-v2 pages must continue to use `Page.pager()` unchanged
- No new Python helpers or plugin registrations needed

---

## Decisions Taken

| # | Question | Decision |
|---|----------|---------|
| Q1 | Hide pagination when `total_pages == 1`? | Hidden — `page_count > 1` guard in template; same guard covers `total_pages == 0` |
| Q2 | Mobile viewport use `size='sm'`? | No — always `size='md'`; no breakpoint-based size switch implemented |
| Q3 | Active-page visual finalized as darker text + weight only? | Yes — darker text (`#101212`) + weight 500, same white background; confirmed in design analysis |
| Q4 | Include "results count" text? | Deferred — explicitly out of scope for this task |
| Q5 | Per-page selector in scope? | Deferred — explicitly out of scope for this task |
| Q6 | Apply to org/group/location listing pages? | Deferred — dataset search page only in this task |
| Q7 | ARIA live region for page changes? | No — no JS added; all navigation via standard `<a href>` links |
| Q8 | Edge case `total_pages == 0` — hide entirely? | Hidden — same `page_count > 1` guard covers this case |
