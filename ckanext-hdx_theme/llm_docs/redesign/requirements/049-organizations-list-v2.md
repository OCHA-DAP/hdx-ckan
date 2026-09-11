# 049 — All Organisations List (v2)

**Scope:** Migrate `/organization/` (All Organisations) to v2 — layout, KPI cards,
search input, sort + results-per-page controls, org card list, pagination.
**Excluded:** search autocomplete, subscriber count.
**Figma sources:** `org-list-xl.html`, `org-list-md.html`, `org-list-sm.html`, `org-list-card.html`

---

## Context

The existing All Organisations page (`/organization/`) lists all CKAN organisations
that have at least one dataset. It supports text search, 4 sort options, and 3 page-size
options, with server-side filtering and pagination via Python/Jinja2.

The v2 redesign adds:
- KPI cards (3 global platform stats) — since commented out; a `title_count` badge next to the page title shows the organisations count instead (see §3 below)
- Org card with expandable description and right-side dataset/member counts
- v2-styled search input, results-per-page, and sort dropdowns
- Pagination using the existing `c-pagination` component

---

## 1. Existing Page Audit

### Templates

| Item | Path |
|---|---|
| **Main template** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/index.html` |
| **Org item snippet** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/browse/snippets/org_item.html` |
| **Blueprint** | `hdx_org` at `/organization/` (desktop) · `hdx_light_org` at `/m/organization/` (mobile) |

Both desktop and mobile call the same `_index()` in `light_organization.py` — only the
template path differs.

### View / Data Logic

| Item | Detail |
|---|---|
| **View** | `ckanext-hdx_org_group/ckanext/hdx_org_group/views/light_organization.py` → `_index()` |
| **Org list** | `get_action('cached_organization_list')(ctx, {})` — all orgs, `all_fields=True`, `include_extras=True` |
| **Filter + sort** | `helper.filter_and_sort_results_case_insensitive(all_orgs, sort_option, q=q, has_datasets=True)` — in-memory, Python |
| **Pagination** | `h.Page(collection, page, url=pager_url, items_per_page=limit)` |

### Template Variables Provided to Template

```python
{
    'q':                str,   # current search query
    'sorting_selected': str,   # e.g. 'title asc'
    'limit_selected':   int,   # e.g. 25
    'page':             Page,  # ckan pagination object
}
```

`page.items` = organisations on current page.
`page.item_count` = total filtered count.

### Search Behaviour

- Query param: `q`
- Input: `<input id="headerSearch">` in template
- JS: `organizations.js` listens for Enter key, calls `replaceParam("q", value)`
- Server-side: `filter_and_sort_results_case_insensitive()` filters by title, name,
  description (case-insensitive) and requires `package_count > 0`

### Sort Options

| Label | Value |
|---|---|
| Name Ascending | `title asc` (default) |
| Name Descending | `title desc` |
| Dataset Count Descending | `datasets desc` |
| Dataset Count Ascending | `datasets asc` |

Query param: `sort`

### Pagination

- Query param: `page` (default 1)
- Limits: 25, 50, 100 (default 25). Query param: `limit`
- `page.pager()` renders v1 Bootstrap pagination HTML (NOT reused in v2)
- Anchor: `#organizationsSection` appended to pagination URLs

### Data Fields per Organisation (from `cached_organization_list`)

| Field | Type | Notes |
|---|---|---|
| `title` / `display_name` | str | Display name for card title |
| `name` | str | URL slug → link to `/organization/{name}` |
| `description` | str | Raw markdown — strip to plain text with `h.markdown_extract() \| striptags` |
| `package_count` | int | Total public datasets |
| `created` | datetime str | Used as "Member since" date |
| `dataset_last_updated` | datetime | Added by `org_add_last_updated_field()` |

**Member count:** computed at render time via `h.get_group_members(org.id)` — calls
`member_list` action per org → N+1 pattern.
**Follower count:** computed via `h.get_group_followers(org.id)` — excluded from v2 scope.

### Existing "Show More" Module

`hdx_show_more` in `fanstatic/hdx_show_more.js` — jQuery Expander plugin, 370-char cutoff.
**Not carried forward** to v2; a new v2 implementation is needed.

---

## 2. Figma Mapping

