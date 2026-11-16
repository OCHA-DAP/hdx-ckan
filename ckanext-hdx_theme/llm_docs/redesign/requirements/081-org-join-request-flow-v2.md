# 081 — Find / Join / Create Organisation Flow v2

**Scope:** migrate the six join-org and create-org screens from `page_light.html` / `bem.blocks` /
Bootstrap to v2. This includes the shared-component extensions they need (`select.html`,
`text-field.html`, `c-step-pager`) and one new component (`c-info-box`).
**Excluded:** views, schema, actions, email templates, analytics senders and `ckanext-ytp-request`. No
routes, validators, permissions or email triggers change.
**Figma sources:** `xl-request-join.html`, `xl-request-new-org.html`, `xl-request-new-confirm.html`,
`sm-join-org.html`, `sm-create-org.html`, `sm-confirm-org.html`

---

## Context

A logged-in user who wants to share data must belong to an organisation. The join flow
(`/org/join/*`) lets them request membership of an existing organisation. The create flow
(`/org/request/*`) lets them ask the HDX team to create a new one. Both flows are listed under
PROGRESS.md "Pages in holding state".

They are reached from v2 pages:

| Entry point | Where | Target |
|---|---|---|
| Header "Add data" (user without `package_create` rights) | `h.hdx_check_add_data()` (`ckanext-hdx_package` helpers) → `v2/header.html` | `hdx_org_join.find_organisation` |
| Org page "Request membership" | `v2/org-hero.html` `header_actions` | `hdx_org_join.find_organisation?selected=<org id>` |
| Dashboard My Organisations | `user/read_organizations.html` | `hdx_org_join.org_join` |
| First login after the "Share data" signup choice | `_compute_url` (`ckanext-hdx_users/logic/first_login.py`) | `hdx_org_join.org_join` |
| "create a new one" links | Find + Confirm screens | `hdx_org_request.new` |

Figma covers Find, New org and Confirm. The Reason step and both "Request submitted" pages have no
export. They are composed from the same shell (D18, D19).

---

## 1. Existing Implementation Audit

### Routes / views (unchanged — reference only)

Blueprints `hdx_org_join` (`/org/join`) and `hdx_org_request` (`/org/request`) are in
`ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization_join.py` and `organization_request.py`.

| Screen | Route | View | Template | v1 stepper |
|---|---|---|---|---|
| Find | GET `/org/join/find/` (`?selected=`) | `find_organisation` | `org/join/find_organisation.html` | 3 steps, step 1 |
| Confirm | POST `/org/join/confirm/` | `confirm_organisation` | `org/join/confirm_organisation.html` | step 1 |
| Reason | POST `/org/join/reason-request/` | `reason_request` | `org/join/reason_request.html` | step 2 |
| Join completed | POST `/org/join/completed/` | `completed_request` | `org/join/completed.html` | step 3 |
| New org | GET/POST `/org/request/new/` | `OrgNewRequestView` | `org/request/org_new_request.html` | 2 steps, step 1 |
| Create completed | GET `/org/request/completed/` | `completed_request` | `org/request/completed_request.html` | step 2 |

- **Index routes:** `/org/join/` (`org_join`) redirects to Find; `/org/request/` (`org_request`) redirects to New.
- **Auth:** `_prepare_and_check_access()` → `check_access('hdx_send_new_org_request')`
  (`ckanext-hdx_users/actions/auth.py`). Logged-in users only; others get `abort(403)`. No sysadmin gate.
- **Org list:** `OrgJoinLogic._fetch_org_list_metadata()` (`controller_logic/organization_join_logic.py`)
  returns `cached_organization_list` minus closed orgs and orgs with `request_membership == 'false'`.
  The result is `{id: display_name}`, sorted by display name.
- **Join chain:** each step POSTs the hidden `org_id` to the next. Confirm and Reason call
  `organization_show` and render with `org_dict=None` when the lookup fails; a missing `org_id`
  redirects to Find. Confirm also calls `set_custom_rect_logo_url(org_dict)`. Completed redirects to
  Find when `message` is blank, otherwise calls `member_request_create` with `role='member'`.
- **Create:** POST validates `request_new_organization_schema`. With errors it re-renders with `data`
  + `errors` (no `error_summary`). On success it calls `hdx_send_new_org_request` and redirects to
  completed. Completed returns 404 unless the referrer contains `/org/request/new`.
