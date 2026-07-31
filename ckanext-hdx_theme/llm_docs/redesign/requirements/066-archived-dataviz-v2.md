# Archived Dataviz Page (v2 Migration)

**Scope:** The `/archive` route only (`hdx_archived_quick_links` blueprint). UI/UX redesign only —
the underlying data assembly (`archived_quick_links_custom_settings.py`) is unchanged.

---

## Context

The originating brief for this task was framed around an "Archived Data Visualization view,"
assuming a page that renders charts/maps and must preserve visualization logic, rendering approach,
and analytics during a v2 migration. Investigation of the three Figma exports
(`xl-archived-dataviz.html`, `md-archived-dataviz.html`, `sm-archived-dataviz.html`) and the live
codebase shows that framing does not match reality: **this page contains no visualization of any
kind.** It renders a title, a count badge, and a flat list of divided rows — each just a text label
and an external-link icon — linking out to other pages (mostly archived crisis/event pages). This is
an exact match, down to the page title string, for the existing live v1 page at `/archive`, which
today is a plain, unstyled version of the same list.

This document therefore describes a v2 UI migration of that existing page, not a
visualization-preservation task, per the decisions below (confirmed with the user during
requirements drafting).

---

## Decisions

- **D1 — Scope reframe (confirmed):** This is a v2 UI migration of the existing `/archive` page
  (`hdx_archived_quick_links` blueprint), not a chart/visualization feature. The originating brief's
  visualization-preservation constraints are satisfied vacuously — there is nothing of that kind on
  this page to preserve or break.
- **D2 — Breadcrumb label (confirmed):** Use **"Archived Dataviz"**, matching the page's own
  title/heading exactly. The Figma exports' literal breadcrumb text ("Dataviz Gallery," identical
  across all three breakpoints) is a copy-paste artifact from reusing the sibling Dataviz Gallery
  page's Figma component, not intended content — the footer nav in the same exports lists "Archived"
  and "Dataviz gallery" as two distinct sibling links, confirming they are different pages.
- **D3 — Sidebar content (confirmed):** Drop both the v1 sidebar description ("The list includes
  archived humanitarian crisis pages...") and the generic FAQ "contact us" widget entirely, matching
  Figma's full-width, no-sidebar layout across XL/MD/SM. This is a deliberate content removal, not
  an oversight (see Risks).
- **D4 — Analytics (confirmed):** No tracking exists on this page today — no GA/Mixpanel anywhere in
  `archived_quick_links/*`. Add none in v2 either; strict parity with v1, matching the same
  reasoning already used for decision D3 in `065-advanced-filters-v2.md`.
- **D5 — Figma artifacts (resolved during drafting):** The exports' hidden (`display:none` in the
  exported CSS) "Datasets 293" sub-header, search box, sort dropdown, and filter-pill row are
  leftovers from a copy-pasted search-results Figma component — not part of the intended design.
  Omitted; the real page has no search/sort/pagination need (a small, fixed, admin-curated list,
  matching v1 behavior exactly). The SM export's stray "You might also like" text is similarly an
  artifact — it appears nowhere else and has no v1 equivalent — omitted.
- **D6 — No v1 fallback gate (resolved during drafting):** Per the `048-locations-list-v2.md`
  precedent, `main.html` is replaced outright — no `{% if v2 %}` branch, no Python-side toggle.
  `archived_quick_links_custom_settings.py::show()` needs no code changes; only the template becomes
  a full `v2/page.html` extension.
- **D7 — Empty state (confirmed):** If `archived_items_list` is empty, still render the title band
  with count "0," and show a short centered empty-state message ("No archived items found.") in
  place of the row list rather than rendering nothing.
- **D8 — Long titles (confirmed):** Row titles wrap onto a second line rather than truncating with
  an ellipsis. Matches Figma (no ellipsis/truncation markup in the exports) and needs no CSS
  truncation added to `text-button.html`, which has none today.
- **D9 — Pagination (confirmed):** Out of scope, no action for this migration. Revisit only if the
  list grows significantly in the future.

---

## 1. Existing Implementation Audit

### 1.1 Route and view logic

- Route `/archive`, blueprint `hdx_archived_quick_links`, registered in
  `ckanext-hdx_theme/ckanext/hdx_theme/plugin.py:412`.
- `ckanext-hdx_theme/ckanext/hdx_theme/views/archived_quick_links_custom_settings.py::show()`
  builds `archived_items_list` from two sources, concatenated:
  - `_prepare_archived_viz_list(viz_list)` — Quick Links settings entries (action
    `hdx_quick_links_settings_show`) where `viz.get('archived', False)` is true, admin-managed via
    `templates/admin/quick_links.html`. Each item: `{id, title, url}`.
  - `_prepare_archived_page_list(page_list)` — CMS pages (action `page_list`) with
    `status == 'archived'`. Each item: `{id, title, url: "/{page_type}/{page_name}"}`.
- No pagination, search, or sort exists in the backend — a single flat, unsorted, uncounted (in the
  UI) list.

### 1.2 Template structure (v1, current)

