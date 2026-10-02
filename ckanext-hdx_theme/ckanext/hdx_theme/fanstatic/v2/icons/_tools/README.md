# v2 icons

Files in `fanstatic/v2/icons/` are served at `/v2/icons/<name>.svg`; templates render them with `{{ h.hdx_v2_icon('v2/icons/<name>.svg') }}` (or a component's `icon_src`).

## Add or update an icon

1. Export the icon from Figma as SVG.
2. Save it in `fanstatic/v2/icons/` (flags in `locations-flags/`, data-grid categories in `humanitarian-data-grids/`).
3. Run `python ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/icons/_tools/normalize.py --colors`.
4. Use it: `{{ h.hdx_v2_icon('v2/icons/<name>.svg') }}`.

The script, over the whole icons folder: lowercases filenames (spaces/`_` → `-`, accents dropped), removes `width`/`height`, adds `aria-hidden="true" focusable="false"`, drops Figma's clip, and wraps the content in `<symbol id="i">` + `<use href="#i"/>`. `--colors` sets every fill and stroke to `currentColor`, except in `locations-flags/`. Re-running it is safe.

It also generates `helpers/v2_icon_view_boxes.py` (every icon's viewBox), which `h.hdx_v2_icon` imports to size the page `<svg>`: re-run the script and commit that file whenever you add or change an icon (an icon missing from it still renders, as 16×16, and logs a warning).

Prod caches `.svg` for 30 days: an edited icon reaches returning visitors within 30 days, so save it under a new name to show it at once.

Icons are decorative (`aria-hidden`): give icon-only buttons and links an `aria-label`.
