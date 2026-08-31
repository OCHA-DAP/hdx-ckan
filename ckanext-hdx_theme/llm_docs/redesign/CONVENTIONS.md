# v2 Redesign — Implementation Conventions

Single source of truth for general rules. Update here; do not duplicate in task files.

---

## BEM class prefixes

| Prefix | Used for | Example |
|--------|----------|---------|
| `c-` | Reusable components | `c-button`, `c-autocomplete` |
| `hdx-v2-` | Non-reusable v2 sections and layouts | `hdx-v2-hero`, `hdx-v2-grid` |

Size modifiers use `--size-{xs,s,m,l}` (`c-button--size-m`, `c-copy-button--size-s`) — never a bare `--{s,m}` or a two-letter shorthand like `--sm`. Exception: `c-list-item` and `c-letter-anchor` still use legacy `--size-lg`/`--size-sm` naming, predating this rule.

---

## Media queries — nest inside element blocks

```less
// Do
&__inner {
    padding: 2rem;
    @media (min-width: @hdx-bp-md) { padding: 4rem; }
}

// Don't
&__inner { padding: 2rem; }
@media (min-width: @hdx-bp-md) { &__inner { padding: 4rem; } }
```

Exception: a single `@media` block may group multiple unrelated elements when there is no per-element responsive logic.

Mobile-first: unprefixed styles are the smallest viewport; `min-width` layers overrides on top. Never pair a `max-width: @X` rule on one element with a `min-width: @X` rule on its counterpart (e.g. a mobile-only control vs. the desktop control it replaces) — both match at exactly `X`, hiding both.

---

## `[hidden]` self-guard

Any component that sets `display` on its own JS-toggled element (a dropdown/autocomplete panel, an
overlay, anything shown/hidden via the `hidden` attribute — see the Alerts section below) must also
carry its own `&[hidden] { display: none; }` guard in that element's own ruleset. Don't rely on
another bundle's reset/reboot rule (e.g. Bootstrap's `[hidden] { display: none !important; }`) to
keep it hidden by default — that bundle may not always be loaded alongside the component's own.

---

## Single compile-time import

Any file that needs breakpoints, typography variables, or type-style mixins should import `mixins.less` only — it re-exports everything:

```less
@import "mixins.less";          // from less/v2/
@import "../mixins.less";       // from less/v2/components/
```

`mixins.less` internally imports `breakpoints.less` and `typography.less`, so callers get all LESS variables and all mixin definitions in one line.

**Exception:** `foundation.less` imports `typography.less` directly (to emit CSS custom properties). Do not change that import.

---

## Page layout — generic column classes

Two-column (sidebar + content) layout is provided by generic classes on
`.hdx-v2-content-columns` in `layout.less`. Pages compose them via the layout
template variables instead of re-declaring flex rules in page LESS:

| Class | Role |
|---|---|
| `hdx-v2-content-columns--gap` | column gap `space-3`, `space-6` at XL (Locations) |
| `hdx-v2-content-columns--gap-xl` | column gap `space-6` at XL only (Dataset, Resource) |
| `hdx-v2-content-columns--stack` | column below XL, row at XL (Org Members/Stats) |
| `hdx-v2-content-columns__sidebar` | sidebar column — `flex: 0 0 25%` at XL |
| `hdx-v2-content-columns__sidebar--xl-only` | hidden below XL (Search, Dataset, Resource, landing pages) |
| `hdx-v2-content-columns__sidebar--sticky` | sticky sidebar (Search, Locations) |
| `hdx-v2-content-columns__sidebar--right` | rendered after the content column (Org Members) |
| `hdx-v2-content-columns__content` | content column — `flex: 1; min-width: 0` |

Page-specific classes remain **only** for genuinely page-specific extras
(e.g. `hdx-v2-search-sidebar` keeps its border-right and padding; the
Locations sidebar keeps its SM/MD `order` swap). Never re-declare the
width/visibility/sticky contract in a page file.

