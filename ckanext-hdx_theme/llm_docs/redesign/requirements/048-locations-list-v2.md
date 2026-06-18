# 048 — All Locations List (v2)

**Scope:** Migrate `/group/` (All Locations) to v2 — layout, KPI cards, alphabetical list, anchor nav sidebar, filter toggle, sort buttons.  
**Search is excluded from scope. Map markup is preserved from v1 but not redesigned.**  
**Figma sources:** `all-location-xl.html`, `all-location-xl-title-kpi.html`, `all-location-xl-legend.html`, `all-location-xl-title-filter.html`, `all-location-xl-content.html`, `all-location-md.html`, `all-location-md-content.html`, `all-location-sm.html`

---

## Context

The existing All Locations page (`/group/`) is a JS-driven page that renders a Leaflet map and an alphabetical country list in a 6-column layout. The v2 redesign **replaces** the existing template directly — no v1 fallback gate is needed.

Key structural changes vs v1:
- KPI cards (new component — already exists on branch)
- Anchor navigation: **left sidebar** (XL) / **right vertical sidebar** (MD) / hidden (SM)
- Alphabetical grouping: server-side Jinja2, flat per-letter section, **3-column grid** (XL) / **2-column grid** (MD) / 1-column (SM)
- HRP items visually distinct: lightcyan background + powderblue border
- Filter: "Show only locations with HRP" toggle
- Sort: A–Z / Z–A buttons using `c-button` component

---

## 1. Existing Implementation Audit

### Template

| Item | Detail |
|---|---|
| **Current template** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/group/index.html` |
| **Extends** | `page_light.html` |
| **Action** | Replace this template entirely with the v2 implementation |

The current template renders the page shell and injects `countries` as a JSON blob into a hidden `<div id="datasetCounts">`. All DOM construction is deferred to JavaScript.

### Controller / Data Logic

| Item | Detail |
|---|---|
| **View** | `ckanext-hdx_org_group/ckanext/hdx_org_group/views/group.py` → `index()` → `GroupIndexReadLogic` |
| **Logic class** | `ckanext-hdx_org_group/ckanext/hdx_org_group/controller_logic/group_read_logic.py` |
| **Group source** | `get_action('cached_group_list')()` — returns all groups sorted by `display_name` (accent-stripped), with `all_fields=True, include_extras=True, package_count=True` |
| **Dataset counts** | `_fetch_dataset_counts()` — Solr faceted search on `groups` field; adds `dataset_count` per country |
| **World first** | `get_all_countries_world_first()` inserts `world` at index 0 |
| **Template var** | `countries` — JSON-encoded list of country dicts |

### Country dict shape (per item in `all_countries_world_1st`)

```python
{
    'id': str,           # CKAN group UUID
    'name': str,         # ISO code, e.g. 'afg'
    'title': str,        # Display name, e.g. 'Afghanistan'
    'display_name': str, # Same as title for groups
    'dataset_count': int,# Added by GroupIndexReadLogic
    'activity_level': 'active' | None,  # 'active' = HRP location
    # ... other CKAN group fields
}
```

`activity_level='active'` is stored as a CKAN group extra and surfaced via `include_extras=True`.

### Data Grid

"Locations part of Data Grid" shown in the Figma KPI cards has no direct equivalent in the current `GroupIndexReadLogic`. Data Grid membership is managed via the `hdx_datagrid_show` action (separate from the group list). A backend change or new helper was required for this KPI value.

### Existing JavaScript (v1 only — NOT carried forward to v2)

| File | Role |
|---|---|
| `fanstatic/browse_/browse.js` | `prepareCountryList()` — builds DOM, groups by letter, adds inactive class |
| `fanstatic/browse_/browse-init.js` | Calls `prepareCountryList()` and `prepareMap()` on load |

The 6-column letter grouping and the omission of 'X' are artifacts of the v1 JS layout. The v2 template handles grouping in Jinja2 with a 3/2/1-column CSS grid.

---

## 2. Figma Design

### XL Overall Structure

The outer page (`all-location-xl.html`) is composed of stacked blocks:

```
breadcrumb          ← white bg, no border
titlekpi            ← white bg, padding: 2.5rem 3rem, gap: 2rem
  title + text-buttons
  kpi row (3 cards)
