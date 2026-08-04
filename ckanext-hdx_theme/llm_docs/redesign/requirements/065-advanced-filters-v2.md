# Advanced Filters + Archived Toggle + Applied Filters Pills (v2 Migration)

**Scope:** Search results page only (`/dataset` search, `v2=true` gate). UI/UX redesign only —
all existing filtering logic, URL/state behavior, and analytics must be preserved unchanged.

---

## Context

Task 031 (basic filtering) built the v2 filter sidebar/overlay for Location, Organisation, Format,
Topics, and Advanced filters, explicitly deferring "Show only / Archived controls" and any pill UI.
Task 056 (org page datasets) reconfirmed that deferral as decision **D12**: *"Figma's 'Time period'
/ 'Data type' / 'Show only' filter sections are out of scope for this task; the existing
`v2/search-filters.html` facet set is reused unchanged, with no new top-level dropdowns or
regrouping."* This task is that deferred work, scoped by the current brief to exactly three things:
the Archived datasets radio toggle, Applied Filters pills (XL only), and a Figma-alignment pass on
the already-built Advanced filters dropdown. Data type and Time period remain out of scope — they
don't exist in v2 today and stay that way here.

---

## Scope

### Included

- Archived datasets radio toggle ("Show only: Actively maintained datasets / Archived datasets")
- Advanced filters panel — Figma-alignment audit of the existing dropdown (no functional rebuild)
- Applied filters pills (XL/LG only)
- Show more / Show less (pill overflow)
- Clear all (pills section)
- Responsive behavior — SM / MD / XL

### Excluded

- Data type filter
- Time period filter
- "Show more" inside the filters panel (already removed by task 031 — stays removed)

---

## 1. Existing Implementation Audit

### 1.1 Advanced filters panel (v1)

- `templates/search/snippets/package_search_facets.html` — v1 facet renderer (macro
  `render_facet_list`), called from `package_list.html`'s v1 branch and from
  `light/snippets/package_list.html` (the `/m/dataset` mobile route, still fully v1).
- `ckanext-hdx_search/ckanext/hdx_search/controller_logic/search_logic.py::_prepare_facets_info()`
  (~line 431) builds `result['facets']['featured']` (the "Advanced filters" group: Sub-national,
  Geodata, P-Codes, Tabular Data, HDX HAPI, COD levels, HPC topics).
- `ckanext-hdx_search/ckanext/hdx_search/plugin.py::dataset_facets()` (line 277) registers the raw
  Solr facet fields.
- JS: `fanstatic/datasets/search-facets.js` (checkbox click → full-page navigation) and
  `datasets/list-header.js` (category collapse/expand + localStorage of open/closed panel state,
  in-category MiniSearch, "Show filter" switch).
- `package_search_facets.html:25` has a dead `ext_archived` "NEW" badge check — the code path that
  used to populate that facet item is commented out in `search_logic.py:610-613`, so it never fires.

### 1.2 Advanced filters panel (v2 — already implemented, task 031)

`templates/v2/search-filters.html` renders 5 groups today: Location (`groups`), Organisation
(`organization`), Format (`res_format`), Topics (`vocab_Topics`), and Advanced filters (`featured`
facet). The Advanced filters dropdown already computes the full Figma-expanded selection state: flat
`ext_*` boolean items plus nested COD/HPC parent-child groups with server-computed
all/some/none parent state (`_parent_all`/`_parent_some` in the template, JS only flips
`.indeterminate` on `DOMContentLoaded`). Figma does not wrap Advanced filters in a dropdown/panel
shell at all, unlike Location/Organisation/Format/Topics — see D5 in §6. "Clear selection" inside
the panel clears
`ADVANCED_FILTER_PARAMS` only, not `vocab_Topics` (shared with the Topics filter). No
expand/collapse "show more" exists inside any panel — 031 removed it deliberately, and this task
keeps it removed.

State is 100% URL-param driven: every checkbox click calls `updateUrl()` in
`fanstatic/v2/search-page.js` (constants `FILTER_PARAMS`, `ADVANCED_FILTER_PARAMS`), which mutates
`URLSearchParams` and does a full `window.location.href` navigation — no AJAX, no client-side
filter-state store. `ADVANCED_FILTER_PARAMS` includes `vocab_Topics` (also in `FILTER_PARAMS`)
because nested HPC advanced-filter items share that facet key; `clearAllFilters()` clears both
arrays' union. `031-basic-filtering.md`'s own Files/Data-Flow tables reference stale names
(`search.less`/`search.js`); the current compiled sources are `less/v2/search-page.less` and
`fanstatic/v2/search-page.js`.

