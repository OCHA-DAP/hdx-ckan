# 058 — Organization Page (Stats Tab): v2 Migration

**Scope:** Migrate the Organization page's **Stats** tab (`/organization/stats/<name>`) to v2 —
reuse the org page-header/tabs shell from task 056, and re-implement the two v1 charts (currently
C3.js/D3) in **vanilla JS + Chart.js**. Standard AND custom/branded orgs are covered. Because the
single-dataset chart logic is shared with the dataset page's own stats chart, that consumer is
migrated too (D3).
**Excluded:** Datasets tab (056, done), Activity tab (057, done), Members tab, Requested Data tab,
HDX Connect; any backend/data-model changes (no new Mixpanel/JQL queries, no new fields, no schema
changes); any change to chart *meaning*, values, or underlying data — this is a rendering-library
swap, not a data or analytics change.
**Figma sources:** `xl-org-stats-page.html` (dedicated Stats-tab export), `md-org-page.html` and
`sm-org-page.html` (full-page exports — only their Stats sections are used here), plus supplementary
material for the dataset-page chart: `dataset-page-xl.html` and the raw chart crops
`org-chart1.svg`, `org-chart2.svg`, `dataset-chart.svg` (see §2, §5 for how these are used and their
limitations).

---

## Context

Task 056 gave the Organization page a v2 hero (`page-header.html`) and `v2/components/tabs.html`,
but scoped its tab-*content* migration to Datasets only — `v2/org-hero.html:76-84` already lists a
`Stats` tab entry (`active_tab == 'stats'`, href `hdx_org.stats`) waiting on this migration, the same
pattern 057 found for Activity. Unlike 057, this isn't primarily a "reuse an existing v2 component"
job: there is no v2 chart component yet anywhere in the codebase. The core work here is a **charting
library swap** — C3.js (which wraps D3) → Chart.js — on top of the now-familiar header/tabs
migration.

This swap is non-trivial for two reasons uncovered during the audit: (1) v1's top-downloads chart
has two interactions — mouse-wheel zoom/pan and clickable axis labels — built on undocumented C3
internals and a DOM-injection hack respectively, neither of which Chart.js (canvas-based) supports
natively; and (2) the single-dataset line-chart logic is *shared* with the dataset page's own stats
chart, so this task's blast radius extends one page beyond "the org page" in the literal sense. Both
points were raised with the user and resolved (D2, D3) before this doc was written.

---

## 1. Existing Implementation Audit

### 1.1 Routing / View

`ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py`:

```python
def stats(id):
    stats_logic = OrganizationStatsLogic(id, g.user, g.userobj)
    org_dict = stats_logic.org_meta_dao.org_dict
    org_dict.update({'allow_req_membership': stats_logic.org_meta_dao.allow_req_membership})
    template_data = {
        'data': stats_logic.fetch_stats(),
        'org_meta': stats_logic.org_meta_dao,
        'org_dict': org_dict,
    }
    if stats_logic.is_custom():
        return render('organization/custom_stats.html', template_data)
    else:
        return render('organization/stats.html', template_data)

def download_organization_stats(id):   # XLSX export, admin-only (organization_update auth)
    ...

hdx_org.add_url_rule(u'/stats/<id>', view_func=stats)
hdx_org.add_url_rule(u'/<id>/download_stats', view_func=download_organization_stats)
```

Note: unlike 057's `activity_offset()`, the `is_custom` branch here is a **lightweight template
override** (custom_stats.html just swaps the header/style blocks), not a full second copy of the
page — see §1.2. No `is_custom` unification decision is needed the way 057 needed one (D8 there);
the existing branch already matches that precedent's *outcome*.

### 1.2 Data Logic

`ckanext-hdx_org_group/ckanext/hdx_org_group/controller_logic/organization_stats_logic.py`,
`OrganizationStatsLogic.fetch_stats()` returns:

```python
{
  'stats_downloaders': ...,                        # topline: unique downloaders, last 30 days
  'stats_viewers': ...,                             # topline: unique viewers/pageviews, last 30 days
  'stats_top_dataset_downloads': [...],             # up to 25 datasets, desc by downloads, last 24 weeks
  'stats_total_downloads': ...,                     # topline: total downloads, all public datasets
  'stats_1_dataset_downloads_last_weeks': [...],    # only if org has exactly 1 dataset
  'stats_1_dataset_name': ...,
  'stats_dw_and_pv_per_week': [...],                # weekly {date, pageviews, downloads}, last 24 weeks
}
```

