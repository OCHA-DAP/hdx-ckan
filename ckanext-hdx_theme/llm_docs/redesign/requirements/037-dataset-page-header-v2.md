# 037 — Dataset Page Header (v2)

**Scope:** Dataset page — replaces the v1 title/actions block entirely.
**Related tasks:** 029 (dataset card), 030 (dataset list v2), 034 (search list header)

---

## 1. Context

The dataset page uses the shared v2 hero header — `v2/components/page-header.html` (`c-page-header`) — covering the title, labels, description, organisation logo, CTA buttons, and a generic metadata strip driven by the `meta_items` list param (the dataset page passes location, update frequency, time period, source).

`hdx_read.html` extends `v2/page.html` and renders the header unconditionally (no feature gate). The v1 layout block has been removed.

Figma export: `llm_docs/redesign/figma_exports/dataset-page-header.html`

---

## 2. Figma Structure Analysis

The export contains three responsive variants stacked vertically. Each is a complete, standalone layout.

### 2.1 XL layout (≥ 1280px)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  bg: --hdx-neutral-01   padding: 2.5rem 3rem   gap: 2.5rem              │
│                                                                          │
│  ┌── TOP ROW (flex-row, gap: 1.5rem) ─────────────────────────────────┐ │
│  │ ┌── LEFT (flex: 1, max-width: 55.125rem, flex-col, gap: 2.5rem) ──┐│ │
│  │ │  DESCRIPTION BLOCK (flex-col, gap: 1rem)                        ││ │
│  │ │    LABEL ROW (flex-wrap, gap: 0.75rem)                          ││ │
│  │ │    [🔒 Request only data][COD+][Part of data grids]             ││ │
│  │ │    [Part of crisis name] View crisis page ↗                     ││ │
│  │ │  <h1> Dataset Title — 1.75rem Merriweather bold                 ││ │
│  │ │  DESCRIPTION (flex-col, gap: 0.5rem)                            ││ │
│  │ │    <p> description text (3-line clamp, neutral-85)              ││ │
│  │ │    Show more ↓                                                  ││ │
│  │ │  CTA BLOCK (flex-col, gap: 0.5rem)                              ││ │
│  │ │    [ 🔔 Get notified ] (primary button)                         ││ │
│  │ │    ⬇ 2.9k+ downloads (icon + text, neutral-8)                  ││ │
│  │ └─────────────────────────────────────────────────────────────────┘│ │
│  │                                                                     │ │
│  │ ┌── RIGHT CARD (17.375rem wide, white, p: 1.5rem, gap: 1rem) ────┐ │ │
│  │ │  [org logo — max-width 9.375rem]                               │ │ │
│  │ │  ✉ Contact organisation                                        │ │ │
│  │ └────────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────── │
│                                                                          │
│  ─────────────────────────── divider ──────────────────────────────    │
│                                                                          │
│  ┌── METADATA ROW (flex-wrap, gap: 1.5rem, font: 12px) ──────────────┐ │
│  │ Location ↓     │ Exp. update freq │ Time period   ⓘ │ Source  ↗ ⓘ │ │
│  │ Multiple loc.  │ Daily            │ 01 Jan 2016 -    │ Insecurity   │ │
│  │ [sub-national] │ [Up to date]     │ 05 Jul 2025      │ Insight …    │ │
│  └───────────────────────────────────────────────────────────────────── │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 MD layout (768–1280px)

Top is still two columns (left + right card). Key differences:

| Property | XL | MD |
|----------|----|----|
| Container padding | 2.5rem 3rem | 2rem 3rem |
| Gap (sections) | 2.5rem | 2rem |
| Left column | flex: 1 (max-w 55.125rem) | flex: 1 (no max-width) |
| Title font-size | 1.75rem | 1.5rem |
| Right card width | 17.375rem | 11.25rem |
| Right card padding | 1.5rem | 1rem |
| Org logo area | max-width 9.375rem | max-width 7.05rem, h 4rem |
| Metadata font | 12px | 14px |
| **Metadata layout** | **4 items in a row** | **2×2 grid (Location+Freq / Period+Source)** |

