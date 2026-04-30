# Task 013: Load Bootstrap in v2 page bundle

Add Bootstrap 5 to the v2 page asset bundle so that Bootstrap classes used in `v2/page.html` (`container`, `alert`, `alert-dismissible`, `fade`, `breadcrumb`) are actually styled.

## Context

`v2/page.html` overrides `{% block styles %}` without calling `{{ super() }}`, so the legacy `page-common-styles` bundle (which includes Bootstrap) is never loaded on v2 pages. Bootstrap classes in the template have no stylesheet backing.

## What to update

### `fanstatic/webassets.yml`

Add a new `v2-page-styles` bundle that loads Bootstrap and preloads the existing component bundle:

```yaml
v2-page-styles:
  output: ckanext-hdx_theme/%(version)s_v2-page-styles.css
  <<: *common-css
  extra:
    preload:
      - hdx_theme/v2-components-styles
  contents:
    - vendor/bootstrap5/css/bootstrap.css
```

Keep `v2-components-styles` unchanged — it is the standalone design system bundle for non-page contexts (component previews, embedded widgets).

### `templates/v2/page.html`

Replace:
```
{% asset 'hdx_theme/v2-components-styles' %}
```
with:
```
{% asset 'hdx_theme/v2-page-styles' %}
```

### Verify

Confirm in browser DevTools that `fanstatic/base/layout.css` and `fanstatic/base/base.css` are **not** loaded on v2 pages. These files hard-code a 1170px container width and disable Bootstrap's responsive behaviour — they must not apply to v2 pages. Because `v2/page.html` fully replaces the styles block, this should already be the case.

## Why

`v2-components-styles` is kept separate to preserve its usefulness outside full-page contexts. Bootstrap is a page-level dependency and belongs in the page bundle, loaded after the design system so component overrides take precedence.