The underlying mixins in `mixins.less` (`.v2-sidebar-flex()`,
`.v2-content-flex()`, `.v2-sidebar-sticky()`) are the primitives these classes
are built from — reach for them only in layouts the generic classes cannot
express.

`.c-anchor-links-wrapper` has `position: sticky; top: var(--hdx-space-12)` built in — pages that use `c-anchor-links` for sidebar navigation (Dataset, HAPI) get stickiness through the component and do **not** need the `--sticky` modifier on the sidebar container.

---

## Breakpoints

Defined **once** in `breakpoints.less`; pulled in automatically via `mixins.less`. No local redefinitions.

| Variable | Value | px |
|----------|-------|----|
| `@hdx-bp-md` | `48rem` | 768px |
| `@hdx-bp-xl` | `80rem` | 1280px |
| `@hdx-bp-xxl` | `87.5rem` | 1400px |

---

## Bootstrap classes — prohibited in v2

Do **not** use Bootstrap grid classes (`row`, `col-*`, `gx-*`, `gy-*`, `g-*`) or utility classes (`d-*`, `gap-*`, `pt-*`, `mt-*`, `align-items-*`, `justify-content-*`, etc.) in v2 templates.

All layout, spacing, and responsive behaviour must be implemented in LESS using `@hdx-bp-*` breakpoints and design tokens.

---

## Container and full-bleed sections

Full-bleed sections (background spans full viewport width) use a two-layer pattern:

- **Outer element** — sets `background-color`, vertical padding only
- **Inner element** — add `hdx-v2-container` class for horizontal padding and max-width; set flex/grid layout here

```html
<section class="hdx-v2-hero">
  <div class="hdx-v2-hero__inner hdx-v2-container">...</div>
</section>
```

`.hdx-v2-container` is defined in `layout.less`. It provides:
- 1rem side padding at SM
- 3rem side padding at MD through XL
- `max-width: 1320px` centered at XXL (≥ 87.5rem)

Do **not** use Bootstrap's `.container` class in v2 templates.

---

## Preserve analytics and functional logic

When redesigning or replacing an existing template or element, carry over all non-presentational logic from the original:

- Analytics blocks (`{% block analytics_* %}`, `data-module`, `data-module-*` attributes)
- SEO blocks (`{% block meta %}`, `{% block subtitle %}`, `structured_data`)
- Functional Jinja blocks (`{% block scripts %}`, `{% block head_extras %}`, etc.) that load page-specific assets or set page state
- Conditional snippets tied to runtime data (e.g. `alert_bar`)

Only the visual structure (HTML elements, BEM classes, CSS) changes. Logic is not optional.

---

## Interaction states: pseudo-classes vs. state classes

Use CSS pseudo-classes for transient, user-triggered states.
Use `is-*` classes only for persistent states set by the server or JavaScript.

| State | Correct approach |
|-------|-----------------|
| Hover | `:hover` in LESS |
| Focus | `:focus-visible` in LESS |
| Pressed | `:active` in LESS |
| Selected / current | `is-active` class (server or JS) |
| Unavailable | `is-disabled` class (server or JS) |
| Expanded | `is-open` class (JS only) |
| Scroll lock (body) while an overlay is open | `is-<component>-open` class on `<body>` (JS only), e.g. `is-drawer-open` |

Do **not** add `is-hovered`, `--hovered`, `is-focus`, or similar classes to templates or JavaScript. If a JS controller must replicate hover visuals (e.g. keyboard navigation), use a clearly named parent-class such as `c-component--keyboard-active` and add a comment in the LESS file explaining why the class exists.

---

## Constant border widths

Border-width never changes between component states (default / hover / focus /
active). State changes are conveyed by `border-color` only:

```less
.c-example {
    border:     1px solid var(--hdx-neutral-1);
    transition: border-color 0.15s ease;

    &:hover { border-color: var(--hdx-neutral-8); }
}
```

