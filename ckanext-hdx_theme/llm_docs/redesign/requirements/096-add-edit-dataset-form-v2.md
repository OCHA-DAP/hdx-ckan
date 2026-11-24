# 096 — Add / Edit Dataset Form v2

**Scope:** the Add and Edit dataset form ("Share data" / "Edit data", the contribute flow) at `/contribute/new` and
`/contribute/edit/<id>` (`hdx_contribute.new` / `.edit`). This covers the form template, its client logic, the way
the form is opened from the rest of the site, and the component extensions it needs.

**Excluded:**
- The package and resource actions, the schema, the validators and the `/contribute/*` view contract.
- The QA dashboard and the dataset read pages.
- The v1 bundles and assets, which stay untouched.
- The sysadmin quarantine controls drawn in `xl-add-dataset-form2.html` (D7). Like v1, the form has none.

**Figma sources:** `xl-add-dataset-form.html` (default), `xl-add-dataset-form-errors.html` (add, errors),
`xl-add-edit-dataset-form-errors.html` (edit, errors) and `xl-add-dataset-form2.html` (sysadmin quarantine variant),
all in `ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. All four are XL frames. There is no MD or SM export.

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `PKG` = `ckanext-hdx_package/ckanext/hdx_package`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `THEME/templates/contribute_flow/create_edit.html`, which extends v1 `page_light.html`, together with its v1 script bundle `contribute-flow-scripts` |
| Objective | Match the Figma structure and look: a step sidebar, a page header with intro and required note, numbered sections, field help, file cards with Sort arrows, inline errors and a Cancel / Submit row. Keep every route, permission, validation rule, save step, data structure and analytics event, and the iframe popup that opens the form (D1) |
| Constraint | v2 pages extend `v2/page.html`, must not load v1 script bundles, and use no Bootstrap classes. The current form's JS is a v1 bundle that preloads v1 styles, so the client logic moves to new v2 page JS (D2) |
| Shared work | The 091 group layout as a shared form layer (D13); `c-config-item` add position and form-mode Sortable (D12); drag-and-drop on `c-image-upload` (D19, D48); a compact `c-info-box` (D20); more field types in `hdxV2.setFieldError` and radio errors (D23); `select.js` source options (D25); a new date-picker component (D17, D32); a v2 contribute popup snippet (D31); a `v2/header.html` param that hides "Add data" (D37); radio, slug-preview and date-picker `size` params and a select size L (D43, D44); a text-button `underline` param (D50); a text-field `leading` slot, a `file-type-icon` `attrs` param and the format → icon-category map in `CONSTANTS` (D49). Defaults keep every other caller's output unchanged |

---

## 2. Repository Audit Findings

### 2.1 Routes, views and permissions

Blueprint `hdx_contribute` in `PKG/views/contribute_flow.py`, registered by `HDXPackagePlugin.get_blueprint`:

| URL | Handler | Behaviour |
|---|---|---|
| `GET /contribute/new` | `new(id=None, action_name='package_create')` | Renders the empty form. `data` is `None` |
| `POST /contribute/new` (`save=new-dataset-json`) | `new` | Runs `package_create` without resources and returns JSON |
| `GET /contribute/edit/<id>` | `edit(id)` → `new(id, 'package_update')` | Loads `package_show_edit`, runs `ContributeFlowReadLogic.process_all()` (`PKG/controller_logic/contribute_flow_read_logic.py`) and renders the form |
| `POST /contribute/edit/<id>` (`save=update-dataset-json`) | `edit` | Runs `package_update` with `allow_partial_update=True` so the existing resources survive, and returns JSON |
| `POST /contribute/validate` | `validate()` | Dry-runs `package_validate` with `batch='FAKE_ORG_BATCH_FOR_VALIDATION'`, resources included, and returns JSON |
| `/dataset/new`, `/dataset/edit/<id>` and the old resource URLs | `dataset_old_links.*_notification_page` (`PKG/views/dataset_old_links.py`) | Return HTTP 300 with a notice page whose link calls `contributeAddDetails(...)` |
| `POST /request_tags/suggest` | `request_tags.request_tags` (`PKG/views/request_tags.py`) | "Suggest a new tag": emails `hdx.faqrequest.email` |

- **Shared rendering:** `_prepare_and_render` passes `data`, `analytics` (`analytics.generate_analytics_data(data)`),
  `errors`, `error_summary` and `aborted`. When `save` contains `-json` it returns the same dict as JSON. Otherwise it
  renders `contribute_flow/create_edit.html`.
- **POST parsing:** `_prepare_data_for_saving` unflattens the form-encoded body and runs
  `ContributeFlowWriteLogic.process_all(g.user)` (`PKG/controller_logic/contribute_flow_write_logic.py`). That maps
  the share mode, dates, locations, tags, maintainer, preview, custom viz and grouping onto the package dict.
- **Errors:** a `ValidationError` returns `errors` / `error_summary`. `_customize_error_messages` rewrites
  "Missing value" for `name`, `notes`, `dataset_source`, `maintainer`, `data_update_frequency`, `groups_list`,
  `methodology`, `owner_org` and `dataset_date`, and the "URL already in use" message for `name`. On `/validate`,
  resource errors are reshaped to `error_summary['Resources'] = {'Resource N': {...}}`. `NotAuthorized`, `NotFound`,
  `NoOrganization`, `DataError` and `SearchIndexError` return `{aborted: true, message, status_code}`.
- **Permissions:** `check_access(action_name, …)`. HDX's `package_create` / `package_update` auth delegate to core.
  A denied logged-in user is redirected to `dashboard.organizations`; an anonymous user gets a 403. The context carries
  `contribute_flow=True`.
- **Schema hooks** (`HDXPackagePlugin.validate`):
  - **Private datasets:** `notes`, `methodology`, `dataset_date` and `data_update_frequency` become optional and
    `groups_list` is removed.
  - **HDX Connect datasets:** `field_names` and `file_types` are required, `num_of_rows` is an optional positive
    integer, frequency and methodology are optional, and `license_id` / `license_other` are dropped.

### 2.2 Container: the contribute popup

- **Opening the form.** Every entry point calls `contributeAddDetails(datasetId, typeOfCall, anchor)`. On v2 pages that
  is `THEME/fanstatic/v2/contribute.js` (in `v2-page-scripts`); on v1 pages it is `THEME/fanstatic/widget/contribute/contribute.js`.
  - It opens the full-screen popup `#addDataPopup` (`THEME/templates/widget/contribute/details.html`). `v2/page.html`
    renders the popup in block `contribute_widget` for logged-in users.
  - The popup holds an iframe pointed at `/contribute/new` or `/contribute/edit/<id>`, and the iframe is
    **preloaded** on `DOMContentLoaded` for the last `.contribute-popup-init` element on the page.
  - The script adds `body.contribute-mode`.
  - Clicks inside the iframe on `.close-iframe`, `.new-header a`, `.breadcrumb a`, `.hdx-v2-breadcrumb-row a` or
    `.hdx-footer a` navigate the top window. The v2 header (`.hdx-v2-header`) and footer (`.hdx-v2-footer`) are not
    in that list.
  - `prepareContributePopup` and `contributeAddDetails` read `#addDataPopup` without a null check.
  - `details.html` loads the v1 `popup-scripts` bundle, so that bundle reaches every v2 page for logged-in users.
  - `typeOfCall` is unused; its link-click call is commented out.
- **Entry points found by this audit:**
  - The v2 navbar "Add data" button (`templates/v2/header.html`), built by `h.hdx_check_add_data()` with
    `data-module="hdx_click_stopper"`. Logged-in users without create rights go to `hdx_org_join.find_organisation`.
  - The org hero "Add dataset" (`templates/v2/org-hero.html`), `organization/snippets/org_actions_menu.html` and the
    empty-org links.
  - The dataset page-header "Edit Dataset" (`templates/v2/components/page-header.html`), the package actions menu,
    the make public/private links and the empty-resources links.
  - Search and dashboard cards (`search/snippets/package_item_v2.html`: Edit, and Archive at `#field_archived`).
  - Data grid rows (`templates/v2/completeness-item.html`).
  - The QA dashboard (`qa_dashboard/qa_package_item.html`) and the light dataset page, both on v1 pages.
- **Quick-edit anchors.** `hdx-quick-edit` (`THEME/fanstatic/v2/components/quick-edit.js`) opens the form scrolled
  to a field id. The ids in use are a contract:
  - `field_title`, `field_notes`, `ui_date_range1`, `field_data_update_frequency`
  - `field_owner_org`, `field_dataset_source`, `field_locations`, `field_methodology`
  - `field_caveats`, `field_license_id`, `field_tag_string`, `field_archived`

### 2.3 Template

