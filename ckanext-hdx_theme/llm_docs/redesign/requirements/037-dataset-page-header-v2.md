# 037 — Dataset Page Header (v2)

**Scope:** Dataset page — replaces the v1 title/actions block entirely.
**Related tasks:** 029 (dataset card), 030 (dataset list v2), 034 (search list header)

---

## 1. Context

The dataset page uses a v2 redesign hero header — `dataset-page-header` — covering the title, labels, description, organisation logo, CTA buttons, and a metadata strip (location, update frequency, time period, source).

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
| Org logo | `org_logo_src` non-empty |
| "Contact organisation" | Always shown |
| "Get notified" button | `supports_notifications=True` |
| Download count | `download_count` non-zero |
| "View all" (Location) | `location_text` non-empty — arrow-down icon, href `#metadata-location` |
| "Sub-national" label | `subnational=True` |
| "Up to date" label | `is_up_to_date=True` |
| Time period tooltip icon | `time_period_tooltip=True` |
| Source "View more" link | `source_text` non-empty AND source overflows 1 line (detected by JS) — links to `#dataset-additional-info` |

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
| "View all" (Location) | `v2/components/text-button.html` | `style='tertiary'`, `size='s'`, `icon=True`, `icon_position='right'`, **`icon_src='v2/icons/arrow-down.svg'`**, `tag='a'`, `href='#metadata-location'` |
| "View more" (Source) | `v2/components/text-button.html` | `style='tertiary'`, `size='s'`, `icon=True`, `icon_position='right'`, `icon_src='v2/icons/arrow-right.svg'`, `tag='a'`, `href='#dataset-additional-info'`, `extra_classes='hdx-v2-dataset-header__source-view-more'` — hidden by default, revealed by JS when text overflows |
| Info-circle (tooltip trigger) | `v2/components/button.html` | `style='tertiary'`, `size='s'`, `type='icon-only'`, `icon=True`, `icon_src='v2/icons/info-circle.svg'`, `attrs={'aria-expanded': 'false'}` — styled via CSS to remove button chrome |

### 3.3 Tooltip

Both source and time period tooltips:
```jinja
{% snippet 'v2/components/tooltip.html', variant='dark', arrow='', text='...' %}
```

The tooltip-wrap div has `margin-left: auto` to push it to the right edge of the metadata label row. The `c-button` inside is overridden via CSS to remove background, border, padding and match the weight of text-button icons. JS toggles `aria-expanded` on click, and CSS shows the tooltip when `aria-expanded="true"`.

### 3.4 Structural elements

| Element | Markup |
|---------|--------|
| Divider | `<hr class="c-divider hdx-v2-dataset-header__divider">` |
| Org logo | `<img>` with `max-width` + `object-fit: contain` |
| Dataset title | `<h1>` — Merriweather bold, responsive font-size; gets `data-module="hdx-quick-edit"` attrs when `edit_mode=True` |
| Description container | `<div data-module="clamped-text">` + `<p class="...__desc-text" data-clamped-content>` + show-more button (updated task 038) |
| Download count | `<div>` with inline SVG + `<span>` |

---

## 4. API

### 4.1 Snippet call (from `hdx_read.html`)

```jinja
{% snippet 'v2/page-header.html',
    title=pkg.title or pkg.name,
    description=pkg.notes,
    org_name=pkg.organization.title,
    org_logo_src=logo_config.image_url if logo_config and logo_config.image_url else '',
    org_href=h.url_for('organization.read', id=pkg.organization.name),
    contact_href=h.url_for('hdx_dataset.contact_contributor', id=pkg.name or pkg.id),
    download_count=pkg.approx_total_downloads,
    request_only=pkg.is_requestdata_type,
    cod_dataset=(analytics_is_cod == 'true'),
    links_list=pkg.links_list or [],
    supports_notifications=analytics_supports_notifications,
    location_text=_location_text,
    subnational=(pkg.subnational|int == 1),
    update_frequency=h.hdx_get_frequency_by_value(pkg.data_update_frequency),
    is_up_to_date=pkg.is_fresh,
    time_period=h.render_date_from_concat_str(pkg.dataset_date),
    time_period_tooltip=True,
    source_text=pkg.dataset_source or '',
    edit_mode=edit_mode,
    pkg_id=pkg.id
%}
```

