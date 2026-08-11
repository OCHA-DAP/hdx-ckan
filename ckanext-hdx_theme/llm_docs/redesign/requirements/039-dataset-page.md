# Dataset Page v2 — Full Implementation

**Figma source**: `llm_docs/redesign/figma_exports/dataset-page-xl.html`, `dataset-page-md.html`, `dataset-page-sm.html`, `dataset-page-sm-open-dropdown.html`, `dataset-page-xl-interactive-data.html`

---

## Prerequisites

Already implemented (do not re-implement):
- `v2/page-header.html` — hero header (task 037)
- `v2/components/resource-card.html` — resource file card (task 038)
- `v2/components/breadcrumb.html` — breadcrumb (task 032)
- `v2/components/anchor-links.html` — desktop anchor nav list

---

## Template to modify

**Main file**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/hdx_read.html`

This extends `v2/page.html` and renders the v2 dataset header already. All new sections go here. No v2 feature gate — the dataset page is always v2.

---

## Section Breakdown

### 1. Breadcrumb

**Block**: `{% block toolbar %}` (overrides toolbarRow, same pattern as `search/search.html`)

```jinja
{% block toolbar %}
  <div class="hdx-v2-breadcrumb-row">
    {% snippet 'v2/components/breadcrumb.html',
        items=[
          {'label': pkg.organization.title, 'href': h.url_for('organization.read', id=pkg.organization.name)},
          {'label': pkg.title or pkg.name, 'href': ''}
        ] %}
  </div>
{% endblock %}
```

Path: **Home → [Organisation name] → [Dataset title (no link)]**

Remove existing `{% block breadcrumb_content %}` + nested `{% block breadcrum_parent_item %}`.

---

### 2. Dataset Header

**Block**: `{% block pre_primary %}` — **DO NOT MODIFY**. Already implemented in task 037.

Note: the `pre_primary` block output is wrapped in `<div class="hdx-v2-dataset-header-section">` as an outer row wrapper (following the `outer-row > hdx-v2-container > content` pattern).

---

### 3. Anchor Links Navigation (Sticky)

Both variants are rendered by a single snippet call in `{% block secondary_content %}` — `v2/dataset-page-anchor-nav.html` was not created. Instead, `v2/components/anchor-links.html` was extended with two new params:
- `heading {string}` — if set, wraps nav in `.c-anchor-links-wrapper` and renders the heading above the list
- `with_mobile_dropdown {bool}` — if true, also renders the mobile sticky dropdown after the desktop nav
- `mobile_only {bool}` — if true, renders **only** `.c-anchor-links-mobile` (no desktop nav or heading wrapper)

**Usage in `{% block secondary_content %}`** (desktop nav only — rendered inside sidebar which is hidden on SM/MD):
```jinja
{% block secondary_content %}
  {% snippet 'v2/components/anchor-links.html',
      items=ns.anchor_items,
      heading=_('Dataset details'),
      with_mobile_dropdown=False %}
{% endblock %}
```

**Mobile dropdown** — no new `v2/page.html` block was added; the mobile anchor dropdown renders inline at the top of `{% block primary %}` instead, outside the hidden sidebar:
```jinja
{% block primary %}
  {% snippet 'v2/components/anchor-links.html',
      items=ns.anchor_items,
      mobile_only=True %}
  …
{% endblock %}
```

The `{% block secondary_content %}` wraps in `.hdx-v2-dataset-sidebar` (XL+ only via CSS). The mobile dropdown (`.c-anchor-links-mobile`) is rendered separately at the top of `{% block primary %}`, outside the sidebar that is hidden on SM/MD.

**Desktop sidebar**:
- CSS class on wrapper: `hdx-v2-dataset-sidebar` (set via `sidebar_class`)
- Shown only at XL (≥80rem), hidden at MD/SM
- Content: "Dataset details" heading (`.c-anchor-links__heading`) + `c-anchor-links` list
- Sticky: `.c-anchor-links-wrapper { position: sticky; top: 4.5rem }` (in `anchor-links.less`)

**Mobile/tablet dropdown**:
- CSS class: `c-anchor-links-mobile` (styles in `anchor-links.less`)
- JS `data-module="anchor-dropdown"` on wrapper
- Hidden at XL, shown and sticky (`position: fixed; top: 7rem`) at MD/SM
- Pattern: button (`.c-anchor-links-mobile__toggle`) → toggled `<ul class="c-anchor-links-mobile__panel">` below

**Anchor items** (built with Jinja2 namespace trick). "Preview" is prepended only when `shapes` (set server-side, see §0 below) is truthy:
```jinja
{% set ns = namespace(anchor_items=(
  [{'label': _('Preview'), 'href': '#preview', 'active': True}] if shapes else []
) + [
  {'label': _('Data and resources'), 'href': '#data-and-resources', 'active': not shapes},
]) %}
{% if pkg.customviz %}
  {% set ns.anchor_items = ns.anchor_items + [{'label': _('Interactive data'), 'href': '#interactive-data', 'active': False}] %}
{% endif %}
{% set ns.anchor_items = ns.anchor_items + [{'label': _('Metadata'), 'href': '#metadata', 'active': False}] %}
{% if showcase_list %}
  {% set ns.anchor_items = ns.anchor_items + [{'label': _('Showcases'), 'href': '#showcases', 'active': False}] %}
{% endif %}
{% set ns.anchor_items = ns.anchor_items + [{'label': _('Activity'), 'href': '#activity', 'active': False}] %}
```

Showcases link is added **only when `showcase_list` is non-empty**. Interactive data link is added **only when `pkg.customviz` is truthy**.

**Section IDs** (must match href values):
- `#preview` (conditional)
- `#data-and-resources`
- `#metadata`
- `#showcases` (conditional)
- `#activity`

