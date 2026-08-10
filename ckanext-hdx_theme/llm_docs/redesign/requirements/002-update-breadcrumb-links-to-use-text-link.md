# Task 002: Update breadcrumb links to use c-text-link component

## Goal

Refactor the breadcrumb component's link implementation to use the existing `c-text-link` component instead of custom `c-breadcrumb__link` styles.

## Scope

**In:**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/breadcrumb.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/breadcrumb.less` (breadcrumb link styles)
- Ensuring breadcrumb links use `c-text-link` with tertiary style, xs size, enabled state

**Out:**
- Changes to the `c-text-link` component itself
- Updates to other navigation components across `anchor-links.less` / `breadcrumb.less` / `nav-item.less` / `pagination.less`

## Requirements

1. Update breadcrumb.html template.
   - Replace the `<a class="c-breadcrumb__link">` elements with the `c-text-link` snippet.
   - Configure the text-link with: `style='tertiary'`, `size='xs'`, `state='enabled'`.
   - Pass the appropriate `href` and `label` parameters to the text-link snippet.

2. Update breadcrumb.less styles.
   - Remove the `.c-breadcrumb__link` style rules from the breadcrumb section.
   - Ensure no breadcrumb-specific link styles remain that conflict with `c-text-link`.

3. Verify the implementation.
   - Confirm that breadcrumb links render with the correct tertiary text-link appearance.
   - Ensure hover, focus, and active states work as expected through the text-link component.
