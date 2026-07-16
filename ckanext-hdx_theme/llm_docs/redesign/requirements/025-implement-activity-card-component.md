# Task 025: Implement c-activity-card component

## Goal

Create a reusable activity card component with an icon, heading, subtitle, and CTA button. Supports four size variants (lg, md, sm, responsive) and two states (enabled, hovered).

## Scope

**In:**
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/activity-card.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/activity-card.less`
- `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/components/activity-card.css`
- Sizes: `lg`, `md`, `sm`, `responsive`
- States: `enabled`, `hovered`

**Out:**
- JS interactivity, data fetching, button click handlers (consuming page's concern)

## Requirements

1. Create c-activity-card component structure.
   - BEM block: `.c-activity-card`
   - Size modifiers: `.c-activity-card--size-lg`, `--size-md`, `--size-sm`, `--size-responsive`
   - Hover state: `.is-hovered`
   - Internal layout (column flex, full width):
     ```
     .c-activity-card
       .c-activity-card__header     ← column flex; contains icon and body
         .c-activity-card__icon     ← inline SVG via {% include %}
         .c-activity-card__body     ← column flex; contains heading and subtitle
           .c-activity-card__heading
           .c-activity-card__subtitle
       .c-activity-card__footer     ← button slot
     ```

2. Implement common styles.
   - Background: `var(--hdx-neutral-01)`
   - Border-radius: `var(--hdx-radius-sm)`
   - Shadow: `var(--hdx-shadow-sm)`
   - Icon: `display: block; line-height: 0; flex-shrink: 0; width: 1.5rem;` — SVG inside fills 100% width, height auto
   - Heading: `var(--hdx-font-display)`, `font-weight: bold`, `line-height: var(--hdx-lh-normal)`
   - Subtitle: `var(--hdx-font-body)`, `color: var(--hdx-neutral-8)`, `line-height: var(--hdx-lh-normal)`
   - All transitions: `0.15s ease`

3. Implement size variants.

   | Property       | `--size-lg`             | `--size-md`             | `--size-sm`             |
   |----------------|-------------------------|-------------------------|-------------------------|
   | padding        | `--hdx-space-8` (32px)  | `--hdx-space-6` (24px)  | `--hdx-space-5` (20px)  |
   | card gap       | `--hdx-space-12` (48px) | `--hdx-space-10` (40px) | `--hdx-space-8` (32px)  |
   | header gap     | `--hdx-space-6` (24px)  | `--hdx-space-5` (20px)  | `--hdx-space-4` (16px)  |
   | body gap       | `--hdx-space-4` (16px)  | `--hdx-space-4` (16px)  | `--hdx-space-3` (12px)  |
   | heading size   | `--hdx-fs-3xl` (28px)   | `--hdx-fs-2xl` (24px)   | `--hdx-fs-xl` (20px)    |
   | subtitle size  | `--hdx-fs-l` (18px)     | `--hdx-fs-m` (16px)     | `--hdx-fs-m` (16px)     |

4. Implement `--size-responsive` variant.
   - Applies sm tokens by default (mobile-first), then overrides to md at `@hdx-bp-md` (48rem) and lg at `@hdx-bp-xl` (80rem).
   - Requires `@import "../breakpoints.less"` at the top of `activity-card.less`.
   - Use case: cards whose size should track the viewport automatically without the caller choosing a fixed size.

5. Implement state styling.
   - **enabled**: `border: 1px solid var(--hdx-neutral-1)`
   - **hovered**: `border-color: var(--hdx-neutral-8)` (constant 1px width, color-only)
   - Apply `transition: border-color 0.15s ease`

6. Reuse existing button component for the footer.
   - Call `{% snippet 'v2/components/button.html', style=button_style, size='l', type='text', label=button_label, tag='a', href=button_href %}`
   - Constrain button max-width to `12.5rem` (200px) via `.c-activity-card__footer`

7. Create CKAN snippet with parameters.
   - `size` (string): `'lg'` | `'md'` | `'sm'` | `'responsive'`, default: `'md'`
   - `state` (string): `'enabled'` | `'hovered'`, default: `'enabled'`
   - `icon_src` (string): path to icon SVG (e.g. `'v2/icons/search.svg'`), resolved via `h.url_for_static()` and inlined with `{% include %}`. Pass `''` to omit. default: `''`
   - `heading` (string): card heading text, default: `''`
   - `subtitle` (string): subtitle/description text, default: `''`
   - `button_label` (string): button CTA text. Pass `''` to omit the footer. default: `''`
   - `button_href` (string): button link URL, default: `'#'`
   - `button_style` (string): button style forwarded to `button.html`. Accepts `'primary'` | `'secondary'` | `'tertiary'`. default: `'primary'`
   - `extra_classes` (string): additional CSS classes, default: `''`

8. Icon rendering — use inline SVG pattern consistent with all other v2 components.
   - HTML: `<span class="c-activity-card__icon" aria-hidden="true">{% include h.url_for_static(icon_src) %}</span>`
   - Icons live in `templates/v2/icons/*.svg` (not `fanstatic/`). The `{% include h.url_for_static() %}` pattern resolves and inlines them at render time.
   - SVGs use `currentColor` for strokes — icon colour is inherited from the surrounding context.

9. Define local LESS tokens at the top of the file, mapped from global foundations.
   - Follow the pattern in `checkbox.less` and `list-item.less`: declare `@c-activity-card-*` variables first, then the block rules.

## Reference

- Figma export: `ckanext-hdx_theme/llm_docs/redesign/figma_exports/hdx-activity-card.html`
- Button snippet: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/button.html`
- Design tokens: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/foundation.less`
- Comparable requirement: `requirements/004-implement-list-item-component.md`
