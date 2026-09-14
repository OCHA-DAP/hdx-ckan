# Data Visualization Gallery (v2 Migration)

**Scope:** The `/dataviz-gallery` route only (`hdx_dataviz_gallery` blueprint, `ckanext-hdx_dataviz`
extension). UI migration only — no backend/API changes, no filtering-logic changes.

---

## Context

The originating brief assumed the existing gallery page has working filters, hover-revealed card
actions, and existing analytics that all need to be "preserved" during a straightforward UI migration.
Auditing the live code and the three Figma exports (`xl-dataviz-gallery.html`,
`md-dataviz-gallery.html`, `sm-dataviz-gallery.html`) surfaced several mismatches between that framing
and reality — the same failure mode already documented in `066-archived-dataviz-v2.md`, where the
brief's assumptions didn't match the actual page:

- The v1 template has its facet-rendering snippet **commented out** — there are no working filters
  today, despite the backend (`DatavizSearchLogic`, inherited from the shared `SearchLogic`) computing
  a full facet set that is simply never rendered.
- Figma's MD/SM exports show a "Filter (10)" button; the XL export hides all filter-related markup
  (`display:none`) entirely. Neither is backed by a real, working feature in the live page.
- The Figma card has no "Explore" button and no "Edit Showcase" link, while the current v1 card has
  both (revealed on hover) — "Edit Showcase" gated to sysadmins.
- No analytics tracking exists on this page today at all (search/sort/pagination/card-click) — the
  shared GA search-tracking hook depends on form IDs this page has never had.

These were resolved directly with the user before finalizing this doc — see Decisions below.

---

## Decisions Taken

- **D1 — Filters (confirmed): none in v2.** There is nothing working to preserve, so v2 migrates only
  what functions in v1 today: search bar, results-per-page, and sort-by. Figma's "Filter (10)"
  button/badge (MD/SM) and the hidden filter-chip row (XL) are dropped entirely — not built now, not
  stubbed as a placeholder. Reuse the pattern already established on other v2 pages that expose this
  same reduced control set (search-nav-controls without a facet sidebar/overlay).
- **D2 — Card interaction (confirmed): independent image/title links + edit link, no outer card
  anchor.** The image and the title are each their own `<a>`, pointing to the "Explore" target
  (`dataviz.url`, opens in a new tab — matching v1's Explore button behavior) — even though Figma's
  static export shows no button and no hover state at all. A small text-only "Edit" affordance is
  shown only when `h.has_dataviz_gallery_permission()` is true, linking to `showcase_blueprint.edit`
  — styled after the existing per-field quick-edit link (`hdx-quick-edit.js`/`c-text-link`,
  `style='primary'`, on the dataset metadata section), not the page-header pencil-icon "Edit Dataset"
  button — and placed in the card's metadata footer next to "Updated on {date}" and the "DATA" link
  (also `c-text-link`, `style='primary'`). The card itself stays a plain `<div>`, not a wrapping `<a>`:
  with three independent link targets (Explore, DATA, Edit) a single outer anchor would mean nesting
  `<a>` inside `<a>`, which is invalid HTML. That makes `c-showcase-card` (also multi-target, also a
  `<div>`) the closer structural precedent here, not `c-highlight-card` (which has exactly one link
  target for the whole card, so wrapping it in a single outer `<a>` never runs into this problem). No
  `hdx_click_stopper` is used on the DATA/Edit links: it's a GA-analytics module (fires
  `sendLinkClickEvent`, then delays navigation), not a click-propagation guard, and wiring it in would
  add tracking this page doesn't have today — a direct contradiction of D3.
- **D3 — Analytics (confirmed): add none.** No GA/Mixpanel tracking exists on this page today —
  confirmed via repo search: the shared `setUpSearchTracking()` hook only fires for
  `#search-page-filters-form` / `#dataset-filter-form` / `#showcaseSection form`, none of which exist
  in `dataviz/index.html`, and `dataviz_item.html` never outputs the `hdx_analytics` payload the
  backend computes for every result. Strict parity with v1 — matching the precedent already set in
  `066-archived-dataviz-v2.md` (D4) and `065-advanced-filters-v2.md`.
- **D4 — Search/sort/page-size reuse (confirmed):** Reuse `templates/v2/search-nav-controls.html`
  (already parameterized and shared by the main search page and the org-members tab) for the
  results-per-page and sort-by dropdowns. Restyle — do not functionally alter — the search input using
  the existing v2 search-bar visual pattern. Keep v1's exact existing sort option set and their exact
  existing labels (Last Modified, Last Added, Relevance, Name Asc/Desc, Trending, Most Downloads) —
  Figma's shown default label ("Last added") is not adopted. Change the results-per-page values from
  v1's **9/18/27** to **12/24/36** (new default 12, matching Figma's displayed default) — confirmed
  safe: `SearchLogic._search()` casts `ext_page_size` to `int` with no whitelist/min/max check
  (`ckanext-hdx_search/controller_logic/search_logic.py`), and the `[9, 18, 27]` list is a plain Jinja
  literal in `dataviz/index.html`, not a backend-enforced set — so this is a template-only change, still
  multiples of 3 for the 3-column grid (D6). Keep the exact existing backend query param names (`q`,
  `sort`, `ext_page_size`, `page`) and the exact existing behavior: full-page GET reload on every change,
  no AJAX, no autocomplete.
