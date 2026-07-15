# 060 — Crisis / Event Pages: v2 Migration

**Scope:** Migrate the modular, content-driven crisis/event pages (`/event/<name>` and
`/dashboards/<name>`, both rendered by `pages/read_page.html`) to a single responsive v2
template. Covers the page header (title, description with Show more, Get notified CTA), every
stored section type (`description`, `map`, `key_figures`, `interactive_data`, `data_list`) and
the full dataset-list machinery (filters, inline search, sort, per-page, pagination) reused from
the search/org pages.
**Excluded:** backend/data changes (no model, action, or section-schema changes; the sole
view-logic change is the one-line `is_mobile` fix, D11); the
mobile "light" routes `/m/event` + `/m/dashboards` and their templates (untouched — D1); the
admin editor `/page/new` + `/page/edit/<id>` (`pages/edit_page.html`, untouched); Figma-only UI
with no backing data — "Interactive data" resource list, "You might also like" cards, "Layer"
dropdown (deferred — D3); Back to top button (skipped — D8); new feature development.
**Figma sources:** `crisis-page-sm.html`, `crisis-page-dataviz-maps-etc-sm.html`,
`crisis-page-dataviz-maps-etc-md.html`, `crisis-page-dataviz-maps-etc-xl.html` — the
`dataviz-maps-etc` variants show the same page with the dataviz/map block inserted between the
header and the dataset results; the screencapture image in the exports is a placeholder for the
embedded map/visualization iframe (requester-confirmed).

---

## Context

Crisis/event pages are HDX's CMS-like "custom pages": a `Page` record whose `sections` column
holds a JSON-encoded, ordered list of typed building blocks, composed by sysadmins/managers in an
admin form and rendered by a dispatch loop. They are the last major public v1 page family with a
finished Figma redesign. The Figma layout is essentially the v2 search page (filter sidebar,
dataset cards, pagination — tasks 029–036) plus a crisis header and a full-width dataviz block —
so this migration is dominated by reuse: the org Datasets tab (056) already proved the exact
embedding pattern (`search_results_wrapper.html` with a page-scoped `my_c`), and
`CustomPagesSearchLogic` already produces that object. The only genuinely new pieces are the
page-layout LESS and a small v2 port of the iframe auto-resize module.

All open questions were resolved with the requester on 2026-07-14 (§12).

---

## 1. Existing Implementation Audit

### 1.1 Extensions and data model

Backend lives in `ckanext-hdx_pages`; all templates/assets live in `ckanext-hdx_theme` (the
`templates/` dir inside `ckanext-hdx_pages` is unused — `add_template_directory` is commented out
in its plugin). There is no separate crisis extension: "crisis" is the UI name for a `Page` of
`type='event'`.

`ckanext-hdx_pages/ckanext/hdx_pages/model.py` — table `page`:

| Column | Meaning |
|---|---|
| `id`, `name`, `title`, `description` | identity fields; `description` is admin-entered SEO keywords (admin form labels it "Keywords", `edit_page.html:101`), also dictized as `keywords`; feeds the Lunr site-search index (`extra_terms`) — not rendered on the page |
| `type` | `'event'` (crisis) or `'dashboards'` |
| `state` | CKAN state (`active`, `draft` via "Save as draft") |
| `status` | `'ongoing'` / `'archived'` |
| `sections` | **JSON-encoded ordered list of section objects** — the CMS content |
| `extras` | JSON, currently `{"show_title": "on"/"off"}` |
| `modified` | timestamp |

Plus `page_group_association` (page ↔ countries) and `page_tag_association` (page ↔ tags), used
for the feature-search/Lunr index, not for rendering.

Each element of `sections` (built in
`ckanext-hdx_pages/ckanext/hdx_pages/views/light_page.py:231-240`):

```json
{
  "type": "map",
  "data_url": "https://data.humdata.org/dataset/.../view/... OR a saved /search?... URL",
  "section_title": "El Nino Affected Countries",
  "description": "plain text shown above the section",
  "long_description": "markdown (description-type sections)",
  "max_height": "350px",
  "m_max_height": "50px"
}
```

Canonical section `type` values (`views/light_page.py:34-41`, admin dropdown at `:195-200`):
**`empty`, `description`, `map`, `key_figures`, `interactive_data`, `data_list`**. Sections are
not schema-validated (`actions/validation.py` checks only name/title).