- `contribute_flow/create_edit.html` extends `page_light.html` (v1) and uses Bootstrap rows and columns.
- **Blocks:**
  - The `analytics_*` blocks are fed from `analytics`.
  - `subtitle` is "Edit data" or "Share data".
  - `contribute_widget` is emptied, so there is no nested popup.
  - `header_core` is the v1 `header-mobile.html`.
  - `breadcrumb_content` is `snippets/active_breadcrumb_item.html`.
- **Scripts:** the Dropbox `dropins.js` script tag (app key attribute), Google `accounts.google.com/gsi/client`,
  `contribute-flow-scripts` and `bem-blocks-scripts`.
- **Snippets:** `bem.blocks/*` fields (`input_field`, `textarea_field`, `select2_field` with the "Other" field,
  `checkbox_field`, `radio_field`, `info_box`, `form_button`, `heading`, `paragraph`, `form_info`, `hr`).
- **Popups:** `widget/contribute/user_waiting.html` (`#userWaitingPopup`),
  `private-dataset-info.html` (`#privateDatasetInfoPopup`), `contribute-dataset-review.html` (unused) and
  `widget/tags/request-tags*.html` (`#requestTagsPopup`).
- **Resource rows** are an inline Underscore template (`#resource-item-tmpl`). Existing resources are embedded as
  JSON (`#resource-list-json`) when there are 20 or fewer; otherwise they are fetched through `package_show_edit`.
- `{% set errors = {} %}` discards any server-passed errors. All error display is client-side.

### 2.4 Form fields

The share-mode column shows where the client shows the asterisk (`data-module-required` on
`hdx_form_element_manager_bem`): **P** public, **R** HDX Connect (requestdata), **V** private.

**Section 1 — Choose how to share**

| Field | Widget | Notes |
|---|---|---|
| `private`: `#radio_private_public` / `#radio_private_requestdata` / `#radio_private_private` | Radio group with descriptions | `process_private_and_req_data` maps `public` → `private='False'`, `requestdata` → `private='False'` + `is_requestdata_type='True'`, and `private` → `'True'`. New datasets default to Private. `#dataset-is-public-description` shows a QA notice for Public. `#requestdata_type_notification` warns that files will be deleted when an existing dataset is switched to HDX Connect |

**Section 2 — Describe dataset**

| Field | Widget | Required | Notes |
|---|---|---|---|
| `title` / `#field_title` | Text + tip | P R V | Slug target. Its changes feed the tag recommender |
| `name` / `#field_name` | Slug with the `<site>/dataset/` prefix | P R V | `vendor/ckan/slug-preview.js`. A `name` error reveals the input |
| `notes` / `#field_notes` | Textarea + markdown tip | P R | `not_empty_ignore_ws` on the server |

**Section 3 — Additional information**

| Field | Widget | Required | Notes |
|---|---|---|---|
| `dataset_source` / `#field_dataset_source` | Text | P R V | New datasets default to the org title |
| `owner_org` / `#field_owner_org` | Select2 | P R V | `h.hdx_organisation_list()` (orgs where the user can create datasets). New datasets default to the first org |
| `maintainer` / `#field_maintainer` | Select2, AJAX | P R V | `/util/user/hdx_autocomplete?q=&org=<owner_org>` (`ckanext-hdx_users` `views/api.py`). Value = user id. The write logic adds `maintainer_email`. New datasets default to the current user |
| `ui_date_range1` / `ui_date_range2` (display), hidden `date_range1` / `date_range2`, `ui_date_ongoing` | jQuery UI datepicker (`hdx_datepicker`), display "MM d, yy", posted as `yy-mm-dd` | P R (error key `dataset_date`) | The server builds `[d1 TO d2]`, with `*` when the end is empty or "Ongoing" is ticked. "Ongoing" has a tooltip and disables the end date |
| `data_update_frequency` / `#field_data_update_frequency` | Select2 | P | `h.hdx_frequency_list(...)`. `-999` = not set. "Live" needs at least one API-type resource (`hdx_disable_live_frequency_filestore_resources_only`) |
| `locations` / `#field_locations` | Select2 multi | P R (error key `groups_list`) | `h.hdx_location_list()`, "world" first |
| `subnational` / `#field_subnational` | Checkbox "This dataset includes sub-national data" | — | Plus the "Sub-national means…" tip |
| `license_id` / `#field_license_id` + `license_other` | Select2 + "Other" textarea | P V (hidden for HDX Connect) | `h.hdx_license_list()`, default `cc-by`. `license_other` is required for `hdx-other` |
| `field_names`, `file_types`, `num_of_rows` | Select2 multi with free tags ×2, text | R | HDX Connect only |
| `methodology` / `#field_methodology` + `methodology_other` | Select2 + "Define methodology" textarea | P | `h.hdx_methodology_list()`, `-1` = not set. Other text is required for "Other" |
| `caveats` / `#field_caveats` | Textarea + markdown tip | — | |
| `tag_string` / `#field_tag_string` | Select2 multi, approved values only | R | `h.hdx_get_allowed_tags_list()` (`crisis-*` hidden from non-sysadmins). "Suggested tags:" from `hdx_recommend_tags`. "See all tags" link. "Suggest a new tag" opens `#requestTagsPopup` |
| `quality` / `#field_quality` | Checkbox, sysadmin only | — | "The quality of this dataset has been confirmed." |
| `resource_grouping` | Hidden, edit only | — | Passed through |

**Section 4 — Upload files** (`#resource-widget`, Backbone)

- "N files (drag and drop to sort)". "Add more files" inserts a new card **at the top**.
- Each card has:
  - a drag handle, "File N", and "Sort:" up/down `<i>` icons;
  - the source radio (`resource<pos>-upload_type`: Upload file / Import from URL), plus Dropbox and Google Drive
    links with tooltips and PNG logos;
  - a drop zone with "Browse";
  - `url`, `name` (required), `format` (Select2 AJAX `/api/2/util/resource/format_autocomplete`, guessed by
    `hdx_guess_format_from_extension`, with a warning for archive files without a format) and `description`;
  - `pii` and `microdata` checkboxes, each with an explainer;
  - "Delete this file", with the trash icon after the label.
- Deletions are queued until submit.
- While any card has PII ticked, the terms checkbox is unchecked and disabled.

**Section 5 — Add automatic Data Previews (Optional)** — visible to everyone (commit c48c3fbcde, HDX-104555)

- `dataset_preview_check` (default on) and `dataset_preview_value`, "Select which file to preview".
- The options are built client-side: `first_resource` plus one option per file. The chosen option sets
  `dataset_preview_enabled` on that resource.

**Section 6 — Add other data visualisations (Optional)**

- One `custom_viz_url` input (module `hdx_custom_dataviz_manager`), posted as `customviz__N__url`, validated by
  `hdx_is_url`.
- The JS allows up to 5, but the add and remove buttons are commented out, so the UI offers one URL.

**Section 6.a — Archive dataset** (edit only)

- `archived` select (No / Yes). Archiving forces the frequency to Never.

**Section 7 — Confirm and submit**

- **Terms:** `#checkbox-hdx-terms` has no `name` attribute. `hdx_terms_checkbox` removes `.disabled` from
  `#create-form-submit` ("Submit Dataset"). The checkbox gates Submit only on the client.
- **Need help?:** FAQ and Contact support links.
- **Delete** (edit only): `hdx_confirm-action` POSTs `/api/action/hdx_dataset_purge` (permanent), then goes to
  `hdx_dataset.search`.
- **Cancel:** `.close-iframe` → `dataset.read`.

### 2.5 Save pipeline

The form never posts normally. `contribute_flow_main` intercepts submit on `#create_dataset_form`:

1. **Validate:** POST `/contribute/validate` with the metadata and the resources (not for HDX Connect). The client
   adds "Please add at least 1 resource" and requires tags for HDX Connect.
2. **Metadata:** POST `/contribute/new` or `/contribute/edit/<id>` with only the inputs inside
   `.contribute-form-container-items` (no resource fields).
   - **Empty values are dropped** (`getFormValues`). "Ongoing" depends on `date_range2` being absent.
   - CSRF goes in a header (`hdxUtil.net.getCsrfTokenAsObject()`).
   - Switching an existing dataset to HDX Connect makes the server delete every resource.
3. **Resources** (`hdx-resource.js`, `PackageResources.saveAll`):
   - Changed resources are saved one at a time through `/api/action/resource_create` or `resource_update`. "Changed"
     means a different `hashResource`, which leaves out `pii`.
   - Multipart with upload progress when a File is attached, JSON otherwise.
   - `batch_mode=DONT_GROUP`.
   - **`resource_update` replaces the whole resource** (`package_revise` with `-resources__<id>__*`), so the full
     `package_show_edit` dict goes back, including the short upload `url`.
   - Queued deletions follow, then `package_resource_reorder` when the order changed.
