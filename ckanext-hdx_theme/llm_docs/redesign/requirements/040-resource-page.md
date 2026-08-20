# Resource Page v2 — Full Implementation

**Figma source**: `llm_docs/redesign/figma_exports/resource-page-xl.html`, `resource-page-md.html`, `resource-page-sm.html`, `resource-page-empty-xl.html`

---

## Prerequisites

Already implemented (do not re-implement):
- `v2/components/page-header.html` — unified `c-page-header` for dataset AND resource pages; the resource page passes `compact_title=True` plus a 3-item `meta_items` list (3 items automatically get the `--cols-3` grid)
- `v2/components/breadcrumb.html` — breadcrumb (task 032)
- `v2/components/anchor-links.html` — desktop anchor nav list + mobile dropdown (task 038)
- `v2/components/file-type-icon.html` — file format icon
- `v2/components/button.html`, `v2/components/text-button.html` — action buttons
- `v2/components/dropdown.html` — used for Export metadata dropdown
- `v2/components/copy-button.html` — clipboard copy with green icon feedback
- `v2/components/dropdown.js` — global dropdown open/close (in `v2-components-scripts`)

---

## Template to modify

**Main file**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/resource_read.html`

Extends `v2/page.html`. No v2 feature gate — always v2, same as the dataset page (`hdx_read.html`).

Layout variables set at the top of the template:
```jinja
{% set outer_row_class  = 'hdx-v2-resource-row' %}
{% set columns_class    = 'hdx-v2-content-columns--gap-xl hdx-v2-resource-columns' %}
{% set sidebar_class    = 'hdx-v2-content-columns__sidebar hdx-v2-content-columns__sidebar--xl-only hdx-v2-resource-sidebar' %}
{% set content_class    = 'hdx-v2-content-columns__content hdx-v2-resource-content' %}
```

Layout (gap, XL-only 25% sidebar, flexible content) comes from the generic `hdx-v2-content-columns` classes in `layout.less`; the `hdx-v2-resource-*` classes hold only page-specific padding.

---

## Section Breakdown

### 1. Breadcrumb

**Block**: `{% block breadcrumb_items %}` — `v2/page.html` provides the row + `hdx-v2-container` wrapper.

```jinja
{% block breadcrumb_items %}
  {% snippet 'v2/components/breadcrumb.html',
      items=[
        {'label': pkg.organization.title, 'href': h.url_for('organization.read', id=pkg.organization.name)},
        {'label': pkg.title or pkg.name,  'href': h.url_for('hdx_dataset.read', id=pkg.name)},
        {'label': h.resource_display_name(res), 'href': ''}
      ] %}
{% endblock %}
```

Path: **Home → [Organisation name] → [Dataset title] → [Resource title (no link)]**

---

### 2. Page Header (via `v2/components/page-header.html`)

`page-header.html` is a **unified**, param-driven snippet — no dataset/resource mode switch. The resource page passes `compact_title=True` (adds the `c-page-header--compact-title` modifier — title fixed at 1.5rem) and a 3-item `meta_items` list; 3 items automatically get the `c-page-header__metadata--cols-3` grid. The outer section uses class `c-page-header`.

#### 2a. Snippet call in `resource_read.html`

```jinja
{% block pre_primary %}
  <div class="hdx-v2-page-header-section">
    <div class="hdx-v2-container">
      {% set metadata_url = h.url_for('hdx_dataset.resource_metadata', id=pkg.id, resource_id=res.id) %}
      {% set can_dl = h.check_access('hdx_resource_download', res) %}
      {% set _meta_items = [
        {'label': _('Last modified'), 'value': h.render_datetime(res.last_modified or res.created) or ''},
        {'label': _('Resource ID'), 'value': res.id, 'copy_value': res.id},
        {'label': _('Resource URL'), 'value': res.url or '', 'copy_value': res.url or '',
         'value_href': res.hdx_rel_url if (res.url and h.is_url(res.url) and can_dl) else ''},
      ] %}
      {% snippet 'v2/components/page-header.html',
          compact_title=True,
          file_format=h.hdx_format_to_icon_category(res.format),
          file_format_text=res.format or '',
          title=h.resource_display_name(res),
          description=res.description or '',
          download_url=res.hdx_rel_url,
          can_download=can_dl,
          ga_resource_title=res.name,
          ga_resource_id=res.id,
          export_json_url=metadata_url ~ '?format=json',
          export_csv_url=metadata_url ~ '?format=csv',
          meta_items=_meta_items,
          resource_type=res.resource_type or '',
          download_size=h.filesize_format(res.Size) if res.Size else '' %}
    </div>
  </div>
{% endblock %}
```

#### 2b. Parameters passed by the resource page

| Param | Type | Default | Description |
|---|---|---|---|
| `compact_title` | bool | `False` | `True` — title fixed at 1.5rem, no XL scale-up (`c-page-header--compact-title`) |
| `file_format` | string | `''` | Category for file-type icon (`h.hdx_format_to_icon_category(res.format)`) |
| `file_format_text` | string | `''` | Raw format string shown next to icon (e.g. `'GEOJSON'`) |
| `title` | string | `''` | Resource display name |
| `description` | string | `''` | Resource description (may be empty) |
| `download_url` | string | `''` | `res.hdx_rel_url` |
| `download_size` | string | `''` | Human-readable size (`h.filesize_format(res.Size)`) — appended as `Download (14.2K)` |
| `can_download` | bool | `False` | `h.check_access('hdx_resource_download', res)` — cached before snippet call; renders the `__cta--row` download + export row |
| `ga_resource_title` | string | `''` | `res.name` — passed as `data-resource-name` on download button |
| `ga_resource_id` | string | `''` | `res.id` — passed as `data-resource-id` on download button |
| `export_json_url` | string | `''` | `metadata_url ~ '?format=json'` |
| `export_csv_url` | string | `''` | `metadata_url ~ '?format=csv'` |
| `meta_items` | list | `[]` | The 3 metadata strip entries (Last modified / Resource ID / Resource URL) — see 2e |
| `resource_type` | string | `''` | `res.resource_type` — used in GA class on download button |

`meta_items` item keys used here: `label`, `value`, `copy_value` (presence renders a copy-button in the label row), `value_href` (renders the value as `c-text-link`). See task 037 §4.2 for the full item schema.

#### 2c. Download button (GA tracking)

The download button and export dropdown render inside `<div class="c-page-header__cta c-page-header__cta--row">` when `can_download` is true.

```jinja
{% set _dl_label = _('Download') ~ ' (' ~ download_size ~ ')' if download_size else _('Download') %}
{% snippet 'v2/components/button.html',
    style='primary', size='m',
    label=_dl_label,
    icon=True, icon_position='left',
    icon_src='v2/icons/download.svg',
    tag='a', href=download_url,
    extra_classes='ga-download resource-url-analytics resource-type-' ~ resource_type,
    attrs={'data-resource-name': ga_resource_title, 'data-resource-id': ga_resource_id} %}
