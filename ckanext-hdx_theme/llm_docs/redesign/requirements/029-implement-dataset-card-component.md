# Task 029: Implement c-dataset-card component

## Goal

Create a reusable, responsive dataset card component matching the Figma design exactly. Three layout sizes driven by breakpoints (xl, md, sm). Hover state implemented via CSS `:hover` pseudo-class only — no state class.

## Scope

**In:**
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/dataset-card.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/dataset-card.less`
- A minimal JS module: `fanstatic/v2/components/clamped-text.js` (shared)

**Out:**
- CKAN template integration, data fetching, routing (consuming page's concern)
- Hover via state class (use `:hover` pseudo-class only per CONVENTIONS.md)

## BEM Structure

```
.c-dataset-card
  .c-dataset-card__body
    .c-dataset-card__left
      .c-dataset-card__org
      .c-dataset-card__title           ← <a> element
      .c-dataset-card__desc            ← JS toggle region (hidden on SM)
        .c-dataset-card__desc-text     ← hidden by default; shown when is-open
        [c-text-button: "Show more"]
    .c-dataset-card__right
      .c-dataset-card__locations
        [c-label --size-xs --cyan]       ← location name
        [c-label --size-xs --grey]       ← "Sub-national" (conditional; hidden on SM)
      .c-dataset-card__date
      .c-dataset-card__formats           ← hidden on SM
        [c-label --size-xs --dark --icon-only]  ← private / archived
        [c-label --size-xs --dark]              ← COD / COD+
        [c-label --size-xs --light + icon=true] ← file extension (csv, xls, etc.)
        .c-dataset-card__formats-more           ← "+N" plain span (conditional)
  .c-dataset-card__footer
    [c-text-link --tertiary --size-xs]   ← "View other N datasets from this contributor"
```

## Common Styles

| Property | Token | Value |
|---|---|---|
| Background | `var(--hdx-neutral-0)` | white |
| Border-radius | `var(--hdx-radius-sm)` | 2px |
| Shadow | `var(--hdx-shadow-sm)` | 0 1px 4px rgba(0,0,0,0.04) |
| Border (default) | `1px solid var(--hdx-neutral-1)` | #ebeff0 |
| Border (hover) | `border-color: var(--hdx-neutral-8)` (constant 1px width) | #3f4748 |
| Transition | — | `border-color 0.15s ease` |
| Body padding | `var(--hdx-space-4)` | 16px all sides |
| Footer padding | `var(--hdx-space-2) var(--hdx-space-4)` | 8px top/bottom, 16px left/right |
| Footer border-top | `1px solid var(--hdx-neutral-1)` | divider line |

## Responsive Layout

| Property | XL (≥80rem) | MD (48–80rem) | SM (<48rem) |
|---|---|---|---|
| `.c-dataset-card__body` | `flex-direction: row` | `flex-direction: row` | `flex-wrap: wrap` |
| `.c-dataset-card__left` width | `30.688rem` (fixed) | `flex: 1`, `max-width: 27.5rem` | `100%` |
| `.c-dataset-card__right` width | `flex: 1` | `15rem` (fixed) | `100%` |
| Column gap | `var(--hdx-space-10)` (2.5rem) | `var(--hdx-space-10)` | — |
| Left column gap | `var(--hdx-space-2)` (8px) between org/title/desc | same | same |
| Right column gap | `var(--hdx-space-3)` (12px) between locations/date/formats | same | — |
| `.c-dataset-card__desc` | visible | visible | `display: none` |
| `.c-dataset-card__formats` | visible | visible | `display: none` |
| Subnational label | visible | visible | `display: none` |

**SM-specific layout note:** In SM, `.c-dataset-card__right` switches to `flex-direction: row` with `align-items: center` and `gap: var(--hdx-space-14)` (10px), so the location label and date appear side-by-side in a single row.

## Typography

| Element | Token | Notes |
|---|---|---|
| Org name | `var(--hdx-fs-s)` / `var(--hdx-neutral-9)` | 14px, weight 400 |
| Title (XL/MD) | `var(--hdx-fs-l)` / `var(--hdx-neutral-10)` | 18px, weight 600, 1-line, `text-overflow: ellipsis` |
| Title (SM) | `var(--hdx-fs-m)` / `var(--hdx-neutral-10)` | 16px, weight 600, 2-line, `-webkit-line-clamp: 2` |
| Description text | `var(--hdx-fs-xs)` / `var(--hdx-neutral-8)` | 12px |
| Date | `var(--hdx-fs-xs)` / `var(--hdx-neutral-9)` | 12px, `line-height: var(--hdx-lh-normal)` |
| Footer link | via `c-text-link --size-xs` | 12px |

## Reused Components

No component extension required — all variants are already supported.

| Use | Component | Props |
|---|---|---|
| "Show more" / "Show less" | `c-text-button` | `style=tertiary, size=s, icon=true, icon_position=right, icon_src='v2/icons/chevron-down.svg'` |
| Location label | `c-label` | `size=xs, color=cyan, icon=false` |
| Subnational label | `c-label` | `size=xs, color=grey, icon=false` |
| Private / archived badge | `c-label` | `size=xs, color=dark, icon_only=true, icon=true, icon_src='v2/icons/lock.svg'` |
| COD / COD+ badge | `c-label` | `size=xs, color=dark, icon=false` |
| File extension badge | `c-label` | `size=xs, color=light, icon=true, icon_src='v2/icons/<ext>.svg'` |
| "View other N datasets" footer | `c-text-link` | `style=tertiary, size=xs` |

## Overflow Badge

Rendered when there are more file formats than the visible set:

- Element: `<span class="c-dataset-card__formats-more">+{{ formats_overflow }}</span>`
- Styles: `font-size: var(--hdx-fs-xs)`, `color: var(--hdx-neutral-9)`, no background, no border, no padding
- Render condition: only when `formats_overflow > 0`

## Snippet Parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `org_name` | string | `''` | Organisation/contributor display name |
| `org_href` | string | `'#'` | URL for org name (omit element if empty) |
| `title` | string | `''` | Dataset title text |
| `title_href` | string | `'#'` | URL the title links to |
| `description` | string | `''` | Full description text (XL/MD only, revealed on expand) |
| `location` | string | `''` | Location label text (e.g. `"Palestine"`) |
| `subnational` | bool | `false` | Show "Sub-national" grey label |
| `date_range` | string | `''` | Date range string (e.g. `"Data from 12 Dec 2022 to 12 Dec 2025"`) |
| `formats` | list | `[]` | Format dicts: `{type: 'extension'\|'cod'\|'cod_plus'\|'private'\|'archived', text: str, icon_src: str}` |
| `formats_overflow` | int | `0` | Count of hidden formats; renders `+N` span when > 0 |
| `show_others_label` | string | `''` | Footer link text (e.g. `"View other 89 datasets from this contributor"`) |
| `show_others_href` | string | `'#'` | Footer link URL |
| `extra_classes` | string | `''` | Additional CSS classes on root `.c-dataset-card` element |

## JS Behavior

~~`data-module="dataset-card"` on `.c-dataset-card__desc`~~ → **updated (task 038)**: now uses `data-module="clamped-text"` on `.c-dataset-card__desc` and `data-clamped-content` on `<p class="c-dataset-card__desc-text">`. Logic lives in the shared `clamped-text.js` module.

**On "Show more" click:**
1. Toggle `is-open` class on `.c-dataset-card__desc-text` — CSS controls `display: none` / `display: block`
2. Toggle button label text: `"Show more"` ↔ `"Show less"`
3. Swap icon src attribute: `chevron-down.svg` ↔ `chevron-up.svg`

No height animation required. The module does not need to run at SM breakpoint since `.c-dataset-card__desc` is hidden in CSS at that size.

## LESS File Structure

```less
@import "../breakpoints.less";