### XL Page Structure (`org-list-xl.html`)

```
[navbar / breadcrumb]          ← standard v2 chrome
[org-list-page-header]         ← title + KPI cards
  "All organisations"          ← <h1>
  3 × kpi-locations-card       ← Datasets / Organisations / Locations
[body]
  [sidebar]                    ← empty in Figma — no sidebar content shown
  [org-list2]
    [header]
      [search]                 ← text input (no autocomplete), flex:1 full-width
      [wrapper-sort]
        Results per page dropdown (size S)
        Sort by dropdown (size S)
    [org-list-card-parent]     ← list of org cards
    [pagination]
```

### MD Page Structure (`org-list-md.html`)

- Same sections; card adapts to narrower layout (left col narrows to ~25.5rem)
- Controls stack or adjust

### SM Page Structure (`org-list-sm.html`)

- KPI cards stack
- Card collapses to title + date only (no right column, no description)

### KPI Cards (from `org-list-xl.html` `.kpi` block)

**Current status:** this KPI row is commented out in `templates/organization/index.html`. A `title_count` badge (`title_count=h.localised_number(kpi_orgs)`, passed to `page-header.html`) shows the organisations count next to the page title instead. The Figma spec below is kept for reference.

| Label | Figma value |
|---|---|
| Datasets | 20,518 |
| Organisations | 225 |
| Locations | 254 |

These are **global platform stats**, not per-page totals.

### Org List Card (`org-list-card.html`)

**XL / MD structure:**

```
.org-list-card (full width, border, shadow)
  .org-list-card2 (flex row, padding: 1rem, gap: 2.5rem)
    .wrapper (left col — XL: 45rem, MD: 25.5rem)
      .org-name      18px / 16px bold, 2-line clamp, linked to org page
      .org-name2     12px, "Member since [date]", color: #2f3536
      .org-description
        "Show more" text link + chevron-down icon
        [expanded: full description; collapsed: hidden]
    .column-right (flex:1, right-aligned)
      .wrapper2 (flex row, gap: 8px, font: 14px)
        "[N] Datasets" · "[N] Members"
```

**Hover state:** border color becomes `#3f4748` (constant 1px width, CSS only, no param)

**SM structure:**

```
.dataset-card (flex wrap, padding: 1rem, gap: 0.625rem)
  .wrapper9 (20.563rem)
    title (16px bold, 2-line clamp)
  .wrapper11 (20.563rem)
    "Member since [date]"
  .column-right5 (display: none at SM)
```

At SM: title + date only. No description, no metadata.

### Excluded from Figma (per scope)

- Subscriber count in `wrapper2` (Figma shows it; scope excludes it)
- Location tags (`wrapper-location` — `display:none` in all Figma sizes; excluded)
- Search autocomplete dropdown

---

## 3. Component Strategy

| UI Element | Component / Approach | Notes |
|---|---|---|
| KPI cards | `c-stats-card--kpi` → `v2/components/stats-card.html`, `variant='kpi'` + `c-stats-card-list c-stats-card-list--row` wrapper | Merged from the former `c-kpi-card`/`c-kpi-card-row` (task 070 B1) |
| KPI info icon | `c-info-icon` → `v2/components/info-icon.html` | Used inside the `kpi` variant's label row |
| Search input | `v2/components/search-input.html` OR plain v2-styled `<input>` | No autocomplete, plain submission |
| Results per page | `v2/components/dropdown.html` (size `s`) | Same pattern as `search-nav-controls.html` |
| Sort by | `v2/components/dropdown.html` (size `s`) | Org-specific sort options (see §5) |
| Org list card | NEW: `c-org-list-card` component | New LESS file + Jinja2 snippet |
| "Show more" | `clamped-text` v2 module (`fanstatic/v2/components/clamped-text.js`) | Reuse — same pattern as `page-header.html`; description fully hidden by default via CSS |
| Pagination | `v2/components/pagination.html` | **Already exists — reuse as-is** |

### New Files