---

### 0. Preview Section (Conditional)

**Condition**: dataset has a resource in GIS format (`shp`/`geojson`/`kml`/`kmz`) with successfully-processed `shape_info` — detected server-side via `dataset_view_logic.has_shape_info()` (`ckanext-hdx_package/ckanext/hdx_package/controller_logic/dataset_view_logic.py`) and surfaced to the template as the `shapes` variable (JSON string), set in `ckanext-hdx_package/ckanext/hdx_package/views/dataset.py::read()`. **Always open** — no accordion. Rendered first, before "Data and resources".

```html
{% if shapes %}
  <section class="hdx-v2-dataset-section" id="preview">
    <div class="hdx-v2-dataset-section__header">
      <h2 class="hdx-v2-dataset-section__title">Preview</h2>
    </div>
    <div class="hdx-v2-dataset-section__body">
      <div id="mapbox-baselayer-url-div" style="display: none;">{{ h.hdx_generate_basemap_config_string() }}</div>
      <div id="shapeData" style="display: none;">{{ shapes }}</div>
      <div id="map" style="height: 400px; margin-bottom: 15px;"></div>
    </div>
  </section>
  <hr class="c-divider">
{% endif %}
```

The map itself (MapLibre GL — `fanstatic/v2/pages/shape-view.js`), its on-map hover info panel, and its layer-toggle control are pre-existing and untouched — only the v2 section wrapper/heading and anchor-nav wiring are new. Loads `hdx_theme/crisis-base-styles` (in `{% block styles %}`) and `hdx_theme/shape-view-scripts` (in `{% block scripts %}`) only when `shapes` is truthy.

Note: `package/hdx-read-shape.html` (the pre-v2 template that used to own this markup via an orphaned `pre_primary_content` block override) is no longer rendered by any controller path as of this change; kept in the repo unused.

---

### 4. Data and Resources Section

**Always open** — no accordion.

```html
<section class="hdx-v2-dataset-section" id="data-and-resources">
  <div class="hdx-v2-dataset-section__header">
    <h2 class="hdx-v2-dataset-section__title">
      Data and resources ({{ pkg.resources | length }})
    </h2>
  </div>
  <div class="hdx-v2-dataset-section__body">
    {# resource cards via resources_list.html #}
    {% snippet "package/snippets/resources_list.html",
        pkg=pkg,
        resources=pkg.resources,
        resource_item_snippet='package/snippets/resource_item_v2.html',
        list_tag='div',
        resource_list_classes='resource-list c-resource-card-list' %}
  </div>
</section>
```

