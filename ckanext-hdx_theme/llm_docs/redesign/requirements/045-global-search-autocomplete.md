# Global Search Bar with Autocomplete (v2)

**Scope:** Homepage hero search + header navbar search (`v2=true` gate)

---

## Context

The v2 redesign includes a `c-autocomplete` component (Jinja2 snippet + LESS) that already
renders the correct HTML structure — input field, panel, chips, results list, confirm button.
However, the panel is never shown: `show_panel` is always `False` and no JavaScript is wired up.

The v1 header has a working typeahead under `.search-ahead` powered by **MiniSearch** and a
pre-built `feature-index.js` client-side index.  The v2 task is to bring equivalent
behaviour into the new component, reusing the same data source and search library.

**Old implementation MUST be kept in place.** The v1 `.search-ahead` in the old header
template (`templates/header-mobile.html`) and its JS (`search_/search.js`) must continue
to work unchanged.

---

## 1. Existing Implementation Audit

### v1 Global Search Typeahead (`search-ahead`)

| Item | Detail |
|---|---|
| **JS file** | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search_/search.js` |
| **Search library** | MiniSearch (`search_/minisearch.min.js`) — client-side full-text |
| **Text normalizer** | `normalize.js` — `toNormalForm()`, strips accents |
| **Asset bundle** | `hdx_theme/search-scripts` (loaded on every page via `v2/page.html`) |
| **Data source** | `var feature_index=[…]` in `search_/lunr/feature-index.js` |
| **Index fields** | `title`, `title_nf`, `extra_terms`, `event`, `url` |
| **Stored fields** | `title`, `extra_terms`, `event`, `url` |
| **Result limit** | 5 items max |
| **Result types** | previous searches, feature_index entries (`organisation` / `location` / `event`), dataset search link, dataviz search link |
| **Bold highlighting** | `process_title(title, termList)` — replaces matched terms with `<strong>` |
| **Analytics** | `hdxUtil.analytics.sendTopBarSearchEvents(searchTerm, resultType)` on `mousedown` |
| **Dropdown element** | `<div class="search-ahead"></div>` inside `.navbar-header` |
| **Input IDs wired** | `#q` and `#qMobile` (keyup + click) |
| **Close behaviour** | `blur` on input → `.hide()` on `.search-ahead` |

#### feature-index.js entry shape

```json
{ "title": "ACNUR (UNHCR)", "url": "https://data.humdata.org/organization/unhcr", "type": "organisation" }
{ "title": "Afghanistan",   "url": "https://data.humdata.org/group/afg",           "type": "location" }
```

#### feature-index.js builder

- CLI: `ckan hdx-feature-search` → runs `click_feature_search_command.py:build_index()`
- Source: direct SQL query on `group` table (active, non-closed)
- Organisations: `type='organisation'`, title = `"Name (ACRONYM)"`
- Locations: `type='location'`, title = `"Country Name"` (groups that are not crises)
- Crises: hardcoded event entries (`type='event'`) — excluded from v2 MVP (see §8)
- Output path: configured via `hdx.lunr.index_location`

### v2 Components (existing, no JS yet)

| Item | Detail |
|---|---|
| **Autocomplete wrapper** | `templates/v2/components/autocomplete.html` → `.c-autocomplete[role=combobox]` |
| **Search input** | `templates/v2/components/search-input.html` → `.c-search-input` |
| **LESS** | `hdx-styles/src/common/less/v2/components/input-field.less` |
| **Panel structure** | chips section (trending), results list, confirm button — all already in markup |
| **`show_panel` param** | currently always `False`; panel rendered only server-side, never via JS |

### Integration points today

| Location | Template | Current search element |
|---|---|---|
| Homepage hero | `templates/home/index.html` | `{% snippet 'v2/components/autocomplete.html', state='enabled' %}` — no JS |
| Header (XL/MD) | `templates/v2/header.html` | `{% snippet 'v2/components/search-input.html', ... %}` inside `<form>` |
| Header (SM) | `templates/v2/header.html` | Search icon button → `#search-offcanvas` (Bootstrap offcanvas) |

---

## 2. Data Sources

### Primary (MVP) — client-side index, no AJAX

| Type | Source | Entry fields |
|---|---|---|
| Organisation | `feature-index.js`, `type='organisation'` | `title` (name + acronym), `url` (org page) |
| Location | `feature-index.js`, `type='location'` | `title` (country name), `url` (group page) |

