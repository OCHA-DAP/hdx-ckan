# v2 Redesign — Implementation Conventions

Single source of truth for general rules. Update here; do not duplicate in task files.

---

## BEM class prefixes

| Prefix | Used for | Example |
|--------|----------|---------|
| `c-` | Reusable components | `c-button`, `c-autocomplete` |
| `hdx-v2-` | Non-reusable v2 sections and layouts | `hdx-v2-hero`, `hdx-v2-grid` |

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

---

## Breakpoints

Defined **once** in `breakpoints.less`. Any file that uses breakpoints imports it. No local redefinitions.

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
- **Inner element** — add `hdx-container` class for horizontal padding and max-width; set flex/grid layout here

```html
<section class="hdx-v2-hero">
  <div class="hdx-v2-hero__inner hdx-container">...</div>
</section>
```

`.hdx-container` is defined in `layout.less`. It provides:
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

## Design tokens

- CSS custom properties: `--hdx-<category>-<step>` (e.g. `--hdx-brand-5`, `--hdx-space-3`)
- LESS variables: same name with `@` (e.g. `@hdx-brand-5`) — LESS-only, not used in media queries
- No hardcoded hex colors, `rgba(...)` overlays, or box-shadow values in component LESS — use the corresponding token (`var(--hdx-neutral-1)`, `var(--hdx-overlay-white-10)`, `var(--hdx-shadow-md)`)
- Component-level LESS variables use `@c-*` prefix and are **not** exported as CSS custom properties
