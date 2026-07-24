# 064 — Auth Pages (Login / Forgot Password / Confirmation / Perform Reset) v2 Migration

**Scope:** Visual migration of the login page, the forgot-password ("request reset") page and its
confirmation state, and the perform-reset ("set new password") page reached via the emailed reset
link, to v2 — layout, spacing, typography, colors, responsive behavior (SM/MD/XL), and component
reuse. Existing validation logic, submission mechanics (full POST vs AJAX/JSON), analytics (none
today), and backend/API contracts are preserved. Two narrow, explicitly-scoped exceptions: adding a
missing CSRF hidden field to the login form (see §12, Decision 6), and folding in the perform-reset
page after the fact with no Figma source (see §12, Decision 5).

**Excluded:** authentication logic, backend/API changes beyond the scoped CSRF addition.

**Figma sources:** `xl-login-filled-with-error.html`, `xl-forgot-password.html`,
`xl-forgot-password-confirmation.html`, `md-login-filled-with-error.html`, `sm-login.html`,
`sm-forgot-password.html`, `sm-forgot-password-confirmation.html`. None for perform-reset — it
reuses the `hdx-v2-auth-card` shell verbatim (§1.4, §12 Decision 5).

---

## Context

There are **two parallel template sets** for these flows in the repo, and only one is live. Core
CKAN's own `ckan/templates/user/login.html` / `user/request_reset.html`, and hdx_theme's classic
overrides of them, are **dead code** for the routes below — a later blueprint registration wins the
URL. The live implementation is a jQuery "popup/widget" system under
`ckanext-hdx_theme/ckanext/hdx_theme/templates/widget/onboarding/*`, wired up by custom Flask
blueprints in `ckanext-hdx_users`:

| Route | View | Live template chain |
|---|---|---|
| `/login`, `/sign-in`, `/user/login` | `hdx_signin.login()` — `ckanext-hdx_users/ckanext/hdx_users/views/signin.py:73-150` | `user/signin.html` → `widget/onboarding/login.html` |
| `/user/reset` | `HDXRequestResetView` — `ckanext-hdx_users/ckanext/hdx_users/views/user.py:50-125` | `user/forgot_password.html` → `widget/onboarding/recover.html` + `recoverSuccess.html` (JS popup-swap on the same route) |
| `/user/reset/<id>` (emailed link) | `HDXPerformResetView` — `user.py:128-160` | `user/perform_reset.html` → `v2/page.html` (`hdx-v2-auth-card`) |

None of these three templates have any `{% if v2 %}` gating today — this is a **net-new v2 build**,
not a toggle-on of hidden v2 markup. Decisions confirmed with the requester are listed in §12.

---

## 1. Existing Implementation Audit

### 1.1 Login

- View: `signin.py`'s `login()` (lines 73-150) is a ground-up reimplementation, not a subclass of
  core CKAN's `ckan/views/user.py:561-606 login()`. Custom `_authenticate()` (lines 35-48) iterates
  `IAuthenticator` plugins directly and only succeeds via `ckanext-security`'s authenticator — core's
  `ckan_authenticator()` fallback is deliberately skipped.
- Template: `widget/onboarding/login.html` (extends `widget/popup/popup.html`). Fields: `#field-login`
  (text, `name="login"`, label "Username or Email", `required`, line 51), `#field-password` (password,
  `name="password"`, label "Password", `required`, line 56), `#field-mfa` (number, `name="mfa"`, label
  "One Time Password", hidden by default, revealed by JS only when the account has TOTP enabled),
  `#field-remember` (checkbox, `name="remember"`, value `"63072000"`, unchecked by default, line 67).
  Submit button starts `disabled` (line 68) and is enabled by JS once required fields are filled. Links:
  "Forgot your password?" → `/user/reset` (line 69), "Not a member? Register" → onboarding value
  proposition (lines 70-72), a back-arrow to `data.login_came_from` or the splash page (line 22) — this
  is login's equivalent of the close affordance seen on the other two pages.
- **CSRF gap:** `widget/onboarding/login.html` has **no `{{ h.csrf_input() }}`** and no hidden
  CSRF field of any kind — confirmed by inspection, zero matches for "hidden"/"token" in the file. Both
  `widget/onboarding/password-reset.html:27` and `ckan/templates/user/request_reset.html:16` include
  one. CKAN's CSRF protection is not globally disabled for plugin blueprints
  (`ckan.csrf_protection.ignore_extensions = false`), so this is a real, pre-existing gap — see §12
  Decision 6 for the scoped fix.
