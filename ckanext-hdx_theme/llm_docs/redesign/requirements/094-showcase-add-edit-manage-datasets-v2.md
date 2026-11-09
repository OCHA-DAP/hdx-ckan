# 094 — Showcase Add / Edit / Manage Datasets v2

**Scope:** migrate the three showcase management pages from the v1 `page.html` shell, Bootstrap and
`macros/form.html` to v2:
- Add showcase (`showcase_blueprint.new`);
- Edit showcase (`showcase_blueprint.edit`);
- Manage datasets (`showcase_blueprint.manage_datasets`).

The structure follows 082 / 092 (signup shell). Changes outside the showcase templates:
- the Request Access "reveal on select value" logic promoted to `utils.js` and reused by the showcase form (D9);
- the Label field removed: `dataviz_label` is no longer required in the gallery, and the Dataviz Gallery card shows the
  title (D19).

**Excluded:**
- the upstream `ckanext-showcase` views, actions, schema and templates (`src/ckanext-showcase`), and the HDX showcase
  auth functions and update action (`ckanext-hdx_dataviz`); the HDX schema wrapper changes only for `dataviz_label`
  (D19);
- the showcase read page (`/showcase/<id>`), the `/showcase` list, `/dataset/showcases/<id>` and the showcase admin
  pages, which stay v1;
- the v2 dataset page Showcases section (D16).

No URL or permission changes; the Label field goes (D19). The `<title>` / Mixpanel page titles change (D3).

**Figma sources:** `xl-showcase-add.html`, `xl-showcase-edit.html`, `xl-showcase-edit-manage-datasets.html` (no MD or
SM export)

---

## Context

Showcases are packages of `type='showcase'` that link to an external visualisation and group the datasets it uses.
Sysadmins and carousel managers also curate them into the Dataviz Gallery (`/dataviz-gallery`).

All three management pages are still v1:
- the old header, footer and old-design banner;
- Bootstrap columns and title-case copy ('Create a Showcase', 'Update Showcase');
- a Bootstrap tab bar on Edit and Manage;
- two side-by-side checkbox tables on Manage datasets.

The Figma exports use the same outer frame as the 082 / 092 exports: a single 580px column with a Merriweather title.
Edit and Manage add a tab row; Manage replaces the tables with dataset cards that each carry their own action.

---

## 1. Existing Implementation Audit

### Routes / views (unchanged — reference only)

All routes belong to the upstream blueprint `showcase_blueprint` (`src/ckanext-showcase/ckanext/showcase/views.py`,
logic in `utils.py`). No HDX extension registers or redirects a `/showcase/*` route today. `hdx_theme` precedes
`showcase` in `ckan.plugins`, so the HDX templates under `templates/showcase/` win; those with `{% ckan_extends %}` fall
through to upstream.

| Screen | Route | View | Template chain |
|---|---|---|---|
| Add | GET/POST `/showcase/new` | `CreateView` (core `dataset.CreateView`) | HDX `showcase/new.html` → upstream `showcase/new.html` → HDX `showcase/edit_base.html` → upstream `showcase/edit_base.html` → v1 `page.html` |
| Edit | GET/POST `/showcase/edit/<id>` | `EditView` (core `dataset.EditView`) | HDX `showcase/edit.html` → upstream `showcase/edit.html` → the same `edit_base.html` chain |
| Manage datasets | GET/POST `/showcase/manage_datasets/<id>` | `manage_datasets` → `utils.manage_datasets_view` | HDX `showcase/manage_datasets.html` → upstream `manage_datasets.html` → the same `edit_base.html` chain |
| Delete | GET/POST `/showcase/delete/<id>` | `delete` → `utils.delete_view` | HDX `showcase/confirm_delete.html` → upstream → v1 `page.html` (GET only, without JS) |
| Read | GET `/showcase/<id>` | `read` → `utils.read_view` | HDX `showcase/read.html` (v1) |

Both form pages render HDX `showcase/new_package_form.html` (the IDatasetForm `package_form`). Core passes it
`form_vars`: `data`, `errors`, `error_summary`, `action` ('new' / 'edit'), `form_style`, `dataset_type`, `stage`. The
Edit page template also receives `pkg_dict` (the stored showcase); the form snippet does not.

**Create (POST):**
1. Parses form + files, forces `type='showcase'`, calls `ckanext_showcase_create`.
2. The action runs the uploader (`image_url` / `image_upload` / `clear_upload`), then `package_create`.
3. `ValidationError` re-renders the Add form with `errors` / `error_summary`; `data` is the posted payload.
4. Success redirects to **`showcase_blueprint.manage_datasets`** of the new showcase, with no flash.

**Edit:**
- GET: core `EditView.get` checks `package_update` (→ 403) after `utils.check_new_view_auth` (`ckanext_showcase_create`
  → 401). `data` is the stored dict with `tag_string` rebuilt from the tags.
- POST: `utils.check_edit_view_auth` (`ckanext_showcase_update` → 401), then `ckanext_showcase_update`, which HDX
  replaces with `chained_showcase_update` (`hdx_dataviz/actions/update.py`): auth, uploader, `package_update`. The update
  is a full replace; extras not posted are deleted.
- `ValidationError` re-renders the Edit form. Success redirects to **`showcase_blueprint.read`** (the possibly renamed
  slug), with no flash.

**Delete:** `ckanext_showcase_delete` → `entity.purge()`: a hard delete that cascades the dataset associations; there is
no restore. Flash 'Showcase has been deleted.' → `showcase_blueprint.index` (`/showcase`, v1).

### Manage datasets (`utils.manage_datasets_view`)

- Auth `ckanext_showcase_update` (→ 401), then `package_show` (missing → 404). It sets `g.pkg_dict`.
- **POST** with `bulk_action.showcase_remove`: every form key starting `dataset_` is an id; each one goes through
  `ckanext_showcase_package_association_delete`. Flash 'The dataset has been removed from the showcase.' /
  'The datasets have been removed from the showcase.'
- **POST** with `bulk_action.showcase_add`: same id collection, `ckanext_showcase_package_association_create` per id. A
  `ValidationError` (already associated) becomes `flash_notice` ('The dataset, {title}, is already in the showcase').
  Flash 'The dataset has been added to the showcase.' / 'The datasets have been added to the showcase.'
- Both POST branches redirect to the bare Manage URL: **`q`, `sort` and `page` are dropped**. A POST with no `dataset_`
  key falls through and re-renders.