- **D5 — Figma artifacts (resolved during drafting):** The following are Figma component-library
  leftovers, not intended design — same failure mode as `066-archived-dataviz-v2.md`'s D5 — and are
  omitted:
  - The hidden (`display:none`) "Datasets 293" secondary counter next to the "Dataviz Gallery 57"
    title, present on every breakpoint.
  - The XL export's hidden filter-chip row (`wrapper5` / `selection-item`).
  - The non-functional carousel dot/arrow scaffolding wrapping each row of 2-3 cards
    (`frame-wrapper`/`frame-child`/`frame-item`, `dataviz-carousel-inner`, all `display:none`), and the
    "carousel" grouping of cards into sub-rows itself — replaced by a single flat, responsive grid (no
    sub-carousels, no dots/arrows, no per-row overflow-x scroll container).
  - SM's duplicate/hidden second pagination block and its stray hidden "You might also like" section
    (`.signals { display:none }`) with 4 empty placeholder cards.
  - The hidden `.search-autocomplete` slot positioned next to the in-page search box on XL/MD — an
    apparent copy from the site's global header autocomplete component, not a feature this page has
    ever had.
- **D6 — Grid layout (default, low-risk):** 1 column at SM, 2 columns at MD, 3 columns at XL —
  extending the existing `c-showcase-card-grid` LESS pattern (currently 1→2 col) with an added 3-col
  rule at XL. This aligns with v1's 9/18/27 page-size options (all multiples of 3).
- **D7 — Hero carousel (confirmed): dropped.** v1's rotating hero banner (`_fetch_carousel_items()`,
  `dataset_type:showcase extras_in_carousel_section:true`) is out of scope for v2 — a real, working
  feature, unlike the filters, but absent from all three Figma exports. `views/dataviz.py` still
  carries the now-dead fetch/populate code, left for a later cleanup pass.

---

## 1. Existing Implementation Audit

### 1.1 Route, controller, template

- Route `GET /dataviz-gallery/` — Flask blueprint `hdx_dataviz_gallery`, registered in
  `ckanext-hdx_dataviz/ckanext/hdx_dataviz/views/dataviz.py` (`url_prefix='/dataviz-gallery'`).
- `index()` renders `dataviz/index.html` via `DatavizSearchLogic`
  (`ckanext-hdx_dataviz/ckanext/hdx_dataviz/controller_logic/dataviz_search_logic.py`), which subclasses
  the shared `SearchLogic` (`ckanext-hdx_search`) with package_type `showcase`, restricted via
  `additional_fq='in_dataviz_gallery:true'`, default sort `metadata_modified desc`, `num_of_items=9`. A
  separate hero carousel is fetched via `_fetch_carousel_items` (`dataset_type:showcase
  extras_in_carousel_section:true`) — unrelated to the card grid below it, dropped in v2 (D7).
- Template: `ckanext-hdx_theme/ckanext/hdx_theme/templates/dataviz/index.html`, extends
  `page_light.html` (v1/Bootstrap).
- This is a distinct feature from the `/archive` page covered by `066-archived-dataviz-v2.md` and from
  the dataset search page's `ext_archived` toggle covered by `065-advanced-filters-v2.md` — no shared
  code or data between them beyond the common `SearchLogic` base class.

### 1.2 Search

- Plain **GET query param `q`**, read server-side in `SearchLogic._search()`, sent to Solr via
  `package_search`.
- UI: `#headerSearch` input (plus a mobile twin `#headerSearchMobile`). No AJAX, no debounce, no
  autocomplete on this page — `datasets/list-header.js` binds `keydown` (Enter) to build a new URL and
  does a full `window.location` reload.

### 1.3 Filters — confirmed non-functional today

- `SearchLogic` builds a full facet dataset (organizations, groups, formats, licenses, tags, "featured"
  facets) that is available to every page using it, but `dataviz/index.html` never renders it: the
  `{% snippet 'search/snippets/package_search_facets.html' ... %}` call is commented out (both in the
  main body and inside the `.mobile-facets` div behind the "Filters [n]" toggle button). The only
  working controls on the page today are search, sort, and page-size.

### 1.4 Sort & page-size