4. **Redirect:** `window.top.location` → `/dataset/<name>`. For a private dataset, `#privateDatasetInfoPopup` shows
   first, unless the localStorage key `/contribute:hidePrivateDatasetInfo` is set.

### 2.6 Client JS

- **Bundle `contribute-flow-scripts`:**
  - `jquery.ui.datepicker.js`, `hdx-datepicker.js`;
  - `contribute_flow/form_element_manager_bem.js`, which handles asterisks per share mode and inline errors by
    element name;
  - `tag_recommender.js`, a 1 s debounce on title and organisation;
  - `error_block_manager.js`, the top `#hdx_error` banner;
  - `hdx_custom_dataviz_manager.js`;
  - Underscore, Backbone and `backbone-model-file-upload.js`;
  - `hdx-google-picker.js`, `hdx-resource.js` and `vendor/sortable/Sortable.js`;
  - `contribute_flow_main.js`.
- The bundle preloads the v1 `contribute-flow-styles` (which preloads `search-styles`) and `hdx-autocomplete`.
- **Also used:** `bem-blocks-scripts` (bem Select2 fields) and, from the `ckan` bundle that `base.html` loads,
  `slug-preview.js`, `hdx_terms_checkbox.js`, `hdx_confirm-action.js`, `hdx_click_stopper.js` and
  `google-analytics.js`.
- **Pub/sub topics:** `hdx-form-validation`, `hdx-dataset-form-change`, `hdx-contribute-global-created`,
  `hdx-resource-information`, `hdx-user-waiting`, `date-field-clicked`.
- **Picker configuration:** Dropbox `Dropbox.choose` with `linkType: "preview"`. Google Drive uses
  `defaultGoogleDriveOptions` in `hdx-resource.js` (GSI token client plus Picker).
- `AppView` also holds an unused splash-step code path (`.contribute-splash`); its markup no longer exists.

### 2.7 Analytics & Mixpanel

| Event | Source | When | Properties |
|---|---|---|---|
| `page view` | `base.html` `analyticsInfo` + `snippets/mixpanel.html`, fed by the template's `analytics_*` blocks | On every load of the form page. Because of the iframe preload, it fires when a page with an entry point loads, not when the user opens the form | page title "Share data" / "Edit data", org, groups, dataset id/name, is cod/indicator/archived, availability, and the rest of the standard set |
| `link click` | `hdx_click_stopper` on the navbar "Add data" | Click | link type `header add data`, label, destination url, authenticated |
| `dataset create` | `hdxUtil.analytics.sendDatasetCreationEvent` (`google-analytics.js`), called by `saveDatasetForm` | New datasets only, after validate succeeds and before the create POST (waits up to 500 ms) | page title (read from `window.parent`), event source `web`, group names, org_name, is cod (first tag only), is indicator, is private, dataset availability. GA `dataset create hdx`. `is private` and `dataset availability` compare against values the form never posts, so they always report public |
| `link click` | `tag_recommender.js` | A suggested tag is clicked | link type `dataset recommended tag` |
| `qa set incomplete` / `qa set complete` (server) | `QACompletedAnalyticsSender` in `package_update` | Every form edit of a QA-completed dataset, because `qa_completed` resets to false | dataset, groups, org, is cod, is private, availability |
| `dataset create` (server) | `DatasetCreatedAnalyticsSender` | Suppressed for the form by `context['contribute_flow']` | — |

Nothing is sent for form open, validation errors, file upload, edit success, delete, cancel or a tag request.

### 2.8 Add vs Edit; sysadmin-only parts

- **Add:**
  - Title "Share data".
  - Defaults from `generate_mandatory_fields` (`PKG/helpers/helpers.py`): Private, `cc-by`, first org, source = org
    title, maintainer = current user, default frequency, preview on.
  - No Archive and no Delete.
- **Edit:**
  - Title "Edit data".
  - Prefill from `ContributeFlowReadLogic`: locations, tags, split date and ongoing, custom viz, grouping, maintainer.
  - Archive and Delete are shown.
  - **Overdue alert:** shown when `data.id and update_status != 'unknown' and not data.is_fresh`. A red alert reads
    "This dataset's update date was **{date}**. Please check or update the Resources or Expected Update Frequency." The
    date comes from `h.hdx_get_due_overdue_date(data)` in `%b %-d %Y` format. "Please check if the following field is
    up to date:" is shown on Update Frequency.
- **Sysadmin only:**
  - The `quality` checkbox and the `crisis-*` tags.
  - There are **no quarantine controls** in the form. Quarantine is set by `hdx_update_in_quarantine_by_microdata`
    and reset on upload by `hdx_reset_on_file_upload`. It is changed manually on the QA dashboard.

### 2.9 Current behaviours (D5)

| Behaviour | Where |
|---|---|
| If a resource save fails, the error goes to the console and the "Saving resource N" overlay stays open; the dataset already exists | `PackageResources.saveAll` |
| An `{aborted: true}` JSON response is treated as success by `validateSucceeded` | `contribute_flow_main.js` |
| `license_id`, approved-tag (`tags[i].name`) and `customviz` errors fall back to the generic banner instead of the field | `form_element_manager_bem.js`, `hdx_custom_dataviz_manager.js` |
| Unticking PII on an existing file is not saved unless another field changes | `hashResource` |
| The "Live" frequency check needs resources, so it runs during validate only | `hdx_disable_live_frequency_filestore_resources_only` |
| Legacy free-text methodology values outside `hdx_methodology_list` render as an empty select | `select2_field.html` |

### 2.10 Tests

All paths are under `PKG/tests/`:
- `test_controller/test_contribute_flow.py`: `test_edit_resource_link`, `test_validate`, `test_save`, `test_edit`,
  `test_edit_lists`.
- `test_views/test_contribute_flow_write_logic.py`: the write-logic units.
- `test_pages/test_dataset.py`:
  - `test_edit_dataset_page`: GET returns 200.
  - `test_edit_dataset_location_order`: `select#field_locations` with "world" first.
- `test_requestdata/test_transformation.py`: switching to HDX Connect.
- `test_views/test_views.py`: `test_dataset_old_links`, `test_request_tags`.
- Schema tests under `test_dataset_special_fields/`.
- There are no JS or analytics tests for this flow.

---

## 3. Figma Design Analysis

### 3.1 Layout

- **Page and band:** the page is neutral-01, with a white `.dataset-page-body` band 1280px wide (padding
  space-4 / space-12 / space-20).
- **Two columns, gap space-6:**
  - a **step sidebar** (`.link-list`, 278px, padding space-10 top);
  - the **main column** (882px, padding space-10 top, gap space-12 between blocks).
- **Header block** (gap space-4):
  - h1 "Share data" / "Edit data" (`.hdx-display-l()`);
  - intro "This form will guide you through the process of describing your dataset and uploading files (where
    necessary)." (`.hdx-body-m-semibold()`);
  - "Required sections and fields are marked with an asterisk (*)." (semibold, error-5);
  - in Edit, the overdue banner.
- **Sections:**
  - Each section has a 1px neutral-3 top border and space-6 padding.
  - Inside, a 260px heading column (h3 plus helper paragraphs) sits next to a 602px fields column, with a space-5 gap.
  - Fields are 30px apart (off-token). Label → control is space-2.
- **Rhythm:** sections 5, 6, the terms and the buttons are nested in the Upload files section with a space-5 gap, so
  the vertical rhythm is uneven.
- **Sticky:** nothing is sticky.

### 3.2 Step sidebar

- **Label:** "Share data" (medium, neutral-95), the same in Edit.
- **Items:** six numbered items: Choose how to share, Describe dataset, Additional information, Upload files, Add
  automatic data previews, Add data visualiisations.
  - **Active (the first):** a 2px primary-5 bar on the left, medium neutral-95.
  - **Inactive:** regular neutral-85.
- The 24px icon slots and the grey track are hidden. There are no completion or error states.

### 3.3 Sections and fields

- **Headings:**
  - `.hdx-heading-h3()`, neutral-85.
  - Sections 1–4 are list-numbered; 5 and 6 have the numbers typed in.
  - The asterisks share the heading colour.
- **Helper text:** `.hdx-body-m()`; links are medium, underlined, in the text colour.
- **Field label:** medium neutral-85, with a red asterisk. The **hint sits above** the control, in grey (off-token
  `#4b5563`).
- **Helper boxes below the control:** light blue (off-token `#ebf2fe`, ≈ primary-05), radius-md, padding space-3 /
  space-4, `.hdx-body-s()`, no icon. They appear for Title, Description, Time Period, Location, License, Caveats and
  Tags.
