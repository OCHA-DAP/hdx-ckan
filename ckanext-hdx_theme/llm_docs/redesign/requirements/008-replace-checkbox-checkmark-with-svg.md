# Task 008: Replace checkbox checkmark with SVG icon

## Goal

Replace the CSS `::after` pseudo-element used as the checkmark in `.c-checkbox__box` with the `v2/icons/check.svg` icon, loaded the same way as other v2 component snippets.

## Why this is useful

The current `::after` approach produces the checkmark by rotating a partial border, which is fragile and diverges from the Figma source. An SVG icon is explicit, pixel-accurate, and consistent with how every other v2 component renders icons.

## Scope

### In scope

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/checkbox.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/checkbox.less`
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/icons/check.svg` (already added, read-only)

### Out of scope

- Component API (parameters remain unchanged)
- Compiled CSS in `fanstatic/` (regenerated from LESS, do not edit manually)
- Any other component that references or composes `c-checkbox`

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

## Verification

1. Render the checkbox in checked and unchecked states — icon should appear and disappear correctly.
2. Toggle disabled + checked — icon should render in muted (`--hdx-neutral-3`) color.
3. Tab to the checkbox — focus ring should appear (keyboard navigation unchanged).
4. Inspect the DOM — no `::after` pseudo-element on `.c-checkbox__box`.
5. Zoom to 200% — icon scales cleanly without aliasing.
