# 093 — Password Reset Confirmation on the Login Page

**Scope:** after a successful password reset, the user lands on the login page instead of the homepage. The login
page then renders flash messages inside the auth card, below the "Log in" title, so the existing success flash
appears there. This needs one config key (D2), a template change on `user/signin.html` and one LESS element.

**Excluded:**
- the core `PerformResetView.post()` and the HDX `HDXPerformResetView` (no view change);
- reset-key verification and expiry, and password validation;
- the perform-reset page itself (064);
- flash rendering on every other page, including forgot-password and perform-reset;
- the `c-alert` and `c-info-box` components.

**Figma sources:** `xl-login-password-reset.html` (no MD or SM export)

---

## Context

The reset email links to the perform-reset page ("set new password", 064). A valid submit flashes "Your password has
been reset." and redirects to `/`, so the confirmation shows in the homepage flash band and the user still has to
find the login page. The Figma export shows the user on the login card with the confirmation inside it.

---

## 1. Existing Implementation Audit

### Routes / views (unchanged — reference only)

| Screen | Route | View | Template |
|---|---|---|---|
| Perform reset | GET/POST `/user/reset/<id>?key=…` | `HDXPerformResetView` (`ckanext-hdx_users/.../views/user.py`): own `get()` and `_get_form_password()`; `post()` inherited from core `PerformResetView` (`ckan/views/user.py`) | `user/perform_reset.html` (v2, 064) |
| Login | GET/POST `/sign-in`, `/login`, `/user/login` | `hdx_signin.login()` (`ckanext-hdx_users/.../views/signin.py`) | `user/signin.html` (v2, 064) |
| Homepage | `/` | `hdx_splash.index` | `home/index.html` |

### Success path (core `post()`)

1. `_prepare` checks the posted key against `user.reset_key`. The HDX `user_update` auth enforces the expiry embedded
   in the key.
2. `user_update` sets the password. The HDX schema applies ckanext-security's password validator, and the security
   action wrapper resets the login throttle.
3. A `pending` user (org invitation) is set to `active`.
4. `mailer.create_reset_key` rotates the key, so the link stops working.
5. The `perform_password_reset` signal fires (no HDX listener).
6. `h.flash_success(_('Your password has been reset.'))`, category `alert-success`.
7. `h.redirect_to(config.get('ckan.user_reset_landing_page'))`. The default is `home.index` and HDX sets no value, so
   the response is a 302 to `/`. The user is not logged in.

Core `RequestResetView.post()` reads `ckan.user_reset_landing_page` too. HDX replaces that view with
`HDXRequestResetView` (JSON responses), which never reads it. The key therefore only drives the perform-reset success
redirect.

### Failure paths (unchanged)

- **GET, invalid or expired link:** HDX `get()` flashes 'The link you accessed is either invalid or has expired…'
  (`alert-error`) and redirects to `hdx_user.request_reset`.
- **POST, key mismatch:** core flashes 'Invalid reset key. Please try again.' and aborts 403. The error page blanks its
  flash block, so the flash shows on the next page that renders one.
- **POST, other errors** (empty password, mismatch, schema error, expired key, user not found): core flashes the error
  and re-renders `user/perform_reset.html`. The flash shows in the band above the card.

### Login page message surfaces

| Surface | Source | Rendering | Position |
|---|---|---|---|
| Flash messages | `h.get_flashed_messages()` in `v2/page.html` `flash_inner` | `c-alert`, variant from the category map (`alert-success` → success, `alert-danger` / `alert-error` → error, `alert-info` → info, `alert-warning` → warning, anything else → info), `extra_classes='hdx-v2-flash'`, dismissible | `.flash-messages` band above the dark `.hdx-v2-auth-page`; `signin.html` does not override `flash` |
| `info_message` | `?info_message_type=` → `UI_CONSTANTS['SIGNIN']` | `c-alert` info, dismissible | inside the card, below `__header` |
| Login failure | `error_message` (`signin.py`) | `text-field.html` `errors` on the password field | under the password field |

- **Other flashes on login:** the reset is not the only flow that ends here. The dashboard redirects flash 'Not
  authorized to see this page' (error) before `redirect_to('user.login')`. Any flash left by a page that did not
  render its flash block also shows here.
- **Spacing:** `.hdx-v2-flash` adds `margin: var(--hdx-space-4) 0` (`layout.less`).
- **Precedents for moving flashes:** `home/index.html` calls `{{ self.flash() }}` inside its own `content`, and
  `error_document_template.html` empties the block.

### Analytics

`user/signin.html` blanks `mixpanel_init` and `google_analytics_init`. There is no reset or login tracking (064 §1.5).

### Tests

`TestPasswordReset` (`ckanext-hdx_users/.../tests/test_password_reset.py`) covers reset keys, `user_update` with a
key and the expired-link GET. Nothing covers the POST redirect.

---