**resources_list.html** renders `resource-card` items (task 038) — do not change its internals. Its `resource_list_classes` param defaults to `'hdx-bs3 resource-list'`; the v2 dataset page passes `'resource-list c-resource-card-list'` (the `resource-list` class stays for `hdx_resource_grouping.js`; `c-resource-card-list` owns the layout in `components/resource-card.less`).

---

### 5. Interactive Data (Conditional)

Condition: `pkg.customviz` is truthy. **Always open** — no accordion.

```html
{% if pkg.customviz %}
<section class="hdx-v2-dataset-section" id="interactive-data">
  <div class="hdx-v2-dataset-section__header">
    <h2 class="hdx-v2-dataset-section__title">Interactive Data</h2>
  </div>
  <div class="hdx-v2-dataset-section__body">
    {% snippet "package/snippets/custom_viz.html", customviz=pkg.customviz %}
  </div>
</section>
{% endif %}
```

Note: this section appears in the anchor nav (added when `pkg.customviz` is truthy).

---

### 6. Metadata Section

**Collapsible accordion**, default open.

```html
<section class="hdx-v2-dataset-section hdx-v2-dataset-section--collapsible is-open"
         id="metadata">
  <div class="hdx-v2-dataset-section__header"
       role="button" tabindex="0" aria-expanded="true" aria-controls="metadata-body">
    <h2 class="hdx-v2-dataset-section__title">Metadata</h2>
    <svg class="hdx-v2-dataset-section__chevron" .../>
  </div>
  <div class="hdx-v2-dataset-section__body" id="metadata-body">
    {# metadata fields inlined directly here — no separate snippet #}
  </div>
</section>
```

#### Metadata implementation notes

Metadata fields are inlined directly into `hdx_read.html`'s metadata section body. The template variable is `pkg` and a local `metadata_edit_mode` variable is used (avoids Jinja2 scope conflicts with `edit_mode`).

**CRITICAL: Preserve all `data-module="hdx-quick-edit"` attributes verbatim from `additional_info.html`.**

Field layout (v2 grid, not the old vertical list):

**Row 1** (3 columns at MD+, stacked at SM):
| Time period | Expected update frequency | Modified |

**Row 2** (3 columns at MD+, stacked at SM):
| Contributor | Source | Dataset added on HDX |

**Full-width fields** (stacked):
- Location (full list, no expand/collapse — `hdx_show_more` is not used in v2)
- Methodology (full text)
- Caveats / Comments (full text, via `h.render_markdown()`)
- License (non-requestdata only; full text for "Other" license)
- Field Names, File Types, Number of Rows (requestdata only)
- Topics/Tags — rendered as `{% snippet 'v2/components/label.html', color='grey', size='s', tag='a', ... %}` (`c-label` chips); wrapped in `.hdx-v2-dataset-metadata__value--tags` (flex/wrap)
- Visibility (editor-only toggle)
- Downloads chart → `div#dataset-downloads-data` + `div#dataset-downloads-chart`
- Export metadata links (JSON | CSV) at bottom

**Metadata strip alignment at XL**: The 4-item `__metadata` strip becomes a CSS grid (`grid-template-columns: calc(25% + var(--hdx-space-6)) repeat(3, 1fr)`), so item 2 (Expected update frequency) aligns with the content column (which sits after the 25% sidebar + gap).

Field variables (from `pkg`):
- `pkg.dataset_date` → `h.render_date_from_concat_str()`
- `pkg.data_update_frequency` → `h.hdx_get_frequency_by_value()`
- `pkg.last_modified` → `h.render_datetime()`
- `pkg.metadata_created` → `h.render_datetime()`
- `pkg.owner_org` / `pkg.organization`
- `pkg.dataset_source`
- `pkg.groups` (locations)
- `pkg.methodology` / `pkg.methodology_other` → `h.methodology_bk_compat()`
- `pkg.caveats` → `h.render_markdown()`
- `pkg.license_id` / `pkg.license_title` → `h.hdx_find_license_name()`
- `pkg.tags` (vocabulary tags and free tags)
- `pkg.private` (visibility)
- `pkg.is_requestdata_type` (hides/shows specific fields)

