# 082 — Edit Organisation Page v2

**Scope:** migrate the Edit Organisation page (`organization.edit`) and the sysadmin Create Organisation page
(`hdx_org.new`), which renders the same form, from the v1 `page.html` shell, Bootstrap and `macros/form.html` to v2.
This includes two new components: `c-slug-preview` and `c-image-upload`. It also includes two small backend
changes:
- a shared logo-URL resolver, so linked logos render;
- logo fixes in the update action: Remove clears the logo, an unposted logo keeps its stored value, and old files
  are deleted only after a successful save.

**Excluded:**
- the core `EditGroupView` / `CreateGroupView` / `DeleteGroupView` views, the schema and validators, and the
  auth functions;
- the v1 visualisation snippets and v1 JS / bundles.

No route, permission, field name or analytics value changes.

**Figma sources:** `xl-edit-org-page.html`, `md-edit-org-page.html`, `sm-edit-org-page.html`

---

## Context

Every v2 org page shows an "Edit org page" action in `v2/org-hero.html` (`header_actions`). It is gated by
`h.check_access('organization_update')` and links to `organization.edit`. That page is the last org page still on
the v1 shell: old header and footer, a Bootstrap form, jQuery modules, numbered sections and a visually hidden H1.

The other org pages are already v2: Datasets, Activity, Stats, Members and Requested Data (056–059, 080).

The Figma exports show a single-column 580px form in the same shell as the 081 create-org request. There is no org
hero, no tabs and no sidebar.

---

## 1. Existing Implementation Audit

### Routes / views (unchanged — reference only)

| Screen | Route | View | Template chain |
|---|---|---|---|
| Edit | GET/POST `/organization/edit/<id>` | core `organization.edit` (`EditGroupView`, `ckan/views/group.py`) | `organization/edit.html` → core `organization/base_form_page.html` → `organization/edit_base.html` → v1 `page.html` |
| Create | GET/POST `/organization/new` | `hdx_org.new` = core `CreateGroupView` (`ckanext-hdx_org_group/.../views/organization.py`) | `organization/new.html` → core `base_form_page.html` → … |
| Delete | GET/POST `/organization/delete/<id>` | core `DeleteGroupView` | core `organization/confirm_delete.html` (no-JS GET only) |
| Restore | POST `/organization/restore/<id>` | `hdx_org.restore` | redirect to `organization.read` |

**The form.** `group_form` returns `organization/new_organization_form.html` for both create and edit. The view
renders it into `form` and passes `action` ('new' / 'edit'), `data`, `errors`, `error_summary` and `group_type`.
`setup_template_variables` → `new_org_template_variables` injects `data['hdx_org_type_list']`.

**Edit `_prepare`:**
- `organization_show` with `for_edit: True`; a missing org gives 404;
- `check_access('organization_update')` gives 403. In practice that means org admins and sysadmins; editors and
  members are refused;
- the context reads `save` / `parent` from `request.args`. No other query params are used.

**Edit POST:**
- It parses `request.form` + `request.files` and sets `allow_partial_update = True`.
- It then calls `organization_update`.
- A slug change triggers `_force_reindex` of the org's datasets.
- `ValidationError` re-renders with `errors` / `error_summary`.
- Success redirects to `organization.read` (v2) with **no flash**.

**Create:** effectively sysadmin-only (`ckan.auth.user_create_organizations = false`). It fires the server
`OrganizationCreateAnalyticsSender` ('org create').

**Restore:**
- Checks `organization_patch`, patches `state='active'` and redirects to the org page.
- It reads only the id from the URL.

### Update action (`ckanext-hdx_org_group/.../helpers/organization_helper.py`)

`organization_update` → `hdx_organization_update` → `hdx_group_or_org_update(context, data_dict, is_org=True)`,
then `lunr.build_index()`.

`hdx_group_or_org_update`:
1. Loads the stored `customization` extra, or `{'image_sq': '', 'image_rect': ''}`.
2. Parses the posted `customization` JSON, or `{}` on failure.
3. Runs `_manage_image_upload_for_org('image_sq' | 'image_rect', …)`:
   - `clear_<f>` removes the stored file and blanks the posted customization value;
   - `<f>_upload` replaces the file through `uploader.Upload('group', …)`, stored in `storage/uploads/group/`.
4. The **rearrange block** sets `customization[<f>]` to the posted `<f>` when non-empty, **otherwise to the
   stored filename**, and to `''` when `<f>` is not posted at all (`KeyError`).
5. `plugin_validate`, then `group_dict_save`, then `IOrganizationController.edit`, the activity, the file uploads,
   and commit.

### Schema (`HDXOrgGroupPlugin._modify_group_schema`, shared by create and update)

| Field | Validators |
|---|---|
| `name` | core update: `ignore_missing`, `not_empty`, `group_name_validator` (no format check on update) |
| `title` | core: `ignore_missing` |
| `description` | `not_empty` |
| `org_url` | `not_missing`, `hdx_url_validator` (empty passes; http → "starts with https://"), `convert_to_extras` |
| `hdx_org_type` | `not_empty`, `correct_hdx_org_type`, `convert_to_extras` ('-1' rejected) |
| `fts_id`, `user_survey_url` | `hdx_org_keep_prev_value_if_empty_unless_sysadmin`, `ignore_missing`, `convert_to_extras` |
| `closed_organization` | `hdx_boolean_string_converter`, `set_inactive_if_closed_organization` (" (inactive)" title suffix), `convert_to_extras` |
| `custom_org`, `request_membership`, `customization`, `visualization_config`, `modified_at`, `org_acronym` | `ignore_missing`, `convert_to_extras` |