- **Available list** (`_add_dataset_search`): `package_search` with
  - `q` from the URL, `sort` (raw string; default `score desc, metadata_modified desc`), page size
    `ckan.datasets_per_page` (20);
  - `fq`: every other non-`_` URL param as `param:"value"`, `+dataset_type:dataset`, and `!id:(…)` excluding the datasets
    already in the showcase;
  - `ext_*` params passed as `extras`;
  - results in `g.page` (`h.Page`, its pager keeps every param except `page`), count `g.page.item_count`;
    `g.query_error` on a Solr error. Facets are computed but not shown.
- **In-showcase list** (`g.showcase_pkgs`): `ckanext_showcase_package_list` = `package_search` on the associated ids,
  **`rows: 100`**, no sort, no pagination.

### Schema (upstream `logic/schema.py` + HDX `hdx_dataviz/util/schema.py`)

| Field | Validators |
|---|---|
| `name` | `not_empty`, `name_validator`, `package_name_validator` (update: `ignore_missing`). Shares the namespace with datasets ('That URL is already in use.') |
| `title` | create: `if_empty_same_as("name")`; update: `ignore_missing` |
| `notes`, `author`, `author_email` | `ignore_missing`, `unicode_safe` (no email check) |
| `url` | `ignore_missing`, `url_validator` (http or https, 'Please provide a valid URL') |
| `tag_string` | `tag_string_convert` (2–100 chars, `[\w \-.]`) |
| `image_url` | `ignore_missing`, extras (no URL check server-side) |
| `in_dataviz_gallery`, `image_frame_mode`, `in_carousel_section` | `_has_dataviz_gallery_permission`, `default('false')`, `boolean_validator`, extras |
| `dataviz_label` | `not_empty_if_in_dataviz_gallery` ('Missing value'), `hdx_check_string_length_wrapper(12)` |
| `data_url` | `ignore_empty`, `_is_https_url` ('Only HTTPS URLs are allowed'), `url_validator` |
| `priority` | `ignore_empty`, `natural_number_validator` |

`_has_dataviz_gallery_permission` silently drops the six dataviz keys for users without the permission. The only
server-required field is `name`, plus `dataviz_label` while `in_dataviz_gallery` is true. `data_url` and `priority`
are validated whatever `in_dataviz_gallery` says.

### Permissions (HDX `hdx_dataviz/actions/auth.py`, replacing the upstream showcase-admin rules)

| Item | Rule |
|---|---|
| Add page + create | `ckanext_showcase_create` → `_is_editor`: `create_dataset` or `admin` in an organisation; core `package_create` on top |
| Edit / Delete | `ckanext_showcase_update` / `_delete` → `allowed_to_modify_dataviz`: a showcase in the gallery needs `has_dataviz_gallery_permission` (sysadmin or "Manage Carousel and Dataviz Gallery"); otherwise `_is_editor` |
| Manage page | `ckanext_showcase_update` |
| Add / remove a dataset | `ckanext_showcase_package_association_create` / `_delete` → `_is_editor` |
| Dataviz fields | `h.has_dataviz_gallery_permission()` (template gate + schema) |

Failures abort with 401; the v2 error page renders 401 with its generic server-error copy.

### v1 form (HDX `showcase/new_package_form.html`)

**Form element:** `<form id="dataset-edit" class="hdx-form" method="post" action="{{ c.form_action or '' }}"
data-module="basic-form" enctype="multipart/form-data">`, `h.csrf_input()`, hidden `_ckan_phase=dataset_new_1` and
`pkg_name`, then `form.errors(error_summary)`.

| Field | Label | Widget | Id |
|---|---|---|---|
| `title` | 'Title' | `form.input`, `slug-preview-target`, placeholder 'eg. A descriptive title' | `field-title` |
| `name` | 'URL' (required) | `form.prepend` `/showcase/`, `slug-preview-slug` (prefix = domain, placeholder `<showcase>`), placeholder 'eg. my-showcase' | `field-name` |
| `notes` | 'Description' | `form.markdown` (Markdown hint), placeholder 'eg. Some useful notes about the data' | `field-notes` |
| `tag_string` | 'Tags' | `hdx_autocomplete` Select2, tag autocomplete, comma tokenizer, placeholder 'eg. economy, mental health, government'; errors from `errors.tags` | `field-tags` |
| `image_url` / `image_upload` / `clear_upload` | 'Image URL (https only)' or 'Image name' / 'Image' / 'Clear Upload' | `form.image_upload` (raw URL input, file input, checkbox) | `field-image-url` |
| `url` | 'External link' | text, placeholder 'https://www.example.com' | `field-url` |
| `author` | 'Submitted By' | text, placeholder 'Joe Bloggs' | `field-author` |
| `author_email` | 'Submitter Email' | text, placeholder 'joe@example.com' | `field-author-email` |

Dataviz block, only when `h.has_dataviz_gallery_permission()`:

| Field | Label | Widget | Id |
|---|---|---|---|
| `in_dataviz_gallery` | 'Show in Dataviz Gallery' | select Yes `true` / No `false` | `field-in-dataviz-gallery` |
| *(below, inside `#dataviz-gallery-section`)* | | | |
| `image_frame_mode` | 'The Showcase Image contains a Frame' | select Yes / No | `field-image-frame-mode` |
| `dataviz_label` | 'Label' (required marker) | text, placeholder 'Label to be shown over the gallery icon' | `field-dataviz-label` |
| `data_url` | 'Data URL (Defaults to showcase URL)' | `type=url`, placeholder 'URL for visualisation data' | `field-data-url` |
| `in_carousel_section` | 'Show in the Carousel Section of the Dataviz Gallery' | select Yes / No | `field-in-carousel-section` |
| `priority` | 'Priority (Decides the order in the carousel)' | text, placeholder 'Enter a number, higher ones appear first' | `field-priority` |

**Actions:** Delete (edit only, `ckanext_showcase_delete` on `data.id`, red link with `hdx_confirm-action` modal 'Are
you sure you want to delete this showcase?') + submit `name=save` 'Create Showcase' / 'Update Showcase', then
'* Required field'.

**Page chrome:**
- Add: H1 'Create a Showcase', no tabs; breadcrumb Home / Showcases / Create Showcase.
- Edit and Manage: no H1; HDX `edit_base.html` tab bar Edit showcase / Manage datasets / View showcase (eye icon,
  read page); breadcrumb Home / Showcases / {title} / Edit on both.

### v1 JS

- `custom_showcase_creation.js` (bundle `custom-showcase-creation-scripts`): shows `#dataviz-gallery-section` when
  `#field-in-dataviz-gallery` is `true`, hides it otherwise. Hidden fields still post.
- `hdx_autocomplete.js` (bundle `hdx-autocomplete`): tag Select2 on `/api/2/util/tag/autocomplete` (HDX
  `hdx_tag_autocomplete_list`: approved tags; `crisis-*` for sysadmins only).
- Slug modules from the `hdx_theme/ckan` bundle: preview "URL: <host>/showcase/<slug> [Edit]"; the title fills the slug
  only when the title was empty at load.
- `hdx_confirm-action.js`: the Delete modal; on confirm it POSTs to `showcase_blueprint.delete` with CSRF.
- Not active on these pages: `basic-form`, `hdx-image-upload` and Manage's `table-selectable-rows` (their bundles are
  not loaded), so there is no select-all and no URL / upload switching.