Downloads chart variables (passed separately from controller):
- `stats_downloads_last_weeks` → stored in `div#dataset-downloads-data`

---

### 7. Showcases Section (Conditional)

Condition: `showcase_list` is non-empty. **Collapsible accordion**, default open.

```html
{% if showcase_list %}
<section class="hdx-v2-dataset-section hdx-v2-dataset-section--collapsible is-open"
         id="showcases">
  <div class="hdx-v2-dataset-section__header"
       role="button" tabindex="0" aria-expanded="true" aria-controls="showcases-body">
    <h2 class="hdx-v2-dataset-section__title">Showcases</h2>
    <svg class="hdx-v2-dataset-section__chevron" .../>
  </div>
  <div class="hdx-v2-dataset-section__body" id="showcases-body">
    <div class="c-showcase-card-grid">
      {% for showcase in showcase_list %}
        {% snippet 'v2/components/showcase-card.html',
            title=showcase.title or showcase.name,
            description=h.markdown_extract(showcase.notes, extract_length=140),
            img_url=showcase.image_display_url or showcase.img_url,
            url=showcase.url or h.url_for('showcase_blueprint.read', id=showcase.name),
            read_more_href=h.url_for('showcase_blueprint.read', id=showcase.name),
            url_is_external=showcase.url | default(False) %}
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}
```

#### Showcase card: `v2/components/showcase-card.html`

New component template.

Parameters:
- `title` {string}
- `description` {string} — markdown-extracted excerpt
- `img_url` {string} — may be empty → show placeholder
- `url` {string} — primary action URL (may be external)
- `read_more_href` {string} — always the HDX showcase page
- `url_is_external` {bool} — adds `target="_blank"` on View button

Layout:
- Image (aspect-ratio 16/9, `object-fit: cover`)
- Body: title + description + actions
- Actions: primary `c-button` "View" + `c-text-link` "Read more"

Grid layout:
- LG/MD (≥48rem): 2 per row (`grid-template-columns: repeat(2, 1fr)`)
- SM (<48rem): 1 per row

---

### 8. Activity Section

**Collapsible accordion**, default closed. Stream is lazily AJAX-fetched on first expand, not rendered server-side.

```html
<section class="hdx-v2-dataset-section hdx-v2-dataset-section--collapsible"
         id="activity">
  <div class="hdx-v2-dataset-section__header"
       role="button" tabindex="0" aria-expanded="false" aria-controls="activity-body">
    <h2 class="hdx-v2-dataset-section__title">{{ _('Activity') }}</h2>
    <span class="hdx-v2-dataset-section__chevron" aria-hidden="true">{% include 'v2/icons/chevron-down.svg' %}</span>
  </div>
  <div class="hdx-v2-dataset-section__body" id="activity-body">
    <div class="dataset-activity-wrapper" data-fetched="false" data-dataset-id="{{ pkg.id }}">
      {% snippet 'v2/activity-stream.html', activity_stream=hdx_activities, id=pkg.id, object_type='package' %}
    </div>
  </div>
</section>
```

No "See more in your dashboard" link — dropped. `fanstatic/v2/pages/dataset.js` handles the lazy fetch via `hdx_package_activity_stream` on first expand.

---

## Block Structure in hdx_read.html

### Blocks to REMOVE:
- `{% block breadcrumb_content %}` (replaced by `{% block toolbar %}`)
- `{% block breadcrum_parent_item %}` (nested inside above)
- `{% block pre_primary_content2 %}` (customviz moves into `primary` block)

### Blocks to ADD:
- `{% block toolbar %}` — v2 breadcrumb (Home → Org → Title)