```

GA tracking reads `.ga-download` click + `data-resource-name` / `data-resource-id` attrs (jQuery `.data()` API). Do not remove or rename these.

#### 2d. Export metadata dropdown

Reuses the existing export URL pattern from `resource_item.html:92`. Uses the standard `c-dropdown` snippet with `navigate=True`. Items navigate directly to the export URL; `dropdown.js` handles open/close and navigation.

```jinja
{% snippet 'v2/components/dropdown.html',
    size='m',
    placeholder=_('Export metadata'),
    navigate=True,
    items=[
      {'value': export_json_url, 'label': _('JSON'), 'active': False},
      {'value': export_csv_url,  'label': _('CSV'),  'active': False}
    ] %}
```

`metadata_url` is built as `h.url_for('hdx_dataset.resource_metadata', id=pkg.id, resource_id=res.id)`.

#### 2e. Metadata strip (resource)

Driven by the 3-item `meta_items` list — 3 items automatically add the `c-page-header__metadata--cols-3` modifier:
- **SM** (< 768px): stacked vertically, full-width
- **MD** (768–1279px): Last modified + Resource ID side by side (50%/50%), Resource URL full-width below
- **XL** (≥ 1280px): CSS Grid with `calc(25% + var(--hdx-space-6)) / 1fr / 2fr` — the extra gap offset on column 1 ensures Resource ID aligns visually with the content section headings below

Resource URL uses `text-link.html` (via the item's `value_href`) — allows word-wrap, no ellipsis.
Copy buttons render from the items' `copy_value` (`copy-button.html`, style=secondary, size=s).

The same alignment principle is applied to the default 4-column `__metadata` grid in `page-header.less`:
`grid-template-columns: calc(25% + var(--hdx-space-6)) repeat(3, 1fr)`.

---

### 3. Anchor Links Navigation (Sticky)

Follows the same pattern as the dataset page (task 039). Items are conditional.

**`_data_explorer` detection** — computed at template root level (before any blocks) so it's accessible in both `{% block secondary_content %}` and `{% block primary %}`:
```jinja
{% set _de_ns = namespace(view=None) %}
{% for _v in resource_views or [] %}
  {% if not _de_ns.view and _v.view_type != 'hdx_hxl_preview' %}
    {% set _de_ns.view = _v %}
  {% endif %}
{% endfor %}
{% set _data_explorer = _de_ns.view %}
```

**Conditional anchor items** — use `_data_explorer`, not `resource_views`:
```jinja
{% set ns = namespace(anchor_items=[]) %}
{% if _data_explorer %}
  {% set ns.anchor_items = ns.anchor_items + [{'label': _('Resource preview'), 'href': '#resource-preview', 'active': True}] %}
{% endif %}
{% if res.datastore_active %}
  {% set ns.anchor_items = ns.anchor_items + [{'label': _('API'), 'href': '#api-access', 'active': not _data_explorer}] %}
{% endif %}
```

**Desktop sidebar** (`{% block secondary_content %}`) and **mobile sticky** (top of `{% block primary %}`): same as before, using the `ns.anchor_items` built above.

**Section IDs**:
- `#resource-preview` — only when `_data_explorer` is set
- `#api-access` — only when `res.datastore_active`

