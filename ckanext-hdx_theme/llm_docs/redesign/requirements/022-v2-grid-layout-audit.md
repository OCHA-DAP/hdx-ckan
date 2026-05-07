# Task 022: Review and align v2 grid/layout system

Audit and align the v2 layout against the Figma grid spec across all breakpoints. The container override is already in place (`layout.less`); this task verifies it is correct, documents the rules for full-bleed components, and establishes the grid contract for future v2 page templates.

---

## Grid reference spec

| Breakpoint | Range       | Columns | Side margin | Gutter | Container behaviour             |
|------------|-------------|---------|-------------|--------|---------------------------------|
| XS         | < 576px     | 4       | 16px        | 24px   | Fluid                           |
| MD         | ≥ 768px     | 12      | 48px        | 24px   | Fluid                           |
| XL         | ≥ 1200px    | 12      | 48px        | 24px   | Fluid                           |
| XXL        | ≥ 1400px    | 12      | —           | 24px   | Max-width 1320px, centered      |

Gutters are 24px at all breakpoints — matches Bootstrap's default `--bs-gutter-x: 1.5rem`, no override needed.

The Figma XS layout uses 4 columns. Bootstrap always uses 12; each Figma column maps to `col-3`.

---

## Container rules

The `.container` override in `layout.less` is the canonical grid implementation for v2 content areas. It must behave as follows:

```less
.hdx-v2 .container {
    max-width: 100%;
    padding-right: @container-padding-xs;   // 1rem  — 16px (XS, SM)
    padding-left:  @container-padding-xs;

    @media (min-width: @hdx-bp-md) {        // 768px
        padding-right: @container-padding-md;  // 3rem — 48px (MD, LG, XL)
        padding-left:  @container-padding-md;
    }

    @media (min-width: @hdx-bp-xxl) {       // 1400px
        max-width:     @container-max-width;   // 1320px — centered (XXL)
        padding-right: calc(var(--bs-gutter-x) * 0.5);
        padding-left:  calc(var(--bs-gutter-x) * 0.5);
        margin-right:  auto;
        margin-left:   auto;
    }
}
```

Verify that `layout.css` (compiled output) matches this and is present in the `v2-page-styles` bundle in `webassets.yml`.

---

## Full-bleed components

Topbar, navbar, footer, and other full-bleed sections use `.container` on their inner wrapper element for horizontal padding and max-width. The outer element handles background and vertical padding only. See [CONVENTIONS.md](../CONVENTIONS.md) — "Container and full-bleed sections".

Verify that these values are present in `top-bar.less`, `navbar.less`, and `footer.less` and that no `.container` wrapper has been introduced inside these components.

---

## Content page templates

Every v2 page template that renders content (breadcrumbs, flash messages, page body) must follow this structure:

```html
<!-- Correct: content always inside .container -->
<div class="container">
  <!-- page content -->
</div>
```

When a page uses Bootstrap rows and columns inside a `.container`, rows must declare an explicit gutter class matching the 24px spec:

```html
<div class="container">
  <div class="row g-3">   <!-- g-3 = 24px gutter -->
    <div class="col-12 col-md-6">…</div>
    <div class="col-12 col-md-6">…</div>
  </div>
</div>
```

Use `g-3` (24px) for standard column grids. Use `g-4` (32px) only where Figma explicitly specifies a larger gap (e.g. footer nav columns).

---

## Review checklist

### `templates/v2/page.html`
- [ ] `<body>` carries the `hdx-v2` class via `{% block bodyclassname %}hdx-v2{% endblock %}`
- [ ] Breadcrumb/toolbar row wraps content in `.container`
- [ ] Flash messages wrap content in `.container`
- [ ] The `{% block content %}` region does not impose its own container (individual page templates are responsible)

### `templates/v2/header.html`
- [ ] `.hdx-v2-top-bar__inner` applies correct side padding (no `.container` inside)
- [ ] `.hdx-v2-navbar__inner` applies correct side padding (no `.container` inside)
- [ ] No Bootstrap `.container` or `.container-fluid` is used inside the header

### `templates/v2/footer.html`
- [ ] Footer has direct side padding at each breakpoint (no `.container` inside)
- [ ] Nav grid uses `.row.g-4` with `col-12 col-md-4` columns
- [ ] No additional wrapper introduces conflicting horizontal padding

### `hdx-styles/src/common/less/v2/layout.less`
- [ ] Container override uses `@hdx-bp-md` and `@hdx-bp-xxl` from `breakpoints.less` (no magic numbers)
- [ ] Max-width of 1320px applies only at XXL (`@hdx-bp-xxl: 87.5rem`)
- [ ] Below XXL, `max-width: 100%` keeps the container fluid

### `fanstatic/webassets.yml`
- [ ] `v2/layout.css` is listed in `v2-page-styles` bundle, after `bootstrap.css`

### Any new v2 page templates
- [ ] Page-level content is wrapped in `.container`
- [ ] Bootstrap column grids inside content use `row g-3` (or documented exception)
- [ ] No inline `max-width`, `padding-left/right`, or `margin: auto` overrides that duplicate container behaviour

---

## Open question

**XL navbar breakpoint delta.** `breakpoints.less` defines `@hdx-bp-xl: 80rem (1280px)` — this is the point where the navbar switches from hamburger to inline navigation. The Figma grid spec marks XL as ≥ 1200px for layout margins only (48px, already covered by the MD rule). The two numbers do not conflict for grid purposes, but they diverge for nav visibility.

Before any changes to `@hdx-bp-xl`, confirm with design whether the navbar should display inline items at 1200px or 1280px. Do not change the breakpoint without that decision.

---

## Files to review

| File | Role |
|------|------|
| `hdx-styles/src/common/less/v2/layout.less` | Container override — source of truth |
| `hdx-styles/src/common/less/v2/breakpoints.less` | LESS breakpoint variables |
| `hdx-styles/src/common/less/v2/navbar.less` | Navbar padding and responsive behaviour |
| `hdx-styles/src/common/less/v2/top-bar.less` | Top-bar padding |
| `hdx-styles/src/common/less/v2/footer.less` | Footer padding and column grid |
| `fanstatic/v2/layout.css` | Compiled output — must match source |
| `fanstatic/webassets.yml` | Asset bundle inclusion |
| `templates/v2/page.html` | Page shell |
| `templates/v2/header.html` | Full-bleed header components |
| `templates/v2/footer.html` | Full-bleed footer component |
