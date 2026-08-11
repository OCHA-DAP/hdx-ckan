# Task 003: Implement c-checkbox component

## Goal

Create a reusable, accessible checkbox component used standalone and as a building block for checklist-based list items.

## Scope

**In:**

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/checkbox.html`
- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/components/checkbox.less`
- Checkbox states: `unchecked`, `checked`, `disabled`
- Accessibility: ARIA attributes and semantic HTML

**Out:**
- Form validation, JS event handlers (consuming components' concern)
- Label text styling

## Requirements

1. Create c-checkbox component structure.
   - Use semantic `<input type="checkbox">` element hidden visually.
   - Use a `<div>` or `<span>` with class `.c-checkbox__box` to display the visual checkbox.
   - Use SVG or icon for the checkmark on checked state.

2. Implement states and styling.
   - **Unchecked**: white background, light gray border, no checkmark
   - **Checked**: primary blue background, checkmark icon visible, no border
   - **Disabled**: muted colors, `cursor: not-allowed` (relies on the native `disabled` attribute for inertness)
   - All states transition smoothly (0.15s ease)

3. Create CKAN snippet with parameters.
   - `id` (string): unique identifier for the checkbox input
   - `checked` (boolean): initial checked state, default: false
   - `disabled` (boolean): whether checkbox is disabled, default: false
   - `name` (string): form name attribute, default: ''
   - `value` (string): form value attribute, default: ''
   - `extra_classes` (string): additional CSS classes, default: ''

4. Ensure accessibility.
   - Use proper `<label>` association with `for` attribute
   - Include `aria-checked` or rely on semantic input[type="checkbox"]
   - Support keyboard navigation (Tab, Space to toggle)
