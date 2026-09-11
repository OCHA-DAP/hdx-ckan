# Task 010: Extend c-tooltip light variant with optional right-side icon button

Add an optional icon slot on the right side of the `c-tooltip--light` body row, matching the Figma "tooltip-location-map" design. The slot renders a small inline SVG icon (e.g. a country flag) inside a white-background container that stretches the full height of the body row.

The existing `flag_src` parameter is repurposed for this slot (right side, inline SVG). There is no separate `icon_btn_src` param.

## Reference

Figma export: `llm_docs/redesign/figma_exports/tooltip-location-map.html`

Key measurements from Figma:
- Icon container: `align-self: stretch`, `bg: #fff`, `border-radius: 2px`, flex, `justify-content: center`, `align-items: flex-start`
- Icon: `width: 1.25rem`

## What to update

### `templates/v2/components/tooltip.html`

- Update `flag_src` doc comment: right-side optional inline SVG icon path (default: `''`).
- Remove the left-side `<img class="c-tooltip__flag">` block.
- Inside `c-tooltip__body`, render `c-tooltip__icon-btn` **after** `c-tooltip__content` using inline SVG include:

  ```html
  {% if flag_src %}
    <div class="c-tooltip__icon-btn" aria-hidden="true">
      {% include h.url_for_static(flag_src) %}
    </div>
  {% endif %}
  ```

### `less/v2/components/label.less`

Inside `.c-tooltip--light { … }`:

- Remove the `.c-tooltip__flag { width: 1.25rem; }` rule (no longer used).
- Add `.c-tooltip__icon-btn`:

  ```less
  .c-tooltip__icon-btn {
      align-self:       stretch;
      display:          flex;
      align-items:      flex-start;
      justify-content:  center;
      background-color: @c-tooltip-light-bg;
      border-radius:    var(--hdx-radius-sm);
      flex-shrink:      0;

      svg { width: 1.25rem; }
  }
  ```

### Demo / showcase page (`templates/v2/components.html`)

Add one `light` tooltip example that passes `flag_src`:

```
{% snippet 'v2/components/tooltip.html',
    variant='light',
    title='Democratic Republic of the Congo',
    subtitle='24 datasets',
    flag_src='v2/icons/locations-flags/democratic-republic-of-congo.svg',
    arrow='below' %}
```

## Why

The Figma design places a country-flag SVG inside a self-stretching white container to the right of the title/subtitle block. Reusing `flag_src` for this slot keeps the API minimal — one param covers the icon whether or not a title/subtitle is present. Inline SVG (via `{% include %}`) is consistent with how other icons are rendered in the component system.
