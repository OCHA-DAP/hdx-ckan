# 092 — Edit Location Page v2

**Scope:** migrate the Edit Location page (`group.edit`) from the v1 `page.html` shell, Bootstrap and
`macros/form.html` to v2. The sysadmin-only Create Location page (`hdx_group.new`) renders the same form and is
migrated too (D11). The structure follows 082 (Edit Organisation), the closest existing v2 form. One backend change:
an `IGroupController.delete` hook that invalidates the group caches (D13).

**Excluded:**
- the core `EditGroupView` / `CreateGroupView` / `DeleteGroupView` views, the group schema and validators, and the
  auth functions;
- the location page itself (063) and the v1 group templates other pages still extend.

No route, permission or field name changes. The `<title>` / Mixpanel page titles change (D5).

**Figma sources:** `xl-edit-location-page.html`, `sm-edit-location-page.html` (no MD export)

---

## Context

The v2 location page (`country/country.html`) passes an "Edit location page" entry to `v2/components/page-header.html`
(`header_actions`). It is gated by `h.check_access('group_update')` and links to `group.edit`.

That page is still v1:
- the old header, footer and old-design banner;
- a Bootstrap form with a visually hidden H1 'Edit Group';
- the `<title>` '{location} - Organizations';
- no inline errors on the HDX fields.

The Figma exports show a single 580px column with the same outer layout as the 082 exports. There are no section
titles, no sidebar and no tabs.

---

## 1. Existing Implementation Audit

### Routes / views (unchanged — reference only)

| Screen | Route | View | Template chain |
|---|---|---|---|
| Edit | GET/POST `/group/edit/<id>` | core `group.edit` (`EditGroupView`, `ckan/views/group.py`) | `group/edit.html` → HDX `group/base_form_page.html` (`ckan_extends`) → core `group/base_form_page.html` → HDX `group/edit_base.html` → v1 `page.html` |
| Create | GET/POST `/group/new` | `hdx_group.new` = core `CreateGroupView` (`ckanext-hdx_org_group/.../views/group.py`) | core `group/new.html` (sidebar `group/snippets/helper.html` "What are Locations?") |
| Delete | GET/POST `/group/delete/<id>` | core `DeleteGroupView` | core `group/confirm_delete.html` (no-JS GET only) |

HDX registers no edit or delete route for groups. `HDXGroupPlugin` (`lib_plugins.DefaultGroupForm`) overrides no
template method, so `group_form` returns `group/new_group_form.html` for both create and edit. The view renders it
into `form` and passes `data`, `group_dict`, `errors`, `error_summary` (`None` on GET), `action` ('new' / 'edit') and
`group_type`.

**Edit `_prepare`:** `group_show` first (missing → 404), then `check_access('group_update')` (→ 403).

**Edit POST:**
- It parses `request.form` + `request.files`, sets `data_dict['id']` to the URL id and sets
  `allow_partial_update = True`.
- It then calls `group_update`.
- A slug change triggers `_force_reindex`, which reindexes every dataset of the location synchronously.
- `ValidationError` re-renders with `errors` / `error_summary`; `data` is then the posted payload.
- Success redirects to `group.read` (the v2 location page) with **no flash**.

**Create:**
- It reuses the same form with `action='new'`: all fields, no Delete, and the label 'Create Group'.
- Gated by `group_create`, which only sysadmins pass (`user_create_groups = false`).
- No v2 or v1 page links to it.

### Update action

`group_update` → `hdx_group_update` → `_run_core_group_org_action(…, core.update.group_update)`
(`ckanext-hdx_org_group/.../helpers/organization_helper.py`). The org-only `hdx_group_or_org_update` (customization,
logos) is never called for groups.

The core path:
1. Validates with `HDXGroupPlugin.update_group_schema()`.
2. Runs the core uploader hook for `image_url`. The form has no file input, so it does nothing.
3. Calls `group_dict_save`, then `IGroupController.edit` → `HDXGroupPlugin.edit` → `invalidate_cache_for_groups`
   (`cached_group_list`, `cached_group_iso_to_title`).
4. Commits, then runs a synchronous `lunr.build_index()`. A "changed group" activity is recorded.