### 1.3 Archived datasets toggle (v1 — current, live)

Not a checkbox — a pair of tab links, "Datasets [N] | Archived Datasets [N]", rendered by
`templates/search/snippets/archived_tabs.html`, included from `package_list.html:39` (v1 branch)
and `light/snippets/package_list.html:30`.

Backend: `search_logic.py`:
- `class ArchivedUrlHelper` (lines 877-935) computes `archived_url` (adds `ext_archived=1`) and
  `unarchived_url` (strips it), `show_archived_link`/`show_unarchived_link`,
  `archived_disabled`/`unarchived_disabled` (a tab renders as disabled text instead of a link when
  it would show 0 results), and `redirect_if_needed()` — force-redirects to the archived view if
  the default (unarchived) view has 0 results but archived datasets exist.
- `_search()` (lines 133-219): `ext_archived=1` → `hide_archived = False`; the actual Solr filter is
  applied at lines 217-219 via a tagged `fq` on `extras_archived` (`ARCHIVED_DATASETS_FACET_NAME =
  'archived'`, `helpers/constants.py:37`). Default (`hide_archived=True`) excludes archived
  datasets.
- `helpers.py::facet_url_extra_args()` (line 1265) preserves `ext_archived` when rebuilding other
  facet-toggle URLs, so switching a regular filter while on the Archived tab keeps you on that tab.
- Called from `ckanext-hdx_package/ckanext/hdx_package/views/light_dataset.py:100-103`
  (`generic_search()`, shared by `/dataset` and `/m/dataset`) — the redirect check runs server-side
  on every search request.

**Confirmed by direct read: `package_list.html`'s v2 branch (lines 82-181) does not render
`archived_tabs.html` or any archived-related markup at all.** This is a pure addition to v2, not a
replacement of an existing v2 element.

### 1.4 Applied filters / removable pills (v1 — current, live)

No pill/chip UI exists anywhere live today. What exists instead:
- A single global "Clear all" text link (`package_list.html:188-189`, identical in
  `light/snippets/package_list.html:15-17`), whose `href` targets the bare search URL but is
  intercepted by `datasets/list-header.js:100-107` → `getFilterUrlNew(true)` (lines 138-166), which
  skips facet params but **still re-adds** `q`, sort, page size, `ext_batch`, and `ext_archived`. In
  practice, "Clear all" today clears facet/advanced-filter selections only — it preserves search
  text, sort, page size, and the archived/unarchived tab.
- A numeric badge only (not pills) on the mobile filter toggle:
  `result['num_of_selected_filters']` (`search_logic.py:632-637`).
- `result['selected_titles']` / `selected_titles_str"` (`search_logic.py:480-481, 553-560,
  615-620`) exist only for SEO (page `<title>`, meta description, canonical link) — never rendered
  as UI.
- Legacy `snippets/facet_list.html` / `search/snippets/search_facets.html` contain an old per-category
  "Clear All" link pattern, but neither is invoked from the live `/dataset` or `/m/dataset` routes —
  dead code, not the live UX.

**Conclusion: pills are genuinely new UI, not a v1→v2 port.**

### 1.5 Analytics tracking

