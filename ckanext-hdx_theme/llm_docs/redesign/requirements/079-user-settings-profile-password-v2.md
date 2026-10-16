# 079 — User Settings: Profile and Password (v2 Migration)

**Scope:** `/user/edit/<id>` (HDX `hdx_user.edit`), where a user edits their profile and password, and
where a sysadmin manages two-step verification and deletes accounts. It moves into the 072 dashboard
shell. The 2FA popup becomes a `c-drawer`, and so does the delete confirmation.

**Excluded:**
- The view, actions, schemas, validators and auth rules.
- The 2FA endpoints and the `ckanext-security` extension.
- Core's delete view.
- The `_before_request` 2FA redirect.
- The other settings pages.

**Figma source:** `figma_exports/xl-user-settings-profile.html` (XL only).

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`. `USERS` = `ckanext-hdx_users/ckanext/hdx_users`.

---

## 1. Audit Findings

### 1.1 Route, access and data
- **View:** `HDXEditView(EditView)` in `USERS/views/user_edit_view.py`.
  - The `hdx_user` blueprint routes `/user/edit` and `/user/edit/<id>` to it.
  - It shadows core `user.edit`, so `url_for('user.edit')` reaches it too.
- **GET:**
  - Calls `user_show`.
  - Uses core's `_extra_template_variables`, which passes `user_dict`, `is_myself`, `is_sysadmin` (the
    *viewer's* flag) and `about_formatted`. There is no deleted-user 404.
  - Also passes `data`, `errors` and `error_summary` (a dict).
  - `show_email_notifications` comes from `ckan.activity_streams_email_notifications`. That setting is
    commented out in `common-config-ini.txt` and set to true in the test ini.
  - `ckanext.security.utils._setup_totp_template_variables` puts `totp_challenger_uri` and `totp_secret` on
    `g` when the viewed user has 2FA.
  - Renders `user/edit_user_form.html`.
- **POST:**
  - Runs only when the form has `save`, sent as the submit button's name.
  - The hidden `name` field is required by the schema.
  - **Password check:** when new passwords are given, or the email differs from the requester's own email,
    `old_password` is authenticated against the **requester** (`g.user`). A wrong password re-renders with
    `errors.oldpassword` ("Password entered was incorrect"). A sysadmin editing someone else therefore
    always enters their own password.
  - **Update:** `user_update` uses `onboarding_user_edit_form_schema`:
    - fullname: allowed characters;
    - email: lowercased, unique among active users;
    - password: 10+ characters from 3 of 4 character sets, and both passwords must match;
    - about: no links ("looks like spam").
  - **Errors:** a `ValidationError` re-renders with field errors. Any other exception re-renders with
    `error_summary` `{'unexpected error': …}` and empty `errors`.
  - **Success:** flash "Profile updated", redirect back to `hdx_user.edit`; `set_repoze_user` on a rename.
  - An empty `activity_streams_email_notifications` defaults to False.
- **Access (`user_update`):** yourself, or a sysadmin for anyone.

  | Case | Result |
  |---|---|
  | Anonymous on `/user/edit` | 400 |
  | Anonymous on `/user/edit/<id>` | 403 |
  | Another user, not a sysadmin | 403 |
  | Sysadmin, unknown id | 404 |
  | Sysadmin, deleted user | Renders |

### 1.2 Rendering (v1)
- **Template chain:** `THEME/templates/user/edit_user_form.html` → `user/read_base.html` → v1 `page.html`.
  - It uses `extends`, not `ckan_extends`, so the security, activity and core `edit_user_form.html` are not
    in the chain.
- **Shell:** breadcrumb Users / {name}, heading "User Settings", the BS5 tab bar, the col-3 profile card,
  and a `col-8` form with `row`/`col-4` label grids.
- **Form** (`#user-edit-form`, `h.csrf_input()`, `form.errors(error_summary)` summary box):
  - **"Profile" legend:**
    - hidden `name`;
    - Full name * (`field-fullname`);
    - Email * (`field-email`, `type=email`);
    - About (`form.textarea`, `field-about`);
    - when `show_email_notifications`: the checkbox "Subscribe to notification emails" with info text.
      It is checked from `g.userobj`, the viewer.
  - **"Password" legend:**
    - `old_password`, labelled "Sysadmin Password" if `is_sysadmin` else "Old Password". It is always empty.
    - `password1` "New Password" and `password2` "Confirm New Password". Both are refilled from `data`
      after an error.
    - `old_password` and `password1` share the id `field-password`.
    - All three have `autocomplete=off`.
  - "* Required field", then `btn btn-primary` "Update Profile" (`name="save"`).
  - **"Two-step verification" fieldset** (only when `is_sysadmin`): "Manage two-step verification" opens
    the popup (§1.3).
  - **"Delete account" fieldset** (only when `check_access('user_delete')`, i.e. sysadmins):
    - If `h.hdx_get_org_member_info(data.id).maint_orgs_pkgs` is set: a Bootstrap modal with "User
      cannot be removed. Please change maintainer for the following datasets: ", the org/dataset list
      and a disabled Confirm.
    - Otherwise: a "Delete" link to core `user.delete` with the v1 `hdx_confirm-action` module ("You are
      deleting user" / "Are you sure you want to delete this user?" / "Delete").
- **Assets:** `hdx_theme/two-step-styles`, `security/mfa_configure` (QRious + `qrcode_renderer.js`;
  preloads core `base/main`) and `hdx_theme/two-step-scripts`.

### 1.3 Two-step verification today
- **Markup and JS:**
  - Popup `THEME/templates/widget/security/two-step-verification.html`, which extends the onboarding
    `widget/popup`. It is opened by `showOnboardingWidget('#tsvPopup')`.
  - JS: `THEME/fanstatic/widget/security/popup-security.js` (jQuery).
  - It acts on the viewed user (`userName=data.name`).
- **Copy:** three intro paragraphs; a 4-step list (Google Authenticator link); a manual-entry sentence;
  "Enter the code from your app to test"; the help line "If your one-time password does not work: …".
- **States:**
  - **Off:** "Turn on two-step verification".
  - **On:** "Turn off two-step verification", "Generate new two-step verification code", the stored QR +
    secret, the test form.
  - **Setup** (after Turn on / Generate):
    - the popup can't be closed and `onbeforeunload` warns;
    - "Cancel" (tooltip "Turn off the two-step verification.");
    - "Save", disabled (tooltip "Please test the two step code before saving.") until a test passes.
- **Endpoints** (`HDXTwoStep`, `hdx_user` blueprint):

  | Endpoint | Method | Purpose |
  |---|---|---|
  | `/user/configure_mfa/<name>/new` | GET | Returns `totp_challenger_uri` + `totp_secret` (JSON) |
  | `/user/configure_mfa/<name>/delete` | GET | Turns 2FA off |
  | `/user/configure_mfa/<name>` | POST | `mfa` + CSRF header (`hdxUtil.net.getCsrfTokenAsObject()`); returns `{success}` |

  - Messages:
    - Test result: "Code is valid, two-step verification is configured correctly!" / "Code is invalid,
      please check code and try again!" / "Error while attempting test!".
    - `/new` and `/delete` failures: `alert('Error!')`.
  - The endpoints also set flashes, which show on the next page load.
- **Flow:** Save reloads the page without the query string; Cancel turns 2FA off, then reloads; Turn off
  swaps the popup to the off state in place.
- **Forced setup:** `THEME/plugin.py` `_before_request` sends sysadmins without 2FA to
  `user.edit?show_totp=True`. The popup auto-opens on `show_totp`.
- **Login** (`user/signin.html` + `v2/pages/login.js`) asks for the code when the account has 2FA.

### 1.4 Analytics, side effects, entry points, tests
- **Analytics:** only the Mixpanel page view. Its "page title" is the `subtitle` block, "Profile and
  Password" today. No events; no emails on email or password change.
- **Entry points:**
  - the nav helper item `profile_and_password` (sidebar + header user menu);
  - v1 `read_base.html` tabs and `header-global.html`;
  - the splash "update your profile" flash;
  - the 2FA redirect.
- **Tests:**
  - `USERS/tests/test_emails/test_email_access.py::TestEditUserEmail` (all five tests assert the v1 input
    HTML; the four email-error tests also assert the v1 summary `<li data-field-label="Email">`);
  - `test_mfa.py`, `test_delete_user_maintainer.py`, `test_password_reset.py`.

### 1.5 Reusable v2 pieces
- **Shell:** `THEME/templates/v2/user-dashboard-base.html` (072).
  - It provides the menu, breadcrumb, `<title>` and the opt-in `user_profile_header` block, which renders
    `c-page-header` with avatar, name, member since, bio and Deleted label, then `.hdx-v2-user-dashboard-divider`.
  - It needs `user_dict` and `is_myself`, which the view passes.
- **Header:** `.hdx-v2-user-dashboard-header` (`pages/user-dashboard.less`).
- **`c-page-header` CTA:** `cta_label` / `cta_href` / `cta_icon_src`.
  - It renders a primary `c-button` m at the end of the description block, at every width.
  - The Signals hero is its only caller ("Sign up", bell icon). The params are not documented in the
    header comment.
- **Fields:**
  - `c-form-field` + `text-field.html`: size `m` is 34px with 14px text; `multiline` gives a fixed 100px
    textarea; `type='password'` adds the eye toggle.
  - `checkbox.html`.
- **Buttons:** `button.html` (`attrs` pass through to `<button>`) and `text-button.html` (primary m: 14px,
  blue, 16px icon, 4px gap).
- **Section row:** `.hdx-page-section-header()` (flex, `space-between`, 12px gap), from the
  dataset/resource sections.
- **Titles:** `.hdx-dashboard-title()` (24px bold).
- **Drawer:**
  - `drawer.html` + `drawer.js`: `hdxV2Drawer(id).open()/close()`, `drawer:close` event, focus trap;
    100/80/50% wide.
  - `.c-drawer-form` (`__text`, `__description`, `__buttons`).
  - Drawers with a plain POST form already exist: org member remove and dataset delete.
- **Feedback:** `alert.html` (`c-alert`), `copy-button.html` (reads `data-copy-value` on click),
  `hdxV2.showAlert` (text only) / `hdxV2.setDisabled` (`fanstatic/v2/utils.js`).
- **Maintainer list:** the org members drawer renders the same org/dataset list as
  `.hdx-v2-org-members__pkg-list` (`pages/org.less`, not loaded on user pages).

---

## 2. Figma Analysis (XL)

- **Breadcrumb:** Home / Account and Settings / Profile and Password. The export's sidebar is the pre-072
  menu; the 072 menu applies.
- **Profile header:** shown on the user's own page. It is the public-profile header (avatar, name, bio,
  "Member since …") plus a **"View public profile"** text-button after the text: blue, 14px medium,
  underlined, with a 16px icon on the left. The icon's glyph isn't exported. A divider follows.