The index is already loaded on every page (part of `hdx_theme/search-scripts` asset bundle).
No network request needed during typing.

### AJAX endpoints (available, not used in MVP)

These exist if a live-data approach is ever preferred:

| Type | Endpoint | Returns |
|---|---|---|
| Organisation | `/api/2/util/organization/autocomplete?q=QUERY` | `[{id, name, title}]` |
| Location | `/api/2/util/group/autocomplete?q=QUERY` | `[{id, name, title}]` |

### Previous searches

- Exposed server-side as JSON in the old header: `<div id="previous-searches">…</div>`
- Used by `search.js` for the v1 dropdown
- Decision needed: whether v2 shows previous searches (see Open Questions §9.2)

### Excluded from MVP

- Dataset search suggestions (backlog)
- Trending suggestions (backlog)

> **Note:** Crisis/event entries (`type='event'`) from `feature-index.js` are **included** — the data
> already exists in the index; v2 does not filter them out (see Decision §9.9).

---

## 3. Component Architecture

### Reuse strategy

```
feature-index.js      ← shared data, already on page
minisearch.min.js     ← shared library, already on page
normalize.js          ← shared utility (toNormalForm), already on page
process_title()       ← copy or import the bold-highlighting helper
```

All three are bundled in `hdx_theme/search-scripts` and available globally.

### New JS module

A new vanilla-JS module (matching the v2 pattern: `dropdown.js`, `carousel.js`) should be
created, e.g. `v2/search-autocomplete.js`.

It should **not** modify `search.js` — old logic stays isolated.

### Snippet changes

The `c-autocomplete` snippet (`templates/v2/components/autocomplete.html`) needs a
`data-module` or `data-` attribute so JS can discover the element, e.g.:

```html
<div class="c-autocomplete" data-hdx-v2-search-autocomplete ...>
```

`show_panel` can remain `False` on initial render; JS opens/closes the panel at runtime.

The panel's results section needs `data-` attributes for JS to target:

- results container: `class="c-autocomplete__results"`
- individual result rows: `class="c-autocomplete__result-row"` with `data-href` and `data-type`

### Integration: homepage

`home/index.html` passes `form_action=h.url_for('dataset.search')` and
`search_source='in-page'` to the snippet. The `<form>` element is owned
by `autocomplete.html` via these params — callers must **not** wrap the snippet
in an outer form.

The form `action` for "View all results" must point to the dataset search:
`/search?q=QUERY&ext_search_source=in-page`

**MD/SM**: The homepage hero autocomplete also triggers the fullscreen overlay
(same as the header), so the overlay is included in `header.html` unconditionally
(all pages, not just non-homepage).

### Integration: header (XL/MD)

`header.html` currently wraps `c-search-input` in a `<form>`.
This needs to be upgraded to the full `c-autocomplete` component so the panel can be shown.
The form action: `/search?q=QUERY&ext_search_source=main-nav`

### Integration: header (SM)

The SM search icon currently targets `#search-offcanvas`.
See Open Question §9.5 for whether the autocomplete overlay integrates with this offcanvas
or is a separate mechanism.

---

## 4. Autocomplete Logic

### Query handling

1. Listen to `input` event on `.c-search-input input`
2. Trim and normalize: `toNormalForm(value.trim())`
3. If empty: close panel
4. If non-empty: run `performSearchQuery(value)` against the MiniSearch index
5. Filter results to `type='organisation'`, `type='location'`, or `type='event'` (all index types included)
6. Render up to **5 results total** across all types, ordered by MiniSearch relevance score
7. Show panel

### MiniSearch config

Reuse the same index config as v1:

```js
const index = new MiniSearch({
  fields: ['title', 'title_nf', 'extra_terms'],
  storeFields: ['title', 'url', 'type']
});
index.addAll(feature_index);  // all types included — organisations, locations, crises
```

### Bold highlighting

Reuse `process_title(title, termList)` from `search.js` (or an equivalent inline version):

```js
function processTitle(title, termList) {
  if (!termList || !termList.length) return title;
  const re = new RegExp(termList.join('|'), 'gi');
  return title.replace(re, '<strong>$&</strong>');
}
```

### Result item rendering

Each result row (inside `.c-autocomplete__results`), using the `v2/components/text-link.html`
snippet for the link (SSR) / mirroring its output in JS:

