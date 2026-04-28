# Task 004: Implement c-list-item component

## Goal

Create a versatile list item component that supports two distinct list types: simple text lists and checklist-based lists with checkboxes. The component ensures consistent styling and layout across different usage contexts.

## Why this is useful

List items are fundamental to content presentation in the design system. By providing a unified component that handles both plain text items and checklist-based items, we reduce code duplication and ensure consistent styling, spacing, and interaction patterns.

## Scope

This task focuses on implementing a flexible list item component that adapts to different content types.

### In scope

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/list-item.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/list-item.less`
- Two list types: `list` (text-only) and `checklist` (with checkbox)
- States: `default`, `hovered`, `active` (for checklist)
- Sizes: `md` (medium, 14px) and `sm` (small, 12px) for text-only lists

### Out of scope

- List container/wrapper component (that's a separate concern)
- Form handling or state management (component is presentational only)
- Nested list support

## Requirements

1. Create c-list-item component with flexible structure.
   - Type: `list` renders text only
   - Type: `checklist` renders checkbox + text label + optional count badge
   - Support for dynamic content slots

2. Implement styling and states.
   - **Text-only list**:
     - Default: neutral gray text
     - Hovered: primary blue text
     - Size `md`: 14px font
     - Size `sm`: 12px font
   - **Checklist list**:
     - Default: unchecked checkbox, neutral gray text
     - Hovered: unchecked checkbox, primary blue text
     - Active: checked checkbox, bold text
     - Always: 14px font for label, 12px for count badge

3. Create CKAN snippet with parameters.
   - `type` (string): `'list'` or `'checklist'`, default: `'list'`
   - `label` (string): item text/label
   - `size` (string): `'md'` or `'sm'` (text-only lists), default: `'md'`
   - `state` (string): `'default'` or `'hovered'` or `'active'` (for checklist), default: `'default'`
   - `checked` (boolean): for checklist type, default: false
   - `count` (string or number): optional badge showing item count like "(309)", default: ''
   - `href` (string): optional link for the item, default: ''
   - `extra_classes` (string): additional CSS classes, default: ''

4. Ensure semantic structure.
   - For `list` type: wrap in appropriate semantic element or use div with proper ARIA if needed
   - For `checklist` type: include checkbox component, ensure proper label association
   - Support optional `href` to make items clickable links