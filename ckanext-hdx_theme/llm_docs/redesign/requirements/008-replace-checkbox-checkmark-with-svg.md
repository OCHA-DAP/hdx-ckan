# Task 008: Replace checkbox checkmark with SVG icon

## Goal

Replace the CSS `::after` pseudo-element checkmark in `.c-checkbox__box` with `v2/icons/check.svg`, consistent with how all other v2 components render icons.

## Scope

**In:**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/checkbox.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/checkbox.less`
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/icons/check.svg` (already added, read-only)

**Out:**
- Component API (parameters unchanged)
- Compiled CSS in `fanstatic/` (auto-generated, do not edit manually)
- Other components that compose `c-checkbox`

## Requirements

1. **Remove `::after` from `.c-checkbox__box`.**
   Delete the `&::after` block and its disabled+checked override (`border-color` on `::after`).

2. **Add the icon to the template using `{% include h.url_for_static(...) %}`.**
   Inside `.c-checkbox__box`, add a `<span class="c-checkbox__icon">` containing `{% include h.url_for_static('v2/icons/check.svg') %}`. This matches the pattern used in `label.html`, `nav-item.html`, and other v2 components.

3. **Size and color the icon via CSS.**
   - `check.svg` has viewBox `0 0 10 7`; size the span to `width: 0.625rem; height: 0.4375rem` (10 × 7 px).
   - Set `width: 100%; height: 100%` on the child `svg` element so it fills the span.
   - `color: @c-checkbox-checkmark-color` on `.c-checkbox__box` propagates via `currentColor` to the SVG stroke.

4. **Control visibility via CSS.**
   - Default: `.c-checkbox__icon { opacity: 0; transition: opacity 0.15s ease; }`
   - Checked: `&__input:checked ~ &__box .c-checkbox__icon { opacity: 1; }`
   - Disabled + checked: `color: @c-checkbox-disabled-border` on `.c-checkbox__box` mutes the icon via `currentColor`; opacity is still 1.

5. **Preserve all existing states without visual change.**
   - Unchecked: white background, `--hdx-neutral-2` border, icon hidden.
   - Checked: `--hdx-primary-5` background, no border, white icon visible.
   - Hover (not disabled): existing border-color rule unchanged.
   - Focus-visible: 2px solid `--hdx-primary-5` outline, 2px offset — unchanged.
   - Disabled unchecked: `--hdx-neutral-1` background, `--hdx-neutral-3` border, icon hidden.
   - Disabled checked: `--hdx-neutral-1` background, `--hdx-neutral-3` border, muted icon visible.

6. **Accessibility.**
   The included SVG already has no role or focusable attributes. Do not alter the hidden `<input type="checkbox">` or any existing ARIA attributes.