**⚠ Extras are a full replace.** When any extra is posted, `group_dict_save` deletes every stored extra that isn't
in the payload. A field the form stops posting therefore loses its stored value. That is why the sysadmin-only
fields have the keep-previous validator.

### Permissions

| Item | Rule |
|---|---|
| Page + save | `organization_update` (org admin, sysadmin) |
| `fts_id`, `user_survey_url` | Rendered only for `c.userobj.sysadmin`; non-sysadmin values restored server-side |
| Delete | `h.check_access('organization_delete', {'id': data.id})` and `data.state == 'active'` (sysadmins; `user_delete_organizations = false`) |
| Restore | Rendered when `organization_delete` passes and `data.state == 'deleted'`; view checks `organization_patch` |
| Every other field | Any user who passes `organization_update` |

### v1 form (`organization/snippets/organization_form.html`, via `new_organization_form.html`)

- **The form:** `<form id="req-create-org-form" … method="post" enctype="multipart/form-data" data-module="basic-form">`
  with `h.csrf_input()`. `basic-form` isn't bundled, so that module does nothing.
- **Error summary:** `form.errors(error_summary)`.
- **Sections:** '1. Basic Details', '2. Custom Styles', '3. Topline Numbers', '4. Visualization Configuration',
  '5. Optional User Survey'.
  - Sections 2–5 are inside `#customization-fields`, hidden until `custom_org` is ticked.
- **The child template:**
  - empties `custom_fields`, so there is no extras UI;
  - sets the submit label to 'Update Organisation' on edit and 'Submit' on create;
  - renders `delete_button` only on edit.

| Field | Widget | Help text | Visibility |
|---|---|---|---|
| `title` 'Name of Organisation' | `form.input`, `slug-preview-target` | 'Be as specific as possible (i.e. don't just say WFP, say WFP-Colombia)' | all |
| `name` 'URL' | `form.prepend` `/organization/`, `slug-preview-slug` (prefix = domain, placeholder `<organization>`) | — | all |
| `org_url` 'URL of Organisation' | `type=url`, placeholder 'https://example.com/about' | 'Where can people go to find more about this organisation?' | all |
| `description` 'Description of Organisation' | `form.markdown` (Markdown hint) | 'Brief overview of what organisation is for.' | all |
| `org_acronym` 'Organisation Acronym' | input | repeats the label | all |
| `hdx_org_type` 'Organisation Type' | `form.select`, `hdx_org_type_list` ('-1' '-- Please select --' + `ORGANIZATION_TYPE_LIST`) | 'What is the type of your organisation ?' | all |
| `fts_id` 'FTS ID' | input | 'ID for Financial Tracking Service' | sysadmin |
| `custom_org` 'Use custom organisation page' | raw checkbox, value 1, row `#customization-trigger` | — | all |
| `closed_organization` | hidden input synced from an unnamed checkbox ('true'/'false') | 'Check the checkbox if the organization is no longer in use/active in HDX' | all |
| `request_membership` (default 'true') | hidden input synced from an unnamed checkbox | long explanation of the "Request Membership" link and closed groups | all |
| `image_sq` / `image_rect` (+ `_upload`, `clear_`) | `form.image_upload` ×2 + preview `<img>` (placeholder from plchldr.co) | 'Logo 75x75' / 'Logo 300x125' | custom |
| `highlight_color`, `logo_bg_color` | spectrum colour picker | one line each | custom |
| `topline_resource` | input | one line | custom |
| `visualization-select` + `vis-*` | select (embedded / embedded-preview) + `snippets/visualization/embedded*.html` | one line each | custom |
| `customization`, `visualization_config`, `modified_at` | hidden, filled by JS | — | all |
| `user_survey_url` 'User Survey Url' | input | 'The user survey url that will be displayed after downloading a file' | sysadmin |

No field has `maxlength` or native `required`; 'mandatory' is only a CSS class.

**Actions:** a left-floated red Delete, `<a data-module="hdx_confirm-action">` with a Bootstrap modal:
- heading 'You are deleting organisation';
- body 'Are you sure you want to delete this Organisation? This will delete all the public and private datasets
  belonging to this organisation.'

When the org is deleted, a 'Restore Organization' submit with `formaction=hdx_org.restore` appears instead. A
primary submit `name=save value=save` follows.

### v1 JS (`custom_organization_creation.js`, bundle `custom-org-creation-scripts`)

