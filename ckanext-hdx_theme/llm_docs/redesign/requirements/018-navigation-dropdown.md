# Task 018: Implement navbar dropdowns (user menu, notifications, products)

Implement the three panel/dropdown surfaces that attach to the navbar: the user account menu, the notifications panel, similarly to the Products nav dropdown. All styles live in `v2/navbar.less` (task 017). JS lives in `v2/navbar.js` (created here).

**Figma source:** `llm_docs/redesign/figma_exports/navigation-dropdown.html`

## Panels overview

| Panel             | Trigger         | Type                    | Width      |
|-------------------|-----------------|-------------------------|------------|
| User menu         | Avatar button   | Custom positioned panel | 14.125rem  |
| Notifications     | Bell button     | Custom positioned panel | 14.125rem  |
| Products dropdown | Products nav-item | Custom positioned panel    | auto       |

## Shared panel tokens (from Figma)

- Background: `#fff`
- Border: `1px solid #ebeff0`
- Border-radius: `4px`
- Shadow: `0px 4px 10px rgba(0,0,0,0.12)`
- Panel padding: `0.75rem 0.5rem 0.75rem 1rem`
- Positioned: `absolute; right: 0; top: calc(100% + 0.5rem); z-index: 1050`

## What to create

### `templates/v2/navbar-user-menu.html` (new snippet)

Rendered inside `header.html` after the avatar button. Hidden by default; shown by JS.

```jinja2
<div class="hdx-user-menu" id="hdx-panel-user-menu" hidden>

  {# Header row: username + close button #}
  <div class="hdx-user-menu__header">
    <span class="hdx-user-menu__name">{{ c.userobj.display_name }}</span>
    <button class="hdx-user-menu__close" type="button"
            aria-label="{{ _('Close menu') }}"
            data-hdx-close="user-menu">
      {% include 'v2/icons/close.svg' %}
    </button>
  </div>

  {# Sysadmin dashboard — sysadmin only #}
  {% if c.userobj.sysadmin %}
  <div class="hdx-user-menu__section">
    <button class="hdx-user-menu__section-toggle" type="button"
            aria-expanded="true" aria-controls="menu-sysadmin">
      {{ _('Sysadmin dashboard') }}
      <span class="hdx-user-menu__chevron">{% include 'v2/icons/chevron-down.svg' %}</span>
    </button>
    <ul class="hdx-user-menu__section-items" id="menu-sysadmin">
      <li><a href="{{ h.url_for('admin.index') }}">{{ _('All sysadmins') }}</a></li>
      <li><a href="{{ h.url_for('user.index') }}">{{ _('All users') }}</a></li>
      <li><a href="#">{{ _('Carousel') }}</a></li>
      <li><a href="#">{{ _('HDX Connect Dashboard') }}</a></li>
      <li><a href="#">{{ _('Custom/Event Pages') }}</a></li>
      <li><a href="#">{{ _('Quick Links') }}</a></li>
      <li><a href="#">{{ _('Package Links') }}</a></li>
      <li><a href="#">{{ _('Email') }}</a></li>
      <li><a href="{{ h.url_for('admin.config') }}">{{ _('Config') }}</a></li>
    </ul>
  </div>
  {% endif %}

  {# User dashboard #}
  <div class="hdx-user-menu__section">
    <button class="hdx-user-menu__section-toggle" type="button"
            aria-expanded="true" aria-controls="menu-dashboard">
      {{ _('User dashboard') }}
      <span class="hdx-user-menu__chevron">{% include 'v2/icons/chevron-down.svg' %}</span>
    </button>
    <ul class="hdx-user-menu__section-items" id="menu-dashboard">
      <li><a href="{{ h.url_for('activity.dashboard') }}">{{ _('Newsfeed') }}</a></li>
      <li><a href="{{ h.url_for('hdx_user_dashboard.datasets') }}">{{ _('My datasets') }}</a></li>
      <li><a href="{{ h.url_for('dashboard.organizations') }}">{{ _('My organisations') }}</a></li>
      <li><a href="{{ h.url_for('dashboard.groups') }}">{{ _('My locations') }}</a></li>
      <li><a href="{{ h.url_for('requestdata.my_requested_data') }}">{{ _('HDX Connect Requests') }}</a></li>
    </ul>
  </div>

  {# User settings #}
  <div class="hdx-user-menu__section">
    <button class="hdx-user-menu__section-toggle" type="button"
            aria-expanded="true" aria-controls="menu-settings">
      {{ _('User settings') }}
      <span class="hdx-user-menu__chevron">{% include 'v2/icons/chevron-down.svg' %}</span>
    </button>
    <ul class="hdx-user-menu__section-items" id="menu-settings">
      <li><a href="{{ h.url_for('user.read', id=c.user) }}">{{ _('Datasets') }}</a></li>
      <li><a href="{{ h.url_for('activity.user_activity', id=c.user) }}">{{ _('Activity stream') }}</a></li>
      {% if c.userobj.sysadmin %}
      <li><a href="#">{{ _('User permission') }}</a></li>
      {% endif %}
      <li><a href="{{ h.url_for('user.api_tokens', id=c.user) }}">{{ _('API tokens') }}</a></li>
      <li><a href="{{ h.url_for('hdx_user.notifications') }}">{{ _('Notifications') }}</a></li>
      <li><a href="{{ h.url_for('user.edit', id=c.user) }}">{{ _('Profile and password') }}</a></li>
    </ul>
  </div>

  {# Logout #}
  {% snippet 'v2/components/button.html',
      style='tertiary', size='m', label=_('Logout'),
      tag='a', href=h.url_for('user.logout') %}

</div>
```