- State rules use `border-color:` — never the `border:` shorthand, which
  silently re-declares the width. Transitions target `border-color`.
- Extra focus emphasis uses a layout-safe `outline`
  (`outline: 1px solid …; outline-offset: 0` reads as a 2px ring with the
  1px border). Error variants recolor the ring.
- Fixed component heights are Figma size specs, not border compensation.
- Constant decorative borders of other widths are fine; reserving space for an
  active-state border uses a `transparent` default (`.c-nav-item` underline).

See [007-stable-border-width-across-states.md](requirements/007-stable-border-width-across-states.md).

---

## Alerts — `c-alert`

All alert-shaped feedback — page-level flash banners (`v2/page.html`) and
form/drawer error & status messages — uses the shared `c-alert` component
(`templates/v2/components/alert.html` + `less/v2/components/alert.less`),
whether server-rendered (Contact Contributor error summary, login page,
flash messages) or JS-toggled (notification drawers, org-members group
message and request approve/decline, org member add/remove/invite flash).

- Variants: `success` | `warning` | `info` | `error` (default). Pass
  `variant='...'` to the snippet; never hand-roll a colored `<p>` for a
  status message.
- Visibility contract: visible by default; JS-managed instances render with
  `hidden=True` and toggle the `hidden` **attribute** (`alert.hidden = false`).
  No `is-visible`/display classes.
- Dismissible by default (renders a `.c-alert__close` button); pass
  `dismissible=False` only when there's a specific reason an instance
  shouldn't be dismissed independently of the surrounding form/drawer.
- JS must never set `.textContent`/`.innerHTML` on the `.c-alert` element
  itself — that wipes the close button. Target the nested `.c-alert__message`
  span instead.
- Do not create page- or drawer-specific alert classes.
- Full-screen "success state" swaps (Contact Contributor, Request Access,
  Forgot Password) that re-title an entire page/card header are a distinct,
  intentional pattern — not alert messages — and are out of scope for this
  component.

---

## Layout widths

Do **not** use fixed `rem` or `px` for layout column widths. Use flex ratios (`flex: 1`, `flex: 2`) or `width: 100%` instead.

Exceptions: global container cap (1320px), fixed-height elements (buttons, inputs), icon dimensions.

---

## Page-title scale — `.hdx-page-title-scale()`

Canonical top-of-page title scale (24 → 28 → 32px Bold) in `mixins.less`, shared by `c-page-header`'s
hero `<h1>` and the homepage's section headings (`.hdx-section-heading()`).

---

## List header pattern — `.hdx-list-header-count()` / `-empty()`

