# Task 006: Use button and text-link components in autocomplete

Refactor the autocomplete suggestion panel so the interactive chips and search results use existing v2 components instead of custom element styling.

## What to update

- In `templates/v2/components/autocomplete.html`:
  - Render `chips` using the `c-button` component.
  - Each chip should use:
    - `style='tertiary'`
    - `type='text'`
    - `size='m'`
    - `state='enabled'`
  - Render each search result link using the `c-text-link` component.
  - Each result link should use:
    - `style='tertiary'`
    - `size='m'`
    - `state='enabled'`

- Render the confirm action using the `c-button` component.
  - The confirm button should use:
    - `style='tertiary'`
    - `type='text'`
    - `size='m'`
    - `state='enabled'`
    - `label=confirm_label`

- In `less/v2/components/input-field.less`:
  - Remove any autocomplete-specific anchor styling that conflicts with `c-text-link`.
  - Preserve list layout and truncation behavior for result labels.

## Why

This aligns the autocomplete panel with the shared design system:
- Reuses button styling for chips, keeping behavior consistent with other tertiary buttons.
- Reuses the text-link component for result links, avoiding duplicate link styles.
- Reduces maintenance and improves visual consistency across HDX v2 UI.