- No flash messages, no session state. Every form has `h.csrf_input()`.

### Create-org schema (`controller_logic/organization_request_logic.py`)

| Field | Validators | Widget (v1) |
|---|---|---|
| `name` | `not_empty`, `unicode_safe` | input |
| `description` | `not_empty`, `unicode_safe` | textarea |
| `website` | `ignore_missing`, `unicode_safe` | input |
| `role` | `not_empty`, `unicode_safe` | input |
| `data_type` | `not_empty`, `unicode_safe` | textarea + 3-item guideline list |
| `data_already_available` | `not_empty`, `unicode_safe` | select2 `{'no': 'No', 'yes': 'Yes'}` |
| `data_already_available_link` | `ignore_missing`, `unicode_safe` | input, always visible |

There is no URL validation and no maximum length. The join form has one field: `message` (Reason,
required, character counter).

### Side effects

- **Join:** `member_request_create` (`ckanext-ytp-request/.../logic.py`) creates a pending `Member`.
  - It emails org admins (`email/content/join_organization_request.html`) and the requester
    (`join_organization_request_confirmation_to_user.html`), but only when the org has admins.
  - The message is emailed, not stored.
  - Sysadmins, existing members and duplicate requests raise `ValidationError`. The view catches every
    error and still renders the completed page.
- **Create:** `hdx_send_new_org_request` (`ckanext-hdx_users/actions/misc.py`) sends two emails:
  - to `hdx.faqrequest.email`, via `new_org_request_hdx_team_notification.html`;
  - to the requester, via `new_org_request_confirmation_to_user.html`.
  - Both are gated on `hdx.onboarding.send_confirmation_email`.
  - It also sends `OrganizationRequestAnalyticsSender` ('org request'), whose 'org type' is always empty.

### Copy

`helpers/ui_constants/onboarding/`:
- `request_join_organisation.py` (steps 'Your org' / 'Details' / 'Submitted');
- `confirm_organisation_choice.py`, `reason_request_organisation.py` and
  `completed_organisation_request.py`, which re-export the join steps;
- `request_create_organisation.py` (steps 'Details' / 'Submitted');
- `completed_organisation_create.py`.

The `*_ERROR` keys in `request_create_organisation.py` are unused.

### v1 front end

- **Templates:** extend `page_light.html` and override `header_core` (mobile header), `styles`
  (`page-extra-light-styles`, `bem-blocks-styles`), `scripts` (`bem-blocks-scripts`) and
  `breadcrumb_content` ('Organisations').
- **Layout:** Bootstrap `.container > .row > .col-*`. Full-width primary button, then a link-style
  Cancel below it.
- **`bem.blocks` snippets:** `stepper`, `heading`, `info_box`, `paragraph`, `select2_field`,
  `input_field`, `textarea_field`, `form_button`, `form_info`.
  - `info_box` also serves `contribute_flow/create_edit.html` (compact, no icon) and
    `ajax_snippets/api_info.html` (compact, icon), both v1.
- **JS:**
  - `hdx-select2-field.js`: searchable org picker, `?selected=` preselect.
  - `bem.blocks/textarea_field.js`: "N characters" counter.
  - `hdx_show_more.js`: jQuery expander on the description, 370 characters, " ... More" / "Less".
- **Confirm screen:**
  - the logo appears only when the org has a custom rect logo;
  - "Member since" uses `h.render_datetime` ("July 16, 2014");
  - the description is output raw with `|safe`.

### Analytics

Only the generic Mixpanel "page view", whose "page title" comes from `{% block subtitle %}`:

| Template | Subtitle |
|---|---|
| Find | 'Request to join an organisation' |
| Confirm | 'Confirm your choice of organisation' |
| Reason | 'Reason for request' |
| Join completed, Create completed | 'Request submitted' |
| New org | 'Request to create a new organisation' |

There are no client events specific to the flow. Server side: 'org request' (create only).

### Tests

- `ckanext-hdx_org_group/.../tests/test_join_organization.py` → `TestJoinOrg.test_join_organization`:
  403 for anonymous users, 404 on GET for the POST routes, page copy, the confirm page containing the
  raw org description and title, and a pending member being created.
- `test_request_organization.py` → `TestRequestOrg.test_request_organization`: page copy, the
  'Missing value' count dropping 5 → 4 as fields are filled.
