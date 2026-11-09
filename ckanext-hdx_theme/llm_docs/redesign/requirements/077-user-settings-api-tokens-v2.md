# 077 — User Settings: API Tokens (v2 Migration)

**Scope:** `/user/<id>/api-tokens` (core `user.api_tokens`), where users list, create and revoke
their API tokens. It moves into the 072 dashboard shell, with an HDX override of the list/create
view.

**Excluded:** the other settings pages (Notifications settings, Profile and Password). Also core's
revoke view, the actions and auth rules, the `expire_api_token` plugin and HDX's `IApiToken` hooks
(creation email, analytics, max-validity validator).

**Figma source:** `figma_exports/xl-user-settings-api.html` (XL only).

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`. `USERS` = `ckanext-hdx_users/ckanext/hdx_users`.
`CORE` = `ckan`.

---

## 1. Audit Findings

### 1.1 Route, access and data
- **Views** (`CORE/views/user.py`, blueprint `user`; HDX shadows neither):
  - `ApiTokenView` on `/user/<id>/api-tokens`, GET + POST.
    - **GET:** `api_token_list` (403 if refused), then `_extra_template_variables()` (`user_dict`,
      `is_myself`, `is_sysadmin`, `about_formatted`), plus `tokens`, `data`, `errors` and
      `error_summary` (a dict). Renders `user/api_tokens.html`. `user_show` still gets
      `include_datasets` and `include_num_followers`, which only the v1 profile card used.
    - **POST:** `api_token_create` with the form fields and `user=id`. A `ValidationError`
      re-renders through GET (200). On success it flashes HTML and redirects to the list.
  - `api_token_revoke` on `/user/<id>/api-tokens/<jti>/revoke`, POST only. Redirects back with
    no flash.
- **The new token** exists only in that flash: "API Token created: `<code>{token}</code>` {copy}
  Make sure to copy it now, you won't be able to see it again!". `{copy}` is a
  `btn btn-default btn-xs` button with `data-module="copy-into-buffer"` and only an `fa fa-copy`
  icon: no accessible name, no copied feedback.
- **Access:** own tokens only. `api_token_list` and `api_token_create` compare the user name;
  `api_token_revoke` checks the token's owner. None sets `auth_sysadmins_check`, so a sysadmin
  can list, create and revoke for any user. An unknown id gives a 500 (uncaught `NotFound`) on a
  sysadmin's GET and on every POST.
- **Validation:**
  - `expire_api_token` (enabled in `common-config-ini.txt`) adds `expires_in` and `unit`, both
    `not_empty` + `is_positive_integer`, and stores the expiry in
    `plugin_extras.expire_api_token.exp`. HDX sets `expire_api_token.default_lifetime = 30`, the
    form's default number.
  - HDX `doesnt_exceed_max_validity_period` (`THEME/helpers/custom_validator.py`, added to
    `expires_in` by `create_api_token_schema` in `THEME/plugin.py`) allows 180 days when the
    token owner is a sysadmin, 365 otherwise. The UI shows the limit only in its error, "Token
    needs to expire in maximum N days".
- **Side effects** (`postprocess_api_token` in `THEME/plugin.py`): the creation email and the
  server-side Mixpanel event `api token creation` (`APITokenCreationAnalyticsSender`). Its
  `source` is `ui` only for the path `user/{name}/api-tokens`. Revoking is not tracked; there is
  no client-side tracking.

### 1.2 Rendering (v1)
- **Template chain:** `ckanext/expire_api_token/templates/user/api_tokens.html` →
  `THEME/templates/user/api_tokens.html` → `user/read_base.html` → v1 `page.html`.
  - The expire plugin's templates come first in the search path and `ckan_extends` into HDX's.
    They fill `additional_fields`, `head_cells` and `token_cells`, which the HDX templates don't
    have, so nothing of them renders.
  - The list is `THEME/templates/user/snippets/api_token_list.html`; `api_tokens.html` is its
    only caller.
- **Shell:** breadcrumb Users / {name}, heading "User Settings", BS5 tab bar, col-3 profile card.
- **Form**, shown when `h.check_access('api_token_create', {'user': user['name']})`:
  - `<legend>` "Manage API Tokens", then `form.errors(error_summary)` ("The form contains invalid
    entries:").
  - `form.input` Name * (label not translated), `form.input` Expires in * (`type=number`, value
    `data.expires_in or h.expire_api_token_default_token_lifetime()`), `form.select` Units: Day /
    Hour / Minute = 86400 / 3600 / 60, no asterisk. Field ids equal the names (`name`,
    `expires_in`, `unit`).
  - `btn btn-primary` "Create API Token", left-aligned.
- **List:** a Bootstrap table with columns App/Token name (in `<code>`) | Last access | Expires
  at | Actions.
  - Dates use `h.render_datetime(…, date_format='%-d %B %Y, %H:%M:%S UTC')`. Last access falls
    back to "Never"; Expires at is blank for a token without `plugin_extras`.
  - Each row has a POST form with `h.csrf_input()` and a `btn btn-danger btn-sm` "Revoke".
- **Empty:** "You haven't created any API Tokens.", also on another user's page.
- **Defects:**
  - Revoke has `data-module="confirm-action"`, but HDX never loads core's `base/ckan` bundle,
    the only one that registers it. Revoke posts at once with no confirmation.
  - The Units `selected` compares int option values with the posted string, so after a
    validation error the select falls back to Day.
- **Entry points:**
  - the v2 sidebar and header user menu (`api_tokens` item in
    `h.hdx_get_user_dashboard_nav_sections()`, shown when `is_own` or `api_token_list` passes);
  - the v1 `read_base.html` tab bar and `header-global.html`;
  - the resource page and `ajax_snippets/api_info.html` token links (anonymous users go through
    `hdx_redirect_manager` `api_tokens_management` after login);
  - the creation and expiry emails.
- **Tests:** action-level only (`THEME/tests/test_actions/test_api_token_create.py`, the token
  email tests in `ckanext-hdx_users`). Nothing requests the page.

### 1.3 Reusable v2 pieces
- **Shell:** `THEME/templates/v2/user-dashboard-base.html` (072), with the menu, breadcrumb,
  `<title>`, page styles and the opt-in `user_profile_header` block. It needs `user_dict` and
  `is_myself`, which core passes.
- **Header:** `.hdx-v2-user-dashboard-header` (`pages/user-dashboard.less`).
- **Fields:** `c-form-field` + `text-field.html` (size `m`: 34px, 14px text) and `select.html`
  (native, 34px, 14px), the pairing of every other v2 form with a select.
- **Buttons:** `button.html` primary m; tertiary s (white, neutral-2 border, shadow-sm, 4/8
  padding).
- **Table:** `table.html` (`c-table`): neutral-1 border, neutral-01 header, zebra rows, 12px
  neutral-85 cells with ellipsis (200px cap), and `__scroll` with `overflow-x: auto`. Cells are
  printed as `{{ cell }}`, so Markup passes through unescaped. This is its first real call site.
- **Empty state:** `.hdx-v2-dashboard-empty`.
- **Flash:** `v2/page.html` renders flashes as `c-alert` (`alert-success` → `success`) above the
  columns, with `h.literal`.
- **Copy:** `copy-button.html` (`c-copy-button`; its JS is in `v2-components-scripts`).
- **View:** HDX `_extra_template_variables()` in `USERS/views/user.py` runs a bare `user_show` and
  404s a deleted user for non-sysadmins. The `hdx_user` blueprint already shadows core `/user/…`
  rules (plugin blueprints register first), as for `/user/<id>`.

---

## 2. Figma Analysis (XL)

- **Breadcrumb:** Home / Account and Settings / API Tokens. The export's sidebar is the pre-072
  menu; the 072 menu applies.
- **Header:** "API Tokens" (display-s) + subtitle "Create and manage API tokens for accessing HDX
  data programmatically" (body-s, neutral-85), 6px apart. A count and sort/page-size controls are
  hidden.
- **Form** (580px column, 20px gap):
  - Name * (16px text, 8/12/8/16 padding, placeholder "app/token name"), Expires in * (empty),
    Units * (34px select, 14px, "Days").
  - A hidden Comments textarea and a hidden secondary button.
  - "Create API Token" primary, right-aligned.
- **List:** "All API Tokens" (display-s), then a 582px table.
  - Header neutral-01, border neutral-1, 12px neutral-85 cells with ellipsis, zebra rows.
  - Columns: App/Token name | Last Access | Expires at | Actions.
  - "Revoke": white, neutral-2 border, shadow-sm, 4/8 padding. Pager hidden.
- **Spacing:** 24px between header, form, list title and table.
- **Not in Figma:** the token-created state, the empty state, errors, another user's page, MD
  and SM.

---

## 3. Current vs Target / Component Mapping

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, col-3 profile card | `v2/user-dashboard-base.html`, left menu at XL (D1) |
| Identity | Profile card for every user | Profile header on another user's page only (D3) |
| Breadcrumb | Users / {name} | Own: Home / Account and Settings / API Tokens. Others: Home / All Users / {name} / API Tokens |
| Header | "User Settings" + `<legend>` "Manage API Tokens" | Title "API Tokens" + own/other subtitle (D2) |
| Fields | `form.input` / `form.select` | `text-field.html` `m` / `select.html`, v1 labels (D4–D6) |
| Errors | Summary box + field messages | Field messages only (D7) |
| Submit | `btn btn-primary`, left | `c-button` primary m, right-aligned (D6) |
| List title | None | "All API Tokens" (D2) |
| Table | Bootstrap table, name in `<code>` | `c-table`, name as plain text (D4, D8) |
| Revoke | `btn btn-danger btn-sm`, broken confirm | `c-button` tertiary s, no confirm (D9) |
| Empty | "You haven't created any API Tokens." | Dashboard empty state, own/other copy (D10) |
| Token created | Core flash: `<code>` + icon-only `copy-into-buffer` button | v2 flash: success `c-alert` with the token + `c-copy-button` (D11) |
| Data | `user_show` with datasets + follower count | Bare `user_show` (D16) |
| `<title>` | API Tokens | Base: API Tokens \| {name} \| All Users |

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `subtitle` | **Reuse** the base with `nav_active='api_tokens'`, `page_label=_('API Tokens')` |
| Profile header | **Reuse** the base's `user_profile_header` block |
| Header | **Reuse** the `.hdx-v2-user-dashboard-header` markup |
| Fields | **Reuse** `c-form-field`, `text-field.html`, `select.html` |
| Units without a placeholder entry | **Extend** `select.html`: no placeholder by default (D5) |
| Buttons | **Reuse** `button.html` |
| Table | **Reuse** `table.html` as-is |
| Empty state | **Reuse** `.hdx-v2-dashboard-empty` |
| List/create view | **Override** `HDXApiTokenView` in `USERS/views/user.py` (D11, D16) |
| Token flash | **New** `user/snippets/api_token_created.html`, reusing `copy-button.html`, shown through the `v2/page.html` flash → `c-alert` |
| Layout | **New** page blocks `.hdx-v2-api-tokens` and `.hdx-v2-api-token-created` in `pages/user-dashboard.less`; **reuse** the shared `.hdx-v2-user-dashboard-actions` and `.hdx-v2-user-dashboard-secret` |

---

## 4. Template Strategy

- `THEME/templates/user/api_tokens.html` is replaced wholesale. It extends
  `v2/user-dashboard-base.html`, as 076's `user/permission.html` does (D1). No shared v1 snippet
  changes, so there is no `{% if v2 %}` and no `v2=true`.
- `THEME/templates/user/snippets/api_token_list.html` is rewritten in place: it builds the rows
  and calls `table.html` (D8).
- `THEME/templates/user/snippets/api_token_created.html` is new: the token flash content (D11).
- The HDX view keeps the URL, so every `user.api_tokens` caller (nav helper, v1 tabs, emails,
  resource page, redirect manager) reaches it unchanged.
- The expire plugin's templates still `ckan_extends` into these and stay no-ops. The page defines
  no `additional_fields`, `head_cells` or `token_cells` block and no top-level `unit_options`;
  the unit options are inline in the `select.html` call.
- **Assets:** the base's `v2-search-page-styles` + `v2-user-dashboard-page-styles`. No page
  scripts, no v1 bundles.
- `user/read_base.html` stays for the other settings pages; its "API Tokens" tab now lands on the
  v2 page.

---

## 5. Page Structure

- **Content** (`{% block primary %}`), top to bottom:
  1. Another user's page only: `{{ self.user_profile_header() }}` (D3).
  2. `.hdx-v2-user-dashboard-header`: the title "API Tokens" is an `<h1>` on your own page and an
     `<h2>` under the profile header. Subtitle "Create and manage API tokens for accessing HDX
     data programmatically", or "Create and manage {name}'s API tokens for accessing HDX data
     programmatically" (display name) on another user's page (D2).
  3. `<div class="hdx-v2-api-tokens">`: the form, then the list (D12).
- **Form**, always shown: `api_token_create`'s auth is the same rule as `api_token_list`'s, which the view
  already enforces:
  - `<form method="POST" class="hdx-v2-api-tokens__form">` + `h.csrf_input()`.
  - Each field in a `c-form-field`:
    - `text-field.html` `size='m'`, `name='name'`, `id='name'`, `label=_('Name')`,
      `required=True`, `placeholder=_('app/token name')`, `value=data.name`, `errors=errors.name`.
    - `text-field.html` `size='m'`, `type='number'`, `name='expires_in'`, `id='expires_in'`,
      `label=_('Expires in')`, `required=True`,
      `value=data.expires_in or h.expire_api_token_default_token_lifetime()`,
      `errors=errors.expires_in`.
    - `select.html` `name='unit'`, `id='unit'`, `label=_('Units')`,
      `options={'86400': _('Day'), '3600': _('Hour'), '60': _('Minute')}`,
      `selected=data.unit|string if data.unit else '86400'`, `errors=errors.unit`. No
      `required`, no placeholder (D5, D13).
  - `<div class="hdx-v2-user-dashboard-actions">` with `button.html` `style='primary'`, `size='m'`,
    `button_type='submit'`, label "Create API Token".
- **List:**
  - Title "All API Tokens", `<h2>` on your own page and `<h3>` on another user's, class
    `hdx-v2-api-tokens__title`.
  - With tokens, the list snippet; without, `.hdx-v2-dashboard-empty` (D10).
- **List snippet:**
  - `headers=[_('App/Token name'), _('Last access'), _('Expires at'), _('Actions')]`.
  - Rows are collected in a `namespace`: `token.name` as plain text, the two date cells with the
    v1 expressions, and the Revoke form captured with `{% set %}…{% endset %}`, so `table.html`
    prints it unescaped (D8).
  - Revoke form: `<form method="POST" action="{{ h.url_for('user.api_token_revoke',
    id=user_dict.name, jti=token.id) }}">` + `h.csrf_input()` + `button.html` `style='tertiary'`,
    `size='s'`, `button_type='submit'`, label "Revoke",
    `attrs={'aria-label': _('Revoke {name}').format(name=token.name)}` (D9, D14).