### 2.3 SM layout (< 768px)

Right card moves **inside** the left column, between description and CTA. All metadata items stack full-width.

```
┌── SM single column (flex-col, gap: 1.5rem, padding: 1.5rem 1rem) ──┐
│  DESCRIPTION BLOCK                                                   │
│    LABEL ROW                                                         │
│    <h1> 1.25rem Merriweather bold                                    │
│    <p> description (3-line clamp) + Show more ↓                     │
│  ORG CARD — full-width strip (p: 0.5rem 0.75rem)                     │
│    [logo]  ✉ Contact organisation                                    │
│  CTA BLOCK                                                           │
│    [ 🔔 Get notified ]  ⬇ 2.9k+ downloads                           │
│  ────── divider ──────────────────                                   │
│  METADATA — 4 items, each full width                                 │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.4 Conditional elements

| Element | Condition |
|---------|-----------|
| Description + Show more | Only if `description` non-empty |
| "Request only data" label | `request_only=True` |
| "COD+" label | `cod_dataset=True` |
| `links_list` label+button groups | `links_list` non-empty |
| Org logo | `logo_src` non-empty |
| "Contact organisation" | Shown when `org_name` provided |
| "Get notified" button | `supports_notifications=True` |
| Download count | `download_count` non-zero |
| Metadata strip + divider | `meta_items` non-empty (`hdx_read.html` passes `[]` unless `_has_meta`) |
| "View all" (Location) | Location item's `link` set when location text non-empty — arrow-down icon, href `#metadata-location` |
| "Sub-national" label | Location item's `chip` set when `pkg.subnational == 1` |
| "Up to date" label | Frequency item's `chip` set when `pkg.is_fresh` |
| Time period tooltip icon | Time period item's `tooltip` dict |
| Source "View more" link | Source item has `link` + `link_on_overflow: True` — rendered hidden, revealed by JS when the value overflows 1 line; links to `#metadata-source` |

---

## 3. Component Breakdown & Mapping

All elements map to existing v2 components. **No new base components needed.**

### 3.1 Labels

| Figma label | Component | Params |
|-------------|-----------|--------|
| "Request only data" | `v2/components/label.html` | `color='yellow'`, `size='s'`, `icon=True`, `icon_src='v2/icons/lock.svg'` |
| "COD+" | `v2/components/label.html` | `color='grey'`, `size='s'` |
| "Part of …" (data grid/crisis) | `v2/components/label.html` | `color='grey'`, `size='s'` |
| "Sub-national" | `v2/components/label.html` | `color='cyan'`, `size='xs'` |
| "Up to date" | `v2/components/label.html` | `color='cyan'`, `size='xs'` |

### 3.2 Buttons

| Figma element | Component | Notes |
|---------------|-----------|-------|
| "Get notified" | `v2/components/button.html` | `style='primary'`, `size='m'`, `icon=True`, `icon_position='left'`, `icon_src='v2/icons/bell.svg'`, `tag='button'` — opens JS notification modal |
| "Contact organisation" | `v2/components/text-button.html` | `style='tertiary'`, `size='m'`, `icon=True`, **`icon_position='left'`**, **`icon_src='v2/icons/mail.svg'`**, `tag='a'` |
| "View crisis page" | `v2/components/text-button.html` | `style='tertiary'`, `size='s'`, `icon=True`, `icon_position='right'`, `icon_src='v2/icons/arrow-right.svg'`, `tag='a'` |
| "Show more" (description) | `v2/components/text-button.html` | `style='tertiary'`, `size='s'`, `icon=True`, `icon_position='right'`, `icon_src='v2/icons/chevron-down.svg'`, `tag='button'` |
| "View all" (Location) | `v2/components/text-button.html` | Rendered from the meta item's `link` dict: `style='tertiary'`, `size='s'`, `icon=True`, `icon_position='right'`, **`icon_src='v2/icons/arrow-down.svg'`**, `tag='a'`, `href='#metadata-location'` |
| "View more" (Source) | `v2/components/text-button.html` | Rendered from the meta item's `link` dict; with `link_on_overflow: True` it gets `extra_classes='c-page-header__meta-view-more'` — hidden by default, revealed by JS when text overflows. `href='#metadata-source'` |
| Info-circle (tooltip trigger) | `v2/components/info-icon.html` | Rendered from the meta item's `tooltip` dict (`{text, id, aria_label}`) — shared `c-info-icon` + `c-tooltip-anchor` pattern |