- `test_auth.py` → `test_new_org_request_page`, `test_new_org_request`.
- `ckanext-hdx_users/.../tests/test_org_requests.py`; `test_onboarding_v2/test_came_from.py`.

---

## 2. Figma Analysis

### Layout (all three screens)

```
breadcrumb            Home / Sign up / Request to join an org (XL New org: Request to create a new org)
.intro-hdx            padding 96px 48px (XL) · 24px 16px (SM) · gap 40 / 32
├── .header           580px
│   ├── stepper       1 Your Org · 2 Details · 3 Submitted (step 1 active on every screen)
│   └── h1            Merriweather 32px XL / 24px SM
└── .form             580px, gap 20
```

### `xl-request-join` / `sm-join-org`

Visible elements, in order:
1. Info box: two paragraphs.
2. Bold line "Please select an organisation to join from the list below:".
3. "If you can not find your organisation in the list, you can request to *create a new one*".
4. "Select" dropdown with chevron.
5. Buttons: Cancel (tertiary) and Continue (primary), right-aligned.

### `xl-request-new-org` / `sm-create-org`

Visible elements, in order:
1. Info box: two paragraphs.
2. "* indicates mandatory fields".
3. Fields: name\*, description, website\*, role\* (textarea), data type\* (one-sentence label),
   "Is the data already available publicly through a website?"\* (Yes/No dropdown),
   "If yes, please provide a link:".
4. Buttons: Cancel and Submit.

### `xl-request-new-confirm` / `sm-confirm-org`

Visible elements, in order:
1. "You have chosen to request to join:" (18px, 600) and the org name (16px, 500).
2. Org logo, 120×45.
3. "About this organisation:" (18px, 600).
4. "Member since 16 July 2014" (600), then the description in link blue, then "...More".
5. Primary "Yes - Choose this organisation".
6. Right-aligned underlined links: "No - Choose a different organisation" or "Create a new one".

### Token map

| Figma | v2 |
|---|---|
| Info box `#e8effb`, 6px radius, 24px padding, 12px gap, 24px `info-fill` icon, black 16px text | `--hdx-primary-05`, `--hdx-radius-md` (nearest token), `--hdx-space-6`, `--hdx-space-3`, `v2/icons/info-fill.svg`, `.hdx-body-m()` `--hdx-neutral-95` |
| Primary button `#1862d8` | `button.html style='primary'` (`--hdx-primary-5`) |
| Cancel: white, `#d8e0e1` border, drop shadow | `button.html style='tertiary'` |
| Asterisk / mandatory note `#c44536` | `__required` spans (`--hdx-error-5`), signup `__mandatory-note` |
| Title 24 / 32px Merriweather | `.hdx-page-title-scale()` (24 / 28 / 32) |
| 580px column | signup `__card` 100% / 80% / 50% |
| Labels `#2f3536` / `#4b5563`, 500 | `text-field` / `select` label (`.hdx-body-m-medium()`) |

### Hidden layers (`display: none` in every export)

reCAPTCHA (all screens), Terms of Service + newsletter checkboxes (New, Confirm), and the Confirm
screen's info box, mandatory note and Cancel button. None of them exist in v1 or in the schema; they are
not built (D17).

### XL vs SM

Same screens, same order, single column at every size. On SM the step labels are hidden layers (badges
only), the title is 24px and the side padding is 16px. The buttons stay side by side and right-aligned.
No separate SM drawer or modal flow.

---

## 3. Current vs Target

| Aspect | v1 | Target | Basis |
|---|---|---|---|
| Base / layout | `page_light.html`, Bootstrap grid | `v2/page.html`, signup shell | D1 |
| Breadcrumb | Home / Organisations | Home / Organisations / page title | D2 |
| Stepper | `bem.blocks/stepper`; create has 2 steps | `c-step-pager`; create has 3 steps, form on step 2 | D6, D14 |
| Title | `bem.blocks/heading` | signup `__heading` on the title scale | D15 |
| Info box | `bem.blocks/info_box` | `c-info-box` | D7 |
| Org picker | select2, bootstrap-5 theme (search inside names) | `select.html` `searchable` (Select2, `hdx-v2` theme) | D3–D5 |
| Create fields | `bem.blocks` inputs/textareas + select2 | `text-field` / `select.html` | §4 |
| Data-type label | label + 3 guidelines | Figma sentence | D9 |
| Required set | schema | schema (Figma differs) | D8 |
| Confirm block | custom-logo only, `render_datetime`, raw description + expander | org-page behaviour | D11 |
| Reason counter | jQuery counter | `text-field` `character_count` | D13 |
| Buttons | full-width primary, link Cancel below | right-aligned tertiary Cancel + primary | D1 |
| Bad org_id | empty page | error alert + back link | D16 |
| reCAPTCHA / ToS / newsletter | none | none (hidden in Figma) | D17 |
| Backend, emails, analytics, `subtitle` | — | unchanged | §8 |