- **Sort**: `search/snippets/package_search_order.html` (Last Modified, Last Added, Relevance, Name
  Asc/Desc, Trending, Most Downloads), handled by `order-by-dropdown.js` — click →
  `replaceParam('sort', value)` → full-page reload, resets `page` to 1.
- **Page size**: radio inputs `ext_page_size` = 9/18/27 (class `filter-pagination`), handled in
  `datasets/list-header.js` → full-page reload with `ext_page_size` in the URL. Backend reads it via
  `int(request.args.get('ext_page_size', num_of_items))` in `SearchLogic._search`.

### 1.5 Card

- Partial: `dataviz/dataviz_item.html`. Fields: `image_display_url` (preview image),
  `dataviz_label`/`title`, `notes` (description), `metadata_modified` ("Updated on ..."), `data_url`
  ("DATA" link, defaulted server-side to `showcase_blueprint.read` if not set on the showcase).
  Actions overlay: "Explore" button (`dataviz.url`, opens in a new tab) and, only
  `if h.has_dataviz_gallery_permission()`, an "Edit Showcase" link to `showcase_blueprint.edit`. Hover
  interaction is pure CSS — `.dataviz-item:hover .preview .actions { display:flex }` — the actions
  overlay is `display:none` by default.

### 1.6 Pagination

- `{{ data.page.pager(q=data.q) }}`, where `data.page` is CKAN core's `Page` (webhelpers-derived
  paginator, `ckan/lib/pagination.py`) — no HDX-specific pagination component involved.

### 1.7 Analytics — confirmed absent

- The shared `setUpSearchTracking()` (`fanstatic/google-analytics.js`) only fires if it finds
  `#search-page-filters-form`, `#dataset-filter-form`, or `#showcaseSection form` — none exist in
  `dataviz/index.html`.
- `SearchLogic` populates `dataset['hdx_analytics']` for every result (including showcases), but
  `dataviz_item.html` never reads or outputs it — no per-card click tracking exists.
- The only analytics present is the site-wide GTM pageview snippet in `base.html`, which fires on every
  page load regardless of content.

---

## 2. Figma Mapping

Files: `xl-dataviz-gallery.html`, `md-dataviz-gallery.html`, `sm-dataviz-gallery.html`
(`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`).

**Layout (consistent across breakpoints):** top-bar → navbar → breadcrumb (Home / Products / Dataviz
Gallery) → header (title + count, search, results-per-page, sort-by) → card grid → classic numbered
pagination → footer.

- **XL**: title "Dataviz Gallery" + count "57", inline search box, results-per-page ("12") and sort-by
  ("Last added") dropdowns in one row. No visible filter UI at all (see D1/D5). Cards are 384px fixed
  width, grouped in rows of 3 inside an `overflow-x: auto` strip with hidden carousel dots/arrows (D5)
  — treated as an artifact; the real layout is a 3-column grid (D6).
- **MD**: same header content, plus a visible "Filter (10)" button (dropped per D1). Cards render 2 per
  row, flexibly sized.
- **SM**: title + count ("200" in this export — a data mismatch with XL/MD's "57", itself a Figma
  placeholder inconsistency, not a design decision), a "Filter (10)" button (dropped per D1), then a
  stacked control row (results-per-page, sort-by, and an inline "Search Dataviz" box — confirmed by
  direct read of the export, not merely a search icon toggle). Cards render as a flat single column.
  Two pagination blocks appear (one `display:none`) plus a hidden "You might also like" block with 4
  empty cards — both artifacts (D5).
- **Card** (`.dataviz-gallery-card`): full-width thumbnail image (10rem/160px tall, `object-fit:
  cover`), bold single-line-truncated title, 3-line-clamped description, and a metadata footer —
  "Updated on {date}" plus a "DATA" link (external, `target="_blank"`, to the linked org's page on
  `data.humdata.org`). No badges, no org logo, no visible hover state, no Explore/Edit-Showcase controls
  anywhere in the static export (see D2).
- No `c-`-prefixed class names appear anywhere in these three exports (unlike `resource-card.html` or
  `highlight-card.html`), confirming the card needs to be newly authored following existing BEM
  conventions rather than lifted from the export markup.

---

## 3. Card Component Strategy

New `c-dataviz-card` component, structurally close to the existing `c-showcase-card`
(`v2/components/showcase-card.html`/`.less` — thumbnail + title + clamped description + actions,
already used for related showcases on the dataset page):

- Thumbnail image (fixed height, `object-fit: cover`).
- Title (single-line truncate).
- Description (3-line clamp, matching Figma and reusing the same clamped-text approach already used by
  `resource-card.html`).
- Metadata footer: "Updated on {date}" + "DATA" external link.
- The image and title are each their own `<a>` per D2, pointing to the Explore target, opening in a
  new tab. The card itself is a `<div>`, not a wrapping anchor.