- `templates/archived_quick_links/main.html` extends `page.html` (v1 two-column layout with a
  sidebar).
- `subtitle` block is literally `_("Archived Dataviz")` — an exact string match to the Figma
  heading text.
- Breadcrumb via `snippets/active_breadcrumb_item.html`, `title=_('Archived Dataviz')`.
- `pre_primary` block renders a title band (`top-banner-archive`).
- `primary` block is effectively empty (one commented-out leftover `div`), and includes
  `archived_quick_links/questions_sections.html` for the actual row list.
- `secondary` block holds the sidebar copy ("The list includes archived humanitarian crisis
  pages... Country pages that were displayed under Quick Links can be found [here](/group)") plus a
  generic FAQ "contact us" widget (`closeCurrentWidget`/`spawnRecaptcha`/`showFaqWidget`, shared
  with other FAQ-style content pages) — dropped per D3.

### 1.3 Row rendering

- `templates/archived_quick_links/questions_sections.html` loops `data.viz_list` and renders each
  item as:
  ```html
  <a role="button" href="{{viz.url}}" class="faq-question-link">
    {{ viz.title | safe }} <i class="icon humanitarianicons-Out-of-platform"></i>
  </a>
  ```
  inside a `.card`/`.card-header` wrapper borrowed from the FAQ accordion component. There is no
  actual expand/collapse behavior — each row is a static outbound link, not a real accordion, despite
  the borrowed CSS/JS scaffolding.

### 1.4 Visualization and analytics — confirmed absent

- No charting library (Chart.js, D3, or otherwise), no map/GIS rendering, and no client-side data
  fetching exists anywhere in `archived_quick_links/*`. Confirmed via repo-wide search: `grep -rl
  "archived"` inside the resource-preview extensions (`ckanext-hdx_office_preview`,
  `ckanext-hdx_hxl_preview`) returns no hits, and no chart/map JS references this page's templates
  or view.
- No GA/Mixpanel tracking exists on this page today — no `ga-*` classes, no `dataLayer.push`, no
  `mixpanel.track` calls anywhere in `archived_quick_links/*`.

### 1.5 Disambiguation — three unrelated "archived"/"dataviz" features

To prevent conflation in any future read of this doc:

- **Dataviz Gallery** (`ckanext-hdx_dataviz`, route `/dataviz-gallery`, template
  `templates/dataviz/index.html` + `dataviz/dataviz_item.html`) — a separate carousel + card
  showcase of external visualization tools (`in_dataviz_gallery` flag). Listed as a sibling footer
  nav link to "Archived," but otherwise unrelated code and unrelated data.
- **Dataset search's "Archived datasets" toggle** (`ext_archived=1` query param on `/dataset`,
  covered by `065-advanced-filters-v2.md`) — a dataset-level Solr filter toggle, powered by
  `ArchivedUrlHelper` in `ckanext-hdx_search`. Entirely different backend, entirely different concept
  of "archived" (a dataset metadata flag, not an admin-curated link list).
- **The repo's actual data-visualization code** — Data Explorer / CSV preview
  (`ckanext-hdx_office_preview`, DataTables-based table, not a chart), Quick Charts
  (`ckanext-hdx_hxl_preview`, a cross-origin iframe to an external app — no chart code lives in this
  repo), and the GIS/shape map preview (`ckanext-hdx_theme/.../fanstatic/shape-view.js`, MapLibre GL
  JS). None of this is touched by, or relevant to, the `/archive` page.

---

## 2. Figma Mapping

Files: `xl-archived-dataviz.html`, `md-archived-dataviz.html`, `sm-archived-dataviz.html`
(`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`).

Consistent structure across all three breakpoints:

1. Top bar / navbar (shared site chrome, already implemented elsewhere).
2. Breadcrumb: Home / Products / **"Archived Dataviz"** (per D2).
3. Page title "Archived Dataviz" with a count badge — "8" in the export sample.
4. A flat list of 8 divided rows, each a text label + external-link icon. Two of the eight carry
   real hrefs in the export (`https://data.humdata.org/event/libya-floods`,
   `.../event/morocco-earthquake`, `.../event/turkiye-syria-earthquakes`) — the rest are placeholder
   labels only (`Myanmar Earthquake`, `Lebanon Crisis`, `Horn of Africa Drought Data Explorer`,
   `Ukraine Data Explorer`, `Rohingya Refugee Crisis`).
5. Footer (shared site chrome, already implemented elsewhere).

No sidebar column exists in any breakpoint — a full-width, single-column layout throughout.

Confirmed Figma export artifacts, omitted per D5 (present in the markup/CSS but `display:none`, or
otherwise inconsistent with both the live v1 page and the rest of the export set):

- A secondary "Datasets 293" sub-header, search box, "Results per page" / "Sort by" dropdowns, and a
  filter-pill row — leftover from a copy-pasted search-results Figma component.
- The SM export's stray "You might also like" text, which appears nowhere else.

Responsive differences between breakpoints are container-only (padding, max-width, single- vs.
multi-column outer chrome) — no structural change to the row list itself.