Removed from these pages: the `bem-blocks-*`, `page-extra-light-styles` and v1 `select2-4-*` bundles, the
jQuery expander and every Bootstrap class.

---

## 4. Component Mapping

| Element | Component |
|---|---|
| Breadcrumb | `v2/components/breadcrumb.html` (D2) |
| Stepper | `v2/components/step-pager.html` (D6, D14) |
| Title, body text, mandatory note, actions row | signup shell classes (D1) |
| Info box (Find, New) | `v2/components/info-box.html` (D7) |
| Org picker | `v2/components/select.html` `searchable=True`, `select_attrs`, `placeholder` (D3–D5, D24) |
| "create a new one" link (Find) | existing `SELECT_ORGANISATION_LABEL` markup (`|safe`) |
| Name, website, link inputs | `v2/components/text-field.html` `size='m'` (D22) |
| Description, role, data type textareas | `text-field.html` `size='m'`, `multiline=True`, `required=True` (D12, D21) |
| "Data already available" | `select.html` `options={'no': 'No', 'yes': 'Yes'}`, `placeholder`, `required=True` (D24) |
| Reason textarea | `text-field.html` `size='m'`, `multiline=True`, `required=True`, `character_count=True` (D13) |
| Per-field errors (New) | `errors=errors.get(<name>)` on each field; no summary alert |
| Confirm logo, member since, description | page markup in `pages/org-request.less`, `.hdx-org-logo()`, the org-description mixins, clamped-text module (D11) |
| Confirm links | `v2/components/text-link.html` (D20) |
| Not-found alert | `v2/components/alert.html` (D16) |
| Cancel / submit / completed CTA | `v2/components/button.html` (`tertiary` / `primary`, `size='l'`) |

---

## 5. Flow & States

```
Find (GET, ?selected=) ──Continue──▶ Confirm (POST org_id) ──Yes──▶ Reason (POST org_id)
   │                                   │  "No – choose a different…" → Find      │
   │ "create a new one"                │  "create a new one" → New               │ Submit
   ▼                                   ▼                                          ▼
New org (GET/POST) ──Submit (valid)──▶ 302 ▶ Create completed      Join completed (POST, always success page)
   └── invalid → re-render with per-field errors
```

| State | Behaviour |
|---|---|
| `?selected=<id>` | Option preselected; the field shows it |
| Search no match | The panel shows Select2's 'No results found' |
| Continue with nothing selected | Blocked by native `required`, also after × clears the field |
| New org errors | Per-field NAVL errors; values kept |
| Confirm/Reason with an unknown `org_id` | D16 alert, form hidden |
| Missing `org_id` / blank message | View redirects to Find (unchanged) |
| Join failure (duplicate, sysadmin, no admins) | Completed page, as today (D17) |
| JS off | Native select without Select2; all forms submit normally |

---

## 6. Responsive Behaviour

| Aspect | SM | MD | XL |
|---|---|---|---|
| Column (`__card`) | 100% | 80% | 50% |
| Step pager | 80%, badges only | 80%, labels | 50%, labels |
| Title | 24px | 28px | 32px |
| Page margins | `--hdx-space-8` | `--hdx-space-8` | `--hdx-space-24` |
| Fields | full column width, stacked | same | same |
| Buttons / links | right-aligned row | same | same |

All values come from `pages/signup.less` and `c-step-pager`. No org-specific breakpoints.

---

## 7. Template Strategy

- The six templates are replaced in place and extend `v2/page.html`. Only these views render them, so no
  `v2` gate is needed and no non-v2 page is affected.
- Each template sets the signup layout variables, empties `{% block secondary %}` and fills
  `{% block breadcrumb_items %}`, `{% block styles %}` (`v2-signup-page-styles`; on Find also `v2-select2-styles`,
  plus `v2-select2-scripts` in `{% block scripts %}`; on Confirm and Reason also `v2-org-request-page-styles`) and
  `{% block primary %}`.
