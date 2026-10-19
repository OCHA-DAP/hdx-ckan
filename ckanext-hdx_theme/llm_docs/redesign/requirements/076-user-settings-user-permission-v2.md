# 076 — User Settings: User Permission (v2 Migration)

**Scope:** `/user/permission/<id>` (HDX `hdx_user_permission.read`), the sysadmin-only form that
grants HDX admin permissions to a user. It moves into the 072 dashboard shell.

**Excluded:** the other settings pages (API Tokens, Notifications settings, Profile and
Password). Also the `Permissions` model, the auth rules and the permission labels.

**Figma source:** none. The layout in §2 is a proposal built from existing v2 form patterns, and
the user approved it.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`. `USERS` = `ckanext-hdx_users/ckanext/hdx_users`.

---

## 1. Audit Findings

### 1.1 Route, access and data
- **View:** `read()` in `USERS/views/permission.py` (blueprint `hdx_user_permission`, prefix
  `/user/permission`, GET + POST).
  - **Access:** the `manage_permissions` auth (`USERS/actions/auth.py`) always returns False, so only
    sysadmins pass, through the sysadmin bypass. Every other caller, anonymous included, gets
    **404** ("page not found"), not 403.
  - **Order:** `Permissions(id)` runs before `user_show`. `find_user_id` raises `ObjectNotFound`,
    which is not an `HTTPException`, so **an unknown id returns 500** on GET and POST.
  - **Template vars:** `_extra_template_variables()` returns `user_dict`, `is_myself`,
    `is_sysadmin` and `about_formatted`. The view adds `permissions`, a list of `{key, label, checked}`.
  - **Data only the v1 card used:** `user_show` is called with `include_datasets` (a
    package_search of up to 50 datasets) and `include_num_followers`. The context also sets
    `with_related`, which nothing reads, and the view builds `about_formatted`.
- **Model:** `Permissions` in `USERS/helpers/permissions.py`.
  - It has 11 permissions in `ALL_PERMISSIONS_LABELS_DICT` insertion order: Carousel and Dataviz
    Gallery, COD, Dataseries, P-Codes, Events/Crisis, View Request Data Dashboard, Quick Links,
    Basic Scheduled Tasks, QA, In HAPI Flag, SDD report.
  - They are stored space-joined in the user extra `hdx_permissions`, via `user_extra_create` or
    `user_extra_update`.

### 1.2 Save (POST)
- The form posts each checked key as `name=key, value=key`, plus `update_permissions=update`.
- When `update_permissions == 'update'`, the view keeps the keys that are in `ALL_PERMISSIONS`
  and calls `set_permissions({'user': g.userobj.id}, keys)`. Any other key is ignored. Unchecking
  every box saves `''`.
- **The redirect is a no-op:** `redirect(...)` is called without `return`, so the POST falls
  through and renders the page as a 200. A browser refresh offers to resubmit.
- There is no flash message and no error handling.

### 1.3 Rendering (v1)
- **Template chain:** `THEME/templates/user/permission.html` → `user/read_base.html` → v1
  `page.html`.
  - Breadcrumb Users / {name}, heading "User Settings", hidden `<h2>` "User Permission".
  - BS5 tab bar, and a col-3 profile card (avatar, name, Deleted label, bio, followers, datasets).
- **Form:** `form.checkbox(key, id='field_' + key, label, value=key, checked)` per permission, then
  a `btn btn-primary` "Update Permissions" button (`name="update_permissions" value="update"`) and
  `h.csrf_input()`.
- **JS:** the form has `data-module="basic-form"`. Its disable-on-submit targets
  `button[name="save"]`, which this form doesn't have, so it never fires. The only behaviour that
  works is the "unsaved modifications" warning when leaving the page.
- **Analytics:** nothing page-specific. The Mixpanel page view uses the `subtitle` block as `pageTitle`.
- **Entry points:**
  - the v2 sidebar and header user menu (`user_permission` item in
    `h.hdx_get_user_dashboard_nav_sections()`, sysadmin only);
  - v1 `header-global.html`;
  - the `read_base.html` tab bar of the v1 settings pages.
- **Tests:** `USERS/tests/test_permissions_controller.py`.
  - `test_manage_permissions` asserts a 200 after POST (the HDX test client doesn't follow
    redirects) and counts `' checked '` in the body.
  - `test_permission_page_load` asserts every key and label in the body.
  - The anonymous and non-sysadmin checks in both never fail: their `assert False` is inside
    `try … except Exception`.

### 1.4 Reusable v2 pieces
- **Shell:** `THEME/templates/v2/user-dashboard-base.html` (072).
  - It provides the menu, the breadcrumb, `<title>`, page styles and the opt-in
    `user_profile_header` block.
  - It needs `user_dict` and `is_myself`, which the view already passes.
- **Header:** `.hdx-v2-user-dashboard-header` (`pages/user-dashboard.less`), with title and subtitle.
- **Checkbox:** `c-checkbox` (`v2/components/checkbox.html`), with `label` and `error_slot`.
  - The shared `.v2-checkbox-row()` mixin (`mixins.less`) lays out checkbox and label; auth,
    signup and request-access use it.
- **Button:** `c-button` (`v2/components/button.html`), with `button_type` and `attrs` for
  name/value.
- **Feedback:** `v2/page.html` renders flashes as `c-alert` (`alert-success` → `success`).
- **Utility:** `.sr-only` (`foundation.less`).

---

## 2. Design Proposal (no Figma)

- **Content** (`{% block primary %}`), top to bottom:
  1. Another user's page only: the profile header, `{{ self.user_profile_header() }}` (D5).
  2. `.hdx-v2-user-dashboard-header`. The title "User Permission" is an `<h1>` on your own page and
     an `<h2>` under the profile header. Subtitle (D2): "Choose which HDX admin features you can
     use" on your own page, "Choose which HDX admin features {name} can use" on another user's
     (display name).
  3. The form.
- **Form markup:**
  - `<form method="POST" class="hdx-v2-user-permission">` + `h.csrf_input()`.
  - `<fieldset class="hdx-v2-user-permission__fieldset">` with a `<legend class="sr-only">`
    "Permissions" (D13).
  - One `<div class="hdx-v2-user-permission__item">` per permission, in the view's order (D11).
    Each holds `c-checkbox` with `id=p.key, name=p.key, value=p.key, checked=p.checked,
    label=p.label, error_slot=false`.
  - Then `c-button` `style='primary'`, `size='m'`, `button_type='submit'`, label "Update
    Permissions", `attrs={'name': 'update_permissions', 'value': 'update'}` (D4).
- **Spacing (tokens):**
  - `.hdx-v2-user-permission`: flex column, `align-items: flex-start`, `gap: var(--hdx-space-6)`
    (list → button).
  - `__fieldset`: `.v2-checkbox-group()` (flex column, `gap: var(--hdx-space-4)`), as signup's
    checkbox group. Bootstrap's reboot
    (`v2-page-styles`) already zeroes its border, margin, padding and min-width.
  - `__item`: `.v2-checkbox-row()`.
  - The header's existing `margin-bottom: var(--hdx-space-6)` separates header and form.
- **Look:** no card. One column with a left-aligned button, the same at every breakpoint (D3).
  The button is always enabled. Hover and focus come from the components' pseudo-classes. No JS (D8).

---

## 3. Current vs Target / Component Mapping

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, col-3 profile card | `v2/user-dashboard-base.html`, left menu at XL (D1) |
| Identity | Profile card for every user | Profile header on another user's page only (D5) |
| Breadcrumb | Users / {name} | Own: Home / Account and Settings / User Permission. Others: Home / Users / {name} / User Permission |
| Header | "User Settings" + hidden `<h2>` | Visible title + subtitle (D2) |
| Checkboxes | `form.checkbox` macro | `c-checkbox` rows in a fieldset (D13) |
| Submit | `btn btn-primary` | `c-button` primary M (D4) |
| JS | `basic-form` (leave warning only) | None (D8) |
| After save | 200 render, no message | 302 to the same page + success flash (D6, D7) |
| Unknown id | 500 | 404 (D9) |
| `<title>` | User Permission | Base: User Permission \| {name} \| Users |

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `subtitle` | **Reuse** the base with `user_nav_active='user_permission'`, `page_label=_('User Permission')` |
| Profile header | **Reuse** the base's `user_profile_header` block |
| Header | **Reuse** the `.hdx-v2-user-dashboard-header` markup |
| Checkbox rows | **Reuse** `c-checkbox` + `.v2-checkbox-row()` |
| Submit | **Reuse** `c-button` |
| Success message | **Reuse** the `v2/page.html` flash → `c-alert` |
| Form layout | **New** page block `.hdx-v2-user-permission` in `pages/user-dashboard.less` |

---

## 4. Dashboard Integration

- **Template:** `THEME/templates/user/permission.html` is replaced wholesale (D1). It extends
  `v2/user-dashboard-base.html`, as 073's `user/read.html` and 075's `user/activity_stream.html`
  do. No shared snippet changes, so there is no `{% if v2 %}` and no `v2=true`.
- **Menu:** the item is `user_permission`, active with `aria-current="page"`. The base builds the
  menu for `user_dict`, so another user's page shows that user's menu.
- **Breadcrumb and `<title>`:** from the base. On your own page, the "Account and Settings" crumb
  links to the section's first item, which for a sysadmin is this page.
- **Assets:** the base's `v2-search-page-styles` + `v2-user-dashboard-page-styles`. No scripts,
  no v1 bundles.
- `user/read_base.html` stays for the v1 settings pages; its "User Permission" tab now lands on
  the v2 page.

---

## 5. Behavior and Logic

- **Unchanged:** the route, the 404 for non-sysadmins, the key filtering, the storage, the
  `update_permissions=update` contract and CSRF.
- **View changes:**
  - **Lookup first (D9):** `_extra_template_variables()` runs after the access check (so
    non-sysadmins keep a uniform 404) but before `Permissions(id)` and the save, so an unknown id
    aborts with 404 and nothing is written.
  - **Save (D6, D7):** after `set_permissions`, call `h.flash_success(_('Permissions updated.'))`,
    then `return redirect(h.url_for('hdx_user_permission.read', id=id))`.
  - **Dead data (D10):** `user_show` gets only `{id}`. `with_related`, `user_obj`,
    `about_formatted` and the `is_sysadmin` template variable are removed.
- **Analytics:** no new tracking. Only `pageTitle` changes.

### Risks & Edge Cases

| Case | Handling |
|---|---|
| Deleted user | Sysadmin access as before; red "Deleted" label in the profile header; saving works |
| Sysadmin's own page | No profile header, `<h1>` title, own menu |
| Target is a sysadmin | Saves as before |
| All boxes unchecked | Saves `''`, as before |
| Crafted extra POST key | Ignored by the `ALL_PERMISSIONS` filter |
| POST without `update_permissions=update` | No save; the page renders, as before |
| Unknown id | 404 (D9) |
| Long label | Wraps in the label column of `.v2-checkbox-row()` |

---

## 6. Responsive Behavior & Accessibility

- **XL (≥ 80rem):** sticky 25% menu on the left (072).
- **MD/SM:** no menu; navigation is through the header user menu. The header stacks (072 rules).
  The form is the same single column, full width.
- **Accessibility:**
  - One `<h1>`: the page title on your own page, the profile header's title on another user's.
  - The fieldset and its `sr-only` legend group the checkboxes.
  - Each native checkbox has a `<label for>`, and Space toggles it.
  - The `:focus-visible` rings come from `c-checkbox` and `c-button`.
  - The submit is a native `<button type="submit">`. The success message is a server-rendered
    `c-alert` at the top of the page.

---

## 7. Decisions Taken

| # | Decision |
|---|---|
| D1 Template | Replace `user/permission.html` wholesale; it extends `v2/user-dashboard-base.html`. |
| D2 Copy | Title "User Permission" (singular, the same as the menu label). Subtitle "Choose which HDX admin features you can use" / "…{name} can use". |
| D3 Layout | One column, flat list, button left-aligned below it; the same at every breakpoint; no card. |
| D4 Button | `c-button` primary M, "Update Permissions", `name="update_permissions" value="update"` kept. |
| D5 Other user | The base's profile header above the header; the title is an `<h2>` there. |
| D6 Feedback | `h.flash_success(_('Permissions updated.'))` after the save. |
| D7 Redirect | `return redirect(...)` (Post/Redirect/Get). |
| D8 JS | None. `basic-form` and its leave warning are dropped. |
| D9 Unknown id | User lookup after the access check, before `Permissions(id)` and the save; an unknown id gives 404. |
| D10 Dead data | Drop `include_datasets`, `include_num_followers`, `with_related`, `user_obj` (core's `user_show` ignores it when `id` is set), `about_formatted` and the `is_sysadmin` template variable (no template reads it). |
| D11 Order | The view's order (`ALL_PERMISSIONS_LABELS_DICT`), no grouping. |
| D12 Tests | `test_manage_permissions`: the sysadmin POST asserts 302 with `Location` on the same page, and the checked count looks for `checked="checked"`. The non-sysadmin checks and the anonymous GET assert 404. No anonymous POST check: CSRF rejects it before the view. New unknown-id test: GET and POST give 404 (no save assert, as there is no user to write to). No flash assert. |
| D13 Markup | `<fieldset>` + `sr-only` `<legend>`; checkbox `id=p.key`; `error_slot=false`. |

---

## 8. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/permission.html` | Rewritten: dashboard base, profile header on another user's page, header, form (D1–D5, D13) |
| `USERS/views/permission.py` | Lookup order, flash, `return redirect`, dead data removed (D6, D7, D9, D10) |
| `THEME/hdx-styles/src/common/less/v2/pages/user-dashboard.less` | `.hdx-v2-user-permission` block (§2) |
| `THEME/hdx-styles/src/common/less/v2/mixins.less` | `.v2-checkbox-group()`, next to `.v2-checkbox-row()` |
| `THEME/hdx-styles/src/common/less/v2/pages/signup.less` | `__checkbox-group` uses `.v2-checkbox-group()` |
| `THEME/templates/v2/user-dashboard-base.html` | Header comment: User Permission also outputs the profile header |
| `USERS/tests/test_permissions_controller.py` | D12 |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Migrated-pages row; the My Organisations row's "settings pages still v1" |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Key-pages entry; the migrated-pages sentence |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/073-user-dashboard-my-datasets-v2.md` | D24: drop `permission.html` from the `read_base.html` children |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 076 status |