**⚠ Extras are a full replace.** When any extra is posted, `group_dict_save` (`ckan/lib/dictization/model_save.py`)
deletes every stored extra that isn't in the payload. `allow_partial_update` does not protect extras.
- The v1 form always posts `language_code`, `relief_web_url`, `hr_info_url`, `geojson`, `activity_level`,
  `key_figures` and `data_completeness`, so the extras list is never empty.
- Any other stored key is therefore wiped on the first form save. This includes the legacy `custom_loc`,
  `customization` and `featured_section`, which are commented out of the schema.
- `alert_bar_title` / `alert_bar_url` use `ignore_empty`, so clearing them removes the extra, by design.
- API `group_patch` and `group_update` calls without extras are not affected.

### Schema (`HDXGroupPlugin._modify_group_schema` + core `default_update_group_schema`)

| Field | Validators |
|---|---|
| `name` | core update: `ignore_missing`, `not_empty`, `group_name_validator` (uniqueness only; `name_validator` runs on create only) |
| `title`, `description`, `image_url` | core: `ignore_missing`, `unicode_safe` (empty accepted) |
| `language_code`, `relief_web_url`, `hr_info_url`, `geojson`, `activity_level`, `key_figures`, `data_completeness` | `ignore_missing`, `convert_to_extras` (no format check; `geojson` is not checked as JSON) |
| `alert_bar_title` | `hdx_clean_field_based_on_other_field_wrapper('alert_bar_url')` (blanked when the URL is empty), `ignore_empty`, `unicode_only`, `hdx_check_string_length_wrapper(40)` ("The text shouldn't be longer than 40 chars"), `convert_to_extras` |
| `alert_bar_url` | `ignore_empty`, `unicode_only`, `hdx_is_url` ("Value is not a URL"; http(s)/ftp(s) only), `convert_to_extras` |

On show, `key_figures` uses `active_if_missing`, so an unset value reads as `'active'`.

The only server-required field on edit is `name`.

### Permissions

| Item | Rule |
|---|---|
| Page + save | `group_update`. Core grants sysadmins and group admins; HDX's `group_member_create` auth refuses members for locations, so in practice sysadmins only |
| Delete | `h.check_access('group_delete', {'id': data.id})`; `user_delete_groups = false`, so sysadmins only |
| Every field | Any user who passes `group_update`; there are no sysadmin-only fields |

### v1 form (`group/new_group_form.html` extending `group/snippets/group_form.html`)

**Form element:**
- `<form id="create-group-form" class="dataset-form form-horizontal" method="post" data-module="basic-form">` with
  `h.csrf_input()`.
- `basic-form` lives only in the core `base/ckan` bundle, which HDX never loads, so it does nothing.

**Error summary:** `form.errors(error_summary)`.

**Fields:** no sections, no help text except the Markdown hint, no native `required`.

| Field | Label | Widget | Id |
|---|---|---|---|
| `title` | 'Title' | `form.input`, `slug-preview-target`, placeholder 'My Group' | `field-title` |
| `name` | 'URL' | `form.prepend` `/group/`, `slug-preview-slug` (prefix = domain, placeholder `<group>`), placeholder 'my-group' | `field-url` |
| `description` | 'Description' | `form.markdown` (Markdown hint link), placeholder 'A little information about my group...' | `field-description` |
| `image_url` | 'Image URL' | `form.input type=url`, placeholder 'https://example.com/my-image.jpg' | `field-image-url` |
| `language_code` | 'Language Code' | raw text input | `field-language_code` |
| `relief_web_url` | 'Relief Web URL' | raw text input | `field-relief_web_url` |
| `hr_info_url` | 'HR.info URL' | raw text input | `field-hr_info_url` |
| `alert_bar_title` | 'Alert Bar Title' | raw text input, no `maxlength` | `field-alert_bar_title` |
| `alert_bar_url` | 'Alert Bar URL' | raw text input | `field-alert_bar_url` |
| `geojson` | 'Geojson' | textarea `.taller-textarea` | `field-geojson` |
| `activity_level` | 'Activity Level' | `form-select`: Inactive / Active | `field-activity-level` |
| `key_figures` | 'Key Figures' | `form-select`: Inactive / Active | `field-key-figures` |
| `data_completeness` | 'Data Grid Availability' | `form-select`: Inactive / Active | `field-data-completeness` |