- **Header:** "Profile and Password" (24px bold) + "Update your account details, password, and login
  preferences" (14px, neutral-85). The count and sort/page-size controls are hidden.
- **Profile fields** (580px column, 20px gap): Full name *, Email *, About * (150px textarea). Fields
  are 37px with 16px text (size L).
- **Password:** "Password" (24px bold), "Sysadmin/Old password *", "New password *", "Confirm new
  password *", then "Update profile" (primary, right-aligned).
- **Two-step verification:** divider, then a row with "Two-step verification" (24px bold) and a
  tertiary "Manage two-step verification" on the right.
- **Delete account:** divider, then a row with "Delete account" and a tertiary "Delete account" button.
- **Spacing:** 24px from header to fields; 48px between sections; 24px above the first divider and 48px
  around the second.
- **Hidden layers:** a Comments textarea and secondary buttons.
- **Not in Figma:** errors, the drawers, another user's page, MD and SM.

---

## 3. Current vs Target / Component Mapping

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, col-3 card | `v2/user-dashboard-base.html`, left menu at XL (D1) |
| Identity | Profile card | Profile header on own and other pages, with "View public profile" (D2, D3) |
| Breadcrumb | Users / {name} | Own: Home / Account and Settings / Profile and Password. Others: Home / Users / {name} / Profile and Password |
| Header | "User Settings" + "Profile" legend | "Profile and Password" + own/other subtitle (D2) |
| Fields | `form.input` / `form.textarea` in a Bootstrap grid | `text-field.html` `m`, sentence-case labels (D6, D7) |
| Errors | Summary box + field messages | Field messages; `c-alert` only for a non-field error (D8) |
| Submit | `btn btn-primary` "Update Profile" | `c-button` primary m "Update profile", right-aligned (D6, D7) |
| 2FA | v1 popup, jQuery, stored secret shown | `c-drawer`, v2 page script, QR/secret only during setup (D12–D15) |
| Delete | `hdx_confirm-action` / Bootstrap modal | `c-drawer` with a POST form (D16) |
| `<title>` | Profile and Password | Base: Profile and Password \| {name} \| Users (D19) |

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `subtitle` | **Reuse** the base with `user_nav_active='profile_and_password'`, `page_label=_('Profile and Password')` |
| Profile header | **Reuse** the base's `user_profile_header` block, with a child flag for the link (D5) |
| Public profile link | **Extend** `page-header.html`: `cta_style`, `cta_attrs` (D4) |
| Header | **Reuse** the `.hdx-v2-user-dashboard-header` markup |
| Fields, checkbox, buttons, text-button | **Reuse** `c-form-field`, `text-field.html`, `checkbox.html`, `button.html`, `text-button.html` |
| Section rows | **Reuse** `.hdx-page-section-header()`; **extend** it with `flex-wrap: wrap` (D11) |
| Drawers | **Reuse** `drawer.html` + `.c-drawer-form` |
| Maintainer list | **Extend** `.c-drawer-form` with `__list`, moved from the org page; **new** shared `v2/maintainer-datasets-list.html` (D17) |
| Secret copy, result messages | **Reuse** `copy-button.html`, `alert.html`, `hdxV2.setDisabled`; **extend** `hdxV2.showAlert` with a variant (D24) |
| 2FA JS | **New** `fanstatic/v2/pages/user-profile.js` + vendored QRious, bundle `v2-user-profile-page-scripts` (D15) |
| Layout | **New** page blocks `.hdx-v2-user-profile` and `.hdx-v2-two-step` (2FA drawer content) in `pages/user-dashboard.less`; **new** shared `.hdx-v2-user-dashboard-actions` and `.hdx-v2-user-dashboard-secret` (D25) |

