# 063 — Location Page (Data Grids): v2 Migration

**Scope:** Migrate the single-location detail page (`/group/<id>`, e.g. `/group/afg` = "Afghanistan") to
v2 — header/intro, the "Data Grid Availability" section (collapsed/expanded states, category cards,
per-dataset status indicators), the legend/definitions drawer, and the in-page "Datasets" browse/filter
section. Reuse the existing data-completeness logic and the existing v2 drawer component; **no
backend/data changes**.
**Excluded:** the "You might also like" section (a separate `.signals` block further down the page); the
conditional "Key Figures" topline-carousel + Leaflet crisis map block (`country/key-figures.html` +
`drawMap()`), which appears in none of the 7 Figma exports and is left as v1, untouched; any
backend/data-model changes.
**Figma sources:** `location-data-grid.html` (XL) and `location-data-grid-sm.html` (SM) are the
authoritative source for the Data Grid section itself, superseding the original 7-export set below where
they disagree. `sm-location-page-datagrids-drawer.html` remains the only capture of the drawer's SM layout.
Original 7: `sm-location-page-datagrids-collapsed.html`, `sm-location-page-datagrids-expanded.html`,
`sm-location-page-datagrids-drawer.html`, `md-location-page-datagrids-collapsed.html`,
`md-location-page-datagrids-expanded.html`, `xl-location-page-datagrids-collapsed.html`,
`xl-location-page-datagrids-expanded.html`.

---

## Context

The location page's "Data Grid Availability" section is the last major content-heavy page in the v2
rollout with no existing v2 precedent: unlike the org page (056-059) or the locations list page (048), it
has no direct analogue already on branch. It combines a data-heavy grid (6 categories × ~20 sub-categories
× N datasets), a single page-wide collapse/expand toggle, per-item status indicators styled like checkboxes,
a legend/definitions drawer, and a layout that reshapes from a vertical stack (SM/MD) to a 3×2 grid (XL) —
compounded by genuinely inconsistent Figma exports across breakpoints (see §2, §4). This doc audits the
current v1 implementation end-to-end, maps every Figma export, and resolves the ambiguities that block a
straightforward migration before any code is written.

---

## Decisions Taken