### Blocks to CHANGE:
- `{% block secondary_content %}` — was metadata/showcases/activity → now anchor nav sidebar (desktop only)
- `{% block primary %}` — was resource list only → now all content sections, plus the mobile anchor dropdown rendered inline at the top (no new `v2/page.html` block was added for it)

### Blocks to KEEP UNCHANGED:
- `{% block pre_primary %}` — dataset-page-header (task 037)
- All analytics blocks (lines 43–55): `analytics_org_name`, `analytics_org_id`, `analytics_is_cod`, `analytics_is_indicator`, `analytics_is_archived`, `analytics_group_names`, `analytics_group_ids`, `analytics_dataset_name`, `analytics_dataset_id`, `analytics_dataset_availability`, `analytics_came_from`, `analytics_supports_notifications`, `analytics_supports_tabular_data_endpoints`
- `{% block head_extras %}` — structured data (schema.org ld+json)
- `{% block subtitle %}`, `{% block meta %}`, `{% block links %}`

### Template variables to set (at top):
```jinja
{% set sidebar_class    = 'hdx-v2-content-columns__sidebar hdx-v2-content-columns__sidebar--xl-only hdx-v2-dataset-sidebar' %}
{% set content_class    = 'hdx-v2-content-columns__content' %}
{% set outer_row_class  = 'hdx-v2-dataset-row' %}
{% set columns_class    = 'hdx-v2-content-columns--gap-xl' %}
```

`columns_class` adds the generic `--gap-xl` modifier to the `hdx-v2-content-columns` flex container in `page.html` (XL-only gap). Sidebar/content layout comes from the generic `__sidebar --xl-only` / `__content` classes in `layout.less`; `hdx-v2-dataset-sidebar` holds only page-specific padding.

### Notification modal (stays in primary block):
```jinja
{% snippet "notification_platform/modals.html",
    object_type=object_type,
    object_id=object_id,
    object_name=object_name,
    object_dict=pkg,
    update_frequency=h.hdx_get_frequency_by_value(pkg.data_update_frequency),
    unsubscribe_token=unsubscribe_token,
    unsubscribe_token_validated=unsubscribe_token_validated,
    unsubscribe_email=unsubscribe_email,
    unsubscribe_token_invalidate=unsubscribe_token_invalidate %}
```

---

## JavaScript

Anchor/scroll logic and accordion logic are split into two files.

### `fanstatic/v2/components/anchor-links.js` — in `v2-components-scripts` (loaded globally)

All anchor nav interactivity. Functions:

#### `initSmoothScroll()`

Intercepts clicks on `.c-anchor-links__item` and `.c-anchor-links-mobile__item`.

Scroll behavior:
- `e.preventDefault()`
- Find target element by `href` attribute (must match section `id`)
- Compute offset via `getStickyOffset()`: adds navbar height and mobile-nav height only when those elements have `position: sticky` or `position: fixed` (does not add them unconditionally)
- Custom `requestAnimationFrame` loop:
  - Duration: **500ms**
  - Easing: `easeInOutCubic(t) = t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3) / 2`
- After scroll: close mobile dropdown if open

#### `initAnchorDropdown()`

Targets `[data-module="anchor-dropdown"]`.

- Toggle button (`.c-anchor-links-mobile__toggle`): toggles `aria-expanded`, toggles `hidden` on panel
- Click outside: close panel
- Click on list item: close panel, update button label text to clicked item's text

#### `initActiveTracking()`

Uses `IntersectionObserver` on `.hdx-v2-dataset-section[id]` elements.

- When section crosses threshold: update active state on both `.c-anchor-links__item` (desktop) and `.c-anchor-links-mobile__item` (mobile)
- Update `.c-anchor-links-mobile__label` text to reflect active section
- Active class: `c-anchor-links__item--active` / `c-anchor-links__item--inactive`, `aria-current="true"`

---

### Info icon tooltip pattern

Used in both `page-header.html` (header metadata strip) and the inlined metadata fields in `hdx_read.html`.