- **Text input:** 37px, neutral-2 border, radius-sm, 16px text.
- **Select:** 14px text, `shadow-sm`, chevron.
- **Textarea:** 150px.
- **URL/Slug:** an always-visible input joined to a "data.humdata.org/dataset/" prefix box.
- **Time Period:**
  - "Start date" and "End date" boxes styled as selects; the icon type can't be identified.
  - An "Ongoing" checkbox with a help icon.
- **Location and Tags:**
  - Single selects in Add.
  - In Edit, chips with no ×: Location is brand-1 / brand-85 (cyan); Tags are neutral-1 (grey).
- **Tags extras:** a "Suggested tags:" line of comma-separated links, then the "See all tags / suggest a new tag" box.
- **Quality checkbox:** sits under the Tags box.
- **"Choose how to share":** three plain radio rows with a medium title and a regular description. No card styling.

### 3.4 Upload files

- **Intro paragraphs:** order, file naming (with a "Learn more" link), formats (with a "Learn more" link), PII
  definition, Microdata definition.
- **"Add more files":** a primary button with a `file-plus` icon, above the list and left-aligned.
- **File card:**
  - White, neutral-3 border, radius-sm, padding about 15 / 20, gap space-14, 20px between cards.
- **Card header:**
  - A 16px icon and "File N" (medium).
  - On the right, "Sort:" (14px) and two 25px caret-square glyphs. They have no border and no disabled state.
- **Body:**
  - "Choose how to upload your file".
  - A row: radio "Upload file" | radio "Import from URL" | Dropbox logo + "Dropbox" | Google Drive logo + "Google
    Drive", separated by pipes.
  - Then one of three states:
    - **URL state:** "Remote file location *", then a "File name *" + "File format *" row, then "Notes about this file".
    - **Upload state:** a drop zone ("Drop file or Browse", 100px, dashed, off-token greys).
    - **Filled state:** a 32px brand-1 file-type tile and the file name.
- **Checkboxes:** "contains Personally Identifiable Information (PII)" and "contains Microdata".
- **Footer:** "Delete this file", right-aligned, 14px medium, underlined, neutral-8, with the icon **after** the label.
- **Section 5:** "5. Add automatic Data Previews (Visible to sysadmin only)". Intro and bullets, "Enable data
  preview" checkbox, "Select which file to preview *" select.
- **Section 6:** "6. Add data visualisations (Optional)". Intro, "Link to visualisation", placeholder "Visualisation
  URL".
- **Terms checkbox**, then Cancel (secondary) and Submit (primary), right-aligned, gap space-4.

### 3.5 Error states

- **Inline errors:**
  - Below the control (after the helper box if there is one).
  - A pink box: error-05 background, error-5 14px text, radius-md, padding space-3 / space-4, no icon.
  - The control border turns error-5. Labels don't change colour.
- **Add errors:**
  - Share mode: "Please select how you want to share your data."
  - Title: "Please provide a title for your dataset."
  - URL: "Please provide a different URL for your dataset as this already exists."
  - Description, Source, Organisation and Maintainer messages, which match `_customize_error_messages`.
  - Visualisation URL: "You can only add four data visualisations."
  - Terms: "Please confirm that your dataset complies with our Terms of Service before submitting."
  - Several fields show a red border with no message.
- **PII and Microdata boxes:** under their checkboxes, both in the error palette. The PII box asks to delete the file;
  the Microdata box explains the disclosure-risk review and the 24-hour notice.
- **Edit errors:**
  - The overdue banner sits under the required note, in the error palette, semibold 16px, not dismissible. Its date
    reads "February 1, 2023".
  - Errors on Title, URL, Description, Visualisation URL and Terms.
- **No change in error state:** the sidebar and the headings.

### 3.6 Quarantine variant (`xl-add-dataset-form2.html`, out of scope, D7)

- A header row: "Add more files" on the left; "Quarantine all files | Release all files" text buttons on the right.
- An unquarantined card has a footer with "Quarantine this file" and "Delete this file".
- A quarantined card:
  - The border turns warning-5.
  - The footer shows the "In quarantine" label (warning-1 / warning-8, 14px, lock icon) on the left, and "Release this
    file" and "Delete this file" on the right.

### 3.7 Token map

| Figma | Token |
|---|---|
| `#101212` / `#2f3536` / `#3f4748` / `#d8e0e1` / `#c4d0d1` / `#ebeff0` / `#fafbfb` | neutral-95 / -85 / -8 / -2 / -3 / -1 / -01 |
| `#1862d8` / `#c44536` / `#f9eceb` | primary-5 / error-5 / error-05 |
| `#d4eae4` / `#0b2d24` | brand-1 / brand-85 |
| `#d48f2a` / `#f6e9d4` / `#553911` | warning-5 / -1 / -8 |
| 4 / 8 / 12 / 16 / 20 / 24 / 40 / 48 / 80px | space-1 / 2 / 3 / 4 / 5 / 6 / 10 / 12 / 20 |
| 2 / 4px radius; `0 1px 4px rgba(0,0,0,.04)` | radius-sm / radius-md; shadow-sm |
| 32px bold serif; 18px semibold; 16px regular / medium / semibold; 14px | `.hdx-display-l()`; `.hdx-heading-h3()`; `.hdx-body-m()` / `-medium()` / `-semibold()`; `.hdx-body-s()` |

Off-token values: `#4b5563` hint, `#333`, `#ebf2fe`, `#007ce1` links, `#d1d5db`, `#eee` / `#ccc` / `#888` drop zone,
30px field gap, 15px card padding, 37px inputs vs 34px selects.

### 3.8 Artefacts (ignored, D28)

- The hidden `hdx@un.org` paragraph, copied from the contact-contributor form.
- The "Your email address *" field.
- The "Source" placeholder on Source and on Tags.
- "Ask a question or provide comments" on the textareas.
- "Creative Commons XXXXX" in the License tip.
- "resources.files" in the Time Period tip, and the stray "*" and "Example?" in the Describe and Description text.
- Source Sans Pro text.
- The "visualiisations" typo.
- Every radio drawn as selected.
- The maintainer error text reused on unrelated fields.

---

## 4. Current vs Figma Comparison

### 4.1 Already matching

- **Copy:** the h1, the intro and the required note.
- **Sections and fields:** the section order and the field set of sections 1–3, the three share options with their
  descriptions, and most field labels and hints.
- **Files:** the file-card field set ("Sort:", upload / URL / Dropbox / Drive, drop zone, name / format / notes,
  PII / microdata, "Delete this file" with the icon after) and "Add more files".
- **Other sections:** the previews and visualisation sections, the terms text and the overdue copy.

### 4.2 Differences