## 2. Figma Analysis

### Layout (`xl-login-password-reset.html`)

```
.xl-login-with-new-password (dark full-bleed, logo-only navbar)
└── .frame-parent (card 25rem, 2.5rem padding, gap 3rem)
    ├── .your-password-has-been-reset-wrapper   ← confirmation box, first child
    │   "Your password has been reset.<br>You can now log in with your new password."
    ├── "Log in"
    ├── Email · Password (eye-off) · "Forgot password?" · ☐ Remember me · [Log in]
    └── "Don't have an account?"  "Sign up"
```

The rest of the card is the 064 login card (`xl-login-filled-with-error.html` without the error). The copy
differences there ('Email', 'Forgot password?') were decided in 064 D8 and D11 and stay as they are.

### Token map

| Figma | Value | Token |
|---|---|---|
| Box background `--color-aliceblue` | `#e8effb` | `--hdx-primary-05` |
| Box radius | 6px | `--hdx-radius-md` (4px, nearest) |
| Box padding | 1.5rem | `--hdx-space-6` |
| Box text | 16px / 130%, `#000` | `.hdx-body-m()`, `--hdx-neutral-95` |
| Box → title | 3rem (card gap) | card `gap`, `--hdx-space-12` at XL |
| Border, icon, close | none | — |

The box is `c-info-box` (081) without its icon. It is not adopted (D4).

### Gaps

- There is no MD or SM export. The card's responsive rules (064 §6) apply.
- The export is a static mock: it has no dismiss affordance and shows no error or info variant.

---

## 3. Current vs Target

| Aspect | Current | Target | Basis |
|---|---|---|---|
| Landing page after a successful reset | `/` (homepage) | login (`/sign-in`) | D2 |
| Confirmation copy | 'Your password has been reset.' | unchanged | D1 |
| Confirmation look | green `c-alert` success | unchanged | D4 |
| Flash position on the login page | band above the auth page | inside the card, below the title | D3, D5 |
| Flash variants on login | category map | unchanged | D4, D6 |
| `info_message` | `c-alert` info below the title | unchanged, in the shared message area after the flashes | D5 |
| Spacing | band margin `--hdx-space-4` | card gap around the area; `--hdx-space-4` between messages | §6, D9 |
| Flash band on forgot-password and perform-reset | band | unchanged | D3 |
| Perform-reset view, validation, key handling, CSRF | — | unchanged | §7 |

---

## 4. Component Mapping

No new or changed component.

| Element | Component |
|---|---|
| Flash messages in the card | `v2/page.html` `flash_inner`, rendered with `self.flash_inner()` → `v2/components/alert.html` (D4) |
| `info_message` | `v2/components/alert.html` `variant='info'`, call unchanged |
| Message area | page element `.hdx-v2-auth-card__messages` (`pages/auth.less`) |

**Assets:** `v2-auth-page-styles` only (existing). Dismiss uses the existing `alert.js` from the v2 component scripts.

---

## 5. Flow & States

```
Reset email ─▶ GET /user/reset/<id>?key=… ─▶ Update Password ─┬─ valid ─▶ flash success ─▶ 302 /sign-in ─▶ alert below "Log in"
                                                              └─ invalid ─▶ re-render perform-reset (band, unchanged)
```

| State | Behaviour |
|---|---|
| Reset success | The login card shows the success alert below the title; the form is unchanged |
| Org invitee sets a first password | Same as reset success, with the core copy (D1); the `pending` user is now `active` (D8) |
| Reset completed while logged in | Login redirects to `/` with 'You are already logged in.'; both flashes show in the homepage band (D7) |
| Login reached with an error flash (e.g. a dashboard redirect) | Error `c-alert` inside the card below the title |
| `info_message_type` set, no flash | Info alert below the title, as today |
| Flash and `info_message` | Flashes first, then `info_message`, `--hdx-space-4` apart |
| No flash and no `info_message` | No message area is rendered |
| Failed login POST | Re-render; a pending flash shows in the card; the password-field error is unchanged |
| Alert dismissed | `alert.js` removes it |
| An ini without the key | The redirect falls back to `/` and the band, as today |

---

## 6. Responsive Behaviour

- **Width:** the message area spans the card's content width at every size (card 100% SM, 80% MD, 400px XL, from
  064).