- Manage search and sort: `organizations.js` (Enter in `#headerSearch` → `q`) and `order-by-dropdown.js` (→ `sort`).

### Dataset page and entry points

- The v2 dataset page (`package/hdx_read.html`) already shows a collapsible "Showcases" section (`#showcases`, anchor
  link) of `v2/components/showcase-card.html` from `ckanext_package_showcase_list`. It has no edit or add action.
- Edit is linked from the v1 read page (`showcase_actions_menu.html`), the v1 `/showcase` list cards and the v2 Dataviz
  Gallery cards (permission only). Manage is linked only from the Edit tabs and the post-create redirect.
- `/showcase/new` has no live entry point (the only "Add Showcase" link is in the unused
  `package/snippets/related_list.html`).

### Analytics

- No showcase-specific tracking: no `data-*` attributes and no form events.
- `<title>` / Mixpanel "page view" `page title`: 'Create Showcase' (Add), 'Showcases' (Edit), 'Showcases - Manage
  datasets' (Manage).
- Server-side "dataset created" analytics skip showcases.

### Tests

- `ckanext-hdx_dataviz/.../tests/test_dataviz_showcase_api.py`: create / update / delete auth for gallery and regular
  showcases; `dataviz_label` required in the gallery.
- `ckanext-hdx_dataviz/.../tests/test_dataviz_page_load.py`: the gallery page and its Edit links.
- `ckanext-hdx_theme/.../tests/test_pages/test_page_load.py`: `/showcase` and the read page only.
- Nothing covers the new, edit or manage views, the association round trip or the form markup. The upstream tests in
  `src/ckanext-showcase` assume upstream auth and are not run in HDX CI.

### v1 bugs and quirks

- **Confirm page Cancel deletes.** Cancel is a submit inside the delete POST form; `delete_view` looks for `cancel` in
  the query string (and does not `return` its redirect), so the POST purges the showcase.
- The id-only auth path reads `in_dataviz_gallery` from the stored extras as a string, so a showcase saved with `'false'`
  still requires the dataviz permission to edit, delete or manage.
- Manage: the in-showcase list (and `num_datasets`) is capped at 100; the indexed `has_showcases` /
  `num_of_showcases` dataset fields are not refreshed by add / remove until the dataset is reindexed.
- Breadcrumb ends 'Edit' on Manage too; the Edit `<title>` is just 'Showcases'.
- Manage sort: 'Name' uses the case-sensitive `title_string`; 'Popular' needs `g.tracking_enabled`, which nothing sets,
  so it never renders.
- `/dataset/showcases/<id>` (v1, unlinked) calls `h.check_access('ckanext_showcase_update')` without an id; for a
  logged-in non-sysadmin that likely errors (inferred from code, not run; out of scope).
- `author_email` and `url` are plain text inputs; `image_url` is checked for https only client-side.

---

## 2. Figma Analysis

### Layout

```
breadcrumb       Add: Home / Showcase / Add showcase
                 Edit, Manage: Home / IOM UN Migration / Dataset name / Showcase
.intro-hdx       padding 96 48; header → form gap 40
├── header       h1 Merriweather Bold 32px #101212 ("Add showcase" / "Edit showcase")
│   └── tabs     (Edit, Manage) Edit showcase · Manage datasets · View showcase — 64px, 14/500, active 4px #1862d8, gap 16
└── form         580px, gap 20
    Add / Edit:
      * indicates mandatory fields              #c44536, 16/600
      Title *                                   text 37px
      URL/Slug *  + "This is how the URL will appear on HDX, you can change this below."
        [data.humdata.org/showcase/][ slug ]    prefix cell + input
      Description *                             textarea 150px
      Tags + "Add tags to help others find your dataset."
        [ input ]  "Suggested tags: health, hxl, indicators, environment, …" (links)
      Upload new thumbnail                      [⬆ Upload file]; Edit: ☐ Clear upload
      External link *                           "https://"
      Submitted by *                            "Name"
      Submitter email *                         "Email"
      Show in Dataviz Gallery                   select 34px "Yes"
      (Edit only) The showcase image contains a frame · Label · Data URL (Defaults to showcase URL)
                  · Show in the carousel section of the dataviz gallery · Priority
      [Delete] [Create showcase | Update]       right-aligned, gap 16
    Manage:
      Datasets in this showcase  19,819         Merriweather 20 + Roboto 16 count
        card (org · title · Show more ⌄ · [− Remove from showcase])
      Add a dataset to this showcase  19,819
        [ Search for datasets 🔍 ]
        card × 7 (… [Add to showcase])          gap 16
        pagination  ‹ Page 1 2 3 … 31 Page ›
```

### Token map

| Figma | v2 |
|---|---|
| H1 Merriweather 32px | `.hdx-v2-signup-form-page__heading` (`.hdx-page-title-scale()`, 24 / 28 / 32) |
| Mandatory note `#c44536` | `.hdx-v2-signup-form-page__mandatory-note` (`--hdx-error-6`) |
| Label 16/500, asterisk `#c44536` | `text-field` / `select` label + `required` marker |
| Help text beside the label `#4b5563` | component `description` (between label and field) |
| Input 37px, `#d8e0e1` border | `text-field.html` `size='m'` (34px, 082 D16) |
| Slug prefix cell + input | `c-slug-preview` (D3) |
| Textarea 150px | `text-field.html` `multiline=True`, `rows=5` |
| Tags input + suggested links | tag Select2 (D7) |
| 'Upload file' button, 'Clear upload' checkbox | `c-image-upload` Upload + Remove (D8) |
| Select 34px, drop shadow | `select.html` |
| Delete: white, border, shadow | `button.html style='tertiary' size='l'` |
| Create / Update `#1862d8` | `button.html style='primary' size='l'` |
| Tabs | `c-tabs` (64px, 4px `--hdx-primary-5`, gap 16 — exact match) |
| Section title Merriweather 20 + count 16 | `v2/list-header.html` `title_size='section'` (`.hdx-section-title()`) |
| Card 582px max, padding 16, gap 16, `#ebeff0` border | `c-dataset-card` (D15) |
| Card buttons 4/8 padding, 12px | `button.html size='s'`: Remove `secondary`, Add `primary` |
| Search field | `search-input.html` |
| Pagination | `pagination.html` |
| 580px column | signup `__card` 100% / 80% / 50% |

