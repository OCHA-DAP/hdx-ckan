---
id: 013
title: Bootstrap integration in v2/page.html
status: ready
---

# REQ-013: Bootstrap Integration in v2/page.html

## Context

`v2/page.html` extends `base.html` but overrides the `styles` block without calling `{{ super() }}`.
As a result, **no Bootstrap CSS is currently loaded** on v2 pages, even though Bootstrap classes
are used in the template (`container`, `alert`, `alert-dismissible`, `fade`, `breadcrumb`).

The only bundle loaded is `hdx_theme/v2-components-styles`, which contains the HDX design system
tokens and component CSS — Bootstrap is not in it.

Bootstrap 5.2.3 is vendored at `fanstatic/vendor/bootstrap5/css/`.

---

## Requirements

### 1. Create a `v2-page-styles` webassets bundle

Create a new webassets bundle in `webassets.yml` named `v2-page-styles` that loads, **in order**:

1. Bootstrap CSS — use the full `bootstrap.css` (not grid-only) to cover resets, utilities,
   and alert styles used in the template.
2. All contents currently in `v2-components-styles` (design tokens + components).

Rationale for a separate bundle rather than adding Bootstrap to `v2-components-styles`:
the component bundle is a self-contained design system and may eventually be used outside
full-page contexts; Bootstrap is a page-level dependency.

### 2. Update `v2/page.html` to use the new bundle

Replace:
```
{% asset 'hdx_theme/v2-components-styles' %}
```
with:
```
{% asset 'hdx_theme/v2-page-styles' %}
```

The `v2-components-styles` bundle can remain for contexts where only design system CSS
is needed (e.g. component previews, embedded widgets).

### 3. Verify no legacy overrides bleed in

Confirm that the following files are **not** loaded on v2 pages:

- `fanstatic/base/layout.css` — hard-codes a 1170px container and disables responsive behavior
- `fanstatic/base/base.css` — sets `min-width: 1260px` on body and overrides container `max-width`

Because `v2/page.html` fully replaces the styles block, these should already be excluded.
Verify in-browser with DevTools and add a note in the template if confirmed.
