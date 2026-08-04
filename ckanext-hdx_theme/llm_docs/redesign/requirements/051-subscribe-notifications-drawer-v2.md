# 051 — Subscribe to Notifications: Drawer (v2)

**Scope IN:** Reusable drawer component + subscribe/unsubscribe notification flow on the **dataset page only** (v2).
**Scope OUT:** Org page, group/location page, crisis page, any backend logic changes.

---

## Context

The existing Subscribe to Notifications system uses four Bootstrap 5 modals to handle the subscribe and unsubscribe flows on dataset, organisation, location, and crisis pages. In the v2 redesign, modals are replaced by a slide-in drawer component. This task introduces the drawer as a reusable v2 component (Phase 1) and migrates all four notification modals to drawers on the dataset page only (Phase 2). All other pages retain the existing modal implementation unchanged.

---

## 1. Existing Modal Audit

### 1.1 Templates

| Template | Role |
|---|---|
| `templates/notification_platform/modals.html` | Renders all four modal instances; injects reCAPTCHA script; data span `#notification_platform_data`; conditionally loads subscribe scripts |
| `templates/notification_platform/signup_modal_content.html` | Signup form body: email field, dataset-updates checkbox, reCAPTCHA widget |
| `templates/notification_platform/buttons.html` | Opt-in (`.notification-platform-opt-in-action-menu`) and opt-out (`.notification-platform-opt-out-action-menu`) trigger buttons — hidden by default via `hidden` attribute, shown by JS via `removeAttr('hidden')` |
| `templates/bem.blocks/modal.html` | Reusable modal macro: `id`, `title`, `content`, `text`, `close_btn_text`, `submit_btn_id`, `submit_btn_text`, `submit_btn_data_attributes` |
| `templates/package/hdx_read.html` | Dataset page template — includes `modals.html` and `buttons.html` |
| `templates/light/organization/read.html` | Org page — includes same snippets (OUT OF SCOPE) |
| `templates/country/country.html` | Location/country page (OUT OF SCOPE) |
| `templates/light/custom_pages/read.html` | Crisis page (OUT OF SCOPE) |

### 1.2 The Four Modals

| Modal ID | Role | Trigger |
|---|---|---|
| `notificationsSignupBemModal` | Subscribe form (email, checkbox, reCAPTCHA) | `.notification-platform-opt-in-action-menu` click, `.notification-platform-opt-in-floating-button` click, download event |
| `notificationsVerificationBemModal` | Confirmation shown after successful subscribe AJAX | Hidden signup modal triggers this |
| `notificationsUnsubscribeBemModal` | Unsubscribe confirmation dialog | `.notification-platform-opt-out-action-menu a` click (via unsubscribe.js) |
| `notificationsUnsubscribedBemModal` | Success state after unsubscribe AJAX | Hidden unsubscribe modal triggers this |

### 1.3 JS Files

| File | Role |
|---|---|
| `fanstatic/notification_platform/util.js` | Core: Bootstrap Modal references, AJAX calls, alert helpers, `showNotificationsSignupModal`, `displayNotificationOptinOption`/`OptoutOption`, analytics calls |
| `fanstatic/notification_platform/subscribe.js` | Binds click handlers on trigger buttons; form submit handler; `hide.bs.modal` listener to clear `popup_source` input |
| `fanstatic/notification_platform/unsubscribe.js` | Reads unsubscribe token from URL / localStorage; validates token; binds submit handler on `notificationsUnsubscribeButton` |

### 1.4 Modal Open/Close Mechanism

`util.js` uses Bootstrap 5 Modal API:
```js
var notificationsSignupModal = bootstrap.Modal.getOrCreateInstance($notificationsSignupModal.get(0));
notificationsSignupModal.show();   // opens
notificationsSignupModal.hide();   // closes
```

Bootstrap handles overlay (backdrop), ESC key, and focus restoration automatically.