```html
<div class="c-autocomplete__result-row" data-href="URL" data-type="organisation|location">
  <div class="c-autocomplete__result-link">
    {% snippet 'v2/components/text-link.html',
        label=title, href=url, style='tertiary', size='m',
        extra_classes='c-autocomplete__result-label' %}
  </div>
  <span class="c-autocomplete__result-count">Organisation | Location</span>
</div>
```

Hover styling comes from `c-text-link`; `c-autocomplete__result-row` adds only the keyboard-focus
indicator (`aria-selected="true"`). The `.c-autocomplete__result-count` slot is repurposed as a type badge.

The suggestion panel is `position: absolute; top: 100%; z-index: 100` so it drops below the
input without affecting navbar layout.

### "View all results" button

- Already rendered as `.c-autocomplete__confirm-btn` (submit button in the snippet)
- Label: `"View all results"` (Figma: `search-autocomplete-md.html`)
- Style: tertiary, size m (already configured in snippet)
- Aligned right (already in LESS)
- On click: submits the form → navigates to `/search?q=QUERY&ext_search_source=…`

### Panel open/close

- **Open**: on input focus (if value non-empty) or on `input` event producing results
- **Close**: on `Escape`, on click outside `.c-autocomplete`, on blur (with mousedown guard)
- **Clear button**: clicking × clears input, hides panel, returns focus to input.
  Implemented via `show_clear=True` param in `search-input.html` which renders a custom
  `c-search-input__clear` button (`close.svg`). Native browser cancel button suppressed
  with CSS (`::-webkit-search-cancel-button`). Visibility controlled by `.c-search-input--filled`.
- `aria-expanded` on `.c-autocomplete` must be toggled (`true` / `false`)

---

## 5. Responsive Behavior

### XL (≥ 80rem / 1280px)

- `c-autocomplete` renders inline inside `.hdx-v2-navbar__search` (header) or `.hdx-v2-hero__search` (homepage)
- Panel drops below the input: absolute positioned, full width of the input
- Figma reference: `home-filled-search-bar-xl.html`

### MD (48rem – 79rem)

- Header `c-autocomplete` is visible in the navbar (`.hdx-v2-navbar__search`)
- Panel behaviour: **fullscreen overlay** (see Figma `search-autocomplete-md.html`)
  - Overlay covers entire viewport, z-index above navbar
  - Header area shows close icon (×)
  - Search input is at the top; results fill below
  - Footer: "Clear" + "View all results" buttons

### SM (< 48rem)

- Search input is hidden in navbar; only the search icon button is shown
- Tapping the icon opens the overlay
- Overlay matches `search-autocomplete-sm.html` Figma
- Reuse the overlay pattern from `hdx-v2-search-filter-overlay` (class + `--open` modifier,
  fixed positioning, z-index 1060, header / scrollable body / footer sections)

---

## 6. Interaction Model

### Keyboard

| Key | Behaviour |
|---|---|
| `ArrowDown` | Move focus to first result; subsequent presses move down the list |
| `ArrowUp` | Move focus up; from first result → returns focus to input |
| `Enter` on result | Navigate to `data-href` of focused result |
| `Enter` on input | Submit form → navigate to search page |
| `Escape` | Close panel; return focus to input |
| `Tab` | Close panel (natural blur) |

ARIA: the active result row should receive `aria-selected="true"`; `.c-autocomplete__panel`
has `role="listbox"`, result rows should have `role="option"`.

### Mouse / touch

- Hover on result row → highlight state
- Click on result row → navigate to `data-href`
- Click outside `.c-autocomplete` → close panel
- Click clear (×) icon → clear input value, hide panel, return focus to input

### Focus states

- Input focus → if value non-empty, show panel
- Input focus → if empty, do NOT show panel (trending suggestions are out of scope)
- Panel open → `aria-expanded="true"` on `.c-autocomplete`
- Panel closed → `aria-expanded="false"`

### Clear (×) button

- Visible when input is in `filled` state (value non-empty)
- Matches Figma `home-filled-search-bar-xl.html` exactly
- LESS already handles `.c-search-input--filled` state; confirm the clear icon is rendered
  by the snippet (check `search-input.html` for close icon slot)

---

## 7. Edge Cases