| File | Purpose |
|---|---|
| `templates/organization/index.html` | v2 template — direct replacement, extends `v2/page.html` |
| `templates/v2/components/org-list-card.html` | Org card snippet |
| `templates/v2/components.html` | Add org-list-card demo section |
| `hdx-styles/…/v2/components/org-list-card.less` | Org card LESS |
| `hdx-styles/…/v2/org-list-page.less` | Page LESS (imports `nav-controls.less`) |
| `fanstatic/v2/pages/org-list.js` | Search Enter handler (`hdxSetNavParam`) |
| `fanstatic/v2/url-nav.js` | Shared `setNavParam` + `[data-nav-key]` click handler |

---

## 4. Org Card Definition

### Snippet: `v2/components/org-list-card.html`

**Parameters:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `org` | dict | required | Organisation dict from `page.items` |
| `member_count` | int | 0 | Pre-fetched member count |

**No `size` param** — breakpoint handled by CSS.
**No `state` param** — hover is CSS-only.

### Template Structure

```jinja2
{% set member_count = member_count if member_count is defined else 0 %}

{% set title       = org.title or org.display_name %}
{% set href        = h.url_for('hdx_org.read', id=org.name) %}
{% set description = h.markdown_extract(org.description, extract_length=0) | striptags if org.description else '' %}
{% set created     = h.render_datetime(org.created) if org.created else _('Unknown') %}
{% set datasets    = org.package_count or 0 %}

<div class="c-org-list-card">
  <div class="c-org-list-card__inner">

    <div class="c-org-list-card__left">
      <a class="c-org-list-card__title" href="{{ href }}">{{ title }}</a>
      <span class="c-org-list-card__date">{{ _('Member since') }} {{ created }}</span>

      {% if description %}
        <div class="c-org-list-card__description" data-module="clamped-text">
          <p class="c-org-list-card__desc-text" data-clamped-content>{{ description }}</p>
          {% snippet 'v2/components/text-button.html',
              label=_('Show more'),
              tag='button',
              icon=True,
              icon_src='v2/icons/chevron-down.svg',
              icon_position='right',
              style='tertiary',
              size='s' %}
        </div>
      {% endif %}
    </div>

    <div class="c-org-list-card__right">
      <span class="c-org-list-card__meta">
        {{ h.hdx_format_number_si(datasets) }} {{ _('Datasets') }}
        <span class="c-org-list-card__sep" aria-hidden="true">•</span>
        {{ h.hdx_format_number_si(member_count) }} {{ _('Members') }}
      </span>
    </div>

  </div>
</div>
```

### Behaviour: "Show more"

- Description is **fully hidden** by default (not truncated or clamped)
- "Show more" button reveals the full description text
- Label changes to "Show less" + chevron-up; clicking again hides the description
- Implemented via the existing `clamped-text` v2 module (`fanstatic/v2/components/clamped-text.js`)
  — same `data-module="clamped-text"` + `data-clamped-content` pattern used in `page-header.html`
- Org card CSS must hide the description element by default so the module's overflow detection
  triggers (`scrollHeight > clientHeight`)

### Responsive Behaviour

| Breakpoint | Layout |
|---|---|
| XL (`≥ 80rem`) | Flex row: left (`~45rem`) + right (`flex:1`, right-aligned) |
| MD (`< 80rem`) | Flex row: left (`~25.5rem`) + right |
| SM (`< 48rem`) | Stack: title + date only; `.c-org-list-card__right` hidden; `.c-org-list-card__description` hidden |

---

## 5. Search & Controls Integration

### Search Input

- Reuse `v2/components/search-input.html` (already exists on branch, used in dataset search)
- `value="{{ q }}"`, placeholder `_('Search organisations')`
- On Enter (or search button click): `replaceParam('q', value)` — same behaviour as v1
- **No autocomplete** — do NOT wire the autocomplete snippet

### Controls

`search-nav-controls.html` targets dataset sort options and cannot be reused directly.
Controls are rendered inline in the org list template using `v2/components/dropdown.html`
(size `s`) with `navigate=True` and `data-nav-key` attributes handled by `url-nav.js`.

**Sort options (Figma-accurate — alphabetical only):**

| Label | `sort` param value |
|---|---|
| Alphabetical A-Z | `title asc` (default) |
| Alphabetical Z-A | `title desc` |

**Page sizes:** `[10, 25, 50]` — Query param: `limit`