`subscribe.js` listens for the Bootstrap close event to reset state:
```js
$notificationsSignupModal.on('hide.bs.modal', function () {
  $signupFormPopupSourceInput.val('');
});
```

### 1.5 Form Submission Flow (subscribe)

1. User clicks trigger button → `showNotificationsSignupModal(popupSource, …)` called
2. LocalStorage checked: if `popupSource === 'download'` and modal already shown for this object, skip
3. `notificationsSignupModal.show()` — Bootstrap opens modal
4. Analytics event fired: `'show popup'`
5. User fills email → submits form
6. `onSignupSubmit(objectId, objectName, objectType, authenticated)` called
7. `$.ajax POST /notifications/subscription-confirmation` with: `email`, `object_id`, `object_type`, `dataset_updates`, `g-recaptcha-response`, CSRF header
8. **Success:** hide signup modal → show verification modal → fire `'confirm popup'` analytics event → update localStorage subscribe state → show opt-out button
9. **Error:** show inline danger alert; reCAPTCHA reset

### 1.6 Form Submission Flow (unsubscribe)

1. User clicks opt-out button link (href contains `?_unsubscribe_token=…`)
2. `unsubscribe.js` reads token from URL params or data attributes on `#notificationsUnsubscribeButton`
3. `unsubscribeModal.show()` — Bootstrap opens confirmation modal
4. Analytics event fired: `'show popup'` for `'unsubscribe from notifications'`
5. User clicks confirm → `$.ajax POST /notifications/unsubscribe-confirmation` with: `token`, CSRF header
6. **Success:** hide unsubscribe modal → show unsubscribed modal → fire `'confirm popup'` analytics → update localStorage → show opt-in button
7. **Error:** show inline danger alert

### 1.7 Analytics Events

All four events use the same function signature:
```js
hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
  interactionType,  // 'show popup' | 'confirm popup'
  popupTitle,       // 'subscribe to notifications' | 'unsubscribe from notifications'
  popupSource,      // 'action menu' | 'floating button' | 'download' | null
  objectId,
  objectName,
  objectType,       // 'dataset' | 'group' | 'organization' | 'crisis'
  emailHash,        // hdxUtil.compute.strHash(email, 'notification_platform') or null
  authenticated
)
```

| # | When | interactionType | popupTitle | emailHash |
|---|---|---|---|---|
| 1 | Signup drawer opens | `'show popup'` | `'subscribe to notifications'` | `null` |
| 2 | Signup AJAX success | `'confirm popup'` | `'subscribe to notifications'` | hashed email |
| 3 | Unsubscribe drawer opens | `'show popup'` | `'unsubscribe from notifications'` | `null` |
| 4 | Unsubscribe AJAX success | `'confirm popup'` | `'unsubscribe from notifications'` | hashed email |

Dispatched to both Mixpanel and GTM dataLayer. **These calls must not change.**

### 1.8 reCAPTCHA

- Script tag injected once in `modals.html`: `<script src="https://www.google.com/recaptcha/api.js" async defer>`
- Widget rendered in `signup_modal_content.html` only when `not logged_in and g.recaptcha_publickey`
- Widget uses `data-sitekey="{{ g.recaptcha_publickey }}"` on a `.g-recaptcha` div
- Response token sent as `g-recaptcha-response` in AJAX payload
- Reset via `grecaptcha.reset()` on both success and error paths in util.js

### 1.9 Data Span

```html
<span id="notification_platform_data"
  hidden
  data-object-id="{{ object_id }}"
  data-object-name="{{ object_name }}"
  data-object-type="{{ object_type }}"
  data-is-authenticated="{{ current_user.is_authenticated }}">
</span>
```

JS reads all object context from this span. Must remain present on the page.

### 1.10 LocalStorage Usage

- `hdxUtil.net.getNotificationModalData()` / `updateNotificationModalData()` — prevents repeat-showing the signup modal when `popupSource === 'download'`
- `hdxUtil.net.getNotificationSubscribedObjects(objectType)` — tracks subscribed object IDs and their unsubscribe tokens