| Scenario | Expected behaviour |
|---|---|
| No results match query | Show panel with "No results found" message (no result rows, confirm button still present) |
| Query is whitespace only | Treat as empty; close panel |
| Special characters (`<`, `>`, `&`, `"`) | Sanitize before inserting into DOM (reuse `hdxUtil.text.sanitize()`) |
| Very long title in result | Truncate with CSS (`overflow: hidden; text-overflow: ellipsis; white-space: nowrap`) |
| Very long query string | Cap query length at 200 chars before passing to MiniSearch |
| index not yet loaded | Guard: skip autocomplete if `typeof feature_index === 'undefined'` |
| Multiple `c-autocomplete` instances on same page | Each instance operates independently; JS must scope event listeners to the specific element |
| Input cleared with keyboard (`Ctrl+A` + `Delete`) | `input` event fires; panel closes |
| Rapid typing | Client-side MiniSearch is synchronous — no debounce needed; re-render on every `input` event |

---

## 8. Constraints

1. **Reuse v1 data and libraries** — `feature-index.js`, `minisearch.min.js`, `normalize.js`
   are already loaded; do not duplicate or re-fetch them
2. **Keep v1 unchanged** — `search_/search.js` and `.search-ahead` in `header-mobile.html`
   must not be modified; v1 and v2 coexist in the same page load
3. **No new backend logic** — all suggestions served from the existing client-side index
4. **ONE implementation** — a single JS module handles both homepage and header; no duplication
5. **No AJAX for MVP** — suggestions come from the pre-built index, not live API calls
6. **All index types included** — organisations, locations, and crises (`type='event'`) are all searchable; no filtering by type
7. **Preserve analytics** — `hdxUtil.analytics.sendTopBarSearchEvents(searchTerm, resultType)`
   must fire on result click; the `ext_search_source` parameter must be appended to all
   navigation URLs
8. **v2 gate** — all changes inside `{% if v2 %}` blocks or in v2-specific JS/LESS files

---

## 9. Decisions Taken

### 9.1 Data source — index vs AJAX

The v1 uses client-side `feature-index.js` (pre-built, loaded once, instant results but
potentially stale). An alternative is live AJAX via `/api/2/util/organization/autocomplete`
and `/api/2/util/group/autocomplete` (always current but requires debounce + loading state).

**Decision:** Reuse the **client-side index** (`feature-index.js` + MiniSearch), matching v1
behaviour exactly. No AJAX for MVP.

### 9.2 Result count and previous searches

**Decision A:** **5 results total** across all types (not 5 per type).

**Decision B:** **Drop previous searches.** The v2 panel does not show a previous-searches section.

### 9.3 Result ordering

**Decision:** **Relevance score only** — use MiniSearch's default ranking. No manual ordering
by type (location before organisation, etc.).

### 9.4 Header search upgrade

**Decision:** **Yes — upgrade the header.** The same `c-autocomplete` snippet is used for both
the homepage hero and the header navbar. Keep the existing visual design; only adjust styles
where the Figma exports require a change.

### 9.5 SM mobile overlay

**Decision:** **No Bootstrap offcanvas.** The SM autocomplete overlay must match the
`hdx-v2-search-filter-overlay` pattern (fixed positioning, z-index 1060, header / scrollable
body / footer sections, `--open` modifier) — the same approach used for the filter overlay on
the search results page. The existing `#search-offcanvas` should be bypassed / removed for v2.

### 9.6 URL navigation on result click

**Decision:** Navigate to the **entity's own page** (e.g. `/organization/unhcr`,
`/group/afg`) — the URL already stored in `feature-index.js`. This matches v1 behaviour.
Implementation must verify against the v1 `search.js` to confirm the exact URL format used.

### 9.7 New Mixpanel / analytics events

**Decision:** **Full parity with v1.** Fire `hdxUtil.analytics.sendTopBarSearchEvents(searchTerm, resultType)`
on result click, exactly as the old implementation does. No new events; no change to properties.

### 9.8 JS module architecture

**Decision:** **New vanilla JS module** — plain ES6 IIFE or class, no jQuery, matching the v2
pattern (`dropdown.js`, `carousel.js`). Do not extend `ckan.module`.

### 9.9 Crisis autocomplete

**Decision:** **Include crisis entries.** Since `type='event'` entries are already present in
`feature-index.js`, v2 does not filter them out — they are searchable alongside organisations
and locations. No additional backend work required.

---

## Figma Sources

| File | Breakpoint | Shows |
|---|---|---|
| `home-active-search-bar-xl.html` | XL | Empty/focused state (trending — out of scope for MVP) |
| `home-filled-search-bar-xl.html` | XL | Typing state with results + type badges + "View all results" |
| `search-autocomplete-md.html` | MD | Full-screen overlay with search + results |
| `search-autocomplete-sm.html` | SM | Full-screen overlay, compact spacing |