The search page's header block (`hdx-v2-list-header`) and the org Members tab's heading row
(`hdx-v2-org-members__header`) share the same row shape via `.hdx-list-header-row()` /
`.hdx-list-header-row-left()` in `mixins.less` — title+count grouped left, sort/filter controls
pushed right by the left group's `flex:1`. Their titles call `.hdx-section-title()` like every
other in-page heading, *except* on the main `/dataset` search page, where an `emphasize_title`
param bumps the title (and its count) to the page-title font-size scale instead. Dataviz Gallery
and Archived Dataviz reuse `c-page-header` directly (`title` + `title_count` params) instead. The
count styling is factored into `.hdx-list-header-count()` (base: family/weight/color, no size) plus
`.hdx-section-title-count()` (adds the 18→20px ramp, used by the default list-header and Members
tab) or `.hdx-page-title-font-size()` directly (24/28/32px, used by the `emphasize_title` variant
and `c-page-header`'s own `title_count` badge).

---

## Page-section pattern — `.hdx-page-section-wrapper()` / `-header()` / `-body()`, `.hdx-section-title()`

Pages with their own anchor-linked content sections (`hdx-v2-dataset-section` on the dataset page,
`hdx-v2-resource-section` on the resource page) own their own BEM block rather than a shared `c-*`
component — each page has its own extra variants (the dataset page adds `&__title-row`, `&__chevron`,
and a `&--collapsible` modifier the resource page doesn't need). The padding/scroll-margin/header/
body styling is factored into `mixins.less` (`.hdx-page-section-wrapper()`, `.hdx-page-section-header()`,
`.hdx-page-section-body()`) — call these instead of re-declaring the rules.

The section title itself calls `.hdx-section-title()` (18px SM / 20px MD+ Semibold) — also used by
org's tab titles, HAPI's/Signals' landing sections, the country page's "Data Grid Availability"
heading, and the Locations page's controls heading and per-letter dividers.

---

## Design tokens

- CSS custom properties: `--hdx-<category>-<step>` (e.g. `--hdx-brand-5`, `--hdx-space-3`)
- LESS variables: same name with `@` (e.g. `@hdx-brand-5`) — LESS-only, not used in media queries
- No hardcoded hex colors, `rgba(...)` overlays, or box-shadow values in component LESS — use the corresponding token (`var(--hdx-neutral-1)`, `var(--hdx-overlay-white-10)`, `var(--hdx-shadow-md)`)
- Component-level LESS variables use `@c-*` prefix and are **not** exported as CSS custom properties
- **Only declare a file-local LESS variable if it's referenced 2+ times in that file** (this applies to any local variable, not just `@c-*` ones — e.g. a page file's one-off `@hero-bg`). A value used exactly once is written inline at its call site instead, carrying over the declaration's trailing comment if the call site doesn't already have one. Remove the "Local tokens" header comment block entirely once every token under it has been inlined.

---

## Accessibility (WCAG 2.1 AA) — mandatory for all v2 tasks

These constraints apply to every component, template, and JS file in the v2 redesign. See `llm_docs/redesign/requirements/041-accessibility-wcag-audit.md` for the full rationale.

### Keyboard interactions

Every interactive element must be fully operable by keyboard. For custom interactive elements:

- Use `<button>` for actions, `<a href>` for navigation — never `<div>`/`<span>` as interactive targets
- `click` handlers on buttons/links already fire on Enter; add a `keydown` handler for `Space` if needed for `<button>` elements used as toggles
- Dropdowns and panels: `Escape` closes and returns focus to the trigger

### ARIA state attributes

Update ARIA attributes whenever state changes:

| State | Attribute |
|-------|-----------|
| Panel open/closed | `aria-expanded="true/false"` on the trigger |
| Widget hidden/visible | `aria-hidden="true/false"` |
| Current nav item | `aria-current="true"` |
| Tooltip association | `aria-describedby` on trigger, `id` + `role="tooltip"` on tooltip element |

### Focus management

Overlays that block page content (offcanvas drawer, modal, full-screen overlay) must:
1. Move focus inside on open (use `window.hdxV2.FocusTrap` — shared in `v2/utils.js`)
2. Trap Tab/Shift+Tab within the overlay
3. Close on Escape
4. Return focus to the triggering element on close

Dropdowns (non-modal): move focus to first item on keyboard-triggered open; return focus to trigger on close.

### SVG icons

All inline SVG icons must carry `aria-hidden="true" focusable="false"`. Icon-only interactive elements require an `aria-label` on the parent `<button>` or `<a>`.

```html
<!-- decorative icon inside labeled button -->
<button aria-label="Close menu">
  <svg aria-hidden="true" focusable="false" ...></svg>
</button>
```

### prefers-reduced-motion

**CSS**: components call the `.hdx-motion()` mixin (`mixins.less`) instead of writing `transition`/`animation` directly. **JS**: guard programmatic animation via `window.hdxV2.prefersReducedMotion()` (`fanstatic/v2/utils.js`).

Both are currently no-ops — `.hdx-motion()`'s body is commented out and `prefersReducedMotion()` is hardcoded to `return false` — pending a follow-up pass (task 069). Reduced-motion preference is not honored anywhere in v2 yet.

### Screen-reader utilities

`.sr-only` and `.sr-only--focusable` are defined in `foundation.less`. Use for:
- Skip-to-main-content link (first focusable element in `<body>`)
- `aria-live` status regions (copy success, form feedback)
- Any text needed by AT but not visible on screen

### Status messages

Any user action that produces a success/error state must announce via a live region already in the DOM:

```html
<span class="sr-only" aria-live="polite" data-copy-status></span>
```

```js
statusEl.textContent = 'Copied to clipboard';
setTimeout(function () { statusEl.textContent = ''; }, 2000);
```

---

## Template inclusion — `{% snippet %}` vs `{% include %}`

| Target | Method | Rationale |
|---|---|---|
| v2 components | `{% snippet 'v2/components/...' %}` | Always — enables parameterisation |
| v2 layout sections (header, footer) | `{% snippet 'v2/...' %}` | Consistency |
| Inline SVG icons | `{% include h.url_for_static(path) %}` | Inlines SVG markup at render time |

Never use `{% include %}` for parameterised v2 templates. The only accepted `{% include %}` pattern in v2 is SVG inlining via `h.url_for_static()`.

---

## Layout variable completeness

**Two-column pages** (sidebar + content): set all four layout variables at the top of the template:

```jinja2
{% set outer_row_class = '...' %}
{% set columns_class   = '...' %}
{% set sidebar_class   = '...' %}
{% set content_class   = '...' %}
```

Leaving any of these unset produces an unclassed wrapper div and makes CSS targeting impossible.

**Single-column pages** (no sidebar): set `content_class` only. `page.html` applies `content_class` whenever it is defined (the former guard `and secondary_block_output != ''` was removed). Use the generic content class — it provides `flex: 1; min-width: 0`:

```jinja2
{% set content_class = 'hdx-v2-content-columns__content' %}
```

Append a page class after it only when the page needs extra content-column styling (padding, alignment).

Never leave a single-column page without `content_class` — without it the content div has no `flex:1` and will not fill the container width.

### `breadcrumb_row_class` — white breadcrumb variant

Pages that need a white breadcrumb row (no bottom border) set:

```jinja2
{% set breadcrumb_row_class = 'hdx-v2-breadcrumb-row--white' %}
```

The `--white` modifier is defined in `layout.less`. Do **not** override `{% block toolbar %}` to hardcode the class — set this variable instead.

---

## `v2=True` gate policy

Pages are gated with `{% if v2 %}` during rollout and promoted to always-v2 when v1 is retired for that page. Do not remove a gate without a deliberate, documented decision.

---

## Web assets — file naming

Page-level LESS and JS files (non-component, non-layout) live in a `pages/` subdirectory (mirroring `components/`) with no `-page` suffix — the directory already conveys that:

| Type | Pattern | Examples |
|---|---|---|
| Page styles | `pages/{page-name}.less` | `pages/search.less`, `pages/dataset.less`, `pages/home.less` |
| Page scripts | `pages/{page-name}.js` | `pages/search.js`, `pages/dataset.js` |
| Component | `{component-name}.less/.js` | `anchor-links.less`, `dropdown.js` |
| Layout / global | descriptive, no suffix | `layout.less`, `navbar.less`, `bar-chart.js`, `nav-controls.less` |

---

## Web assets — bundle naming

Bundle keys mirror their file naming pattern: `v2-{page-name}-page-{styles|scripts}`.

```
v2-components-styles / v2-components-scripts   # design system — all v2 pages (via preload)
v2-page-styles / v2-page-scripts               # layout + global — all v2 pages (explicit in page.html)
v2-{page-name}-page-styles / -scripts          # page-specific — loaded only on that page
v2-{lib-name}-scripts                          # shared utility lib — loaded explicitly in each consuming template
```

---

## Web assets — preload chain

Only the two foundational bundles may declare `extra: preload:` in `webassets.yml`:
- `v2-page-styles` preloads `v2-components-styles`
- `v2-page-scripts` preloads `v2-components-scripts` + `v2-search-scripts`

All other page-specific bundles have **no preload**. Their dependencies are already loaded by the time they run because `v2/page.html` always loads the base bundles first.

Shared utility lib bundles (`v2-{lib-name}-scripts`, e.g. `v2-carousel-scripts`) are **not** declared as preloads. Load them explicitly with `{% asset %}` in the consuming template, before the page-specific bundle:

```jinja2
{% block scripts %}
  {{ super() }}
  {% asset 'hdx_theme/v2-carousel-scripts' %}
  {% asset 'hdx_theme/v2-signals-landing-page-scripts' %}
{% endblock %}
```

---

## Web assets — page-only code belongs in the page bundle

Scripts and styles used exclusively on one page go into that page's bundle, not `v2-page-scripts`/`v2-page-styles`. Examples that were corrected: `highlights-carousel.js` + `Hammer.js` → `v2-home-page-scripts`; `pages/search.js` → `v2-search-page-scripts`.

---

## One LESS file per component

Each component gets its own file in `components/`. Do not group unrelated components in a single file (the old `navigation.less` pattern that mixed `c-nav-item`, `c-anchor-links`, `c-pagination`, `c-breadcrumb` is the anti-pattern).

---

## Form-field components — which one to use

Three distinct components cover form fields; pick by field type, don't extend the wrong one:

- `search-input.html` — search boxes only (`type='search'`).
- `text-field.html` — generic text/email/password/textarea fields (password-toggle, multiline).
- `select.html` — native `<select>`-backed fields.

`search-input.html` used to cover the generic-field role too; it split into `text-field.html` once form pages (contact contributor, request access, auth) needed password toggles and textareas.

---

## Component wrapper ownership

Containers that lay out a set of `c-*` components (card lists, card grids)
belong to the **component's own LESS file** as sibling blocks — never to page
files:

- `c-<name>-list` — vertical flex list (`c-dataset-card-list`,
  `c-resource-card-list`, `c-org-list-card-list`, `c-member-list-card-list`,
  `c-activity-card-list`, `c-stats-card-list`)
- `c-<name>-grid` — grid (`c-content-card-grid`, `c-selection-item-grid`,
  `c-showcase-card-grid`, `c-dataviz-card-grid`)
- `c-<name>-row` — inline flex-wrap row (`c-kpi-card-row`, `c-selection-item-row`)

Child sizing lives inside the wrapper, scoped with a direct-child selector
(`> .c-stats-card { flex: 1; }`). Pages must not size or restyle `c-*`
children directly — if a component needs a contextual variant, add a modifier
to the component (`c-search-input--block`, `c-dropdown--inline`,
`c-page-header--compact-title`) and pass it via `extra_classes`.

Page LESS keeps only page-rhythm concerns around the wrapper (e.g.
`padding-bottom` on the org-list section) and full-bleed page bands
(`*-header-section` wrappers), which are page-owned.

---

## Inline single-consumer utilities

If a utility class or function has exactly one consumer and no realistic reuse case, inline it into the consumer rather than maintaining a separate component file. Promote it to a shared module (`utils.js`) the moment a second consumer needs the same logic — never copy it. (`FocusTrap` started inlined into `navbar.js` from `focus-trap.js`; once `components/drawer.js` needed the same Tab-trap logic, it moved to `window.hdxV2.FocusTrap` in `utils.js`.)

---

## LESS — always use design tokens

Use design tokens instead of raw values whenever a token exists:

```less
// Do
width:  var(--hdx-space-1);    // 4px
gap:    var(--hdx-space-3);    // 12px
.hdx-body-s-medium();          // 14px medium

// Don't
width:  0.25rem;
gap:    12px;
font-family: var(--hdx-font-body);
font-size: var(--hdx-fs-s);
font-weight: var(--hdx-fw-medium);
```

Figma-specific values with no corresponding token (e.g. `7.05rem`, `11.25rem`) may stay raw — add a `// Figma spec` comment.