---

## 4. Template Strategy

- `THEME/templates/user/edit_user_form.html` is replaced wholesale and extends
  `v2/user-dashboard-base.html` (D1). No shared v1 snippet changes, so there is no `{% if v2 %}` and no `v2=true`.
- The view is untouched. Every caller of `hdx_user.edit` / `user.edit` (nav helper, v1 tabs, header,
  splash flash, 2FA redirect) reaches the v2 page unchanged.
- `user/read_base.html` stays; the v1 settings tabs still link here.
- **Assets:**
  - the base's `v2-search-page-styles` + `v2-user-dashboard-page-styles`;
  - `v2-user-profile-page-scripts`, only when the 2FA section renders (D15).
- v1 `two-step-*` and `security/mfa_configure` are no longer loaded; the v1 widget files stay as they are.
- The delete drawer needs no page JS (inline `hdxV2Drawer` onclick, as on the org members page).

---

## 5. Page Structure

- **Top** (`{% block primary %}`):
  1. `{% set public_profile_link = true %}` (top level), then `{{ self.user_profile_header() }}` for every
     viewer (D2, D5).
  2. `.hdx-v2-user-dashboard-header`:
     - title "Profile and Password" as `<h2>`;
     - subtitle "Update your account details, password, and login preferences", or "Update {name}'s
       account details, password, and login preferences" (display name) on another user's page (D2).
  3. `<div class="hdx-v2-user-profile">`, the settings stack.