### 4.2 Parameter reference

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | string | `''` | Dataset title text. |
| `description` | string | `''` | Full description. Empty = section hidden. |
| `org_name` | string | `''` | Organisation display name (used as img alt). |
| `org_logo_src` | string | `''` | Logo image URL. Empty = logo area hidden. |
| `org_href` | string | `'#'` | Link to org page. |
| `contact_href` | string | `'#'` | Link for "Contact organisation" button. |
| `download_count` | int | `0` | From `pkg.approx_total_downloads`. Zero/falsy = stat hidden. |
| `request_only` | bool | `False` | Show "Request only data" yellow label. |
| `cod_dataset` | bool | `False` | Show "COD+" grey label. |
| `links_list` | list | `[]` | List of `{label, title, url, newTab}` dicts from `pkg.links_list`. |
| `supports_notifications` | bool | `False` | Show "Get notified" button (JS modal). |
| `location_text` | string | `''` | E.g. `'Multiple locations'` or single group title. |
| `subnational` | bool | `False` | Show "Sub-national" label in location row. |
| `update_frequency` | string | `''` | E.g. `'Daily'`. |
| `is_up_to_date` | bool | `False` | Show "Up to date" cyan label. |
| `time_period` | string | `''` | E.g. `'01 January 2016 - 05 July 2025'`. |
| `time_period_tooltip` | bool | `False` | Show info-circle tooltip on time period. |
| `source_text` | string | `''` | Source/contributor display text. Truncated to 1 line; "View more" shown by JS if overflowing. |
| `long_source` | bool | `False` | Unused — kept for API compatibility. |
| `edit_mode` | bool | `False` | Adds `data-module="hdx-quick-edit"` attrs to title and description container. |
| `pkg_id` | string | `''` | Package ID — required when `edit_mode=True`. |

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
<div class="hdx-v2-dataset-header__desc" data-module="clamped-text">
  <p class="hdx-v2-dataset-header__desc-text" data-clamped-content>{{ description }}</p>
  <!-- c-text-button "Show more" / "Show less" -->
</div>
```

JS toggles `is-open` class on the `<p>` (not `is-expanded` on the container). CSS uses `-webkit-line-clamp: 3` by default; `.is-open` on `<p>` removes the clamp.

### 5.2 Tooltip (time period + source)

The `__tooltip-wrap` div has `margin-left: auto` to push it to the right of the `__meta-label-row`. Inside it: a `c-button` (icon-only, aria-expanded="false") and a `c-tooltip--dark`.

CSS overrides strip the `c-button` of all button chrome (background, border, padding, shadow) and size the icon to `0.875rem`. CSS shows the tooltip when `.c-button[aria-expanded="true"] ~ .c-tooltip`. JS in `page-header.js` toggles `aria-expanded` on click and closes all tooltips on outside click.

Tooltip copy:
- **Time period:** `"The earliest start date and latest end date across all resources included in the dataset."`
- **Source:** `"Source information placeholder."` *(TBD)*

### 5.3 Source truncation and "View more"

Source value is always truncated to 1 line via `white-space: nowrap; overflow: hidden; text-overflow: ellipsis` on the `__meta-value--source` modifier.

The "View more" link (class `hdx-v2-dataset-header__source-view-more`) is always rendered in the HTML but hidden via CSS (`display: none`). On `DOMContentLoaded`, `page-header.js` checks if `sourceSpan.scrollWidth > sourceSpan.clientWidth` and if so sets `display: inline-flex` to reveal the link. Clicking "View more" scrolls to `#dataset-additional-info` (the "Additional information" section in the secondary column of `hdx_read.html`).

