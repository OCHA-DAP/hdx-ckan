# Task 013: Load Bootstrap in v2 page bundle

Add Bootstrap 5 to the v2 page asset bundle. `v2/page.html` no longer uses Bootstrap's `container`/`alert`/`breadcrumb` classes today (it uses `hdx-v2-container`, `c-alert`, and `c-breadcrumb` instead — CONVENTIONS.md bans Bootstrap's `.container` in v2 outright), but Bootstrap itself is still loaded as a page-level dependency for other v2 markup.

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

## Why

`v2-components-styles` is kept separate to preserve its usefulness outside full-page contexts. Bootstrap is a page-level dependency and belongs in the page bundle, loaded after the design system so component overrides take precedence.