| # | Decision | Rationale |
|---|---|---|
| D1 | `.data-grid-checkbox` elements (status swatches on category cards, sub-category rows, and the chart legend) are **decorative status indicators, not real form checkboxes** — they are not built on `c-checkbox`. Hovering one reveals an info tooltip, reusing v1's existing per-dataset "Limitations" tooltip content/pattern, just restyled onto the new swatch. | Requester's explicit choice. No `<input>`, ARIA checkbox role, or click handler exists on any `.data-grid-checkbox` instance in any of the 7 Figma exports — only the task brief's requirement for an XL hover state implied any interactivity at all, and a hover-triggered tooltip (not a toggle/filter) is the interpretation that matches both the visual evidence and v1's existing per-dataset tooltip precedent. |
| D2 | Legend content matches Figma exactly: the drawer becomes a pure category/sub-category **definitions glossary** (no color swatches, no checkboxes). The color/status key moves permanently to the new inline 4-item `.chart-legend` next to the stacked bar chart in the page header. v1's CSS-hover "Show legend" floating panel (`completeness_legend.html`) is retired entirely. | Requester's explicit choice, resolving a genuine content-model mismatch: v1's current legend is a 3-color swatch key ("What do the Data Grids measure?"); Figma's drawer (`sm-location-page-datagrids-drawer.html`, mirrored by `drawer-legend-sm.html`) is a glossary of all 6 categories + ~20 sub-categories with descriptive text and no color swatches at all. Splitting the two concerns — color key inline, definitions in the drawer — is the only reading that uses every piece of Figma content without inventing anything. |
| D3 | **One unified, responsive v2 template** replaces both `country/country.html` (desktop) and `light/group/read.html` (mobile) — full replacement, no `{% if v2 %}` gate. | Requester's explicit choice, matching task 048's approach (direct replacement) rather than 056-058's gated rollout. The two existing templates already render near-identical markup with only a `hide_details` flag differing (§1.2) — collapsing them into one responsive template removes duplication rather than preserving it under a new coat of paint. |
| D4 | The "Datasets" browse/filter/results section that appears directly below the grid in every Figma export (sidebar filters, dataset cards, pagination — distinct from the excluded "You might also like" block further down) **is in scope for this doc**, documented as a reuse of the existing shared search-results snippet, not new work. | Requester's explicit choice. "Full location page layout" is stated as included scope, and the section is visually present on every one of the 7 exports; per §1.8, it already reuses the exact snippet `organization/read.html` (task 056) calls with `v2=true` — there is no new UI to design here, only wiring to confirm. |
| D5 | The conditional "Key Figures" topline-stats-carousel + Leaflet crisis map block (`country/key-figures.html`, `country.html` lines ~102–186, `drawMap()`/C3 sparklines in `country.js`) is **out of scope** — left rendering as v1, untouched by this task. | Requester's explicit choice. This block sits between the header and the Data Grid section on today's page but appears in none of the 7 Figma exports, and the task's own page-structure outline lists only "Header/Intro" and "Data Grids" — treating it as a separate, deferred concern (comparable to how task 048 left v1 map markup in place, "not redesigned") avoids silently dropping a working feature under the guise of this task. |
| D6 | The chart-legend's "N/A" percentage is computed via a **pure Jinja2 aggregation** over the already-fetched `category.data_series` — no changes to `data_completeness.py`. The per-category mini progress bar also gets a 4th N/A segment (not just the page-level header chart). When a location has zero N/A sub-categories, the 4th legend swatch (and the mini-bar's N/A segment) is hidden rather than always shown. | Requester's explicit choice. Keeps the "no backend changes" constraint intact (§3.1, R1) while extending the same N/A treatment consistently to both progress-bar instances; hiding at zero avoids showing an always-present but meaningless "N/A: 0%" swatch. |
| D7 | Hover tooltips on `.data-grid-checkbox` status swatches are **per-dataset only** (reusing `dataset.general_comment`, per D1/§3.5). The static header-level chart-legend swatches and each category card's own summary swatch do **not** get any tooltip content. | Requester's explicit choice, confirming v1's existing behavior (only per-dataset rows carry "Limitations" text) rather than inventing new tooltip copy for swatches that aren't tied to one specific dataset. |
| D8 | The 3-stat divided KPI row (§2.3: "Total datasets in the Data Grid" / "Organisations contributing" / "Sub-categories available & up-to-date") **extends `c-stats-card`** (task 058), adapted from a card grid to a single borderless flex row with vertical-line separators, rather than extending `c-kpi-card` or introducing new page-scoped markup. | Requester's explicit choice. Reuses the existing borderless-card visual language (already the closest fit per §3.3) instead of adding a fourth distinct "stats row" pattern to the codebase. |
| D9 | The page-level header chart and each category's own indicator are a **row of repeated `c-data-grid-status` swatches** (one per sub-category), not a proportional bar. No separate progress-bar component. | Matches `location-data-grid.html`/`-sm.html` exactly. |
| D10 | The legend/definitions drawer is normalized onto the existing **`c-drawer`** component at its current responsive widths (100% SM / 80% MD / 50% XL) across all three breakpoints, including XL, where no Figma target exists at all. | Requester's explicit choice, per the task's "reuse first, do not duplicate drawer logic" constraint (§4) — accepted even though it fills an XL gap Figma leaves entirely open. |
| D11 | Trigger labels are normalized to a single pair used at every breakpoint: **"Definitions"** (opens the drawer) and **"Overview of Data Grids"** (external link) — no `(XX)` count suffix. MD's "Legend"/"Data grids overview" wording and the `(XX)` placeholder are both dropped. The "Overview of Data Grids" link points to `/dashboards/overview-of-data-grids` (root-relative, in-site path). | Requester's explicit choice, resolving both the label inconsistency (§2.8) and the undefined `(XX)` count (§2.8) by dropping the count entirely rather than picking which entity it should represent. |
| D12 | No new analytics tracking is added for this task. The expand/collapse control and the definitions-drawer's open action remain untracked, matching v1's existing gap (§1.8) — this migration does not introduce new events. | Requester's explicit choice: preserve v1's analytics behavior as-is rather than adding new tracking as a side effect of the migration. |
| D13 | The `indent-icon` shown in place of the status swatch on a `.sub-category` row is the visual treatment for **complementary datasets** (`dataset.is_complementary`), not a generic "2nd+ dataset in this sub-category" marker. It applies at every breakpoint, on any complementary dataset regardless of its position in the list. This resolves both the multi-dataset row pattern (§2.5) and the complementary-dataset edge case (§3.6, §9) as the same requirement. | Requester's explicit choice, correcting the doc's earlier reading of the single captured SM example — the dataset shown with an indent-icon in that example is complementary, which is the actual rule, not its ordinal position. |
| D14 | Category label copy is sourced from the **live per-country YAML config** verbatim, not hardcoded to either the task brief's "Food Security, Nutrition & Poverty" or the XL Figma export's "Food Security & Nutrition". | Requester's explicit choice — avoids hardcoding a label that may already differ from the real config data driving the page. |
| D15 | "Geography & Infrastructure" uses the existing generic `location.svg` icon as-is; no new dedicated icon asset is sourced for this task. | Requester's explicit choice, unblocks R4 without new design/asset work. |
| D16 | The new header keeps a plain **Organisations count** and **Datasets count** (both as `metadata-item`s, matching Figma) plus the permission-gated **"Edit location page"** link. The v1 Organisations-count hover dropdown (listing every contributing org) is dropped. The **Followers count is removed** entirely. | Requester's explicit choice: match Figma's header composition (which shows only plain counts), dropping the hover-dropdown interaction and the Followers metric that Figma never depicts. |
| D17 | The drawer's own overlay/slide motion (25% black backdrop, ease-out 300ms) is applied to the **shared `c-drawer` component**, not scoped to this drawer alone, so every existing drawer in the app matches. Category cards render **collapsed by default** (a deliberate departure from v1's checked-by-default checkbox, §9). Tooltip positioning on the status-swatch/title tooltips is a known issue, deliberately **deferred**, not fixed in this round. | Requester's explicit choices, made after implementation testing surfaced a card-collapse height bug and the wrong default expand state. |
| D18 | The Definitions drawer's jump-nav is **sticky again**, superseding D17's original "non-sticky at every breakpoint" call — but as part of one combined `__sticky-top` block (intro paragraph + both jump-nav variants) rather than the jump-nav sticking on its own. Offset is measured via a self-contained `MutationObserver` in `location-page.js` (watching the drawer's `is-open` class), not a `drawer.js` change. | Requester's explicit choice, after testing showed the non-sticky jump-nav (D17) visually drifted down the drawer while scrolling — `position: relative` (needed for the mobile dropdown panel's width) has no scroll-freeze behavior on its own, so nothing kept it pinned. Pinning the whole intro/jump-nav block together, rather than re-tuning the jump-nav alone, also fixed the jump-to-category scroll offset, which previously only accounted for the drawer's title bar, never the jump-nav's own height. |

---

## 1. Existing Implementation Audit

### 1.1 Routing / View

```
ckanext-hdx_org_group/ckanext/hdx_org_group/views/group.py
  hdx_group blueprint, /group/<id> → read(id) → _read()
    ↓
ckanext-hdx_org_group/ckanext/hdx_org_group/controller_logic/group_read_logic.py
  GroupReadLogic
    ↓
ckanext-hdx_org_group/ckanext/hdx_org_group/helpers/country_helper.py
  get_template_data()  — builds the `data` dict passed to the templates
```

`048-locations-list-v2.md`'s `GroupIndexReadLogic` (the **All Locations** browse/search page at `/group/`)
is a related but entirely different view — confirmed distinct in that doc and re-confirmed here. This doc
covers only the **single-location detail page**.

### 1.2 Templates

| Template | Lines | Extends | Role |
|---|---|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/country/country.html` | 280 | `crisis/crisis-base.html` → v1 `page.html` (Bootstrap shell) | Desktop |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/group/read.html` | 175 | v1 light/mobile base | Mobile — renders the same widgets with `hide_details=true` |

Both templates ultimately extend a **v1 Bootstrap shell**, not `v2/page.html` — this migration re-parents
the page's ancestor chain entirely, not just its Data Grid markup (see Risk R3, §8). Per D3, the two
templates collapse into one responsive v2 template; `hide_details` (today's only branch point between
them) is superseded by CSS-driven responsive behavior.

### 1.3 Header / Intro (current v1)

`country.html:35-100` (`{% block crisis_data %}`):

```jinja2
<h1 class="country-title">{{ data.country_dict.display_name }}</h1>
{{ h.snippet('notification_platform/buttons.html', object_id=data.country_dict.id, object_type='group') }}
...
{{ num_of_pack }} Datasets  →  <a href="?#dataset-filter-start">…</a>   (+ CODs count if any)
{{ num_of_followers }} Followers
{{ num_of_orgs }} Organisations  → hover dropdown listing every contributing org, via `followers-list-popup`
{% snippet "country/country_actions_menu.html", country=..., can_edit=h.check_access('group_update', ...) %}
```

This maps directly onto the Figma `dataset-page-header` block (title + "Get notified" button + key-figure
metadata: Datasets count, Organisations count + "Edit location page" link) — the current v1 markup already
has a 1:1 conceptual match:

| v1 element | Figma element | Notes |
|---|---|---|
| `<h1 class="country-title">` | `<b class="dataset-title">` | Location display name |
| `notification_platform/buttons.html` snippet | "Get notified" button | Same component already used elsewhere (e.g. task 051's drawer flow) — reuse as-is |
| Datasets count (`?#dataset-filter-start` anchor) | `metadata-item` "Datasets" | See §5 for anchor-scroll behavior |
| Organisations count + hover dropdown | `metadata-item` "Organisations" | Per D16, the hover dropdown is dropped — v2 renders a plain count, matching Figma |
| Followers count | *(not present in any Figma export)* | Per D16, removed entirely |
| `country/country_actions_menu.html` (permission-gated) | "Edit location page" text-button | Preserve the `group_update` permission gate |

### 1.4 Data Grid section (current v1)

`country.html:187-239`:

```jinja2
{% if data.data_completeness %}
<div class="row data-completeness">
  <div class="list-header crisis-list-header">
    <span class="list-header-title">Data Grid Availability</span>
    <div class="progress-breakdown progress-header">   <!-- 3-segment bar: blue / striped / empty, each with a Bootstrap tooltip showing its % -->
    <span class="list-header-showall">
      {{ good_dataseries_num }}/{{ total_dataseries_num }} Core Data
      {{ total_datasets_num }} Datasets
      {{ org_num }} Organisations
    </span>
    <span class="completeness-header-actions">
      <a class="show-completeness-legend">Show legend</a>
      {% snippet 'country/completeness_legend.html' %}   <!-- pure CSS :hover panel, NOT JS/drawer -->
      <input type="checkbox" id="expand-data-completeness" checked>
      <label for="expand-data-completeness">Expand</label>
    </span>
  </div>
  {% snippet 'country/completeness_list.html', data=data %}
</div>
{% endif %}
```

`country/completeness_list.html` (97 lines) — the grid body, a Bootstrap `col-12 col-md-4` 3-per-row grid
of `.data-item` category cards:

```jinja2
{% for category in data.data_completeness.categories %}
  <div class="data-item">
    <div class="data-item-summary">                          <!-- always visible -->
      <div class="categ-title" data-bs-original-title="{{ category.title }}: {{ category.description }}">
        {{ category.title }}
      </div>
      {{ category.stats.total_datasets_num }} Datasets
      <div class="completeness-progress"> … 3-segment mini progress bar, per-segment tooltip … </div>
    </div>
    <div class="data-item-details" style="{% if hide_details %}display:none{% endif %}">
      {% for subcateg in category.data_series %}
        <div class="sub-category">
          <div class="sub-categ-title" data-bs-original-title="{{ subcateg.description }}">{{ subcateg.title }}</div>
          {% if subcateg.stats.state == 'not_applicable' %}
            <div class="flag">{{ h.hdx_datagrid_org_get_display_text(subcateg) }}</div>
          {% elif subcateg.datasets | length > 0 %}
            {% for dataset in subcateg.datasets %}
              <div class="dataset{% if dataset.is_complementary %} dataset-complementary{% endif %}"
                   data-bs-original-title="{{ dataset.title }}<br/><b>Limitations</b>: {{ dataset.general_comment }}">
                <span class="data-completeness {% if dataset.is_good %}blue{% else %}striped{% endif %}"></span>
                <a href="{{ h.url_for('dataset_read', id=dataset.name) }}"
                   data-module="hdx_click_stopper" data-module-link_type="data grid dataset">{{ dataset.title }}</a>
                <span class="data-org">{{ dataset.organization_title }}</span>
              </div>
            {% endfor %}
          {% else %}
            <a class="add-data" {% if not c.userobj %}data-module="hdx_click_stopper" data-module-link_type="data grid add data"{% endif %}>Add Data</a>
          {% endif %}
        </div>
      {% endfor %}
    </div>
  </div>
{% endfor %}
```

**Important:** every hover tooltip in this section (`category.title`+`description`, `subcateg.description`,
per-dataset "Limitations" text) is already fetched by the backend and already rendered today, just as
Bootstrap-tooltip title text rather than a drawer/glossary. This directly informs the Drawer Strategy
(§4) and Data Grid Analysis (§3): **no backend change is required** to source the Definitions drawer's
glossary content — `category.description` and `subcateg.description` already exist in the data passed to
the template.

### 1.5 Interaction (current v1) — single global toggle, no per-row state

`ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/country/country.js`:

```js
function onDataCompletenessExpand() {
  $(".data-item-details").toggle(this.checked);
}
$("#expand-data-completeness").change(onDataCompletenessExpand);
```

There is **exactly one** interactive control for the entire grid: the "Expand" checkbox in the section
header. Checking/unchecking it shows/hides **every** category's `.data-item-details` simultaneously — there
is no per-category collapse and **no per-row checkboxes of any kind** in the current implementation. State
is not persisted (resets on page reload).

`country.js` is a **shared, multi-purpose page script** — it also contains `drawMap()` (Leaflet), C3
sparkline setup, and mobile topline-carousel logic for the out-of-scope Key Figures/map block (D5). Only
the 3-line `onDataCompletenessExpand` function belongs to this task; the rest of the file must not be
touched or migrated here.

### 1.6 Legend (current v1) — pure CSS hover, not JS/drawer

```less
.show-completeness-legend:hover ~ .completeness-legend { display: block; }
```

`country/completeness_legend.html` (30 lines) is a static floating panel: "What do the Data Grids measure?"
intro text + a 3-state color-swatch key (available/up-to-date, available/not-up-to-date, unavailable). This
is **not** JS-driven and **not** a drawer — hovering the "Show legend" link is the entire mechanism. Per D2,
this whole panel is retired in v2.

### 1.7 Rendering — fully server-side, no AJAX

All data-completeness content is Jinja2-rendered from the initial page response. Data flow:
`country_helper._get_data_completeness()` → `caching.cached_data_completeness()` →
`DataCompleteness.get_config()` (`ckanext-hdx_org_group/ckanext/hdx_org_group/helpers/data_completeness.py`,
329 lines), which:

1. Fetches a **per-country YAML config** from an external URL (`hdx.datagrid.config_url_pattern` setting) —
   defines the 6 categories, their sub-categories, and Solr include/exclude rules per sub-category.
2. Runs a Solr `package_search` query per rule (`__build_query`/`__generate_query_from_rules`).
3. Runs each matched dataset through the freshness calculator
   (`ckanext-hdx_package/ckanext/hdx_package/helpers/freshness_calculator.py`) to mark it "good"/"not good".
4. Aggregates 3-level stats: per-dataseries (`state ∈ {good, not_good, empty, not_applicable}`),
   per-category, and page-level general stats — **`not_applicable` sub-categories are explicitly excluded
   from every percentage/stat computed at every level** (see Risk R1, §8, and D6).

A separate `hdx_datagrid_show` API action (`ckanext-hdx_org_group/ckanext/hdx_org_group/actions/get.py`)
exposes the same data externally but is **not called by any JS on this page today** — v2 stays fully
server-rendered, matching v1's architecture; no AJAX is introduced.

### 1.8 Analytics (current v1)

Dispatcher: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/google-analytics.js` —
`hdxUtil.analytics.send*Event()` builds a Mixpanel payload + GTM `dataLayer.push()`.

Trigger: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/hdx_click_stopper.js`, a
`ckan.module('hdx_click_stopper')` bound via `data-module="hdx_click_stopper" data-module-link_type="..."`.
On click it calls `hdxUtil.analytics.sendLinkClickEvent({id, linkType, label, destinationUrl})`, then defers
navigation until the tracking call resolves/times out.

| Event (`link_type`) | Where | Logged-in behavior |
|---|---|---|
| `data grid dataset` | Every dataset link in `completeness_list.html:69` | Tracked for all users |
| `data grid add data` | "Add Data" link, logged-out only | Logged-in users get a plain `onclick="contributeAddDetails(...)"` call — **not tracked today** (existing asymmetry, preserve as-is) |

**The expand/collapse checkbox has zero analytics tracking today** — per D12, v2 does not add tracking here
either.

### 1.9 Dataset browse/filter/results section (in scope, D4)

Confirmed: this section — visible directly below the Data Grid in every one of the 7 Figma exports, and
structurally distinct from the excluded "You might also like" `.signals` block further down the same page
— renders via the **same shared snippet** `organization/read.html:86-87` (task 056) already calls with
`v2=true`:

```jinja2
{% snippet 'search/snippets/search_results_wrapper.html', v2=true, ... %}
```

Per D4, this doc treats the section as **reuse, not redesign**: the existing v2 dataset-search/results
components (tasks 030, 031, 035, 036, 045) already implement filters, sort, dataset cards, and pagination.
The only location-page-specific work is confirming the location facet is pre-applied the same way v1's
`num_of_pack`/`?#dataset-filter-start` anchor behavior worked (see §5), and that a location filter chip is
pre-populated (visible in every Figma export as a "Ukraine"/similar chip in the active-filters row).

### 1.10 Out-of-scope block (D5)

Between the header (§1.3) and the Data Grid section (§1.4), `country.html` currently renders a conditional
"Key Figures" block (`country/key-figures.html`, gated on `data.country_dict.key_figures` +
`top_line_data_list`) — a topline-stats carousel with C3 sparklines — plus a Leaflet crisis map
(`countryMapPolygon` div + `drawMap()` in `country.js`), and one permanently-dead
`{% if data.widgets.show and false %}` block. **None of this appears in any of the 7 Figma exports**, and
the task's page-structure outline lists only "Header/Intro" and "Data Grids" as in-scope sections. Per D5,
this entire block is left rendering exactly as it does today — this doc does not touch it, and the new v2
template must preserve whatever conditional rendering currently surrounds it (do not silently drop it while
rebuilding the surrounding template).

### 1.11 Web assets

| Bundle | Contents |
|---|---|
| `country-scripts` | `country/country.js` (preloads base CKAN + `country-styles`) |
| `country-styles` | `crisis/topline.css`, `country/country.css` |

---

## 2. Figma Mapping

### 2.1 Common structure across all 7 exports (top to bottom)

```
global header (OCHA Services bar, navbar, breadcrumb: Home / Locations / <Country>)
dataset-page-header                    ← HEADER/INTRO (§1.3)
  title + "Get notified" button
  key-figure metadata (Datasets count, Organisations count)
  "Edit location page" text-button
header-wrapper-parent                  ← DATA GRID SECTION (CORE)
  header: "Data Grid Availability" + subtitle "Assessing the availability of core data across six categories"
  line-parent: 3 KPI-style stats (Total datasets in the Data Grid / Organisations contributing / Sub-categories with available & up-to-date datasets)
  text-buttons-parent: "Show less"/"Show more" toggle + stacked-bar-chart + 4-item .chart-legend
  frame-group: the 6 category cards
  buttons-group: "Definitions"/"Legend" + "Overview of Data Grids"/"Data grids overview" (labels vary — §2.6)
body                                    ← DATASETS SECTION (§1.9, D4)
  sidebar: Location / Organisation / Time period / Data type / Format / Topics / Advanced filters
  dataset-lists: header (count, results-per-page, sort), active-filter chips, dataset cards, pagination
signals                                 ← "You might also like" — EXCLUDED
footer
```

### 2.2 Class families (CSS classes only — `data-grid-*` is never an actual `data-*` HTML attribute
anywhere in these exports)

`data-grid-wrapper`, `data-grid-category-card` (+ numeric suffixes for Figma's duplicate-instance naming),
`data-grid-checkbox` (+ numeric suffixes), `data-grid-checkbox-icon` (1–4), `data-gridaffected-icon` (and
per-category variants), `data-grid-subcategory-item`, `data-grid-location-card-7`/`-11`.

### 2.3 KPI/stat-row recipe (exact)

```
.line-parent           flex row
  .metadata-item3 / .metadata-item5   flex column, centered — value (bold) + label (2-line)
  .frame-child          1px vertical divider line between each stat, height ~5.688rem
```

Three stats: "Total datasets in the Data Grid", "Organisations contributing to the Data Grid",
"Sub-categories with available & up-to-date datasets" (rendered as `9/15`). Per D8, this extends
`c-stats-card` (task 058's borderless card), adapted to a single divided flex row with vertical-line
separators rather than a card grid — see Component Strategy §6.

### 2.4 Stacked bar chart + chart legend (exact)

```
.text-buttons-parent
  .text-buttons3            "Show less"/"Show more" toggle for the KPI/chart panel — see §2.7
  .stacked-bar-chart
    .stacked-bar-chart2     a horizontal bar built from repeated small square icons (bar-value-icon)
    .chart-legend
      .chart-legend-item ×4
        .data-grid-checkbox (or -checkbox4 for the 4th)   ← swatch icon, see §2.8/§3
        text: "Available & up-to-date" / "Available" / "Unavailable" / "N/A"
```

This 4-item legend is the **new inline color key** referenced in D2 — it replaces v1's floating hover-panel
color key entirely.

### 2.5 Category card recipe — collapsed vs. expanded, per breakpoint

| Breakpoint | Collapsed | Expanded |
|---|---|---|
| SM | icon + name, "N missing data" count, one status swatch, **plus a row of 4 status icons** (`data-grid-checkbox-icon` 1–4) | Full `.sub-category` rows: label + status swatch + dataset name + org name. One sub-category ("Humanitarian needs") shows a 2nd dataset row using an `indent-icon` in place of the status swatch — confirmed to simply be the 2nd+ dataset under the same sub-category (not a new parent/child structure) |
| MD | Same fields as SM collapsed, **minus** the 4-icon row — just name + count + one swatch | Same sub-category-row pattern as SM expanded |
| XL | Same as MD collapsed, in a 3×2 grid (see §2.6) | Same sub-category-row pattern, in the 3×2 grid |

Per D13, the indent-icon in the single captured SM-expanded example is not a "2nd dataset" ordinal marker —
it is the visual treatment for that dataset's `is_complementary` flag. The rule generalizes to every
breakpoint and to any complementary dataset regardless of its position in the sub-category's dataset list
(see §3.6).

### 2.6 XL layout — 3×2 grid, not a vertical stack

```
.frame-group
  .data-grid-category-card-parent   row 1 of 3 cards (Affected people / Coordination & Context / Food Security & Nutrition)
  .data-grid-category-card-group    row 2 of 3 cards (Geography & Infrastructure / Health & Education / Climate)
```

Figma marks the containing frame at a fixed `74rem` width. Per CONVENTIONS' "Layout widths" rule (no fixed
`rem`/`px` for layout column widths — use flex ratios or `100%`), this must be implemented as a flex/grid
with `fr` units sized to fill the available content column, not a literal `width: 74rem`.

Separately: the KPI/chart panel's own "Show less" toggle (`.text-buttons3`, §2.4) appears **already
expanded in both** the XL-collapsed and XL-expanded export files — the collapsed/expanded filename
distinction at XL affects only the 6 category cards, not the KPI/chart panel. No export shows what a
collapsed KPI/chart panel looks like at any breakpoint.

### 2.7 Legend/definitions delivery — inconsistent across the raw Figma exports

| Breakpoint | Delivery mechanism found in the export | Content |
|---|---|---|
| SM | Dedicated file `sm-location-page-datagrids-drawer.html` (≈identical to `drawer-legend-sm.html`) — a bottom-sheet/full-height drawer | Header "Data Grid Definitions" + close (X) + intro ("...6 categories and 20 sub-categories...") + sticky "Jump to sub-categories" pill; body: all 6 categories, each icon+name+description+divider, followed by its sub-categories (name + longer description) |
| MD | Same glossary content baked in as a hidden `#drawerContainer.popup-overlay` (`display:none`) — **present in the MD-collapsed export only**, absent entirely from MD-expanded (very likely an export/mock gap, not an intentional per-state difference) | Same as SM |
| XL | **No drawer/modal markup exists in either XL export.** The `popup-overlay` instances present in the XL files are unrelated dataset-list filter dropdowns (location/date/format), not a legend target | Undefined — no content captured at all |

Per D10, all three breakpoints normalize onto the single existing `c-drawer` component at its current
responsive widths (100% SM / 80% MD / 50% XL) — per the task's own "reuse first, do not duplicate drawer
logic" constraint (§4) — even though this departs from MD's literal full-width-modal mock and fills a gap
XL's exports leave entirely open.

### 2.8 Copy

- Per D11, trigger button labels are one pair at every breakpoint: **"Definitions"** + **"Overview of Data
  Grids"** — MD's "Legend"/"Data grids overview" wording and the `(XX)` count suffix are both dropped.
- Per D11, the "Overview of Data Grids" link points to `/dashboards/overview-of-data-grids` (root-relative,
  in-site path), not an external HDX docs URL.
- Per D14, category label copy is sourced from the live YAML config verbatim — neither the task brief's
  "Food Security, Nutrition & Poverty" nor the XL Figma export's "Food Security & Nutrition" is hardcoded.

### 2.9 Confirming `all-location-*` files belong to a different page

Re-confirmed (matching task 048's own scope note): `all-location-{sm,md,xl}.html` and their
`-content`/`-legend`/`-title-kpi`/`-title-filter` fragments belong to the **Locations list/browse page**
(`/group/`, task 048) — heading "Locations", A–Z alphabet nav, HRP toggle, interactive-map/alphabetical-order
switch. None of these files contain any `data-grid-*` class and are not part of this task's scope, beyond
sharing the `c-drawer`/`c-checkbox`/`c-tooltip` components referenced throughout.

---

## 3. Data Grid Analysis

### 3.1 State-model comparison — the central risk (see also Risk R1, §8)

| | v1 today | Figma (new chart-legend) |
|---|---|---|
| States | 3 explicit (`good`/blue, `not_good`/striped, `empty`) + a separately-handled `not_applicable` flag (excluded from every stat) | 4 explicit: Available & up-to-date, Available, Unavailable, **N/A** |
| Where computed | `data_completeness.py`, `__calculate_stats_for_category`/`_dataseries`/`_general` | N/A |

`data_completeness.py` explicitly excludes `not_applicable` sub-categories from every percentage/stat it
computes today. The N/A count is a **pure Jinja2 aggregation** over the already-fetched
`category.data_series` (counting entries whose `stats.state == 'not_applicable'`) at template-render time —
this stays within "no backend changes" since no Python file changes, only the template's own arithmetic.
This applies to both the page-level status row and each category's own status row (§3.2); when a location
has zero N/A sub-categories, the N/A legend item is hidden rather than always shown (D6).

### 3.2 Status row (page-level chart + per-category indicator)

Both the page-level header chart and each category's own collapsed-card indicator are a row of small,
fixed-size `c-data-grid-status` swatches — one per sub-category — not a proportional segmented bar
(confirmed against `location-data-grid.html`/`-sm.html`: every category card's swatch count and coloring
matches its actual sub-category states 1:1). No separate progress-bar component exists.

Per the user's explicit choice, the two rows order their swatches differently: the **page-level chart**
(`country.html`) groups all its swatches by state — every "available & up-to-date" swatch first, then
"available", then "unavailable", then "na" — reusing the already-computed `state_ns` counts, matching the
chart-legend's own order below it. Each **category card's own indicator** (`completeness-item.html`) stays
in category/subcategory data order, unchanged — this divergence is deliberate, not an oversight.

### 3.3 KPI/stat-row component

Per D8, the 3-stat divided row extends `c-stats-card` (058), adapted from a card grid to a single
borderless flex row with vertical-line separators:

| Option | Fit |
|---|---|
| **Extend `c-stats-card` (058) — chosen** | Borderless card is close; adapted from a card grid to a single divided flex row with vertical-line separators |
| Extend `c-kpi-card` (048) | Bordered-box style doesn't match Figma's borderless divided-row look |
| New page-scoped markup | Matches Figma exactly but adds a fourth visual pattern for "3 stats in a row" across the codebase |

### 3.4 Status-swatch component (`.data-grid-checkbox`)

Per D1, this is not a real checkbox. Model it as a small presentational status marker (`role="img"`,
`aria-label` describing the state, e.g. `aria-label="Available and up-to-date"`, plus a state class per
value) — following the same pattern as the existing `c-graph-point` single-marker component, not
`c-checkbox`'s form-input semantics.

### 3.5 Hover state (XL requirement)

Per D1, reuse `dataset.general_comment` ("Limitations" text) via the existing `c-tooltip` component,
attached to each per-dataset status swatch — this is a direct visual restyle of v1's existing per-dataset
Bootstrap tooltip (§1.4), not new interaction design. Per D7, the *static* header-level and
category-summary-level swatches (the chart-legend items and each category card's own status swatch, which
aren't tied to one specific dataset) get no tooltip content — only the per-dataset swatches inside expanded
sub-category rows carry a tooltip.

Known issue (deferred, D17): `.c-tooltip-anchor` (the shared wrapper providing the absolute-positioned
tooltip box) was built for a right-aligned trailing icon (`c-info-icon`) — a mismatch for the swatch
(left-of-row) and title (flex-stretched anchor) tooltips here, which can render detached from their
trigger. Not fixed in this round.

### 3.6 Complementary datasets

v1 has a `dataset.is_complementary` flag (sourced from the YAML config's `complementary_datasets`
overrides) rendered via a `.dataset-complementary` CSS hook. Per D13, this **is** the indent-icon treatment
seen in the SM-expanded Figma example (§2.5) — the indent-icon replaces the status swatch on any dataset row
where `dataset.is_complementary` is true, at every breakpoint, regardless of the dataset's position within
its sub-category.

---

## 4. Drawer Strategy

### 4.1 Reuse the existing `c-drawer` component directly — no new primitive

| Piece | Path |
|---|---|
| Template macro | `templates/v2/components/drawer.html` — takes `drawer_id`, optional `title`, `caller()` body block |
| Styles | `hdx-styles/src/common/less/v2/components/drawer.less` — `.c-drawer` (`display:none` → `flex` via `.is-open`), slides via `translateX`; responsive width 100% (SM) / 80% (MD) / 50% (XL) |
| Behavior | `fanstatic/v2/components/drawer.js` → global `window.hdxV2Drawer(drawerId)` returns `{open, close}` — handles focus save/restore, Escape-to-close, full Tab-trap (via `window.hdxV2.getFocusable()` in `fanstatic/v2/utils.js`), click-to-close on any `[data-drawer-close]`, `aria-hidden` toggling, fires a `drawer:close` CustomEvent |

Already used by ≥6 existing drawers (notification-platform modals, org-members remove/leave/message
drawers) — confirmed fully generic, not feature-specific. Per the task's explicit "do NOT reimplement
drawer logic" constraint, this component is used as-is.

### 4.2 Content

Per D2, the drawer body is a pure definitions glossary: intro paragraph, a "Jump to sub-categories"
pill nav (§4.3), then all 6 categories (icon + name + description + divider) each followed by its
sub-categories (name + longer description). Per §1.4, `category.description` and `subcateg.description`
are already fetched by `country_helper.get_template_data()` today — **the glossary content requires zero
backend change**, only new markup that resurfaces already-available fields.

### 4.3 "Jump to sub-categories" pill

The intro paragraph and both jump-nav variants (desktop pills and mobile dropdown) sit inside one
`__sticky-top` wrapper, sticky at every breakpoint — offset below the drawer's own title bar via a
`--drawer-header-height` custom property, measured by a self-contained `MutationObserver` in
`location-page.js` watching the drawer's `is-open` class (no changes to the shared `drawer.js`). Only the
category/sub-category glossary list scrolls underneath it (D18).

Desktop (XL): plain `text-button` links, part of the sticky block above.

Mobile (SM/MD): the existing `c-anchor-links-mobile` dropdown (`anchor-links.html`, `mobile_only=True`),
extended with two new optional params — `mobile_label` (a static "Jump to sub-categories" CTA instead of
the component's usual current-section label) and `mobile_wrapper_extra_classes` (applies
`c-anchor-links-mobile--drawer-scoped`, which opts the dropdown itself out of the component's own
page-level sticky rule — its position within the outer `__sticky-top` block is what keeps it pinned
instead — while staying `position: relative`, a valid containing block for its own floating panel).
Both params default to the component's original behavior, so its other callers (`resource_read.html`,
`hdx_read.html`) are unaffected.

### 4.4 Delivery mechanism across breakpoints

Per D10, SM/MD/XL normalize onto the single `c-drawer` component at its existing responsive widths (100%
SM / 80% MD / 50% XL), building an XL/MD experience Figma never fully specified (§2.7).

### 4.5 Two trigger links per breakpoint

Per D11, "Definitions" (opens the drawer) and "Overview of Data Grids" (external-link icon, pointing to
`/dashboards/overview-of-data-grids`) are the one label pair used at every breakpoint, with no `(XX)` count
suffix.

### 4.6 Analytics

Per D12, no new tracking is added for the drawer's open action — it remains untracked, matching v1's
existing gap (nothing in v1 tracks the "Show legend" hover panel either).

---

## 5. Interaction Mapping

| Interaction | v1 today | v2 |
|---|---|---|
| Expand/collapse (whole grid) | `<input type=checkbox>` + jQuery `.toggle()` on all `.data-item-details` | Text-button ("Show more"/"Show less") + `aria-expanded` attribute, driving every card's native `<details>` `open` property at once (checkbox and jQuery replaced, same single-toggle-for-everything behavior preserved, per §2.5's confirmed Figma reading). Rendered twice — next to the title on SM/MD (primary style), next to the chart on XL (tertiary style) — only one visible at a time, both driven together |
| Expand/collapse (one category card) | *(did not exist)* | New (round 4) — each card is a native `<details>`/`<summary>`; clicking the summary row expands/collapses just that card, independent of the global toggle above, which always forces every card to the same state rather than reading back any mixed per-card state |
| Dataset link click | `data-module="hdx_click_stopper" data-module-link_type="data grid dataset"` → Mixpanel/GTM | Preserved verbatim, same module/attribute |
| Add-Data link click (logged out) | `data-module-link_type="data grid add data"` → tracked | Preserved verbatim |
| Add-Data link click (logged in) | Plain `onclick="contributeAddDetails(...)"`, untracked | Preserved verbatim (existing asymmetry kept, not "fixed" as part of this task) |
| Hover (category/sub-category/dataset title) | Bootstrap `bs_tooltip` module | `c-tooltip`, same content, CSS `:hover`/`:focus-visible` only — no `is-hovered` classes |
| Hover (`.data-grid-checkbox` status swatch, XL) | *(did not exist)* | New — `c-tooltip`, reusing dataset "Limitations" content per D1/§3.5 |
| Show legend | Pure CSS `:hover` reveals a static panel | Removed entirely (D2) — replaced by the inline chart-legend (always visible, no interaction needed) + Definitions drawer (click-triggered) |
| Drawer open/close | *(did not exist)* | `window.hdxV2Drawer('...').open()/.close()` — focus-trap/Escape/ARIA included for free |
| Dataset-list anchor scroll | `?#dataset-filter-start` query param + anchor, scrolls to the results section | Must carry over — confirm the new template preserves this exact anchor id or an equivalent, so existing external links/bookmarks into `?#dataset-filter-start` keep working |

---

## 6. Component Strategy

### 6.1 Reuse map

| UI element | Component | Notes |
|---|---|---|
| Header/intro hero | Inline `page-header.html` call in `country.html`'s `pre_primary` block | No separate hero wrapper file |
| "Get notified" button | `notification_platform/buttons.html` | Existing, reuse as-is |
| Legend/definitions drawer | `v2/components/drawer.html` + `drawer.less` + `drawer.js` | Existing, reuse as-is (§4) |
| Tooltips (category/sub-category/dataset/status-swatch) | `c-tooltip` | Existing |
| Category icons | `templates/v2/icons/humanitarian-data-grids/{affected,climate,coordination,food,health}.svg` | 5 of 6 exist; "Geography & Infrastructure" uses the existing generic `location.svg` (D15) |
| Status row (page-level chart + per-category indicator) | Repeated `c-data-grid-status` swatches | One swatch per sub-category, in a plain flex row — not a proportional segmented bar (round 3); no separate progress-bar component |
| KPI/stat-row | Extend `c-stats-card` (058) with a `variant='plain'` modifier | (§3.3, D8; `variant` added round 4) |
| Status swatch | `c-data-grid-status`, modeled on `c-graph-point`'s pattern | Explicitly not `c-checkbox`; complementary state renders `v2/icons/indent.svg` (round 4) |
| Dataset browse/filter/results | `search/snippets/search_results_wrapper.html` + existing v2 filter/results components (tasks 030/031/035/036/045) | Existing, reuse as-is (§1.9, D4) |

### 6.2 Considered and rejected

**`c-accordion`** — evaluated and rejected as a drop-in for the category cards. Its model is one
`<details>`-like element collapsing/expanding independently, with no way to also force every card open/closed
from one external control. The page needs both: a global toggle driving every card at once (§1.5, §2.5) *and*
per-card click-to-expand (round 4). Resolved by using the same underlying native `<details>`/`<summary>`
mechanism directly in `completeness-item.html` (not the `c-accordion` component itself), with the global
toggle just setting `.open` on every card's `<details>` element.

---

## 7. Responsive Strategy

| Zone | SM | MD | XL |
|---|---|---|---|
| Category cards | Vertical stack, 1 col | Vertical stack, 1 col | 3-col × 2-row grid (flex/grid-fr, not fixed px — see §2.6) |
| Collapsed card content | Icon+name+status row (one swatch per sub-category), single-line title with ellipsis | Same as SM | Same as SM/MD (round 4 — direct instruction; diverges from `location-data-grid-sm.html`, which shows icon+name only at SM) |
| Expanded card content | Full sub-category rows (label + swatch + dataset + org) | Same as SM | Same as SM/MD |
| KPI/chart panel | Present, own collapse state unclear (§2.6) | Present | Present, always shown expanded in both Figma exports |
| Legend/definitions delivery | `c-drawer` at 100% width (§4.4, D10) | `c-drawer` at 80% width (§4.4, D10) | `c-drawer` at 50% width — no Figma target exists (§2.7, D10) |
| Trigger labels | "Definitions" / "Overview of Data Grids" | "Definitions" / "Overview of Data Grids" | "Definitions" / "Overview of Data Grids" |
| Dataset browse/filter section | Reused v2 components' existing SM behavior | Reused v2 components' existing MD behavior | Reused v2 components' existing XL behavior |

---

## 8. Risks

| Risk | Note |
|---|---|
| **R1 — N/A-state vs. "no backend changes" constraint (HIGH)** | The new 4-state chart-legend needs an "N/A" count that `data_completeness.py` explicitly excludes from its stats today. Per D6, this is a pure-Jinja2 aggregation with zero Python changes — must be validated during implementation, not assumed to just work. |
| **R2 — Two new/extended components built simultaneously (MEDIUM)** | The status swatch (new) and the KPI/stat-row (extends `c-stats-card`, D8) are both needed for this one page with no existing precedent to copy wholesale. |
| **R3 — Template ancestor-chain migration (MEDIUM)** | `country.html` currently extends `crisis/crisis-base.html` → v1 `page.html`. Re-parenting to `v2/page.html` means re-implementing every page-wide block the v1 shell currently provides — breadcrumb, `{% block analytics_group_names %}`/`{% block analytics_group_ids %}`/`{% block analytics_came_from %}`/`{% block analytics_supports_notifications %}` (all present in `country.html:4-11` — must be preserved per CONVENTIONS' "Preserve analytics and functional logic" rule), SEO blocks (`{% block subtitle %}`, `{% block meta %}`), and the mobile/desktop `{% block links %}` alternate-media link. |
| **R4 — Missing 6th category icon (LOW)** | Only 5 of 6 category SVG icons exist (§6.1) — "Geography & Infrastructure" uses the existing generic `location.svg` (D15). |
| **R5 — Complementary-dataset visual treatment (LOW)** | `dataset.is_complementary` has a v1 CSS hook — per D13, it maps to the indent-icon treatment in the new sub-category rows (§3.6). |
| **R6 — Shared script left untouched (LOW)** | `country.js`'s `onDataCompletenessExpand` is orphaned (the v1 checkbox it bound to no longer renders) rather than extracted — simpler than editing a shared file that still serves the out-of-scope Key Figures/map block (D5). |
| **R7 — Out-of-scope block preserved but not verified (LOW-MEDIUM)** | Because the Key Figures/crisis-map block (D5) isn't in any Figma export, there's no visual reference to confirm it still renders correctly once it's sitting inside a page that's otherwise been fully rebuilt around it — needs explicit manual verification during implementation, not just "leave the block's code untouched." |

---

## 9. Edge Cases

| Case | Expected behavior |
|---|---|
| No data-grid config for a country | Existing `{% if data.data_completeness %}` guard already hides the entire section — preserve |
| Category fully `not_applicable` | Confirm rendering (currently shown via the `flag`/`not_applicable` branch, §1.4) |
| Sub-category with 0 datasets | "Add Data" link, logged-in vs. logged-out variants (§1.8) |
| Sub-category with 2+ datasets, any of them complementary | Per D13, any dataset with `is_complementary` true gets the indent-icon treatment in place of its status swatch, at any position and any breakpoint |
| Complementary datasets | Indent-icon treatment, per D13 (§3.6) |
| Very long dataset/organisation names | No truncation spec visible in any Figma export — needs a sensible `overflow`/`text-overflow: ellipsis` default, consistent with how other v2 pages (e.g. 048's `title10` class) handle this |
| JS disabled | Cards render collapsed by default (a deliberate departure from v1's checked-by-default checkbox); each card's native `<details>`/`<summary>` still opens on click with zero JavaScript, so content stays reachable — only the global "Show more"/"Show less" toggle requires JS |
| Location with zero N/A sub-categories | Per D6, the 4th chart-legend swatch and the mini-bar's N/A segment are hidden entirely |
| Follower count (currently shown in v1 header, §1.3) | Removed entirely, per D16 |

---

## Files Affected

| Layer | File | Expected change |
|---|---|---|
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/country/country.html` | Re-parented to `v2/page.html`; header + Data Grid section + commented-out Key Figures/map block (D5) all in `{% block pre_primary %}` |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/light/group/read.html` | Unchanged, out of scope for now |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/completeness-item.html` | Single category-card partial, called directly by `country.html`; a native `<details>`/`<summary>`, collapsed by default, so clicking a card expands/collapses it independent of the page's global toggle |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/country/completeness_legend.html` | Retired (D2) |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/country/country_actions_menu.html` | Orphaned — "Edit location page" is a `header_actions` entry passed to `page-header.html` |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/location-datagrid-drawer.html` | Definitions glossary, sourced from existing `description` fields (§4.2); intro + desktop jump-list + mobile dropdown (static "Jump to sub-categories" label) wrapped in one `__sticky-top` block (D18) |
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/stats-card.html` | `variant='card'\|'plain'` param — `'plain'` is the location-page KPI look (no chrome, value above label, centered) |
| LESS | `hdx-styles/src/common/less/v2/location-page.less` | Page-specific (per `-page.less` naming convention) |
| LESS | `hdx-styles/src/common/less/v2/components/stats-card.less` | `--plain` modifier |
| LESS (orphan) | `country/country.css`, `crisis/topline.css` | Left in place, unused (matches task 058's precedent for orphaned v1 assets) |
| JS | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/location-page.js` | Global expand/collapse (two `text-button` instances, one shown per breakpoint, driving every card's native `<details>` at once); drawer jump-nav scroll wiring (reuses `window.hdxSmoothScrollTo` from `anchor-links.js` against the drawer's own scroll container, offset by the `__sticky-top` block's rendered height); a self-contained `MutationObserver` measuring the drawer's title-bar height into a `--drawer-header-height` custom property (D18) |
| JS | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/country/country.js` | Untouched — still serves the out-of-scope block (D5) |
| JS | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/components/drawer.js` | Unchanged — the sticky-top offset is measured by `location-page.js`'s own `MutationObserver`, not a `drawer.js` event |
| Icons | `templates/v2/icons/humanitarian-data-grids/*.svg` | 5 reused as-is; 6th ("Geography & Infrastructure") uses existing `location.svg` (D15) |
| Icons | `templates/v2/icons/indent.svg` | Complementary-dataset marker |
| Web assets | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` | New `v2-location-page-styles` / `v2-location-page-scripts` bundles; `country.html` also loads `v2-search-page-styles`/`v2-search-page-scripts` |