- Preserved verbatim: every `{% block subtitle %}`, the form ids (`find-organisation-form`,
  `confirm-organisation-form`, `reason-request-form`, `org-new-request-form`), field `name`s, the hidden
  `org_id`, `h.csrf_input()`, form `action`s and methods, and the `?selected=` read.
- Cancel links go to `home.index`. The completed CTAs go to `home.index` with the existing labels.
- Unused templates under `templates/organization/` (`request_new.html`, `request_mem_or_org.html`,
  `request_organization_form.html`, `organization_preselector.html`, `snippets/req_membership*.html`)
  are not touched.

---

## 8. Functionality & Analytics Preservation

| Item | Status |
|---|---|
| Routes, methods, auth (403), redirects, referrer guard | Unchanged |
| Schema validators and field names | Unchanged |
| `member_request_create`, `hdx_send_new_org_request`, all emails | Unchanged |
| Server analytics 'org request' | Unchanged |
| Mixpanel page title (`subtitle` blocks) | Unchanged |
| Header "Add data" click tracking (`hdx_click_stopper`) | Unchanged (outside these templates) |
| `?selected=` preselect | Preserved through `select.html` `selected` |

---

## 9. Accessibility

- **Org picker:** the bold line and the "can not find" line keep their visual order. The `<select>`
  gets `aria-labelledby` / `aria-describedby` to them (D5). `required` is native.
- **Select2:** combobox / listbox roles and `aria-activedescendant` come from Select2; the picker's
  labelling reaches its combobox and search box through `select.js` (D5).
- **Step pager:** `<ol>` of `<li>`, `aria-current="step"` on the active step, `.sr-only` label copies
  (", completed" on finished steps) behind `aria-hidden` visible labels, decorative connectors (D14).
- **Info box:** static content, no live-region role. The icon is `aria-hidden` (D7).
- **Alert:** `c-alert` error (`role="alert"`) for the not-found state (D16).
- **Counter:** visible text below the Reason textarea, not a live region (D13).
- **Logo:** `alt` as in `page-header.html` (the org name).
- **Show more:** a `text-button` with the clamped-text module's state handling.
- **Fields:** each field passes an `id` so its label gets `for`. Required asterisks are
  `aria-hidden`, backed by native `required`. The label-less Reason textarea is named by the heading
  (`aria-labelledby`) and described by the instructions (`aria-describedby`).

---