---

## 2. Figma Mapping

### 2.1 Figma Sources

| File | Describes |
|---|---|
| `llm_docs/redesign/figma_exports/drawer-legend-sm.html` | Drawer structural pattern at SM breakpoint: header (fixed), scrollable body, close icon |
| `llm_docs/redesign/figma_exports/subscribe-notifications-md.html` | Subscribe form inside drawer at MD breakpoint |
| `llm_docs/redesign/figma_exports/subscribe-notifications-xl.html` | Subscribe form inside drawer at XL breakpoint |

### 2.2 Drawer Structure (from `drawer-legend-sm.html`)

```
.c-drawer
  .c-drawer__overlay          ← full-viewport backdrop
  .c-drawer__container        ← slides in from right
    .c-drawer__header
      <title text>
      .c-drawer__close        ← icon button (1.5rem × 1.5rem)
    .c-drawer__body           ← scrollable content slot
```

Header: `padding: 1.5rem 1rem 0.75rem`, `gap: 1.5rem`
Close icon: `1.5rem × 1.5rem`

### 2.3 Subscribe Form Layout (from MD + XL Figma exports)

**Title:** Merriweather, `2rem`, `font-weight: 700`, `line-height: 130%`
**Description:** Roboto, `1rem`, `color: var(--hdx-neutral-darkest)` (≈ `#2f3536`), `line-height: 130%`
Includes "Learn more" link (underlined, font-weight 500) and "log in" inline link.

**Email field label:** Roboto, `1rem`, `font-weight: 500`; required asterisk in `var(--hdx-error)` (≈ `#c44536`)
**Email input:** border `1px solid var(--hdx-neutral-light)`, border-radius `2px`, height `2.313rem`, padding `0.5rem 0.75rem 0.5rem 1rem`
**"Already have an account? Log in"** — below the email field, right-aligned (or inline link)

**Dataset update frequency text:** Roboto, `0.875rem`, `font-weight: 600`

**reCAPTCHA container:** `width: 18.875rem`, `height: 4.75rem`, background `#f9f9f9`, border `1px solid #d3d3d3`, border-radius `3px`, box-shadow `0 0 4px 1px rgba(0,0,0,0.08)`

**Buttons:** right-aligned flex row, `gap: 1rem`
- Cancel: outlined, border `1px solid var(--hdx-neutral-light)`, background white, `max-width: 12.5rem`, padding `0.5rem 0.75rem`
- Submit ("Verify email address"): primary, background `var(--hdx-primary)` (≈ `#1862d8`), white text, `max-width: 12.5rem`, same padding

**Vertical gap between form elements:** `1.25rem`

### 2.4 Responsive Drawer Sizing

| Breakpoint | Drawer Width | Inner Padding (drawer-inner) |
|---|---|---|
| SM (`< @hdx-bp-md`) | `100%` | `1.5rem 1rem` (top/side) |
| MD (`@hdx-bp-md` to `@hdx-bp-xl`) | `~80%` | `3rem 2rem 1.5rem` (top / sides / bottom) |
| XL (`≥ @hdx-bp-xl`) | `~50%` | `2.5rem 2.5rem 1.5rem` (top / sides / bottom) |

Drawer slides in from the right edge. Width must use `%` or `flex` — no fixed `px` widths.

---

## 3. Phase 1 — Drawer Component

### 3.1 Structure

New snippet: `templates/v2/components/drawer.html`

Parameters:
- `drawer_id` — unique HTML id for the container (required)
- `title` — optional header title string
- `caller` block — content rendered inside `.c-drawer__body`

Rendered HTML:
```html
<div class="c-drawer" id="{{ drawer_id }}" aria-hidden="true" role="dialog" aria-modal="true">
  <div class="c-drawer__overlay" data-drawer-close></div>
  <div class="c-drawer__container" tabindex="-1">
    <div class="c-drawer__header">
      {% if title %}
        <span class="c-drawer__title">{{ title }}</span>
      {% endif %}
      <button class="c-drawer__close" aria-label="Close" data-drawer-close>
        <!-- X icon SVG -->
      </button>
    </div>
    <div class="c-drawer__body">
      {{ caller() }}
    </div>
  </div>
</div>
```