- **Profile header link** (base block, when `public_profile_link` is set):
  - `cta_style='text'`, `cta_label=_('View public profile')`,
    `cta_href=h.url_for('hdx_user.read', id=user_dict.name)`, `cta_icon_src='v2/icons/link-external.svg'`;
  - `cta_attrs={'target': '_blank', 'rel': 'noopener noreferrer'}` (D3, D4).
- **Stack:**
  1. `<form method="POST" class="hdx-v2-user-profile__form">` + `h.csrf_input()`.
     - **Non-field error:** when `error_summary and not errors`, `alert.html` (error) with the summary
       values (D8).
     - **`__group` (profile fields):**
       - hidden `name`;
       - Full name: `text-field.html` `size='m'`, `name='fullname'`, `id='field-fullname'`,
         `required=True`, `autocomplete='name'`;
       - Email: `type='email'`, `id='field-email'`, `required=True`, `autocomplete='email'`;
       - About: `multiline=True`, `id='field-about'`;
       - when `show_email_notifications`: `checkbox.html` (`activity_streams_email_notifications`,
         value `True`, checked from `data`, the viewed user) + the v1 info text in a `<p>`.
       - Values come from `data`; each field gets `errors=errors.<field>`.
     - **`__section` (password):**
       - `__section-header` with `<h3>` "Password";
       - Old password: `type='password'`, `name='old_password'`, `id='field-old-password'`, label
         "Sysadmin password" if `is_sysadmin` else "Old password", `autocomplete='current-password'`,
         `errors=errors.oldpassword`, always empty;
       - New password: `name='password1'`, `id='field-password'`, `autocomplete='new-password'`,
         value `data.password1`;
       - Confirm new password: `name='password2'`, `id='field-password-confirm'`,
         `autocomplete='new-password'`, value `data.password2` (D9);
       - `.hdx-v2-user-dashboard-actions`: `button.html` `style='primary'`, `size='m'`, `button_type='submit'`,
         label "Update profile", `attrs={'name': 'save'}`.
  2. When `is_sysadmin`: `<hr class="c-divider">`, then the 2FA section.
     - `__section-header` with `<h3>` "Two-step verification" + `button.html` `style='tertiary'`,
       `size='m'`, label "Manage two-step verification", which opens `two-step-drawer`.
  3. When `h.check_access('user_delete', {'id': user_dict.id})`: `<hr class="c-divider">`, then the delete
     section.
     - `__section-header` with `<h3>` "Delete account" + a tertiary m "Delete account", which opens
       `delete-user-drawer`.