- A small text-only "Edit" link, rendered only for permitted sysadmins, sits in the card's metadata
  footer row alongside "Updated on {date}" and the "DATA" link — following the existing per-field
  quick-edit link style (`c-text-link`, no icon) already used on the dataset page's metadata section,
  not the page-header pencil-icon "Edit Dataset" button. No click-stopper module is needed (§D2) — there's no outer card anchor for it to conflict with.
- Grid: `c-dataviz-card-grid`, following `c-showcase-card-grid`'s LESS pattern extended with a
  3-column rule at XL per D6 — its own class, not a shared one (component wrapper ownership).

---

## 4. Search & Filters Integration

- Search remains a plain GET `q` param, full-page-reload input — restyled to the v2 search-bar visual
  pattern, not functionally changed. No autocomplete, no AJAX, no debounce (D4).
- No filters at all (D1) — no facet sidebar, no fullscreen overlay, no "Filter" trigger button on any
  breakpoint.
- All state (search term, sort, page size, page number) continues to live entirely in URL query params
  (`q`, `sort`, `ext_page_size`, `page`), exactly as today. No new client-side state, no change to
  `DatavizSearchLogic`/`SearchLogic`.

---

## 5. Component Strategy

### Reuse as-is

| Component | Usage |
|---|---|
| `v2/search-nav-controls.html` | Results-per-page + sort-by dropdowns (already used by the search page and org-members tab) |
| `v2/components/pagination.html` (`c-pagination`) | Bottom pagination |

### Extend only if needed

- New `c-dataviz-card` component (§3), including its own `c-dataviz-card-grid` wrapper (§D6) — no
  existing card matches this exact field set (thumbnail + title + clamped description +
  date/DATA-link footer + independent image/title links + gated edit link).
- A small page-owned LESS partial for the title+count+search+controls header row, following the same
  "page owns its own one-off BEM header block" precedent already used in
  `066-archived-dataviz-v2.md` rather than introducing a new shared component for a single-use header
  shape.

### Do not

- Do not build a filter sidebar, overlay, or chip row (D1).
- Do not add autocomplete/AJAX search behavior (D4).
- Do not add new analytics instrumentation (D3).
- Do not change `DatavizSearchLogic`/`SearchLogic` or any backend filtering/search logic.

---

## 6. Responsive Strategy

- **XL**: 3-column card grid; single header row (title + count, search, results-per-page, sort-by); no
  filter UI.
- **MD**: 2-column card grid; header wraps per Figma (title+count row, then search, then
  results-per-page/sort-by); no filter UI.
- **SM**: 1-column card grid; controls stack (title+count row, then results-per-page, sort-by, and
  search in a stacked column); single pagination block at the bottom only — the duplicate pagination
  block and "You might also like" section are dropped (D5).

---

## 7. Risks

- **Search/param regression** ❗ — must preserve exact query param names (`q`, `sort`, `ext_page_size`,
  `page`) and full-page-reload behavior; any drift breaks bookmarked/shared URLs.
- **Sort/page-size value mismatch** ❗ — must keep v1's exact sort option values, and must update
  page-size to exactly **12/24/36** (D4) — a template-only Jinja literal change, not a backend
  whitelist — or the header row will drift from what `dataviz/index.html` actually sends.
- **Reduced click target vs Figma intent** — only the image and title are clickable to Explore;
  clicking the description text or footer whitespace does nothing. Accepted per D2, since a true
  whole-card anchor isn't valid HTML with three independent link targets on this card.
- **Layout drift from removing Figma's carousel scaffolding** ❗ — replacing the "carousel" grouping
  with a flat grid (D5/D6) is a deliberate structural deviation from the literal export; needs visual
  QA against Figma's actual card sizing/spacing, not its row-grouping mechanics.
- **Analytics non-regression** ❗ — D3 means adding nothing; care must be taken not to accidentally
  introduce duplicate GTM firing or an analytics hook that doesn't belong on this page.
- **Permission leak on the edit link** ❗ — must gate strictly on `h.has_dataviz_gallery_permission()`,
  matching v1's existing check exactly.

---

## 8. Edge Cases

- No results: existing empty-state behavior from `SearchLogic`/`dataviz/index.html` should be
  preserved, restyled to v2.
- Many results: handled by existing pagination, no change.
- Long titles: single-line truncate (ellipsis) per Figma.
- Long descriptions: 3-line clamp per Figma.
- Card with no permission for edit: edit link must not render at all (not just hidden via CSS).
- Showcase with no external URL: image/title render as non-interactive elements instead of a link
  (previously rendered `href=""`, opening a new tab to nowhere).
- Slow responses: no skeleton/loading state exists in v1; none is added.
- Rapid search/sort/page-size changes: not a concern — every change is a full-page reload, no
  debouncing needed (matches today's behavior).