- **Around the area:** the card gap, `--hdx-space-8` at SM/MD and `--hdx-space-12` at XL (Figma's 3rem).
- **Between messages:** `--hdx-space-4`, as in the flash band (D9). The `.hdx-v2-flash` margin is reset to 0 inside the area.
- There is no breakpoint-specific rule.

---

## 7. Functionality & Analytics Preservation

| Item | Status |
|---|---|
| Perform-reset view, key verification and expiry, password validation, pending → active, key rotation | Unchanged |
| Success flash text and category | Unchanged |
| CSRF on both forms | Unchanged |
| Login POST, lockout and MFA checks, remember me, `came_from` | Unchanged |
| Flash consumption | Still once per login render, so no flash carries over |
| Analytics | None on either page; unchanged |
| Backend | One ini key (D2) |

---

## 8. Accessibility

- `c-alert` keeps `role="status"` for success and info and `role="alert"` for error and warning. The dismiss button
  keeps `aria-label` 'Dismiss'.
- **Reading order:** the "Log in" heading, then the messages, then the form.
- The area is rendered on the server at page load; no live-region update is involved.

---

## 9. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| An environment's ini lacks the key | The redirect falls back to `/` and today's band. `common-config-ini.txt` is shared by every environment (the prod template loads it with `use = config:`) |
| Leftover flashes from other pages appear in the login card | Same messages as today in a new position (D3) |
| A logged-in user completes a reset | Homepage with both flashes (§5); accepted (D7) |
| Perform-reset schema errors flash a Python dict repr | Pre-existing core behaviour on the perform-reset page; out of scope |
| Login handles flashes differently from forgot-password and perform-reset | Accepted (D3) |
| Differences from Figma: copy, colour, border, close button, position | D1, D4, D5 |

---

## 10. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | Copy | Core 'Your password has been reset.' · Figma's two sentences (needs an HDX copy of core `post()`) | Core copy; no `post()` override |
| D2 | Redirect | `ckan.user_reset_landing_page` · thin `post()` wrapper | `ckan.user_reset_landing_page = hdx_signin.login` in `common-config-ini.txt` and `docker/hdx-test-core.ini.tpl`; no Python change |
| D3 | Flashes in the card | Success only · all | Every flash on the login page renders in the card, and the page band is not rendered on login. The other auth pages keep the band |
| D4 | Component | Extend `c-info-box` (`show_icon`) · `c-info-box` as-is · `c-alert` | The existing flash rendering as-is: `v2/page.html` `flash_inner` (`c-alert`, current category map), green success, dismissible. `c-info-box` unchanged |
| D5 | Position | Above the title (Figma) · below the title | Below the title, in one message area with `info_message`; flashes first |
| D6 | Info and unmapped categories | `c-alert` info · `c-info-box` | Unchanged (`c-alert` info), following D4 |
| D7 | Reset completed while logged in | Accept both flashes on the homepage · skip 'You are already logged in.' when a flash is queued (Python in `hdx_signin.login`) | Accept; no Python change (D2) |
| D8 | Org invitees (`hdx_user_invite` link to perform-reset) | Accept the core copy on the login card · invitee-specific copy (needs a `post()` override) | Accept; core copy (D1) |
| D9 | Gap between stacked messages | `--hdx-space-4` (flash band) · `--hdx-space-3` | `--hdx-space-4` |

---

## 11. Files Affected

| File | Change |
|---|---|
| `common-config-ini.txt` | `ckan.user_reset_landing_page = hdx_signin.login` in a new `## User Settings` section (D2) |
| `docker/hdx-test-core.ini.tpl` | Same key (D2). CI and `run-plugin-tests.sh` generate the gitignored `hdx-test-core.ini` from it |
| `templates/user/signin.html` | Empty `flash` block. A `__messages` area below `__header` holds `self.flash_inner()` and the existing `info_message` alert. Header comment gets the Figma source and this doc |
| `hdx-styles/src/common/less/v2/pages/auth.less` | `__messages` element; Figma source in the header comment |
| `ckanext-hdx_users/.../tests/test_password_reset.py` | Extend `TestPasswordReset`: a valid POST redirects to `hdx_signin.login`, and the login page then shows 'Your password has been reset.' inside `.hdx-v2-auth-card__messages` |
| `llm_docs/redesign/PROGRESS.md` | Login row: flashes render inside the card |

Template and LESS paths are relative to `ckanext-hdx_theme/ckanext/hdx_theme/`. There is no view, component, JS or
`webassets.yml` change.

---

## 12. Verification Checklist

- [ ] Full flow: request a reset, open the link and set a valid password. You land on `/sign-in` with the green 'Your
      password has been reset.' below "Log in", and Dismiss removes it.
- [ ] The used link no longer works.
- [ ] An org-invite link sets the first password and lands on `/sign-in` with the success alert in the card.
- [ ] A failed perform-reset POST still re-renders the page with the error flash in its band.
- [ ] Logged out, `/dashboard` shows 'Not authorized to see this page' in the login card below the title, with no band
      above the page.
- [ ] `?info_message_type=add-data` shows the info alert below the title as before. With a flash as well, the flashes
      come first.
- [ ] With no flash and no `info_message` there is no empty message area and the card spacing is unchanged.
- [ ] Login, MFA reveal, the lockout pre-check and remember me still work.
- [ ] The new and existing `test_password_reset.py` tests pass.
- [ ] Visual check at SM, MD and XL.
