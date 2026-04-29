# Task 012: Extend c-radio with optional info-circle tooltip

Add an optional info-circle icon with a hover tooltip to the existing `c-radio` component. The icon sits inline to the right of the label text. A tooltip appears on hover when tooltip text is provided.

## Reference

Figma export: `llm_docs/redesign/figma_exports/radio-button.html`

Key measurements from Figma:
- Row layout: `display: flex; align-items: center; gap: 0.5rem` (8px between radio circle and label+icon group)
- Label + icon inner gap: `0.375rem` (6px) — distinct from the outer 8px gap
- Icon size: `1rem × 1rem` (`info-circle.svg`)
- Enabled unchecked label color: `#3f4748` → `--hdx-neutral-8` (already set)
- Enabled checked label color: `#101212` → `--hdx-neutral-95` (missing — add it)
- Disabled label color: `#9db1b3` → `--hdx-neutral-7` (already set)

States to cover (all shown in Figma):

| checked | disabled | hint |
|---------|----------|------|
| false   | false    | true |
| true    | false    | true |
| false   | true     | true |
| true    | true     | true |

## What to update

### `templates/v2/components/radio.html`

1. **Add parameters:**
   - `hint_text` `{string}` — tooltip body text. When non-empty, renders a `c-tooltip` on hover. Default: `''`
   - Update `hint_src` default from `'v2/icons/info.svg'` to `'v2/icons/info-circle.svg'`

2. **Group label + hint in a `<span class="c-radio__body">`** so the inner 6px gap is separate from the outer 8px gap between radio circle and label group:

   ```html
   {% if label or hint %}
     <span class="c-radio__body">
       {% if label %}
         <span class="c-radio__label">{{ label }}</span>
       {% endif %}

       {% if hint %}
         <span class="c-radio__hint-wrap">
           <span class="c-radio__hint" aria-hidden="true">
             {% include h.url_for_static(hint_src) %}
           </span>
           {% if hint_text %}
             {% snippet 'v2/components/tooltip.html',
                 variant='dark', text=hint_text, arrow='' %}
           {% endif %}
         </span>
       {% endif %}
     </span>
   {% endif %}
   ```

3. **Remove the old `<img class="c-radio__hint">` block** — it is replaced by the inline SVG above.

4. **Update the doc comment** to document `hint_text`, the updated `hint_src` default, and add a tooltip example:

   ```
   {% snippet 'v2/components/radio.html',
       name='format', value='csv', label='CSV',
       hint=True, hint_text='Comma-separated values' %}
   ```

### `hdx-styles/src/common/less/v2/components/selection.less`

All changes are inside the existing `.c-radio { … }` block.

1. **Add `&__body`** — flex wrapper that creates the 6px inner gap between label text and icon:

   ```less
   &__body {
       display:     flex;
       align-items: center;
       gap:         var(--hdx-space-13);  // 6 px
   }
   ```

2. **Add `&__hint-wrap`** — positions the tooltip relative to the trigger icon:

   ```less
   &__hint-wrap {
       position:    relative;
       display:     inline-flex;
       align-items: center;

       .c-tooltip {
           position:   absolute;
           bottom:     calc(100% + 0.375rem);
           left:       50%;
           transform:  translateX(-50%);
           white-space: nowrap;
           display:    none;
           z-index:    10;
       }

       &:hover .c-tooltip { display: block; }
   }
   ```

3. **Update `&__hint`** — switch from `<img>` sizing to inline SVG sizing:

   ```less
   &__hint {
       width:       1rem;
       flex-shrink: 0;
       display:     block;
       color:       inherit;

       svg {
           width:   1rem;
           height:  1rem;
           display: block;
       }
   }
   ```

4. **Add checked label color** (currently missing — Figma shows `#101212` for enabled+checked):

   ```less
   &--checked &__label {
       color: var(--hdx-neutral-95);
   }
   ```

### Demo page (`templates/v2/components.html`)

Extend the existing radio demo block with hint+tooltip variants covering all four state combinations:

```
{% snippet 'v2/components/radio.html',
    name='demo-hint', value='a', label='Unchecked with info',
    hint=True, hint_text='Additional context for this option' %}
{% snippet 'v2/components/radio.html',
    name='demo-hint', value='b', label='Checked with info',
    checked=True, hint=True, hint_text='Additional context for this option' %}
{% snippet 'v2/components/radio.html',
    name='demo-hint', value='c', label='Disabled unchecked with info',
    state='disabled', hint=True, hint_text='Additional context for this option' %}
{% snippet 'v2/components/radio.html',
    name='demo-hint', value='d', label='Disabled checked with info',
    checked=True, state='disabled', hint=True, hint_text='Additional context for this option' %}
```

## Constraints

- All existing `c-radio` usages without `hint=True` must remain unchanged.
- `hint=True` without `hint_text` renders the icon only — no tooltip markup is emitted.
- Use `v2/icons/info-circle.svg` as inline SVG (`{% include %}`), not `<img>`. This matches the rest of the v2 icon system and allows `color: inherit` to apply.
- No new JS required — tooltip show/hide is pure CSS (`:hover`).

## Why

The Figma groups the label text and info icon inside a sub-wrapper with a tighter 6px gap, while the radio circle sits 8px away from that group — matching the existing `gap: var(--hdx-space-2)` on `.c-radio`. A `__body` wrapper is the minimal structural change needed to reproduce this. Inline SVG replaces `<img>` so the icon inherits the disabled muted color automatically via `color: inherit`, without any additional state rules.