---

### 4. Resource Preview (CONDITIONAL)

**Condition**: `_data_explorer and h.check_access('hdx_resource_download', res)`

Only the **Data Explorer** view (`view_type != 'hdx_hxl_preview'`) is shown — no `<ul class="nav nav-tabs">` tab menu. `resource_views_list.html` is **not used**.

```jinja
{% if _data_explorer and h.check_access('hdx_resource_download', res) %}
<section class="hdx-v2-dataset-section" id="resource-preview">
  <div class="hdx-v2-dataset-section__header">
    <h2 class="hdx-v2-dataset-section__title">{{ _('Resource preview') }}</h2>
  </div>
  <div class="hdx-v2-dataset-section__body">
    <div class="resource-view">
      {% snippet 'package/snippets/resource_view.html',
         resource_view=_data_explorer,
         resource=resource,
         package=package %}
    </div>
  </div>
</section>
{% endif %}
```

Do **not** change the internals of `resource_view.html`.

---

### 5. API Access Section (CONDITIONAL)

**Condition**: `res.datastore_active`

Content is rendered inline (not as a modal). Mirrors the content of `ajax_snippets/api_info.html` but does not call that template directly.

The "See documentation" button is placed inside the **section header** (alongside the title, using `hdx-v2-dataset-section__header` flex row):
```jinja
{% snippet 'v2/components/button.html',
    style='tertiary', size='m',
    label=_('See documentation'),
    icon=True, icon_position='left',
    icon_src='v2/icons/link-external.svg',
    tag='a',
    href='https://un-ocha-centre-for-humanitarian.gitbook.io/hdx-docs/build-with-hdx/build-with-hdx/hdx-api/tabular-data-endpoints',
    attrs={'target': '_blank', 'rel': 'noopener'} %}
```

The section body uses `.hdx-v2-resource-api` — column layout on SM/MD, row layout at XL:

**Block 1 — API Token**:
- Label text
- `c-button--secondary` link: "Access to get token"
  - Logged in: `h.url_for('user.api_tokens', id=c.userobj.name)`
  - Not logged in: `h.url_for('user.login', came_from=h.url_for('hdx_redirect_manager.redirect_page', page_name='api_tokens_management'))`

**Block 2 — Resource ID**:
- Label + value
- `copy-button.html`, same component used by the page-header's Resource ID/URL and Dataset ID copy buttons:

