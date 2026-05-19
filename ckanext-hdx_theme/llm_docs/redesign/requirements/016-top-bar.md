# Task 016: Implement v2 top bar

Implement the thin utility top bar in `v2/header.html` as part of the `hdx-v2` page layout. Provides the OCHA Services dropdown trigger and a Documentation link at 2.125rem height, matching the Figma design.

**Figma source:** `llm_docs/redesign/figma_exports/top-bar.html`

## Responsive breakpoints

| Label | Range    | Padding  | Layout                                           |
|-------|----------|----------|--------------------------------------------------|
| SM    | < 80rem  | `0 1rem` | Left: OCHA Services trigger; Right: Documentation |
| LG    | ≥ 80rem  | `0 3rem` | Same two-part layout, wider side padding          |

## What to update

### `templates/v2/header.html`

Full implementation. Two sections inside a flex row:

1. **OCHA Services trigger** (`__services`) — OCHA logo (`/images/homepage/logo-ocha-white.svg`, lazy-loaded, 1.313rem × 1.125rem) + "OCHA Services" text + chevron-down icon (`v2/icons/chevron-down.svg`). Entire group is a `<button>` Bootstrap dropdown trigger (`data-bs-toggle="dropdown"`). Dropdown panel (`__dropdown`) ports all links from the production `header-global.html`: Related Platforms (2 links), Other OCHA Services (5 links), third column (4 links), "See all" button. All dropdown links carry `data-module="hdx_click_stopper"` and `data-module-link_type="header"`.

2. **Navigation links** (`__nav`) — "Documentation" link using `{% snippet 'v2/components/text-link.html' %}` with `data-module="hdx_click_stopper"` and `data-module-link_type="header"`. URL TBD, placeholder `#`.

Key decisions:
- User auth section (Log in / Sign up / avatar) is out of scope — belongs to the main navigation bar task.
- Trigger uses `<button>` (not `<a href="#">`) for accessibility.
- Dropdown open state not shown in Figma; dropdown panel is ported from production header with v2 BEM styling.
- Chevron: inline `{% include 'v2/icons/chevron-down.svg' %}`.
- Bootstrap 5 dropdown JS manages show/hide — no custom JS needed.

### `hdx-styles/src/common/less/v2/top-bar.less` (new file)

BEM block `.hdx-v2-top-bar`. Local tokens: `@hdx-top-bar-bg: #0b2d24`, `@hdx-top-bar-bp-lg: 80rem`.

Height: 2.125rem. Font: `var(--hdx-fs-xs)` (12px) Roboto, white, line-height 1.3.

Elements: `__inner`, `__services`, `__services-trigger`, `__services-logo`, `__services-text`, `__services-chevron`, `__dropdown`, `__dropdown-grid`, `__dropdown-col`, `__dropdown-heading`, `__dropdown-list`, `__see-all`, `__nav`.

Scoped override: `.hdx-v2-top-bar .c-text-link { color: var(--hdx-neutral-0); font-size: var(--hdx-fs-xs); font-weight: var(--hdx-fw-medium) }` — white 12px text matching bar font.

Dropdown overrides Bootstrap `.dropdown-menu` defaults: `background-color: @hdx-top-bar-bg`, `border: none`, `border-radius: 0`.

### `fanstatic/v2/top-bar.css` (new file — compiled from top-bar.less)

### `fanstatic/webassets.yml`

Add `v2/top-bar.css` to `v2-page-styles` after `v2/footer.css`:

```yaml
v2-page-styles:
  contents:
    - vendor/bootstrap5/css/bootstrap.css
    - v2/layout.css
    - v2/footer.css
    - v2/top-bar.css
```

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| 1 | Documentation URL | `https://docs.humdata.org` |
| 2 | Dropdown open state | Implemented using the custom `data-hdx-v2-panel="services"` system (same as navbar panels), managed by `navbar.js` — Bootstrap dropdown JS not used |

## Why

The existing global header (`header-global.html`) combines the OCHA services bar, user auth, and main navigation into one template. The v2 design decouples these into separate components. This task implements only the thin utility bar shown in the `top-bar.html` Figma export: OCHA Services dropdown + Documentation link. The full main navigation and user auth are separate tasks. All `hdx_click_stopper` analytics are preserved. The implementation is self-contained: no changes to existing LESS files outside this block.