- Error display: a single inline block, not CKAN's flash-message system —
  `<div class="error-message" style="{{ '' if error_message else 'display: none;' }}">{{ error_message }}</div>`
  (lines 64-66). `error_message` is a plain string set server-side: `_("Login failed. Bad username or
  password.")` (`signin.py:142`). There is no per-field error state and no `error_summary`/`errors`
  dict for login — contrast with the dead-code core snippet, which does support per-field errors.
  The unvalidated-email case is handled entirely differently: `signin.py:108-113` logs the user out,
  flashes a message, and **redirects to the splash page** — a different error surface than the inline
  login-widget message.
- Rate limiting / lockout: real enforcement is server-side in `ckanext-security`
  (`src/ckanext-security/ckanext/security/authenticator.py`, `LoginThrottle` at
  `src/ckanext-security/ckanext/security/cache/login.py:27-67`), keyed by username or IP. A client-side
  preview endpoint, `GET /util/user/check_lockout` (`ckanext-hdx_users/ckanext/hdx_users/views/user_edit_view.py:74-83`),
  is called synchronously by `signin.js:13-29` before the real POST. **Pre-existing bug:**
  `signin.js:24` calls `_showLoginError(...)`, but no such function is defined anywhere in the fanstatic
  tree — if this branch is hit, the reference error aborts the handler before `event.preventDefault()`
  runs, so the intended client-side lockout warning silently fails to render (the server-side throttle
  still rejects the request; only the friendly pre-warning is broken). Flagged in §8, not fixed here
  beyond the natural consequence of §5 replacing this handler wholesale.
- MFA/TOTP: `GET /util/user/check_mfa` (`user_edit_view.py:87-95`) is used by `signin.js:48-64` to
  reveal `#field-mfa`; actual verification happens inside `ckanext-security`'s authenticator.
- JS: `fanstatic/widget/signin/signin.js` (bundle `signin-scripts`, `webassets.yml:506-510`). The
  login submit itself is a plain full-page POST (no AJAX) — JS only does lockout pre-check, MFA
  toggling, submit-button enable/disable (`requiredFieldsFormValidator`, duplicated verbatim in both
  `signin.js:66-81` and `onboarding.js:89-104`), and "remember me" cookie read/prefill with Gravatar
  (lines 91-106).
- Analytics: `user/signin.html:30-31` blanks `{% block mixpanel_init %}` and
  `{% block google_analytics_init %}` — both empty. See §1.5.

### 1.2 Forgot Password ("request reset")

- View: `HDXRequestResetView` (`user.py:50-125`) is an independent `MethodView`, not a subclass of
  core's `RequestResetView` for `get`/`post`. `GET /user/reset` renders `user/forgot_password.html`,
  which renders three widgets on one page load: `widget/onboarding/recover.html` (the form),
  `widget/onboarding/recoverSuccess.html` (the confirmation, hidden until swapped in), and
  `widget/loading/loading.html` (a redirect-in-progress screen).
- Form: `widget/onboarding/recover.html` (extends `widget/onboarding/notification.html` →
  `widget/popup/popup.html`). Body copy: "Enter your username or email below and we will send you an
  email with a link to enter a new password." (line 21). Single field `#field-recover-id`
  (`name="user"`, `type="text"`, `required`, line 26) — accepts username or email, no `@`-format
  validation, matching core CKAN semantics. **Accessibility bug found:** the field's `<label>` (line
  25) is `for="field-login"` — a copy-paste artifact from `login.html` — while the actual input id is
  `field-recover-id`, breaking the label/input association. Flagged for a fix in §7, independent of any
  copy-wording decision.
- `<form id="recover-form" onsubmit="return false;">` (line 19) — the native submit is always
  suppressed; this is a pure AJAX form (see §1.3).
- reCAPTCHA: invisible v2, bound directly to the submit button —
  `<input class="... hdx-recaptcha ..." disabled type="submit" value="Reset" data-sitekey="..." data-callback='onSubmit' data-size="invisible" data-badge="inline">`
  (line 42). No visible challenge unless Google's risk engine triggers one.
- No CSRF hidden field in the markup — CSRF is added via the AJAX call's headers instead (see §1.3),
  which is a legitimate pattern for that path.
- Footer: "Not a member? Register" (line 45).

### 1.3 Confirmation

There is **no separate route or template** for "confirmation" today — it's a same-page, JS-driven
popup swap:

1. `widget/onboarding/forgot-password.js:1-7` calls `showOnboardingWidget('#recoverPopup')` on
   `$(document).ready`, so the recover form is what opens by default.
2. On submit, `widget/onboarding/recover.js:4-26` intercepts and does:
   `$.ajax({ url: "/user/reset", type: 'POST', data: $this.serialize(), headers: hdxUtil.net.getCsrfTokenAsObject(), success: ... })`.
   On success (`result.success`), it closes the recover widget and calls
   `showOnboardingWidget('#recoverSuccessPopup')`. On failure, it shows `result.error.message` inline in
   `.error-message` and adds an `.error` class to the input — all client-side, no page reload.