The drawer starts with `aria-hidden="true"` and class `.is-open` is toggled by JS.

### 3.2 LESS

New file: `hdx-styles/src/common/less/v2/components/drawer.less`

- `.c-drawer` — `position: fixed; inset: 0; z-index: var(--hdx-z-drawer); display: none;` (shown when `.is-open`)
- `.c-drawer__overlay` — full viewport, semi-transparent backdrop (`background: rgba(0,0,0,0.4)`)
- `.c-drawer__container` — positioned right, full height, `overflow-y: auto`, transition `transform 0.3s ease`; slides in from `translateX(100%)` → `translateX(0)`
- Widths via breakpoint mixins (no fixed px):
  - SM: `width: 100%`
  - MD: `width: 80%`
  - XL: `width: 50%`
- `.c-drawer__header` — flex row, space-between, sticky at top, `padding: var(--hdx-space-6) var(--hdx-space-4) var(--hdx-space-3)`
- `.c-drawer__body` — `padding: 0 var(--hdx-space-4) var(--hdx-space-6)` (overridden per content)
- `.c-drawer__close` — icon button, no background, `width: 1.5rem; height: 1.5rem`
- `.is-open` modifier on `.c-drawer` — `display: flex` (or block), body `overflow: hidden`

Design tokens: use `var(--hdx-space-N)`, `var(--hdx-z-*)`, existing color tokens. No raw rem values where a token exists.

### 3.3 JavaScript

New file: `fanstatic/javascript/v2/drawer.js`

Provides a `window.hdxV2Drawer(drawerId)` factory (not a constructor — call it each time you need a handle):

```js
window.hdxV2Drawer = function(drawerId) { ... }
```

Returns `{ open, close }`. Internally:
```js
function hdxV2Drawer(drawerId) {
  var drawer = document.getElementById(drawerId);
  var container = drawer.querySelector('.c-drawer__container');
  var lastFocus;

  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function getFocusable() {
    return Array.from(container.querySelectorAll(FOCUSABLE));
  }

  function open() {
    lastFocus = document.activeElement;
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    var focusable = getFocusable();
    if (focusable.length) focusable[0].focus();
    else container.focus();
    document.body.classList.add('drawer-open');
  }

  function close() {
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('drawer-open');
    if (lastFocus) lastFocus.focus();
    drawer.dispatchEvent(new CustomEvent('drawer:close'));
  }

  // ESC key + Tab focus trap
  document.addEventListener('keydown', function (e) {
    if (!drawer.classList.contains('is-open')) return;
    if (e.key === 'Escape') { close(); return; }
    if (e.key === 'Tab') {
      var focusable = getFocusable();
      if (!focusable.length) return;
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }
  });

  // overlay and close buttons
  drawer.addEventListener('click', function (e) {
    if (e.target.classList.contains('c-drawer__overlay') || e.target.closest('.c-drawer__close')) {
      close();
    }
  });

  return { open: open, close: close };
}
```

- ESC closes the active drawer
- Overlay click closes
- Focus returns to the element that triggered open (`lastFocus`)
- `drawer:close` custom event emitted for subscriber JS to hook into (replaces `hide.bs.modal`)
- No Bootstrap Modal dependency

### 3.4 Demo Page Integration

Add a new section in `templates/v2/components.html`:

```html
<section class="demo-section" id="drawer">
  <h1 class="demo-section__title">Drawer</h1>
  <p class="demo-section__subtitle">Slide-in panel from the right edge</p>
  <div class="demo-row">
    <button class="c-button c-button--primary" id="demo-drawer-trigger">Open drawer</button>
  </div>
  {% call h.snippet('v2/components/drawer.html', drawer_id='demo-drawer', title='Drawer title') %}
    <p>Drawer content goes here.</p>
  {% endcall %}
</section>
```