### 1.2 Routing / views

`ckanext-hdx_pages/ckanext/hdx_pages/views/light_page.py` — five blueprints (`:44-50`, URL rules
`:443-451`):

| Route | View | Template |
|---|---|---|
| `GET /event/<id>` | `read_event` → `_read(id, False, True)` | `pages/read_page.html` |
| `GET /dashboards/<id>` | `read_dashboard` | `pages/read_page.html` |
| `GET /m/event/<id>`, `/m/dashboards/<id>` | `read_light_*` | `light/custom_pages/read.html` |
| `/page/new`, `/page/edit/<id>`, `/page/delete/<id>` | `CreateView`/`EditView`/`DeleteView` | `pages/edit_page.html` |

`_read` (`:151-185`): `page_show` → `_populate_template_data` → template vars
(`page_dict`, `page_has_mobile_version`, `analytics`, unsubscribe-token vars via
`add_unsubscribe_token(…, ObjectType.CRISIS, …)` `:180-181`). All read routes are wrapped in
`@check_redirect_needed` (mobile/desktop redirect). Editing is gated by
`PERMISSION_MANAGE_CRISIS` (`helpers/helper.py:93-99`).

`_populate_template_data` (`:109-148`):

1. `json.loads` the sections; per section computes the iframe style
   (`helpers/helper.py:25-32`) — **v1 quirk: `is_mobile=True` is always passed
   (`:115`), so the desktop page also uses `m_max_height`** (fallback height `400px`).
   **Fixed in this task (D11):** `_populate_template_data` will pass the real per-request
   `is_mobile` flag so desktop uses `max_height` and mobile uses `m_max_height`, as originally
   intended.
2. `data_list` sections: parse the saved search URL (`_find_dataset_filters`,
   `helpers/helper.py:35-37`), build Solr params (`generate_dataset_results`,
   `helpers/helper.py:40-74`: `q`→`text:(…)`, facet keys `organization`/`groups`/`vocab_Topics`/
   `res_format`/`license_id`/`cod_level`, raw `fq`, `sort`→`default_sort_by`,
   `ext_page_size`→`num_of_items`; live request args except `page` merged), run
   `CustomPagesSearchLogic._search(...)`
   (`controller_logic/custom_pages_search_logic.py`, a `SearchLogic` subclass that only overrides
   URL generation so pager/facet links point to `/event/<name>…#datasets-section`,
   `helpers/helper.py:49`), store the result on `section['template_data']`. Archived-URL redirect
   handled via `add_archived_url_helper().redirect_if_needed()` (`:128-131`).
3. Desktop only: if the **first** section is a `map`, pop it into `page_dict['title_section']`
   (`:145-147`) → rendered as a full-bleed map behind the title with a share button
   (`pages/snippets/visualization_title.html`, `analytics_shared_item="crisis"`).

### 1.3 Templates and section dispatch (today)

```
ckanext-hdx_theme/.../templates/pages/read_page.html      desktop page (extends v1 page.html)
  ├─ pages/snippets/visualization_title.html               full-bleed first-map title section
  └─ pages/snippets/section_item.html                      per-section dispatch (loop at :62-65)
ckanext-hdx_theme/.../templates/light/custom_pages/read.html   mobile light page (untouched)
ckanext-hdx_theme/.../templates/pages/edit_page.html      admin editor (untouched)
```

`read_page.html`: analytics blocks (`:6-7`), subtitle `… | Crisis Datasets` (`:9`), meta
description (`:10-13`), mobile `rel=alternate` link + canonical (`:15-20`), breadcrumb
`Home / {type} / {title}` (`:22-32`), header with `show_title` gate (`:44-46`), state label when
not `active` (`:47-49`), **page-level `description` commented out** (`:50`), notification buttons
(`:51`), section loop (`:62-65`), notification modals with unsubscribe-token params (`:69-76`),
assets (`:89-90`).

`pages/snippets/section_item.html` — the type switch:

- `data_list` (`:12-32`) → `search/snippets/package_list.html` (v1 params: `query`, `packages`,
  `full_facet_info`, `ext_page_size`, `sorting_selected`, `other_links`) + `my_c.page.pager()`.