```jinja
{% snippet 'v2/components/copy-button.html',
    value=res.id,
    style='secondary', size='m',
    icon_position='left',
    label=_('Copy resource ID') %}
```

**Block 3 — Example Query**:
- `__label-row`: label + "More info" `text-button` (tertiary, size s, external link to query docs)
- Query URL rendered via `text-link.html` (no `extra_classes`):

```jinja
{% set query_url = h.url_for('api.action', logic_function='datastore_search', resource_id=res.id, limit=10, qualified=True) %}
```

---

### 6. Data Dictionary

Built later by task 068. Gated on `res.datastore_active`: `<section class="hdx-v2-resource-section" id="data-dictionary" data-module="data-dictionary" data-resource-id="{{ res.id }}">`, with a "Data dictionary" entry added to the anchor-nav item list alongside "Resource preview" and "API".

---

### 7. Other Resources Section

❌ **OUT OF SCOPE** — not implemented.

---

## `c-copy-button` Component

### Template: `templates/v2/components/copy-button.html`

Parameters:

| Param | Type | Default | Description |
|---|---|---|---|
| `value` | string | `''` | Text to copy to clipboard |
| `style` | string | `'secondary'` | `'secondary'` \| `'tertiary'` |
| `size` | string | `'m'` | `'m'` \| `'s'` |
| `icon_position` | string | `'left'` | `'left'` \| `'right'` |
| `label` | string | `'Copy'` | Button label text |
| `extra_classes` | string | `''` | Additional CSS classes |

Renders a `<button>` with `data-copy-value="{{ value }}"`. No `__feedback` span — visual feedback is handled via the `is-copied` CSS class only.

### JS: `fanstatic/v2/components/copy-button.js`

Added to `v2-components-scripts` bundle. Listens for `click` on any element with `[data-copy-value]`; `copy-button.html` is currently the only template that renders that attribute.

- On success: `navigator.clipboard.writeText(el.dataset.copyValue)` → adds `is-copied` class to the element
- After 2 seconds: removes `is-copied` class
- On failure (no clipboard API): silent no-op

Does **not** use the legacy `copy-into-buffer.js` module.

### LESS: `hdx-styles/src/common/less/v2/components/copy-button.less`

~~~less
&.is-copied .c-copy-button__icon { color: var(--hdx-success-5); }
~~~

Copy icon uses `stroke="currentColor"` / `fill="currentColor"` so the green color applies via CSS.

---

## Block Structure in `resource_read.html`

### Base template change
```jinja
{# Before: #}
{% extends "page.html" %}

{# After: #}
{% extends "v2/page.html" %}
```

### Blocks to REMOVE:
- `{% block breadcrumb_content_selected %}` — empty block
- `{% block breadcrumb_content %}` — replaced by `{% block toolbar %}`
- `{% block resource %}` and `{% block resource_inner %}` — replaced by structured v2 blocks
- `{% block data_preview %}` — moved into section in `{% block primary %}`
- `{% block primary_content %}` — was already commented out
- `{% block secondary_content %}` — was commented out

### Blocks to ADD:
- `{% block breadcrumb_items %}` — v2 breadcrumb (Home → Org → Dataset → Resource)
- `{% block pre_primary %}` — page header via `v2/components/page-header.html`
- `{% block secondary_content %}` — desktop anchor nav sidebar
- `{% block primary %}` — mobile anchor dropdown + all content sections

### Blocks to KEEP UNCHANGED:
All analytics blocks (top of template):
```
{% block analytics_org_name %}{{ package.organization.name }}{% endblock %}
{% block analytics_org_id %}{{ package.organization.id }}{% endblock %}
{% block analytics_is_cod %}{{ analytics.analytics_is_cod }}{% endblock %}
{% block analytics_is_indicator %}{{ analytics.analytics_is_indicator }}{% endblock %}
{% block analytics_is_archived %}{{ analytics.analytics_is_archived }}{% endblock %}
{% block analytics_group_names %}{{ analytics.analytics_group_names | safe }}{% endblock %}
{% block analytics_group_ids %}{{ analytics.analytics_group_ids | safe }}{% endblock %}
{% block analytics_dataset_name %}{{ package.name }}{% endblock %}
{% block analytics_dataset_id %}{{ package.id }}{% endblock %}
{% block analytics_dataset_availability %}{{ analytics.analytics_dataset_availability }}{% endblock %}
```

