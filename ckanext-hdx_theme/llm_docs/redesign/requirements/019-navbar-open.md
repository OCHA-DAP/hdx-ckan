# Task 019: Implement navbar offcanvas menu (mobile/tablet)

Implement the full-height sliding panel that appears when the hamburger is tapped on MD and SM breakpoints. The panel covers the full viewport below the navbar. No duplicate logo or extra close button inside the panel.

**Figma source:** `llm_docs/redesign/figma_exports/navbar-open.html`

## Responsive breakpoints

| Label | Range         | Panel width | Hamburger visible |
|-------|---------------|-------------|-------------------|
| SM    | < 48rem       | 100vw       | Yes               |
| MD    | 48rem – 79rem | 100vw       | Yes               |
| XL    | ≥ 80rem       | —           | Hidden            |

## Layout specs (from Figma)

- Panel: fixed, full-width, fills from bottom of navbar to bottom of viewport
- Background: `#fff`
- Padding: `1.25rem`
- Nav item: full-width flex row, `padding: 0.375rem 0`, `border-bottom: 1px solid #ebeff0`
- Products sub-items: `padding-left: 1rem`, `font-size: 0.875rem`, `color: #3f4748`
- User row (logged in): avatar + display name at top, chevron-right; tapping enters second level
- Login button (logged out): NOT full-width, `width: auto`, bottom of panel
- Slide animation: `transform: translateY` from above viewport; `transition: 0.25s ease`

## What to create

### `templates/v2/header.html` (offcanvas markup)

Markup lives inline at the end of `header.html`, outside `<nav class="hdx-v2-navbar">`, before `</header>`.

```jinja2
{# ── Offcanvas panel ─────────────────────────────────────── #}
<div class="hdx-v2-offcanvas" id="hdx-v2-offcanvas" aria-hidden="true">
  <div class="hdx-v2-offcanvas__body">

    {# Primary level — always visible when offcanvas is open #}
    <div class="hdx-v2-offcanvas__primary">

      {# User row — logged in only; tapping enters second level #}
      {% if c.userobj %}
        {% set notif = h.hdx_get_user_notifications() %}
        <button class="hdx-v2-offcanvas__user" type="button"
                aria-label="{{ _('User menu') }}"
                data-hdx-v2-offcanvas-level="user-detail">
          {% snippet 'v2/components/avatar.html',
              size='sm',
              initials=c.userobj.display_name[0] | upper,
              badge=notif.count > 0 %}
          <span class="hdx-v2-offcanvas__user-name">{{ c.userobj.display_name }}</span>
          <span class="hdx-v2-offcanvas__user-chevron">{% include 'v2/icons/chevron-right.svg' %}</span>
        </button>
      {% endif %}

      {# Primary nav items #}
      <nav class="hdx-v2-offcanvas__nav" aria-label="{{ _('Mobile navigation') }}">
        <a class="hdx-v2-offcanvas__nav-item" href="{{ h.url_for('home.index') }}"
           data-module="hdx_click_stopper" data-module-link_type="header">
          {{ _('Home') }}
        </a>
        <a class="hdx-v2-offcanvas__nav-item" href="{{ h.url_for('dataset.search') }}"
           data-module="hdx_click_stopper" data-module-link_type="header">
          {{ _('Data') }}
        </a>
        <a class="hdx-v2-offcanvas__nav-item" href="{{ h.url_for('group.index') }}"
           data-module="hdx_click_stopper" data-module-link_type="header">
          {{ _('Locations') }}
        </a>
        <a class="hdx-v2-offcanvas__nav-item" href="{{ h.url_for('organization.index') }}"
           data-module="hdx_click_stopper" data-module-link_type="header">
          {{ _('Organisations') }}
        </a>

        {# Products — inline expandable (default open per Figma) #}
        <button class="hdx-v2-offcanvas__nav-item hdx-v2-offcanvas__nav-item--expandable"
                type="button"
                aria-expanded="true"
                aria-controls="offcanvas-products">
          {{ _('Products') }}
          <span class="hdx-v2-offcanvas__expand-chevron">{% include 'v2/icons/chevron-down.svg' %}</span>
        </button>
        <ul class="hdx-v2-offcanvas__subnav" id="offcanvas-products">
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX HAPI') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX Signals') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Data Grids') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Greater Middle East Crisis') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('occupied Palestinian territory – Israel Hostilities') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Common Operational Datasets (CODs)') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Dataviz Gallery') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX Dataviz Guidelines') }}</a></li>
          <li><a href="#" data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Archived') }}</a></li>
        </ul>
      </nav>

      {# Login button — logged out only, NOT full-width #}
      {% if not c.userobj %}
        <div class="hdx-v2-offcanvas__footer">
          {% snippet 'v2/components/button.html',
              style='secondary', size='l', label=_('Log in'),
              tag='a', href=h.url_for('user.login') %}
        </div>
      {% endif %}

    </div>{# /.hdx-v2-offcanvas__primary #}

    {# Second level — user account detail (logged in only) #}
    {% if c.userobj %}
      <div class="hdx-v2-offcanvas__level" id="hdx-v2-offcanvas-level-user-detail" hidden>
        <button class="hdx-v2-offcanvas__back" type="button" data-hdx-v2-offcanvas-back>
          {% include 'v2/icons/chevron-left.svg' %}
          {{ _('Back') }}
        </button>
        {# Reuse desktop user menu snippet — no duplication #}
        {% snippet 'v2/navbar-user-menu.html' %}
      </div>
    {% endif %}

  </div>{# /.hdx-v2-offcanvas__body #}
</div>

{# Backdrop #}
<div class="hdx-v2-offcanvas__backdrop" hidden data-hdx-v2-close="offcanvas"></div>
```