- Hides the edit nav tab.
- Sets up the spectrum pickers.
- Toggles `#customization-fields` on `#field-custom_org`.
- Syncs the hidden `request_membership` / `closed_organization` to 'true' / 'false'.
- Swaps `.visualization-div` on `#visualization-select`.
- On `.create-org-btn` click:
  - trims the description;
  - sets `modified_at = Date.now()`;
  - **only if `custom_org` is ticked**, builds `customization` (`highlight_color`, `logo_bg_color`,
    `topline_dataset`, `topline_resource`; `topline_dataset` has no input, so it is never posted) and
    `visualization_config` (the selected type's `vis-*` fields);
  - removes the header search / Mailchimp forms;
  - calls `$('#req-create-org-form').submit()`.

Other modules on the page:
- `slug-preview-target` / `slug-preview-slug` (`fanstatic/vendor/ckan/slug-preview.js`, `jquery.slug-preview.js`,
  `jquery.slug.js` + core `jquery.url-helpers.js` `$.url.slugify` / `$.url.escape`), all in the `base-main` /
  `ckan` bundles that every v2 page loads; the target listens to `keyup` only;
- `hdx-image-upload` (`fanstatic/hdx-image-upload.js`), with states blank / attached / web and Upload / Link / Remove;
- `hdx_confirm-action`.

Bundles loaded by the form: `colorpicker-scripts`, `custom-org-creation-scripts`, `image-upload-scripts`. `new.html`
also loads `organization-create-styles`.

### Where custom-org data is still used on v2

| Data | Consumer |
|---|---|
| `customization.image_rect` | `OrgMetaDao.__process_custom` → `custom_rect_logo_url` (`v2/org-hero.html`), `organization_join.set_custom_rect_logo_url` (join confirm, `package/request_access.html`), `dataset._process_customizations` (dataset page logo) |
| `custom_org` | `OrgMetaDao.is_custom` and the dataset view build logo URLs only for custom orgs (`set_custom_rect_logo_url` doesn't check it); the dataset view picks `package/custom_hdx_read.html` |
| `highlight_color`, `logo_bg_color` | `dataset._process_customizations` → `organization/custom/custom_style.html` (`package/hdx-read-hxl.html` only) |
| `image_sq` | `OrgMetaDao` → `custom_sq_logo_url` (`light/organization/read.html`) |
| `topline_resource`, `visualization_config` | Only `organization/custom/custom_org*.html`, which no view has rendered since 056 |

All three logo resolvers build `url_for('hdx_local_image_server.org_file', filename=<value>)`. A linked URL stored
by the v1 Link mode therefore does not render. The hero falls back to `org_dict.image_url`, which this form cannot
edit.

### Analytics

- No client or server event is specific to org edit.
- `organization/edit.html` fills `analytics_org_name` (`data.name`) and `analytics_org_id` (`data.id`). These feed
  `analyticsInfo.organizationName` / `organizationId` (`base.html`), the Mixpanel "page view" and the GTM
  `dataLayer`.
- The Mixpanel "page title" comes from `{% block subtitle %}`: 'Edit Organisation' (edit), 'Create an Organisation'
  (create).
- Server side: 'org create' (`OrganizationCreateAnalyticsSender`, create only).

### v1 bugs and quirks

- The `org_url` input passes `error=errors.image_url`, so its errors never render inline.
- `user_survey_url` passes no `error` at all.
- Both `image_upload` calls render `id="field-image-url"`, and the two visualisation snippets share ids.
- The title input renders two `type` attributes.
- The Restore button has `.create-org-btn`. Its click runs the JS `.submit()`, which ignores `formaction`, so
  Restore posts to the edit view.
- Unticking `custom_org` posts an empty `customization`, so the colours and topline are lost. The logos survive
  because the rearrange block restores them.
- Logo **Remove** deletes the file, but the rearrange block restores the old filename, leaving a broken logo.
- Remove and a new upload delete the old file before validation, so a failed save also leaves a broken logo.
- Restore (`organization_patch`) posts no `image_sq` / `image_rect`, so both logos are blanked.
- The delete modal says datasets will be deleted. With `ckan.auth.create_unowned_dataset = false`, core instead
  refuses (403, "Organization cannot be deleted while it still has datasets").
- No success flash after saving.

### Tests

All under `ckanext-hdx_org_group/.../tests/`:

| Test | Asserts |
|---|---|
| `test_controller/test_custom_org_controller.py` → `test_edit_custom_orgs` | Sysadmin GET contains `id="customization-trigger"`; non-admin 403 |
| `test_org_custom_fields.py` → `TestOrgFTSIDController`, `TestOrgUserSurveyUrlController` (+ API classes) | Org admin POST to `organization.edit` keeps the sysadmin-only values; the sysadmin edit GET contains the stored survey URL |
| `test_closed_organization.py` | " (inactive)" suffix |
| `test_auth.py` → `TestOrgAuth` | Create / edit / delete auth |
| `test_actions.py` → `test_org_not_existing` | Delete, then `hdx_org.restore` (admin 404, sysadmin 200) |

No Cypress coverage.

---

## 2. Figma Analysis

### Layout (all three exports)

```
breadcrumb       Home / IOM UN Migration / Edit org page   (SM: #fafbfb row, 16px gutters)
.intro-hdx       padding 96 48 (XL) · 32 48 (MD) · 24 16 (SM)
                 title → form gap 40 (XL) · 16 (MD) · 24 (SM)
├── h1           "Edit org page", Merriweather Bold, 32px XL/MD · 24px SM, #101212
└── form         580px XL/MD · full width SM; sections and fields gap 20
    ├── Basic Details            (20px/600 XL/MD · 18px SM, #2f3536)
    │     Name of organisation *          text, 37px
    │     URL of organisation *           text
    │     Description of organisation *   textarea (grows with content)
    │     Organisation Acronym            text
    │     Organisation type *             "Select ▾" dropdown, 34px
    │     FTS ID                          text (label without asterisk, black)
    │     ☐ Use custom organisation page  + blue "HDX Terms of Service" + *  (copy artefact)
    │     ☐ This organisation is closed/inactive
    │     ☐ Allow membership requests
    ├── Logo
    │     Organisation logo *   [486px URL field, display:none] [⬆ Upload]
    ├── Visualisation configuration   (MD/SM only)
    │     Visualisation type *  "Select ▾"
    ├── Optional user survey
    │     User survey URL       text
    │     reCAPTCHA "I'm not a robot"  (visible)
    └── [Cancel] [Submit]        right-aligned, gap 16
```

### Token map

| Figma | v2 |
|---|---|
| H1 Merriweather 24 / 32px | `.hdx-v2-signup-form-page__heading` → `.hdx-page-title-scale()` (24 / 28 / 32) |
| Section title 18 / 20px, 600, `#2f3536` | `.hdx-section-title()` (18 SM / 20 MD+ Semibold) |
| Label 16px/500 `#2f3536` | `text-field` / `select` label (`.hdx-body-m-medium()`) |
| Asterisk `#c44536` | `__required` (`--hdx-error-5`), `aria-hidden` |
| Input 37px, `#d8e0e1` border, 2px radius | `text-field.html` `size='m'` (34px) |
| Select 34px, drop shadow | `select.html` |
| Checkbox 20px, `#d1d5db`, 3.5px radius | `checkbox.html` (`c-checkbox`) |
| Primary `#1862d8` | `button.html style='primary'` |
| Cancel / Upload: white, `#d8e0e1` border, drop shadow | `button.html style='tertiary'` |
| Upload icon 16px | `v2/icons/upload.svg` |
| 580px column | signup `__card` 100% / 80% / 50% |

### Artefacts and inconsistencies

- **reCAPTCHA:** visible here (in 081 it was a hidden layer). There is no captcha in v1 or in the schema.
- **Custom-page checkbox label:** "Use custom organisation page HDX Terms of Service *" is copied from a terms
  checkbox.
- **Visualisation configuration:** present only in MD/SM.
- **Required markers:** Figma marks URL of organisation and Organisation logo required. The schema does not.
- **Missing from Figma:** the URL slug, the square logo, colours, topline, the visualisation sub-fields, Delete,
  Restore and every help text.

### XL vs MD vs SM

Same content in the same order, single column at every size:

| | SM | MD | XL |
|---|---|---|---|
| Side padding | 16px | 48px | 48px |
| Title size | 24px | 32px | 32px |
| Section titles | 18px | 20px | 20px |
| Fields | full width | 580px | 580px |

Buttons stay side by side and right-aligned. There are no drawers or overlays.

---

## 3. Current vs Target

| Aspect | v1 | Target | Basis |
|---|---|---|---|
| Base / layout | v1 `page.html`, Bootstrap, `.create-org` | `v2/page.html`, signup shell | D13 |
| Breadcrumb | Home / Organizations / {org} / Admin | Home / Organisations / {org} / Edit org page | D14 |
| H1 | visually hidden 'Edit Organisation' | 'Edit org page' (create: 'Create an organisation') | D3, D9 |
| Sections | numbered 1–5, `custom_org` reveal | 1. Basic Details · 2. Logo · 3. Optional user survey, no reveal | D1, D9, D11 |
| Slug | `form.prepend` + slug-preview | `c-slug-preview`, identical behaviour | D5 |
| Logos | square + rect behind the reveal | one always-visible rect uploader, `c-image-upload` | D2, D6 |
| Colours / topline / visualisation | editable behind the reveal | hidden-carried, preserved | D1, D11 |
| Help text, Markdown hint | per field | none | D10 |
| Required markers | `mandatory` class | schema-driven asterisks + native `required` | D8 |
| Errors | `form.errors` list + `.error-block`; `org_url` unbound | summary `c-alert` + per-field on every field | D15 |
| Actions | Delete (left) + 'Update Organisation' | Cancel + Submit; Delete / Restore in a bottom section | D4, D9 |
| Delete confirm | Bootstrap modal, wrong copy | `c-drawer`, disabled while the org has datasets | D4 |
| Logo choice | independent of the custom flag | ticks `custom_org` | D12 |
| Linked logos | stored, never rendered | rendered on hero / dataset / request-access / join | D7 |
| Logo Remove | file deleted, filename kept | logo cleared | D18 |
| Unposted logo keys (square logo, Restore) | blanked | stored value kept | D18 |
| JS | jQuery click handler, spectrum, `hdx-image-upload`, slug-preview | `v2/pages/org-edit.js` on `submit` + component JS | D5, D6, D17 |
| reCAPTCHA / ToS text | none | none (Figma artefacts) | D8 |
| Views, schema, auth, `subtitle`, analytics | — | unchanged | §8 |

Removed from these pages:
- the bundles `colorpicker-scripts`, `custom-org-creation-scripts`, `image-upload-scripts`,
  `organization-create-styles`;
- the hidden edit nav tab;
- every Bootstrap class.

---

## 4. Component Mapping

| Element | Component |
|---|---|
| Breadcrumb | `v2/components/breadcrumb.html` (D14) |
| Shell: H1, field column, actions row | signup shell `.hdx-v2-signup-form-page` > `__card` (`__heading`, `__fields`, `__actions`), `v2-signup-page-styles` (D13) |
| Section titles, danger section | new `pages/org-edit.less` → `v2-org-edit-page-styles`: `hdx-v2-org-edit__section-title` (`.hdx-section-title()`), `__danger` (`.hdx-page-section-header()` title + button row) |
| Create greeting | `v2/components/info-box.html` (D3) |
| Name, org URL, acronym, FTS ID, user survey URL | `v2/components/text-field.html` `size='m'` |
| Description | `text-field.html` `size='m'`, `multiline=True`, `required=True` |
| URL slug | **new** `v2/components/slug-preview.html` (D5) |
| Organisation type | `v2/components/select.html` `options=h.hdx_organization_type_dict()`, `placeholder='Select'`, `required=True` |
| Custom page, closed, membership checkboxes | `v2/components/checkbox.html` rows (`.v2-checkbox-row()`) |
| Organisation logo | **new** `v2/components/image-upload.html` (D6), built on `button.html` tertiary + `upload.svg` / `link.svg` / `close.svg` |
| Error summary | `v2/components/alert.html` (D15) |
| Cancel / Submit | `button.html` (`tertiary` `tag='a'` / `primary` `button_type='submit'`, `size='l'`) |
| Delete trigger / Restore | `button.html` `tertiary` (D4) |
| Delete confirm | `v2/components/drawer.html` + `.c-drawer-form` (`__text`, `__buttons`), as `user/edit_user_form.html` `delete-user-drawer` |

### New component: `c-slug-preview`

- **Files:** `templates/v2/components/slug-preview.html`, `less/v2/components/slug-preview.less`,
  `fanstatic/v2/components/slug-preview.js`.
- **Params:** `name`, `id`, `value`, `label`, `required`, `errors`, `placeholder` (input, 'my-organisation'),
  `prefix` (domain + path), `preview_placeholder` (`<organization>`), `target_id` (the title input to follow).
- **Server render:**
  - the `text-field` (label 'URL', `required`) inside a wrapper, with no prefix;
  - a `hidden` preview row "**URL:** {prefix}{slug} [Edit]", Edit being a `c-text-button`.
- **JS:**
  - Swaps the field for the preview on init unless the field has errors.
  - Restricts and slugifies the input.
  - Auto-fills from the target (on `input`) only if the target was empty at load.
  - Stops the auto-fill on the first manual keystroke.
  - Reveals the field on `invalid`, so the browser can show its message.
  - Edit reveals the field and focuses it.
- **Slugify:** `$.url.slugify` / `$.url.escape` and `$.fn.slug`, already on every v2 page through `hdx_theme/ckan`
  → `base-main`. Output is therefore byte-identical to v1.
- **Bundle:** new `v2-slug-preview-scripts` with only `v2/components/slug-preview.js`. It is page-loaded like
  `v2-select2-scripts`.

### New component: `c-image-upload`

- **Files:** `templates/v2/components/image-upload.html`, `less/v2/components/image-upload.less`,
  `fanstatic/v2/components/image-upload.js`.
- **Params:** `field_url`, `field_upload`, `field_clear`, `value` (stored value), `preview_url` (resolved, D7),
  `clear_value` (re-rendered clear flag), `label`, `url_label`, `remove_label`, `placeholder`, `id`,
  `upload_enabled` (`h.uploads_enabled()`), `errors`, `accept` (default `image/*`; the form passes
  `image/png,image/gif,image/jpeg`, the `ckan.upload.group.mimetypes` default).
- **States (parity with `hdx-image-upload`):**
  - **Blank:** Upload (Figma) + Link buttons.
  - **Attached:** thumbnail + Remove. A stored upload shows no file name (stored names carry a timestamp
    prefix); a newly chosen file adds its name and an object-URL thumbnail. A missing stored file hides the
    thumbnail.
  - **Web:** URL input (Figma's hidden 486px field) + × reset.
- **Transitions:**
  - Remove and × reset to blank, empty the URL and the file input and set `field_clear='true'`.
  - Choosing a file shows it and resets `field_clear` (v1 parity).
  - Initial state: web if the value is http(s), attached if there is a stored filename, blank otherwise.
- **Uploads disabled:** URL input only (v1 `is_upload_enabled` false).
- **Events:** emits `image-upload:change` when a file is chosen or a URL is entered, so the page can auto-tick
  (D12).
- **Bundle:** CSS/JS into `v2-components-styles` / `v2-components-scripts`.

---

## 5. Form Contract

### Visible fields (Figma order)

| Section | Field | Component | Required | Notes |
|---|---|---|---|---|
| Basic Details | `title` 'Name of organisation' | text-field | ✓ | `id='field-title'`; slug target |
| | `name` 'URL' | slug-preview | ✓ | prefix `<domain>/organization/` |
| | `org_url` 'URL of organisation' | text-field `type='url'` | — | v1 placeholder 'https://example.com/about'; `errors.org_url` |
| | `description` 'Description of organisation' | text-field multiline | ✓ | trimmed on submit |
| | `org_acronym` 'Organisation Acronym' | text-field | — | |
| | `hdx_org_type` 'Organisation type' | select | ✓ | placeholder 'Select' |
| | `fts_id` 'FTS ID' | text-field | — | sysadmin only |
| | `custom_org` 'Use custom organisation page' | checkbox, value `1` | — | row `id="customization-trigger"` |
| | `closed_organization` 'This organisation is closed/inactive' | unnamed checkbox + hidden input | — | 'true'/'false' (v1 contract) |
| | `request_membership` 'Allow membership requests' | unnamed checkbox + hidden input | — | default 'true' |
| Logo | `image_rect` / `image_rect_upload` / `clear_image_rect` 'Organisation logo' | image-upload | — | always visible; errors `errors.image_rect_upload` (type) or `errors.upload` (size) |
| Optional user survey | `user_survey_url` 'User survey URL' | text-field | — | sysadmin only; `errors.user_survey_url` |
| Actions | Submit `name=save value=save` | button | | |

The Optional user survey section renders only for sysadmins, as in v1.

### Hidden carry (always posted)

| Field | Value |
|---|---|
| `customization` | `h.dump_json` of the stored customization (`group_dict`; `{}` on create) without `image_sq` / `image_rect` |
| `visualization_config` | stored string verbatim (`group_dict`; empty when unset) |
| `modified_at` | set by `org-edit.js` on submit |

- **Square logo:** `image_sq` is not posted. The update action keeps the stored value (D18).
- **Colours and topline:** carried regardless of `custom_org`, so they survive unticking (a deliberate fix of the
  v1 wipe).
- **Images:** never part of `customization` from the form; the server merges them.

### Kept verbatim

- Form id `req-create-org-form`, `method="post"`, `enctype="multipart/form-data"`, `h.csrf_input()`.
- Every field `name`.
- The v1 `field-*` ids for the visible fields: `field-title`, `field-url`, `field-org-url`, `field-description`,
  `field-org-acronym-id`, `field-hdx-org-type-id`, `field-fts-id`, `field-custom_org`,
  `field-closed_organization`, `field-request_membership`, `field-user-survey-url`.
- `#customization-trigger`.

---

## 6. Flow & States

```
Org hero "Edit org page" ─▶ GET edit ─▶ Submit ─┬─ valid ─▶ 302 organization.read (no flash, unchanged)
                                               └─ invalid ─▶ re-render: per-field errors (+ summary if no field error)
Cancel ─▶ organization.read (create: organization.index)
Delete organisation ─▶ drawer ─▶ Delete POST organization.delete ─▶ core: index + flash (disabled if datasets)
Restore organisation (deleted org) ─▶ POST hdx_org.restore ─▶ organization.read
```

| State | Behaviour |
|---|---|
| Edit, JS on | Slug field collapsed to "URL: …/organization/<slug> [Edit]"; title does not auto-fill |
| Create, empty | Title typing fills the slug until the slug is typed into |
| Create/edit re-render with slug error | Slug field visible with its error; no preview |
| Any re-render | Core passes the posted payload as `data`: fields read it; the Delete / Restore gate, breadcrumb, Cancel and hidden carry read `group_dict`. The logo keeps a posted Remove (`clear_image_rect`); a posted upload that was never written shows the stored logo |
| Logo blank / attached / web | Per §4 `c-image-upload`; initial state from the stored value |
| Logo chosen or URL entered | `custom_org` ticked (D12); Remove does not untick |
| Uploads disabled | Logo URL field only |
| Closed / membership toggled | Hidden 'true'/'false' synced on change and on submit |
| Org has datasets | Drawer says it can't be deleted; Delete disabled |
| Org deleted | Delete section shows Restore instead of Delete |
| Not a sysadmin | No FTS ID, no user survey section, no delete section |
| JS off | Slug field visible; native file input + URL field; hidden booleans keep server values; `modified_at` empty (as v1); no Delete drawer (as 079); Restore works |

---

## 7. Responsive Behaviour

| Aspect | SM | MD | XL |
|---|---|---|---|
| Column (`__card`) | 100% | 80% | 50% |
| Title | 24px | 28px | 32px |
| Section title | 18px | 20px | 20px |
| Page margins | `--hdx-space-8` | `--hdx-space-8` | `--hdx-space-24` |
| Fields | full column width, stacked | same | same |
| Logo row | thumbnail + controls; buttons wrap below the URL field | inline | inline |
| Actions / danger section | right-aligned row | same | same |

Values come from `pages/signup.less`, `.hdx-section-title()` and the components. There are no org-specific
breakpoints.

---

## 8. Template Strategy

- **`organization/edit.html`:** rewritten in place to extend `v2/page.html`.
  - Layout: `outer_row_class='hdx-v2-signup-outer-row'`, `breadcrumb_row_class='hdx-v2-breadcrumb-row--white'`,
    `content_class='hdx-v2-content-columns__content'`.
  - Blocks: `analytics_org_name` / `analytics_org_id` (unchanged), `subtitle` 'Edit Organisation' (unchanged),
    `breadcrumb_items`, `styles` (`v2-signup-page-styles`, `v2-org-edit-page-styles`) and `scripts`
    (`v2-slug-preview-scripts`, `v2-org-edit-page-scripts`).
  - `primary` renders `<div class="hdx-v2-signup-form-page">{{ form | safe }}</div>`.
- **`organization/new.html`:** same treatment. `subtitle` 'Create an Organisation' unchanged; breadcrumb
  Organisations / 'Create an organisation'.
- **`organization/new_organization_form.html`:** becomes the standalone v2 form. It no longer extends
  `organization/snippets/organization_form.html` and branches on `action` for:
  - the H1;
  - the create info box;
  - Cancel's target;
  - the delete/restore section, edit only.
- **No `v2` gate needed:** only the core create/edit views render these templates.
- **Left untouched:**
  - `organization/snippets/organization_form.html`, still extended by the unused `request_organization_form.html`;
  - `organization/edit_base.html`, still extended by `bulk_process.html`, whose route redirects;
  - `snippets/visualization/*`;
  - `custom_organization_creation.js`, `hdx-image-upload.js` and their bundles.

---

## 9. Functionality & Analytics Preservation

| Item | Status |
|---|---|
| Routes, methods, redirects, `_force_reindex` on slug change | Unchanged (core views) |
| Auth: `organization_update`, `organization_delete`, `organization_patch`, sysadmin-only fields | Unchanged |
| Schema, validators, field names | Unchanged |
| Extras not edited in the UI | Preserved through the hidden carry (§5) |
| Mixpanel page title (`subtitle`), `analyticsInfo` org name/id | Unchanged |
| Server 'org create' | Unchanged |
| Delete / Restore | Same endpoints and gates; new confirm UI and copy (D4) |
| Backend changes | Logo URL resolver (D7), logo fixes (D18) |

---

## 10. Accessibility

- **Fields:** every field has an `id` and its label gets `for`. Asterisks are `aria-hidden`, backed by native
  `required`.
- **Sections:** each has an `<h2>` title. The checkbox labels are `<label for>`.
- **Slug preview:**
  - "Edit" is a `<button type="button">` with `aria-controls` (the field wrapper) and `aria-expanded`.
  - Revealing the field moves focus to the input.
  - The preview text is static, not a live region.
- **Image upload:**
  - The component is a `role="group"` labelled by the field label.
  - Upload is a `<button type="button">` that opens a visually hidden `<input type="file">`, labelled by the
    field label.
  - The chosen file name is announced through an `aria-live="polite"` status.
  - Remove and × have `aria-label`s ('Remove organisation logo').
  - Focus moves to the URL input after Link, to Remove after a file is chosen, and to Upload after Remove or ×.
  - The URL input has an `.sr-only` label.
  - The thumbnail `alt` is empty, because it is decorative: the group label and Remove already name the logo.
- **Error summary:** `c-alert` error (`role="alert"`).
- **Delete drawer:** existing `c-drawer`: `role="dialog"`, `aria-modal`, focus trap, Escape closes, focus returns to
  the trigger.
- **Buttons vs links:** Cancel is a link (navigation). Submit, Delete, Restore, Upload, Link, Remove and Edit are
  buttons.
- **Known component gap (not fixed here):** `text-field.html` sets neither `aria-invalid` nor `aria-describedby`
  for its error span.

---

## 11. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| A field missing from the POST deletes its extra | Hidden carry (§5); a test saves an unchanged form and compares extras |
| Carried JSON malformed by quoting | `h.dump_json` into an auto-escaped `value` attribute |
| `OrgMetaDao` `json.loads(customization)` when `custom_org` is set | The update action always re-dumps valid JSON |
| Auto-tick switches the org's dataset pages to `package/custom_hdx_read.html` | Accepted (D12) |
| Create with `customization='{}'` and no logo | Covered by the create test (`hdx_group_or_org_create`) |
| `test_edit_custom_orgs` asserts `id="customization-trigger"` | Id kept on the custom-page checkbox row |
| Slug output diverges from v1 | Same already-loaded `$.url.slugify` (D5) |
| Linked logo URLs now render | External image URLs show on public pages; same trust level as v1's admin-entered URL |
| Delete of an org with datasets | Delete disabled while `package_count` > 0 (D4); draft-only datasets aren't counted and still get core's 403 |
| Breadcrumb differs from Figma | Matches the v2 org pages (D14) |
| 34px fields vs Figma 37px | Matches 081 / 050 / 061 (D16) |

---

## 12. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | Field scope | Full v1 parity · Figma fields + hidden carry · Figma + fields still read by v2 | Figma fields visible (§5). Square logo, colours, topline and visualisation config are not editable and are carried (`customization` / `visualization_config` hidden inputs, `image_sq` kept server-side) |
| D2 | Logo | Both logos inside the custom reveal · rect only, always visible · core `image_url` | One always-visible, optional 'Organisation logo' = `customization.image_rect` |
| D3 | Create page | Migrate too · fork the form · branch v1/v2 on `action` | Migrate `organization/new.html` too, same form. H1 'Create an organisation'; v1 greeting ('Creating an organisation is easy.' + explanation) in `c-info-box`; no delete section; Cancel → `organization.index` |
| D4 | Delete / Restore | Keep + drawer + fix copy · keep v1 copy · drop; with datasets: disable (079) · core 403; trigger: button (079) · link to core confirm page | Bottom section: `c-divider`, then the `hdx-v2-org-edit__danger` row with an unnumbered `<h2>` 'Delete organisation' and a tertiary 'Delete organisation' button (inline `onclick` `hdxV2Drawer('delete-org-drawer').open()`, as 079). `c-drawer` `delete-org-drawer`: heading 'Delete organisation'; text 'Are you sure you want to delete this organisation?', or, when `group_dict.package_count` > 0, 'This organisation cannot be deleted while it still has datasets.' with Delete disabled; tertiary Cancel (`data-drawer-close`) + primary 'Delete' submitting `<form method="post" action="organization.delete">` with CSRF. Deleted orgs show `<h2>` 'Restore organisation' and a 'Restore organisation' button in its own `<form method="post" action="hdx_org.restore">`. v1 gates kept, read from `group_dict` (`data` is the posted form after a failed save) |
| D5 | Slug | Visible field on create · auto-fill page JS · visible on both · v1 behaviour; CKAN slug-preview modules · new component | v1 behaviour on create **and** edit through the new `c-slug-preview` (§4), auto-filling on `input`. Slugify from the already-loaded `$.url.slugify`; the page-loaded `v2-slug-preview-scripts` holds only the component JS |
| D6 | Logo uploader | Upload + remove + preview · full v1 parity incl. link · upload only | Full `hdx-image-upload` parity in the new `c-image-upload` (§4) |
| D7 | Linked logo URLs | Leave unrendered · fix | New resolver `hdx_organization_logo_url(value, qualified=False)` in `organization_helper.py`, also a template helper: http(s) passthrough, else `url_for('hdx_local_image_server.org_file', filename=…)`, empty → none. Used by `OrgMetaDao.__process_custom` (sq + rect), `organization_join.set_custom_rect_logo_url` (`qualified=True`, as before) and `dataset._process_customizations`, and by the form's logo preview |
| D8 | Required markers / Figma artefacts | Schema · Figma client-side · Figma + server | Schema: slug, description, org type; plus title (v1 `mandatory`, no server check). URL of organisation and logo optional. No reCAPTCHA; label 'Use custom organisation page' |
| D9 | Copy | Figma copy, keep subtitle · v1 copy · Figma everywhere | Figma copy: H1 / breadcrumb 'Edit org page'; sections '1. Basic Details', '2. Logo', '3. Optional user survey' (numbered, as v1); labels as §5; 'Cancel' (→ `organization.read`) and 'Submit'. `subtitle` blocks unchanged |
| D10 | Help text | Keep all · keep essential · drop all | None, Markdown hint included. v1 placeholders kept |
| D11 | Visualisation configuration | Hidden carry (XL) · type select only · select + sub-fields | No section at any width; `visualization_config` carried verbatim |
| D12 | Logo vs `custom_org` | Document only · render regardless of flag · auto-tick | `org-edit.js` ticks `#field-custom_org` on `image-upload:change`; Remove doesn't untick |
| D13 | Page shell | Signup shell as-is · generalise the signup shell · org hero + tabs | Signup shell as-is (081 D1). Org-edit rules in new `pages/org-edit.less` → `v2-org-edit-page-styles` |
| D14 | Breadcrumb | Figma (Home / {org} / page) · v2 org-page convention | Home / Organisations (`organization.index`) / {org} (`organization.read`) / 'Edit org page' (last, unlinked) |
| D15 | Errors | Summary always · per-field only · 079 pattern | 079 pattern: `alert.html` with `error_summary.values() | join(' ')` only when there are no field `errors`; `errors=errors.get(<name>)` on every field, including `org_url` and `user_survey_url`; the logo shows `image_rect_upload` (type) or `upload` (size, raised after the save) |
| D16 | Field size | `size='l'` · `size='m'` | `size='m'` (34px) everywhere; textarea at component height (081 D22 / D23) |
| D17 | Page JS | Port the v1 click handler · submit-event module | `fanstatic/v2/pages/org-edit.js` → `v2-org-edit-page-scripts`. It binds the form `submit` event (trim description, set `modified_at`, sync the hidden booleans) and `change` on the two booleans, and handles D12. Restore is its own form, so it is no longer hijacked |
| D18 | Logo handling | Keep v1 · fix | In `hdx_group_or_org_update`: when `clear_<field>` is set and no new value is posted, keep `''` instead of restoring the stored filename; when `<field>` is not posted, keep the stored value instead of `''`; delete old files only after a successful save: a replaced upload is removed by core's `Upload.upload()`, a Removed file next to the `upload()` calls. Stored keys are read with `.get()`. `hdx_group_or_org_create` unchanged |
| D19 | Views / flash | HDX view override with flash · core views | Core views unchanged; no success flash (parity) |

---

## 13. Files Affected

| File | Change |
|---|---|
| `templates/organization/edit.html` | v2 rewrite (§8) |
| `templates/organization/new.html` | v2 rewrite (§8, D3) |
| `templates/organization/new_organization_form.html` | Standalone v2 form (§5, D4, D15) |
| `templates/v2/components/slug-preview.html` | New `c-slug-preview` (D5) |
| `templates/v2/components/image-upload.html` | New `c-image-upload` (D6) |
| `hdx-styles/src/common/less/v2/components/slug-preview.less` | New |
| `hdx-styles/src/common/less/v2/components/image-upload.less` | New |
| `hdx-styles/src/common/less/v2/pages/org-edit.less` | New: section titles, danger section |
| `fanstatic/v2/components/slug-preview.js` | New |
| `fanstatic/v2/components/image-upload.js` | New |
| `fanstatic/v2/pages/org-edit.js` | New (D12, D17) |
| `fanstatic/webassets.yml` | `slug-preview.css`, `image-upload.css` / `.js` in `v2-components-*`; new `v2-slug-preview-scripts`, `v2-org-edit-page-styles`, `v2-org-edit-page-scripts` |
| `templates/v2/components.html` | Demo sections for both components |
| `ckanext-hdx_org_group/.../helpers/organization_helper.py` | Logo URL resolver (D7); logo fixes (D18) |
| `ckanext-hdx_org_group/.../plugin.py` | `hdx_organization_logo_url` template helper (D7) |
| `ckanext-hdx_org_group/.../helpers/org_meta_dao.py` | `__process_custom` uses the resolver |
| `ckanext-hdx_org_group/.../views/organization_join.py` | `set_custom_rect_logo_url` uses the resolver |
| `ckanext-hdx_package/.../views/dataset.py` | `_process_customizations` uses the resolver |
| `ckanext-hdx_org_group/.../tests/` | `test_controller/test_custom_org_controller.py`: v2 edit/create render and gating, unchanged-form save keeps every extra (and unticking the custom page keeps the colours); `test_actions.py`: Remove, failed save keeps the file, Restore keeps the logos; `test_helpers.py`: resolver |
| `llm_docs/redesign/PROGRESS.md` | Migrated-pages row; new components |
| `llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Edit org key-page entry; `slug-preview.js` in the jQuery exceptions |
| `llm_docs/redesign/CONVENTIONS.md` | `slug-preview.html` and `image-upload.html` in the form-field components list |

Template, LESS, JS and bundle paths are relative to `ckanext-hdx_theme/ckanext/hdx_theme/`.

---

## 14. Verification Checklist

- [ ] Edit and create render on v2 for a sysadmin. Edit renders for an org admin without FTS ID, user survey or
      delete section. Editors and members get 403.
- [ ] Saving an unchanged edit form leaves every extra identical: colours, topline, `visualization_config`,
      `image_sq`, and FTS ID / user survey for an org admin.
- [ ] Unticking 'Use custom organisation page' keeps the colours and topline.
- [ ] Slug, create: typing or pasting the title fills the slug until the slug is typed into. Output matches v1
      `$.url.slugify` for accented, symbol and repeated-space input. A title with no slug characters reveals the
      slug field with the browser's message on submit.
- [ ] Slug, edit: the preview shows, and Edit reveals and focuses the field. A rename redirects to the new URL and
      the datasets are re-indexed.
- [ ] Logo upload, link and remove work. An external URL renders in the hero, on the dataset page and on
      request-access. Remove leaves no broken image, and neither does a failed save after Remove or upload.
      Uploads disabled → URL field only. Choosing a logo ticks the custom page.
- [ ] An empty description or org type and an http `org_url` show per-field errors; the summary appears only for
      errors without a field.
- [ ] Delete drawer (sysadmin, active org): with datasets → message, Delete disabled; empty org → deleted, flash on
      the index. Restore on a deleted org → org page, both logos kept.
- [ ] `<title>` / Mixpanel page titles and `analyticsInfo` org name/id unchanged; 'org create' still sent.
- [ ] No Bootstrap classes and no `colorpicker`, `custom-org-creation`, `image-upload` or
      `organization-create-styles` assets in the rendered HTML.
- [ ] Existing tests pass: `test_custom_org_controller`, `test_org_custom_fields`, `test_closed_organization`,
      `test_auth`, `test_actions`. The new tests pass too.
- [ ] Keyboard walkthrough: slug Edit, Upload / Link / Remove, drawer open / confirm / Escape.
- [ ] Visual check at SM, MD, XL and XXL against the three exports.
