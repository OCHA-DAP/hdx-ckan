# Task 014: Align Bootstrap container with Figma grid specs

Override Bootstrap's `.container` on v2 pages to match the Figma margin and max-width specs across all breakpoints. Scoped to the `.hdx-v2` body class so legacy pages are unaffected.

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
@v2-container-padding-xs:  1rem;     // 16px — XS + SM
@v2-container-padding-md:  3rem;     // 48px — MD through XL
@v2-container-max-width:   1320px;   // XXL centered
@v2-breakpoint-md:         768px;
@v2-breakpoint-xxl:        1400px;

.hdx-v2 .container {
    max-width: 100%;
    padding-right: @v2-container-padding-xs;
    padding-left:  @v2-container-padding-xs;

    @media (min-width: @v2-breakpoint-md) {
        padding-right: @v2-container-padding-md;
        padding-left:  @v2-container-padding-md;
    }

    @media (min-width: @v2-breakpoint-xxl) {
        max-width:     @v2-container-max-width;
        padding-right: calc(var(--bs-gutter-x) * 0.5);
        padding-left:  calc(var(--bs-gutter-x) * 0.5);
        margin-right:  auto;
        margin-left:   auto;
    }
}
```

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

Add `class="hdx-v2"` to `<body>` via the `bodyclassname` block:

```
{% block bodyclassname %}hdx-v2{% endblock %}
```

## Why

Bootstrap's default `.container` at MD/LG/XL uses fixed max-widths (720px, 960px, 1140px) that don't match the Figma fluid-with-margin spec. The XXL max-width of 1320px already matches Figma's XL spec — no override needed there. All overrides are scoped to `.hdx-v2` so legacy pages using `.container` are unaffected.