### Artefacts and inconsistencies

- **Copied layers:** hidden (`display:none`) Request Access layers — "Get in touch with the contributing
  organization…", "Tell them about your work…", an org logo and a "[Dataset] Lebanon Displacement Data" line. The
  Description placeholder is the Request Access text.
- **Delete on Add:** there is nothing to delete before creation.
- **Edit / Manage breadcrumb:** org and dataset crumbs; showcases have no owning organisation or dataset.
- **Sample values:** 'Global Hunger Index' title, 'Source' in Tags, '22222222' priority, `19,819` on both counts.
- **Add hides the dataviz block** while showing 'Yes'; Edit shows it. v1 toggles it on the select value.
- **Required markers:** six fields marked; the server requires only the slug (§1 Schema).
- **Manage:** the in-showcase card has a darker `#3f4748` border; the 'Add to showcase' button reuses the minus icon; the
  sort dropdown and filter chips exist as hidden layers.
- **Missing from Figma:** MD / SM, Cancel, error states, the delete confirmation, empty states, flash messages.

### Breakpoints

XL only. MD / SM follow the 082 / 092 shell (§7).

---

## 3. Current vs Target

| Aspect | v1 | Target | Basis |
|---|---|---|---|
| Base / layout | v1 `page.html`, Bootstrap columns | `v2/page.html`, signup shell | D1 |
| Template structure | `ckan_extends` chain over upstream | HDX `showcase/edit_base.html` as the v2 base; children without `ckan_extends` | D2 |
| H1 | 'Create a Showcase'; none on Edit / Manage | 'Add showcase'; 'Edit showcase' on Edit and Manage | D3 |
| `<title>` | 'Create Showcase' / 'Showcases' / 'Showcases - Manage datasets' | 'Add showcase' / 'Edit showcase' / 'Manage showcase datasets' | D3 |
| Breadcrumb | Home / Showcases / {title} / Edit | Home / Showcases / {title} / 'Edit showcase' or 'Manage datasets'; Add: Home / Showcases / 'Add showcase' | D5 |
| Tabs | Bootstrap `nav-tabs` | `c-tabs` | D11 |
| Labels / buttons | title case | Figma sentence case; 'Create showcase' / 'Update showcase' | D3 |
| Help text | Markdown hint; Priority in the label | mandatory note, slug and tags descriptions, Markdown hint | D4 |
| Required markers | URL; Label (gallery) | Title, URL | D6 |
| Label (`dataviz_label`) | required in the gallery, 12 characters; gallery card header | removed; the gallery card shows the title | D19 |
| Slug | `form.prepend` + slug modules | `c-slug-preview` | D3 |
| Tags | `hdx_autocomplete` (+ comma tokenizer) | tag Select2 (approved tags) | D7 |
| Image | raw URL + file + 'Clear Upload' | `c-image-upload` Upload / Link / Remove, 2 MB check | D8 |
| Dataviz reveal | jQuery `custom_showcase_creation.js` | `window.hdxV2.wireReveal` + `pages/showcase-form.js` | D9 |
| Errors | summary list | 082 D15: per-field, summary `c-alert` only without field errors or when they're all in the hidden dataviz section | D1, D17 |
| Delete | Bootstrap modal; confirm-page Cancel deletes | `c-drawer`; confirm-page Cancel is a link | D10 |
| Manage layout | two Bootstrap tables side by side | one column: in-showcase section, then add section | D12 |
| Manage actions | checkboxes + bulk button per table | one button per `c-dataset-card` | D12, D15 |
| Manage after add / remove | search, sort and page reset | unchanged | D13 |
| Manage sort | 'Order by' dropdown | `list-header` sort dropdown | D14 |
| Manage pagination | `c.page.pager` | `c-pagination`, centred | D14 |
| Dataset page Showcases section | v2 | unchanged | D16 |
| Views, schema, auth, success redirects | — | unchanged | §9 |

Removed from these pages: the `custom-showcase-creation-scripts`, `hdx-autocomplete` and `showcase/ckanext-showcase-css`
assets, `hdx_confirm-action`, `form.errors`, `search_form_new.html` and every Bootstrap class.

---

## 4. Component Mapping

No new component and no component change.

| Element | Component |
|---|---|
| Breadcrumb | `v2/components/breadcrumb.html` (D5) |
| Shell: H1, column, form column, actions row | signup shell `.hdx-v2-signup-form-page` > `__card` (`__heading`, `__mandatory-note`, `__fields`, `__body-text`, `__actions`), `v2-signup-page-styles` (D1, §8) |
| Edit / Manage tabs | `v2/components/tabs.html` (D11) |
| Title, External link, Submitted by, Submitter email, Data URL, Priority | `v2/components/text-field.html` `size='m'`, each in a `c-form-field` wrapper (082 pattern) |
| Description | `text-field.html` `multiline=True`, `rows=5`, `hint` = Markdown link (D4) |
| URL slug | `v2/components/slug-preview.html`: `prefix` = `h.url_for('showcase_blueprint.read', id='', qualified=true)` without scheme, `preview_placeholder='<showcase>'`, `target_id='field-title'`; page-loaded `v2-slug-preview-scripts` (D3) |
| Tags | `v2/components/select.html` `multiple`, `searchable`, `select_attrs={'data-source': '/api/2/util/tag/autocomplete', 'data-source-type': 'tag'}`; `v2-select2-styles` / `v2-select2-scripts` (D7) |
| Thumbnail | `v2/components/image-upload.html` (D8) |
| Yes / No selects | `select.html`, `options={'true': 'Yes', 'false': 'No'}` |
| Error summary | `v2/components/alert.html` (082 D15) |
| Delete trigger / submit | `button.html` (`tertiary` / `primary` `button_type='submit'`, `size='l'`) (D10) |
| Delete confirm | `v2/components/drawer.html` + `.c-drawer-form` (`__text`, `__buttons`), as 092 `delete-location-drawer` (D10) |
| Manage section headings + counts, sort | `v2/list-header.html` (`title_tag='h2'`, `show_filters=False`) (D14) |
| Manage search | `v2/components/search-input.html` (`icon_submit`, `show_clear`) |
| Manage dataset rows | `v2/components/dataset-card.html` in a `c-dataset-card-list` + `caller()` actions group (D15) |
| Manage pagination | `v2/components/pagination.html` in a `.hdx-v2-pagination-row` (search page, as /dataset) |
| Flashes after add / remove / delete | `v2/page.html` flash block (`c-alert`) |