All numeric data comes from **Mixpanel via JQL** (`ckanext-hdx_theme/.../util/jql.py`), through
dogpile-cached wrappers, plus a live Solr query in the stats logic that resolves each top-downloaded
dataset's id to its title/name/url (needed for the bar chart's clickable labels, D2). **None of this
changes** — the v2 templates/JS consume the exact same `data` dict shape.

The XLSX export (`helpers/organization_helper.py:832-896`, `hdx_generate_organization_stats`) builds
an openpyxl workbook from a wider Mixpanel pull (`pageviews_downloads_per_organization_last_4_years`)
and fires `OrganizationStatsDownloadAnalyticsSender` (GA event `org stats download`) — unrelated to
the charts, unchanged by this task, but its permission-gated UI must stay on the page (D4).

### 1.3 Templates

- `organization/stats.html` — extends `organization/read_v1_base.html` (v1 shell/header/tabs).
  Embeds all chart data as hidden-div JSON (`h.json_dumps(...)`) for `#stats-data-single-dataset-*`,
  `#stats-data-pageviews`, `#stats-data-top-downloads`; renders the XLSX permission gate; two chart
  sections ("Number of Downloads" → `#chart-data-top-downloads`, "Downloads and Total Page Views" →
  `#chart-data-pageviews`) each paired with topline KPI card(s).
- `organization/custom_stats.html` — extends `stats.html`, overrides only the branded-header block
  and injects custom-style LESS; no chart-specific differences.

### 1.4 Charting — C3.js (D3-based), fully server-rendered, zero AJAX

Bundle wiring (`fanstatic/webassets.yml`): `charting-scripts` (`vendor/d3/d3.js`, `vendor/c3/c3.js`,
`vendor/maplibregl/...`), `charting-styles` (`vendor/c3/c3.css`, ...), `organization-stats-scripts`
(`organization_/stats.js`, `datasets/stats-chart.js`).

**Chart A — Downloads/pageviews line chart** (`organization_/stats.js`, `configPageviews`):
C3 `type: 'line'`, timeseries x-axis, two series (`pageviews`, `downloads`) from
`stats_dw_and_pv_per_week` (24 weekly points), `bindto: "#chart-data-pageviews"`. Uses C3 `regions`
to render the most recent point as a dashed segment.

**Chart B — Top-downloads bar chart** (`organization_/stats.js`, `configTopDownloads`): C3
`type: 'bar'`, `axis.rotated: true` (horizontal), one bar per dataset from
`stats_top_dataset_downloads` (≤25 datasets), `bindto: "#chart-data-top-downloads"`.
- Custom tooltip formatter computing each dataset's % of `stats_total_downloads`.
- `onrendered`/`onresized` hook (`substituteDatasetNamesWithLinks`) replaces C3's auto-generated
  y-axis tick `<text>` with real `<a>` elements linking to each dataset's page, via raw D3 selection
  `.html()` injection.
- Mouse-wheel zoom/pan (`enableMouseWheelZoom`) manipulating C3's internal, undocumented
  `chart.internal.brush` API directly.
- **Special case:** if the org has exactly 1 dataset, this whole bar chart is replaced by a call to
  `setupDatasetDownloads(...)` (shared helper, below) rendering a single-series line chart of that
  dataset's weekly downloads instead.

**Shared helper — `fanstatic/datasets/stats-chart.js`, `setupDatasetDownloads`**: a C3 `type: 'line'`
monthly-tick chart with a dynamically computed "nice" y-axis max. Used in **two** places today: (a)
the org stats page's single-dataset special case above, and (b) the dataset page's own
`#dataset-downloads-chart` (a per-dataset download-trend widget). Per D3, both consumers migrate to
Chart.js together in this task.

All chart data is embedded server-rendered JSON — no AJAX/API calls exist in either JS file.

### 1.5 Analytics

