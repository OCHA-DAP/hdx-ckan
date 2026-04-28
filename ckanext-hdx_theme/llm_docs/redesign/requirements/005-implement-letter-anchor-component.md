# Task 005: Implement c-letter-anchor component

## Goal

Refactor the letter anchor component to be a standalone, reusable component instead of relying on the `c-nav-item` styling. The letter anchor is a distinctly different interaction pattern from navigation items and should have its own dedicated component definition.

## Why this is useful

The current implementation uses `c-nav-item` styles for letter anchors, which conflates two different UI patterns:
- Navigation items (horizontal menu in header/top bar)
- Letter anchors (alphabet filtering, typically in sidebars)

By creating a dedicated component, we:
- Reduce confusion and maintenance burden
- Allow independent styling evolution
- Enable reuse in different contexts (sidebars, index lists, etc.) without nav-item baggage
- Clarify the component's intended use and states

## Scope

This task focuses on refactoring the letter anchor into a standalone component that currently exists in navigation.less.

### In scope

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/letter-anchor.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/letter-anchor.less`
- States: `enabled`, `hovered`, `active`, `disabled`
- Sizes: `lg` (large, 2.3125rem) and `sm` (small, 1.5rem)

### Out of scope

- Navigation item component (remain in navigation.less)
- List/grid layout for multiple letter anchors (that's a container concern)
- Sorting or filtering logic (component is presentational only)

## Requirements

1. Create c-letter-anchor component structure.
   - Root element: `.c-letter-anchor`
   - Size modifiers: `--size-lg`, `--size-sm`
   - State modifiers: `--active`, `--disabled`

2. Implement states and styling.
   - **Enabled**: neutral gray text, normal font-weight, clickable
   - **Hovered**: primary blue text, normal font-weight, cursor pointer
   - **Active**: primary blue text, semibold font-weight
   - **Disabled**: light gray text, muted, `pointer-events: none`
   - All state transitions: 0.15s ease
   - Both sizes centered flex layout with proper padding

3. Create CKAN snippet with parameters.
   - `letter` (string): the letter/character to display (e.g., 'A', 'B')
   - `size` (string): `'lg'` or `'sm'`, default: `'lg'`
   - `state` (string): `'enabled'`, `'hovered'`, `'active'`, `'disabled'`, default: `'enabled'`
   - `href` (string): link URL, default: '#'
   - `extra_classes` (string): additional CSS classes, default: ''

4. Ensure proper styling hierarchy.
   - Move `c-letter-anchor` rules from `navigation.less` to new `letter-anchor.less`
   - Remove letter anchor rules from `navigation.less` (only nav-item, anchor-links, pagination, breadcrumb remain)
   - Preserve exact visual appearance and token usage