**Assets:**
- **Styles:** `v2-signup-page-styles` on all three; `v2-select2-styles` on Add / Edit; `v2-search-page-styles` on Manage
  (list header, pagination row). No showcase LESS.
- **Scripts:**
  - Add / Edit: `v2-slug-preview-scripts`, `v2-select2-scripts`, new `v2-showcase-form-page-scripts`
    (`v2/pages/showcase-form.js`, D9).
  - Manage: new `v2-showcase-manage-page-scripts` (`v2/url-nav.js` for the sort dropdown, per-page bundle precedent).
  - `window.hdxV2.wireReveal` ships in `v2-components-scripts` (`utils.js`).

---

## 5. Form Contract

### Add / Edit — visible fields (Figma order)

| Field | Label | Component | Required | Notes |
|---|---|---|---|---|
| — | '* indicates mandatory fields' | `__mandatory-note` | | above the fields (D4) |
| `title` | 'Title' | text-field | ✓ | `id='field-title'`; slug target; placeholder 'eg. A descriptive title' |
| `name` | 'URL' | slug-preview | ✓ | `id='field-name'`; description 'This is how the URL will appear on HDX, you can change this below.'; placeholder 'eg. my-showcase' |
| `notes` | 'Description' | text-field multiline | — | `id='field-notes'`; placeholder 'eg. Some useful notes about the data'; hint 'You can use {Markdown formatting} here' (090 `markdown_link`) |
| `tag_string` | 'Tags' | select (tag Select2) | — | `id='field-tags'`; description 'Add tags to help others find your showcase.'; placeholder 'eg. economy, mental health, government'; `selected` / `options` from `data.tag_string` split on commas (090); errors from `errors.tag_string` (091) |
| `image_url` / `image_upload` / `clear_upload` | 'Upload new thumbnail' | image-upload | — | `id='field-image-url'`; D8 params |
| `url` | 'External link' | text-field | — | `id='field-url'`; placeholder 'https://www.example.com' |
| `author` | 'Submitted by' | text-field | — | `id='field-author'`; placeholder 'Joe Bloggs' |
| `author_email` | 'Submitter email' | text-field | — | `id='field-author-email'`; placeholder 'joe@example.com' |
| `in_dataviz_gallery` | 'Show in Dataviz Gallery' | select | | `id='field-in-dataviz-gallery'`; gated (D9) |
| `image_frame_mode` | 'The showcase image contains a frame' | select | | `id='field-image-frame-mode'`; inside the section |
| `data_url` | 'Data URL (Defaults to showcase URL)' | text-field | — | `id='field-data-url'`; placeholder 'URL for visualisation data' |
| `in_carousel_section` | 'Show in the carousel section of the dataviz gallery' | select | | `id='field-in-carousel-section'` |
| `priority` | 'Priority' | text-field | — | `id='field-priority'`; placeholder 'Enter a number, higher ones appear first' |
| Submit `name=save` | 'Create showcase' / 'Update showcase' | button | | |

- Every field gets `errors=errors.get(<name>)`.
- Selects show `'true'` when `h.asbool(data.<field>)`, else `'false'` (v1).
- Every input is `type='text'`, `data_url` included (D18).

### Kept verbatim

- `id="dataset-edit"`, `method="post"`, `action="{{ c.form_action or '' }}"`, `enctype="multipart/form-data"`,
  `h.csrf_input()`.
- Every field `name`, the uploader trio, the submit `name=save`, and the ids `field-title`, `field-name`,
  `field-in-dataviz-gallery`, `dataviz-gallery-section`.

### Free to change

The hidden `_ckan_phase` and `pkg_name` inputs are read by neither showcase view (both `post` methods are overridden);
they are dropped. The `hdx-form` class and `data-module="basic-form"` go.

### Data on re-render

- Fields read `data` (the posted payload after a failed save).
- The breadcrumb, tabs, delete gate and drawer read `pkg_dict` (stored values), passed to the form snippet as
  `h.snippet(form_snippet, c=c, pkg_dict=pkg_dict, **form_vars)` on Edit. A failed rename therefore still links to the
  stored slug.
- Image preview: computed from `data.image_url` with the plugin's `image_display_url` rule, on GET and re-render
  alike (an uploaded filename → the `uploads/showcase/<file>` static URL; a URL needs none).

### Manage datasets — POST contract (unchanged)

Each card holds its own `<form method="post">` without `action` (posts to the current URL, query included):
- `h.csrf_input()`;
- `<input type="hidden" name="dataset_<package.id>" value="on">`;
- the button `name="bulk_action.showcase_add" value="add"` (available list) or
  `name="bulk_action.showcase_remove" value="remove"` (in-showcase list).

The search form is `GET` with `q`, carrying the current `sort` as a hidden input when set.

---

## 6. Flow & States

```
/showcase/new ─▶ Create showcase ─┬─ valid ─▶ 302 Manage datasets (unchanged; no flash)
                                  └─ invalid ─▶ re-render with errors
Edit tab ─▶ Update showcase ─┬─ valid ─▶ 302 read page (v1, unchanged; no flash)
                             └─ invalid ─▶ re-render with errors
Edit ─▶ Delete ─▶ drawer ─▶ POST delete ─▶ purge ─▶ flash + /showcase (v1)
Manage ─▶ card button ─▶ POST ─▶ association create / delete ─▶ flash ─▶ 302 bare Manage URL (D13)
Manage ─▶ search / sort / page ─▶ GET with q, sort, page
```

| State | Behaviour |
|---|---|
| Add, empty | Title typing fills the slug until the slug is typed into; no tabs; no Delete |
| Edit, JS on | Slug collapsed to "URL: …/showcase/<slug> [Edit]" |
| Re-render with a slug error | Slug field visible with its error; no preview |
| Re-render with any other error | Error under the field; summary `c-alert` only when no field has an error, or when every field error is in the hidden dataviz section (D17) |
| User without dataviz permission | No dataviz fields (template gate; the schema drops them anyway) |
| 'Show in Dataviz Gallery' = No | Section hidden (`hidden` attribute server-side); fields keep their values and still post (v1) |
| … switched to Yes | Section shown |
| Image file over 2 MB / not an image | Dropped client-side; `check_message` shown and announced |
| Manage, showcase empty | 'This showcase has no datasets associated to it.' (v1 copy, `__body-text`) |
| Manage, no available results | 'No datasets could be found' (v1 copy); Solr error: 'There was an error while searching. Please try again.' |
| Manage, after add / remove | Flash `c-alert`; search, sort and page reset; the dataset has moved list |
| Duplicate add (stale page) | `flash_notice` from the action (unchanged) |
| Not authorised | 401 (unchanged) |
| JS off | Slug field visible; dataviz section as rendered; no delete drawer (as 082 / 092); sort dropdown inert, `?sort=` works |