- **Token flash** (`api_token_created.html`, param `token`), rendered by the view into the success
  flash (D11):
  - `<span class="hdx-v2-api-token-created">` holding "API Token created:", the token in
    `.hdx-v2-user-dashboard-secret`, `copy-button.html` `style='secondary'`, `size='s'`, `value=token`, and "Make sure to copy it now, you won't be able to see it again!" as plain text.
- **Spacing (tokens):**
  - `.hdx-v2-api-tokens`: flex column, `gap: var(--hdx-space-6)`. Width 100% at SM, 80% from MD
    (D12).
  - `__form`: flex column, `gap: var(--hdx-space-5)`.
  - `__title`: `.hdx-dashboard-title()`.
  - The header's existing `margin-bottom: var(--hdx-space-6)` separates header and form.
  - `.hdx-v2-api-token-created`: flex column, `align-items: flex-start`,
    `gap: var(--hdx-space-2)`.

---

## 6. Behavior and Logic

- **View (D11, D16):** `HDXApiTokenView(ApiTokenView)` in `USERS/views/user.py`, rule
  `/<id>/api-tokens` on the `hdx_user` blueprint (endpoint `hdx_user.api_tokens`, GET + POST).
  - **GET:** core's `api_token_list` call (same context, `include_plugin_extras` included), its
    403 and a 404 for `NotFound` (D18). Then HDX `_extra_template_variables(context, {'id': id})`.
    Passes `tokens`, `data` and `errors`; not `error_summary` (D7).
  - **POST:** core's form parsing, `user=id`, `api_token_create({}, …)`, 403, 404 for `NotFound`
    (D18) and `ValidationError` re-render. On success:
    `h.flash_success(h.snippet('user/snippets/api_token_created.html', token=token), allow_html=True)`,
    then a redirect to `user.api_tokens`.