- `description` (`:33-40`) → `h.render_markdown(section.long_description)`.
- **else** — `map` / `key_figures` / `interactive_data` (`:41-67`) → optional `section_title`
  header row + optional `section.description` text +
  `<iframe data-module="data-viewer" src="{{ section.data_url }}" style="{{ section.style }}">`
  with a `data-viewer-error` div. **There is no distinct rendering per iframe type** — all three
  are generic embeds.

### 1.4 Dataset list (`data_list`)

Reuses the site dataset-search logic end-to-end (§1.2.2) — filters, inline `q` search, sort,
page-size and pagination all work in-page today because live request args are merged over the
section's saved filters. The saved `data_url` is a normal HDX search URL captured in the admin
form (fixture example, page `elnino`:
`https://data.humdata.org/search?q=el%20nino&sort=last_modified+desc&ext_page_size=25&page=1`).

### 1.5 Data visualizations

Iframes only — no native charting. Auto-resize + error handling via the CKAN module `data-viewer`
(`ckanext-hdx_theme/.../fanstatic/modules/data-viewer2.js`: `_recalibrate` on load,
`minHeight: 400`, Firefox cache-bust) bundled in the v1 base assets.

### 1.6 Notifications ("Get notified")

`notification_platform/buttons.html` + `notification_platform/modals.html` with
`object_type='crisis'`. **Both snippets are already v2-built** (051): `buttons.html` renders
`v2/components/button.html` opt-in/opt-out buttons; `modals.html` loads
`hdx_theme/v2-components-scripts`, `notification-platform-unsubscribe-scripts`,
`v2-form-validator-scripts` and (when supported) `notification-platform-subscribe-scripts` — the
same wiring the v2 dataset page uses (`package/hdx_read.html:117-120` passes
`supports_notifications` + `notification_object_*` into `page-header.html`, which renders
`buttons.html` at `v2/components/page-header.html:263-271`).

### 1.7 Analytics

- `_read` passes `analytics_came_from` + `analytics_supports_notifications`
  (`views/light_page.py:175-178`, from `ckanext-hdx_package/.../helpers/analytics.py`) into the
  template's `analytics_came_from` / `analytics_supports_notifications` blocks
  (`read_page.html:6-7`) → Mixpanel page-view init in `templates/base.html`.
- Dataset-card interactions: GA/Mixpanel via `data-*` attributes on the v2 card (038 convention)
  — comes along automatically with the reused v2 dataset list.
- Share button (`visualization_title.html:22-23`, `analytics_shared_item="crisis"`) — dropped
  together with the title-section variant (D6); no other share UI exists in the Figma design.

### 1.8 Assets (today)

Desktop page loads `hdx_theme/search-scripts` + `hdx_theme/custom-pages-styles`
(`read_page.html:89-90`); the `data-viewer` module ships in the v1 base bundle. None of these may
be loaded by the v2 page (v1-assets-untouched rule).

---

## 2. Section Inventory

Every stored section type, its purpose, and its v2 mapping:

| Type | v1 rendering | Figma counterpart | v2 mapping |
|---|---|---|---|
| *(page header — not a section)* | title + `show_title` gate + state label + notification buttons; description commented out | crisis header: title, description + Show more, Get notified CTA | `v2/components/page-header.html` — `title`, `description` (clamped-text Show more, D4), `supports_notifications` + `notification_object_*` (D7); `c-label` for non-active state |
| `description` | `h.render_markdown(long_description)` | text/content block | **First** `description`-type section in stored order is promoted into the page-header's `description` slot (plain text via `h.markdown_extract`+`striptags`, not rendered inline) — D4. Any subsequent `description` section still renders as a v2 text section: rendered markdown with v2 body typography |
| `map` | iframe (`data-viewer`); first-map = full-bleed title section + share | full-width map below header (screenshot placeholder) | bare full-width iframe section, auto-resize module (D5); **no title row, no accordion, no full-bleed variant, no share** (D6) |
| `key_figures` | iframe (`data-viewer`) | — (header KPI box is unrelated and omitted, D2) | same bare full-width iframe section (D6) |
| `interactive_data` | iframe (`data-viewer`) | "Interactive Data or Map" block | same bare full-width iframe section (D6) |
| `data_list` | v1 `package_list.html` + pager, filters via saved search URL | dataset results: filter sidebar/overlay, inline search, sort, per-page, cards, pagination | `search/snippets/search_results_wrapper.html` with `my_c=section.template_data, v2=true` + `v2/search-filters.html` sidebar (§5) |
| `empty` | never saved (filtered in `_populate_sections`); would fall into the iframe branch | — | skipped defensively (no output for unknown/`empty` types) |