**Actions:**
- **Delete:** left-floated red, edit only. It is `<a href="group.delete" data-module="hdx_confirm-action">`, a
  Bootstrap modal with heading 'You are deleting location' and body 'Are you sure you want to delete this
  location?'.
- **Save:** primary submit `name=save`, labelled 'Update Group' / 'Create Group'.

**Bundle:** `hdx_theme/group-form-scripts`. It has no files of its own and only pulls in
`organization-form-styles` CSS. The slug-preview modules come from the `hdx_theme/ckan` bundle every page loads.

Nothing outside these two templates references `create-group-form`, `create-loc-btn` or the HDX field ids.

### Delete flow

1. `hdx_confirm-action` builds a POST form with CSRF.
2. `DeleteGroupView.post` → `group_delete` → core `_group_or_org_delete`. This marks every membership of the location
   deleted, so datasets lose the location; it does not reindex them. Lunr is then rebuilt.
3. Flash 'Group has been deleted.' → `group.index` (the v2 locations list, which renders flashes).

Gaps:
- There is no restore route; only an API `group_patch` can restore, and the memberships stay deleted.
- `HDXGroupPlugin` has no `IGroupController.delete`, so `cached_group_list` keeps the deleted location on the
  locations list and homepage until the cache expires.
- After a failed save, `data.id` is the URL id (the name). A delete from that re-rendered page passes the name to the
  membership query, so the memberships are not deleted.
- Without JS the link opens core `group/confirm_delete.html`. That page's Cancel is a POST submit, and
  `DeleteGroupView.post` doesn't check for it, so it deletes too.

### Where the fields are read on v2

| Field | Consumer |
|---|---|
| `activity_level` | `GroupIndexReadLogic` `is_hrp` (HRP chip, filter, KPI on the locations list), `browse.js` map, homepage `h.hdx_get_locations(hrp=True)` |
| `data_completeness` | `country_helper.get_template_data` → the location page data grids |
| `alert_bar_title` / `alert_bar_url`, `key_figures` | Mobile `light/group/read.html` only (the v2 blocks in `country.html` are commented out) |
| `description`, `image_url` | Legacy `group/read_base.html` / `group/snippets/info.html` and core `/group/about/<id>` only |
| `geojson` | No reader; still serialised into `cached_group_list` |
| `language_code`, `relief_web_url`, `hr_info_url` | No reader |

### Analytics

- The edit chain sets no `analytics_*` block, so `analyticsInfo` carries no location.
- The `subtitle` block comes from HDX `group/edit_base.html`: `{{ c.group_dict.display_name }} - {{ _('Organizations') }}`.
  It feeds both the `<title>` and the Mixpanel "page view" `page title`.
- There is no server-side sender for group create, update or delete, and no tracking attribute on the header action.

### Tests

- `ckanext-hdx_org_group/.../tests/test_auth.py` → `TestGroupAuth`: create, edit, delete and member auth, asserted at
  action level.
- `ckanext-hdx_theme/.../tests/test_logic/test_caching.py`: the cache is invalidated on `group_create`.
- Nothing covers the edit or delete views, the form markup or the extras wipe. There is no Cypress coverage.

### v1 bugs and quirks

- The HDX fields render no inline errors; only the top summary shows them.
- The selects have no empty option, so an unset `activity_level` / `data_completeness` displays and saves as 'Inactive'.
  `key_figures` displays 'Active' (`active_if_missing`).
- Breadcrumb Home / Groups / {location} / Manage, with structured-data positions 2, 2, 4.
- The `<title>` says 'Organizations'; the H1 'Edit Group' is hidden; the save label says 'Group'.
- On edit, `custom_fields` calls `super()`, which prints the legacy extras loop inside an HTML comment.
- A `dataset_fields` override targets a block the parent has commented out.
- Ids mix `_` and `-`. URL fields are `type=text` except `image_url`. `alert_bar_title` has no `maxlength`.

---

## 2. Figma Analysis

### Layout