- **Drawers** (after the stack, outside the form):
  - **`two-step-drawer`** (title "Two-step verification", only when `is_sysadmin`) (D13).
    - **Intro:** the v1 intro paragraphs and the 4-step list, verbatim (the Google Authenticator link
      opens in a new tab).
    - **Off state** (`g.totp_challenger_uri` empty): "Turn on two-step verification", primary m.
    - **On state:**
      - "Two-step verification is on.";
      - "Turn off two-step verification", tertiary m;
      - "Generate new two-step verification code", text-button primary m.
      - The stored QR and secret are not rendered; `totp_challenger_uri` is only an on/off flag.
    - **Setup block** (`hidden` until Turn on / Generate):
      - a `<canvas>` with `role="img"` and an accessible name, for the QR;
      - the v1 manual-entry sentence;
      - the secret in `.hdx-v2-user-dashboard-secret` + `copy-button.html` (`data-copy-value` set by JS).
    - **Test block** (on state and setup; `hidden` in the off state):
      - a `<form>` with `text-field.html` `size='m'`, `name='mfa'`, `id='field-mfa'`, label "Enter
        the code from your app to test", `autocomplete='one-time-code'`, and a "Test" secondary m;
      - a hidden `c-alert` for the result, its variant set by JS (D24);
      - the v1 help line.
    - **Setup actions** (`hidden` until Turn on / Generate):
      - the two v1 tooltip strings, verbatim, as visible `c-drawer-form__text` lines: "Please test the
        two step code before saving." and "Turn off the two-step verification.";
      - `c-drawer-form__buttons`: "Cancel" tertiary + "Save" primary, disabled until a test passes.
    - A hidden error `c-alert` for `/new` and `/delete` failures.
  - **`delete-user-drawer`** (title "Delete account", only with `user_delete` access) (D16).
    - `<form class="c-drawer-form" method="post" action="{{ h.url_for('user.delete', id=user_dict.id) }}">` +
      `h.csrf_input()`.
    - **Maintainers** (`h.hdx_get_org_member_info(user_dict.id)`): "User cannot be removed. Please change maintainer for the following datasets: ",
      then `v2/maintainer-datasets-list.html` (dataset links open in a new tab), and Confirm
      disabled.
    - **Otherwise:** "Are you sure you want to delete this user?".
    - Buttons: Cancel tertiary (`data-drawer-close`) + Confirm primary submit.
- **Spacing (tokens):**
  - `.hdx-v2-user-profile` and `__form` (one rule): flex column, `gap: var(--hdx-space-12)`. The root is
    100% wide at SM, 80% from MD (D18).
  - `__group`: flex column, `gap: var(--hdx-space-5)`.
  - `__section`: flex column, `gap: var(--hdx-space-6)`, and a fields group with `gap: var(--hdx-space-5)`.
  - `__section-header`: `.hdx-page-section-header()`; `__section-title`: `.hdx-dashboard-title()`.
  - `.hdx-v2-user-dashboard-actions`: flex, `justify-content: flex-end`. `.hdx-v2-user-dashboard-secret`:
    `.hdx-body-s-semibold()`, `word-break: break-all` (D25).
  - `<hr class="c-divider">` items are stack children (48px on both sides) (D10).
  - The header's existing `margin-bottom: var(--hdx-space-6)` separates the header and the stack.