// Component-level tokens
@c-dataset-card-border-default: 1px solid var(--hdx-neutral-1);
@c-dataset-card-border-color-hover: var(--hdx-neutral-8);
@c-dataset-card-left-xl:        30.688rem;
@c-dataset-card-left-md-max:    27.5rem;
@c-dataset-card-right-md:       15rem;
// …

.c-dataset-card {
  // common styles

  &__body { … }
  &__left {
    // default (SM) styles
    @media (min-width: @hdx-bp-md) { … }  // MD
    @media (min-width: @hdx-bp-xl) { … }  // XL
  }
  // etc.
}
```

- Nest `@media` queries **inside** element blocks per CONVENTIONS.md
- Declare all `@c-dataset-card-*` variables at the top of the file

## Design Token Cross-Reference

| Figma variable | Hex | HDX token |
|---|---|---|
| `--color-white` | #ffffff | `var(--hdx-neutral-0)` |
| `--color-whitesmoke-200` | #ebeff0 | `var(--hdx-neutral-1)` |
| `--color-darkslategray-100` | #3f4748 | `var(--hdx-neutral-8)` |
| `--color-darkslategray-200` | #2f3536 | `var(--hdx-neutral-9)` |
| `--color-gray` | #101212 | `var(--hdx-neutral-10)` |
| `--shadow-drop` | 0 1px 4px rgba(0,0,0,0.04) | `var(--hdx-shadow-sm)` |
| `--br-2` | 2px | `var(--hdx-radius-sm)` |
| `--gap-40` / `--gap-10` | 2.5rem / 0.625rem | `var(--hdx-space-10)` / `var(--hdx-space-14)` |
| `--gap-12` | 0.75rem | `var(--hdx-space-3)` |
| `--gap-8` | 0.5rem | `var(--hdx-space-2)` |
| `--padding-16` | 1rem | `var(--hdx-space-4)` |
| `--padding-8` | 0.5rem | `var(--hdx-space-2)` |
| `--fs-18` | 1.125rem | `var(--hdx-fs-l)` |
| `--fs-14` | 0.875rem | `var(--hdx-fs-s)` |
| `--fs-12` | 0.75rem | `var(--hdx-fs-xs)` |

## Reference

- Figma export: `ckanext-hdx_theme/llm_docs/redesign/figma_exports/dataset-card.html`
- Design tokens: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/foundation.less`
- Breakpoints: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/breakpoints.less`
- Conventions: `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md`
- Comparable requirement: `requirements/025-implement-activity-card-component.md`
- Label component: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/label.html`
- Text-button component: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/text-button.html`
- Text-link component: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/text-link.html`