### 3.3 Tooltip

The time period tooltip:
```jinja
{% snippet 'v2/components/info-icon.html',
    aria_label=item.tooltip.aria_label,
    tooltip_text=item.tooltip.text,
    tooltip_id=item.tooltip.id %}
```

Uses the shared `c-info-icon` / `c-tooltip-anchor` pattern. Hover/focus visibility is CSS; `page-header.js` toggles `is-open` + `aria-expanded` on click, and closes on outside click or Escape (returning focus to the trigger).

### 3.4 Structural elements

| Element | Markup |
|---------|--------|
| Divider | `<hr class="c-divider">` |
| Org logo | `<img>` with `max-width` + `object-fit: contain` |
| Dataset title | `<h1>` — Merriweather bold, responsive font-size; gets `data-module="hdx-quick-edit"` attrs when `edit_mode=True` |
| Description container | `<div data-module="clamped-text">` + `<p class="...__desc-text" data-clamped-content>` + show-more button (updated task 038) |
| Download count | `<div>` with inline SVG + `<span>` |

---

## 4. API

### 4.1 Snippet call (from `hdx_read.html`)

The caller builds the metadata strip as a `meta_items` list via `{% set %}`, guarded by `_has_meta`:

```jinja
{% set _meta_items = [
  {'label': _('Location'), 'value': _location_text,
   'chip': {'text': _('Sub-national'), 'color': 'cyan'} if _subnational else None,
   'link': {'label': _('View all'), 'href': '#metadata-location'} if _location_text else None},
  {'label': _('Expected update frequency'), 'value': _update_frequency,
   'chip': {'text': _('Up to date'), 'color': 'cyan'} if pkg.is_fresh else None},
  {'label': _('Time period'), 'value': _time_period,
   'tooltip': {'aria_label': _('More info about time period'),
               'text': _('The earliest start date and latest end date across all resources included in the dataset.'),
               'id': 'tooltip-time-period'}},
  {'label': _('Source'), 'value': _source_text,
   'link': {'label': _('View more'), 'href': '#metadata-source'} if _source_text else None,
   'link_on_overflow': True},
] if _has_meta else [] %}

{% snippet 'v2/components/page-header.html',
    title=pkg.title or pkg.name,
    description=pkg.notes,
    org_name=pkg.organization.title,
    logo_src=logo_config.image_url if logo_config and logo_config.image_url else '',
    contact_href=contact_href,
    download_count=pkg.approx_total_downloads,
    request_only=pkg.is_requestdata_type,
    cod_dataset=(analytics_is_cod == 'true'),
    links_list=pkg.links_list or [],
    supports_notifications=analytics_supports_notifications,
    notification_object_type=object_type,
    notification_object_id=object_id,
    notification_object_dict=pkg,
    meta_items=_meta_items,
    edit_mode=edit_mode,
    pkg_id=pkg.id,
    pkg_state=pkg.state,
    membership=membership,
    hide_membership=False,
    org_id=pkg.owner_org
%}
```

### 4.2 Parameter reference