3. The confirmation UI is `widget/onboarding/recoverSuccess.html`: title `"Please check your email"`,
   body `"Email was sent if the username or <br/>email address matched in our system."`, plus an
   animated mail-envelope gif. Its close button (`forgot-password.js:3-6`) shows a loading screen and
   redirects to `/`.
- Backend returns **JSON, not HTML**: `HDXRequestResetView.post()` (`user.py:57-125`) returns raw
  `json.dumps(...)` strings via constants in `ckanext-hdx_users/ckanext/hdx_users/views/user_view_helper.py:1-24`.
  Every user-found-or-not path returns the same success shape (lines 92-94, 101, 113-115, 120, 123) —
  this intentionally never discloses whether an account exists, matching core CKAN's own
  `RequestResetView.post()` behavior. This contract must not change.

### 1.4 Perform Reset (`/user/reset/<id>`)

Reached only via the emailed token link, and structurally its own screen: full-page POST (not AJAX),
core CKAN flash-message error handling (`post()` is inherited unmodified from
`ckan/views/user.py:828-877`), and its own copy about password rules. No Figma export exists for it —
folded into this task after the initial migration per §12 Decision 5, reusing the login/forgot-password
`hdx-v2-auth-card` shell verbatim rather than following a design export.

- Template: `user/perform_reset.html` now extends `v2/page.html` directly (same shell as
  `user/signin.html`) instead of `base.html` + the old `widget/onboarding/password-reset.html` popup.
- Fields: `password1`/`password2`, rendered via `v2/components/search-input.html` (`type='password'`),
  labels "Password" / "Confirm password" (the latter changed from the old widget's "Confirm" for
  consistency with the signup page's `password2` label — §12 Decision 15). Field `name`s, CSRF
  (`h.csrf_input()`), and the empty-`action` full-page POST are all unchanged, so
  `HDXPerformResetView`'s inherited `_get_form_password()`/`post()` keep working with no view changes.
- Client-side validation: kept at today's level — required-field-only submit gating (new
  `fanstatic/v2/perform-reset-page.js`, bundle `v2-perform-reset-page-scripts`), mirroring the old
  widget's `requiredFieldsFormValidator`. The signup page's live password-strength/match checklist
  (`v2/form-validator.js`) is deliberately **not** reused here — see §12 Decision 14.
- Error handling: `HDXPerformResetView.post()` is inherited unmodified from core and never passes an
  `errors`/`error_summary` context var — it only calls `h.flash_error(...)`/`h.flash_success(...)` and
  re-renders the same template. The new template does not override `{% block flash %}`, so the
  inherited `v2/page.html` flash block (existing `hdx-v2-flash {category}` + legacy
  `.alert-danger`/`.alert-error` CSS) is the sole error/success surface, same as it already is for the
  forgot-password page's own expired-link redirect.
- Analytics: kept untracked — `mixpanel_init`/`google_analytics_init`/`hotjar_init` all blanked, same
  as before and as the sibling pages (§1.5, §11).