Figma sections with **no** v1 counterpart — deferred (D3): "Interactive data" resource-card list
(MD/XL), "You might also like" cards (XL), "Layer" dropdown. Back to top — skipped (D8). Header
KPI box — omitted (D2).

---

## 3. Figma Mapping

Page skeleton (all exports): top-bar / navbar / breadcrumb / crisis header / [dataviz block] /
dataset results / footer. Top-bar, navbar, breadcrumb, footer are the standard v2 shell from
`v2/page.html` — nothing to do.

### XL (`crisis-page-dataviz-maps-etc-xl.html`)

```
[breadcrumb  Home / Products / {title}]                          (D9)
[crisis-page-header]
  left:  title (Merriweather 1.5rem) · rich description + "Show more" · Get notified CTA
         (follower count + logged-in action row: empty placeholders — not implemented,
          no v1 counterpart; Get notified = notification platform buttons)
  right: org logo/follow placeholders — not implemented (no v1 counterpart)
  [metadata KPI box "Datasets 142 / Organisations 13"] — OMITTED (D2)
[dataviz block: full-width map — export wraps it in an "Interactive Data or Map"
 accordion header + Layer dropdown; NOT implemented: bare iframe only (D6, D3)]
[two columns: filter sidebar (filter-no-scroll, = v2 search sidebar) | results:
 "Datasets" + count · per-page + sort dropdowns · inline search · active-filter chips ·
 dataset cards (with contributor grouping) · pagination]
["You might also like" ×4 — deferred (D3)]
```

### MD (`crisis-page-dataviz-maps-etc-md.html`)

Single column: header (description + Show more) → bare full-width map → results with `Filter (n)`
button opening the standard filter overlay → cards → pagination. "Interactive data" resource list
— deferred (D3). Back to top after content — skipped (D8).

### SM (`crisis-page-sm.html`, `…-sm.html`)