**Template**:
```jinja
<span class="c-info-icon" tabindex="0" aria-label="{{ _('More info about ...') }}">{% include 'v2/icons/info-circle.svg' %}</span>
{% snippet 'v2/components/tooltip.html', variant='dark', arrow='', text=_('...') %}
```

**CSS** — `.c-info-icon` (in `label.less`, follows BEM `c-` convention): `display: inline-flex; align-items: center; color: var(--hdx-neutral-85); cursor: pointer; flex-shrink: 0; svg { 0.875rem × 0.875rem }`.

**Tooltip wrapper** — `.c-tooltip-anchor` (generic reusable class in `label.less`) wraps the icon + tooltip pair.

**Tooltip trigger** — CSS hover + JS `.is-open` class for tap (mobile):
```less
.c-info-icon:hover ~ .c-tooltip,
.c-info-icon:focus-visible ~ .c-tooltip,
.c-info-icon.is-open ~ .c-tooltip { display: block; }
```

**Tooltip positioning** — right-anchored to prevent overflow: `right: 0; left: auto; transform: none`.

**Alignment**:
- Header (`page-header.less` `.c-tooltip-anchor`): `margin-left: auto` — right-aligned in label-row.
- Metadata section: no `margin-left: auto` — left-aligned immediately after label text.

**JS** — `page-header.js` adds/removes `.is-open` on `.c-info-icon` on click; queries `.c-tooltip-anchor` for wrapper; document click closes all.

---

### `fanstatic/v2/pages/dataset.js` — in `v2-dataset-scripts`

Contains **only section accordion logic** (all anchor/scroll logic is in `anchor-links.js` above).

#### `initSectionAccordions()`

Targets `.hdx-v2-dataset-section--collapsible .hdx-v2-dataset-section__header`.

- Click, Enter, Space: toggle `.is-open` on parent `section`, toggle `aria-expanded`
- CSS handles chevron rotation and `body` visibility (`display: none` when not `.is-open`)

---

## CSS: `fanstatic/v2/pages/dataset.css`

Compiled from LESS source at `hdx-styles/src/common/less/v2/pages/dataset.less`.
Register in new `v2-dataset-styles` bundle (preloads `v2-page-styles`).

### Layout classes

```css
/* Ensure flex layout — hdx-v2-content-columns is defined in search.css, not page-styles */
.hdx-v2-content-columns {
    display: flex;
    align-items: stretch;
}

/* Anchor nav sidebar — generic layout classes (layout.less) */
.hdx-v2-content-columns__sidebar.hdx-v2-content-columns__sidebar--xl-only {
    /* XL+: 25% sidebar; MD/SM: hidden */
}

/* Main content area — generic layout class (layout.less) */
.hdx-v2-content-columns__content {
    flex: 1;
    min-width: 0;
}
```

At XL (≥80rem): the generic `__sidebar` class gives 25% width (percentage, not fixed rem); `--xl-only` hides it at MD/SM. `.hdx-v2-dataset-sidebar` adds only `padding: var(--hdx-space-12) 0` at XL. The search sidebar uses the same generic classes plus its page-specific border-right/padding.

### Anchor nav (desktop + mobile) — in `anchor-links.less`, NOT in `dataset.less`

Desktop wrapper and heading:
```
.c-anchor-links-wrapper — position: sticky; top: 4.5rem
.c-anchor-links__heading — uppercase label above the list (semibold, neutral-85, xs)
```

Mobile dropdown:
```
.c-anchor-links-mobile
  — display: none by default; display: block at max-width < @hdx-bp-xl
  — position: fixed; top: 7rem; left: 0; right: 0; z-index: 200
  — border-bottom: 1px solid neutral-2
  __toggle — full-width button, flex, space-between; data-module="anchor-dropdown"
  __label  — current section name
  __chevron — rotates 180deg when open (transition 0.2s)
  __panel  — list, background white, hidden attribute toggled by JS
  __item   — hover state; is-active class for active section
```

### Layout wrapper

```
.hdx-v2-content-columns--gap-xl (generic, layout.less)
  — XL+: gap: var(--hdx-space-6)          // 1.5rem flex gap between sidebar and content
```

### Section wrapper