Include `drawer.js` in the `v2-components-scripts` webassets bundle (or equivalent shared v2 component bundle). Add `drawer.less` to the v2 component import list.

---

## 4. Phase 2 — Subscribe Flow (Dataset Page)

### 4.1 Scope Decision

All four notification modals are replaced by drawer panels **on the dataset page only**, gated by `{% if v2 %}`. Non-dataset pages and non-v2 paths continue using the existing Bootstrap modals unchanged.

### 4.2 Template Strategy

**Updated:** `templates/notification_platform/modals.html` — updated in place to render drawer components instead of Bootstrap modals. No separate `drawers.html` was created.

`modals.html` now:
- Loads `hdx_theme/v2-components-scripts` (includes `drawer.js`) in addition to its existing assets
- Retains the same `#notification_platform_data` span (unchanged)
- Retains the reCAPTCHA script injection (unchanged)
- Renders four drawer instances using `{% call h.snippet('v2/components/drawer.html', ...) %}`

**Four drawer IDs** (same names as old modal IDs for minimal JS delta):
- `notificationsSignupDrawer`
- `notificationsVerificationDrawer`
- `notificationsUnsubscribeDrawer`
- `notificationsUnsubscribedDrawer`

**Signup drawer body:** reuses `notification_platform/signup_modal_content.html` inside the drawer body.

**Verification / unsubscribed drawers:** render body text from the same Jinja constants as before.

**Unsubscribe confirmation drawer:** renders body text + submit button via the v2 button snippet (not raw HTML); `data-*` attributes passed via `attrs` dict.

### 4.3 Dataset Page Integration

`templates/package/hdx_read.html` includes `notification_platform/modals.html` unconditionally (no `{% if v2 %}` split). Since `modals.html` now renders drawers for all users, the v2 drawer experience applies to all dataset page visitors.

`page-header.html` now loads `notification_platform/buttons.html` to render the opt-in / opt-out CTAs in the dataset header. Parameters `notification_object_type`, `notification_object_id`, and `notification_object_dict` are threaded from `hdx_read.html` → `page-header.html` → `buttons.html`.

`templates/user/notifications.html` (hub page) no longer includes `modals.html` or notification scripts — unsubscribe happens on the object page via navigation link (see Decision 7).

### 4.4 JS Migration Strategy

Existing `subscribe.js` and `unsubscribe.js` were updated in place — no new `-v2.js` files created.

All three files — `util.js`, `subscribe.js`, `unsubscribe.js` — are vanilla JS (no jQuery). `$()`, `$.ajax`, and `.on()` are replaced with `document.querySelector`/`getElementById`, `fetch()`, and `addEventListener`. `fetch()` uses `new URLSearchParams(data)` as body with `Content-Type: application/x-www-form-urlencoded`; CSRF token merged from `hdxUtil.net.getCsrfTokenAsObject()` via `Object.assign`. The `drawer:close` custom event (dispatched by `drawer.js` via `dispatchEvent(new CustomEvent('drawer:close'))`) is listened to with `addEventListener('drawer:close', fn)` in `subscribe.js`.

### 4.5 Form Component Reuse

| Element | Source | Change needed |
|---|---|---|
| Email input | `signup_modal_content.html` | None — reused as-is |
| Dataset-updates checkbox | `signup_modal_content.html` | None |
| reCAPTCHA widget | `signup_modal_content.html` | None |
| Form validation | `fanstatic/v2/form-validator.js` | New vanilla JS validator; activated via `data-hdx-v2-form-validator` on `<form>`; bundle `v2-form-validator-scripts` loaded by `modals.html` |
| Cancel button | New in drawer footer area | Use v2 `c-button--tertiary` or outlined variant; add `data-drawer-close` attribute |
| Submit button | Replaces modal footer submit | Use v2 `c-button--primary` |

The existing form's cancel button uses `data-drawer-close`, handled generically by `drawer.js` — no explicit binding needed.