Include in `header.html` immediately after the avatar button, inside `.hdx-navbar__actions`.

### `templates/v2/navbar-notifications.html` (new snippet)

Rendered inside `header.html` after the bell button.

```jinja2
{% set notif = h.hdx_get_user_notifications() %}
<div class="hdx-notifications" id="hdx-panel-notifications" hidden>

  <div class="hdx-notifications__header">
    <span class="hdx-notifications__title">
      {{ _('Notifications') }}{% if notif.count %} ({{ notif.count }}){% endif %}
    </span>
    <button class="hdx-notifications__close" type="button"
            aria-label="{{ _('Close notifications') }}"
            data-hdx-close="notifications">
      {% include 'v2/icons/close.svg' %}
    </button>
  </div>

  {% if notif.list %}
    <ul class="hdx-notifications__list">
      {% for item in notif.list %}
        <li class="hdx-notifications__item{% if item.for_sysadmin %} hdx-notifications__item--sysadmin{% endif %}">
          {% include item.html_template %}
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p class="hdx-notifications__empty">{{ _('No notifications') }}</p>
  {% endif %}

</div>
```

Each notification snippet (`item.html_template`) must render:
- A title string (e.g. "1 membership request for HDX")
- `item.last_date` formatted as "Jun 3, 2025"
- An arrow-right icon linking to the relevant action URL

The existing snippets in `light/notifications/` can be adapted to match this structure. The wrapper `<li>` is provided by the loop above; each snippet renders only its inner content.

### Products dropdown ✅ Already implemented in task 017

The Products dropdown was implemented as part of task 017 rather than waiting for this task. Key details of what was built:

- Class used: `hdx-navbar__products-menu` (not `hdx-products-menu` as shown below)
- Items driven by `h.hdx_get_quick_links_list(archived=False)` helper (not a static list)
- `min-width: 14rem` (not 18rem)
- CSS lives in `navbar.less` / `navbar.css` under `&__products-menu`

The static example below is kept for reference only.

### Products dropdown static example (reference only — superseded by task 017 implementation)

```jinja2
<ul class="dropdown-menu hdx-products-menu" aria-labelledby="navbar-products-trigger">
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX HAPI') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX Signals') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Data Grids') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Greater Middle East Crisis') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('occupied Palestinian territory – Israel Hostilities') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Common Operational Datasets (CODs)') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Dataviz Gallery') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('HDX Dataviz Guidelines') }}</a></li>
  <li><a class="dropdown-item" href="#"
         data-module="hdx_click_stopper" data-module-link_type="header">{{ _('Archived') }}</a></li>
</ul>
```

Bootstrap handles open/close via `data-bs-toggle="dropdown"` on the nav-item (task 017). No extra JS needed.

### CSS additions to `fanstatic/v2/navbar.css`