```
breadcrumb       Home / Afghanistan / Edit location page    (SM: #fafbfb row, 16px gutters)
.intro-hdx       padding 96 48 (XL) · 24 16 (SM)
                 title → form gap 40 (XL) · 24 (SM); form → actions gap 40 (XL) · 24 (SM)
├── h1           "Edit location page", Merriweather Bold, 32px XL · 24px SM, #101212
└── form         580px XL · full width SM; fields gap 20; no section titles
      Title *                    text, 37px
        [data.humdata.org/group/][ slug input ]   prefix cell + input, no label, under Title
      Description *              textarea, grows with content
      Image URL *                text
      Language Code              text
      Reliefweb URL *            text
      HR.Info URL *              text
      Alert Bar Title *          text
      Alert Bar URL *            text
      Geojson                    textarea, grows with content (full GeoJSON shown)
      Activity Level *           "Select ▾" dropdown, 34px, drop shadow
      Key Figuresl *             "Select ▾"
      Data Grid Availability *   "Select ▾"
    reCAPTCHA "I'm not a robot"
    [Delete] [Update Location]   right-aligned, gap 16
```

### Token map

| Figma | v2 |
|---|---|
| H1 Merriweather 24 / 32px | `.hdx-v2-signup-form-page__heading` → `.hdx-page-title-scale()` (24 / 28 / 32) |
| Label 16px/500 `#2f3536` | `text-field` / `select` label |
| Asterisk `#c44536` | component `required` marker (`--hdx-error-5`), `aria-hidden` |
| Input 37px, `#d8e0e1` border, 2px radius | `text-field.html` `size='m'` (34px, 082 D16) |
| Textarea | `text-field.html` `multiline=True` |
| Select 34px, drop shadow | `select.html` |
| Delete: white, `#d8e0e1` border, drop shadow | `button.html style='tertiary'` |
| Update Location `#1862d8` | `button.html style='primary'` |
| 580px column | signup `__card` 100% / 80% / 50% |
| SM page `#fafbfb` | signup shell is white (082 uses the same shell at SM) |

### Artefacts and inconsistencies

- **reCAPTCHA:** visible, as in the 082 exports. No captcha exists in v1 or the schema.
- **"Key Figuresl":** a typo for 'Key Figures'.
- **Sample values:** 'IOM' in Language Code; `psdata.un.org` URLs; a DRC GeoJSON on Afghanistan.
- **SM leftovers:** hidden (`display:none`) layers copied from a dashboard frame: the user-dashboard sub-menu,
  "Results per page" / "Sort by" controls and a count next to the title.
- **Required markers:** Figma marks ten fields required; the server requires only `name` (§1 Schema).
- **Missing from Figma:** the slug label, Cancel, every help text, error states, the delete confirmation and the
  create variant.

### XL vs SM

Same content in the same order, single column at both sizes:

| | SM | XL |
|---|---|---|
| Side padding | 16px | 48px |
| Top padding | 24px | 96px |
| Title size | 24px | 32px |
| Title → form, form → actions | 24px | 40px |
| Fields | full width | 580px |

Buttons stay side by side and right-aligned. There are no drawers or overlays.

---

## 3. Current vs Target

| Aspect | v1 | Target | Basis |
|---|---|---|---|
| Base / layout | v1 `page.html`, Bootstrap, `.create-org` | `v2/page.html`, signup shell | D1 |
| Breadcrumb | Home / Groups / {location} / Manage | Home / Locations / {location} / Edit location page | D2 |
| H1 | hidden 'Edit Group' | 'Edit location page' (create: 'Create location') | D4, D11 |
| `<title>` / Mixpanel page title | '{location} - Organizations' (create: 'Create a Group') | 'Edit Location' (create: 'Create Location'); edit also fills the group analytics blocks | D5 |
| Sections | none | none (Figma) | D1 |
| Slug | `form.prepend` + slug-preview modules | `c-slug-preview` | D8 |
| Labels | v1 copy | Figma copy; 'ReliefWeb URL', 'HR.info URL'; 'Key Figures' | D4 |
| Required markers | none | Title, URL, the three selects | D6 |
| Selects | Inactive / Active, no placeholder | unchanged | D7 |
| Textareas | `.taller-textarea` GeoJSON | component height | D9 |
| Help text | Markdown hint | none | D10 |
| Placeholders | 'My Group', 'my-group', '…about my group...', slug preview `<group>` | reworded to location | D14 |
| Errors | summary list; HDX fields unbound | 082 D15: per-field on every field, summary `c-alert` only when no field error | D1 |
| Actions | Delete (left, red link) + 'Update Group' | Delete + 'Update Location', right-aligned (create: 'Create Location' only) | D3 |
| Delete confirm | Bootstrap modal (`hdx_confirm-action`) | `c-drawer` POST form; gate reads `group_dict` | D3 |
| Location list after a delete | stale until `cached_group_list` expires | updated at once | D13 |
| reCAPTCHA | none | none (artefact) | §2 |
| Views, schema, auth, routes, success redirect (no flash) | — | unchanged | §9 |