| Area | Current | Figma |
|---|---|---|
| Base / chrome | v1 `page_light.html`, v1 header, Bootstrap grid | v2 header, breadcrumb "Home / Share data" |
| Container | Full-screen iframe popup | A page (the popup isn't shown) |
| Navigation | None | Numbered step sidebar with an active bar |
| Section layout | Bootstrap `col-4` heading / `col-8` fields | 260px heading column / 602px fields, top borders |
| Hints | Tip boxes (bem `info_box`) | Hint above in grey; light-blue helper box below |
| Slug | Preview with edit link (CKAN `slug-preview.js`) | Always-visible prefixed input |
| Dates | jQuery UI datepicker inputs | Select-like boxes |
| Errors | Top banner + inline red text | Pink box under each field; no top banner |
| PII / microdata explainers | Red / plain text | Error-palette boxes |
| Overdue | Bootstrap `alert-danger` | Error-palette banner in the header |
| Terms | Disabled Submit until ticked | Error message after Submit |
| Actions | Full-width "Submit Dataset", Delete, centred Cancel link | Right-aligned Cancel + Submit |

### 4.3 Only in Figma

- Quarantine controls: not built (D7).
- "(Visible to sysadmin only)" on previews: not adopted (D8).
- Four visualisation URLs: not adopted (D9).
- The terms error: not adopted (D10). The share-mode and Title errors: not used (D27).

### 4.4 Only in the current form (kept, D11)

- Archive (edit) and Delete dataset (edit).
- The HDX Connect fields `field_names` / `file_types` / `num_of_rows`.
- The license and methodology "Other" fields.
- The subnational checkbox.
- Drag-and-drop reordering and new files at the top (D12).
- "Please check if the following field is up to date:" on Update Frequency.
- The popups: saving progress, private-dataset info, suggest a tag, confirm delete (D24).
- The share-mode notices: the QA paragraph under Public and the HDX Connect deletion warning (D36).
- The v1 replace drop zone, "Drop file to overwrite or Browse" (D48).

### 4.5 Copy differences (D26)

| # | Current | Figma | Decision |
|---|---|---|---|
| C1 | "1. Choose how to share", "2. Describe dataset", "3. Add additional information", "4. Upload files", "5. Add automatic Data Previews (Optional)", "6. Add other data visualisations (Optional)", "6.a Archive dataset", "7. Confirm and submit" | "Choose how to share", "Describe dataset", "Additional information", "Upload Files", "5. Add automatic Data Previews (…)", "6. Add data visualisations (Optional)", no confirm heading | Numbers from a CSS counter (091 D19 / D40): "Choose how to share", "Describe dataset", "Additional information", "Upload files", "Add automatic data previews (Optional)", "Add data visualisations (Optional)", and "Archive dataset" in edit mode. No "Confirm and submit" heading. The sidebar uses the same labels without "(Optional)" (D14) |
| C2 | "Tip: …" prefix on every tip | No prefix | Figma: no "Tip:" |
| C3 | Title placeholder "Example: Thailand: Rainfall Indicators at Subnational Level" | "ie. Humanitarian Needs Assessment in Afghanistan, Jan-Dec 2026" | Figma |
| C4 | Slug hint "This is how the URL will appear on HDX." | "This is how the URL will appear on HDX, you can change this below." | Figma |
| C5 | Source hint "The source of the data is the entity that collected or created it." | No hint | Figma: no hint |
| C6 | Upload intro "…You can upload multiple files by clicking the 'Add More Files' button and re-order them." | "…You can upload multiple files if you need to by clicking the 'Add More Files' button and re-order them if you need to." | Figma |
| C7 | File naming "…We recommend making sure the name is a clear indication of the file's content as well as the dates of the data it contains." | "Use a consistent file naming convention so that users can reliably find your file. Learn more about file naming conventions." | Figma; the link is `DOCUMENTATION_LINKS['QA_PROCESS']` (docs.humdata.org/publish) |
| C8 | Previews "…insights in your data." / "Enable Data Preview" | "…insights in your dataset." / "Enable data preview" | Figma |
| C9 | "Link to vizualization" / "eg. https://example.com/dataviz" | "Link to visualisation" / "Visualisation URL" | Figma label; the example placeholder stays |
| C10 | "Submit Dataset" | "Submit" | Figma |
| C11 | "Delete this file" + icon after | Same | As both (icon after) |
| C12 | License tip "In general CC BY-IGO or CC-BY are our recommended licenses for data on HDX as they allow others to use data freely…" | "In general "Creative Commons XXXXX" is our recommended license…" | Figma's sentence with v1's two licenses: "In general "CC BY-IGO" or "CC BY" are our recommended licenses for data on HDX as they allow others to use your data freely as long as they credit your organisation. If you are unsure, please consult with your organisation's data policy or legal team. Read more about licenses." |
| C13 | Overdue date "Feb 1 2023" (`%b %-d %Y`) | "February 1, 2023" | Figma: `h.hdx_get_due_overdue_date(data, format='%B %-d, %Y')`; the helper is unchanged |

---

## 5. Component & System Mapping

| Figma piece | v2 component (file, params) | Gap |
|---|---|---|
| Page shell | `v2/page.html` + `hdx-v2-content-columns` (`__sidebar --xl-only`, `__content`), the `package/hdx_read.html` pattern; block `breadcrumb_items` with `v2/components/breadcrumb.html`: "Home / Share data" or "Home / Edit data" (D33) | None |
| Step sidebar | `v2/components/anchor-links.html` (`items`, `heading`, `extra_classes='c-anchor-links--numbered'`, `with_mobile_dropdown`). Sticky by default; IntersectionObserver scrollspy; left primary-5 bar | Bar width (4px vs Figma 2px) stays the component's |
| Section groups | 091: `<section class="hdx-v2-content-columns hdx-v2-content-columns--stack …__group">`, h2 in `__sidebar` (25%), fields in `__content`. Counter numbering, top border and padding live in `.hdx-v2-custom-page-form` (`LESS/pages/sysadmin.less`) | Page-owned rules → shared form layer (D13) |
| Header | `<h1>` + intro + note, as 091 `__note` (semibold error-5) | None |
| Text / textarea | `text-field.html` (`size='l'` (D44), `label`, `required`, `description` above, `hint` below, `multiline`, `rows`, `errors`, `input_attrs`) | `leading` slot for the File name tile (D49) |
| Native select (frequency, license, methodology) | `select.html` (`options`, `placeholder`, `selected`, `description`, `errors`) + `hdxV2.wireReveal` for "Other" | `size='l'`, native and Select2 (D44) |
| Searchable select (organisation, maintainer, format) | `select.html searchable=True` (`components/select.js`, `v2-select2-*` bundles), `select_attrs={'data-source': …}` | Maintainer needs an extra `org` param read from another field; format needs the format-autocomplete source (D25) |
| Locations / tags chips | `select.html multiple=True searchable=True` (`chip_color='cyan'` for locations; grey default for tags) | Free-text entry for HDX Connect `field_names` / `file_types` (`tags=True`, D55) |
| Suggested tags | None (v1 `tag_recommender.js`; 094 D7 dropped it for showcases) | Page JS on `hdx_recommend_tags` |
| Slug | `slug-preview.html` (`prefix`, `target_id`, `description`, `errors`; `v2-slug-preview-scripts`) | `size` param (D16, D44) |
| Dates + Ongoing | None for dates (only the LESS-only `c-dropdown-calendar` month panel). `checkbox.html` for Ongoing, `info-icon.html` for its tooltip | New date-picker component (D17, D32), `size` param (D44) |
| Radios with description | `radio.html` (`description`, `c-radio--has-description`) in a `fieldset` / `legend` (091) | `errors` param (D23); `size='m'` (D43) |
| Checkboxes | `checkbox.html` (`errors`, `attrs`); `.v2-checkbox-row()` / `.v2-checkbox-group()` | None |
| Helper boxes (and the Public QA notice, D36) | `info-box.html` (`paragraphs`; light blue, `info-fill` icon, padding space-6) | Compact option: no icon, smaller padding, body-s (D20) |
| Notice boxes (PII, microdata, overdue, HDX Connect deletion) | `alert.html` (`variant` error / warning / info / success, `dismissible=False`) | None (D22, D36) |
| Inline errors | `errors=` on each field (`__error`, red body-s text, red border); `hdxV2.setFieldError` for JS | `setFieldError` handles only text-field and checkbox → select, radio group, file, slug (D21, D23) |
| File list and cards | `config-item.html` form mode, 091 recipe (`draggable: False`, `title_tag: 'h3'`, `move_buttons: True`, `collapsible: False`, `delete_position: 'footer'`, `delete_label`), `c-config-item-list` with `data-title-format="File {n}"`, `config-item.js` (`v2-config-item-scripts`) | Form mode has no Sortable and no programmatic add; new cards append at the end → add-position option and opt-in form-mode Sortable (D12) |
| Sort arrows | `c-config-item` `move_buttons` (§5.1) | None |
| Upload source row | `radio.html` ×2 + `text-button.html` / `button.html` tertiary | `underline` param on `text-button.html` (D50); the v1 PNG logos as `<img>` (D18) |
| Drop zone / file tile | `image-upload.html` (upload / url / clear contract, `image-upload:change`, `config-item:add` aware); `file-type-icon.html` in the File name field | Optional drag-and-drop (D19, D48); the tile goes in the File name input (D49) |
| Buttons | `button.html` (Add more files: primary `file-plus.svg`; Cancel tertiary (D34); Submit primary), `text-button.html` | None |
| Dialogs | `drawer.html` (`c-drawer`), `spinner` (068) | Page overlay with `c-spinner` and a live region for saving progress (D24) |
| Divider | `<hr class="c-divider">` | None |

### 5.1 Sort arrows: what exists

- **Where they exist:** only in `c-config-item` with `move_buttons=True`. That is the 091 custom-page form. The
  sysadmin config editors (087 Package Links, 088 Products Menu, 089 Homepage Highlights) are drag-only (Sortable).
- **Markup:** inside `c-config-item__header` / `__actions` / `__move`, a "Sort:" label (body-s, `aria-hidden`), then
  two `button.html` icon-only tertiary size-s buttons. Icons are `chevron-up.svg` / `chevron-down.svg` (091 D15:
  Figma's caret-square glyphs aren't in the icon set). Each button is `aria-labelledby` its own label plus the card
  heading, and carries `data-config-item-move="up|down"`.
- **Behaviour** (`config-item.js`):
  - `move()` swaps the card with its neighbour, `renumber()` rewrites the titles, and `refreshMove()` disables the
    first card's up and the last card's down.
  - Focus stays on the pressed button, or moves to the other button if the pressed one became disabled.
  - An `aria-live` region (`data-config-item-status`, `data-move-message`) announces the new position.
- **Reuse:** the arrows can be reused for file cards with no change. Posted field names don't follow the visual
  order on their own; 091 renames them on submit (`pages/custom-page-form.js`). For files, the order goes to
  `package_resource_reorder` instead.

### 5.2 Gaps summary

- New date-picker component (D17, D32).
- Drop zone on `c-image-upload` (D19, D48); file tile in the File name input (D49).
- Suggested tags (page JS).
- `select.js` source options (D25).
- `c-config-item` form-mode Sortable, programmatic add and add position (D12).
- Radio `errors` and wider `setFieldError` (D23).
- Compact `c-info-box` (D20).
- An XHR upload with progress (`hdxV2.post` uses `fetch`, which has no upload progress).
- Saving-progress overlay (D24) and the v2 contribute popup snippet (D31).

---

## 6. Options & Recommendations

### 6.1 Container (D1: B)

| | A. Top-level page | B. Keep the iframe popup |
|---|---|---|
| Change | `contributeAddDetails` navigates to the form URL (anchor kept). No preload. `v2/page.html` stops rendering `details.html`. The navbar button gets a real `href` | Render the v2 page inside the iframe. Add `.hdx-v2-header a`, `.hdx-v2-footer a` and the header search form to the link capture. Add a null check for `#addDataPopup`. Give the popup dialog semantics and focus management (D31) |
| UX | Normal page: Back, refresh, new tab and deep links all work | Unchanged popup feel. Back and refresh act on the host page |
| Analytics | "page view" fires when the form is actually opened, so the volume drops (the preload inflates it today). "dataset create" `page title` becomes the form page. "link click" events are unchanged | Unchanged, including the preload page views |
| Quick-edit anchors | Native `#id` scroll; needs a scroll offset and a re-scroll after Select2 and the file list load | Unchanged |
| v1 hosts (QA dashboard, light dataset page) | Still open the iframe (v1 `contribute.js` stays untouched), so the v2 form must work inside an iframe: links target the top window, the redirect uses `window.top` | Same |
| Side effect | The v1 `popup-scripts` bundle leaves v2 pages | The bundle stays |

### 6.2 Client logic and save pipeline (D2: A)

| Option | Summary | Fit |
|---|---|---|
| **A. New v2 page JS** | `fanstatic/v2/pages/dataset-form.js` (plus a save module if large), built on the v2 components. The save pipeline is ported step for step against the same endpoints and the same POST contract: validate with resources, metadata JSON with empty fields dropped, changed resources one at a time (full-dict round-trip, `batch_mode`, XHR multipart with progress), deletions, reorder, then redirect | Meets every constraint. Highest test effort. Analytics calls are re-wired to the same events |
| B. Fork the Backbone app into `fanstatic/v2/` | Only the models and sync code carry over. The views depend on Bootstrap classes, the bem Select2 module, Underscore templates in Jinja and `ckan.module` sandbox topics | Two diverging copies, plus Backbone and Underscore on a v2 page |
| C. Load `contribute-flow-scripts` on the v2 page | Its preloads pull in v1 `contribute-flow-styles` / `search-styles` and `hdx-autocomplete`. `bem-blocks-scripts` loads Select2 a second time. The jQuery UI datepicker needs v1 CSS | Not permitted (v1 bundle on a v2 page) |
| D. Server-side form post with re-render | One multipart POST with all files, errors rendered on the server, PRG | Needs backend changes. Loses per-file progress and keeps no file input after an error. Very large requests (`ckan.max_resource_size` per file). All-or-nothing saves |

### 6.3 Phasing (D3)

The form has one Submit and one save pipeline, so it can't ship section by section without a half-v1, half-v2 page.
096 ships everything in one release: the iframe fixes (§6.1 B), all sections, files, edit mode, HDX Connect, Archive,
Delete, popups and analytics.

### 6.4 Template strategy (D4)

- **Replace in place (the 082 / 094 precedent).** `contribute_flow/create_edit.html` extends
  `v2/page.html`. The `/contribute/*` views don't change. The v1 bundles (`contribute-flow-scripts`,
  `contribute-flow-styles`, `bem-blocks-*`, `user-waiting-scripts`, `request-tags-scripts`) become orphans and stay
  untouched.