---

## 5. Analytics Preservation

The four analytics events (§1.7) are called in `util.js`. The function signature and call sites do not change. The only change is that the code path to reach them goes through `HdxDrawer.open()` / `close()` instead of Bootstrap Modal API — the analytics calls happen at the same logical moments:

| Event | Moment | Location in code | Change |
|---|---|---|---|
| Show signup | After `notificationsSignupDrawer.open()` | `showNotificationsSignupModal` in util.js | Rename function or add v2 variant; analytics call stays identical |
| Confirm signup | In AJAX success callback | `onSignupSubmit` in util.js | No change |
| Show unsubscribe | After `notificationsUnsubscribeDrawer.open()` | unsubscribe.js | Same call |
| Confirm unsubscribe | In AJAX success callback | `onUnsubscribeSubmit` in util.js | No change |

---

## 6. Responsive Strategy

| Breakpoint | Drawer width | Drawer padding |
|---|---|---|
| SM `< 48rem` | `100%` | `var(--hdx-space-6) var(--hdx-space-4)` |
| MD `48rem – 80rem` | `80%` | `var(--hdx-space-12) var(--hdx-space-8) var(--hdx-space-6)` |
| XL `≥ 80rem` | `50%` | `var(--hdx-space-10) var(--hdx-space-10) var(--hdx-space-6)` |

Breakpoint tokens from `hdx-styles/src/common/less/v2/breakpoints.less` (`@hdx-bp-md`, `@hdx-bp-xl`).

Form elements inside the drawer body stretch to fill the available width (`align-self: stretch` / `width: 100%`). At MD and below, the form is naturally constrained by the 80%/100% drawer width. At XL the drawer is 50% of viewport — no fixed form width needed.

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| Drawer opened while already open | `open()` is idempotent — checks `.is-open` class before adding it |
| Signup submission error | Inline `.alert-danger` shown inside drawer body (same selectors as today) — reCAPTCHA reset |
| reCAPTCHA failure / token missing | Server returns `success: false` → inline alert shown; `grecaptcha.reset()` called |
| Drawer opened via "download" popup source multiple times | LocalStorage guard in `showNotificationsSignupModal` unchanged — prevents repeat shows |
| Small screen scrollable content | `.c-drawer__body` has `overflow-y: auto`; `.c-drawer__header` is sticky at top of container |
| Multiple drawers on page | Each `HdxDrawer` instance scoped to its own ID; ESC handler checks `.is-open` on each |
| Verification / unsubscribed drawers have no form | Body renders text-only content; drawer structure the same |
| Focus trap | Full ARIA focus trap implemented in `drawer.js`: Tab/Shift+Tab cycle through all focusable elements within the drawer; ESC closes. `lastFocus` restored on close. Required in Phase 1. |

---

## 8. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Analytics events silently broken after migration | ❗ Critical | All four event calls are in `util.js` and untouched; add a smoke test that confirms events fire on drawer open/submit |
| AJAX submission broken by DOM selector mismatch | ❗ Critical | ✅ Resolved — util.js selectors updated to target drawer IDs (`#notificationsSignupDrawer` etc.) |
| Bootstrap Modal still initialised on v2 page (conflicts) | High | ✅ Resolved — `modals.html` renders only drawer HTML; all Bootstrap Modal API calls removed from util.js/subscribe.js/unsubscribe.js |
| reCAPTCHA script loaded twice | Medium | Inject script tag only once in `modals.html` |
| v1 pages broken by changes to `util.js` | High | Keep v1 code paths intact; add v2 drawer paths as additive branches, not replacements |
| Drawer not fully accessible (focus trap) | Medium | Minimum: focus is moved to container on open and restored on close. Full ARIA focus trap can be added later |

---

## 9. Files Affected

### New Files