```css
/* ── Shared panel container ───────────────────────────────── */
.hdx-user-menu,
.hdx-notifications {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  z-index: 1050;
  min-width: 14.125rem;
  background: #fff;
  border: 1px solid #ebeff0;
  border-radius: 4px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.12);
  padding: 0.75rem 0.5rem 0.75rem 1rem;
}
.hdx-user-menu[hidden],
.hdx-notifications[hidden] { display: none; }

/* Parent must be position:relative for absolute panels */
.hdx-navbar__bell,
.hdx-navbar__avatar-trigger { position: relative; }

/* ── User menu ────────────────────────────────────────────── */
.hdx-user-menu__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ebeff0;
  margin-bottom: 0.5rem;
}
.hdx-user-menu__name { font-weight: 600; line-height: 130%; flex: 1; }
.hdx-user-menu__close {
  width: 1.25rem;
  height: 1.25rem;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hdx-user-menu__section { margin-bottom: 0.25rem; }
.hdx-user-menu__section-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 0.875rem;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0.125rem 0;
  font-family: inherit;
}
.hdx-user-menu__chevron { width: 1.25rem; transition: transform 0.15s; }
.hdx-user-menu__section-toggle[aria-expanded="false"] .hdx-user-menu__chevron {
  transform: rotate(-90deg);
}
.hdx-user-menu__section-items {
  list-style: none;
  margin: 0;
  padding: 0 0 0 1rem;
}
.hdx-user-menu__section-items[hidden] { display: none; }
.hdx-user-menu__section-items li { padding: 0.25rem 0; }
.hdx-user-menu__section-items a {
  font-size: 0.875rem;
  color: #101212;
  text-decoration: none;
}
.hdx-user-menu__section-items a:hover { text-decoration: underline; }

/* ── Notifications panel ──────────────────────────────────── */
.hdx-notifications__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ebeff0;
  margin-bottom: 0.5rem;
}
.hdx-notifications__title { font-weight: 600; font-size: 0.875rem; flex: 1; }
.hdx-notifications__close {
  width: 1.25rem;
  height: 1.25rem;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hdx-notifications__list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 18.75rem;
  overflow-y: auto;
}
.hdx-notifications__item {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #ebeff0;
  padding: 0.5rem 0;
  font-size: 0.875rem;
}
.hdx-notifications__item--sysadmin { background: lightyellow; }
.hdx-notifications__empty {
  font-size: 0.875rem;
  color: #6c757d;
  margin: 0;
  padding: 0.5rem 0;
}

/* ── Products dropdown ────────────────────────────────────── */
/* Bootstrap .dropdown-menu handles base styles.
   Scoped override only if needed: */
.hdx-products-menu { min-width: 18rem; }
```

### `fanstatic/v2/navbar.js` (new file)

Vanilla JS, self-contained IIFE. Initialize on `DOMContentLoaded`.

**Responsibilities:**

1. **Panel toggle** (`data-hdx-panel` on trigger buttons)
   - Clicking a trigger removes `hidden` from `#hdx-panel-{value}`, sets `aria-expanded="true"`.
   - Closes any other open custom panel first.
   - Second click on same trigger closes the panel.

2. **Panel close** (`data-hdx-close` on close buttons, ESC key, outside click)
   - Restores `hidden`, sets `aria-expanded="false"` on the trigger.
   - Outside click: close if click target is outside the panel and its trigger.

3. **User menu section collapse** (`.hdx-user-menu__section-toggle`)
   - Toggles `hidden` on the sibling `.hdx-user-menu__section-items`.
   - Flips `aria-expanded` attribute.

4. **Hamburger toggle** (task 019 integration — sets up offcanvas open)
   - Delegated to the offcanvas JS block (task 019); hamburger `data-hdx-panel="offcanvas"` is handled by rule 1.

No jQuery. No external dependencies.

`fanstatic/webassets.yml` already references `v2/navbar.js` in `v2-page-scripts` — no change needed.

## Open items

| # | Item                    | Notes                                                          |
|---|-------------------------|----------------------------------------------------------------|
| 1 | Products URLs           | All `#` — real URLs needed before launch                       |
| 2 | Sysadmin dashboard URLs | Some routes use `#` — verify actual route names in codebase    |
| 3 | Notification item links | Each `html_template` snippet needs a link URL per type         |
| 4 | `close.svg` icon        | Confirm path `v2/icons/close.svg` exists                       |
| 5 | `arrow-right.svg` icon  | Needed in notification item snippets                           |

## Why

The legacy user menu uses Bootstrap `dropstart` with jQuery collapse. The v2 design calls for a custom panel matching precise Figma shadow/border/sizing — not achievable cleanly with Bootstrap's built-in dropdown. The notifications panel replaces the old card-based dropdown with the same pattern. Both reuse the single `navbar.js` controller, keeping JS surface area minimal.