## 10. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| Renaming a field `name` breaks NAVL / views | Names kept verbatim (§7) |
| `test_join_organization` asserts the raw description on Confirm | `render_markdown` wraps it in `<p>`. The test description is plain text, so the substring still matches; checked in verification |
| `test_request_organization` counts 'Missing value' | Per-field errors only, no summary alert |
| Select2 4.1 leaves its search box unfocused with jQuery 3.6+ (select2#5993) | `select.js` focuses it on `select2:open`, as v1 did |
| Native `required` sits on the visually hidden `<select>` | The browser's bubble anchors at the field's top-left, as in v1 |
| The 050, 061, group-message and HDX Connect drawer textareas become natively required (D12) | All are already required; the drawers submit via JS, so native validation never blocks them |
| Signup heading shrinks at SM/MD (D15) | Matches the signup Figma ramp |
| Join errors are swallowed | Preserved as existing backend behaviour (D17) |

---

## 11. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | Page shell | Signup shell as-is · generalise the signup shell · message-form shell (050/061) | Signup shell as-is: `outer_row_class='hdx-v2-signup-outer-row'`, `breadcrumb_row_class='hdx-v2-breadcrumb-row--white'`, `content_class='hdx-v2-content-columns__content'`, `.hdx-v2-signup-form-page` > `c-step-pager` + `__card` (`__heading`, `__body-text`, `__mandatory-note`, `__fields`, `__actions`), bundle `v2-signup-page-styles`. Org-only rules (confirm block, reason list) go in a new `pages/org-request.less` → `v2-org-request-page-styles` |
| D2 | Breadcrumb | Home / Organisations / page · Figma Home / Sign up / page · Home / page | Home / Organisations (`organization.index`) / `CONST.PAGE_TITLE` (last item, unlinked) |
| D3 | Org picker | Native `select.html` · `select.html` + filter box · Select2 (v1) | Select2 4.1.0-rc.0 (v1's vendored `vendor/select2-4/`) through `select.html` `searchable=True`, which marks the `<select>` `data-searchable`. Page-loaded bundles: `v2-select2-styles` (vendor CSS) and `v2-select2-scripts` (vendor JS + `fanstatic/v2/components/select.js`). `select.js` applies the `hdx-v2` theme, `width: 100%`, the `.c-dropdown` wrapper as `dropdownParent`, `selectionCssClass: 'c-dropdown__select'` (the closed field keeps the native select's styles and chevron) and the disabled empty option as placeholder. The theme (`dropdown.less`) gives the open panel the `c-dropdown__panel` skin, a `c-search-input`-style search box with icon and `c-list-item`-style rows (highlighted primary-5, selected medium weight). jQuery is already on every v2 page and is used only for the Select2 calls |
| D4 | Select2 behaviour | v1 defaults · custom copy | v1 defaults: `allowClear` (× clears back to the placeholder), Select2's English messages ('No results found'), no search-box placeholder, default matcher (case- and diacritic-insensitive substring). No new constants |
| D5 | Picker accessible name | `aria-labelledby` keeping the Figma order · `label` param with the hint below | New `select_attrs` param on `select.html` (attributes on the `<select>`, like text-field's `input_attrs`). It carries `aria-labelledby` (bold line) and `aria-describedby` ("can not find" line). `select.js` copies both onto Select2's combobox, and `aria-labelledby` onto its search box. No visible asterisk; `required` kept |
| D6 | Create-org stepper | 3 steps, form on step 2 · 3 steps, Figma literal · keep v1's 2 steps | 3 steps with the join labels: New org = step 2, Create completed = step 3. `request_create_organisation.py` re-exports the join `STEPS_1..3`; `completed_organisation_create.py` adds `STEPS_3` |
| D7 | Info box | Page-local markup · extend `c-alert` · new component | New `c-info-box` (`templates/v2/components/info-box.html` + `less/v2/components/info-box.less`). v1 `info_box` has two more callers waiting for migration. Minimal API: `paragraphs`, `extra_classes`; always the `info-fill` 24px icon in `--hdx-primary-5` (`aria-hidden`); `--hdx-primary-05` background, `--hdx-radius-md`, `--hdx-space-6` padding, `--hdx-space-3` gap, `.hdx-body-m()` `--hdx-neutral-95`. Compact and no-icon variants are added when `contribute_flow` migrates |
| D8 | Required fields | Schema · Figma (website required, description optional) | Schema: name, description, role, data type and "data already available" required; website and link optional |
| D9 | Copy | Keep the constants · Figma copy | Constants kept. `TEXTAREA_DATA_TYPE_LABEL` becomes the Figma sentence ('What type of data would your organisation like to share? Please include details about the topics and locations covered by the data, along with the format.'). `TEXTAREA_DATA_TYPE_LABEL_GUIDELINE_TITLE`, `_1`/`_2`/`_3` and the unused `*_ERROR` keys are deleted |
| D10 | "If yes, please provide a link" | Always visible · reveal on 'Yes' | Always visible and optional; no JS |
| D11 | Confirm "About this organisation" | v2 org-page behaviour · v1 behaviour | Date: `h.hdx_format_date(org_dict.created)`. Logo: `custom_rect_logo_url` → core `organization_show`'s `image_display_url` → none, sized with `.hdx-org-logo()`. Description: `h.render_markdown(org_dict.description)` in the clamped-text module (`data-module="clamped-text"`, `[data-clamped-content]`, a `text-button` with `data-clamped-toggle`). Member since and description call `.hdx-member-since()` / `.hdx-clamped-desc()` / `.hdx-clamped-desc-text()` (`mixins.less`), which `c-page-header` also calls, so not Figma's link blue or semibold date |
| D12 | Textarea `required` | Extend `text-field.html` · leave it | The textarea renders `required` and `input_attrs` the same way the `<input>` does. The required textareas on 050, 061, the group-message drawer and the HDX Connect drawers gain native `required` |
| D13 | Reason character counter | Drop it · add one to `text-field` | Opt-in `character_count` param on `text-field.html`: a server-rendered `.c-form-field__hint` counter below the field, not a live region. `input-field.js` updates it on `input` ("N characters" / "1 character") |
| D14 | Step-pager semantics | Fix in the component · leave it | `<ol>` / `<li>` markup, `aria-current="step"` on the active step, an `.sr-only` copy of each label (", completed" on completed steps) behind the `aria-hidden` visible label, so SM reads the labels too; `aria-hidden` connectors open each `<li>` after the first. No visual change; the signup pages get it too |
| D15 | Heading size | Title scale in `signup.less` · 32px everywhere · org-only override | `.hdx-v2-signup-form-page__heading` uses `.hdx-page-title-scale()` (24 / 28 / 32); applies to the signup pages too |
| D16 | Unknown `org_id` on Confirm / Reason | Error alert + back link · v1 parity · redirect in the view | Template only: when `data.org_dict` is empty, render `alert.html` (error, `dismissible=False`) with 'This organisation could not be found. `<a href="{0}">`Choose another organisation`</a>`.' (passed through `h.literal`, `{0}` = Find), instead of the form. New key `BODY_ORG_NOT_FOUND` in `request_join_organisation.py`, re-exported by `confirm_organisation_choice.py` and `reason_request_organisation.py` |
| D17 | Hidden Figma layers and backend | — | reCAPTCHA, ToS, newsletter and the hidden Confirm layers are not built. No view, schema, email or analytics change; join errors stay swallowed |
| D18 | Reason screen (no Figma) | — | Step 2; heading `PAGE_TITLE`; `__body-text` `BODY_MAIN_TEXT`; "Please indicate:" + `<ul>` of the two entries; `text-field` multiline `name='message'`, required, with the counter; Cancel / Submit in `__actions` |
| D19 | Completed screens (no Figma) | — | Step 3 on both flows; heading `PAGE_TITLE` + `__body-text` `BODY_MAIN_TEXT`; primary `button.html tag='a'` → `home.index` with the existing `BUTTON_SUBMIT` label |
| D20 | Confirm actions | — | Primary submit "Yes - Choose this organisation". Below it, a right-aligned row: tertiary `text-link` "No - Choose a different organisation" (→ Find), "or", tertiary `text-link` "create a new one" (→ `hdx_org_request.new`) |
| D21 | Role field | One-line input (v1) · textarea (Figma) | Textarea: `text-field` `multiline=True`, `required=True` |
| D22 | Field size | `size='l'` (signup) · `size='m'` (050/061) | `size='m'` on every text field and textarea, the same 34px height as `select.html` |
| D23 | Textarea height | Component 100px · 140px page rule · `rows`-driven | Component height (`.c-search-input--textarea`); Figma's 140px is not applied |
| D24 | Select placeholders | v1 placeholders · Yes/No defaults to 'No' · Figma 'Select' | `SELECT_ORGANISATION_PLACEHOLDER` and `SELECT_DATA_ALREADY_AVAILABLE_PLACEHOLDER`; native `required` forces a choice |
| D25 | Org page "Request membership" | Fix in `org-hero.html` · Risks row only · notice on Find | `v2/org-hero.html` shows it only when `allow_req_membership` and `org_dict.request_membership != 'false'`, as v1 `org_actions_menu.html` does. Find drops those orgs, so `?selected=` would preselect nothing |

---

## 12. Files Affected

| File | Change |
|---|---|
| `templates/org/join/find_organisation.html` | v2 rewrite: info box, searchable org select + Select2 bundles, Cancel / Continue |
| `templates/org/join/confirm_organisation.html` | v2 rewrite: confirm block (D11), actions (D20), not-found alert (D16) |
| `templates/org/join/reason_request.html` | v2 rewrite (D18), not-found alert (D16) |
| `templates/org/join/completed.html` | v2 rewrite (D19) |
| `templates/org/request/org_new_request.html` | v2 rewrite: info box, mandatory note, fields (§4), Cancel / Submit |
| `templates/org/request/completed_request.html` | v2 rewrite (D19) |
| `templates/v2/org-hero.html` | "Request membership" gated on `request_membership` (D25) |
| `templates/v2/components/info-box.html` | New `c-info-box` (D7) |
| `hdx-styles/src/common/less/v2/components/info-box.less` | New |
| `templates/v2/components/select.html` | `searchable`, `select_attrs` (D3, D5) |
| `hdx-styles/src/common/less/v2/components/dropdown.less` | Select2 `hdx-v2` theme block (D3) |
| `fanstatic/v2/components/select.js` | New: Select2 init, labelling copy, search-box focus (D3, D5) |
| `templates/v2/components/text-field.html` | Textarea `required` / `input_attrs` (D12); `character_count` (D13) |
| `fanstatic/v2/components/input-field.js` | Counter updates |
| `templates/v2/components/step-pager.html` | List semantics (D14) |
| `hdx-styles/src/common/less/v2/components/step-pager.less` | List reset, connector placement |
| `hdx-styles/src/common/less/v2/pages/signup.less` | `__heading` → `.hdx-page-title-scale()` (D15) |
| `hdx-styles/src/common/less/v2/pages/org-request.less` | New: confirm block, reason list, links row |
| `hdx-styles/src/common/less/v2/mixins.less` | `.hdx-member-since()`, `.hdx-clamped-desc()`, `.hdx-clamped-desc-text()` (D11) |
| `hdx-styles/src/common/less/v2/components/page-header.less` | `__member-since`, `__desc`, `__desc-text` call those mixins; compiled CSS unchanged |
| `fanstatic/webassets.yml` | `info-box.css` in `v2-components-styles`; new `v2-select2-styles`, `v2-select2-scripts` and `v2-org-request-page-styles` |
| `templates/v2/components.html` | Demo sections: `c-info-box`, searchable select (+ Select2 bundles), counter |
| `helpers/ui_constants/onboarding/request_join_organisation.py` | `BODY_ORG_NOT_FOUND` (D16) |
| `helpers/ui_constants/onboarding/confirm_organisation_choice.py`, `reason_request_organisation.py` | Re-export `BODY_ORG_NOT_FOUND` |
| `helpers/ui_constants/onboarding/request_create_organisation.py` | Join steps (D6), data-type label, guideline and `*_ERROR` keys removed (D9) |
| `helpers/ui_constants/onboarding/completed_organisation_create.py` | `STEPS_3` (D6) |
| `ckanext-hdx_org_group/.../tests/test_join_organization.py` | Extended: v2 markup, `?selected=` preselect, not-found alert |
| `ckanext-hdx_org_group/.../tests/test_request_organization.py` | Extended: data-type label, 3-step pager |
| `ckanext-hdx_users/.../tests/test_onboarding_v2/test_onboarding_create_user.py` | Step-label asserts include `aria-hidden="true"` (D14) |
| `llm_docs/redesign/PROGRESS.md` | Holding-state rows → migrated pages; `c-info-box` and the new bundle; next-steps item |
| `llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Holding-state line; Org join / create flow key-page entry |
| `llm_docs/redesign/requirements/052-signup-flow-v2.md` | Only statements made false by D14 / D15 |
| `llm_docs/redesign/requirements/056-organization-page-datasets-v2.md` | D13 gating statement (D25) |

Template, LESS, JS and constants paths are relative to `ckanext-hdx_theme/ckanext/hdx_theme/`.

---

## 13. Verification Checklist

- [ ] Find renders on v2 with and without `?selected=<org id>`; the preselected org shows in the field.
- [ ] The org field looks like the other selects; its panel search matches mid-word and
      accent-insensitively; × clears back to the placeholder.
- [ ] Continue with no org selected is blocked natively.
- [ ] Confirm shows the logo (custom and `image_url` orgs), "Member since" in `h.hdx_format_date`
      format, and the markdown description with Show more / Show less.
- [ ] Confirm / Reason POSTed with a bogus `org_id` show the not-found alert and no form.
- [ ] A Reason submit creates a pending member; the join completed page shows step 3.
- [ ] New org: invalid POST shows per-field errors and no summary; a valid POST redirects to
      completed (step 3); completed without the referrer → 404.
- [ ] New org: role is a textarea; inputs and selects are 34px.
- [ ] "Request membership" is hidden on orgs with `request_membership` 'false'.
- [ ] Page `<title>` / Mixpanel page titles are unchanged on all six screens.
- [ ] No Bootstrap classes and no `bem-blocks`, `page-extra-light` or v1 `select2-4` assets in the rendered HTML.
- [ ] The existing tests in `test_join_organization.py`, `test_request_organization.py`, `test_auth.py`,
      `test_org_requests.py` and `test_came_from.py` pass.
- [ ] The signup pages' step pager looks unchanged; the heading is 24 / 28 / 32px.
- [ ] The 050 / 061 forms and the group-message / HDX Connect drawers still submit with native `required` on their textareas.
- [ ] Keyboard walkthrough: org field (open, type, arrows, Enter, Escape) → Continue; Show more toggle; the
      field announces the bold line and its value.
- [ ] Visual check at SM, MD, XL, XXL.