Also preserve: `{% block head_extras %}`, `{% block subtitle %}`, `{% block meta %}`.

---

## JavaScript

### `fanstatic/v2/components/dropdown.js` — new, in `v2-components-scripts`

Handles ALL `c-dropdown` open/close toggle and outside-click-close. Also handles `[data-nav-value]` clicks that are **not** inside `[data-nav-key]` (export metadata items) by navigating to the URL directly.

Does not interfere with `search.js` which handles `[data-nav-key]` items via `setNavParam`.

### `fanstatic/v2/components/page-header.js`

Targets all `.c-page-header` instances (`querySelectorAll`). Overflow "View more" reveal on `[data-header-meta-overflow]` items + tooltip click/keyboard handling for `.c-info-icon`. Export dropdown toggle logic lives in `dropdown.js`.

### `fanstatic/v2/pages/search.js` — modified

Dropdown toggle/close code **removed** (moved to `dropdown.js`). Retains: URL helpers (`setNavParam`, `updateUrl`), checkbox change handler, nav item → setNavParam, clear facet, MiniSearch, FilterOverlay.

### `fanstatic/v2/components/copy-button.js` — new, in `v2-components-scripts`

See `c-copy-button` spec above.

---

## CSS: `fanstatic/v2/pages/resource.css`

Compiled from LESS source at `less/v2/pages/resource.less`.
Registered in the `v2-resource-page-styles` bundle.

### Layout classes

Column layout comes from the generic `hdx-v2-content-columns` classes in `layout.less` (`--gap-xl`, `__sidebar --xl-only`, `__content`). The page classes hold only page-specific extras:

```
.hdx-v2-resource-columns
  — padding: var(--hdx-space-4) 0 5rem

.hdx-v2-resource-sidebar
  — XL+: padding: var(--hdx-space-10) 0
  — NO border-right (resource sidebar has no divider — content fills right side directly)

.hdx-v2-resource-content
  — padding: var(--hdx-space-8) 0 at MD+

.hdx-v2-resource-api
  — display: flex; flex-direction: column; gap: var(--hdx-space-6)
  — XL+: flex-direction: row; align-items: flex-start

  __block
  — display: flex; flex-direction: column; gap: var(--hdx-space-2); flex: 1

  __label
  — font: 600, 0.875rem, var(--hdx-neutral-95); margin: 0

  __label-row
  — display: flex; gap: var(--hdx-space-3); align-items: center

  __value
  — font: 400, 1rem, var(--hdx-neutral-85)

  __query
  — font: 0.875rem; word-break: break-all
```

### Resource-relevant `c-page-header` styles (in `less/v2/components/page-header.less`)

```
.c-page-header

  --compact-title
  — .c-page-header__title fixed at 1.5rem (no XL scale-up)

  __format / __format-label
  — file-type icon + uppercase format label above the title

  __desc
  — data-module="clamped-text" handles clamping (-webkit-line-clamp: 3)

  __cta--row
  — flex-direction: row; align-items: center; gap: var(--hdx-space-3)
  — download button + export metadata dropdown (.c-dropdown { width: fit-content })

  __metadata--cols-3            (applied automatically when meta_items|length == 3)
  — SM: items stacked, full width
  — MD: items 1+2 at 50%, item 3 full-width below
  — XL: grid-template-columns: calc(25% + var(--hdx-space-6)) 1fr 2fr
  — __meta-value: single-line ellipsis by default; .c-text-link values wrap
```

---

## webassets.yml changes

### `v2-components-scripts` — includes:
```yaml
v2-components-scripts:
    contents:
        - v2/components/dropdown.js      # global dropdown behavior
        - v2/components/page-header.js   # overflow "View more" + tooltips
        - v2/components/copy-button.js
        # ... other component scripts
```

### `v2-components-styles` — includes `copy-button.css`:
```yaml
v2-components-styles:
    contents:
        - ...
        - v2/components/copy-button.css
```