---

## 6. Behavior and Logic

- **Profile form:** the same field names, `save` and hidden `name` as v1, so the view, schema, password
  check, flashes and PRG all behave as before (D21). `required=True` adds the native `required` attribute
  to Full name and Email only.
- **2FA (`fanstatic/v2/pages/user-profile.js`, vanilla JS)** (D12, D14):
  - **Trigger:** "Manage two-step verification" opens `two-step-drawer`. `?show_totp` in the URL opens it
    on load.
  - **Turn on / Generate:**
    - GET `/user/configure_mfa/<name>/new`;
    - on success: fill the secret and the copy button's `data-copy-value`, draw the QR with QRious
      (size 250), show the setup block, test block and setup actions, and hide the state block;
    - set `onbeforeunload` (v1 message).
  - **Test:**
    - POST `/user/configure_mfa/<name>` with `mfa` and `hdxUtil.net.getCsrfTokenAsObject()`;
    - show the v1 result message in the `c-alert` (`hdxV2.showAlert`, success or error variant);
    - on success, enable Save (`hdxV2.setDisabled`) and clear `onbeforeunload`.
  - **Save:** `location.assign` to the URL without the query string.
  - **Cancel:** GET `/user/configure_mfa/<name>/delete`, then reload.
  - **Turn off:** GET `…/delete`, then reload.
  - **Closing mid-setup:** `drawer:close` counts as Cancel while the setup is untested, and as Save after a
    test passed.
  - **Failures:** a `/new` or `/delete` failure shows "Error!" in the drawer's error `c-alert`; closing
    mid-setup reloads even when `/delete` fails.
  - Endpoints, methods, payloads and flashes are exactly v1's.
- **Delete:** core `user.delete` POST, unchanged:
  - `hdx_user_delete` refuses maintainers;
  - deleting yourself logs you out;
  - deleting another user redirects to the user list.

### Risks & Edge Cases

| Case | Handling |
|---|---|
| Validation error | 200 re-render; messages under their fields; new/confirm keep their values (D9) |
| Wrong old/sysadmin password | "Password entered was incorrect" under the old-password field |
| Unexpected error | Error `c-alert` with "An unexpected error occurred. Please try again or contact us." |
| Sysadmin on another user | Profile header + link to their public page; title `<h2>` under it; "Sysadmin password"; 2FA and delete act on that user |
| Own page, link | Opens `/user/<me>` (My Datasets) in a new tab |
| Deleted user (sysadmin) | Red "Deleted" label in the profile header; the form still saves |
| Non-sysadmin | No 2FA or delete sections; no page script |
| Sysadmin forced to set up 2FA | Redirect with `?show_totp` opens the drawer |
| Drawer closed during setup | Before a passed test: same as Cancel (2FA turned off, reload). After: same as Save (reload) |
| Error on the hidden `name` field | Not shown; only a tampered request can cause it (D8) |
| Dataset maintainer delete | Drawer lists their datasets; Confirm disabled |
| `show_email_notifications` off (prod) | No checkbox; saves send False, as v1 |
| Narrow screens | Section rows wrap the button under the title; the stack is 100% at SM |

---

## 7. Responsive Behavior & Accessibility

- **XL (≥ 80rem):** sticky 25% menu (072); the stack is 80% wide; section rows put the title left and the
  button right.
- **MD:** no menu (header user menu); 80% wide; the `c-page-header` and dashboard header use their own
  responsive rules.