Removed from the page: the `group-form-scripts` bundle, `hdx_confirm-action`, `form.errors`, every Bootstrap class and
the commented-out extras leak.

---

## 4. Component Mapping

No new component. Every element maps to an existing v2 component or the 082 shell.

| Element | Component |
|---|---|
| Breadcrumb | `v2/components/breadcrumb.html` (D2) |
| Shell: H1, field column, actions row | signup shell `.hdx-v2-signup-form-page` > `__card` (`__heading`, `__fields`, `__actions`), `v2-signup-page-styles` (D1) |
| Title, Image URL, Language Code, ReliefWeb URL, HR.info URL, Alert Bar Title, Alert Bar URL | `v2/components/text-field.html` `size='m'`, each in a caller `c-form-field` wrapper (082 pattern) |
| Description, Geojson | `text-field.html` `size='m'`, `multiline=True` (D9) |
| URL slug | `v2/components/slug-preview.html`: `prefix` = `h.url_for('group.read', id='', qualified=true)` without scheme, `placeholder='my-location'`, `preview_placeholder='<location>'` (D14), `target_id='field-title'`; page-loaded `v2-slug-preview-scripts` (D8) |
| Activity Level, Key Figures, Data Grid Availability | `v2/components/select.html`, `options={'inactive': 'Inactive', 'active': 'Active'}` (D7) |
| Error summary | `v2/components/alert.html` (082 D15) |
| Delete trigger / Update Location | `button.html` (`tertiary` / `primary` `button_type='submit'`, `size='l'`) (D3) |
| Delete confirm | `v2/components/drawer.html` + `.c-drawer-form` (`__text`, `__buttons`), as 082 `delete-org-drawer` (D3) |

**Assets:**
- **Styles:** `v2-signup-page-styles` only; no location-specific LESS (D1, D3).
- **Scripts:** `v2-slug-preview-scripts` only. v1 has no other form JS, so no page JS is needed.

---

## 5. Form Contract

### Visible fields (Figma order)

| Field | Label | Component | Required | Notes |
|---|---|---|---|---|
| `title` | 'Title' | text-field | ✓ | `id='field-title'`; slug target; placeholder 'My location' (D14) |
| `name` | 'URL' | slug-preview | ✓ | `id='field-url'`; prefix `<domain>/group/`; placeholder 'my-location' (D14) |
| `description` | 'Description' | text-field multiline | — | placeholder 'A little information about my location...' (D14) |
| `image_url` | 'Image URL' | text-field `type='url'` | — | as v1; placeholder 'https://example.com/my-image.jpg' (D14) |
| `language_code` | 'Language Code' | text-field | — | |
| `relief_web_url` | 'ReliefWeb URL' | text-field | — | |
| `hr_info_url` | 'HR.info URL' | text-field | — | |
| `alert_bar_title` | 'Alert Bar Title' | text-field | — | no `maxlength`; the 40-char limit is a server error (D10) |
| `alert_bar_url` | 'Alert Bar URL' | text-field | — | |
| `geojson` | 'Geojson' | text-field multiline | — | |
| `activity_level` | 'Activity Level' | select | ✓ | |
| `key_figures` | 'Key Figures' | select | ✓ | |
| `data_completeness` | 'Data Grid Availability' | select | ✓ | |
| Submit `name=save` | 'Update Location' (create: 'Create Location') | button | | |

Every field gets `errors=errors.get(<name>)`. The selects carry `required` but can't be empty (D7).

### Kept verbatim

- `method="post"`, `h.csrf_input()`, every field `name`, and the slug ids `field-title` / `field-url`.
- `enctype` stays the default: the form has no file input.

### Free to change