Sections are separated by `<hr class="c-divider">` between adjacent sections — **no `border-top`** on sections.

```
.hdx-v2-dataset-section
  — padding: space-10 0 (MD+), space-6 0 (SM)   // no border-top
  __header — flex, space-between, align-center
           — cursor: default (always-open) or pointer (collapsible)
  __title  — h2, display font, semibold, neutral-95
  __chevron — transition: transform 0.2s; rotates 180deg when NOT .is-open
  __body   — padding-top: space-8

.hdx-v2-dataset-section--collapsible:not(.is-open) .hdx-v2-dataset-section__body {
    display: none;
}
.hdx-v2-dataset-section--collapsible:not(.is-open) .hdx-v2-dataset-section__chevron {
    transform: rotate(180deg);
}
```

### Metadata grid

```
.hdx-v2-dataset-metadata
  __grid — display: grid; grid-template-columns: repeat(3, 1fr); gap: space-6 (MD+)
           SM: grid-template-columns: 1fr; gap: space-4
  __cell / __full — display: flex; flex-direction: column; gap: space-1
  __label — .hdx-heading-h4(), neutral-85
  __label-row — flex row, gap: space-1
```

### Showcase grid

`.c-showcase-card-grid` (component-owned, in `components/showcase-card.less`):
```
  — display: grid; gap: space-6
  — grid-template-columns: repeat(2, 1fr) (MD+)
  — grid-template-columns: 1fr (SM < 48rem)
```

`.c-showcase-card` styles live in `hdx-styles/src/common/less/v2/components/showcase-card.less` (compiled to `fanstatic/v2/components/showcase-card.css`, registered in `v2-components-styles`):
```
  — border: 1px solid neutral-2; border-radius: radius-md; overflow: hidden
  __image — width: 100%; aspect-ratio: 16/9; overflow: hidden
  __img — width: 100%; height: 100%; object-fit: cover
  __image-placeholder — background: neutral-1; width: 100%; height: 100%
  __body — padding: space-4; display: flex; flex-direction: column; gap: space-3
  __title — font: semibold, m, neutral-95
  __desc  — font: regular, s, neutral-85
  __actions — display: flex; gap: space-2; align-items: center; margin-top: auto
```

### Activity section

No v2-specific CSS overrides. The `activity_stream.html` snippet provides its own markup and styling. Section padding comes from the shared `.hdx-v2-dataset-section` rules only.

---

## webassets.yml additions

`v2-components-scripts` gets `v2/components/anchor-links.js` (after `page-header.js`).
`v2-components-styles` gets `v2/components/showcase-card.css` (after `selection.css`).

After `v2-search-scripts` block:

```yaml
v2-dataset-styles:
    output: %(version)s_v2-dataset-styles.css
    preload: v2-page-styles
    contents:
        - v2/dataset.css

v2-dataset-scripts:
    output: %(version)s_v2-dataset-scripts.js
    preload: v2-page-scripts
    contents:
        - v2/dataset.js
```

Load in `hdx_read.html`:
```jinja
{% block styles %}
  {{ super() }}
  {% asset 'hdx_theme/v2-dataset-styles' %}
{% endblock %}

{% block scripts %}
  {{ super() }}
  {% asset 'hdx_theme/v2-dataset-scripts' %}
{% endblock %}
```

---

## Analytics Preservation (CRITICAL)

These blocks in `hdx_read.html` (lines 43–55) must NOT be touched:

```
{% block analytics_org_name %}
{% block analytics_org_id %}
{% block analytics_is_cod %}
{% block analytics_is_indicator %}
{% block analytics_is_archived %}
{% block analytics_group_names %}
{% block analytics_group_ids %}
{% block analytics_dataset_name %}
{% block analytics_dataset_id %}
{% block analytics_dataset_availability %}
{% block analytics_came_from %}
{% block analytics_supports_notifications %}
{% block analytics_supports_tabular_data_endpoints %}
```

These feed Mixpanel. Do NOT rename, remove, or restructure them.

---

## Jinja2 Block Safety Rules