---

## 7. Responsive Behaviour

As 082 / 092 §7, with no showcase-specific breakpoint:
- **Column (`__card`):** 100% SM, 80% MD, 50% XL.
- **Title:** 24 / 28 / 32px. **Page margins:** `--hdx-space-8`, `--hdx-space-24` at XL.
- **Tabs:** `c-tabs` scrolls horizontally when it doesn't fit.
- **Fields:** full column width, stacked. **Actions:** right-aligned row.
- **Manage:** list headers wrap their sort control under the title when narrow (`show_filters=False` keeps the controls
  at every width); `c-dataset-card` uses its SM layout; pagination `size='md'`, centred.

Figma's 40 / 20px gaps come out as the shell's 32 / 24px (as accepted in 082); the 16px card gap is `c-dataset-card-list`'s.

---

## 8. Template Strategy

All paths under `ckanext-hdx_theme/ckanext/hdx_theme/templates/showcase/`.

- **`edit_base.html`:** rewritten in place as the v2 base; extends `v2/page.html`, no `ckan_extends`.
  - Layout: `outer_row_class='hdx-v2-signup-outer-row'`, `breadcrumb_row_class='hdx-v2-breadcrumb-row--white'`,
    `content_class='hdx-v2-content-columns__content'`.
  - `{% set pkg = pkg_dict or g.pkg_dict %}`; children set `showcase_page` ('new' / 'edit' / 'manage').
  - Blocks: `subtitle` (D3), `breadcrumb_items` (D5), `styles`, `scripts` (§4 per page), `primary` =
    `<div class="hdx-v2-signup-form-page"><div class="hdx-v2-signup-form-page__card">` holding the H1, `c-tabs` (D11,
    edit / manage only) and the child's `showcase_content` block. The card is a `<div>` on every page, so the H1 and
    tabs share the column with the content.
- **`new.html`:** v2 child (`showcase_page='new'`), `showcase_content` = `h.snippet(form_snippet, c=c, **form_vars)`.
- **`edit.html`:** v2 child (`showcase_page='edit'`), `showcase_content` = the form snippet with `pkg_dict` (§5).
- **`new_package_form.html`:** rewritten as the standalone v2 form `<form class="hdx-v2-signup-form-page__fields">`
  (§5): the mandatory note, error summary, fields and `__actions` are its direct children, one column with one gap, as
  Figma's `.form`. It branches on `action == 'edit'` for the submit label and the Delete trigger; the drawer renders
  after the form.