- Styling: reuses `hdx_theme/v2-auth-page-styles` (`auth-page.less`'s `hdx-v2-auth-card` BEM elements)
  as-is; no new LESS.

### 1.5 Analytics (today)

All three live pages explicitly blank the base template's tracking blocks:

- `user/signin.html:30-31` → `mixpanel_init`, `google_analytics_init` both empty.
- `user/forgot_password.html:36-38` → same two, plus `hotjar_init` empty.
- `user/perform_reset.html` → same three, empty.

GTM (`GTM-MFNPQ7K`) and Mixpanel are otherwise injected globally by `base.html`'s
`google_analytics_init`/`mixpanel_init` blocks — every other page gets this for free by not blanking
them. **There is no login/reset-specific tracking today** — no `dataLayer.push`, no `mixpanel.track`,
no `data-ga-*` attribute anywhere referencing login/signin/password-reset. See §11 and §12 Decision 7.

---

## 2. Figma Mapping

All exports use raw Figma-generated custom properties (`--color-*`, `--padding-*`, `--gap-*`, `--fs-*`,
`--br-*`), not `--hdx-*` tokens, and literal hex/rem values — these need mapping to real design tokens
during implementation, not treated as a source of truth for variable names.

### `xl-login-filled-with-error.html`

```
.xl-login-filled-with-error (full-bleed dark section, #0b2d24, 12-col grid)
├── .navbar (teal #18614c bar, logo only — no menu/search in this crop)
└── .log-in-parent (centered white card, 25rem wide, 2.5rem padding, absolutely positioned)
    ├── "Log in"                      ← heading, Merriweather 700, 2rem
    ├── Email field (filled, valid — no error state on this field)
    ├── Password field (masked, eye-off icon)
    │   └── warning-parent            ← red border on field + inline error below:
    │       "Incorrect email or password" (red text + warning icon)
    ├── ☐ "Remember me"
    ├── [Log in] button
    ├── "Forgot password?" (link)
    └── "Don't have an account? Sign up"
```

The error is tied **only to the password field** (red border + inline warning below it) — not a
top-of-form banner. Current implementation renders one generic message instead (§1.1); §3 maps this.

### `md-login-filled-with-error.html`

Effectively an **empty stub** — only the outer grid wrapper and the teal navbar with logo render. No
card, no form fields, no error state, no heading, no button. Cannot serve as a spec for MD. Per §12
Decision 4, MD is derived from `sm-login.html` instead.

### `sm-login.html`

```
.sm-login (flex-column, dark bg, navbar in normal flow above the card)
├── navbar (24.563rem wide — mobile viewport minus padding; logo + search icon + hamburger menu,
│           both wired to empty click-handler stubs in the export)
└── .md-form (card, 21.875rem wide, 3rem padding — literal class name "md-form" despite being
             in the sm-login file, a Figma layer-naming leftover)
    ├── "Log in"                      ← heading, 1.75rem (smaller than XL's 2rem)
    ├── Email field (placeholder "Your email", empty/clean state — no error here)
    ├── Password field (placeholder "Enter your password", eye-off icon)
    ├── ☐ "Remember me"
    ├── [Log in] button
    └── "Don't have an account? Sign up"
```

No error state depicted in this export (clean-state only, unlike the XL export). Card is narrower than
XL (350px vs 400px) but has more padding (48px vs 40px).

### `xl-forgot-password.html`

```
.xl-forgot-password (same dark full-bleed + teal navbar pattern as login)
└── .frame-parent (card, 25rem wide, 2.5rem padding — identical dimensions to the login card)
    ├── "Forgot your password?" + [X] close icon   ← heading row
    ├── "Enter your username or email below and we will send you an email with a link to
    │    enter a new password."
    ├── "Username or email" field
    ├── reCAPTCHA mock — static "I'm not a robot" checkbox + "reCAPTCHA" branding footer
    │   (non-literal — see §12 Decision 2)
    ├── [Reset] button
    └── "Don't have an account? Sign up"
```

No error state in this export. No "Forgot password?" link here (this *is* that page) and no explicit
"back to login" text link — the only way back in the mock is the [X] close icon, which maps directly
onto the existing `notification.html`/`popup.html` `.close` icon and `closeCurrentWidget()` behavior
(§1.3) — already reused as-is, not new.

### `xl-forgot-password-confirmation.html`

```
.xl-forgot-password-confirmatio (same dark full-bleed + navbar; card ~half the height of the others)
└── .frame-parent (card, 25rem wide, 2.5rem padding)
    ├── "Check your email" + [X] close icon
    └── "Email was sent if the username or email address matched in our system."
```

No fields, no button, no footer links — purely a confirmation message. `[X]` again maps onto the
existing close-and-redirect-home behavior (`forgot-password.js:3-6`).

### `sm-forgot-password.html` / `sm-forgot-password-confirmation.html`

Same structure/copy as their XL counterparts, headings drop to 1.75rem (forgot-password) / 1.75rem
(confirmation, vs XL's 2rem), reCAPTCHA mock slightly smaller. **Card padding inconsistency found:**
`sm-forgot-password.html`'s card uses `2.5rem` padding, while `sm-login.html`'s card uses `3rem` —
standardized on `2.5rem` for all three SM cards (Decision 13, §6/§8). The close icon in both SM exports
is exported under the CSS class `.menu-icon` (a mislabeling artifact — visually it's still the same
close glyph as the XL `[X]`, per context).

### Responsive summary (XL vs MD vs SM)

| Aspect | XL | MD | SM |
|---|---|---|---|
| Card positioning | `position: absolute`, centered over a full-bleed dark 12-col grid | No spec (stub) — derive from SM per Decision 4 | Normal flex flow, card stacks below the mobile navbar |
| Card width (login/forgot-password) | 25rem | — | 21.875rem |
| Card padding | 2.5rem (all three page types) | — | 2.5rem (all three page types — standardized per Decision 13, overriding `sm-login.html`'s exported 3rem) |
| Heading size | 2rem | — | 1.75rem |
| Navbar | Full desktop bar, logo only | Bar present, logo only, no card below it | Mobile bar: logo + search icon + hamburger, both wired to empty stubs |

---

## 3. Form & Validation Mapping

| Field / element | Current | Redesigned (v2) |
|---|---|---|
| Login — username/email | `#field-login`, plain `<input required>`, label "Username or Email" | `v2/components/search-input.html` (`type='text'`), same `name`/`required`; label stays "Username or Email" (Decision 8) — Figma's "Email" is not adopted since the field still accepts either |
| Login — password | `#field-password`, plain `<input type="password" required>` | `search-input.html` with `type='password'` — built-in eye/eye-off toggle matches Figma's icon exactly, no bespoke JS needed |
| Login — MFA/OTP | `#field-mfa`, `<input type="number">`, hidden until JS reveals it | `search-input.html` with `type='number'`, same JS-driven `hidden`/reveal logic (`check_mfa`), no new component. "Forgot your password?" is positioned directly after this field in the DOM (not after the password field) so it renders below the OTP field whenever MFA is revealed, matching Figma's password→link ordering with the OTP field spliced in between |
| Login — remember me | `#field-remember`, checkbox, value `"63072000"` | `v2/components/checkbox.html`, same `name`/`value` preserved as-is (§8 flags the value's odd semantics, not to be touched) |
| Login — error | Single `.error-message` div, generic string, shown/hidden via inline `style` | Figma ties the error visually to the password field: render via `search-input.html`'s `errors` prop on the password field (adds `.c-search-input--error` + inline message) — same generic `error_message` string from `signin.py:142`, just re-targeted to the password field's error slot instead of a floating top div. Wording stays as-is (Decision 9) — Figma's "Incorrect email or password" is not adopted |
| Forgot password — user | `#field-recover-id`, plain `<input required>`, mislabeled `for` attribute (§1.2 bug) | `search-input.html` (`type='text'`), `errors` prop wired to `result.error.message` from the existing AJAX response — same JSON contract, only the rendering target changes. Label/input association bug fixed here |
| Forgot password — submit/status | JSON success/error handled by hand-rolled JS (`recover.js`) toggling `.error-message`/`.error` classes | Same AJAX call and JSON shape; JS updates `c-search-input--error` state and a `c-form-alert` (or the field-level error span) instead of legacy classes — no change to the request/response contract |
| reCAPTCHA | Invisible v2, bound to submit button | Unchanged (§12 Decision 2) — Figma's visible checkbox mock is not implemented |
| Perform reset — new password | `#field-password` (`password1`), plain `<input required>`, label "Password" | `search-input.html` with `type='password'` — same eye toggle as login's password field |
| Perform reset — confirm password | `#field-confirm-password` (`password2`), plain `<input required>`, label "Confirm" | `search-input.html` with `type='password'`, label changed to "Confirm password" (Decision 15) |
| Perform reset — submit gating | `requiredFieldsFormValidator` (required-only) | New `v2/perform-reset-page.js`, same required-only gating — signup's live strength/match checklist deliberately not adopted (Decision 14) |
| Perform reset — server error | `h.flash_error(...)`/`h.flash(..., category='alert-error')` only, no `errors` dict | Unchanged — surfaced via the inherited `v2/page.html` flash block (§1.4), no per-field `errors` prop wired since core never passes one |

No validation *logic* changes anywhere in this table — every row is a rendering-target change onto
existing v2 components, using the same field names, the same required-ness, and the same
error-message sources.

---

## 4. Component Strategy

| UI element | Approach | Justification |
|---|---|---|
| Username/email/password/MFA/user text inputs | **Reuse** `v2/components/search-input.html` | Already supports `type='password'` with a built-in eye toggle (matches Figma exactly, no new JS), `label`/`required`/`errors` props cover every field in scope |
| Remember me | **Reuse** `v2/components/checkbox.html` | Already supports `label` + `errors`; no new component needed |
| Submit / secondary buttons | **Reuse** `v2/components/button.html` | `style='primary'` for Log in/Reset, `style='tertiary'`/text-link for Register/Sign up/Cancel-style links |
| "Forgot password?" / "Sign up" / "Not you?" links | **Reuse** `v2/components/text-link.html` / `text-button.html` | Existing generic link/button components already used elsewhere for this exact pattern. "Forgot password?" uses `style='tertiary'` (Figma's `.text-link` color is a dark neutral, not the royal-blue used for "Sign up"); "Sign up" stays `style='primary'` |
| Top-level / field-level error and status messages | **Reuse** `v2/components/form-alert.html` and `search-input.html`'s built-in `errors` slot | `c-form-alert` is the established v2 pattern for form-level status (per `request_access.html:60-62`); field-level errors use the input's own `errors` prop, matching Figma's per-field error treatment |
| Page shell (logo-only navbar, dark background, no site header/footer/breadcrumb) | **Extend** the pattern from `error_document_template.html` | Closer analog than `request_access.html` (which keeps the full v2 site header/footer/breadcrumb chrome) — Figma shows only a logo bar and no footer on all three auth pages, matching how `error_document_template.html` extends `v2/page.html` with `header`/`footer` blocks emptied out |
| MFA/OTP input | **Extend** `search-input.html` (`type='number'`) | No dedicated MFA component exists or is needed — it's a plain numeric text input |
| Popup/modal chrome (`widget/popup/popup.html`, `notification.html`) | **Reuse as-is** | No v2 equivalent exists; the close-icon/`closeCurrentWidget()` behavior for forgot-password/confirmation is preserved unchanged (§1.3, §5) |
| reCAPTCHA visible checkbox | **Not implemented** | Per Decision 2 — current invisible integration is kept, rendered into a dedicated `#recover-recaptcha` container rather than the submit button |

---

## 5. Interaction Mapping

- **Login submit** — unchanged full-page POST to `signin.py`'s `login()`. Client-side: lockout
  pre-check (`GET /util/user/check_lockout`) before submit; the v2 JS rewrite (replacing `signin.js`
  against new v2 markup/classes) naturally retires the broken `_showLoginError` reference (§1.1, §8) by
  wiring the lockout message into the redesigned error UI from scratch — not left broken.
- **MFA reveal** — `GET /util/user/check_mfa` still toggles the (now `search-input.html`-based) MFA
  field's visibility exactly as today.
- **Remember me** — cookie prefill/Gravatar behavior (`signin.js:91-106`) is preserved; the checkbox
  component's `name`/`value` stay identical so the server-side handling in `signin.py:124-134` needs no
  change.
- **Forgot password submit → confirmation** — unchanged AJAX/JSON contract (§1.3, §3). On success, the
  v2 recover widget is hidden and the v2 confirmation widget is shown in place — same
  `showOnboardingWidget`/`closeCurrentWidget` mechanism, no navigation, no new route (§12 Decision 3).
- **Close icon (forgot-password, confirmation)** — maps onto the existing `.close`
  icon/`closeCurrentWidget()` pattern already provided by `notification.html`. Confirmation's close
  additionally triggers the existing loading-screen-then-redirect-to-`/` behavior (`forgot-password.js:3-6`)
  — reused as-is.
- **Back arrow (login)** — none. No login Figma export (`xl-login-filled-with-error.html`, `sm-login.html`,
  the MD stub) shows any back/close affordance in the card header — only the "Log in" heading.
  `login_came_from` stays wired to the form's `action` URL; there is no visual back link.
- **reCAPTCHA** — unchanged invisible v2 flow, rendered into a dedicated container (`#recover-recaptcha`,
  between the field and the button) rather than onto the submit button itself.

---

## 6. Responsive Strategy

| Breakpoint | Login | Forgot Password | Confirmation |
|---|---|---|---|
| **XL (≥ 80rem)** | Card `25rem`/`2.5rem` padding, absolutely centered over full-bleed dark grid; heading `2rem` | Same card dimensions as login; `[X]` close icon in heading row | Same card shell, shorter card (no form/fields) |
| **MD (48–80rem)** | No Figma spec — derived from SM's stacked-flow layout (Decision 4), scaled to MD sizing, not from XL's absolute-positioned card | Same derivation | Same derivation |
| **SM (< 48rem)** | Card `21.875rem`/`2.5rem` padding (Decision 13 — standardized, overriding the `3rem` in `sm-login.html`'s export), normal document flow below mobile navbar (logo + search + hamburger); heading `1.75rem` | Card `21.875rem`/`2.5rem` padding, matching its own export | Same card shell as forgot-password |

One shared markup/LESS structure across all three pages per breakpoint (card + navbar shell), not
three independent stylesheets — consistent with how `error_document_template.html` handles its three
page variants with one breakpoint-driven stylesheet.

---

## 7. Accessibility Considerations

- **Fix:** `recover.html`'s field `<label for="field-login">` incorrectly targets `field-login`
  instead of the field's real id `field-recover-id` — a copy-paste artifact from `login.html`. Corrected
  as part of this rebuild regardless of the copy-wording decisions (§10).
- All current `required` attributes are preserved on every field (login/password/MFA/remember/user).
- `c-form-alert`'s `role="alert"` (already built into the component) provides an accessible live region
  for the re-targeted error message, improving on the current plain `<div>` with inline `style` toggling.
- Focus-visible states come from the v2 components' existing defaults (`search-input.html`,
  `checkbox.html`, `button.html`) — no bespoke focus styling needed.
- Keyboard navigation through the eye-toggle button, checkbox, and submit button is unchanged (native
  interactive elements throughout, no custom tab-index handling introduced).
- The `[X]` close icon and back-arrow both need an accessible label (e.g. `aria-label="Close"` /
  `aria-label="Back"`) if not already present on the current markup — confirm during implementation
  against the existing `.close.humanitarianicons-Exit-Cancel` icon's current accessible name.

---

## 8. Risks

| Risk | Detail | Mitigation |
|---|---|---|
| CSRF fix could interact with an untested code path | `signin.py`'s `login()` POST has never had a CSRF token to validate against; adding `h.csrf_input()` changes what the request body contains | Per Decision 6: add the field, then explicitly verify a live login POST still succeeds (token round-trips through CKAN's standard CSRF validation, no bespoke bypass in `signin.py` to account for) before considering this done |
| Pre-existing broken lockout-warning JS (`_showLoginError` undefined, `signin.js:24`) | Currently fails silently; server-side throttle still protects the account, only the friendly warning is broken | The v2 rewrite of this handler (§5) naturally replaces it with working code targeting the new error UI — not a separate fix, a byproduct of the required JS rewrite |
| No MD Figma spec for any of the three pages | `md-login-filled-with-error.html` is an empty stub; no MD export exists at all for forgot-password/confirmation | Resolved via Decision 4 (derive from SM) — flagged here as "derived, not sourced from an actual design," so it's revisited if a real MD Figma frame appears later |
| SM card padding inconsistency (`sm-login.html` 3rem vs `sm-forgot-password.html` 2.5rem) | Both cards should plausibly share one padding value; Figma exports disagree | Resolved via Decision 13: standardize on `2.5rem` for all three SM cards (also matches XL's padding across all three page types) |
| Remember-me duration semantics | `value="63072000"` is consumed as `timedelta(milliseconds=int(_remember))` in `signin.py:124-134` — 63,072,000 ms is ~17.5 hours, not the 730 days the value's name implies | **Flag only, do not fix** — this is authentication-logic behavior, explicitly out of this task's scope |

---

## 9. Edge Cases

| Case | Handling |
|---|---|
| Invalid email format | Not validated as an email today (username-or-email accepted as-is); preserved unchanged |
| Multiple failed login attempts | Server-side `LoginThrottle` (`ckanext-security`) unchanged; client-side pre-check warning now renders correctly (§8) instead of silently failing |
| Server errors on login | Existing generic `error_message` path, re-targeted to the password field's error slot (§3) — no new error states introduced |
| Server errors on forgot-password | Existing JSON `{success:false, error:{message}}` path, re-targeted to the field's error slot — same contract |
| Slow AJAX response (forgot-password) | Existing `widget/loading/loading.html` loading-screen widget reused as-is |
| Empty inputs | HTML `required` blocks client-side submission on all fields, exactly as today; server-side behavior unchanged |
| MFA-required accounts | `check_mfa` reveal logic unchanged, MFA field rendered via `search-input.html` (§3) |
| reCAPTCHA risk-triggered challenge | Invisible v2 behavior unchanged (§12 Decision 2) — a challenge can still appear when Google's risk engine triggers one, exactly as today |

---

## 10. Copy Wording Decisions

Per Decision 1 (§12), copy-wording conflicts between Figma and current strings were decided **per
string**, not as a blanket policy. Resolved per-string outcome (full decisions in §12, Decisions 8-12):

| Location | Current copy | Figma copy | Decision |
|---|---|---|---|
| Login field label | "Username or Email" (`login.html:50`) | "Email" (`xl-login-filled-with-error.html`) | Keep current — Decision 8 |
| Login failure message | `_("Login failed. Bad username or password.")` (`signin.py:142`) | "Incorrect email or password" | Keep current — Decision 9 |
| Footer CTA (login + forgot-password) | "Not a member? Register" (`login.html:70-72`, `recover.html:45`) | "Don't have an account? Sign up" | Adopt Figma copy — Decision 10 |
| Login "forgot password" link | "Forgot your password?" (`login.html:69`) | "Forgot password?" (note: the forgot-password *page's own heading*, "Forgot your password?", already matches Figma exactly — only this login-page link text conflicts) | Keep current — Decision 11 |
| Confirmation heading | "Please check your email" (`recoverSuccess.html`) | "Check your email" | Keep current — Decision 12 |

SM card padding (3rem vs 2.5rem, §6/§8) is resolved in Decision 13: standardize on `2.5rem` across all
three SM cards.

---

## 11. Analytics Strategy

Per Decision 7 (§12): keep all three pages **untracked**, matching today exactly. The v2 templates
continue blanking `mixpanel_init`/`google_analytics_init` (and `hotjar_init` on the forgot-password
page) — no new events are introduced by this migration. If login/reset analytics becomes a product
requirement later, the signup/onboarding flow's existing pattern
(`ckanext-hdx_users/ckanext/hdx_users/views/onboarding.py:372-427`, explicit `analytics_account_type`
context passed into templates) is the established precedent to follow — not applied here.

---

## 12. Decisions (confirmed with requester)

1. **Copy wording.** Decided per-string, not as a blanket policy — see §10 for the full list requiring
   individual sign-off.
2. **reCAPTCHA.** Keep the current invisible reCAPTCHA v2, rendered into a dedicated container rather
   than bound to the submit button. Figma's static "I'm not a robot" checkbox mock
   (`xl-forgot-password.html`, `sm-forgot-password.html`) is a non-literal placeholder and is not
   implemented as a persistent visible widget.
3. **Confirmation flow architecture.** Keep the current single-route JS swap-in-place behavior
   (`/user/reset`, AJAX success swaps the recover widget for the confirmation widget with no
   navigation). Each widget is restyled to match its own Figma export; no new route, no browser-history
   change.
4. **MD breakpoint.** Since Figma's MD login-with-error export is an empty stub and no MD export
   exists at all for forgot-password/confirmation, MD is derived from SM's stacked-flow layout (card
   in normal document flow below the mobile navbar), scaled to MD sizing — not from XL's
   absolutely-positioned card.
5. **`/user/reset/<id>` ("set new password") page.** Folded into this task despite no Figma source
   existing for it — reuses the login/forgot-password `hdx-v2-auth-card` shell verbatim (§1.4). No
   view/backend changes; only the template/CSS/JS shell was replaced.
6. **CSRF gap on the login form.** Approved for fixing as part of this rebuild (`widget/onboarding/login.html`
   has no `h.csrf_input()`, unlike the other two forms), conditioned on verifying it doesn't break the
   live login POST flow (§8) before considering the change complete.
7. **Analytics.** Keep all three pages untracked, matching today. No new tracking is introduced by this
   migration (§11).
8. **Login field label.** Keep current "Username or Email" (`login.html:50`). Figma's "Email" is not
   adopted — the field still accepts either, and the current label is more accurate.
9. **Login failure message.** Keep current `_("Login failed. Bad username or password.")`
   (`signin.py:142`). Figma's "Incorrect email or password" is not adopted.
10. **Footer CTA (login + forgot-password).** Adopt Figma's "Don't have an account? Sign up" on both
    pages, replacing the current "Not a member? Register" (`login.html:70-72`, `recover.html:45`). The
    "Sign up" link is right-aligned (`justify-content: space-between` on the footer row); "Don't have an
    account?" stays at the left edge.
11. **Login "forgot password" link.** Keep current "Forgot your password?" (`login.html:69`). Figma's
    shorter "Forgot password?" is not adopted for this link (the forgot-password page's own heading
    already matches Figma and is unaffected).
12. **Confirmation heading.** Keep current "Please check your email" (`recoverSuccess.html`). Figma's
    "Check your email" is not adopted.
13. **SM card padding.** Standardize on `2.5rem` for all three SM cards (login, forgot-password,
    confirmation), overriding `sm-login.html`'s exported `3rem`. This also matches the `2.5rem` used
    across all three XL card types.
14. **Perform-reset password validation.** Keep today's client-side behavior — required-field-only
    submit gating. Do not adopt the signup page's live password-strength/match checklist
    (`v2/form-validator.js`); that would be new user-facing behavior, not a reskin. Server-side
    validation (via `user_update`'s schema) and flash-message error surfacing are unchanged.
15. **Perform-reset confirm-password label.** Adopt "Confirm password" (was "Confirm" in the old
    widget), for consistency with the signup page's `password2` label.

---

## Constraints (carried forward)

- No Bootstrap classes anywhere in the new markup
- `--hdx-*` design tokens and BEM `c-*` component conventions throughout — Figma's raw
  `--color-*`/`--padding-*`/etc. custom properties are source material to map, not to ship verbatim
- No backend/API changes beyond the single scoped-in CSRF addition (Decision 6) — every other field
  name, route, and request/response contract stays exactly as it is today
- No new analytics — all three pages remain untracked (Decision 7)
- Must match Figma exactly except where a Decision explicitly overrides it: invisible reCAPTCHA
  (Decision 2), swap-in-place confirmation architecture (Decision 3), SM-derived MD layout (Decision 4),
  copy wording kept as current rather than Figma's on four strings (Decisions 8, 9, 11, 12), and SM
  card padding standardized at `2.5rem` rather than reproducing `sm-login.html`'s `3rem` (Decision 13)