Dataset-relevant params (see the docblock in `templates/v2/components/page-header.html` for the full list — org/landing/crisis and download-CTA params included):

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | string | `''` | Dataset title text. |
| `compact_title` | bool | `False` | Title fixed at 1.5rem, no XL scale-up (`c-page-header--compact-title`, resource pages). |
| `description` | string | `''` | Full description. Empty = section hidden. |
| `org_name` | string | `''` | Organisation display name (used as img alt). |
| `logo_src` | string | `''` | Logo image URL. Empty = logo area hidden. |
| `contact_href` | string | `'#'` | Link for "Contact organisation" button. |
| `download_count` | int | `0` | From `pkg.approx_total_downloads`. Zero/falsy = stat hidden. |
| `request_only` | bool | `False` | Show "Request only data" yellow label. |
| `cod_dataset` | bool | `False` | Show "COD+" grey label. |
| `links_list` | list | `[]` | List of `{label, title, url, newTab}` dicts from `pkg.links_list`. |
| `supports_notifications` | bool | `False` | Show "Get notified" button (JS modal). |
| `meta_items` | list | `[]` | Metadata strip entries (strip + divider render only when non-empty). 3 items get the resource-style `--cols-3` grid; otherwise the 4-column dataset grid. |
| `extra_classes` | string | `''` | Extra classes on the root section. |
| `edit_mode` | bool | `False` | Adds `data-module="hdx-quick-edit"` attrs to title and description container. |
| `pkg_id` | string | `''` | Package ID — required when `edit_mode=True`. |

Each `meta_items` entry:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `label` | string | required | Column heading. |
| `value` | string | `''` | Value text. |
| `value_href` | string | `''` | Render value as `c-text-link` (resource URL). |
| `chip` | dict | `None` | `{text, color}` — `c-label` size xs after the value (Sub-national / Up to date). |
| `tooltip` | dict | `None` | `{text, id, aria_label}` — info-icon in the label row (time period). |
| `copy_value` | string | `''` | When set, a copy-button in the label row copies this text (resource ID / URL). |
| `link` | dict | `None` | `{label, href}` — text-button in the label row (Location "View all", Source "View more"). |
| `link_on_overflow` | bool | `False` | Link starts hidden; `page-header.js` reveals it when the value overflows one line. Implies `truncate`. |
| `truncate` | bool | `False` | Single-line ellipsis value. |

### 4.3 Removed params (vs initial proposal)

| Removed | Reason |
|---------|--------|
| `size` | Pure CSS responsive via `@hdx-bp-md` / `@hdx-bp-xl`. |
| `part_of_data_grids` | Subsumed by `links_list`. |
| `part_of_crisis`, `crisis_name`, `crisis_href` | Subsumed by `links_list`. |
| `org_contact_url`, `notify_href` | Buttons open existing JS modals. |
| `location_view_all_href` | Always `#metadata-location`. |

---

## 5. Behavior

### 5.1 Description expand/collapse

~~`data-module="dataset-page-header"`~~ → **updated (task 038)**: now uses shared `data-module="clamped-text"` with `data-clamped-content` on `<p>`. Handled by `clamped-text.js`.

```html
<div class="c-page-header__desc" data-module="clamped-text">
  <p class="c-page-header__desc-text" data-clamped-content>{{ description }}</p>
  <!-- c-text-button "Show more" / "Show less" -->
</div>
```

JS toggles `is-open` class on the `<p>` (not `is-expanded` on the container). CSS uses `-webkit-line-clamp: 3` by default; `.is-open` on `<p>` removes the clamp.

### 5.2 Tooltip (time period)

Rendered via the shared `v2/components/info-icon.html` snippet from the meta item's `tooltip` dict — a `c-info-icon` inside a `c-tooltip-anchor` with a `c-tooltip`.

Hover/focus visibility is pure CSS. `page-header.js` (which targets all `.c-page-header` instances via `querySelectorAll`) toggles `is-open` + `aria-expanded` on click/tap, closes all tooltips on outside click, and closes on Escape returning focus to the trigger.

Tooltip copy:
- **Time period:** `"The earliest start date and latest end date across all resources included in the dataset."`

### 5.3 Source truncation and "View more"

The source item sets `link_on_overflow: True`, which truncates the value to 1 line (`white-space: nowrap; overflow: hidden; text-overflow: ellipsis` via the `__meta-value--truncate` modifier) and marks the meta item with `data-header-meta-overflow`.