The form id `create-group-form`, the class `create-loc-btn` and the mixed-style field ids have no references
outside the two v1 templates. The target keeps the form id and uses `field-<name-with-hyphens>` throughout.

### Data on re-render

As 082 §6:
- Fields read `data`, the posted payload after a failed save.
- The breadcrumb, the delete gate, the drawer and its action URL read `group_dict`. This also fixes the
  name-vs-id delete bug (§1 Delete flow).

---

## 6. Flow & States

```
Location page "Edit location page" ─▶ GET edit ─▶ Update Location ─┬─ valid ─▶ 302 group.read (no flash, unchanged)
                                                                  └─ invalid ─▶ re-render: per-field errors (+ summary if no field error)
Delete ─▶ drawer ─▶ Delete POST group.delete ─▶ caches invalidated (D13) ─▶ core: flash + group.index
/group/new ─▶ Create Location ─▶ 302 group.read of the new location (unchanged)
```

| State | Behaviour |
|---|---|
| Edit, JS on | Slug collapsed to "URL: …/group/<slug> [Edit]"; the title does not auto-fill it (D8) |
| Create, empty | Title typing fills the slug until the slug is typed into |
| Re-render with a slug error | Slug field visible with its error; no preview |
| Re-render with any other error | Error under the field; summary `c-alert` only when no field has an error |
| Alert Bar Title without URL | Saved as empty (server rule, unchanged) |
| Not a sysadmin | 403 from the view; the location page hides the action |
| JS off | Slug field visible; no delete drawer (as 082) |

---

## 7. Responsive Behaviour

The same as 082 §7 with no location-specific breakpoint:
- **Column (`__card`):** 100% SM, 80% MD, 50% XL.
- **Title:** 24 / 28 / 32px.
- **Page margins:** `--hdx-space-8`, then `--hdx-space-24` at XL.
- **Fields:** full column width, stacked.
- **Actions:** a right-aligned row at every size.

Figma's 96px XL top padding and the 40 / 24px gaps come out as the shell's spacing, as accepted in 082.

---

## 8. Template Strategy

- **`group/edit.html`:** rewritten in place to extend `v2/page.html`.
  - Layout: `outer_row_class='hdx-v2-signup-outer-row'`, `breadcrumb_row_class='hdx-v2-breadcrumb-row--white'`,
    `content_class='hdx-v2-content-columns__content'`.
  - Blocks:
    - `subtitle` 'Edit Location';
    - `analytics_group_names` / `analytics_group_ids` from `group_dict` (name / id), as `country/country.html`;
    - `breadcrumb_items`: Locations (`hdx_group.index`) / `group_dict.display_name` (`group.read`) / 'Edit location
      page';
    - `styles` (`v2-signup-page-styles`) and `scripts` (`v2-slug-preview-scripts`).
  - `primary` renders `<div class="hdx-v2-signup-form-page">{{ form | safe }}</div>`.
- **`group/new.html`:** a new HDX override with the same layout, `styles`, `scripts` and `primary`.
  - `subtitle` 'Create Location'; breadcrumb Locations / 'Create location'; no analytics blocks.
  - It replaces core `group/new.html`, so the v1 "What are Locations?" sidebar goes.
- **`group/new_group_form.html`:** becomes the standalone v2 form. It no longer extends
  `group/snippets/group_form.html` and branches on `action` for the H1, the submit label and the delete trigger.
- **No `v2` gate:** only the core group create/edit views render these templates.
- **Left untouched:**
  - `group/edit_base.html`, still extended by `group/members.html`;
  - `group/base_form_page.html`;
  - `group/snippets/group_form.html`, which has no child once the form is standalone (D11);
  - `group/snippets/helper.html` ('What are Locations?'), which no rendered template includes any more;
  - `hdx_confirm-action.js` and the `group-form-scripts` bundle.

---

## 9. Functionality & Analytics Preservation

| Item | Status |
|---|---|
| Routes, methods, success redirect, `_force_reindex` on slug change, no success flash | Unchanged (core views) |
| Auth: `group_update`, `group_delete` | Unchanged |
| Schema, validators, field names, the posted extras set | Unchanged; the extras wipe behaves as v1 (D12) |
| Header action on the location page | Unchanged |
| Delete endpoint, flash and redirect | Unchanged; new confirm UI (D3) |
| `<title>` / Mixpanel page title | Changed: 'Edit Location', 'Create Location' (D5) |
| `analyticsInfo` | Edit now carries the location name / id (D5) |
| Backend | `HDXGroupPlugin.delete` invalidates the group caches (D13) |