No tracking on chart views/interactions or the tab itself. The only stats-page analytics event is
the XLSX download (`org stats download`, §1.2) — out of scope for this task, but its trigger must
keep firing once the permission-gated UI is re-placed (D4).

### 1.6 FAQ

V1 has 3 identical "?" badges, all linking to
`/faq#auto-faq-Organisations-Where_can_I_see_how_popular_an_organisation_s_datasets_are_-a`. Figma
replaces all three with a single "See documentation" text link. Per D1, that link now points to
`https://docs.humdata.org/publish/publish-data/organizations-on-hdx#understanding-how-your-data-on-hdx-is-used`
— a real, externally-hosted HDX docs page, not the old in-site FAQ anchor.

---

## 2. Figma Mapping

### XL (`xl-org-stats-page.html`)

- Standard header/tabs shell, identical to 056/057's precedent; Stats tab active.
- `.stats-accordion` header row: bold "Stats" title + "See documentation" link (D1) + a static
  (non-functional) chevron — same non-collapsible treatment 057 chose for Activity (§7).
- 3 topline/KPI cards: total downloads, unique downloaders (last 30 days), unique viewers (last 30
  days) — a 1:1 visual match for `stats_total_downloads`/`stats_downloaders`/`stats_viewers`.
- Top-downloads section: a static mock of a horizontal bar chart — dataset name labels down the left
  (real HDX dataset titles used as filler), value-axis ticks 0–900 in steps of 100, bars as
  absolutely-positioned divs. This is a **static mock only** — no zoom/pan or link-click affordance
  is shown (that's precisely why D2 was asked and decided explicitly, rather than inferred from
  Figma).
- Downloads/pageviews section: a static mock of a dual-series line/area chart — y-axis ticks
  covering both series' scale, x-axis month labels (7 months shown), a legend ("Page views" /
  "Downloads" with color swatches), and a **static tooltip mock** (date + both values) — this
  tooltip is the exact visual spec to replicate in the Chart.js tooltip callback.