[map block]         ← OUT OF SCOPE
legend              ← padding: 1rem 3rem
titlefilter         ← white bg, padding: 2rem 3rem 1rem
  Alphabetical order title (inline with controls)
  HRP toggle + Sort buttons
header              ← flex row: sidebar + scrollable content
  header-inner (left sidebar, 20.375rem)
    "Jump to section"
    A–Z 5-column grid
  warpper (right, overflow-y:auto)
    [search — EXCLUDED]
    letter sections (3-col grid each)
```

### Title + KPI (`all-location-xl-title-kpi.html`)

```
.titlekpi {
  padding: 2.5rem 3rem;
  gap: 2rem;
  background: #fff;
}
  .title-parent  (flex column, gap: 1rem)
    <b>Locations</b>        font: Merriweather Bold 2rem, line-height 130%
    .text-buttons-parent  (flex row, gap: 0.75rem, font 14px Roboto)
      "Interactive map" + arrow-down-icon    color: royalblue #1862d8, underline, weight 500
      "|" separator                          color: #9db1b3
      "Alphabetical order" + arrow-down-icon color: #3f4748 (not blue)

  .kpi  (flex row, gap: 1rem)
    3 × .kpi-locations-card (flex:1, padding: 0.75rem, border: 1px solid #ebeff0, border-radius: 4px)
      label (16px Roboto) + arrow-down-icon (= info icon)
      bold number (1.5rem Merriweather, color: #2f3536)
```

**Existing component:** `v2/components/kpi-card.html` + `v2/components/kpi-card.css` — **already on branch, use as-is.**

### Legend (`all-location-xl-legend.html`)

```
.legend {
  padding: 1rem 3rem;
  display: flex; align-items: center; gap: 0.75rem;
  font: 14px Roboto, color: #2f3536;
}
  .legend-child {
    width: 1rem; height: 1rem;
    border-radius: 2px;
    background: #d4eae4;   ← lightcyan square (NOT a circle)
  }
  "Locations with a Humanitarian Response Plan"
```

Static — no dynamic content.

### Title + Filter Row (`all-location-xl-title-filter.html`)

```
.titlefilter {
  padding: 2rem 3rem 1rem;
  background: #fff;
}
  .dataset-title-parent  (flex row, align-items: center, gap: 3rem)
    <b>Alphabetical order</b>   width: 17.375rem, font: 1.5rem Merriweather Bold
    .frame-parent  (flex: 1, align-items: center, justify-content: space-between, gap: 1.25rem)
      .text-link-label-parent  (flex row, gap: 1rem, cursor: pointer)
        "Show only locations with Humanitarian Response Plan"
        .toggle (2rem×1rem, border-radius:8px, bg:#d8e0e1)
          .switch (0.75rem circle, bg:#fff)
      .sort-by-parent  (flex row, gap: 0.5rem)
        "Sort by" label (14px Roboto)
        .buttons-parent  (flex row, gap: 0.25rem)
          ACTIVE button:   bg:#fafbfb, border:1px solid #101212, padding:0.5rem, border-radius:2px
          INACTIVE button: bg:#fff, border:1px solid #d8e0e1, shadow, padding:0.5rem
```

### Anchor Navigation Sidebar + Content (`all-location-xl-content.html`)

```
.header  (flex row, bg: #fff)
  .header-inner  (width: 20.375rem, padding: 2rem 0 0 3rem)   ← LEFT SIDEBAR
    .jump-to-section-parent  (flex column, gap: 1.5rem)
      "Jump to section"  (16px Roboto, font-weight: 600)
      .letter-anchor-links-parent  (CSS grid, repeat(5,1fr), width:15.875rem, gap:0.75rem)
        Each letter cell: 2.312rem wide, padding: 0.5rem 0.75rem, border-radius: 2px
          ACTIVE (A): color: royalblue #1862d8, font-weight: 500
          INACTIVE: color: #3f4748

  .warpper  (overflow-y: auto, padding: 2rem 3rem 6rem, gap: 2rem)   ← SCROLLABLE CONTENT
    [search — EXCLUDED]
    .a, .a, ...  (each letter section, width: 53.625rem)
      <b class="dataset-title">A</b>   (1.5rem Merriweather, color: #2f3536)
      .selection-item-parent  (grid, repeat(3,1fr), gap: 0.75rem)
        HRP item:    bg: #d4eae4, border: 1px solid #a8d5c9, shadow, padding: 0.5rem
        Normal item: bg: #fff,    border: 1px solid #d8e0e1, shadow, padding: 0.5rem
        All items:   border-radius: 2px, font: 14px Roboto, color: #3f4748
```

**No location starts with X in the data. Figma showed X as disabled; the implementation excludes X entirely from `all_letters`.**  
**"World" is NOT in the alphabetical list.**

### MD Layout (`all-location-md-content.html`)

```
.frame-parent  (flex column, padding: 2rem 3rem, gap: 2rem)
  .frame-group  (flex column, gap: 2rem)
    .dataset-title-parent  (flex COLUMN, gap: 0.5rem)   ← title stacked above controls
      <b>Alphabetical order</b>   1.25rem Merriweather
      .frame-container  (flex row, justify-content: space-between, gap: 1.25rem)
        HRP toggle + label
        Sort by + buttons (12px text, padding: 0.25rem 0.5rem — smaller than XL)
    [search — EXCLUDED]

  .frame-div  (flex row, gap: 0.75rem)
    .a-parent  (flex:1, flex column, gap: 2rem)   ← content
      letter sections:
        <b>A</b>   1.25rem Merriweather
        .selection-item-parent (grid, repeat(2,1fr), gap: 0.5rem)
          HRP item:    bg: #d4eae4, border: 1px solid #a8d5c9, padding: 0.375rem
          Normal item: bg: #fff,    border: 1px solid #d8e0e1, padding: 0.375rem
          Font: 12px Roboto

    .letter-anchor-links-parent  (flex column, gap: 0.375rem)   ← RIGHT SIDEBAR
      Each anchor: 1.5rem wide, padding: 0.25rem 0.5rem
      ACTIVE (A): royalblue, font-weight: 600
      INACTIVE: darkslategray
```

### SM Layout (`all-location-sm.html`)

```
.sm-all-locations
  .breadcrumb
  .titlekpi
    <b>Locations</b>   (no text-buttons)
    .kpi  (3 KPI cards — no info icon)
  .letters-list
    .legend  (static, same square)
    .frame-wrapper
      "Show only locations with HRP" + toggle
      (NO sort buttons in SM — implementation includes them at all breakpoints)
    [search — EXCLUDED]
    .frame-parent
      letter sections with data-scroll-to attrs
      Single-column location items
    (NO anchor nav bar — implementation renders right sidebar at all breakpoints)
```

---

## 3. Component Strategy

### Reuse Map

| UI Element | Component | Notes |
|---|---|---|
| KPI card | `c-kpi-card` → `v2/components/kpi-card.html` | **Already exists on branch** |
| Info icon on KPI | `c-info-icon` → `v2/components/info-icon.html` | Used inside kpi-card |
| Location item | `c-selection-item` → `v2/components/selection-item.html` | `color='cyan'` for HRP items, `color='light'` otherwise; `width: 100%; min-width: 0` on component base for grid sizing |
| HRP filter toggle | `c-toggle` → `v2/components/toggle.html` | |
| Sort buttons | `c-button` → `v2/components/button.html` | Secondary style, with active/selected modifier |
| Top text-buttons | `c-text-button` → `v2/components/text-button.html` | `arrow-down` icon, royalblue (map) / darkslategray (alpha) |
| Letter anchor (XL sidebar) | `c-letter-anchor` → `v2/components/letter-anchor.html` | Size `lg`, state `active`/`enabled`/`disabled` |
| Letter anchor (MD + SM sidebar) | `c-letter-anchor` → `v2/components/letter-anchor.html` | Size `lg` (all breakpoints) |

### New Files

| File | Purpose |
|---|---|
| `templates/light/group/index.html` | Replace existing template |
| `hdx-styles/src/common/less/v2/locations-list-page.less` | Page LESS (already scaffolded?) |
| `fanstatic/v2/all-locations-page.js` | Filter toggle + sort JS |

---

## 4. KPI Card Definition

**Already implemented** at `v2/components/kpi-card.html` with CSS at `v2/components/kpi-card.css`.

### Usage in template

```jinja2
<div class="c-kpi-row">
  {% snippet 'v2/components/kpi-card.html',
      label=_('Total locations'),
      value=total_count,
      tooltip_text=_('...'),
      tooltip_id='kpi-total' %}

  {% snippet 'v2/components/kpi-card.html',
      label=_('HRP locations'),
      value=hrp_count,
      tooltip_text=_('...'),
      tooltip_id='kpi-hrp' %}

  {% snippet 'v2/components/kpi-card.html',
      label=_('Locations part of Data Grid'),
      value=datagrid_count,
      tooltip_text=_('...'),
      tooltip_id='kpi-datagrid' %}
</div>
```

The `kpi-card.css` already hides the info icon on SM via `@media (max-width: 47.99rem) { .c-kpi-card__header .c-info-icon { display: none; } }`.

---

## 5. Alphabetical Grouping Logic

### v1 approach (NOT carried forward)

Grouping in `browse.js` — hardcoded 6 letter columns, rendered into Bootstrap grid.

### v2 approach (server-side Jinja2)

Grouping in `GroupIndexReadLogic` or a helper, passed as a structured dict:

```python
grouped_countries = {
    'A': [{'title': 'Afghanistan', 'name': 'afg', 'href': '/group/afg', 'is_hrp': True}, ...],
    'B': [...],
    ...
}
letters_present = ['A', 'B', 'C', ...]
```

**Special characters:** Åland Islands normalised to 'A'. Use `strip_accents()` from `ckanext-hdx_package/ckanext/hdx_package/helpers/caching.py`.

**World:** `get_all_countries_world_first()` inserts it at index 0. In v2 the list must **exclude the "World" location** — skip it when building `grouped_countries`.

**X:** No location starts with X in the data. X is excluded from `all_letters` in the template — no anchor entry is rendered at any breakpoint.

**Items per section:** The letter heading (`<b>A</b>`) is a Merriweather Bold heading, not a `c-section-title` component. Render inline in the template.

---

## 6. Sidebar / Anchor Navigation Behavior

### XL — Left sidebar (sticky)

```
Position:  left of scrollable content, sticky
Width:     20.375rem
Padding:   2rem 0 0 3rem (top/left only)
Content:   "Jump to section" (16px, weight 600)
           5-column CSS grid of c-letter-anchor (size=lg)
           Grid: repeat(5, 1fr), gap 0.75rem, width 15.875rem
```

The `.warpper` (scrollable content) scrolls while `.header-inner` (sidebar) stays in place. Implement with CSS (`position: sticky; top: 0; align-self: flex-start`) or use the scrollable-content-area pattern.

**Active state:** JS `IntersectionObserver` updates the active letter as sections scroll into view.
**Disabled state:** Any empty letter (after filtering) rendered with `state='disabled'`. X is excluded entirely — not rendered at any size.

### MD — Right vertical sidebar

```
Position:  right of content, after .a-parent in flex row
Direction: vertical (flex-direction: column), gap: 0.375rem
Width:     auto (letter links: 2.3125rem each — size='lg')
```

The MD sidebar is on the **right** of the content (flex `order: 1`), sticky (`position: sticky; top: 0; align-self: flex-start`), with natural content-driven width (single column of letter anchors).

### SM — Right sidebar (no heading)

Same component as MD: right-side vertical sidebar with letter anchors. The "Jump to section" heading is hidden below XL via CSS. The sidebar renders at all breakpoints.

---

## 7. Filtering and Sorting Logic

### "Show only locations with HRP" toggle

- `c-toggle` component with label to the left
- Toggled on → hide all items where `is_hrp=False`; also hide letter headings with no visible items; update disabled state of letter anchors
- Implemented client-side in `all-locations-page.js`
- Toggle uses `c-toggle` — confirmed by Figma `.toggle`/`.switch` pattern

### Sort by

- Two `c-button` (secondary style) buttons: "Alphabetical A-Z" (default active) | "Alphabetical Z-A"
- Active button: use a selected/active modifier class (dark border `#101212`, bg `#fafbfb`)
- Inactive button: default secondary (gainsboro border, white bg, shadow)
- "Alphabetical Z-A": reverses order of letter sections AND items within each section
- Implemented client-side in JS

### SM filter

- Toggle + sort buttons — same JS logic applies at all breakpoints
- Sort buttons are rendered at SM/MD/XL; no breakpoint-specific hiding

---

## 8. Responsive Strategy

### XL (`≥ 80rem / 1280px`)

| Zone | Behavior |
|---|---|
| Breadcrumb | White bg, no border |
| Title | Merriweather Bold 2rem |
| Text-buttons | "Interactive map" (royalblue) + "Alphabetical order" (darkslategray), both with arrow-down icon |
| KPI row | 3 flex cards with info icons |
| Legend | 1rem square + text, padding 1rem 3rem |
| Title+filter row | "Alphabetical order" (17.375rem fixed) inline with HRP toggle + Sort buttons |
| Sidebar | Left, 20.375rem, sticky, 5-col letter grid, `c-letter-anchor` size=lg |
| Content | Right of sidebar, `overflow-y: auto`, 3-col item grid, gap 0.75rem |
| Item padding | 0.5rem |
| Letter heading | 1.5rem Merriweather Bold |

### MD (`< 80rem`)

| Zone | Behavior |
|---|---|
| Breadcrumb | Same (white bg, no border) |
| Title | Merriweather Bold (smaller) |
| Text-buttons | Absent (no "Interactive map" / "Alphabetical order") |
| KPI row | 3 cards, NO info icons |
| Legend | Same static |
| Title+filter | "Alphabetical order" stacked above controls (column), not inline |
| Sort font | 12px (smaller than XL 14px) |
| Sort padding | 0.25rem 0.5rem |
| Sidebar | RIGHT vertical, natural/content width (single letter column), sticky |
| Content | Left of sidebar (flex:1), 2-col item grid, gap 0.5rem |
| Item padding | 0.375rem |
| Letter heading | 1.25rem Merriweather |

### SM

| Zone | Behavior |
|---|---|
| Title | No text-buttons |
| KPI | No info icons |
| Filter | Toggle + sort buttons (sort visible at all breakpoints) |
| Content | 1-column items |
| Anchor nav | Right sidebar rendered (same as MD, no heading) |

---

## 9. Data Requirements

### Backend additions needed in `GroupIndexReadLogic`

| Data | Current status | Action needed |
|---|---|---|
| `total_count` | Not explicitly computed | `len(all_countries_world_1st) - 1` (minus World) |
| `hrp_count` | Not computed | `sum(1 for c in countries if c.get('activity_level') == 'active')` |
| `datagrid_count` | Not available | Implemented in `group_read_logic.py` |
| `grouped_countries` | Not computed (done in JS) | New helper — group by first letter, exclude 'world', normalise accents |
| `letters_present` | Not computed | Keys of `grouped_countries` |

### Template variables (proposed)

```python
{
    'total_count': int,
    'hrp_count': int,
    'datagrid_count': int | None,   # TBD — may ship as placeholder
    'grouped_countries': dict,       # {'A': [country_dict, ...], ...}
    'letters_present': list,         # ['A', 'B', ...]
}
```

---

## 10. Exact Colors and Tokens

| Figma color | Hex | HDX token (to confirm) |
|---|---|---|
| HRP item bg | `#d4eae4` | `var(--hdx-teal-1)` or similar |
| HRP item border | `#a8d5c9` | `var(--hdx-teal-3)` or similar |
| Normal item border | `#d8e0e1` | `var(--hdx-neutral-2)` |
| Active sort button bg | `#fafbfb` | `var(--hdx-neutral-1)` |
| Active sort button border | `#101212` | `var(--hdx-neutral-11)` |
| Inactive sort border | `#d8e0e1` | `var(--hdx-neutral-2)` |
| Letter heading | `#2f3536` | `var(--hdx-neutral-9)` |
| Item text | `#3f4748` | `var(--hdx-neutral-8)` |
| Active anchor | `#1862d8` | `var(--hdx-blue-5)` |
| Jump to section | `#101212` | `var(--hdx-neutral-11)` |
| Shadow | `0px 1px 4px rgba(0,0,0,0.04)` | `var(--hdx-shadow-drop)` |

---

## 11. Edge Cases

| Case | Expected behavior |
|---|---|
| No locations | Show KPIs as 0; hide alphabetical section; show empty state message |
| Letter with no entries (after HRP filter) | Hide letter section; disable corresponding anchor |
| X letter | Excluded from `all_letters` — no anchor or section rendered at any breakpoint |
| All filtered out by HRP toggle | Show message; all letter sections hidden |
| Very long location name | `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` — already in Figma `.title10` class |
| Special characters (Å, É, etc.) | Normalise for grouping; display original title |
| `world` group | Excluded from the v2 list entirely |
| HRP toggle + Z-A sort simultaneously | Both compose correctly |

---

## 12. Risks

| Risk | Mitigation |
|---|---|
| Grouping divergence | Test accent normalisation against v1 sort order |
| `datagrid_count` KPI unavailable | ✅ Implemented in `group_read_logic.py` |
| JS filtering/sorting complexity | ✅ Toggle and sort are independent state; implemented in `all-locations-page.js` |
| Sidebar sticky on XL | ✅ `position: sticky; top: 0; align-self: flex-start` — works at all breakpoints |
| X letter anchor | ✅ X excluded from `all_letters`; no render needed |
| SM sort buttons | ✅ Sort buttons rendered at all breakpoints; no SM-specific hiding |

---

## Decisions Taken

| # | Decision | Rationale |
|---|---|---|
| 1 | Replace `light/group/index.html` directly | Full migration — no v1 fallback needed |
| 2 | Server-side Jinja2 grouping | Removes JS dependency; cleaner template |
| 3 | Left sidebar (XL) / right sidebar (MD + SM) | Confirmed from `all-location-xl-content.html` and `all-location-md-content.html`; SM renders same sidebar as MD (no heading) |
| 4 | 3-col grid (XL), 2-col grid (MD) | Confirmed from Figma CSS |
| 5 | `c-selection-item` with `color='cyan'` for HRP items | `c-selection-item--cyan` variant matches Figma HRP bg/border; `width: 100%; min-width: 0` added to component base for grid use |
| 6 | `c-button` for sort buttons | User confirmation + Figma button style matches |
| 7 | `c-kpi-card` (existing) | Already on branch — reuse as-is |
| 8 | Map (v1 markup) preserved but not redesigned; search excluded | Template retains `<div id="map">` and Leaflet asset bundle; only the search box is absent |
| 9 | World excluded from list | Not shown in Figma |
| 10 | Tertiary style + `is-active` class for sort buttons | Matches `:active` pseudo-class visually; `c-button` component extended with `is-active` modifier for all three button styles |
| 11 | Sidebar sticky at all breakpoints, 25% width at XL only | SM/MD sidebar has natural content width (letter column); 25% flex via `.v2-sidebar-flex()` applied at XL only |
| 12 | Standard `secondary`/`primary` block layout with `outer_row_class` | Matches dataset/resource/search page structure; white background via `outer_row_class` wrapper |
| 13 | Z-A reverses both letter sections and items within | Both letter order and country order within each section are reversed for consistent Z-A experience |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/group/index.html` | Replace with v2 implementation |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/controller_logic/group_read_logic.py` | Add `total_count`, `hrp_count`, `datagrid_count`, `grouped_countries`, `letters_present`; exclude World |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/views/group.py` | Pass new template vars |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/locations-list-page.less` | Page-specific LESS (or update existing scaffolded file) |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/all-locations-page.js` | Filter toggle + sort JS |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/kpi-card.html` | Already exists — no change needed |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/components/kpi-card.css` | Already exists — no change needed |