**XL layout:** Search input (`flex:1`, no `max-width` cap, `order:-1`) + controls block
(`flex-shrink:0`) in one nowrap row — search on the left, dropdowns on the right.

**MD/SM layout:** Controls block (`width:100%`) fills the first row with "Results per page"
left and "Sort by" right (`justify-content:space-between` on `.hdx-v2-nav-controls`).
Search bar (`flex-basis:100%`) wraps to a full-width second row below.

DOM order is `__right` first, `__search` second; CSS `order:-1` on `__search` at XL
moves it visually before `__right`.

### Differences from Dataset Search

| Feature | Dataset search | Org list |
|---|---|---|
| Sort options | Last Modified, Trending, etc. | Alphabetical A-Z / Z-A only |
| Page sizes | 10, 25, 50, 100 | 10, 25, 50 |
| Autocomplete | Yes | No |
| Filters sidebar | Yes (LG+) | None |

---

## 6. Rendering Strategy

### Template loop

```jinja2
{% for org in page.items %}
  {% snippet 'v2/components/org-list-card.html',
      org=org,
      member_count=h.get_group_members(org.id) %}
{% endfor %}
```

`h.get_group_members(org.id)` calls `member_list` action per org — N+1 pattern (same
as v1). For anonymous users the action falls back to `include_users=False` and returns 0
(auth restriction in CKAN). Member count is only meaningful for authenticated users.

### Pagination

```jinja2
{% if page.page_count > 1 %}
  <div class="hdx-v2-org-list-pagination">
    {% snippet 'v2/components/pagination.html',
        size='md',
        current_page=page.page,
        total_pages=page.page_count,
        base_url=h.url_for('organizations_index', q=q, sort=sorting_selected, limit=limit_selected) ~ '&page=' %}
  </div>
{% endif %}
```

The `hdx-v2-org-list-pagination` wrapper uses `display:flex; justify-content:center`
to centre the pagination row.

---

## 7. Responsive Strategy

### Page Layout

No sidebar. Full-width single column at all breakpoints (same as v1). The Figma XL sidebar
column is removed entirely.

### KPI Row

Commented out at all breakpoints (see §2, "KPI Cards"); a `title_count` badge next to the page title shows the organisations count instead.

### Controls (search + sort)

| Breakpoint | Behaviour |
|---|---|
| XL | Search (`flex:1`, `order:-1`) + controls (`flex-shrink:0`) in one nowrap row |
| MD | Row 1: controls full-width (Results per page ← → Sort by, `space-between`); Row 2: search full-width |
| SM | Same as MD — controls above (space-between), search full-width below |

No "N Results" count label — not part of the Figma design.

### Pagination

`hdx-v2-org-list-pagination` wrapper: `display:flex; justify-content:center` — pagination
is horizontally centred at all breakpoints.

### Card

| Breakpoint | Behaviour |
|---|---|
| XL | Left col ~45rem + right col flex:1 |
| MD | Left col ~25.5rem + right col |
| SM | Stack; right col hidden; description hidden |

---

## 8. Edge Cases

| Case | Expected behaviour |
|---|---|
| No organisations | `page.item_count == 0` → show empty state message ("No organisations found") |
| Empty search result | Same empty state; preserve search input value |
| No description | Hide `.c-org-list-card__description` entirely |
| Very long title | 2-line clamp with `text-overflow: ellipsis` |
| Very long description | Fully hidden by default; "Show more" reveals all; no layout overflow |
| Large dataset count | Format with `h.hdx_format_number_si()` (e.g. `4800` → `"4.8k"`) |
| `member_count = 0` | Show "0 Members" — expected for anonymous users (CKAN auth restriction) |
| `package_count = None` | Treat as 0, show "0 Datasets" |
| Missing `created` date | Show fallback ("Unknown") or hide the date line |
| Single page of results | Omit pagination (existing `c-pagination` already handles `total_pages <= 1`) |
| `limit` param missing / invalid | Default to 25 (already handled in view) |

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| Member count always 0 for anonymous users | CKAN `member_list` action requires auth; fallback returns 0. Known limitation — same as v1 |
| `clamped-text.js` not triggering | Description must have `max-height:0` by default; `clamped-text.js` detects overflow on `DOMContentLoaded` |
| Inconsistent card layout | Test at XL / MD (48rem) / SM breakpoints with long titles and long descriptions |
| KPI vars undefined in view | `light_organization.py._index()` must provide `kpi_datasets`, `kpi_orgs`, `kpi_locations`; without them cards show "0" |
| Sort param divergence | Only `title asc` / `title desc` are valid for `filter_and_sort_results_case_insensitive`; other values fall back to default |

