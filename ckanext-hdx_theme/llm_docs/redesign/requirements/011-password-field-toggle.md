# Task 011: Extend c-search-input with password toggle support

Add an optional password mode to the existing `c-search-input` component. When `type='password'` is passed, the right-side icon becomes an interactive eye / eye-off toggle instead of a static search icon.

## Reference

Figma export: `llm_docs/redesign/figma_exports/password-field.html`

Key measurements from Figma (identical to the existing `c-search-input` size-l):
- `border-radius: 2px`, `background: #fafbfb`, `border: 2px solid #3f4748` (filled state)
- Padding: `0.5rem 0.75rem 0.5rem 1rem`, `gap: 0.5rem`
- Icon: `1rem × 1rem`, right-aligned, vertically centred

No layout or spacing changes are needed — the existing size-l styles already match Figma exactly.

## What to update

### `templates/v2/components/text-field.html`

1. Add a `type` parameter (default: `'search'`) and an `autocomplete` parameter (default: `''`) to the parameter block and defaults section.

2. Pass `type` to the `<input>` element instead of hardcoding `type="search"`. Set `autocomplete` when provided.

3. Replace the static `<span class="c-search-input__icon">` with conditional rendering:

   - **Default (non-password):** render the icon exactly as today.
   - **Password:** render a `<button>` instead of a `<span>`, with `type="button"` to prevent form submission:

   ```html
   {% if type == 'password' %}
     <button class="c-search-input__icon c-search-input__toggle"
             type="button"
             aria-label="Show password">
       <span class="c-search-input__toggle-eye">
         {% include h.url_for_static('v2/icons/eye.svg') %}
       </span>
       <span class="c-search-input__toggle-eye-off" hidden>
         {% include h.url_for_static('v2/icons/eye-off.svg') %}
       </span>
     </button>
   {% else %}
     <span class="c-search-input__icon">{% include h.url_for_static(icon_src) %}</span>
   {% endif %}
   ```

   Existing icons to use (already in the repo):
   - `templates/v2/icons/eye.svg`
   - `templates/v2/icons/eye-off.svg`

4. Update the doc comment to document the two new parameters and the password example.

### `hdx-styles/src/common/less/v2/components/input-field.less`

Inside the existing `.c-search-input` block, add a `&__toggle` rule alongside `&__icon`. No other rules change.

```less
&__toggle {
    display:     flex;
    align-items: center;
    background:  none;
    border:      none;
    padding:     0;
    cursor:      pointer;
    color:       inherit;
    flex-shrink: 0;

    svg {
        width:   @c-input-icon-dim;
        height:  @c-input-icon-dim;
        display: block;
    }
}
```

### `fanstatic/v2/components/input-field.js`

Vanilla JS only. Scoped to `.c-search-input__toggle` so it never touches non-password inputs.

```js
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.c-search-input__toggle').forEach(function (btn) {
    var input    = btn.closest('.c-search-input').querySelector('input');
    var eyeEl    = btn.querySelector('.c-search-input__toggle-eye');
    var eyeOffEl = btn.querySelector('.c-search-input__toggle-eye-off');

    btn.addEventListener('click', function () {
      var isPassword   = input.type === 'password';
      input.type       = isPassword ? 'text' : 'password';
      eyeEl.hidden     = isPassword;
      eyeOffEl.hidden  = !isPassword;
      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    });
  });
});
```

### Demo page (`templates/v2/components.html`)

Add one password-input example in the input-field section:

```
{% snippet 'v2/components/text-field.html',
    type='password',
    name='password',
    placeholder='Enter password',
    autocomplete='current-password' %}
```

## Constraints

- All existing `c-search-input` usages (without `type='password'`) must remain unchanged — the default `type` value ensures full backwards compatibility.
- Use existing `v2/icons/eye.svg` and `v2/icons/eye-off.svg`; do not add new icon files.
- No jQuery. The existing `onboarding/toggle-password-visibility.js` (jQuery-based) is unrelated and must not be modified.
- Initial state: `type="password"`, eye visible, eye-off hidden.

## Why

The Figma password field is visually identical to `c-search-input` size-l — same border, background, padding, and icon slot. Adding `type` as a parameter keeps the component API minimal and avoids duplicating markup or styles. The toggle button reuses the existing `__icon` sizing so no layout changes are needed.