The "View more" link (class `c-page-header__meta-view-more`) is always rendered in the HTML but hidden via CSS (`display: none`). On `DOMContentLoaded`, `page-header.js` checks each `[data-header-meta-overflow]` item and, if the value span's `scrollWidth > clientWidth`, sets `display: inline-flex` to reveal the link. Clicking "View more" scrolls to `#metadata-source` in the metadata section of `hdx_read.html`.

### 5.4 `links_list` rendering

Each item: `{label (optional), title, url, newTab}`. Rendered as a flex `__link-group` per item in the label row:
```html
<div class="c-page-header__link-group">
  {% if link.label %}
    <!-- label component, text truncated "This dataset is part" → "Part" -->
  {% endif %}
  <!-- text-button: style='tertiary', size='s', icon_position='right', arrow-right -->
</div>
```

### 5.5 edit_mode

When `edit_mode=True`, the h1 title receives `data-module="hdx-quick-edit" data-module-anchor="field_title" data-module-dataset="{{ pkg_id }}"`. The description `<p>` (not the outer `clamped-text` div) receives `data-module="hdx-quick-edit" data-module-anchor="field_notes" data-module-dataset="{{ pkg_id }}"`, mirroring the title pattern.

---

## 6. Responsive Behavior

All responsive logic via LESS `@media` queries nested inside element blocks.

| Property | XL (≥ 1280px) | MD (768–1280px) | SM (< 768px) |
|---|---|---|---|
| Container padding | `var(--hdx-space-10) var(--hdx-space-12)` | `var(--hdx-space-8) var(--hdx-space-12)` | `var(--hdx-space-6) var(--hdx-space-4)` |
| Top section gap | `var(--hdx-space-10)` | `var(--hdx-space-8)` | `var(--hdx-space-6)` |
| Top layout | `flex-row` | `flex-row` | `flex-column` |
| Left column | `flex: 1; max-width: 55.125rem` | `flex: 1; min-width: 0` | 100% |
| Title font-size | `var(--hdx-fs-3xl)` 1.75rem | `var(--hdx-fs-2xl)` 1.5rem | `var(--hdx-fs-xl)` 1.25rem |
| Right card position | beside left col | beside left col | inside left col |
| Right card width | 17.375rem fixed | 11.25rem fixed | auto (row layout) |
| Right card padding | `var(--hdx-space-6)` | `var(--hdx-space-4)` | `var(--hdx-space-2) var(--hdx-space-3)` |
| Metadata font-size | `var(--hdx-fs-xs)` 12px | `var(--hdx-fs-s)` 14px | `var(--hdx-fs-s)` 14px |
| **Metadata item layout** | **4 in a row** (flex: 1, min-width: 15.625rem) | **2-column** (width: calc(50% - var(--hdx-space-3))) | **Full width** (width: 100%) |

---

## 7. Integration

### 7.1 Files

| File | Status | Role |
|------|--------|------|
| `templates/v2/components/page-header.html` | Created | Component snippet (shared by dataset, resource, org, landing, crisis pages) |
| `less/v2/components/page-header.less` | Created | All `.c-page-header` LESS |
| `fanstatic/v2/components/page-header.js` | Created | Overflow "View more" reveal + tooltip click/keyboard JS |
| `fanstatic/webassets.yml` | Modified | Adds `page-header.js` to `v2-components-scripts` bundle |
| `templates/package/hdx_read.html` | Modified | Builds `_meta_items` (guarded by `_has_meta`), renders snippet unconditionally; passes `edit_mode` + `pkg_id` |

### 7.2 What was NOT created

- No new base components — all uses existing `label.html`, `button.html`, `text-button.html`, `text-link.html`, `info-icon.html`, `copy-button.html`.

### 7.3 BEM naming

Block: `c-page-header` (shared component).