---

## 10. Accessibility

- **Fields:** every field has an `id` and its label gets `for`. Asterisks are `aria-hidden`, backed by native
  `required`.
- **Slug preview:** "Edit" is a `<button type="button">` with `aria-controls` and `aria-expanded`; revealing the field
  moves focus to the input.
- **Error summary:** `c-alert` error (`role="alert"`).
- **Delete drawer:** existing `c-drawer`: `role="dialog"`, `aria-modal`, focus trap, Escape closes, focus returns to
  the trigger.
- **Buttons vs links:** Delete and Update Location are buttons; the breadcrumb is the only navigation back.
- **Known component gap (not fixed here, as 082 §10):** `text-field.html` and `select.html` set neither `aria-invalid`
  nor an `aria-describedby` reference to their error span.

---

## 11. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| A field missing from the POST deletes its extra | The v2 form posts the v1 field set; a test saves an unchanged form and compares extras |
| Legacy extras are wiped on save | Same as v1 (D12) |
| Slug rename breaks links and reindexes every dataset of the location synchronously | Slug collapsed behind Edit (D8); behaviour unchanged |
| Large GeoJSON in the textarea | Same payload as v1; component height, scrolls inside (D9) |
| Alert Bar Title over 40 characters | Server error under the field (D10) |
| Delete leaves the location in `cached_group_list` until expiry | `HDXGroupPlugin.delete` (D13) |
| Delete removes every dataset membership; there is no restore | Drawer copy states it (D3) |
| Breadcrumb differs from Figma | Matches the v2 location page (D2) |
| 34px fields vs Figma 37px | Matches 082 D16 |

---

## 12. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | 082 precedents | Adopt all · diverge on named items | Adopt all: signup shell, white at every size (Figma's `#fafbfb` SM background dropped); `size='m'` fields; 082 D15 errors (`alert.html` with `error_summary.values() \| join(' ')` only when there are no field `errors`; `errors=errors.get(<name>)` on every field); no success flash; no section titles |
| D2 | Breadcrumb | Figma (Home / {location} / page) · v2 location convention | Home / Locations (`hdx_group.index`) / {location} (`group.read`) / 'Edit location page' (last, unlinked); create: Home / Locations / 'Create location' |
| D3 | Actions / Delete | Figma row · 082 Cancel + Submit + bottom section · Figma row + Cancel; drawer text v1 · v1 + consequence | Figma row in `__actions`, right-aligned: tertiary `size='l'` 'Delete' (edit only, inline `onclick` `hdxV2Drawer('delete-location-drawer').open()`, as 082) then primary `size='l'` submit. No Cancel. `c-drawer` `delete-location-drawer`, title 'Delete location', text 'Are you sure you want to delete this location? Datasets will no longer be tagged with this location. This can't be undone.'; tertiary Cancel (`data-drawer-close`) + primary 'Delete' submitting `<form method="post" action="group.delete">` with CSRF, outside the main form. Gate `action == 'edit' and h.check_access('group_delete', {'id': group_dict.id})`; the action URL uses `group_dict.id` |
| D4 | Copy | Figma · v1 · brand spelling | Figma copy: H1 'Edit location page', submit 'Update Location', labels as §5; brand spelling 'ReliefWeb URL' and 'HR.info URL'; typo fixed to 'Key Figures' |
| D5 | `<title>` and analytics | Keep · 'Edit Location' · '{location} - Edit location page'; with or without group analytics blocks | `subtitle` 'Edit Location' (create: 'Create Location'). Edit sets `analytics_group_names` / `analytics_group_ids` from `group_dict`, as `country/country.html` does. The Mixpanel "page view" `page title` values change accordingly |
| D6 | Required markers | Schema-driven · Figma client-side · Figma + server | Title, URL slug and the three selects carry `required`. Description, Image URL, ReliefWeb URL, HR.info URL, Alert Bar Title / URL, Language Code and Geojson stay optional |
| D7 | Select empty state | v1 parity · Figma 'Select' placeholder + required | v1 parity: options Inactive / Active, no placeholder; `selected` = the stored value, so an unset value shows the first option ('Active' for Key Figures, via `active_if_missing`) |
| D8 | Slug | `c-slug-preview` · Figma always-visible prefixed field | `c-slug-preview` (§4); no `text-field` extension |
| D9 | Textarea height | Component height · extend `text-field` · page LESS | Component height for Description and Geojson; no component or page LESS change |
| D10 | Help text / constraints | None · `maxlength` only · `maxlength` + hints | None: no hints, no Markdown note, no `maxlength`; v1 input types kept. The 40-char limit and the URL rule surface as server errors under their fields |
| D11 | Create Location | Migrate · edit only · migrate and delete the orphan | Migrate `/group/new` with the same form: H1 'Create location', submit 'Create Location', no delete; new HDX `group/new.html` (§8). `group/snippets/group_form.html` left untouched |
| D12 | Extras wipe | Parity · hidden-carry · measure first | Parity: the v2 form posts the v1 field set; unposted legacy extras are deleted on save, as today |
| D13 | Delete cache lag | Document only · fix | `HDXGroupPlugin.delete(self, country)` (`IGroupController`) calls `invalidate_cache_for_groups` with `ignore_auth`, mirroring `edit`. Core calls it inside `_group_or_org_delete`, before the commit |
| D14 | Placeholders | v1 verbatim · reword to location · format examples only · none | v1 placeholders kept, reworded to location: Title 'My location', slug 'my-location', Description 'A little information about my location...', Image URL 'https://example.com/my-image.jpg'; slug preview token `<location>` |