Single column: header — the export hides the description (`display:none`); **overridden by D4:
description renders clamped with Show more at SM too** (Jira: "show more behavior, SM
specifically noted") → bare full-width map (dataviz variant) → results with `Filter (n)` button →
compact dataset cards → pagination. Floating Back to top — skipped (D8). "You might also like" is
`display:none` in the export.

Export token names map to the standard v2 tokens (`--color-teal`→`--hdx-brand-7`,
`--color-royalblue`→`--hdx-primary-5`, etc.) — same mapping as prior tasks; no new tokens.

---

## 4. Template Strategy

Direct replacement, org-page precedent (056): `pages/read_page.html` is rewritten to extend
`v2/page.html` — one template, all breakpoints, both page types (D1). Structure mirrors
`organization/read.html`:

- Same head blocks preserved: subtitle `… | Crisis Datasets`, meta description, canonical link,
  mobile `rel=alternate` link (kept — the `/m/` pages remain), analytics blocks (§9).
- `breadcrumb_items` → `v2/components/breadcrumb.html` with
  `Home / Products / {title}` — "Products" unlinked, active item = page title (D9).
- `pre_primary` → header via `v2/components/page-header.html`: `title` (gated by
  `extras.show_title`, v1 parity), `description` sourced from the **first** `description`-type
  section's `long_description` (plain text via `h.markdown_extract`+`striptags`) with
  clamped-text Show more (D4, corrected) — `page_dict.description` (SEO keywords, §1.1) is never
  displayed, `supports_notifications` + `notification_object_type='crisis'` / `object_id` /
  `object_dict` (D7), state label via `c-label` when `state != 'active'`. No tabs, no header
  stats.
- **Section dispatch** stays a loop over `page_dict.sections` in stored order; the per-type
  switch moves to a new v2 dispatcher snippet `templates/v2/crisis-section.html` (page-scoped,
  not under `components/` — 057 precedent), replacing `pages/snippets/section_item.html`. The
  **first** `description`-type section is pulled out of the loop entirely in `read_page.html`
  (before this dispatcher ever sees it) and promoted into the header, above:
  - `description` (2nd+ occurrence only) → markdown text section;
  - `map` / `key_figures` / `interactive_data` → bare iframe section, contained in
    `hdx-v2-container` (§6);
  - `data_list` → §5; unknown/`empty` → no output.
  Non-`data_list` sections render full-width (inside `pre_primary`/full-width wrappers); the
  `data_list` section renders as the two-column search row.
- The first-map `title_section` special case is **dropped** (D6): the template ignores
  `page_dict.title_section` if present — safer: the view keeps producing it, so the v2 template
  simply renders sections in order including a popped title-section map first, without the
  full-bleed treatment. Zero view changes.
- `visualization_title.html` and `section_item.html` are left orphaned in place (057 D9-style),
  never edited — the light page does not use them (`light/custom_pages/read.html` has its own
  inline switch) except `section_item.html`, which only `read_page.html` uses.
- Notification modals: keep the `notification_platform/modals.html` snippet call with the same
  unsubscribe-token params (already v2-compatible, §1.6).

Ordering, section mix and count are entirely CMS-driven and must keep working for any
combination — the dispatcher makes no assumptions about which sections exist (§11).

---

## 5. Dataset Integration Strategy

**Reuse, zero duplication.** `CustomPagesSearchLogic` already produces the same
`template_data` shape (`q`, `page`, `item_count`, `full_facet_info`, `ext_page_size`,
`sort_by_selected`, `other_links`) that `organization/read.html:87-88` feeds into the shared v2
chain. The `data_list` branch of the dispatcher becomes:

- Sidebar (XL): `<form id="search-page-filters-form">` + `v2/search-filters.html` with
  `facet_list=section.template_data.full_facet_info.get('facets', {})` — rendered via the page's
  `secondary_content` block using the search-page layout classes
  (`hdx-v2-search-row/columns/sidebar/content`), exactly like `organization/read.html:64-82`.
- Results: `search/snippets/search_results_wrapper.html` with
  `my_c=section.template_data, v2=true, tracking_enabled=g.tracking_enabled` — brings the list
  header + count, sort/per-page nav controls, inline search bar, active-filter chips, MD/SM
  filter overlay, `dataset-card` list and `c-pagination`, all unchanged.
- Context adaptation only: pager/facet URLs already point at `/event/<name>…#datasets-section`
  (the wrapper already strips the `#fragment` when building the pagination `base_url` —
  `search/snippets/search_results_wrapper.html:35-37`); in-page search,
  filters, sort and page-size keep working through the existing merge of live request args over
  the saved filters (§1.2.2). **No changes to `CustomPagesSearchLogic`, `helper.py` or any
  search logic.**
- Layout nuance vs the search/org pages: the two-column search row starts at the `data_list`
  section, below any full-width sections — handled purely in template structure + page LESS.

Constraint recorded: exactly **one** `data_list` section per page is supported (all production
pages have one; duplicated DOM ids — `#dataset-filter-form`, `#hdx-filter-overlay` — make a
second instance undefined behavior; v1 had the same constraint implicitly). See §11.

---

## 6. Data Visualization Strategy

- Keep iframes as iframes — no reimplementation of any visualization (`data_url` embeds are
  rendered by the target viz apps, not by HDX).
- All three iframe types render identically (v1 parity): a bare iframe inside an outer
  `hdx-v2-crisis-iframe-section` white band (`background-color: var(--hdx-neutral-0)`,
  `margin-top`/`margin-bottom: var(--hdx-space-8)`, 2rem each) wrapping an `hdx-v2-container`
  that constrains the iframe's width — same outer-band-plus-container nesting every other v2
  page-band uses (`hdx-v2-crisis-header-section`, `hdx-v2-org-header-section`, etc.), not
  full-bleed/edge-to-edge — **no section title row, no description text, no
  accordion/collapse, no full-bleed title variant, no Layer dropdown** (D6, D3). The stored
  `section_title`/`description` fields remain in the data model and admin form; they are
  simply not displayed on the v2 page (accepted information loss — §10).
- **Auto-resize ported to v2** (D5): new `fanstatic/v2/crisis-page.js` containing a minimal
  vanilla-JS port of `modules/data-viewer2.js` behavior — on-load height recalibration
  (`minHeight` 400px), error surface — attached via `data-module`-style `data-*` hooks. The v1
  module is never loaded. Recalibration only ever writes `iframe.style.height` when it
  successfully reads the real (same-origin, loaded) content height — a cross-origin iframe, or
  one whose `'load'` event fires before the script attaches (fast/cached content), is left at
  whatever height `_compute_iframe_style` already computed (the admin's `max_height`, or the
  400px default) instead of being clobbered down to the `minHeight`+padding fallback.
- Height config honored: keep applying the computed `section.style` (the view already provides
  it); the v1 `is_mobile=True` quirk (§1.2.1) is **fixed** as part of this task (D11) — the view
  now passes the real per-request `is_mobile` flag, so desktop uses `max_height`.
- No Chart.js / `v2-chart-scripts` needed — nothing on this page draws native charts.

---

## 7. Component Strategy

| UI element | Approach | Justification |
|---|---|---|
| Page shell (top-bar, navbar, breadcrumb, footer) | **Reuse as-is** — `v2/page.html` | Standard |
| Breadcrumb trail | **Reuse** — `v2/components/breadcrumb.html`, `Home / Products / {title}` | D9 |
| Header | **Reuse as-is** — `v2/components/page-header.html` (`title`, `description`, notification params) | Generic params from 056/037 suffice; no new hero |
| Description Show more | **Reuse** — `clamped-text` module (`fanstatic/v2/components/clamped-text.js`) | Established page-header pattern; D4 |
| Get notified | **Reuse as-is** — `notification_platform/buttons.html` + `modals.html` (`object_type='crisis'`) | Already v2-built (051); v1 crisis page already passes `crisis` |
| State label | **Reuse** — `c-label` | Replaces v1 Bootstrap label |
| Filter sidebar + MD/SM overlay | **Reuse as-is** — `v2/search-filters.html` + wrapper-provided overlay | 031/056; same facet dict |
| Inline search / sort / per-page / chips / cards / pagination | **Reuse as-is** — via `search_results_wrapper.html` → `package_list.html` → `dataset-card.html`, `v2/search-nav-controls.html`, `v2/components/pagination.html` | 029/033/035/036/056; no duplication |
| Text (`description`) sections | **First one promoted into the header's `description` param** (D4); any subsequent one **reused as-is** — rendered markdown + v2 body typography | Real CMS prose belongs in the header slot Figma shows; `page.description` (keywords) does not |
| Iframe sections | **New minimal** — plain iframe markup in the dispatcher, contained in `hdx-v2-container` + auto-resize port in `fanstatic/v2/crisis-page.js` | No v2 embed block exists; smallest possible addition (D5/D6) |
| Section dispatcher | **New page-scoped snippet** — `templates/v2/crisis-section.html` | Replaces `section_item.html`; not a `c-*` component (057 precedent) |
| Header KPI box, resource list, You-might-also-like, Layer dropdown, Back to top, share button | **Not implemented** | D2/D3/D6/D8 |

Assets: new `v2-crisis-page-styles` (compiled `v2/crisis-page.css`; LESS source
`hdx-styles/src/common/less/v2/crisis-page.less`, page classes `hdx-v2-crisis-*`) and
`v2-crisis-page-scripts` (`v2/crisis-page.js`); page also loads `v2-search-page-styles` +
`v2-search-page-scripts` (dataset list, like the org Datasets tab). No edits to any v1 bundle.

---

## 8. Responsive Strategy

| Breakpoint | Header | Dataviz sections | Dataset list |
|---|---|---|---|
| **XL (≥ 80rem)** | title + clamped description + Get notified | bare iframe(s), contained in `hdx-v2-container`, `margin-top` between sections | two columns: filter sidebar + results (search-page layout classes) |
| **MD (48–80rem)** | same | same — `m_max_height`-based style (v1 parity, §1.2.1) | single column; `Filter (n)` button → full-screen overlay |
| **SM (< 48rem)** | same — description clamped, NOT hidden (D4, deliberate Figma deviation) | same | single column; overlay; compact card variant (built into `dataset-card`) |

Section stacking is the stored order at every breakpoint. All breakpoints via `@hdx-bp-*` LESS
variables; no Bootstrap classes. Iframe widths are fluid (`width: 100%` comes with the computed
style); heights from the stored style + JS recalibration (D5).

---

## 9. Analytics Preservation

| What | How it is preserved |
|---|---|
| Mixpanel page view with `cameFrom` + `supportsNotifications` | Keep the `analytics_came_from` / `analytics_supports_notifications` template blocks on the v2 template (same mechanism as `organization/read.html:10-13`); the view already supplies the values — untouched |
| Notification signup/unsubscribe events | Carried by the reused `notification_platform` snippets + their bundles (§1.6) — unchanged |
| Dataset interactions (card clicks, filters, search) | Come with the reused v2 dataset list — `dataset-card` GA `data-*` attributes (038), search/filter tracking identical to the search page and org Datasets tab |
| Share event (`analytics_shared_item="crisis"`) | Removed with the share button (D6) — the only intentional analytics removal, requester-approved |

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Breaking dynamic section rendering** ❗ — pages are CMS-composed; any section mix/order/count must render | Dispatcher is a pure type-switch over the stored list, no assumptions; unknown/`empty` types produce no output; acceptance: render `elnino`-style fixtures plus single-section and description-only pages (§11) |
| **Duplicating dataset logic** ❗ | None written: `CustomPagesSearchLogic` + `search_results_wrapper.html` reused verbatim; only template wiring is new |
| **Losing analytics** ❗ | §9 checklist; the two analytics blocks are the only server-side hook and are kept verbatim; share event removal is explicit (D6) |
| **Inconsistent sections** ❗ — three iframe types with per-page heights styled ad hoc | One shared iframe section rendering for all three types; heights only via the computed `section.style` + shared JS |
| Hidden information loss — `section_title`/`description` on iframe sections no longer shown (D6) | Recorded here + in §12; admin form untouched, data preserved; revisit if content team objects |
| `#datasets-section` anchor behavior — v1 pager URLs carry the fragment | Wrapper already strips `#fragment` for `c-pagination`'s `base_url`; verify pager, facet links and filter-overlay "Show results" all land on the dataset section |
| View emits `title_section` for first-map pages; v2 must not lose that section | Template re-inlines it at the top of the section flow (§4) — no view change, verified with a first-map fixture |
| Two templates share `light/custom_pages/read.html` helpers/JS assumptions | Light page untouched (D1); only `read_page.html` + new v2 files change; `section_item.html`/`visualization_title.html` orphaned, not deleted |

---

## 11. Edge Cases

| Case | Expected behavior |
|---|---|
| Page with no sections / `sections` empty | Header renders; no section output; no errors |
| Description-only page (fixture `elescondite`, `show_title: off`) | No `<h1>` (extras gate); its `description`-type section is promoted into the header (D4), not rendered as a body section |
| `show_title = off` | Title hidden, description/CTA still render (v1 parity) |
| No `description`-type section in `sections` | No description block in the header, no Show more button (clamped-text no-ops) |
| First `description`-type section's `long_description` empty/whitespace | Section is still promoted (and excluded from the section flow) but header shows no description — same net result as if it were absent |
| More than one `description`-type section | Only the first is promoted into the header; the 2nd+ renders inline as a normal text section, unchanged |
| Very long / multi-paragraph header description | Clamped at all breakpoints with Show more/Show less (D4); `h.markdown_extract`+`striptags` may flatten paragraph/list boundaries with no separating whitespace — accepted limitation of the reused helper (same one `org_hero.html` uses) |
| `data_list` with zero results | v2 list header shows count 0 + empty result list (search-page behavior); sidebar facets may be empty — filters form still renders |
| Saved search URL with unparseable/missing params | v1 parity — `generate_dataset_results` ignores unknown keys; empty `fq` searches everything |
| Archived saved-search URL | Existing `add_archived_url_helper` redirect fires before render — unchanged |
| Iframe `data_url` empty or failing to load | Error div shown by the ported auto-resize module; page otherwise intact |
| Missing `max_height`/`m_max_height` | Computed style falls back to `400px` height (helper unchanged) |
| Section with unknown/`empty` type in stored JSON | Skipped silently |
| More than one `data_list` section | Unsupported (documented constraint, §5) — first renders, rest render nothing; flagged in the doc rather than engineered around |
| First section is a `map` | Renders as a normal full-width iframe at the top (D6); `title_section` re-inlined |
| `state != 'active'` (draft) page viewed by a manager | `c-label` state chip next to the title (v1 parity) |
| `type = 'dashboards'` page | Same template/behavior; breadcrumb still `Products` (D9); subtitle unchanged |
| Anonymous vs `PERMISSION_MANAGE_CRISIS` user | Read page has no manage UI in v1 — nothing to gate; edit routes untouched |
| Notification platform disabled for the object | `buttons.html` renders opt-in hidden (existing helper gate) — unchanged |

---

## 12. Decisions (2026-07-14)

All requester's explicit choices, resolved before writing this doc:

| # | Decision | Rationale |
|---|---|---|
| **D1** | One responsive v2 template for `/event` + `/dashboards`; `/m/` light routes/templates untouched | Both types share `read_page.html` today; no routing/backend change |
| **D2** | Header KPI box ("Datasets / Organisations" counts) **omitted** | No v1 data source; v1 key figures are iframes, not counts |
| **D3** | "Interactive data" resource list, "You might also like", "Layer" dropdown — **deferred** | Figma-only; no backing data/feature; "no new feature development" |
| **D4** | Header description, clamped + Show more at **all** breakpoints (incl. SM), is sourced from the **first `description`-type section's `long_description`** — not `page_dict.description`, which is admin-entered SEO keywords (§1.1), never rendered on the page | Live-testing showed `page_dict.description` displaying as a keyword list, not prose; the admin form itself labels the field "Keywords". Section `long_description` is the real CMS prose content and belongs in the header slot Figma shows. Show-more-at-all-breakpoints part of the original decision (Jira note winning over the Figma SM export) is unchanged |
| **D5** | Iframe auto-resize **ported to v2** (`fanstatic/v2/crisis-page.js`) | Preserves v1 behavior; v1 bundles must not load on v2 pages |
| **D6** | Dataviz sections = **bare iframe below the header, every breakpoint, contained in `hdx-v2-container`** (full width of the container, `margin-top` spacing above — not full-bleed/edge-to-edge) — no accordion, no title row, no full-bleed first-map variant, no share button | Requester: the Figma screenshot is the map placeholder, "right below the page header, full width, no title"; supersedes the earlier accordion answer; contained (not full-bleed) per follow-up review |
| **D7** | Get notified = existing `notification_platform/buttons.html` + `modals.html` with `object_type='crisis'`, wired through `page-header.html` params | Snippets are already v2 (051); dataset-page precedent |
| **D8** | Back to top button **skipped** | No v1 or v2 precedent; candidate for a future shared pattern |
| **D9** | Breadcrumb `Home / Products / {title}`, "Products" unlinked | Figma; consistent with the navbar Products menu |
| **D10** | Iframe sections stay **bare** — `section_title`/`description` remain unrendered (no title-row addition) | Requester confirmed on review; matches D6, no content-team ask to restore it |
| **D11** | v1 `is_mobile=True` height quirk (§1.2.1) **fixed** as part of this task | Requester elected to fix now rather than defer; one-line view change in `views/light_page.py` (`_populate_template_data`) to pass the real per-request `is_mobile` flag |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/.../templates/pages/read_page.html` | Replaced with the v2 template (extends `v2/page.html`): header via `page-header.html` (description sourced from the first `description`-type section, D4), section loop via the new dispatcher, search-row layout blocks, notification modals kept |
| `ckanext-hdx_theme/.../templates/v2/crisis-section.html` | **NEW** — section-type dispatcher (description 2nd+ / iframe / data_list no-op) |
| `ckanext-hdx_theme/.../templates/v2/components/page-header.html` | Added optional `state_label_text`/`state_label_color` params (chip rendered after the title); title `<h1>` now skipped entirely when `title` is empty (was previously always rendered) — backward compatible, other callers unaffected |
| `hdx-styles/src/common/less/v2/crisis-page.less` | **NEW** — page layout (`hdx-v2-crisis-*`), iframe section (outer white band + margin-top/bottom, inner container-constrained), description section, compiled to `fanstatic/v2/crisis-page.css` |
| `ckanext-hdx_theme/.../fanstatic/v2/crisis-page.js` | **NEW** — iframe auto-resize + error handling port (D5) |
| `ckanext-hdx_theme/.../fanstatic/webassets.yml` | New `v2-crisis-page-styles` / `v2-crisis-page-scripts` bundles |
| `pages/snippets/section_item.html`, `pages/snippets/visualization_title.html` | Orphaned in place (superseded by the v2 template), never edited |
| `ckanext-hdx_pages/ckanext/hdx_pages/views/light_page.py` (`_populate_template_data`) | **One-line change** (D11): pass the real per-request `is_mobile` flag instead of the hardcoded `True`, so desktop iframes use `max_height` |
| `light/custom_pages/read.html`, `pages/edit_page.html`, `page.description` storage/dictize/Lunr indexing | **Untouched** — no other view/logic/backend/data-model change anywhere in this task |