### 5.4 `links_list` rendering

Each item: `{label (optional), title, url, newTab}`. Rendered as a flex `__link-group` per item in the label row:
```html
<div class="hdx-v2-dataset-header__link-group">
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
| `templates/v2/page-header.html` | Created | Component snippet |
| `hdx-styles/src/common/less/v2/styles.less` | Modified | Contains all `.hdx-v2-dataset-header` LESS (embedded, not a separate file) |
| `fanstatic/v2/components/page-header.js` | Created | Show-more + tooltip JS |
| `fanstatic/webassets.yml` | Modified | Adds `page-header.js` to `v2-components-scripts` bundle |
| `templates/package/hdx_read.html` | Modified | Renders snippet unconditionally; passes `edit_mode` + `pkg_id`; `id="dataset-additional-info"` on secondary section header |

### 7.2 What was NOT created

- No separate `dataset-page-header.less` — styles embedded in `styles.less`.
- No new base components — all uses existing `label.html`, `button.html`, `text-button.html`, `tooltip.html`.

### 7.3 BEM naming

Block: `hdx-v2-dataset-header` (page section — no `c-` prefix).

```
hdx-v2-dataset-header
  __top
  __left
  __description
  __labels
  __link-group          one per links_list item
  __title
  __desc                data-module="clamped-text" (updated task 038)
  __desc-text           line-clamped <p> data-clamped-content; clamp lifted when __desc-text.is-open
  __cta
  __notify-btn
  __downloads
  __right-card
    --sm-only           visible < 768px; row layout inside left col
    --md-up             visible ≥ 768px; sidebar col layout
  __org-logo
  __divider
  __metadata
  __meta-item           width: 100% SM / calc(50%-12px) MD / flex:1 XL
  __meta-label-row      flex row; tooltip-wrap gets margin-left: auto
  __meta-label
  __meta-value
    --source            nowrap + text-overflow: ellipsis on inner span
  __source-view-more    always display:none; JS sets inline-flex when overflow
  __tooltip-wrap        margin-left: auto; c-button chrome removed via CSS
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
| OQ-5 | "View all" on Location always renders when `location_text` non-empty. Uses `arrow-down.svg`. Anchor: `#metadata-location`. |
| OQ-6 | If `org_logo_src` empty, logo area hidden entirely. |
| OQ-7 | "Get notified" opens JS notification modal. "Contact organisation" is an `<a>` linking to `contact_href`. Uses `mail.svg` icon on the left. |
| OQ-8 | Hidden text-link in Location value row (Figma only) — out of scope, skipped. |
| OQ-9 | Tooltip copy hardcoded. Time period: defined. Source: placeholder `"Source information placeholder."` (TBD). |
| OQ-10 | Labels flex-wrap freely with no per-line cap. |
| OQ-11 | ~~`data-module="dataset-page-header"` handled by `page-header.js`~~ → **updated (task 038)**: uses shared `data-module="clamped-text"` + `data-clamped-content`; JS handler removed from `page-header.js`. |
| OQ-12 | Tooltip trigger is `c-button` (icon-only) with CSS chrome removed; aria-expanded toggled by JS; outside click closes. |
| OQ-13 | Source "View more" link is rendered but hidden; JS reveals it only when text visually overflows 1 line (scrollWidth > clientWidth). Links to `#dataset-additional-info` in the secondary block. |
| OQ-14 | `hdx_read.html` has no v2 feature gate — the new header is always rendered. v1 layout block removed. |
| OQ-15 | MD layout: left column uses `flex: 1` (not fixed width) to avoid blank space beside org card on wide viewports. |
| OQ-16 | Spacing and typography use CSS custom properties (`var(--hdx-space-*)`, `var(--hdx-font-*)`, etc.), not raw rem values. |
| OQ-17 | edit_mode support: title and description container receive `data-module="hdx-quick-edit"` attrs when `edit_mode=True`, passed alongside `pkg_id`. |