### DO NOT duplicate these blocks (defined in `v2/page.html`):
- `secondary`, `primary`, `pre_primary`, `post_primary`
- `breadcrumb`, `breadcrumb_content`, `toolbar`
- `scripts`, `styles`

### Jinja2 list building (namespace trick):
```jinja
{% set ns = namespace(items=[...]) %}
{% if condition %}
  {% set ns.items = ns.items + [{...}] %}
{% endif %}
```
Standard `{% set items = items + [...] %}` fails in Jinja2 due to scoping — use namespace.

---

## Files Affected

### New Files

| File | Type | Notes |
|------|------|-------|
| `templates/v2/components/showcase-card.html` | Jinja template | Showcase card component |
| `fanstatic/v2/components/anchor-links.js` | JavaScript | Smooth scroll, anchor dropdown, active tracking (in `v2-components-scripts`) |
| `fanstatic/v2/pages/dataset.js` | JavaScript | Section accordions only (in `v2-dataset-scripts`) |
| `fanstatic/v2/pages/dataset.css` | CSS | Dataset page styles |
| `fanstatic/v2/components/showcase-card.css` | CSS | Showcase card component styles |
| `hdx-styles/src/common/less/v2/pages/dataset.less` | LESS | Source for `dataset.css` |
| `hdx-styles/src/common/less/v2/components/showcase-card.less` | LESS | Source for `showcase-card.css` |

### Files to Modify

| File | Change |
|------|--------|
| `templates/package/hdx_read.html` | Full restructure per block breakdown above; `columns_class`; inlined metadata fields; `<hr class="c-divider">` between sections; conditional Preview section (§0) + anchor-nav entry for GIS/geo-preview datasets |
| `ckanext-hdx_package/ckanext/hdx_package/views/dataset.py` | `read()`: geo-preview branch now `break`s instead of `return render('package/hdx-read-shape.html', ...)`, falling through to the normal `hdx_read.html`/`custom_hdx_read.html` render with `shapes` set in `template_data` |
| `templates/v2/page.html` | Support `columns_class` on `hdx-v2-content-columns` |
| `templates/v2/components/page-header.html` | Tooltip triggers via `info-icon.html` (`c-info-icon`); anchor hrefs fixed; overflow items marked `data-header-meta-overflow` |
| `templates/v2/components/anchor-links.html` | Added `heading`, `with_mobile_dropdown`, and `mobile_only` params |
| `templates/v2/components/resource-card.html` | Renamed `ga_resource_title` → `resource_title`, `ga_resource_id` → `resource_id` |
| `templates/package/snippets/resource_item_v2.html` | Updated to use new param names |
| `hdx-styles/src/common/less/v2/pages/dataset.less` | Sidebar padding (layout via generic `hdx-v2-content-columns` classes); section `border-top` removed; tooltip hover trigger + right-anchor |
| `hdx-styles/src/common/less/v2/components/page-header.less` | Header `.c-tooltip-anchor`: hover + `.is-open` trigger; `right: 0` positioning |
| `hdx-styles/src/common/less/v2/components/label.less` | Added `.c-info-icon` and `.c-tooltip-anchor` |
| `hdx-styles/src/common/less/v2/pages/search.less` | `.hdx-v2-search-sidebar` at XL: `flex: 0 0 25%` |
| `hdx-styles/src/common/less/v2/components/anchor-links.less` | Added `.c-anchor-links-wrapper`, `.c-anchor-links__heading`, `.c-anchor-links-mobile` blocks |
| `hdx-styles/src/common/less/v2/components/resource-card.less` | Added `.resource-list` / `.resource-item` reset styles |
| `fanstatic/v2/components/page-header.js` | Tooltip: target `.c-info-icon` + toggle `.is-open`; `.c-tooltip-anchor` wrapper; overflow reveal uses `[data-header-meta-overflow]` |
| `fanstatic/webassets.yml` | Added `anchor-links.js` to `v2-components-scripts`; `showcase-card.css` to `v2-components-styles`; new `v2-dataset-styles`/`v2-dataset-scripts` bundles |

---