- **Unchanged:** core's revoke view (no confirm, no flash); the actions, auth rules and
  validators; the creation email; the server-side analytics (the form posts to the same path, so
  `source` is unchanged); CSRF; the field names; the default lifetime.
- **Template changes:** the shell and layout, field errors without a summary box, the unit kept
  after an error (D13), row-specific Revoke names (D14), the other-user empty copy (D10).
- **Native validation:** `required=True` adds the `required` attribute to Name and Expires in, as
  on the contact-contributor form (no `novalidate`). The browser stops empty fields before the
  server sees them.

### Risks & Edge Cases

| Case | Handling |
|---|---|
| Validation error | 200 re-render; values and unit kept (D13); the message sits under its field |
| Expiry over the limit | "Token needs to expire in maximum N days" under Expires in |
| Sysadmin on another user's page | Profile header; can list, create and revoke for that user, as today |
| Deleted user | A sysadmin sees the red "Deleted" label in the profile header. Anyone else gets the HDX helper's 404, which only matters for one's own page, and a deleted user can't log in |
| No tokens | "All API Tokens" + empty state (D10) |
| Token without `plugin_extras` | Expires at blank, as v1 |
| Long token name | Ellipsis at `c-table`'s 200px cap |
| Narrow screens | 80% at XL is about 678px at a 1280px viewport, enough for the table's ~470–620px; below that `.c-table__scroll` scrolls horizontally (D12) |
| Token flash | Dismissible success `c-alert` above the columns. It lives in the signed cookie session (`SESSION_TYPE` default `cookie`), about 1KB, as core's flash did (D11) |

