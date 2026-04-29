# Task 009: Refactor dropdown panel to use existing components

Refactor `dropdown-panel.html` so the search bar, list items, confirm button, and clear link all delegate to existing v2 components instead of inline custom markup.

## What to update

### `templates/v2/components/dropdown-panel.html`

- Replace the `<div class="c-dropdown__search">` block with the `c-search-input` component:
  ```
  {% snippet 'v2/components/search-input.html',
      size='m',
      state='enabled',
      placeholder=search_placeholder %}
  ```

- Replace each `<li class="c-dropdown-item …">` with the `c-list-item` component:
  ```
  {% snippet 'v2/components/list-item.html',
      type='checklist',
      size='m',
      state='active' if item.checked else 'default',
      label=item.label,
      count=item.count,
      checked=item.checked %}
  ```

- The confirm button already uses `c-button`. Add the missing `state` and `type` params:
  ```
  {% snippet 'v2/components/button.html',
      style='secondary', type='text', size='m', state='enabled', label=confirm_label %}
  ```

- The clear link already uses `c-text-link`. Verify it passes `state='enabled'`:
  ```
  {% snippet 'v2/components/text-link.html',
      style='tertiary', size='s', state='enabled', label=clear_label %}
  ```

- Update the top documentation comment to reflect the new component dependencies and remove references to any parameters that no longer apply (e.g. `search_icon`).

### `less/v2/components/dropdown.less`

- Remove `.c-dropdown__search` and all its nested rules — styling is now owned by `c-search-input`.
- Remove `.c-dropdown-item` and all its nested rules (`.c-dropdown-item__checkbox`, `__checkbox-bg`, `__checkbox-check`, `__body`, `__label`, `__count`) — styling is now owned by `c-list-item`.
- Keep all other rules: `.c-dropdown`, `.c-dropdown__panel`, `.c-dropdown__list-wrap`, `.c-dropdown__list`, `.c-dropdown__scrollbar`, `.c-dropdown__footer`, `.c-dropdown-calendar`.
- Remove any local tokens that are only referenced by the deleted rules (`@c-dropdown-cb-dim`, `@c-dropdown-cb-checked-bg`, `@c-dropdown-cb-radius`).

### Demo / showcase page

Update only if the dropdown panel demo still references removed parameters (e.g. `search_icon`) or relies on the old `c-dropdown-item` markup directly. Otherwise leave the demo unchanged.

## Why

- `c-dropdown__search` duplicates `c-search-input` styling; keeping both causes drift.
- `c-dropdown-item` duplicates `c-list-item--type-checklist` styling; the checkbox, hover, and active states are already handled by the shared component.
- Removing duplicate LESS reduces the surface area for visual inconsistencies across HDX v2 UI.