- **SM:** 100% wide; a section row's button wraps under its title when they don't fit on one line.
- **Accessibility:**
  - One `<h1>` (the profile header's name); the page title is `<h2>`; section titles are `<h3>`.
  - Labels are tied to their inputs (`for`/`id`; the duplicate v1 id is fixed). Asterisks are
    `aria-hidden` and only Full name and Email carry `required`.
  - Autocomplete purposes are set for name, email and the passwords (WCAG 1.3.5).
  - The drawers use `drawer.js` (focus trap, Escape, focus return). Their result messages use `c-alert`
    roles.
  - The QR canvas has `role="img"` and a label. The secret has a labelled copy button.
  - Field errors are visible text under each field.
  - The new-tab link relies on its icon as the cue, as other v2 external links do.

---

## 8. Decisions Taken

| # | Decision |
|---|---|
| D1 Template | Replace `user/edit_user_form.html` wholesale; it extends `v2/user-dashboard-base.html`. The view is untouched. |
| D2 Profile header | Shown on your own page and on another user's. Profile header `<h1>`, page title `<h2>`, section titles `<h3>`. Figma subtitle on your own page; "Update {name}'s account details, password, and login preferences" on another user's. |
| D3 Public link | "View public profile" → `hdx_user.read` for the viewed user (own page: My Datasets). New tab, `link-external.svg` on the left. |
| D4 page-header CTA | New `cta_style` (`'button'` default, `'text'` → `text-button.html` primary m) and `cta_attrs` (dict, like `header_actions[].attrs`). The header comment documents `cta_label`, `cta_href`, `cta_icon_src`, `cta_style`, `cta_attrs`. Signals is unchanged. |
| D5 Block hook | Child flag `public_profile_link`; the base `user_profile_header` passes the CTA only when it is set. |
| D6 Copy | Figma sentence case: "Old password"/"Sysadmin password" (by viewer), "New password", "Confirm new password", "Update profile", "Delete account". Asterisks only on Full name and Email. No visible "Profile" heading. |
| D7 Fields | `text-field.html` size `m`; About at the component's 100px; distinct ids; autocomplete `name`/`email`/`current-password`/`new-password`; submit `attrs={'name': 'save'}`; notifications checkbox kept behind its config, checked from the viewed user (`data`; v1 used the viewer). |
| D8 Errors | Per field. An error `c-alert` only when `error_summary` has no field errors. Server-side checks only (no `form-validator.js`), as v1. |
| D9 Refill | As v1: new/confirm refilled after an error; old password always empty. |
| D10 Spacing | 48px between sections and around dividers at all widths; 24px title→fields; 20px between fields. |
| D11 Section rows | `.hdx-page-section-header()` + `flex-wrap: wrap` in the mixin; titles `.hdx-dashboard-title()`. |
| D12 2FA access | Sysadmin viewers only, as v1. The JS calls the v1 endpoints for `user_dict.name` with v1 methods and payloads. |
| D13 2FA drawer | `two-step-drawer`, title "Two-step verification", v1 copy. On-state: "Two-step verification is on." + Turn off + Generate + the test block, no stored QR/secret. Setup: QR, secret + `c-copy-button`, the test block, v1 tooltip strings as visible text, Cancel + Save. Test block: code field + Test, result `c-alert`, v1 help line. |
| D14 2FA behaviour | v1 flow (Save reload, Cancel off + reload, `onbeforeunload`, `?show_totp`); Turn off also reloads (v1 swapped in place); closing mid-setup = Cancel before a passed test, Save after; failures show "Error!" in a `c-alert`. |
| D15 2FA assets | `fanstatic/v2/pages/user-profile.js`; QRious 4.0.2 vendored to `fanstatic/v2/qrious/qrious.min.js`; bundle `v2-user-profile-page-scripts`, loaded with the 2FA section. |
| D16 Delete | `delete-user-drawer` with a POST form to core `user.delete`; v1 texts; maintainers get the list and a disabled Confirm; Cancel + Confirm. The action, access check and maintainer lookup use `user_dict.id` (`data.id` is the URL id after a failed save). |
| D17 Drawer list | `.hdx-v2-org-members__pkg-list` moves to `drawer.less` as `c-drawer-form__list`; its markup moves to `v2/maintainer-datasets-list.html`, which the org members drawer uses too. |
| D18 Width | `.hdx-v2-user-profile` 100% at SM, 80% from MD (own rule). |
| D19 Analytics | No new events. The Mixpanel page title follows the base subtitle, "Profile and Password \| {name} \| Users", as on 072–078. |
| D20 Tests | Update the five `TestEditUserEmail` tests for the v2 markup (email errors under the Email field). Add to `TestEditUserEmail`: own GET (title, link with `target="_blank"`); 2FA section/drawer only for sysadmin viewers; delete drawer only for sysadmins, with Confirm disabled for maintainers; wrong old password → error under its field. |
| D21 Unchanged | View, actions, schema, validators, auth, 2FA endpoints and flashes, core delete view, `_before_request` redirect, field names, CSRF. |
| D22 New copy | The other-user subtitle; "Two-step verification is on."; the 2FA drawer title "Two-step verification" (v1: "How to turn on two-step verification"); the delete drawer title "Delete account" with the org drawer's "Confirm". |
| D23 Hidden layers | Figma's Comments textarea, count, sort/page-size and secondary buttons are not built. |
| D24 showAlert variant | `hdxV2.showAlert(alertEl, text, variant)`: the optional `variant` swaps the `c-alert--*` class and the role as `alert.html` sets them. Existing callers are unchanged. |
| D25 Shared dashboard classes | `.hdx-v2-user-dashboard-actions` (right-aligned submit row) and `.hdx-v2-user-dashboard-secret` (semibold secret text that breaks anywhere) in `pages/user-dashboard.less`. They replace this page's copies and 077's `__actions` / `__token`, so `api_tokens.html`, `api_token_created.html` and its test switch to them. |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/edit_user_form.html` | Rewritten: dashboard base, profile header + link, header, form, 2FA and delete sections, drawers (D1–D16) |
| `THEME/templates/v2/user-dashboard-base.html` | `user_profile_header` passes the CTA when `public_profile_link` is set; header comment documents the flag (D5) |
| `THEME/templates/v2/components/page-header.html` | `cta_style`, `cta_attrs`; one CTA snippet call; header comment (D4) |
| `THEME/templates/user/api_tokens.html` | Submit row in `.hdx-v2-user-dashboard-actions` (D25) |
| `THEME/templates/user/snippets/api_token_created.html` | Token in `.hdx-v2-user-dashboard-secret` (D25) |
| `THEME/tests/test_actions/test_api_token_create.py` | Token regex follows the class (D25) |
| `THEME/templates/v2/components.html` | Drawer demo "Confirm — with list" (D17) |
| `THEME/templates/v2/maintainer-datasets-list.html` | New: shared maintainer org/dataset list (D17) |
| `THEME/templates/organization/members.html` | Maintainer list uses the shared snippet (D17) |
| `THEME/hdx-styles/src/common/less/v2/components/drawer.less` | `.c-drawer-form__list` (D17); generic `.c-drawer-form` section comment |
| `THEME/hdx-styles/src/common/less/v2/pages/org.less` | `__pkg-list` removed (D17) |
| `THEME/hdx-styles/src/common/less/v2/mixins.less` | `flex-wrap: wrap` in `.hdx-page-section-header()` (D11) |
| `THEME/hdx-styles/src/common/less/v2/pages/user-dashboard.less` | `.hdx-v2-user-profile` and `.hdx-v2-two-step` blocks (§5); shared `-actions` / `-secret`, 077's `__actions` / `__token` removed (D25) |
| `THEME/fanstatic/v2/pages/user-profile.js` | New: 2FA drawer logic (D13, D14) |
| `THEME/fanstatic/v2/qrious/qrious.min.js` | New: vendored QRious 4.0.2 (D15) |
| `THEME/fanstatic/v2/utils.js` | `hdxV2.showAlert` optional `variant` (D24) |
| `THEME/fanstatic/webassets.yml` | `v2-user-profile-page-scripts` (D15) |
| `USERS/tests/test_emails/test_email_access.py` | Updated + new render tests (D20) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Migrated-pages row; Page header bullet (D4) |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Key-pages entry; base contract `public_profile_link` (D5) |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | `showAlert` signature (D24); page-section header wraps (D11) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 079 status |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/037-dataset-page-header-v2.md` | §4.2: `cta_style`, `cta_attrs` (D4) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/054-signals-landing-page.md` | §7: `cta_style`, `cta_attrs` and the current CTA markup (D4) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/070-v2-full-audit.md` | Excluded: user dashboard/settings migrated in 072–079 |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/072-user-dashboard-my-organisations-v2.md` | v1-sibling notes dropped |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/073-user-dashboard-my-datasets-v2.md` | D24: no `read_base.html` child left; D27: `public_profile_link` CTA (D5) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/074-user-dashboard-hdx-connect-requests-v2.md` | `showAlert` signature (D24) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/077-user-settings-api-tokens-v2.md` | Shared dashboard classes (D25) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/078-user-settings-notifications-v2.md` | §4: `read_base.html` line |