---

## 7. Responsive Behavior & Accessibility

- **XL (≥ 80rem):** sticky 25% menu on the left (072); `.hdx-v2-api-tokens` at 80%.
- **MD:** no menu; navigation is through the header user menu. The header stacks (072 rules);
  80%.
- **SM:** 100%.
- **Accessibility:**
  - One `<h1>`: the page title on your own page, the profile header's title on another user's.
    The list title is one level below the page title.
  - Labels are tied to their inputs (`for`/`id`); the asterisks are `aria-hidden` and the inputs
    carry `required`.
  - Field errors are visible text under each field.
  - Each Revoke button is named after its token (D14).
  - `:focus-visible` rings come from the components.
  - The flash's `c-copy-button` has a label and announces "Copied to clipboard" through its
    `aria-live` status.

---

## 8. Decisions Taken

| # | Decision |
|---|---|
| D1 Template | Replace `user/api_tokens.html` wholesale; it extends `v2/user-dashboard-base.html`. |
| D2 New copy | Figma's subtitle on your own page, "Create and manage {name}'s API tokens for accessing HDX data programmatically" on another user's; list title "All API Tokens". |
| D3 Other user | The base's profile header above the header; the page and list titles step down a level. |
| D4 v1 copy | v1 wins over Figma: "Last access", Day / Hour / Minute, no Units asterisk, Expires in prefilled with the default lifetime. Figma wins for the Name placeholder "app/token name" and the token name as plain text, without `<code>`. |
| D5 Units select | No placeholder entry. `select.html`'s `placeholder` defaults to `''`, and the disabled option renders only when a placeholder is passed. Every live caller passes one. |
| D6 Layout | Submit right-aligned; text fields size `m`, so all three fields are 34px like the Units select. |
| D7 Errors | Per field only, through the components' `errors`; no summary alert. |
| D8 Table | `table.html` as-is; the Revoke cell is Markup from a `{% set %}` block; the rows are built in the rewritten `api_token_list.html`. |
| D9 Revoke | `c-button` tertiary s in a POST form; core's view; no confirm and no flash, as today. |
| D10 Empty | "All API Tokens" stays; `.hdx-v2-dashboard-empty` with "You haven't created any API Tokens." or "{name} hasn't created any API Tokens." (display name). |
| D11 Token flash | HDX POST override flashes `api_token_created.html`: v1 text, the token as plain wrapping text, `c-copy-button` with its default label `_('Copy')`. No Bootstrap classes, no `<code>`, no `copy-into-buffer`. |
| D12 Widths | `.hdx-v2-api-tokens` (form and list) 100% SM, 80% MD and XL. |
| D13 Unit kept | String option values; `selected` is the posted unit or `'86400'`. |
| D14 Revoke name | `aria-label` "Revoke {token name}". |
| D15 Not added | No max-lifetime hint; the limit stays in the error only. |
| D16 Data | GET uses HDX `_extra_template_variables()` (bare `user_show`): no `include_datasets`, `include_num_followers`, `user_obj` or `about_formatted`. |
| D17 Tests | Extend `THEME/tests/test_actions/test_api_token_create.py` (email already mocked), authenticating with an API token header as 076's view tests do: GET 200 for the owner and for a sysadmin on another user, 403 for another user; valid POST → 302 to the same URL, then the token and `data-copy-value` on the next GET and no `copy-into-buffer`; POST over the limit → 200 with the "maximum 365 days" message and the posted unit still selected; a sysadmin's GET and POST on an unknown id → 404. |
| D18 Unknown id | `HDXApiTokenView` turns `NotFound` from `api_token_list` and `api_token_create` into `abort(404, _('User not found'))`, the HDX helper's message. Another user's GET stays 403, since auth runs first. |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/api_tokens.html` | Rewritten: dashboard base, profile header on another user's page, header, form, list (D1–D7, D10, D12, D13) |
| `THEME/templates/user/snippets/api_token_list.html` | Rewritten: rows + `table.html` (D4, D8, D9, D14) |
| `THEME/templates/user/snippets/api_token_created.html` | New: token flash content (D11) |
| `USERS/views/user.py` | `HDXApiTokenView` + `/<id>/api-tokens` rule on `hdx_user` (D11, D16, D18) |
| `THEME/templates/v2/components/select.html` | `placeholder` default `''`; the option only when set; header comment (D5) |
| `THEME/templates/v2/components/copy-button.html` | `label` default `_('Copy')` (D11) |
| `THEME/templates/v2/components/page-header.html`, `THEME/templates/package/hdx_read.html` | Drop the now-default `label=_('Copy')` |
| `THEME/hdx-styles/src/common/less/v2/pages/user-dashboard.less` | `.hdx-v2-api-tokens` and `.hdx-v2-api-token-created` blocks (§5) |
| `THEME/tests/test_actions/test_api_token_create.py` | View tests (D17) |
| `THEME/templates/v2/user-dashboard-base.html` | Header comment: the profile-header note no longer lists pages |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Migrated-pages row |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Key-pages entry |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/070-v2-full-audit.md` | D1 decision row: `table.html` has a real caller (API Tokens) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 077 status |
