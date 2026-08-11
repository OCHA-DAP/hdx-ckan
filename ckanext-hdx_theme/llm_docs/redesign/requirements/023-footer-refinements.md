# Task 023: Footer v2 refinements

Refine the existing v2 footer implementation to better align with the Figma spec and v2 design system component standards. No structural changes to the footer's overall layout or analytics integration.

**Figma source:** `llm_docs/redesign/figma_exports/footer.html`

---

## What to update

### `templates/v2/footer.html`

- **REQ-2 — SVG social icons.** Replace `<i class="fa-brands fa-github ...">` and `<i class="fa-brands fa-linkedin-in ...">` with inline SVG includes. Both files exist in `templates/v2/icons/`:
  ```jinja2
  {% include 'v2/icons/github.svg' %}
  {% include 'v2/icons/linkedin.svg' %}
  ```
  Both SVGs use `fill="currentColor"` and inherit white from the footer context automatically.

- **REQ-3 — Social link labels via `c-text-link`.** Replace the custom `.hdx-v2-footer__social-label` span with `c-text-link` classes applied to the label element directly. The outer `<a class="hdx-v2-footer__social-link">` anchor is unchanged:
  ```html
  <span class="c-text-link c-text-link--primary c-text-link--size-s">GitHub</span>
  ```
  The footer-level `.c-text-link` color overrides (white on dark background) already in `footer.less` apply automatically.

- **REQ-4 — OCHA text: plain flex.** Remove the fixed `max-width` from `__ocha-text` (see LESS change below). `__service-detail` stays plain BEM divs — no Bootstrap classes (superseded by task 027's Bootstrap removal):
  ```html
  <div class="hdx-v2-footer__service-detail">
    <span class="hdx-v2-footer__ocha-logo"> … </span>
    <p class="hdx-v2-footer__ocha-text"> … </p>
  </div>
  ```

- **REQ-5 — MD breakpoint: newsletter/social split.** The 75/25 split and stacking behavior are implemented entirely in `footer.less` via flex (`&__newsletter`/`&__social` at `flex: 0 0 75%`/`25%` on MD+) — no Bootstrap row/column classes (superseded by task 027):
  ```html
  <div class="hdx-v2-footer__actions">
    <div class="hdx-v2-footer__newsletter"> … </div>
    <div class="hdx-v2-footer__social"> … </div>
  </div>
  ```

- **REQ-7 — Newsletter input: `c-text-field` component.** Replace the raw `<input class="hdx-v2-footer__email-input">` with the snippet. Preserve all Mailchimp form attributes on the wrapping `<form>`. `text-field.html` never renders an icon, so no `show_icon` param is needed:
  ```jinja2
  {% snippet 'v2/components/text-field.html',
      size='m', state='enabled',
      type='email', name='EMAIL', id='mce-EMAIL',
      placeholder=_('Enter your email'), value='' %}
  ```

- **REQ-8 — Newsletter button: `button` component.** Replace the raw `<button>` with the snippet, retaining the `hdx-v2-footer__subscribe-btn` extra class for dark-background color overrides:
  ```jinja2
  {% snippet 'v2/components/button.html',
      style='secondary', type='text', size='m',
      state='enabled', icon=False,
      label=_('Subscribe'), button_type='submit',
      extra_classes='hdx-v2-footer__subscribe-btn',
      attrs={'name': 'subscribe', 'id': 'mc-embedded-subscribe'} %}
  ```

### `hdx-styles/src/common/less/v2/footer.less`

- **REQ-1 — Bottom-align `__related`.** Three coordinated changes:
  1. Add `margin-top: auto` to `__related` — absorbs free space at any breakpoint where `__branding` has height to spare.
  2. On `__top` at XL, change `align-items: flex-start` → `align-items: stretch` — lets `__branding` grow to the full row height (set by the taller `__nav` column).
  3. Remove the fixed `height: 17.5rem` from `__branding` at XL — was a hard-coded guess; height is now driven by the row. With real height available, `justify-content: space-between` distributes logo-wrap / actions / related correctly, pushing `__related` to the bottom.

- **REQ-2 — `__social-icon` sizing.** Remove `font-size` and `line-height` rules (FontAwesome glyph metrics). Size the SVG via `width`/`height`, consistent with `__ext-icon`:
  ```less
  &__social-icon {
      width:       1.25rem;
      flex-shrink: 0;
      line-height: 0;
      svg { width: 1.25rem; height: auto; display: block; }
  }
  ```

- **REQ-3 — Remove `__social-label` block.** Delete the `&__social-label` ruleset; `c-text-link` styles replace it.

- **REQ-4 — Remove `__ocha-text` max-width.** Delete `max-width: 31.875rem` from `__ocha-text`. Remove or simplify the custom `flex-direction`/`align-items` rules on `__service-detail` that Bootstrap's row/col stacking now handles.

- **REQ-5 — Remove `__newsletter` MD flex override.** Delete the `flex: 1` rule scoped to `min-width: @hdx-bp-md and max-width: @hdx-bp-xl` on `__newsletter`; Bootstrap columns replace it. Remove `flex-direction: row` and `gap: 2.5rem` from the MD-only `__actions` media query; the Bootstrap row handles the row direction.

- **REQ-6 — Hide OCHA logo border on SM.** Add to `__ocha-logo`:
  ```less
  @media (max-width: (@hdx-bp-md - 0.001rem)) {
      border-right:  none;
      padding-right: 0;
  }
  ```

- **REQ-7 — Newsletter input: replace `__email-input` block.** Delete the `&__email-input` ruleset. Add a scoped rule for the `c-search-input` within the newsletter row — `flex: 1` lets it grow, `max-width` caps it:
  ```less
  &__newsletter-row .c-search-input {
      flex:      1;
      max-width: 22rem;
  }
  ```

- **REQ-8 — `__subscribe-btn` overrides retained.** The `__subscribe-btn` block must remain to adapt the secondary button to the dark footer background (transparent bg, white border/text, hover/active states).

### `templates/v2/components/search-input.html`

- **REQ-9 — `show_icon` param.** Add an optional boolean parameter `show_icon` (default `True`) that controls whether the right-side icon is rendered. When `False`, the `{% elif show_icon %}` branch is skipped entirely. The password-toggle path (`type='password'`) is unaffected — it is checked first.
  ```jinja2
  {# param default #}
  {% set show_icon = show_icon if show_icon is defined else True %}

  {# rendering #}
  {% if type == 'password' %}
    … toggle button …
  {% elif show_icon %}
    <span class="c-search-input__icon">{% include h.url_for_static(icon_src) %}</span>
  {% endif %}
  ```

### `fanstatic/v2/footer.css`

Recompile from `footer.less` after all LESS changes.

---

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| 1 | Newsletter input icon — should the search icon be shown in the footer email input? | No icon shown. Added `show_icon` boolean param (default `True`) to `c-search-input` (REQ-9) and passed `show_icon=False` in the footer newsletter snippet (REQ-7). |

---

## Constraints

- Do not alter Mailchimp form attributes (`action`, `method`, `id`, `name`, `novalidate`) or the honeypot comment block.
- Preserve all `data-module="hdx_click_stopper"` and `data-module-link_type="footer"` analytics attributes on every link.

## Why

The initial footer implementation (task 015) used FontAwesome for social icons, a custom raw `<input>` for the newsletter, and fixed max-widths rather than the Bootstrap grid. This task replaces those with existing v2 design system components (`c-search-input`, `button.html`, `c-text-link`, inline SVG icons) and aligns layout constraints with the Bootstrap grid — consistent with how other v2 components are built.