- **Alternative: a new template plus a config switch** in `_prepare_and_render`, for a dark launch and quick rollback.
  This departs from the precedent and keeps two forms alive.

No shared v1/v2 snippet is involved, so no `v2=true` branching is needed.

---

## 7. Functionality & Mixpanel Preservation

- **Routes and auth:** the `/contribute/*` URLs, the auth checks, the redirect for denied users, and the old-link
  notice pages.
- **Posted fields:** every field name and value convention in §2.4:
  - sentinels: `-999` frequency, `-1` methodology, `first_resource` / `no_preview` preview;
  - empty fields dropped;
  - the `private` radio values;
  - `customviz__N__url`, `resource_grouping`.
- **Save order:** validate (with resources unless HDX Connect) → metadata → changed resources one at a time → deletions
  → reorder → redirect.
- **Resources:** the full-dict round-trip on `resource_update`, `batch_mode=DONT_GROUP`, CSRF in the header.
- **Validation:** the client rules (at least one file, tags for HDX Connect), `_customize_error_messages` and the
  "Resource N" mapping; a `name` error reveals the slug field.
- **HDX Connect:** hide files, license, previews and visualisations (D38); show `field_names` / `file_types` / `num_of_rows`; change which
  fields are required; warn before files are deleted on conversion.
- **Field behaviour:**
  - maintainer filtered by organisation;
  - format guessing and the archive-format warning;
  - the preview select kept in sync with the file list;
  - "Other" reveal for license and methodology;
  - Ongoing disables the end date;
  - the sysadmin `quality` checkbox and crisis tags;
  - defaults from `generate_mandatory_fields`;
  - the edit prefill;
  - the overdue alert.
- **Files:** upload, URL, Dropbox (`linkType: "preview"`) and Google Drive with their current configuration; new card at
  the top, drag and arrows (D12); PII disables the terms checkbox, which gates Submit (D10); deletions are queued until
  submit.
- **Popups:** private-dataset info with its localStorage key; suggest a tag (`/request_tags/suggest`); confirm and
  purge on Delete; saving progress.
- **Ids and blocks:** the 12 quick-edit ids (§2.2), the `analytics_*` and `subtitle` blocks.
- **Mixpanel:**
  - `page view` with its page title;
  - `link click` "header add data" (unchanged entry point);
  - `dataset create` (new only, after validate, before create, the 500 ms wait, the same property set with real
    `is private` / `dataset availability` / `is cod` values, D6);
  - `link click` "dataset recommended tag".
  - The server events are untouched.
- **Tests:** keep `test_pages/test_dataset.py` green, which needs `select#field_locations` with "world" first.

---

## 8. Responsive & Accessibility

### 8.1 Breakpoints (no MD/SM exports, D29)

- **XL:** sidebar + main column; each group is heading column + fields (091).
- **Below XL:**
  - The groups stack (`--stack`): heading above fields, as 091 D16.
  - The sidebar is hidden (D14).
- **SM:** the file-card rows (File name + File format, the upload-source row) wrap to one column. Cancel and Submit
  stay right-aligned.

### 8.2 Accessibility

- **Grouping:** the share mode and each upload-source choice are a `fieldset` + `legend`. Required fields keep native
  `required` plus the `aria-hidden` asterisk.
- **Errors:** the error elements need ids, `aria-describedby` and `aria-invalid` (missing in the v2 field components
  today). After a failed Submit, focus goes to the first invalid field, or to the form-level `c-alert` when only
  field-less errors exist (D35).
- **Saving progress:** an `aria-live` region ("Saving file N of M"). Focus is managed on open and close of every
  drawer and of the contribute popup (D31).
- **File list:** move announcements and focus after add, delete and move, as `config-item.js` already does. The drop
  zone needs a keyboard-reachable "Browse" button.
- **Sidebar:** `aria-current` on the active step (anchor-links does this).

---

## 9. Decisions Taken