- **`manage_datasets.html`:** v2 child (`showcase_page='manage'`), `showcase_content` = two
  `<section class="hdx-v2-signup-form-page__fields">`:
  1. `list-header` 'Datasets in this showcase' + `g.showcase_pkgs | length`, no controls; a `c-dataset-card-list` of
     cards with Remove;
  2. `list-header` 'Add a dataset to this showcase' + `g.page.item_count` with the sort dropdown (D14); the search
     form (placeholder 'Search for datasets'); a `c-dataset-card-list` of cards with Add; `c-pagination` in a `.hdx-v2-pagination-row`
     (`current_page=g.page.page`, `total_pages=g.page.page_count`, `base_url` keeping every current param except `page`,
     as v1's `pager_url`).
  - Card: `org_name=package.organization.title` (plain text), `title=package.title or package.name`,
    `title_href=h.url_for('dataset.read', id=package.name)`, no description (D15); `caller()` = the §5 form as the `c-dataset-card__actions-group`, holding a `size='s'` button
    ('Add to showcase' primary + `v2/icons/plus.svg`; 'Remove from showcase' secondary + `v2/icons/minus.svg`).
- **`confirm_delete.html`:** stays v1; only its Cancel submit button becomes a link to `showcase_blueprint.edit` (D10).
- **No `v2` gate:** only the showcase views render these templates.
- **Left untouched:**
  - every upstream template in `src/ckanext-showcase`;
  - HDX `read.html`, `search.html`, `showcase_actions_menu.html`, `snippets/showcase_item.html`,
    `snippets/showcase_list.html`;
  - `custom_showcase_creation.js` + its bundle, `hdx-autocomplete`, `hdx_confirm-action.js`;
  - `package/hdx_read.html` and `showcase-card.html` (D16).

### Backend (D19)

- `ckanext-hdx_dataviz/.../util/schema.py`: `dataviz_label` = `_has_dataviz_gallery_permission`, `ignore_missing`,
  `unicode_safe`, `convert_to_extras`; `not_empty_if_in_dataviz_gallery` is deleted.
- `templates/dataviz/index.html` (theme): the `dataviz-card` title is `dataviz.title`.

### JS (D9)

- `fanstatic/v2/utils.js`: `window.hdxV2.wireReveal(select, target, options)` (elements; returns when either is
  missing) — on `change` and at init, shows `target` when the select value (lower-cased) is in `options.values`, else
  hides it. Options: `hiddenClass` (toggled when given; otherwise the `hidden` attribute), `requiredInputs` (elements
  that get `required` while shown), `clearOnHide` (empties every input and textarea in `target` when hidden).
- `fanstatic/v2/pages/request-access.js`: its three `wireOtherReveal` calls use the helper with
  `values: ['other', 'hdx-other']`, its `-other--hidden` class and `clearOnHide: true` — no behaviour change.
- `fanstatic/v2/pages/showcase-form.js` (new): `wireReveal` on `#field-in-dataviz-gallery` and
  `#dataviz-gallery-section`, `{values: ['true']}`. The section wrapper is a plain `<div>` (so `hidden` applies)
  holding a `__fields` div; it renders `hidden` unless the value is true.

---

## 9. Functionality & Analytics Preservation

| Item | Status |
|---|---|
| Routes, methods, create → Manage and edit → read redirects, no success flash | Unchanged (upstream views) |
| Auth: create, update, delete, association, dataviz gate | Unchanged |
| Schema, validators, field names, uploader trio, posted field set | Unchanged, except `dataviz_label`: optional, no length limit, no longer posted (D19) |
| Dataviz Gallery card title | `title` instead of `dataviz_label or title` (D19) |
| Manage POST contract (`bulk_action.*`, `dataset_<id>`), flashes, available-list search (`q`, `sort`, URL `fq` params, page size) | Unchanged; one dataset per POST (D12) |
| Manage redirect target | Unchanged: the bare Manage URL (D13) |
| In-showcase list cap (100) | Unchanged |
| Delete endpoint, purge, flash, redirect | Unchanged; new confirm UI; confirm-page Cancel no longer deletes (D10) |
| Dataviz reveal (no clearing, hidden fields post) | Unchanged behaviour, new JS (D9) |
| Tags endpoint | Unchanged; free-text tags via comma tokenizer no longer possible (D7) |
| Image URL mode, upload, clear | Kept; 2 MB client check added; v1's client-only https check dropped (D8) |
| Request Access "Other" reveals | Unchanged behaviour on the shared helper (D9) |
| `<title>` / Mixpanel page title | Changed (D3) |
| Dataset page Showcases section, entry points | Unchanged (D16) |

---

## 10. Accessibility

- **Fields:** every field has an `id` and a `for` label; asterisks are `aria-hidden`, backed by native `required`;
  descriptions and hints are referenced by `aria-describedby` (component behaviour).
- **Slug preview:** "Edit" is a `<button type="button">` with `aria-controls` / `aria-expanded`; revealing moves focus to
  the input.
- **Tags:** Select2 gets the label and description ids (`select.js`).
- **Image:** `c-image-upload` buttons and the visually hidden URL label; the check message is announced.
- **Dataviz section:** hidden with `hidden` (removed from the accessibility tree).
- **Tabs:** `<nav aria-label="Showcase sections">`, the active link has `aria-current="page"`.
- **Manage:** section headings are `<h2>`; the search form is `role="search"` and the input gets
  `input_attrs={'aria-label': 'Search for datasets'}` (`search-input.html` has no visible label); card buttons repeat
  their visible text, so each gets `aria-label` 'Add to showcase: {title}' / 'Remove from showcase: {title}'
  (the visible text stays first). After the POST the page reloads with the flash `c-alert`.
- **Delete drawer:** existing `c-drawer`: `role="dialog"`, `aria-modal`, focus trap, Escape, focus return.
- **Known component gap (not fixed here, as 082 / 092 §10):** `text-field.html` and `select.html` set neither
  `aria-invalid` nor an `aria-describedby` reference to their error span.

---

## 11. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| Search, sort and page reset after each add / remove (one dataset per POST) | v1 redirect kept (D13); the user searches again |
| A form save drops a stored `dataviz_label` (full replace) | Accepted: nothing shows it any more (D19) |
| Unapproved tags already on a showcase | Kept: rendered as selected options; only new free-text tags are impossible (D7) |
| Gallery showcases saved with `'false'` keep needing the dataviz permission (§1 quirk) | Unchanged; out of scope |
| In-showcase count capped at 100 | v1 parity; noted |
| Add / remove leaves `has_showcases` stale in Solr | v1 parity; noted |
| Delete is a purge | Drawer copy says it can't be undone (D10) |
| Draft showcase opened on Edit renders the Add template (core) | Same form; Add chrome; unchanged |
| Breadcrumb / tab links to v1 pages (list, read) | Expected until those pages migrate |
| 34px fields vs Figma 37px; shell gaps | Match 082 D16 / 092 |

---

## 12. Decisions Taken

| # | Decision | Options considered | Chosen |
|---|---|---|---|
| D1 | Shell | Signup shell (082 / 092) · message-form shell (050 / 061) | Signup shell: `.hdx-v2-signup-form-page` > `__card` (a div from the base; the form is a `__fields` column inside it, §8), white, `size='m'` fields, 082 D15 errors (`alert.html` with `error_summary.values() \| join(' ')` only when there are no field `errors`), success redirects unchanged; Figma 40 / 20px gaps become the shell's 32 / 24px |
| D2 | Template structure | HDX `edit_base.html` as the v2 base · three standalone pages | `showcase/edit_base.html` rewritten in place as the v2 base (§8); `new.html`, `edit.html`, `manage_datasets.html` are its children without `ckan_extends` |
| D3 | Copy | Figma tidied · Figma literal · v1 | Figma sentence case: H1 'Add showcase' / 'Edit showcase' (Manage too); labels as §5 ('URL' on `c-slug-preview`, not 'URL/Slug'); buttons 'Create showcase' / 'Update showcase'; `<title>` 'Add showcase' / 'Edit showcase' / 'Manage showcase datasets'; v1 placeholders kept |
| D4 | Help text | Figma + v1 meaning · Figma literal · none | Mandatory note '* indicates mandatory fields'; slug description 'This is how the URL will appear on HDX, you can change this below.'; tags description 'Add tags to help others find your showcase.'; Markdown hint (090); no Priority hint |
| D5 | Breadcrumb | Showcases / title / page · v1 · short | Add: Home / Showcases / 'Add showcase'. Edit: Home / Showcases / {title} / 'Edit showcase'. Manage: Home / Showcases / {title} / 'Manage datasets'. Showcases → `showcase_blueprint.index`, {title} → `showcase_blueprint.read`, from `pkg`; last item unlinked |
| D6 | Required markers | Title + URL · Figma's six client-side · schema only · Figma's six + server | Native `required` + asterisk on Title and URL; server-required fields unchanged apart from D19 |
| D7 | Tags | Select2 tag field · + static suggested tags · plain input | `select.html` `multiple`, `searchable`, tag `data-source` (090 pattern), same endpoint as v1; no 'Suggested tags' line |
| D8 | Image | Upload + Link + 2 MB check · Upload + Link · upload only | `c-image-upload`: `label='Upload new thumbnail'`, `upload_label='Upload file'`, `upload_enabled=h.uploads_enabled()`, Link kept, Remove replaces 'Clear upload'; `max_bytes=2097152` (literal matching `ckan.max_image_size = 2`; no template helper exposes it; 089 literal precedent), `check_message='Please keep files under 2 MB.'`; no https check on the URL (no `c-image-upload` param added) |
| D9 | Dataviz reveal | Promote to `utils.js` · showcase-only JS · always visible; elements · selectors | `window.hdxV2.wireReveal` in `utils.js` (CONVENTIONS "Inline single-consumer utilities": second consumer), used by `request-access.js` and new `pages/showcase-form.js` (§8 JS); takes elements like the other helpers, `clearOnHide` empties every input in the target (Request Access unchanged); gate `h.has_dataviz_gallery_permission()` unchanged |
| D10 | Delete | Drawer + confirm Cancel fix · drawer only · drawer + v2 confirm page | Edit only, gated by `h.check_access('ckanext_showcase_delete', {'id': pkg.id})`; tertiary 'Delete' (inline `onclick` `hdxV2Drawer('delete-showcase-drawer').open()`) then primary submit, right-aligned; no Cancel; Figma's Delete on Add dropped. `c-drawer` `delete-showcase-drawer`, title 'Delete showcase', text 'Are you sure you want to delete this showcase? This can't be undone.', tertiary Cancel (`data-drawer-close`) + primary 'Delete' posting to `showcase_blueprint.delete` (`pkg.id`) with CSRF, outside the main form. HDX `confirm_delete.html` Cancel becomes a link to Edit |
| D11 | Tabs | `c-tabs` · none (082 D13) | `c-tabs` on Edit / Manage: 'Edit showcase' (`showcase_blueprint.edit`), 'Manage datasets' (`.manage_datasets`), 'View showcase' (`.read`, v1); `aria_label='Showcase sections'`; none on Add |
| D12 | Add / remove | Per-card button · bulk checkboxes · both | One POST form per card with the existing `bulk_action.*` + one `dataset_<id>` (§5); no backend change to the action handling; multi-select dropped |
| D13 | Search state after add / remove | HDX route wrapper · v1 redirect · AJAX | v1 redirect: upstream `manage_datasets_view` redirects to the bare Manage URL, so search, sort and page reset after each add / remove; no backend change |
| D14 | Sort | v1 set, fixed · /dataset default set · v1 as is · drop (Figma) | `list-header` sort dropdown on the add section: `sorting_options` Relevance (`score desc, metadata_modified desc`, the no-sort default) / Name Ascending (`title_case_insensitive asc`) / Name Descending (`title_case_insensitive desc`) / Last Modified (`metadata_modified desc`); no Popular; `sort_key='sort'`, no page size; `url-nav.js` |
| D15 | Card | `c-dataset-card` · `c-resource-card` (Figma layer name); `c-dataset-card-list` · cards in `__fields`; description + 'Show more' · none | `c-dataset-card` unchanged (§8), in a `c-dataset-card-list` (16px gap as Figma, 078 precedent); no description or 'Show more' (Figma has them); Figma's darker in-showcase border not reproduced |
| D16 | Dataset page | No change · edit link on cards · edit link + add entry | No change: the Showcases section is already v2; Edit stays reachable from the read page, `/showcase` and the gallery; Add stays URL-only |
| D17 | Errors in the hidden dataviz section | Summary alert fallback · show the section on error · leave as is | The summary `c-alert` also renders when every field error is in the hidden dataviz section (template only) |
| D18 | Data URL input type | `type='text'` · `type='url'` (v1) | `type='text'`, as 082's logo URL: a hidden invalid `type=url` input would silently block submit; the server still checks https and the URL |
| D19 | Label field (`dataviz_label`) | Field + schema + gallery title · field + schema · out of both schemas | The team uses Title (no character limit) as the gallery card header: the Label field is removed from the form; the update schema drops the required-in-gallery rule and the 12-character limit (`ignore_missing`, still an extra for API callers); the Dataviz Gallery card shows `title` (§8 Backend). A form save drops a stored label |

---

## 13. Files Affected

| File | Change |
|---|---|
| `templates/showcase/edit_base.html` | v2 base rewrite (D2, §8) |
| `templates/showcase/new.html` | v2 child |
| `templates/showcase/edit.html` | v2 child, form snippet gets `pkg_dict` |
| `templates/showcase/new_package_form.html` | Standalone v2 form + delete drawer (§5, D10) |
| `templates/showcase/manage_datasets.html` | v2 child: two sections, cards, search, sort, pagination (§8) |
| `templates/showcase/confirm_delete.html` | Cancel as a link (D10) |
| `fanstatic/v2/utils.js` | `window.hdxV2.wireReveal` (D9) |
| `fanstatic/v2/pages/request-access.js` | Uses `wireReveal` (D9) |
| `fanstatic/v2/pages/showcase-form.js` | New (D9) |
| `fanstatic/webassets.yml` | `v2-showcase-form-page-scripts`, `v2-showcase-manage-page-scripts` |
| `templates/dataviz/index.html` | Card title = `title` (D19) |
| `ckanext-hdx_dataviz/.../util/schema.py` | `dataviz_label` optional, `not_empty_if_in_dataviz_gallery` deleted (D19) |
| `ckanext-hdx_dataviz/.../tests/test_dataviz_showcase_api.py` | Label checks removed (D19) |
| `ckanext-hdx_dataviz/.../tests/test_dataviz_page_load.py` | Extend: Add / Edit / Manage render on v2 for a sysadmin (200 + H1) |
| `llm_docs/redesign/PROGRESS.md` | Migrated-pages row, bundles, `wireReveal` in the `utils.js` helper list |
| `llm_docs/redesign/CONVENTIONS.md` | `wireReveal` (Form-field components) |
| `llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Showcase management key-page entry |

Template and `fanstatic` paths are relative to `ckanext-hdx_theme/ckanext/hdx_theme/`. No LESS change.

---

## 14. Verification Checklist

- [ ] Add, Edit and Manage render on v2 for a sysadmin and for an org editor (regular showcase); anonymous users get
      401 as before.
- [ ] Add: no tabs, no Delete; title fills the slug; Create showcase lands on Manage datasets.
- [ ] Edit: saving an unchanged form keeps every stored field but `dataviz_label`, including the other dataviz extras
      and the image; a rename
      redirects to the new read URL; tabs and breadcrumb use the stored slug after a failed save.
- [ ] Errors: duplicate slug, invalid External link, invalid tag, non-https Data URL and a non-numeric Priority each
      show under their field; with the gallery set to No, the Data URL / Priority errors show in the summary alert
      (D17).
- [ ] Dataviz: hidden for users without the permission; the section follows the select; no Label field; a gallery
      showcase saves without a label; switching to No keeps the values (v1); gallery cards show the title.
- [ ] Image: upload, link, Remove (clears) and replace; a file over 2 MB is refused with the message.
- [ ] Tags: existing tags shown; autocomplete adds approved tags.
- [ ] Delete drawer: copy, Cancel, Escape, focus return; Delete purges and lands on `/showcase` with the flash. The
      no-JS confirm page Cancel returns to Edit without deleting.
- [ ] Manage: counts; Add and Remove move the dataset between sections with the flash (search, sort and page reset);
      Remove and Add buttons at the card's bottom right; sort options and centred pagination work; empty states;
      search error copy.
- [ ] Request Access "Other" reveals behave as before.
- [ ] `<title>` / Mixpanel page titles 'Add showcase' / 'Edit showcase' / 'Manage showcase datasets'.
- [ ] No Bootstrap classes and no v1 showcase / autocomplete / confirm-action assets in the rendered HTML.
- [ ] Existing tests pass (`test_dataviz_showcase_api.py`, `test_dataviz_page_load.py`, `test_page_load.py`); the new
      test passes.
- [ ] Keyboard walkthrough: tabs, slug Edit, tag Select2, image buttons, card buttons, drawer.
- [ ] Visual check at SM, MD, XL and XXL against the three exports.