---

## 10. Decisions Taken

**Sort options** → **Alphabetical A-Z / Z-A only** (matches Figma; backend only supports
`title asc` / `title desc` for in-memory sort; datasets asc/desc also supported but not
surfaced in v2 per Figma).

**D1. KPI data source** → **Computed in `_index()` from already-loaded data.**
`kpi_orgs = len(all_orgs)`. `kpi_datasets` and `kpi_locations` from cached lists.

**D2. Number formatting** → **SI suffixes via `h.hdx_format_number_si()`.**
`4800 → "4.8k"`, `1200000 → "1.2M"`. Applied to both dataset and member counts.

**D3. v2 gate** → **Direct template replacement** (no `{% if v2 %}` gate — same as task 048).

**D4. Page size options** → **10 / 25 / 50** (aligns with search results page default range).

**D5. Member count** → **Pass `h.get_group_members(org.id)` per org (N+1 pattern).**
Returns 0 for anonymous users (CKAN auth restriction — known limitation). Acceptable;
same as v1.

**D6. Description display** → **Fully hidden initially; `clamped-text.js` reveals on click.**
`max-height:0` by default. `data-module="clamped-text"` + `data-clamped-content` on the
`<p>` element. "Show more" → "Show less" toggle.

**D7. Count label** → **No "N Results" label.** The Figma `.datasets-parent` element is
not a page-level result counter; it does not map to a rendered UI element.

**D8. "Show more" JS** → **Reuse existing `clamped-text.js`** (`fanstatic/v2/components/clamped-text.js`).
No new JS module needed.

**D9. Org card** → **Reusable snippet** at `v2/components/org-list-card.html`; also
documented in the `components.html` demo page.

**D10. Sidebar** → **No sidebar.** Removed entirely.

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/…/templates/v2/page.html` | `content_class` applied whenever set (removed `and secondary_block_output` guard); enables no-sidebar pages to use a named content flex rule |
| `ckanext-hdx_theme/…/templates/organization/index.html` | Replace v1 with v2; extends `v2/page.html`; sets `content_class = 'hdx-v2-content-columns__content'` |
| `ckanext-hdx_theme/…/templates/v2/components/org-list-card.html` | New org card snippet |
| `ckanext-hdx_theme/…/templates/v2/components.html` | Add org-list-card demo section |
| `ckanext-hdx_theme/…/hdx-styles/src/…/v2/components/org-list-card.less` | New card LESS |
| `ckanext-hdx_theme/…/hdx-styles/src/…/v2/org-list-page.less` | New page LESS (imports `nav-controls.less`) |
| `ckanext-hdx_theme/…/hdx-styles/src/…/v2/nav-controls.less` | New shared nav-controls LESS (also used by search-page) |
| `ckanext-hdx_theme/…/fanstatic/v2/pages/org-list.js` | New search Enter handler |
| `ckanext-hdx_theme/…/fanstatic/v2/url-nav.js` | New shared `setNavParam` module |
| `ckanext-hdx_theme/…/fanstatic/webassets.yml` | Add `v2-org-list-page-styles`, `v2-org-list-page-scripts` bundles |
| `ckanext-hdx_theme/…/helpers/helpers.py` | Add `hdx_format_number_si(n)` helper |
| `ckanext-hdx_theme/…/plugin.py` | Register `hdx_format_number_si` helper |
| `ckanext-hdx_org_group/…/views/light_organization.py` | Add `kpi_datasets`, `kpi_orgs`, `kpi_locations` to `template_data` |
| `ckanext-hdx_theme/…/fanstatic/v2/pages/search.js` | Extract `setNavParam` → `url-nav.js` (use `window.hdxSetNavParam`) |
| `ckanext-hdx_theme/…/hdx-styles/src/…/v2/search-page.less` | Extract nav-controls block → `nav-controls.less` |
