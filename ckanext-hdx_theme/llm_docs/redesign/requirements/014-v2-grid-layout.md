# Task 014: Align Bootstrap container with Figma grid specs

Add a standalone `.hdx-v2-container` class matching the Figma margin and max-width specs across all breakpoints, applied directly to elements that need it. Bootstrap's own `.container` is never overridden — v2 templates don't use it at all.

## Breakpoint mapping

Figma uses different labels than Bootstrap:

| Figma | Figma range    | Bootstrap | Container behaviour                              |
|-------|----------------|-----------|--------------------------------------------------|
| XS    | < 576px        | XS        | Fluid, 16px side padding                         |
| —     | 576–767px      | SM        | Fluid, 16px side padding *(follows XS — no Figma spec)* |
| MD    | ≥ 768px        | MD        | Fluid, 48px side padding                         |
| —     | 992–1199px     | LG        | Fluid, 48px side padding *(follows MD — no Figma spec)* |
| LG    | ≥ 1200px       | XL        | Fluid, 48px side padding                         |
| XL    | ≥ 1400px       | XXL       | Max-width 1320px, centered                       |

Gutters are 24px at all breakpoints — matches Bootstrap's default `--bs-gutter-x: 1.5rem`, no override needed.

The Figma XS layout uses 4 columns. Bootstrap always uses 12; each Figma column maps to `col-3`.

## What to update

### `hdx-styles/src/common/less/v2/layout.less` (new file)

```less
@import "mixins.less";

@container-padding-xs:  1rem;     // 16px — SM
@container-padding-md:  3rem;     // 48px — MD through XL
@container-max-width:   1320px;   // XXL centered

.hdx-v2-container {
    max-width:     100%;
    padding-right: @container-padding-xs;
    padding-left:  @container-padding-xs;

    @media (min-width: @hdx-bp-md) {
        padding-right: @container-padding-md;
        padding-left:  @container-padding-md;
    }

    @media (min-width: @hdx-bp-xxl) {
        max-width:     @container-max-width;
        margin-right:  auto;
        margin-left:   auto;
    }
}
```

Breakpoints (`@hdx-bp-md`, `@hdx-bp-xxl`) come from the shared `mixins.less`/`breakpoints.less`, not locally-declared variables.

### `fanstatic/v2/layout.css` (compiled output — new file)

Compile `layout.less` and commit the output. The compiled CSS is what webassets serves.

### `fanstatic/webassets.yml`

Add `v2/layout.css` to the `v2-page-styles` bundle contents, after `bootstrap.css`:

```yaml
v2-page-styles:
  ...
  contents:
    - vendor/bootstrap5/css/bootstrap.css
    - v2/layout.css
```

### `templates/v2/page.html`

Add `class="hdx-v2"` to `<body>` via the `bodytag` block:

```
{% block bodytag %}{{ super() }} class="hdx-v2"{% endblock %}
```

Apply `.hdx-v2-container` directly to `__inner` elements of full-bleed sections — it's an opt-in class, not a Bootstrap override.

## Why

Bootstrap's default `.container` at MD/LG/XL uses fixed max-widths (720px, 960px, 1140px) that don't match the Figma fluid-with-margin spec. Rather than overriding Bootstrap's class and risk affecting other Bootstrap usage, `.hdx-v2-container` is a standalone class v2 templates opt into — legacy pages keep using Bootstrap's own `.container` untouched.