### CSS additions to `less/v2/navbar.less`

```css
/* ── Offcanvas panel ──────────────────────────────────────── */
.hdx-v2-offcanvas {
  position: fixed;
  top: calc(var(--hdx-top-bar-h, 2.125rem) + var(--hdx-navbar-h, 4rem));
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
  z-index: 1040;
  transform: translateY(-110%);
  visibility: hidden;
  transition: transform 0.25s ease, visibility 0.25s;
  overflow: hidden;
}
.hdx-v2-offcanvas.is-open {
  transform: translateY(0);
  visibility: visible;
}

/* Only shown on MD/SM; hidden on XL */
@media (min-width: 80rem) {
  .hdx-v2-offcanvas { display: none; }
}

/* Body */
.hdx-v2-offcanvas__body {
  height: 100%;
  overflow-y: auto;
  position: relative;
}

/* Primary level */
.hdx-v2-offcanvas__primary {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  min-height: 100%;
}

/* User row */
.hdx-v2-offcanvas__user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.5rem 0;
  border: none;
  border-bottom: 1px solid #ebeff0;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  margin-bottom: 0.25rem;
}
.hdx-v2-offcanvas__user-name {
  flex: 1;
  text-align: left;
  font-weight: 500;
  font-size: 0.875rem;
}
.hdx-v2-offcanvas__user-chevron { width: 1.25rem; color: #3f4748; }

/* Nav items */
.hdx-v2-offcanvas__nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.375rem 0;
  border: none;
  border-bottom: 1px solid #ebeff0;
  background: transparent;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  color: #3f4748;
  text-decoration: none;
  font-family: inherit;
}
.hdx-v2-offcanvas__expand-chevron { width: 1.25rem; transition: transform 0.15s; }
.hdx-v2-offcanvas__nav-item--expandable[aria-expanded="false"] .hdx-v2-offcanvas__expand-chevron {
  transform: rotate(-90deg);
}

/* Products sub-nav */
.hdx-v2-offcanvas__subnav {
  list-style: none;
  margin: 0;
  padding: 0 0 0 1rem;
}
.hdx-v2-offcanvas__subnav[hidden] { display: none; }
.hdx-v2-offcanvas__subnav li a {
  display: block;
  padding: 0.375rem 0;
  font-size: 0.875rem;
  color: #3f4748;
  text-decoration: none;
  border-bottom: 1px solid #ebeff0;
}

/* Footer (login button) — not full-width */
.hdx-v2-offcanvas__footer {
  margin-top: auto;
  padding-top: 1.25rem;
  display: flex;
}

/* Second level */
.hdx-v2-offcanvas__level {
  position: absolute;
  inset: 0;
  background: #fff;
  overflow-y: auto;
  padding: 1.25rem;
}
.hdx-v2-offcanvas__level[hidden] { display: none; }

.hdx-v2-offcanvas__back {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.875rem;
  text-decoration: underline;
  font-family: inherit;
  padding: 0 0 1rem 0;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #ebeff0;
}
.hdx-v2-offcanvas__back svg { width: 1rem; }

/* Backdrop */
.hdx-v2-offcanvas__backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1039;
}
.hdx-v2-offcanvas__backdrop[hidden] { display: none; }
```

### JS additions to `fanstatic/v2/navbar.js` (extends task 018)

Add to the existing IIFE the following behaviors:

5. **Offcanvas open** — when hamburger (`data-hdx-v2-panel="offcanvas"`) is clicked:
   - Add `.is-open` to `#hdx-v2-offcanvas`; remove `hidden` from backdrop.
   - Set `aria-hidden="false"` on offcanvas; `aria-expanded="true"` on hamburger.
   - Lock body scroll: `document.body.style.overflow = 'hidden'`.
   - Swap hamburger icon to close icon (add/remove CSS class on the button).

6. **Offcanvas close** — backdrop click, ESC key, or `data-hdx-v2-close="offcanvas"`:
   - Remove `.is-open`; restore `hidden` on backdrop.
   - Set `aria-hidden="true"`; `aria-expanded="false"` on hamburger.
   - Restore body scroll.
   - Return to primary level (hide any open second-level).
   - Swap icon back to hamburger.

7. **Second-level navigation** — clicking `.hdx-v2-offcanvas__user` (`data-hdx-v2-offcanvas-level`):
   - Add `hidden` to `.hdx-v2-offcanvas__primary`.
   - Remove `hidden` from `#hdx-v2-offcanvas-level-{value}`.

8. **Back button** (`data-hdx-v2-offcanvas-back`):
   - Reverse: hide the level, show `.hdx-v2-offcanvas__primary`.

9. **Products inline toggle** — clicking `.hdx-v2-offcanvas__nav-item--expandable`:
   - Toggle `hidden` on `#offcanvas-products`.
   - Flip `aria-expanded`.

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| 1 | Back-button icon | Shipped as `chevron-left.svg`, not `arrow-left.svg` — `arrow-left.svg` exists in `templates/v2/icons/` but is unused |
| 2 | `chevron-right.svg` path — confirm icon exists | Confirmed — `chevron-right.svg` exists in `templates/v2/icons/` |
| 3 | Body scroll lock — verify no conflict with existing page scroll logic | Implemented via `document.body.style.overflow = 'hidden'` / `''`; no conflicts observed |
| 4 | Products URLs — all `#`, real URLs needed before launch | Resolved — products are rendered dynamically via `h.hdx_get_quick_links_list(archived=False, exclude_crisis=True)`; no hardcoded `#` URLs remain. Crisis/dashboard items are excluded (`/dashboards/overview-of-data-grids` always force-included); the hardcoded "Archived Dataviz" item after the loop is commented out |
| 5 | Hamburger icon swap — swap SVG or use CSS transform on single icon | CSS class approach chosen: `.is-open` added to the hamburger button; icon swap handled via CSS without JS SVG manipulation |

## Why

The legacy `header-mobile.html` duplicates most of the desktop header and relies on Bootstrap collapse with jQuery. The v2 offcanvas uses a single dedicated snippet, reuses `navbar-user-menu.html` for the second level (no duplication), and is driven by the same `navbar.js` controller as the desktop panels. Login button is explicitly `width: auto` to prevent it stretching full-width on mobile, per the task spec.

---

## Implementation notes (diverges from spec above)

### Second level: user sections use offcanvas-native markup

The spec suggested reusing `navbar-user-menu.html` (the desktop panel snippet) inside the second level. The actual implementation does not do this — it would have required extensive LESS overrides to un-style the desktop panel's `hdx-v2-user-menu__*` classes for the dark-background offcanvas.

Instead, the second level renders the user menu sections using the same expandable pattern as Products in the primary level:

```jinja2
{% for section in h.hdx_get_user_menu_sections() %}
  <button class="hdx-v2-offcanvas__nav-item hdx-v2-offcanvas__nav-item--expandable"
          type="button" aria-expanded="true"
          aria-controls="offcanvas-user-{{ section.id }}">
    {{ section.label }}
    <span class="hdx-v2-offcanvas__expand-icon">{% include 'v2/icons/chevron-down.svg' %}</span>
  </button>
  <ul class="hdx-v2-offcanvas__subnav" id="offcanvas-user-{{ section.id }}">
    {% for item in section.items %}
    <li><a href="{{ item.href }}" ...>{{ item.label }}</a></li>
    {% endfor %}
  </ul>
{% endfor %}
<div class="hdx-v2-offcanvas__footer">
  {# Logout button — style='secondary' inherits .hdx-v2-offcanvas .c-button--secondary override #}
</div>
```

The data comes from `h.hdx_get_user_menu_sections()` — see task 018 implementation notes for the helper details. The existing `hdx-v2-offcanvas__nav-item--expandable` JS handler in `navbar.js` covers these buttons automatically (no new JS needed).

### LESS cleanup

With the above change, all `hdx-v2-user-menu__*` overrides were removed from the `&__level` block in `navbar.less` — approximately 40 lines of override CSS deleted. The `&__footer` rule gained `margin-top: auto` to anchor the logout button at the bottom of the flex-column second level.
