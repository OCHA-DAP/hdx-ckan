# Task 025: Implement c-activity-card component

## Goal

Create a reusable activity card component with an icon, heading, subtitle, and CTA button. Supports three sizes (lg, md, sm) and two states (enabled, hovered).

## Scope

**In:**
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/activity-card.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/activity-card.less`
- Sizes: `lg`, `md`, `sm`
- States: `enabled`, `hovered`

**Out:**
- JS interactivity, data fetching, button click handlers (consuming page's concern)

## Requirements

1. Create c-activity-card component structure.
   - BEM block: `.c-activity-card`
   - Size modifiers: `.c-activity-card--size-lg`, `--size-md`, `--size-sm`
   - Hover state: `.is-hovered`
   - Internal layout (column flex, full width):
     ```
     .c-activity-card
       .c-activity-card__header     ← column flex; contains icon and body
         .c-activity-card__icon     ← 24×24px img or inline SVG
         .c-activity-card__body     ← column flex; contains heading and subtitle
           .c-activity-card__heading
           .c-activity-card__subtitle
       .c-activity-card__footer     ← button slot
     ```

2. Implement common styles.
   - Background: `var(--hdx-neutral-0)`
   - Border-radius: `var(--hdx-radius-sm)`
   - Shadow: `var(--hdx-shadow-sm)`
   - Icon width: `1.5rem` (24px); height auto
   - Heading: `var(--hdx-font-display)`, `font-weight: bold`, `line-height: 130%`
   - Subtitle: `var(--hdx-font-body)`, `color: var(--hdx-neutral-7)`, `line-height: 130%`
   - All transitions: `0.15s ease`

3. Implement size variants.

   | Property       | `--size-lg`             | `--size-md`             | `--size-sm`             |
   |----------------|-------------------------|-------------------------|-------------------------|
   | padding        | `--hdx-space-8` (32px)  | `--hdx-space-6` (24px)  | `--hdx-space-5` (20px)  |
   | card gap       | `--hdx-space-12` (48px) | `--hdx-space-10` (40px) | `--hdx-space-8` (32px)  |
   | header gap     | `--hdx-space-6` (24px)  | `--hdx-space-5` (20px)  | `--hdx-space-4` (16px)  |
   | body gap       | `--hdx-space-4` (16px)  | `--hdx-space-4` (16px)  | `--hdx-space-3` (12px)  |
   | heading size   | 28px (`--hdx-fs-2xl`)   | 24px (`--hdx-fs-xl`)    | 20px (`--hdx-fs-l`)     |
   | subtitle size  | 18px                    | `--hdx-fs-m` (16px)     | `--hdx-fs-m` (16px)     |

   For the lg subtitle (18px): use the nearest available token or define a local token.

4. Implement state styling.
   - **enabled**: `border: 1px solid var(--hdx-neutral-1)`
   - **hovered**: `border: 1.5px solid var(--hdx-neutral-7)`
   - Apply `transition: border 0.15s ease`

5. Reuse existing button component for the footer.
   - Call `{% snippet 'v2/components/button.html', style='primary', size='l', type='text', label=button_label, tag='a', href=button_href %}`
   - Constrain button max-width to `12.5rem` (200px) via `.c-activity-card__footer`

6. Create CKAN snippet with parameters.
   - `size` (string): `'lg'` | `'md'` | `'sm'`, default: `'md'`
   - `state` (string): `'enabled'` | `'hovered'`, default: `'enabled'`
   - `icon_src` (string): path to icon SVG, default: `''`
   - `heading` (string): card heading text, default: `''`
   - `subtitle` (string): subtitle/description text, default: `''`
   - `button_label` (string): button CTA text, default: `''`
   - `button_href` (string): button link URL, default: `'#'`
   - `extra_classes` (string): additional CSS classes, default: `''`

7. Define local LESS tokens at the top of the file, mapped from global foundations.
   - Follow the pattern in `checkbox.less` and `list-item.less`: declare `@c-activity-card-*` variables first, then the block rules.

## Reference

- Figma export: `ckanext-hdx_theme/llm_docs/redesign/figma_exports/hdx-activity-card.html`
- Button snippet: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/button.html`
- Design tokens: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/foundation.less`
- Comparable requirement: `requirements/004-implement-list-item-component.md`