---

## 13. Files Affected

| File | Change |
|---|---|
| `templates/group/edit.html` | v2 rewrite (§8) |
| `templates/group/new.html` | New HDX override, v2 (§8, D11) |
| `templates/group/new_group_form.html` | Standalone v2 form (§4, §5, D3) |
| `ckanext-hdx_org_group/.../plugin.py` | `HDXGroupPlugin.delete` (D13) |
| `ckanext-hdx_org_group/.../tests/test_views.py` | Extend `TestViews`: edit and create render on v2 for a sysadmin, 403 for a regular user; a failed save keeps the drawer on the location id; an unchanged edit-form save keeps every posted extra; a POST delete invalidates the group caches |
| `ckanext-hdx_theme/.../tests/test_logic/test_caching.py` | `test_group_cache_invalidation_on_change` also asserts the invalidation on `group_delete` |
| `llm_docs/redesign/PROGRESS.md` | Migrated-pages row |
| `llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Edit / create location key-page entry |

Template paths are relative to `ckanext-hdx_theme/ckanext/hdx_theme/`. No LESS, JS or `webassets.yml` change.

---

## 14. Verification Checklist

- [ ] Edit and create render on v2 for a sysadmin; a regular user gets 403 on both.
- [ ] Saving an unchanged edit form leaves every form field's stored value identical, including the alert bar pair.
- [ ] Slug, edit: the preview shows, and Edit reveals and focuses the field. A rename redirects to the new URL.
- [ ] Slug, create: typing the title fills the slug until the slug is typed into.
- [ ] Errors: a duplicate slug, an Alert Bar Title over 40 characters (with a URL) and an invalid Alert Bar URL each
      show under their field; the summary `c-alert` appears only for errors without a field.
- [ ] Alert Bar Title without a URL saves as empty (server rule).
- [ ] The selects show the stored values; an unset Activity Level shows 'Inactive' and Key Figures 'Active'.
- [ ] Delete drawer: copy, Cancel, Escape, focus return. Delete lands on the locations list with the flash, and the
      location is gone from the list at once. A delete after a failed save still removes the memberships.
- [ ] `<title>` / Mixpanel page titles 'Edit Location' / 'Create Location'; `analyticsInfo` carries the location on
      edit.
- [ ] No Bootstrap classes and no `group-form-scripts` or `hdx_confirm-action` assets in the rendered HTML.
- [ ] Existing tests pass: `TestGroupAuth`, `test_caching`, `test_views`. The new tests pass too.
- [ ] Keyboard walkthrough: slug Edit, drawer open / confirm / Escape.
- [ ] Visual check at SM, MD, XL and XXL against the two exports.