| File | Purpose |
|---|---|
| `templates/v2/components/drawer.html` | Reusable drawer Jinja2 snippet |
| `fanstatic/javascript/v2/drawer.js` | `window.hdxV2Drawer(id)` factory — open/close/ESC/overlay/full focus trap |
| `hdx-styles/src/common/less/v2/components/drawer.less` | Drawer LESS component |
| `fanstatic/v2/form-validator.js` | Vanilla JS form validator; auto-init on `form[data-hdx-v2-form-validator]`; full v1 validation parity; `c-form-validator__live-feedback` live feedback with CSS `::before` icons |

### Modified Files

| File | Change |
|---|---|
| `templates/notification_platform/modals.html` | Rewritten to render four drawers using `v2/components/drawer.html`; assets updated; unsubscribe button uses v2 button snippet |
| `templates/notification_platform/buttons.html` | Rewritten to use v2 button snippets; `d-none` → `hidden` attribute |
| `templates/v2/components/page-header.html` | Loads `notification_platform/buttons.html` for dataset opt-in/opt-out CTAs |
| `templates/package/hdx_read.html` | Threads `notification_object_type/id/dict` params to `page-header.html` |
| `fanstatic/notification_platform/util.js` | jQuery → vanilla JS; `$.ajax` → `fetch`; Bootstrap Modal → `window.hdxV2Drawer()` |
| `fanstatic/notification_platform/subscribe.js` | jQuery → vanilla JS; `hide.bs.modal` → `addEventListener('drawer:close', ...)` |
| `fanstatic/notification_platform/unsubscribe.js` | jQuery → vanilla JS; hub click handler removed |
| `templates/user/notifications.html` | Unsubscribe link is real navigation (`?_unsubscribe_token=...`); `modals.html` snippet and notification scripts removed |
| `hdx-styles/src/common/less/v2/components/input-field.less` | `.c-form-validator__live-feedback` BEM styles appended (live feedback list with `::before` icons) |
| `fanstatic/webassets.yml` | Added `v2-form-validator-scripts` bundle; added `jquery.js` to `v2-page-scripts`; added `drawer.js` to `v2-components-scripts` |
| `templates/v2/components.html` | Drawer demo section (3 generic lorem ipsum drawers); "Search input — with label" demo subsection |
| `hdx-styles/src/common/less/v2/components.less` | Import `drawer.less` |

---

## 10. Decisions Taken

| # | Decision |
|---|---|
| 1 | **Cancel button uses `data-drawer-close` attribute.** The signup form cancel button uses `data-drawer-close` so that `drawer.js` handles it generically. No explicit binding needed in `subscribe.js`. |
| 2 | **Verification and unsubscribed drawers require explicit close.** No auto-close timer. User must click X or overlay — matches existing modal behaviour. |
| 3 | **Full ARIA focus trap required in Phase 1.** Tab key must cycle within the open drawer. `drawer.js` implements a full focus trap (query all focusable elements, intercept Tab/Shift+Tab). |
| 4 | **New `v2/form-validator.js` created (vanilla JS, not CKAN module).** The existing `hdx-form-validator` module remains for v1 pages. v2 pages use `data-hdx-v2-form-validator` on `<form>` and load `v2-form-validator-scripts`. All v1 validation types preserved; live feedback uses `c-form-validator__live-feedback*` BEM classes with CSS `::before` icons instead of FontAwesome. |
| 5 | **`drawer.js` is part of a `v2-components-scripts` bundle** (or equivalent shared v2 component bundle), keeping it consistent with the existing v2 loading pattern. |
| 6 | **The subscribe form title (Merriweather, 2rem, bold) is rendered in the drawer header** via the `title` param of the drawer snippet. The notification content template does not render its own heading. `.c-drawer__title` is styled with Merriweather bold. |
| 7 | **Hub unsubscribe uses navigation link, not AJAX.** The `notifications.html` hub page renders `<a href="{{ subscription.object_link }}?_unsubscribe_token=...">` — a real navigation link. On arrival at the object page, the existing Python token validation + `unsubscribe.js` auto-opens the unsubscribe drawer. No drawers or JS needed on the hub page itself. |