- No FAQ badges anywhere in this export — confirms D1's replacement is total, not additive.
- No admin/XLSX-export UI is depicted anywhere in this export (confirms D4 is filling a genuine
  Figma gap, not missing something that's actually there).

### MD (`md-org-page.html`, Stats section only) / SM (`sm-org-page.html`, Stats section only)

Same content as XL — identical 3 KPI cards, identical 2 charts, identical "See documentation" link —
embedded within the full-page export's Stats accordion section. No separate MD/SM stats-only export
exists (the same gap 057 hit for Activity); this doc scopes to reading only the Stats section out of
each full-page file. No breakpoint-specific interaction differences are visible in the static mocks;
per §7, resizing/stacking behavior for the charts themselves is inferred from Chart.js's standard
responsive behavior plus the existing v2 breakpoint tokens, not from anything Figma depicts
explicitly.

### Dataset-page chart (supplementary, for the D3 side-migration)

No dedicated Figma export for `#dataset-downloads-chart` exists yet. `dataset-page-xl.html` contains
only download-count badges (e.g. "1.7k+ downloads", "Download (14.2K)" repeated list rows), not a
chart mock. `dataset-chart.svg`, `org-chart1.svg`, `org-chart2.svg` are raw Figma vector exports —
text is baked in as glyph paths rather than real DOM/CSS, which makes them effectively opaque to
direct inspection (no chart type, axis values, or labels can be reliably extracted from the path
data). Per D5, this doc proceeds without a decoded Figma spec for that chart: the Chart.js
replacement should visually match the **current C3.js chart's existing styling** as closely as
possible, and a clean chart-only export (HTML/CSS, not raw SVG) should be requested before
implementation begins if pixel-level Figma fidelity is required there.

---

## 3. Chart Inventory

| # | Chart | Type (current) | Data structure | Current implementation | Required Chart.js output |
|---|---|---|---|---|---|
| A | Downloads & page views | C3 `line`, timeseries, 2 series | `stats_dw_and_pv_per_week`: 24× `{date, pageviews, downloads}` | `organization_/stats.js` `configPageviews`; dashed-segment region for most recent point | Chart.js `line`, 2 datasets, `segment` styling callback for the last point, tooltip showing both series per date (matches Figma's static tooltip mock, §2), legend matching Figma swatches |
| B | Top downloads (bar) | C3 `bar`, `axis.rotated` (horizontal) | `stats_top_dataset_downloads`: ≤25× `{dataset_id, name, url, value, total}` | `organization_/stats.js` `configTopDownloads`; DOM-injected `<a>` axis labels; undocumented-API zoom/pan; % tooltip | Chart.js horizontal bar; custom tick-drawing + click hit-testing plugin for clickable dataset links (D6, canvas has no native `<a>`); zoom/pan via vendored `chartjs-plugin-zoom` (D7); tooltip % formatter preserved (D2); long dataset names truncated with ellipsis, full name in tooltip (D8) |
| C | Single-dataset downloads (org, conditional) | C3 `line`, monthly ticks | `stats_1_dataset_downloads_last_weeks` (weekly series for the org's one dataset) + dynamically computed "nice" y-max | `datasets/stats-chart.js` `setupDatasetDownloads`, invoked from the org bar-chart's single-dataset branch | Chart.js `line`, same "nice max" tick logic ported, same shared function reused from both call sites (D3) |
| D | Dataset page downloads | C3 `line`, monthly ticks | Same shape as C, per-dataset weekly download series | Same `setupDatasetDownloads` helper, invoked from the dataset page template | Same Chart.js implementation as C — literally the same function, second call site (D3) |

---

## 4. Chart Migration Strategy

- **All four charts live in one module, `fanstatic/v2/charts.js`**: `setupDatasetDownloads` (Charts C & D,
  D3), the Chart A/B builders (`initPageviewsChart`/`initTopDownloadsChart`), and the dataset-page call
  site. All read the exact same embedded-JSON hidden divs (`#stats-data-pageviews`,
  `#stats-data-top-downloads`, `#stats-data-single-dataset-*`, `#dataset-downloads-data`) — **no
  template-side data reshaping**, only the JS consuming that JSON changes.
- Initialization is a plain vanilla-JS self-invoking init on page load — not a CKAN `ckan.module`, since
  chart init has no dependency on CKAN's module-binding lifecycle. `charts.js` detects which chart
  containers are present rather than being called into explicitly, so pages just load the bundle.
- Chart B's two custom interactions (D2) are the highest-risk migration items:
  - **Clickable axis labels:** Chart.js renders tick labels on canvas, so there is no DOM node to
    turn into an `<a>`. Per D6, this is built as a custom Chart.js tick-drawing + click-hit-testing
    plugin rather than an HTML-overlay layer — the plugin owns both drawing the tick label and
    hit-testing clicks against each bar's rendered position.
  - **Zoom/pan:** Chart.js has no built-in zoom/pan. Per D7, the community `chartjs-plugin-zoom`
    plugin is vendored (not a hand-rolled wheel handler) — the same way as Chart.js itself (§6) since
    there's no npm pipeline to pull it from a registry.

---

## 5. Styling Strategy

- Chart colors, fonts, and gridline styling are driven from v2 design tokens — spacing via
  `var(--hdx-space-N)`, typography via the existing `.hdx-body-*` mixins where applicable to
  surrounding labels/legends, and chart-specific colors (bar fill, line stroke, dashed-segment color)
  read from the same CSS custom properties the rest of v2 uses, rather than hardcoded hex values
  scattered through the JS.
- The legend and tooltip are **not** left in Chart.js's default look — both get bespoke DOM/CSS to
  match Figma's mock exactly (§2's swatches and tooltip layout), using Chart.js's
  `plugins.legend.display: false` / custom tooltip `external` callback pattern so the legend and
  tooltip are real styled HTML rather than Chart.js's canvas-drawn defaults. This mirrors how v1's
  C3 tooltip formatter already fully customized tooltip content — the new implementation keeps that
  level of control.
- New LESS added under the v2 architecture (task 021's structure), not the legacy
  `organization_/stats.less` — the legacy file is superseded, not extended, once the templates move
  off `read_v1_base.html`.
- `charts.js` reads tokens with no fallback literal (`token(name)`); `tokenPx(name)` converts a rem
  token to a px number for the few numeric Chart.js fields that need one (tick font size, bar
  thickness/radius, tooltip offset). Chart-tuning numbers with no token equivalent (point radius,
  stroke width, dash pattern, zoom window, max label width) stay as named constants.

---

## 6. Integration Strategy

- **Vendoring:** Chart.js is vendored as a committed UMD build under `fanstatic/v2/chartjs/` —
  `chart.umd.js` (4.5.0), `chartjs-plugin-zoom.min.js` (2.2.0, D7), and the self-contained
  `chartjs-adapter-date-fns.bundle.min.js` (D12; the thin, non-bundle adapter build needs a separate
  `dateFns` global this repo doesn't vendor, so it isn't used). Registered in `webassets.yml` as
  `v2-chart-scripts`, which also carries `v2/charts.js` — vendor libraries and the page code that
  consumes them ship as one bundle.
- **Bundle lifecycle:** the old `charting-scripts`/`charting-styles` (d3+c3) bundle is left in place,
  unused by any v2 page — confirmed by grep that no template still loads it for the pages this task
  touches (§8).
- **Template wiring:** `organization/stats.html` loads `v2-chart-scripts` only. `package/hdx_read.html`
  loads `v2-chart-scripts` + `v2-dataset-page-scripts` (the latter is just `v2/dataset-page.js`'s
  accordion logic).
- **Lifecycle:** load → Chart.js bundle parses on page load → the page's own init script reads the
  embedded JSON hidden divs → constructs each `new Chart(ctx, {...})` → no update/refetch lifecycle
  is needed since there's no AJAX (matches v1 exactly — chart state is fully determined at page
  render time).

---

## 7. Responsive Strategy

| Breakpoint | Chart container | Chart behavior | Legend/labels |
|---|---|---|---|
| XL (≥ 80rem) | Full-width section per Figma | Chart.js `responsive: true`, fixed aspect ratio matching Figma's chart dimensions | Legend to the side/top per Figma swatch placement (§2) |
| MD (< 80rem, ≥ 48rem) | Same section, narrower | Chart.js resizes via its own `resize` handling — no custom JS needed beyond default `responsive` behavior | Legend may wrap/stack — exact behavior TBD at implementation, no MD-specific mock exists beyond what's embedded in the full-page export (§2) |
| SM (< 48rem) | Narrowest, likely stacked KPI cards above chart | Same `responsive: true` handling; bar chart's y-axis label width (dataset names) is the main squeeze risk given D2's clickable-label requirement | Legend stacks vertically if it doesn't fit one row |

Tabs-row overflow behavior at SM is unchanged — reuses 056's existing `.c-tabs`/`.c-tab` solution,
not re-decided here.

---

## 8. Risks

| Risk | Mitigation / Note |
|---|---|
| Breaking chart data accuracy during the C3→Chart.js port | No data-shape changes (§1.2, §4) — only the rendering library changes; the embedded-JSON contract is preserved byte-for-byte |
| Breaking the XLSX-export analytics event | Unrelated to charts but lives on the same page/template — the permission-gated UI and its trigger must be carried over verbatim when re-placing it near the header row (D4) |
| No built-in Chart.js zoom/pan | Requires vendoring `chartjs-plugin-zoom` (D7, §4, §6) — genuinely more implementation work than the feature it replaces |
| Canvas has no native clickable text | Clickable axis labels (D2) require a custom tick-drawing + hit-testing plugin (D6, §4) — flagged as the single highest-effort item in this migration |
| Shared single-dataset helper touches the dataset page | Explicitly in scope per D3, but it means this "org page" task's testing surface includes the dataset page's stats widget too — must be verified on both surfaces before considering this task done |
| No Figma export for the dataset-page chart | D5 — proceeding on "match current visual styling"; a clean chart-only export would still reduce risk before implementation starts |
| Stale/unused old chart bundle | Confirmed by grep: `charting-scripts`/`charting-styles` (d3+c3) and `organization-stats-scripts` are not loaded by any template (§6) — left in place rather than deleted, since removing dead code wasn't in scope for this task |

---

## 9. Edge Cases

| Case | Expected behavior |
|---|---|
| Org with zero datasets / no download data | Existing v1 guard behavior (chart sections presumably hidden or empty-state) — no new empty-state copy is introduced by this task; carry over whatever v1 currently does unchanged |
| Org with exactly 1 dataset | Bar chart (Chart B) is replaced by the single-dataset line chart (Chart C) exactly as v1 does today — this branch condition is unchanged |
| Very long dataset names on the bar-chart y-axis | Not addressed in Figma's mock (filler names are all short); per D8, truncated with an ellipsis at a fixed max label width, with the full dataset name available via the tooltip |
| Datasets tied on download count | No special handling in v1 or Figma — order/tie-break behavior (if any) comes from the existing Solr/JQL sort, unchanged |
| Non-admin / logged-out viewer | XLSX prompt shows the "log in" copy instead of the download link, per existing permission gate (D4) — unchanged logic, just re-placed visually |
| JS disabled | No fallback chart rendering exists in v1 (chart divs would simply stay empty) — this task does not introduce a no-JS fallback, matching current behavior |

---

## Decisions Taken

| # | Decision | Rationale |
|---|---|---|
| D1 | The "See documentation" link (replacing v1's 3 FAQ badges) points to `https://docs.humdata.org/publish/publish-data/organizations-on-hdx#understanding-how-your-data-on-hdx-is-used` | Requester's explicit choice — the task brief's own FAQ-link reference was a broken placeholder, not a usable URL |
| D2 | Both v1 chart interactions on the top-downloads bar chart — mouse-wheel zoom/pan and clickable dataset-name axis labels — are preserved, rebuilt in Chart.js via custom plugin/overlay work, even though neither appears in Figma's static mock | Requester's explicit choice, prioritizing "preserve all interactions" over "match Figma exactly" where the two constraints conflict |
| D3 | The shared single-dataset line-chart helper (`setupDatasetDownloads`) is migrated to Chart.js for **both** consumers — the org stats page's single-dataset branch and the dataset page's own `#dataset-downloads-chart` — rather than forked so only the org page changes | Requester's explicit choice; avoids leaving one codepath on C3.js and the other on Chart.js indefinitely |
| D4 | The admin-only XLSX export link/permission-gated prompt is preserved and placed near the "Stats"/"See documentation" header row, since Figma has no dedicated slot for it | Requester's explicit choice over dropping it or treating it as a separate/legacy feature |
| D5 | No decoded Figma spec exists for the dataset-page chart (Chart D); this doc proceeds on "match current C3.js visual styling," with a note that a clean chart-only export would still help before implementation | The only material offered (`dataset-page-xl.html`, raw `.svg` crops) doesn't yield a reliable chart-level spec — glyph-path SVGs aren't practically decodable, and the HTML export contains only download-count badges, not the chart itself |
| D6 | Chart B's clickable dataset-name axis labels are built as a custom Chart.js tick-drawing + click-hit-testing plugin, not an HTML-overlay layer | Requester's explicit choice, overriding this doc's earlier lower-risk lean toward the overlay approach |
| D7 | Chart B's drag-pan uses the vendored community `chartjs-plugin-zoom` plugin; wheel input shifts the same fixed-size window without ever resizing it (no scale-changing zoom), via a small hand-rolled handler ported from v1's `enableMouseWheelZoom` approach | Requester's explicit choice — wheel-triggered zoom (resizing the visible range) produced a confusing view; matching v1's actual fixed-window-pan behavior was preferred over the plugin's resizing wheel-zoom |
| D8 | Very long dataset names on Chart B's y-axis are truncated with an ellipsis at a fixed max label width, with the full name available via tooltip | Requester's explicit choice, resolving the edge case Figma's mock (all-short filler names) left unaddressed |
| D9 | Line-chart series colors: Page views = `--hdx-primary-5` (#1862d8), Downloads = `--hdx-primary-2` (#a3c0ef) | Requester's explicit choice — the legend swatches in every Figma export are flattened `<img>`s, so the mapping wasn't extractable from the exports |
| D10 | KPI copy: no "Last 30 days" sublabel on the total-downloads card (per the XL export; the value is all-time), but the MD/SM "…from this organisation" wording is used at all breakpoints | Requester's explicit choice, resolving a conflict between the XL and MD/SM exports (MD/SM wrongly show "Last 30 days" under the all-time total) |
| D11 | Custom orgs unified: the stats view renders one template for standard + custom orgs (056/057 precedent); `custom_stats.html` is left orphaned on disk | Requester's explicit choice, overriding this doc's earlier keep-the-branch position (§1.1) |
| D12 | `chartjs-adapter-date-fns.bundle.min.js` (self-contained build) is vendored so charts use Chart.js's native time scale | Requester's explicit choice over a category-axis workaround that would have avoided the extra vendored file |
| D13 | Chart.js + plugins vendored under `fanstatic/v2/chartjs/` in a `v2-chart-scripts` bundle, which also carries the page JS, `v2/charts.js`; `v2/dataset-page.js` keeps only its non-chart accordion logic (v1 `organization_/stats.js` and `datasets/stats-chart.js` are left untouched/orphaned, not rewritten in place) | Requester's explicit choices — v1 bundles/files stay untouched, and v1 `dataset-scripts` is dropped from the v2 dataset page (its only live role there was the C3 chart; its other handlers target markup that no longer exists) |
| D14 | The three KPI stat cards are a new `c-stats-card` component (borderless white card, semibold label, optional sublabel, 24px body-font value) | Requester's explicit choice over reusing/extending the visually-different `c-kpi-card` |
| D15 | Chart tooltips reuse the existing `c-tooltip--graph` component — template-rendered per chart, driven by a Chart.js external-tooltip handler; call sites must pass a non-empty `graph_title` so the date/title row renders (an empty value silently removes `.c-tooltip__text` from the DOM, breaking the tooltip's date display) | Requester pointed at the already-implemented tooltip component instead of introducing a new one |
| D16 | Bar-chart dataset labels render as dark text (per Figma) with a pointer cursor and primary-color hover, not v1's always-blue link color | Requester's explicit choice, keeping Figma's colors while preserving clickability (D2) |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/chartjs/` | **New** — vendored `chart.umd.js` (4.5.0), `chartjs-adapter-date-fns.bundle.min.js` (D12), `chartjs-plugin-zoom.min.js` (2.2.0, D7) |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/charts.js` | **New** — all four charts (A–D): `setupDatasetDownloads` (D3), `initPageviewsChart`/`initTopDownloadsChart`, clickable-label hit-test plugin (D6), zoom/pan (D7), single-dataset branch, dataset-page call site; token colors read with no fallback literal, `tokenPx()` for numeric px config |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/pages/dataset.js` | Chart-init code removed (now in `charts.js`, self-initializing); keeps only the section-accordion logic |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` | `v2-chart-scripts` carries the vendor libs + `v2/charts.js`; `v2-dataset-page-scripts` is just `v2/dataset-page.js`; `v2-components-styles` gains `stats-card.css`; all v1 bundles untouched (D13) |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/stats.html` | Replaced with the v2 template: `v2/page.html` shell + `org-hero.html` (Stats tab active), `c-stats-card` KPIs, chart cards, "See documentation" link (D1), re-placed XLSX prompt (D4) |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py` | `stats()` unified for standard + custom orgs (D11); fetches `datasets_num` for the hero stats |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/stats-card.html` | **New** — `c-stats-card` component (D14) |
| `ckanext-hdx_theme/.../hdx-styles/src/common/less/v2/components/stats-card.less` | **New** — `c-stats-card` styles (D14) |
| `ckanext-hdx_theme/.../hdx-styles/src/common/less/v2/pages/org.less` | Stats-tab section added (`hdx-v2-org-stats*`): header/export row, KPI column/row per breakpoint, chart cards, legend |
| `ckanext-hdx_theme/.../hdx-styles/src/common/less/v2/layout.less` | `.hdx-v2-chart` canvas wrapper + `.hdx-v2-chart-tooltip` floating-tooltip utility (shared by org stats + dataset page) |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/hdx_read.html` | v1 `dataset-scripts` removed (D13); loads `v2-chart-scripts`; graph tooltip rendered in the downloads-chart block |
| Orphaned (left on disk, no longer loaded on v2 pages) | `organization/custom_stats.html` (D11), `fanstatic/organization_/stats.js`, `organization-stats-scripts`/`-styles` bundles; `datasets/stats-chart.js` remains only for v1 `dataset-scripts` consumers |