| # | Question | Options | Recommended | Decision |
|---|---|---|---|---|
| D1 | Container | Top-level page / keep the iframe popup | Top-level page | **Keep the iframe popup.** The v2 page renders inside it. The preload and the Mixpanel "page view" semantics stay as they are. The popup's link capture gains the v2 header and footer, `#addDataPopup` gets a null check, and the popup gets dialog semantics |
| D2 | Client logic | New v2 page JS / fork Backbone / server-side post | New v2 page JS | **New v2 page JS**, with the save pipeline ported step for step against the same endpoints (§6.2 A) |
| D3 | Phasing | Three steps / container + form / everything in 096 | Three steps | **Everything in 096**: the iframe fixes and the full v2 form in one release |
| D4 | Template | Replace in place / new template + config switch | In place | **Replace `contribute_flow/create_edit.html` in place** |
| D5 | Current behaviours (§2.9) | Strict parity / fix what the new JS touches | Fix | **Fix:** a visible error and a closed overlay on file-save failure, aborted responses handled as errors, license / tag / visualisation errors inline, PII changes saved. The Live-frequency timing and the legacy methodology values stay as they are |
| D6 | `dataset create` properties | Keep as is / real values | Keep as is | **Real values.** The page passes `sendDatasetCreationEvent` the share mode in the shape it reads (`private`, `is_requestdata_type`) and all tags as one comma-joined `tag_string`, so `is private`, `dataset availability` (public / private / metadata only) and `is cod` (`cod` among the tags) are correct. `google-analytics.js` is unchanged. Event name, timing and the other properties are as before |
| D7 | Quarantine controls (`xl-add-dataset-form2.html`) | — | — | **Out of scope.** The form keeps v1 behaviour, with no quarantine controls |
| D8 | Data previews audience (Figma: sysadmin only) | v1, everyone / sysadmins only | v1 | **v1: visible to everyone.** The heading has no sysadmin note |
| D9 | Visualisation URLs (Figma: up to four) | v1, one / up to four | v1 | **v1: one URL.** The "four" error isn't used |
| D10 | Terms | Figma error after Submit / v1 disabled Submit | Figma | **v1: Submit stays disabled until the terms checkbox is ticked.** There is no terms error message. PII unticks and disables the checkbox; as in v1, only PII boxes ticked in the session count, and deleting such a card releases it |
| D11 | Elements not in Figma (§4.4) | per element: v1 position / alternative | as listed | **Archive:** its own "Archive dataset" section after the visualisations, edit only, with a sidebar step in edit mode. **Delete:** a tertiary button at the left of the action row, edit only, with a `c-drawer` confirm (082 / 092), the same purge call and the redirect to search. **The rest as v1:** HDX Connect fields in "Additional information" (HDX Connect mode), the "Other" textareas under their selects, subnational under Location. "Need help?" and the files count are dropped (D45) |
| D12 | File list | end + drag + arrows / top + drag + arrows / end + arrows only | end + drag + arrows | **v1: new card at the top, drag-and-drop and Sort arrows.** `c-config-item` gets an add-position option and an opt-in Sortable for form mode. JS builds every card from one `<template>`; the 20-inline / fetch split stays |
| D13 | Group layout | shared form layer / page-class copy | Shared | **Shared form layer:** 091's group rules (counter numbering, top border, padding, heading style) move out of `.hdx-v2-custom-page-form` into `.hdx-form-*()` mixins in `LESS/mixins.less`, used by both forms. 091 keeps its classes and its CSS rules |
| D14 | Step sidebar | heading: match h1 / "Share data" / "On this page"; sticky / static; below XL: hidden / mobile dropdown | match h1, sticky, hidden | **`c-anchor-links--numbered`**, heading = the h1 ("Share data" / "Edit data"), sticky (component default), hidden below XL (091). Edit mode adds the "Archive dataset" step (D11) |
| D15 | Widths | generic 25% columns / Figma px | Generic | **Generic columns:** the 25% `hdx-v2-content-columns` sidebar and the 25% `--stack` heading column (091 D34) |
| D16 | URL / slug | `c-slug-preview` / Figma prefixed input | `c-slug-preview` | **Keep `c-slug-preview`** (091 D5) |
| D17 | Time Period dates | native date input / new v2 component / vendored library | Native | **New v2 date-picker component** (template + LESS + JS). Display as v1 ("November 16, 2026"), posts `yyyy-mm-dd` to the hidden `date_range1` / `date_range2`, start and end limit each other, "Ongoing" disables the end date, and `ui_date_range1` stays the quick-edit anchor |
| D18 | Upload source row | radios + text buttons with the v1 PNGs / new SVG icons / segmented control | v1 PNGs | **Two `c-radio` (Upload file, Import from URL) + Dropbox and Google Drive as tertiary text buttons** showing the existing PNG logos (`/images/icons/dropbox.png`, `drive.png`) as `<img>`. No new icons |
| D19 | Drop zone | extend `c-image-upload` / new `c-file-upload` | Extend | **Extend `c-image-upload`:** optional drag-and-drop in the blank and attached states (D48). Existing callers are unchanged by default |
| D20 | Helper boxes under fields | compact `c-info-box` / `c-info-box` as is / plain hint | Compact | **Compact `c-info-box` option:** no icon, smaller padding (space-3 / space-4), body-s. Existing callers are unchanged |
| D21 | Inline field errors | v2 error / Figma pink box everywhere / pink box on this form | v2 error | **Keep the v2 field error** (red text under the control, red border) |
| D22 | Notice boxes | PII error, microdata info, overdue warning / all error / overdue error | First | **`c-alert`, not dismissible:** PII `error`, microdata `info`, the edit overdue notice `warning` |
| D23 | Client-side errors | extend `setFieldError` + radio errors / page-local | Extend | **Extend `hdxV2.setFieldError`** to select (Select2), radio group, file and slug, with `aria-invalid` / `aria-describedby`; `radio.html` gets an `errors` param |
| D24 | Dialogs and saving progress | drawers + overlay / drawers for all | Drawers + overlay | **`c-drawer`** for private-dataset info (same localStorage key), suggest a tag (`/request_tags/suggest`) and the Delete confirm. **Saving progress:** a full-page overlay with `c-spinner` and an `aria-live` "Saving file N of M" message |
| D25 | `select.js` | extend / page-local | Extend | **Extend `select.js` / `select.html`** with optional data attributes: an extra query param read from another field (maintainer `org`), the format-autocomplete source; free-text entry (`field_names`, `file_types`) is the `tags` param (D55). Existing selects are unchanged |
| D26 | Copy | per row (§4.5) | C1–C2, C8–C10 Figma; C3–C7, C12 current | **§4.5 Decision column.** Figma wording throughout. C7's link goes to `QA_PROCESS`. C12 keeps v1's two licenses in Figma's sentence. C13 uses "February 1, 2023" |
| D27 | New error copy | Title message + no share-mode / v1 messages | First | **v1 messages.** An empty title never errors (core copies the URL slug into it), so the Title message would never show. No share-mode message, because the radio always has a value |
| D28 | Figma artefacts (§3.8) | ignore / review individually | Ignore | **Ignored.** Where Figma has an artefact, the current text stays (e.g. the Time Period tip says "all files") |
| D29 | MD / SM | as 091 / two-column from MD | As 091 | **As 091 (§8.1):** sections stack below XL, the sidebar is hidden, and file-card rows wrap to one column on SM |
| D30 | Tests | render + Title message / render only / none | First | **Extend `PKG/tests/test_pages/test_dataset.py`:** `/contribute/new` and `/contribute/edit/<id>` render 200 with the v2 h1 and the quick-edit ids (`field_archived` in edit only). The existing tests stay green. No JS tests |
| D31 | Popup markup | v2 snippet, Esc = Cancel / v2 snippet, no Esc / keep `details.html` + JS | v2 snippet, Esc = Cancel | **v2 snippet, no Esc.** `v2/page.html` block `contribute_widget` renders a v2 snippet with `role="dialog"`, `aria-modal`, a label, focus into the iframe and the page behind `inert`. The v1 `popup-scripts` bundle leaves v2 pages; v1 pages keep `details.html`. Cancel stays the only way out |
| D32 | Date-picker panel (no Figma) | build on `c-dropdown-calendar` / wait for Figma | Build on it | **Build on the LESS-only `c-dropdown-calendar` panel** (`LESS/components/dropdown.less`): its header, prev/next and grid styles, plus a day grid with previous / next month. The title switches to the month grid (previous / next year). No typing |
| D33 | Breadcrumb | per mode (v1) / "Share data" in both (Figma) / edit via the dataset | Per mode | **Per mode, as v1:** "Home / Share data" in add, "Home / Edit data" in edit |
| D34 | Cancel style | tertiary (082 / 079) / secondary (Figma) | Tertiary | **Tertiary**, as the other v2 page forms |
| D35 | Form-level errors | alert for field-less errors / always a summary (v1) / alert above the action row | Field-less | **091 pattern:** field errors stay inline. Errors with no field go in a non-dismissible `c-alert` at the top of the form: "at least 1 file", server or connection errors, aborted responses, file-save failures (D5) and server errors that match no field (their own text). v1's generic banner text is not used |
| D36 | Share-mode notices (not in Figma) | compact info box + warning / info box + error / two `c-alert`s | First | **QA paragraph under Public:** compact `c-info-box` (D20). **HDX Connect deletion notice:** `c-alert` `warning`, not dismissible. Both keep v1's copy and show/hide conditions |
| D37 | Navbar "Add data" inside the iframe | drive the top popup / hide on the form page / leave inert | Drive the top popup | **Hidden on the form page:** `v2/header.html` gets a boolean param (default on) that drops "Add data" from the navbar and the SM offcanvas footer; the form's `header_core` turns it off. Not `minimal`, so the rest of the header stays |
| D38 | Sections hidden for HDX Connect | v1 (files, license, previews, visualisations, Archive) / files, license, previews / + visualisations | Files, license, previews | **Upload files, License, Previews and Visualisations; Archive stays.** v1 also hides Archive, a side effect of the HDX-10450 section reorder, which breaks the card "Archive" quick-edit |
| D39 | Validation | server only (v1) / browser checks first | Server only | **Server only:** `novalidate`, all errors from the validate call. JS toggles the asterisk and `required` per share mode |
| D40 | File-save payload | resource fields only / v1's payload | Fields only | **v1's payload,** `originalHash` included |
| D41 | Overdue "Please check…" line (D11) | warning alert / line in the field / drop | Alert | **Non-dismissible `c-alert` `warning` above Update Frequency** |
| D42 | Figma asterisks on "Select which file to preview" and Caveats | v1 / preview only / both | v1 | **v1: no asterisks** (neither is required) |
| D43 | Share radios (Figma: 16px, medium label) | `c-radio` size param / label weight only / page override | Size param | **`radio.html` `size='m'`** on the three share radios: label `.hdx-body-m-medium()` neutral-95, description `.hdx-body-m()` neutral-85. Default `'s'` is unchanged |
| D44 | Input size (Figma 37px, 16px, padding 8 / 12 / 8 / 16) | text inputs + slug at L / text inputs only | With slug | **L** for every text-field, select and date picker in the form and the file cards (Figma draws selects 34px / 14px): `select.html` `size='l'` (40px, 16px medium, native and Select2); `slug-preview.html` and `date-picker.html` get a `size` param (default `'m'`). The Suggest-a-tag drawer stays M |
| D45 | "N files (drag and drop to sort)" and "Need help?" (not in Figma, D11) | remove / keep | Remove | **Both removed:** "Add more files" stands alone, and nothing sits between the terms and the buttons |
| D46 | Terms checkbox placement | top row of the action area / own bordered block | Action area | **The first, full-width row of the action area**, outside the sections. The action row's top border is the only separator, as Figma's terms block |
| D47 | PII ↔ Microdata gap (Figma 4px, 8px in the errors frame) | 8px / 4px / 16px | 8px | **8px (space-2)** between the two checkboxes and their notices |
| D48 | Drop zone after a file is chosen; Browse colour | v1 replace drop zone (user) | — | **v1:** the attached state stays a drop zone, "Drop file to overwrite or Browse", with no tile or file name. Browse is the secondary (black) text button, as Figma, at size L |
| D49 | File-type tile (Figma: 32px tile + file name in the File name input) | uploads only / always; neutral / by format; map in `CONSTANTS` / copied into the page JS | Uploads only, neutral; `CONSTANTS` | **Inside the File name input** (text-field `leading`), **for uploaded files only, colour and icon by format.** The format → category map lives in `CONSTANTS['FORMAT_ICON_CATEGORIES']`; `hdx_format_to_icon_category` reads it and the page gets it as JSON. The tile follows the File format select. It is 24px (`size='xs'`), so the field keeps its L height |
| D50 | Dropbox / Google Drive underline (Figma: none) | text-button param / page override | Param | **No underline:** `text-button.html` `underline=False` (`c-text-button--no-underline`); the default `true` keeps other callers underlined |
| D51 | Page fetch wrappers (CONVENTIONS: no local wrappers) | `hdxV2.post` + JSON bodies / form posts only / keep | `hdxV2.post` + JSON | **Every POST goes through `hdxV2.post`**, which sends a plain-object body as JSON; the API replies are checked for `success` |
| D52 | Unused v1 ids; unreferenced Time Period hint | drop + wire / drop / wire / keep | Drop + wire | **v1 ids nothing reads are dropped** (the 12 quick-edit ids stay); the Time Period fieldset is `aria-describedby` its hint |
| D53 | jQuery in page JS (vanilla rule) | vanilla reads + doc / doc only / `select.js` native events | Vanilla reads + doc | **jQuery only to listen to or set a Select2 field** (Select2 fires `change` through jQuery only); value reads are vanilla |
| D54 | Section 3 "this support page" link (the old Centre metadata page) | `DOCUMENTATION_LINKS` key / inline URL | `DOCUMENTATION_LINKS` key | **`DOCUMENTATION_LINKS['METADATA']`** (docs.humdata.org/about/hdx-metadata); the link title is "HDX Metadata" |
| D55 | Free-text entry on Field names / File types (Select2 reads `data-*` attributes over the JS options, so `data-tags=""` turned tag mode off) | `data-tags="true"` / `select.js` ignores the value / `select.html` param | `data-tags="true"` | **`select.html` `tags=True`** renders `data-tags="true"`; both HDX Connect selects use it; `test_new_dataset_page` counts both |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/contribute_flow/create_edit.html` | Rewritten on `v2/page.html` (D4) |
| `THEME/fanstatic/v2/pages/dataset-form.js` (new) | Form logic and save pipeline (D2, D5, D6) |
| `THEME/templates/contribute_flow/snippets/{resource_fields,request_tags_drawer}.html` (new) | File card fields; "Suggest a new tag" drawer (D24) |
| `THEME/fanstatic/webassets.yml` | `v2-dataset-form-page-styles` / `-scripts`; the scripts bundle also takes the unchanged `contribute_flow/hdx-google-picker.js`. The date-picker CSS / JS join `v2-components-styles` / `-scripts` |
| `LESS/pages/dataset-form.less` (new), `LESS/mixins.less`, `LESS/pages/sysadmin.less` | Page layout; 091's group rules move to the shared mixins (D13) |
| `THEME/fanstatic/v2/contribute.js`, `THEME/templates/v2/page.html` (block `contribute_widget`), `THEME/templates/v2/contribute-popup.html` (new), `LESS/layout.less`, `THEME/templates/v2/header.html` | Iframe link capture for the v2 header and footer, `#addDataPopup` null check, dialog semantics (D1, D31); `show_add_data` (D37) |
| `THEME/templates/v2/components/{radio,info-box,image-upload,config-item,select,slug-preview,text-field,text-button,file-type-icon}.html`, `THEME/fanstatic/v2/components/{select,config-item,image-upload}.js`, `THEME/fanstatic/v2/utils.js`, matching `LESS/components/*.less` (`input-field.less` for the text-field, `buttons.less` for the text-button, `label.less` for `c-file-type`), `LESS/components/anchor-links.less` | Component options (D12, D19, D20, D23, D25, D43, D44, D48, D49, D50); config-item `delete_icon_position` (C11); anchor-links `[hidden]` steps; `hdxV2.post` JSON bodies (D51) |
| `THEME/helpers/constants.py`, `THEME/helpers/helpers.py` | `FORMAT_ICON_CATEGORIES`, read by `hdx_format_to_icon_category` (D49) |
| `PKG/helpers/constants.py` | `DOCUMENTATION_LINKS['METADATA']` (D54) |
| `THEME/templates/v2/components/date-picker.html`, `LESS/components/date-picker.less`, `THEME/fanstatic/v2/components/date-picker.js` (new), `LESS/components/dropdown.less` | D17, D32, D44 |
| `THEME/templates/v2/components.html` | Demo entries for visual component changes |
| `PKG/tests/test_pages/test_dataset.py` | D30 |
| `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md`, `PROGRESS.md` | Updated at implementation |

---

## 11. Risks & Edge Cases

- **Data loss on update:** a partial resource dict sent to `resource_update` wipes the fields that are left out.
- **Mode switch:** converting a dataset with files to HDX Connect deletes them on the server. The warning must
  survive.
- **Large lists:** datasets with more than 20 files load through `package_show_edit`; the file list and preview select
  must wait for it.
- **Partial save:** the metadata is saved before the files, so a file failure leaves a dataset with missing files.
- **"Ongoing":** it relies on the empty end date being dropped from the POST.
- **Live frequency:** it's rejected only at validate time, when resources are included.
- **Quick-edit:** anchors that point at Select2 fields scroll before the widget is ready.
- **Pickers:** the Dropbox and Google Drive pickers are tied to the site domain and their current configuration; test
  on staging.
- **Inside the iframe (D1):** the v2 navbar renders in the form page without "Add data" (D37). The header search form
  must act on the top window, and the page must not start a nested popup.
- **Legacy data:** free-text methodology values render empty and block re-saving a public dataset.