```
c-page-header
  --compact-title       title fixed at 1.5rem (resource pages)
  --underlined          SM/MD bottom border (Signals)
  __top
  __left
  __description
  __format              file-type icon + label (resource)
  __format-label
  __labels
  __link-group          one per links_list item
  __title
  __subtitle
  __member-since
  __desc                data-module="clamped-text" (updated task 038)
  __desc-text           line-clamped <p> data-clamped-content; clamp lifted when __desc-text.is-open
  __cta
    --row               download + export metadata row (resource)
  __notify-btn
  __downloads
  __right-card
    --sm-only           visible < 768px; row layout inside left col
    --md-up             visible ≥ 768px; sidebar col layout
  __logo
  __card-actions
  __card-stats
  __card-stat
  __card-stat-label
  __card-stat-value
  __metadata
    --cols-3            resource-style 3-column grid (auto when meta_items|length == 3)
  __meta-item           width: 100% SM / calc(50%-12px) MD / flex:1 XL; data-header-meta-overflow when link_on_overflow
  __meta-label-row      flex row
  __meta-label
  __meta-value
    --truncate          nowrap + text-overflow: ellipsis on inner span
  __meta-view-more      always display:none; JS sets inline-flex when overflow
```

---

## 8. Constraints

- ❌ No Bootstrap classes
- ✅ All spacing uses `var(--hdx-space-*)` CSS custom properties
- ✅ All fonts/weights/line-heights use `var(--hdx-font-*)`, `var(--hdx-fw-*)`, `var(--hdx-lh-*)` CSS custom properties
- ✅ Colors from `var(--hdx-*)` tokens
- ✅ BEM naming as above
- ✅ Hover = CSS `:hover` pseudo-class only
- ✅ Reuse existing components — no new ones
- ❌ No inline styles
- ✅ Media queries nested inside element blocks (CONVENTIONS.md rule)
- ✅ Breakpoints from `breakpoints.less` only (`@hdx-bp-md`, `@hdx-bp-xl`)

---

## 9. Decisions

| ID | Decision |
|----|----------|
| OQ-1 | Data grids entries come from `pkg.links_list`. Items with `link.label` render as label + text-button; items without render as text-button only. |
| OQ-2 | `request_only` mapped from `pkg.is_requestdata_type`. |
| OQ-3 | Crisis entries come from `pkg.links_list` (same mechanism as data grids). |
| OQ-4 | Download count is `pkg.approx_total_downloads`. |
| OQ-5 | "View all" on Location always renders when the location text is non-empty. Uses `arrow-down.svg`. Anchor: `#metadata-location`. |
| OQ-6 | If `logo_src` empty, logo area hidden entirely. |
| OQ-7 | "Get notified" opens JS notification modal. "Contact organisation" is an `<a>` linking to `contact_href`. Uses `mail.svg` icon on the left. |
| OQ-8 | Hidden text-link in Location value row (Figma only) — out of scope, skipped. |
| OQ-9 | Tooltip copy hardcoded in the caller's `meta_items`. Only the time period item has a tooltip. |
| OQ-10 | Labels flex-wrap freely with no per-line cap. |
| OQ-11 | ~~`data-module="dataset-page-header"` handled by `page-header.js`~~ → **updated (task 038)**: uses shared `data-module="clamped-text"` + `data-clamped-content`; JS handler removed from `page-header.js`. |
| OQ-12 | Tooltip trigger is `c-button` (icon-only) with CSS chrome removed; aria-expanded toggled by JS; outside click closes. |
| OQ-13 | Source "View more" link is rendered but hidden; JS reveals it only when text visually overflows 1 line (scrollWidth > clientWidth). Links to `#metadata-source`. |
| OQ-14 | `hdx_read.html` has no v2 feature gate — the new header is always rendered. v1 layout block removed. |
| OQ-15 | MD layout: left column uses `flex: 1` (not fixed width) to avoid blank space beside org card on wide viewports. |
| OQ-16 | Spacing and typography use CSS custom properties (`var(--hdx-space-*)`, `var(--hdx-font-*)`, etc.), not raw rem values. |
| OQ-17 | edit_mode support: title and description container receive `data-module="hdx-quick-edit"` attrs when `edit_mode=True`, passed alongside `pkg_id`. |