### `v2-resource-page-styles` bundle:
```yaml
v2-resource-page-styles:
    output: ckanext-hdx_theme/%(version)s_v2-resource-page-styles.css
    contents:
        - v2/resource-page.css
```

### Load in `resource_read.html`:
```jinja
{% block styles %}
  {{ super() }}
  {% asset 'hdx_theme/v2-resource-page-styles' %}
{% endblock %}
```

No page-specific scripts block needed — all JS is in `v2-components-scripts`, which loads globally.

---

## Files Affected

### New Files

| File | Type | Notes |
|---|---|---|
| `templates/v2/components/page-header.html` | Jinja template | Unified `c-page-header` (dataset + resource + org/landing/crisis) |
| `templates/v2/components/copy-button.html` | Jinja template | `c-copy-button` — green icon on copy success |
| `fanstatic/v2/components/page-header.js` | JavaScript | Overflow "View more" reveal + tooltip handling; export dropdown logic in `dropdown.js` |
| `fanstatic/v2/components/copy-button.js` | JavaScript | Clipboard copy; `is-copied` CSS class approach (in `v2-components-scripts`) |
| `fanstatic/v2/components/dropdown.js` | JavaScript | Global dropdown toggle + URL navigate (in `v2-components-scripts`) |
| `fanstatic/v2/components/copy-button.css` | CSS | Copy button styles (in `v2-components-styles`) |
| `fanstatic/v2/pages/resource.css` | CSS | Resource page layout |
| `less/v2/components/copy-button.less` | LESS | Source for `copy-button.css` |
| `less/v2/pages/resource.less` | LESS | Source for `resource-page.css` |

### Files to Modify

| File | Change |
|---|---|
| `templates/package/resource_read.html` | Extends `v2/page.html`; all blocks restructured per above; analytics blocks preserved |
| `templates/package/hdx_read.html` | Calls `v2/components/page-header.html` with `meta_items`; wrapper class `hdx-v2-page-header-section` |
| `less/v2/components/page-header.less` | All `.c-page-header` styles incl. `--compact-title`, `__cta--row`, `__metadata--cols-3` |
| `fanstatic/v2/pages/search.js` | Dropdown toggle/close code removed (moved to `dropdown.js`) |
| `fanstatic/webassets.yml` | `v2-resource-page-styles` bundle; `dropdown.js` + `copy-button.js/css` in component bundles |

---

## Analytics Preservation (CRITICAL)

These blocks must remain in `resource_read.html` verbatim — they feed Mixpanel. Do **not** rename, remove, or restructure them.

```
{% block analytics_org_name %}{{ package.organization.name }}{% endblock %}
{% block analytics_org_id %}{{ package.organization.id }}{% endblock %}
{% block analytics_is_cod %}{{ analytics.analytics_is_cod }}{% endblock %}
{% block analytics_is_indicator %}{{ analytics.analytics_is_indicator }}{% endblock %}
{% block analytics_is_archived %}{{ analytics.analytics_is_archived }}{% endblock %}
{% block analytics_group_names %}{{ analytics.analytics_group_names | safe }}{% endblock %}
{% block analytics_group_ids %}{{ analytics.analytics_group_ids | safe }}{% endblock %}
{% block analytics_dataset_name %}{{ package.name }}{% endblock %}
{% block analytics_dataset_id %}{{ package.id }}{% endblock %}
{% block analytics_dataset_availability %}{{ analytics.analytics_dataset_availability }}{% endblock %}
```

GA download tracking uses `data-resource-name` / `data-resource-id` attrs on the download button (jQuery `.data()` API) — not hidden spans.

---

## Jinja2 Block Safety Rules

These blocks are defined in `v2/page.html` — do not duplicate:
- `secondary`, `primary`, `pre_primary`, `post_primary`
- `breadcrumb`, `breadcrumb_content`, `toolbar`
- `scripts`, `styles`

Use the Jinja2 namespace trick for conditional list building:
```jinja
{% set ns = namespace(anchor_items=[]) %}
{% if condition %}
  {% set ns.anchor_items = ns.anchor_items + [{...}] %}
{% endif %}
```

Standard `{% set items = items + [...] %}` fails in Jinja2 due to scoping.