`fanstatic/google-analytics.js::setUpSearchTracking()` (`$(document).ready`, comment: *"We're only
sending mixpanel events. GA deals with search differently / automatically"*):
1. Serializes `#search-page-filters-form` / `#dataset-filter-form` (both forms exist identically in
   v1 and current v2 markup).
2. Maps recognized params via `mixpanelMapping` (lines 29-152): `q`, `vocab_Topics`, `res_format`,
   `organization`, `groups`, `license_id`, `cod_level`, `ext_subnational`, `ext_tabular_data`,
   `ext_geodata`, `ext_requestdata`, `ext_hxl`, `ext_sadd`, `ext_administrative_divisions`,
   `ext_p_coded`, etc.
3. **`ext_archived` is absent from this mapping** — the archived toggle has never been tracked, in
   v1 or v2.
4. If any mapped param has a value, fires `mixpanel.track("search", ...)` with page title, result
   count (`#analytics-number-of-results`), and search-box location. This fires on page load after
   navigation, not per click — consistent with every filter change being a full reload today.
5. `v2/search-page.js` has zero analytics calls of its own; the generic page-load tracker above is
   the only mechanism currently wired to v2 filters.

No `data-ga-*` attributes exist on any filter/facet markup. GTM `dataLayer` pushes are used for
other flows (share, download, resource preview, etc.) but never for search/filter events.

---

## 2. Figma Mapping

Files read: `xl-filters.html`, `md-filters.html`, `sm-filters.html`, `xl-applied-filters.html`,
`xl-applied-filters-expanded.html` (plus cross-referenced siblings `filter-active-filters.html`,
`filter-md-button.html`, `filter-md-button-active.html`).

**Filter panel (`xl/md/sm-filters.html`)** — one shared structure across breakpoints: Location,
Organisation, Time period (excluded), Data type (excluded), Format, Topics, Advanced filters
(with nested HPC/COD groups + "Show more/less" inside the group — excluded, 031 already removed
this pattern), and a "Show only" radio group (Actively maintained datasets / Archived datasets) at
the bottom. Breakpoint differences are container-only:
- **XL**: generous padding (`1.25rem 2.5rem 5rem 3rem`), no internal scroll, `border-right` —
  persistent sidebar column, matches the existing LG sidebar container.
- **MD**: tighter padding (`1.5rem`), `overflow-y: auto` — internally scrolling drawer, opened via
  the existing "Filter (N)" button + overlay (task 031).
- **SM**: smallest padding (`1rem`), `overflow-y: auto`, fixed height — same drawer pattern as MD.

The "Show only" radio markup (identical across all three files, only class suffixes differ):
selected option = filled ring+dot (`c-radio`-equivalent), unselected = empty ring. Label text is
exactly **"Archived datasets"** / **"Actively maintained datasets"**.

**Applied filters (`xl-applied-filters.html` / `-expanded.html`, XL only)** — pill row sits inside
the same header block as the "Datasets N" title, results-per-page/sort controls, and search box —
i.e. the same region as `package_list.html`'s v2 `hdx-v2-list-header` + `hdx-v2-search-bar-row`.
Structure: a "Clear all" text link, then the pill row (`flex-wrap: wrap`), then a "Show more"/"Show
less" text+chevron control shown only in the expanded/overflowing sample. Figma's own pill icon
usage is inconsistent (chevron on most, "x" on one) — resolved by decision D2 below in favor of the
one behavior our existing component supports.

No sm/md applied-filters Figma export exists — consistent with the task scope ("Applied Filters
Pills (LG ONLY)"); MD/SM continue to rely on the existing Filter-button badge count only.

---

## 3. State & Data Flow Analysis

No new state and no new backend calls. Everything below is a read-side projection of data
`search-filters.html` already has:

```
CKAN controller → full_facet_info (facets + archived_url_helper)
     ↓
search_results_wrapper.html → package_list.html (v2 branch)
     ↓
search-filters.html
  - Location/Organisation/Format/Topics: facet_list[key].items | selectattr('selected')
  - Advanced filters: facet_list['featured'].items (flat + nested), same selected-detection
    logic already used to build each dropdown's trigger text
  - Archived: full_facet_info.archived_url_helper (new — same object already computed
    server-side for the v1 tabs, just not read by any v2 template yet)
     ↓
Applied Filters pills = one pill per selected item across all of the above (Archived pill
appears only when the "Archived" option is selected — "Actively maintained" is the default,
no-op state and produces no pill, matching how v1 never showed a pill/tab-highlight for it either)
     ↓
Pill click / Archived radio click / Clear all click → all still just navigate to a URL built
from existing helpers (updateUrl()/clearFacet() for regular filters, archived_url_helper.*_url
for archived) → full page reload → same generic Mixpanel page-load event fires as today
```

No debounce or batching exists today (every checkbox is a full navigation) and none is introduced
here. No filter-count limit exists in the backend; none is introduced.

---

## 4. Archived Toggle Strategy

**D1 (confirmed):** the two `v2/components/radio.html` options navigate using the existing
`archived_url_helper.archived_url` / `.unarchived_url`, computed server-side per request — not the
generic `updateUrl()` facet mechanism used by the other filters. This preserves
`archived_disabled`/`unarchived_disabled` (0-result disabled state) and `redirect_if_needed()`
exactly, with zero new URL-building logic.

Integration:
- Added to `templates/v2/search-filters.html`, appended after the Advanced filters block
  (matches Figma's group ordering).
- `radio.html` params: `name='show_only'`, two `value`/`label` pairs ("active" / "Actively
  maintained datasets", "archived" / "Archived datasets"), `checked` bound to whether the current
  request has `ext_archived=1`, `state='disabled'` when the corresponding
  `archived_url_helper.*_disabled` flag is true.
- The "archived" option additionally passes `hint=True, hint_text=archived_url_helper.archived_explanation`
  — `radio.html`'s existing info-icon + tooltip params — matching Figma's icon next to "Archived
  datasets" (no icon on "Actively maintained"). Reuses the exact copy already live on the v1 tabs'
  `[?]` tooltip (`ArchivedUrlHelper.archived_explanation`, `search_logic.py:879`) — no new copy.
- Click handler navigates to the option's precomputed URL (same mechanism conceptually as every
  other filter's "click → new URL → full reload", just sourced from `archived_url_helper` instead
  of `updateUrl()`).
- No change to `_search()`, `ArchivedUrlHelper`, or the Solr `fq` — strictly a UI-layer addition.
- The v1 `archived_tabs.html` tab UI is untouched (still v1-only, still gated by `{% if not v2 %}`).

---

## 5. Applied Filters Strategy

**D2 (confirmed) — pills:** `v2/components/selection-item.html`, `size='s'`, `state='active'`
(default `color='light'`) for every pill — renders the existing `.c-selection-item__close` "x" icon
uniformly. Figma's chevron-vs-x inconsistency is resolved in favor of the single behavior the
component already supports; no component changes needed.

- **Clear all**: `v2/components/text-link.html`, `style='secondary'`, `size='xs'` — `c-text-button`
  only defines `l`/`m`/`s` sizes, not `xs`, so `text-link.html` (which does define `--size-xs`) is
  used instead, matching the pre-existing v1 "Clear all" pattern (an anchor intercepted by JS, see
  §1.4). Clears filter params only (same scope as today's v1 "Clear all" / `clearAllFilters()`),
  preserving `q`, sort, page size — and, consistent with `getFilterUrlNew(true)`'s current
  behavior, preserving `ext_archived` too.
- **Show more / Show less**: `text-button.html`, `style='tertiary'`, `size='s'`, `icon=True`,
  `icon_position='right'` (chevron-down), shown only when the pill row overflows one line.

**D4 (confirmed) — overflow detection:** dynamic row-wrap measurement in JS (compare the rendered
pill-row height against a single-row height) rather than a fixed pill-count threshold, so it stays
correct at any viewport width within the XL range rather than assuming a fixed count like Figma's
7-pill sample.

Pill generation: one pill per currently-selected item across Location, Organisation, Format,
Topics, and Advanced filters (flat `ext_*` + COD/HPC children), plus an Archived pill when
`ext_archived=1`. Removing a pill navigates to the same URL its source checkbox/radio-uncheck would
already produce (`updateUrl(facet, value, false)` for regular filters,
`archived_url_helper.unarchived_url` for the Archived pill) — no new removal logic, pills are purely
alternate triggers for existing navigation functions.

**Pill sizing (D6):** `.c-selection-item` defaults to `width:auto; max-width:none`; the pill row
caps each pill at `max-width: 12.5rem` (Figma's own `--max-w-200` token) via a `.c-selection-item-row`
wrapper in `components/selection.less` (mirroring the existing `.c-selection-item-grid` wrapper for
the All Locations grid), relying on the component's existing `.c-selection-item__label` ellipsis for
long labels.

**Pill row spacing (D7):** one uniform `--hdx-space-2` (0.5rem) gap throughout the row — between
pills, and between the pill row and "Clear all"/"Show more" — rather than Figma's two-tier gap
(0.5rem pill-to-pill vs 0.25rem/1rem for the outer wrapper).

Placement: inside `package_list.html`'s v2 branch, immediately after the `hdx-v2-search-bar-row`
form and before the MD/SM overlay markup, hidden below the XL breakpoint via CSS (same pattern
already used for `hdx-v2-list-header__controls` vs `__filter-btn`).

---

## 6. Component Strategy

### Reuse as-is (no changes needed)

| Component | Usage |
|---|---|
| `v2/components/radio.html` | Archived toggle — real `<input type="radio">`, matches Figma's ring+dot markup exactly |
| `v2/components/selection-item.html` (`state='active'`) | Applied filter pills — already renders the "x" close icon |
| `v2/components/text-link.html` | "Clear all" (`secondary`/`xs`) |
| `v2/components/text-button.html` | "Show more"/"Show less" (`tertiary`/`s`, icon right) |
| `v2/components/dropdown.html` + `dropdown-panel.html` + `list-item.html` + `checkbox.html` | Location/Organisation/Format/Topics dropdowns — unchanged |

### Extend only if needed

- Pill row wrapper — new CSS-only container for wrap/overflow measurement (no new template
  component; a plain wrapping `<div>` around repeated `selection-item.html` calls, styled via
  `less/v2/components/selection.less` or a new small `applied-filters.less` partial). Same partial
  adds a `max-width` override (D6) and a gap value (D7) that only apply within this row.
- Advanced filters (D5) — Figma renders this group inline, not inside a `dropdown.html` panel like
  the other four: drop the dropdown/panel wrapper for this one group and render the already-computed
  `_adv_ci.items` (see §1.2) directly as `selection-item.html` chips — every item, not only selected
  ones (`size='m'`; unselected = `state='enabled'`; selected = `state='active'`, `color='light'`,
  "x" close icon). Child rows (HPC/COD sub-items) render a separate leading indent-marker element
  (`hdx-v2-advanced-filters__indent-icon`, `v2/icons/indent.svg`) next to an independent
  `selection-item.html` chip — matching Figma's own `.indent-parent > .indent-icon + .selection-item`
  sibling structure, not a chip with a built-in leading icon. No chevron/disclosure icon on the
  parent group header row — always-expanded, nothing to disclose. No component-level (`.html`) code
  changes needed — only the render target for this one filter group.

### Do not

- No new filtering logic, no parallel filter system, no duplicated Jinja blocks — `search-filters.html`
  remains the single shared panel for both the LG sidebar and MD/SM overlay call sites.

---

## 7. Responsive Strategy

- **XL**: sidebar (existing) gains the Archived radio at the bottom of `search-filters.html`;
  Applied Filters pill row appears in the results header, above the dataset grid.
- **MD / SM**: existing overlay (task 031) gains the same Archived radio at the bottom of the same
  shared `search-filters.html` include — no separate markup needed since both call sites already
  render this one file. No pills at MD/SM — the existing "Filter (N)" button badge already
  communicates active-filter count at these breakpoints, per explicit task scope ("applied pills
  only on XL").

---

## 8. Risks

- **Breaking filter logic** — mitigated: Archived toggle and pill removal both navigate through
  existing, unmodified functions/helpers (`updateUrl()`, `clearFacet()`, `archived_url_helper.*_url`);
  no new URL-building or Solr-query code is introduced.
- **State desynchronization** — the Archived radio's `checked` state must reflect the *server's*
  view of `ext_archived` on every page load, including after `redirect_if_needed()` force-redirects
  the user to the archived view. Since the radio is rendered fresh on every full-page load (no
  client-side state), this is automatically consistent as long as `checked` is bound to the current
  request param rather than cached/assumed client-side.
- **Incorrect dataset results** — none of this work touches `_search()` or the Solr `fq` construction;
  risk is limited to UI wiring pointing at the wrong precomputed URL.
- **Analytics regression** — mitigated by D3 (strict parity: no new tracking code, archived/pill
  interactions ride the same existing page-load Mixpanel event as every other filter change today).
- **Overflow/pill layout issues** — mitigated: dynamic row-wrap measurement (D4) runs on
  `DOMContentLoaded`, `window.load` (webfonts/layout settle), and `resize`; long pill labels are
  bounded by D6's max-width/ellipsis rule.

---

## 9. Edge Cases

- **No filters applied**: no pill row rendered at all (matches "no pill/tab highlight when Actively
  maintained is selected" — it's the default, no-op state).
- **Many filters applied**: pill row overflows one line → "Show more" appears (D4); "Show less"
  collapses back.
- **Long filter names**: capped via D6's `max-width: 12.5rem` plus the existing
  `.c-selection-item__label` ellipsis, so a long label (e.g. a long organisation name) can't break
  the row-wrap measurement in D4.
- **Rapid filter toggling**: no debounce exists today (each click is an immediate full-page
  navigation) and none is introduced — consistent with "DO NOT introduce new state management."
- **Archived toggle combined with other filters**: already handled server-side —
  `facet_url_extra_args()` preserves `ext_archived` when building other facet-toggle URLs, and
  `archived_url_helper.archived_url`/`unarchived_url` preserve the other active facet params when
  toggling Archived. Pills for other active filters continue to render normally regardless of which
  Archived state is selected.