---

## 3. Link-List Analysis

*(In place of the originating brief's "Visualization Analysis" section — there is no visualization
to analyze; see D1.)*

### Current implementation

A static list of outbound links, rendered via borrowed FAQ-accordion CSS with no actual
expand/collapse behavior (§1.3).

### Redesign mapping — reuse existing v2 components, no new ones

- **Each row** → `v2/components/text-button.html`:
  ```jinja2
  {% snippet 'v2/components/text-button.html',
      style='tertiary', size='m', label=item.title,
      icon=True, icon_position='right', icon_src='v2/icons/link-external.svg',
      tag='a', href=item.url, attrs={'target': '_blank'},
      extra_classes='hdx-v2-archived-dataviz__row' %}
  ```
  This is the same pattern already used for outbound links in `v2/components/page-header.html`. The
  `extra_classes` param drives row vertical padding in `archived-dataviz-page.less`.
- **Divider between rows** → `<hr class="c-divider">` between non-last items, matching the loop
  pattern already used in `v2/location-datagrid-drawer.html`:
  ```jinja2
  {% for item in archived_items_list %}
    {{ row markup }}
    {% if not loop.last %}<hr class="c-divider">{% endif %}
  {% endfor %}
  ```
- **Title + count** → `<h1 class="hdx-v2-archived-dataviz__title">` + `<span class="hdx-v2-archived-dataviz__count">`,
  sized to match `hdx-v2-list-header__title`/`__count` from `search/snippets/package_list.html`
  (`.hdx-display-l()` + responsive overrides, `.hdx-body-m()`). Count is computed server-side as
  `len(archived_items_list)` — same data, simply now rendered (v1 shows no count today).

---

## 4. Archived Context Strategy

"Archived" in this feature means an admin-flagged Quick Links entry (`viz.archived == True`) or a
CMS page with `status == 'archived'` — a manually curated list, unrelated to the dataset-search
`ext_archived` toggle (§1.5). There is no integration point between the two, and none is introduced.

No changes to `_prepare_archived_viz_list()`, `_prepare_archived_page_list()`, or `show()` —
strictly a template-layer migration.

---

## 5. Component Strategy

### Reuse as-is

| Component | Usage |
|---|---|
| `v2/page.html` | Base template, using the no-sidebar pattern already established by `organization/index.html` / `package/request_access.html`: set `content_class` only, leave `{% block secondary %}` empty, and override `{% block primary %}` directly (bypassing the legacy `<article class="module">` wrapper), per `CONVENTIONS.md`'s single-column-page guidance. |
| `v2/components/breadcrumb.html` | `items=[{'label': _('Products'), 'href': ''}, {'label': _('Archived Dataviz'), 'href': ''}]` |
| `v2/components/text-button.html` | Each outbound link row (§3) |
| `c-divider` (`divider.less`) | Row separators |
| `v2/icons/link-external.svg` | Row icon |

### Extend only if needed

- A small page-specific LESS partial for the title+count header and row-list spacing, following the
  precedent that each page owns its own small BEM classes for this kind of one-off header block
  (`hdx-v2-list-header`-style) rather than introducing a new shared `c-*` component for a
  single-use pattern. `hdx_theme/v2-archived-dataviz-page-styles` → `less/v2/archived-dataviz-page.less`,
  registered in `webassets.yml` — styles only, no scripts bundle (page has no interactive behavior).

### Do not

- Do not introduce a new visualization system or component — none exists to replace (D1).
- Do not keep a `{% if v2 %}` fallback branch — full replacement per D6.

---

## 6. Responsive Strategy

- **XL**: full padded width, matching the Figma container sizing already used elsewhere.
- **MD / SM**: single-column, tighter padding, matching Figma. No reflow or resize concerns — this
  is one column of simple text rows, not a grid or chart that needs recalculation at different
  widths.

---

## 7. Risks

- **Visualization / analytics / data-mismatch risk**: none — none of those subsystems exist on this
  page, before or after the migration.
- **Content-loss risk**: D3 permanently removes the sidebar description and FAQ "contact us" widget
  from the live page. This is a deliberate, confirmed decision — flagged here explicitly so it is
  not later "fixed" as an apparent oversight.
- **Naming collision risk**: `templates/archived_quick_links/questions_sections.html` is not
  referenced by any template — the row list is inlined directly in `main.html`. A **different,
  unrelated** file shares the same name at `templates/faq_others/questions_sections.html` — do not
  touch that one.

---

## 8. Edge Cases

- **Zero archived items**: `archived_items_list` could be empty (no admin-flagged entries currently
  archived). Figma's export only shows the 8-item sample; no empty-state design exists in Figma —
  per D7, still show the title band with count "0" plus a short centered empty-state message.
- **Long link titles**: `text-button.html`'s `label` has no built-in truncation. Per D8, titles wrap
  onto a second line; no truncation CSS is added.
- **List growth**: currently 8 items; no pagination exists in Figma or v1. Per D9, out of scope for
  this UI-only migration regardless of future growth.
