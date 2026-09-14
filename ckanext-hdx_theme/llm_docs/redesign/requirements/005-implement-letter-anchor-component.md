# Task 005: Implement c-letter-anchor component

## Goal

Extract letter anchors from `c-nav-item` into a dedicated standalone component. The two patterns (nav items vs. alphabet filtering) have distinct semantics and should not share styles.

## Scope

**In:**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/letter-anchor.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/letter-anchor.less`
- States: `enabled`, `hovered`, `active`, `disabled`
- Sizes: `lg` (large, 2.3125rem) and `sm` (small, 1.5rem)

**Out:**
- Navigation item component (`navigation.less` unchanged)
- List/grid layout, sorting or filtering logic

## Requirements

1. Create c-letter-anchor component structure.
   - Root element: `.c-letter-anchor`
   - Size modifiers: `--size-lg`, `--size-sm`
   - State modifiers: `--active`, `--disabled`

2. Implement states and styling.
   - **Enabled**: neutral gray text, normal font-weight, clickable
   - **Hovered**: primary blue text, normal font-weight, cursor pointer
   - **Active**: primary blue text, normal font-weight
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
