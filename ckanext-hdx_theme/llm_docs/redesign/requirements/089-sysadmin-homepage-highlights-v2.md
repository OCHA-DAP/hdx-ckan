# 089 — Sysadmin Dashboard: Homepage Highlights (v2 Migration)

**Scope:** `/ckan-admin/carousel/show` (`hdx_carousel.show`), the editor of the homepage highlights, moved onto the
084 sysadmin shell and the shared `admin/config-item-base.html` editor (087, 088 D12). Also in scope: the thumbnail
control (an extension of `c-image-upload`, D1–D4), file posting and New Item initialisation in `config-item.js`
(D11), a two-column list layout (D5), fixes in the kept v1 endpoints with their tests (D12, D13), and the
non-integer `order` fix in the Package Links and Products Menu views (D14).

**Excluded:**
- The homepage highlights section (043): `c-highlight-card`, the carousel JS, `hdx_get_carousel_list()` and its
  three-item cap.
- Custom Pages, the last v1 sysadmin page.
- The stored shape of `hdx.carousel.config` and the actions `hdx_carousel_settings_show` / `_update`.
- Keyboard reordering, a success message, an unsaved-changes warning, an empty-state message (088 D8), new
  analytics events.

**Figma source:** `xl-sysadmin-homepage-highlights.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. Compared with `xl-sysadmin-package-links.html` (§3.3).

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `hdx_carousel.show` (`/ckan-admin/carousel/show`). Reached from the sysadmin menu (`homepage_highlights`), the header user menu, v1's admin tabs ("Carousel") and the v1 header's "Carousel" icon |
| Objective | v2 page on `admin/config-item-base.html` (`nav_active='homepage_highlights'`, `page_label=_('Homepage Highlights')`) with Figma's layout, keeping the endpoints, the multipart payload, file storage, save order, auth and reload on success |
| Strategy | **Direct replacement** of `THEME/templates/admin/carousel.html` (no `?v2` gate, as 084–088) |
| Shared work | `c-image-upload` (082) gains optional params for the thumbnail (D1–D4); `config-item.js` posts files and announces New Item cards (D11); `c-config-item-list` gains a grid layout (D5). Defaults keep Package Links, Products Menu and the organisation logo field unchanged |

---

## 2. Repository Audit Findings

### 2.1 Routes and auth

All three views are in `THEME/views/custom_settings.py`.

| Endpoint | URL | Notes |
|---|---|---|
| `hdx_carousel.show` | `/ckan-admin/carousel/show` (GET) | Renders the editor with the list as a JSON string in `data['hdx.carousel.config']` |
| `hdx_carousel.update` | `/ckan-admin/carousel/update` (POST, multipart) | Creates or replaces one item from form fields and an optional `graphic_upload` file; returns the whole config as a JSON string |
| `hdx_carousel.delete` | `/ckan-admin/carousel/delete/<id>` (POST) | Removes one item and its uploaded file; returns the whole config |

- **Auth:** every view calls `check_access('hdx_carousel_update')` (`THEME/helpers/auth.py`:
  `Permissions(user).has_permission(PERMISSION_MANAGE_CAROUSEL)`, label "Manage Carousel and Dataviz Gallery").
  Sysadmins pass through the CKAN bypass. No view catches `NotAuthorized` and CKAN core has no handler for it, so
  guests and users without the permission get a 500 (the 087/088 views abort 403).
- **Menu:** `hdx_get_sysadmin_nav_sections()` already lists `homepage_highlights` → `hdx_carousel.show` under that
  check, after All Users.
- **2FA:** `/ckan-admin/carousel/show` is not in `_before_request` `protected_urls` (unchanged).
- **CSRF:** v1 JS sends `hdxUtil.net.getCsrfTokenAsObject()` headers; `hdxV2.post` does the same.

### 2.2 Stored data and the homepage

- System-info key `hdx.carousel.config`: a JSON list of `{id, title, description, graphic, url, order, newTab,
  embed, buttonText?}`, read by `hdx_carousel_settings_show` and written by `hdx_carousel_settings_update` (both in
  `THEME/helpers/actions.py`). When nothing is stored, `show` receives `INITIAL_CAROUSEL_DATA`
  (`THEME/helpers/initial_carousel_settings.py`): eight items with an `order` but no `id`, graphics under
  `/images/homepage/`.
- `update()` builds the item in `_process_request()`: `title` required, `description`, `graphic`, `url`, `order` as
  int, `newTab` / `embed` from `'true'`, `buttonText` only when posted, a uuid when no id is posted. `_persist_file()`
  then stores a posted `graphic_upload` through `GlobalUpload` (`THEME/helpers/uploader.py`) as
  `<first 4 characters of the id>_<uuid><extension>`. It deletes the previous `graphic` file, then sets `graphic`
  to `/global/<filename>` (`hdx_global_file_server.global_file_download`). The list is sorted by `order`.
- `delete()` removes the item and deletes its `graphic` file by basename; a static `/images/...` graphic only logs a
  failed removal.
- `GlobalUpload.upload()` rejects a file over `ckan.max_image_size` (MB, default 2) with `GlobalUploadException`.
- **Consumer:** the v2 homepage (`home/index.html`) renders `h.hdx_get_carousel_list()`, the first **three** items
  (`max_items=3`, fixed by 043), as `c-highlight-card`s with `image_url=item.graphic`, `title`, `href=item.url` and
  `open_new_tab=item.newTab`. The card image is 10rem high, card-wide, `object-fit: cover`; clicks are tracked by
  `hdx_click_stopper` with `link_type` `carousel`. `description`, `embed` and `buttonText` reach no page: their v1
  renderer `home/snippets/hdx_carousel_item.html` has no callers.

### 2.3 v1 page

- `admin/carousel.html` extends v1 `admin/base.html` (subtitle "Administration"). It uses:
  - Bootstrap rows / `col-*`, inline styles and a leftover `data-module="hdx_custom_pages"`;
  - the config JSON in a hidden `#carousel-config-saved-data` div and an underscore `#carousel-item-tpl` template;
  - an intro ("Configure the homepage carousel items", "On the desktop view the carousel items are split into pages
    of 4 items, on mobile they are shown one by one") above a reference screenshot of the v1 carousel
    (`/images/homepage-carousel-sample.png`);
  - a sidebar "Homepage Carousel" help panel listing the fields, with Embed, Button text and New Window left blank.
- `fanstatic/admin/carousel.js` (Backbone):
  - **Card:** header "Carousel Item {order}" (the whole header is the drag handle), trash link, chevron toggle.
    Cards start **collapsed**, two per row, showing only a "Preview Item": a mock-up of the v1 carousel tile (image,
    "Explore" or button-text button, title, description). An open card spans the row with the preview beside the
    fields.
  - **Fields:** Title, Description (optional), Upload new thumbnail (native file input `graphic_upload`), URL, Embed
    (Yes / No), Button text (placeholder "eg. https://..."), New Window (Yes / No); selects through v1 select2;
    hidden `id` and `graphic`.
  - **Thumbnail check:** on file choice, size ≤ 50,000 bytes and natural width exactly 550px, else
    `alert("Please keep files under 50KB and width at 550px!")` and the file is dropped. `?overrideImage=true` in
    the page URL skips the check. A valid file shows in the preview.
  - **New Item** ("+ New Item"): appended open, `order = length + 1`, Embed and New Window No.
  - **Delete:** removes the card at once; a saved item's id is queued and deleted on Save. No confirmation.
  - **Reorder:** Sortable, header handle, `animation: 250`; `order` becomes the 1-based position.
  - **Save:** multipart POST `/delete/<id>` per queued id, then `/update` per item (every non-null model
    attribute, the chosen file as `graphic_upload`), one after the other; then `location.reload(true)`. Any
    rejection → `alert("Couldn't save, please check logs!")`.

### 2.4 v1 bugs

| Bug | Cause | Fix |
|---|---|---|
| An untitled item disappears after Save | `update()` returns 200 `{"message": "Badly formatted data"}`; v1 JS treats it as success | D12 |
| An unknown id overwrites the last item (e.g. one another sysadmin deleted meanwhile) | `_find_carousel_item_by_id` returns -1; `existing_setting_list[-1] = item` | D12 |
| A highlight without a URL links to `/None` on the homepage | URL is optional; `c-highlight-card` renders `href="{{ href }}"` | Required URL (§6.3) + D12 |
| An upload over the size limit returns 500 and leaves the item pointing at a deleted file | `_persist_file()` deletes the previous file before `GlobalUpload.upload()` raises; the exception is not caught | D12 |
| Duplicate ids (`title`, `thumbnail`, `url_field`, …) on every card | Static ids in the underscore template | §6.3 |
| Guests and users without the permission get a 500, not a 403 | `check_access` raises `NotAuthorized`, uncaught | D13 |
| A non-integer `order` returns 500 (crafted requests; the Package Links and Products Menu views too) | `int(request.form.get('order', -1))` raises `ValueError` | D14 |

### 2.5 Assets

- `admin-scripts` (preloaded), `admin-carousel-scripts` (`admin/carousel.js`), and `admin-styles`, which includes
  `admin/carousel.css`.
- `v2-config-item-scripts` (087) and `config-item.css`, `image-upload.css` / `image-upload.js` (in the
  `v2-components-*` bundles) already exist.

### 2.6 Analytics and tests

- No Mixpanel or GA events on the page. The `base.html` page view still fires; `pageTitle` changes from
  "Administration" to "Homepage Highlights | Sysadmin". Homepage tracking is unchanged.
- No tests cover the carousel views or actions.

### 2.7 Reusable v2 pieces

| Piece | Use here |
|---|---|
| `admin/config-item-base.html` | Shell, header, list, New Item `<template>`, error alert, actions row (D5 adds a layout value) |
| `v2/components/config-item.html` + `components/config-item.js` | Cards; drag, collapse, renumber, New Item, Delete, required check, Save chain, retry (D11 extends the JS) |
| `v2/components/image-upload.html` + `image-upload.js` | Thumbnail (§5.2) |
| `text-field.html`, `select.html`, `c-form-field` | The other fields |
| `button.html`, `alert.html` | Upload file, New Item, Save, Save error |
| `admin/snippets/quick_link_fields.html` | Model for this page's own fields snippet (088 D5) |

---

## 3. Figma Design Analysis (XL)

### 3.1 Page

**Shell:** as 084–088: left "Sysadmin" menu in the helper's order, "Homepage Highlights" active (4px primary
underline); breadcrumb Home / Sysadmin / Homepage Highlights.

**Header** (padding 40 / 48): "Homepage Highlights" (Merriweather 24px bold); 6px below, "Manage the highlight
contents shown on the homepage" (14px, neutral-85). **Hidden (`display:none`):** the count "28", "Results per
page", "Sort by", a right-hand chevron and a primary button.

**Body:** the card grid and the actions row, 24px apart.

### 3.2 Grid and card

- **Grid:** two cards per row, each 29.188rem (467px), 24px apart in both directions, across the 59.9rem content
  width; four cards in two rows.
- **Card:** the box, header (16px `format-paragraph-spacing` handle, title, Delete) and field typography match
  Package Links (087 §3.2), mapped by `c-config-item` as built. Title "Homepage Highlight N".
- **Body**, 10px apart:

| Element | Figma | v2 |
|---|---|---|
| Preview | Empty 12.225rem (196px) box, card-wide, `#f5f7f7` (`--hdx-neutral-05`); about 2.2:1, the ratio of the homepage card image at XL | `c-image-upload` preview (D1, D3, D15) |
| Title \* | 37px text field, value "HDX HAPI" | `text-field` `l`, required |
| Description | 37px text field, "Lorem ipsum" / "/hapi" | Hidden input (D6) |
| Upload new thumbnail | Label + "Upload file" button (white, `--hdx-neutral-2` border, drop shadow, 14px medium, 16px icon) | `c-image-upload` Upload button: `button.html` `tertiary` `m` + `upload.svg` |
| URL \* | 37px text field with an "e.g. https://example.com/…" placeholder | `text-field` `l`, required |
| Embed | 34px select, "No" | Hidden input (D6) |
| Button text | 37px text field, "Submit" | Hidden input (D6) |
| New window | 34px select, "Yes" | `select` `m` |

**Hidden in the card:** a `chevron-up` (20px) beside each card, an "e.g. https://example.com/…" hint, and a search
icon and an eye-off icon inside the Title field.

### 3.3 Differences from the Package Links export

| | Package Links | Homepage Highlights | v2 |
|---|---|---|---|
| Layout | One card per row (59.938rem) | Two per row (29.188rem) | D5 |
| Card body | Fields only | Preview box first | D3 |
| Fields | Title, URL, Open in a new tab, Text to be displayed, Datasets to highlight | Title, Description, Upload new thumbnail, URL, Embed, Button text, New window | §6.3 |
| Field labels | Black / neutral-85 | Mostly `#4b5563` (no token) | `c-form-field` labels as built |
| Card title | Package Links Item N | Homepage Highlight N | D7 |

**Artefacts:**
- Two icon layers are misnamed: the "Upload file" icon is `chevron-down-icon`, and the New Item icon is
  `bell-icon`.
- "Homepage Highlight  1" has a double space.
- Cards 1–2 and 3–4 repeat their sample values, and every card shows Embed "No" / New window "Yes".
- The URL fields show the Figma-wide "population-jan-2011.json" placeholder.

### 3.4 Actions row

As Package Links: "New Item" left (`tertiary`, `plus.svg`) and "Save" right (primary), full grid width.

---

## 4. Current vs Target Comparison Matrix

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 admin tabs, intro + screenshot, help panel | `admin/config-item-base.html`, menu at XL | D10 |
| Breadcrumb / `<title>` | None / "Administration" | Home / Sysadmin / Homepage Highlights / "Homepage Highlights \| Sysadmin" | Derived |
| Heading | Intro `<h3>` | `<h1>` + subtitle, no count | D8, D10 |
| Rendering | JSON blob → Backbone + underscore | Server-rendered cards + `<template>` for New Item | Derived |
| Layout | Collapsed cards two per row; an open card spans the row | Cards open on load, two per row | D5 |
| Card | Blue header bar, trash, chevron | `c-config-item` | Derived |
| Preview | Mock-up of the v1 carousel tile | The whole image at the card width | D1, D3, D15 |
| Thumbnail | Native file input, replace only | Extended `c-image-upload` | D1, D2 |
| Image check | 50 KB / 550px `alert()`, `?overrideImage=true` | Same rule as an inline field error; override kept | D4 |
| Description, Embed, Button text | Edited, rendered by v1 only | Hidden inputs, no fields | D6 |
| Copy | "Carousel Item N", "Description (optional)", "New Window", "+ New Item" | Figma, with 088's "Open in a new tab" | D7 |
| Required | Title, server-side, silent drop | Title + URL, client-side errors | §6.3 |
| New card defaults | Embed No, New Window No | Embed No, Open in a new tab No | D9 |
| Reorder / collapse / save / reload | Sortable, chevron, sequential calls, reload, `alert()` | `config-item.js`, c-alert error | Derived |
| Server | §2.4 bugs | Fixed | D12–D14 |
| Assets | `admin-scripts`, `admin-carousel-scripts`, `admin-styles` | `v2-config-item-scripts`; styles and `image-upload.js` in the components bundles | Derived |

---

## 5. Component & System Reuse Strategy

### 5.1 Homepage highlights component

`c-highlight-card` (043, `v2/components/highlight-card.html`) exists and renders the stored items on the homepage.
It is the consumer of this editor: a whole-card `<a>` with `hdx_click_stopper` tracking, an image and a title. It is
not placed in the editor, where a tracked link would sit inside a form and Figma shows a bare image box. The editor
preview shows the whole image at the card width, with no set ratio (D15).

### 5.2 File upload: `c-image-upload` fit

`c-image-upload` (082) is the only v2 file control. The other upload UIs (resource upload, contribute flow, the
HDX Connect reply form) are v1.

| Need (Figma / v1) | `c-image-upload` today | Gap |
|---|---|---|
| One "Upload file" button that also replaces a stored image | Blank: Upload + Link; attached: thumbnail + file name + Remove (replace = Remove, then Upload) | Label; Upload while attached |
| Image comes from an upload only | Link button and URL input (web state) on `field_url` | Hide Link; carry `graphic` in a hidden input (D2) |
| No removal | Remove → blank, clear field `'true'` | Hide Remove (D2); the view has no clear handling |
| Large preview, empty box when there is no image | 4rem-high thumbnail in the attached state only | Large preview variant |
| Size / width check | `accept` only | D4 |
| Works in a New Item card | Initialises on `DOMContentLoaded` only | D11 |
| Field names `graphic` / `graphic_upload` | `field_url` / `field_upload` params | Fits |
| Sent with its card on Save | — | `config-item.js` posts `control.value` for every named control, so the file never leaves the browser (D11) |

**Options (D1):**

| Option | For | Against |
|---|---|---|
| A. Extend with optional params, defaults unchanged | One uploader; the 082 form is untouched | Five more params on a young component |
| B. Reuse as-is | No component change beyond D11 | Off Figma: Link, Remove, a small thumbnail, "Upload". Adds external images and image removal, which the view does not handle (`clear` ignored, the old file stays on disk) |
| C. Page markup in the fields snippet (preview `<img>`, hidden `graphic`, `button.html`, visually hidden file input) + page JS | Figma-exact; no shared change | Repeats `image-upload.js` (picker, object URL, status, broken-image fallback) |

Chosen: **A** (D1).

### 5.3 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, menu, crumb, `<title>`, header, list, actions, bundle | `admin/config-item-base.html` | Reuse + layout value | D5 |
| Card | `c-config-item` | Reuse | Derived |
| Fields | New `admin/snippets/homepage_highlight_fields.html` | New page snippet | Derived (088 D5) |
| Thumbnail | `c-image-upload` | Extend | D1–D4 |
| Grid | `c-config-item-list` | Extend | D5 |
| Behaviour | `components/config-item.js` | Extend | D11 |
| Buttons, error | `button.html`, `text-button.html`, `alert.html` | Reuse | Derived |

---

## 6. Functional Requirements

Each requirement cites its decision (§9).

### 6.1 Backend (`THEME/views/custom_settings.py`, D12–D14)

- Every view: `NotAuthorized` → `abort(403)`, as 087/088 (D13).
- `show()`: same action; passes `items` (the list) instead of the JSON string in `data`.
- `update()`, no title, no URL or a non-integer `order` (D14): the same `{"message": "Badly formatted data"}` with
  status 400, before any file is stored.
- `THEME/views/package_links_custom_settings.py`, `THEME/views/quick_links_custom_settings.py`: the same
  non-integer `order` → 400 (D14).
- `update()`, existing id: replace when `_find_carousel_item_by_id` finds it, otherwise append.
- `_persist_file()`: upload first, then delete the previous file. A `GlobalUploadException` returns 400 with the
  exception's text as `message` (D21); the stored config and files are unchanged.
- `GlobalUpload.upload()` (`THEME/helpers/uploader.py`) accepts PNG, GIF and JPEG files only, by extension and
  content; any other file raises `GlobalUploadException` "Unsupported upload type".
- `hdx_global_file_server.global_file_download` (`THEME/views/image_server.py`) serves files other than PNG, GIF and
  JPEG as downloads.
- `delete()`, the other `_process_request()` fields, the actions, the permission check and the stored shape:
  unchanged.

### 6.2 Page template (`THEME/templates/admin/carousel.html`)

- Extends `admin/config-item-base.html` and sets `nav_active='homepage_highlights'`,
  `page_label=_('Homepage Highlights')`, `list_subtitle` (§6.6), `update_url` (`hdx_carousel.update`),
  `delete_url` (`hdx_carousel.delete`, `id='__id__'`), `title_format=_('Homepage Highlight {n}')`, `error_message`,
  `id_prefix='homepage-highlight'`, `fields_snippet='admin/snippets/homepage_highlight_fields.html'` and
  `list_layout='grid'` (D5, D20).
- Items render in stored order. Unsaved defaults (`INITIAL_CAROUSEL_DATA`, no id) render as new cards, which Save
  creates, as in v1.

### 6.3 Fields snippet (`THEME/templates/admin/snippets/homepage_highlight_fields.html`)

Params `item` (default `{}`) and `prefix` (required), header comment in the `quick_link_fields.html` format. Each
field sits in a `c-form-field`; names as v1, ids `<prefix>-<name>`. Order per D3:

| Field | Snippet | Name | Value | Placeholder (v1) |
|---|---|---|---|---|
| Upload new thumbnail | `image-upload.html`: `field_url='graphic'`, `field_upload='graphic_upload'`, `link_enabled=False`, `remove_enabled=False`, `upload_label=_('Upload file')`, `preview='l'`, `accept='image/png,image/gif,image/jpeg'`, D4 check params, `check_message` | `graphic`, `graphic_upload` | `item.graphic` (value and preview) | — |
| Title | `text-field` `l`, `required=True` | `title` | `item.title` | "Title" |
| URL | `text-field` `l`, `required=True` | `url` | `item.url` | "eg. https://..." |
| Open in a new tab | `select` `m`, `required=True` (D22), Yes / No | `newTab` | `'true'` if `item.newTab` is true or `'true'`, else `'false'` | — |
| (hidden) | `<input type="hidden">` | `description`, `embed`, `buttonText` | The stored value, only when set (`embed`: `'true'` when `item.embed` is true or `'true'`) | — |

Title and URL carry `data-required-message` through `input_attrs` (§6.6). New cards default to Open in a new tab
No; with no `embed` posted the view stores false (D9).

### 6.4 `c-image-upload` extension (D1–D4)

New optional params; with their defaults the output is unchanged:

| Param | Default | Effect when set |
|---|---|---|
| `link_enabled` | `True` | `False`: no Link button, web state or × reset; the value travels in a hidden `field_url` input |
| `remove_enabled` | `True` | `False`: no Remove; the Upload button stays in the attached state and replaces the file |
| `upload_label` | `_('Upload')` | Upload button label |
| `preview` | `'s'` | `'l'`: a full-width preview box above the label (D16), always present: the image at full width and its own height (D15), or an empty `--hdx-neutral-05` box at least 10rem high (D18). A broken image falls back to the empty box |
| `max_bytes`, `image_width` | none | D4: checked when a file is chosen; a file that does not decode as an image fails it. On failure the chosen file is dropped, the previous image (stored or chosen) stays (D23), and `check_message` shows in the field's error element (always rendered, hidden while empty) and is announced through the status live region |
| `check_message` | `''` | The D4 error text (D19) |

The clear field is not rendered when both Link and Remove are off; nothing would set it. Choosing a valid file
updates the preview and file name, announces the name and dispatches `image-upload:change`, as today.

### 6.5 `config-item.js` and the list layout (D5, D11)

- **Files:** a `type="file"` control appends `files[0]` when a file is chosen and nothing otherwise; the stored
  `graphic` posts from its hidden input.
- **New Item:** after inserting the card, dispatch a bubbling `config-item:add` event on it; `image-upload.js`
  listens on `document` and initialises each `[data-image-upload]` inside. Focus still goes to the card's first
  text field (Title).
- **Grid:** the base renders `c-config-item-list--grid` when the page sets `list_layout='grid'` (D20): `__items`
  becomes a row-wrapping flex box (D17) with two equal columns from MD up, one below, cards aligned to the top of
  their row. Package Links and Products Menu don't set it.

### 6.6 Copy

| Element | Text |
|---|---|
| Page title | Homepage Highlights |
| Subtitle | Manage the highlight contents shown on the homepage (D8) |
| Card title | Homepage Highlight {n} |
| Labels | Upload new thumbnail, Title\*, URL\*, Open in a new tab\* (D7, D22) |
| Options | Yes, No |
| Buttons | Upload file, Delete, New Item, Save |
| Required errors | Title is required · URL is required |
| Image check error | Please keep files under 50KB and 550px wide. (D4; v1: "Please keep files under 50KB and width at 550px!") |
| Save error | There was an error saving the homepage highlights. Please try again. |

### 6.7 Behaviour

`config-item.js` as built (088 §6.5), plus:
- choosing a thumbnail previews it and runs the D4 check;
- Save sends each chosen file with its card's update;
- the reload shows the stored `/global/` image.

No page JS or page LESS.

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Sysadmin / carousel-permission access | Unchanged; others get 403 (v1: 500, D13) |
| Endpoints, field names, multipart, `order` = position, `newTab` / `embed` `'true'` / `'false'` | Unchanged |
| Upload stored under `/global/`, previous file deleted on replace, file deleted with its item | Unchanged; replace order fixed (D12) |
| Delete on Save, deletes before updates, one call at a time, reload on success | Unchanged |
| Drag reordering (mouse / touch), collapse toggle | Kept |
| Image check and its URL override | Kept, as an inline field error (D4) |
| Default items when nothing is stored | Unchanged |
| Description, Embed, Button text | Stored values kept through hidden inputs; no longer editable (D6) |
| Homepage section, its tracking, the three-item cap | Unchanged |
| Page view | Still fires; new `pageTitle` (§2.6) |

**Intentional differences:**
- Cards are open on load (v1: collapsed).
- The intro, screenshot and help panel are dropped (D10).
- URL becomes required.
- Description, Embed and Button text are no longer editable.
- The server bugs are fixed (D12–D14).
- Inline errors and a c-alert replace `alert()`.
- Card ids are unique.
- The preview shows the image as the homepage crops it, not a mock-up of the v1 tile.

---

## 8. Responsive & Accessibility Considerations

### 8.1 Breakpoints (MD/SM inferred)

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Menu | Sticky left column | Header user menu only | Same as MD |
| Header | Title + subtitle | Same | Same, wrapping per list-header |
| Grid | Two columns | Two columns (D5) | One column |
| Preview | Card-wide, the image's own height | Same | Same |
| Actions row | New Item left, Save right | Same | Same |

### 8.2 Accessibility

- **Headings:** `<h1>` page; `<h2>` per card.
- **Labels:** every control has a `<label for>`; ids unique per card. The thumbnail is a `role="group"` labelled
  "Upload new thumbnail"; Upload file opens the visually hidden file input; the chosen file name is announced.
- **Preview image:** `alt=""`; the card's Title names the item.
- **Image check error:** the field's error element, announced through the status live region; focus stays on
  Upload file.
- **Toggle, Delete, required errors, busy Save, Save error:** as 088 §8.2.
- **Reordering:** mouse and touch only, in the grid as in a column (088 D8); the handle icon is `aria-hidden`;
  Sortable's animation is off under reduced motion.
- CSS `:hover` / `:focus-visible` only; no Bootstrap classes or data attributes.

---

## 9. Decisions Taken

Every decision was asked and confirmed with the user.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Thumbnail control | Extend `c-image-upload` with optional params / reuse as-is / page markup + page JS (§5.2) | Extend | **Extend** (§6.4); defaults keep the organisation form unchanged |
| D2 | Link (external image URL) and Remove | Neither (v1, Figma) / Remove only / both | Neither | **Neither**; `graphic` posts from a hidden input |
| D3 | Preview position | Field first (preview + Upload file at the top of the card, then Title) / Figma order (the field after Description, its preview above the button) / preview at the top and the button after Description, synced by a page script over `image-upload:change` | Field first | **Field first**: image, then title, as on the homepage card |
| D4 | Image check | v1 rule (≤ 50 KB, exactly 550px wide) as an inline error, skipped when the page URL has `overrideImage=true` (the snippet omits the params) / size only / no client check. A file that does not decode: the same message / a separate one | v1 rule; same message | **v1 rule**; a file that does not decode fails it with the same message; the server's size limit answers 400 (D12) |
| D5 | Card layout (no MD/SM exports) | Two columns at XL and MD, one at SM / two at XL only / one column (087, 088) | 2 / 2 / 1 | **2 / 2 / 1** via an optional base value → `c-config-item-list--grid` |
| D6 | Description, Embed, Button text (no page renders them) | Keep, as Figma / hidden inputs, no fields / drop | Keep | **Hidden inputs, no fields**: no v2 page renders them and the homepage card has no button. Each renders only when set, as 087/088's `buttonText`, so a save keeps the stored values |
| D7 | Copy (Figma vs v1 vs 088) | Figma ("Homepage Highlight {n}", "New window", "Upload new thumbnail" / "Upload file", "Description") / Figma with 088's new-tab label / v1 ("Carousel Item {n}", "New Window", "Description (optional)") | Figma | **Figma with 088's "Open in a new tab"** for the `newTab` select (§6.6); v1 placeholders |
| D8 | Subtitle | Figma as-is / mention that only the first three show | Mention the cap | **Figma as-is** (§6.6) |
| D9 | New card Embed / Open in a new tab | No / No (v1, 088 D2) / Figma's sample No / Yes | No / No | **No / No** |
| D10 | v1 intro, sample screenshot, help panel; Figma's hidden count | Drop all / keep the intro as a hint | Drop | **Drop**; count hidden |
| D11 | New Item cards: initialising the uploader | `config-item.js` dispatches `config-item:add`, `image-upload.js` listens / `image-upload.js` exposes an init that `config-item.js` calls / delegated listeners in `image-upload.js` | Event | **Event**; plus the file posting in `config-item.js` (§6.5) |
| D12 | Server fixes and tests | The §6.1 fixes + a new `THEME/tests/test_carousel/test_carousel.py` / fixes without tests / leave the views | Fixes + tests | **Fixes + new test module**; no carousel test file exists to extend, `test_quick_links.py` is the model |
| D13 | Guests and users without the permission (500 today) | Abort 403, as 087/088 / leave the 500 | Abort 403 | **Abort 403** in all three views; covered by the 403 test in `test_carousel.py` |
| D14 | Non-integer `order` (500; crafted requests only) | 400 in the carousel view only / 400 in the carousel, Package Links and Products Menu views / leave, as 087/088 | Carousel only | **All three views** (§6.1); one test each, the 087/088 ones in their existing test files |
| D15 | Preview size (the homepage image is 10rem high at a fluid width, so "the homepage ratio" is no single value) | `aspect-ratio` of the Figma box (425 / 196) / fixed 196px height / fixed 10rem height | Figma ratio | **No set ratio or size**: the image fills the card width at its own height, so the 350×160 images in use come out at about Figma's box |
| D16 | Preview position inside the field | Preview, label, button (Figma) / label, preview, button (the component's order) | Preview first | **Preview, label, button**; the chosen file's name follows the button |
| D17 | Two-column list CSS | Row-wrapping flex box, which Sortable 1.3.0 orders as tiles / CSS grid, which Sortable treats as one vertical list | Flex | **Flex row-wrap** |
| D18 | Empty preview height | `min-height` 10rem (homepage card image) / 196px (Figma) / a fixed box with the image contained | 10rem | **`min-height: 10rem`** |
| D19 | Image check error text | Caller passes a `check_message` param / the component builds it from `max_bytes` / `image_width` | Param | **`check_message`** |
| D20 | Name of the base's layout value | `list_layout = 'grid'` / `grid_layout = True` | `list_layout` | **`list_layout = 'grid'`** |
| D21 | Message of the 400 on a failed upload | The exception's text / "Badly formatted data" / a new translated message | Exception text | **Exception text** (e.g. "File upload too large") |
| D22 | "Open in a new tab" asterisk (087/088 Figma show it; this Figma's "New window" has none) | `required=True`, as 087/088 / this Figma | `required=True` | **`required=True`**: one label on the three editors; the select always has a value |
| D23 | A failing file chosen after an accepted one (the file input then held neither) | Put the accepted file back into the input (`DataTransfer`) / revert to the stored image / leave | Put it back | **Put it back**: the preview, the file name and the posted file stay the accepted one |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/carousel.html` | Full v2 replacement on the base (§6.2) |
| `THEME/templates/admin/snippets/homepage_highlight_fields.html` | New: one card's fields (§6.3) |
| `THEME/templates/admin/config-item-base.html` | Optional layout value (§6.5) |
| `THEME/templates/v2/components/image-upload.html` | New params (§6.4) |
| `LESS/components/image-upload.less` | Large preview |
| `THEME/fanstatic/v2/components/image-upload.js` | Upload while attached, file check, `config-item:add` |
| `THEME/fanstatic/v2/components/config-item.js` | File posting, `config-item:add` (§6.5) |
| `LESS/components/config-item.less` | `c-config-item-list--grid` |
| `THEME/views/custom_settings.py` | `items`; §6.1 fixes |
| `THEME/views/package_links_custom_settings.py`, `THEME/views/quick_links_custom_settings.py` | Non-integer `order` → 400 (D14) |
| `THEME/helpers/uploader.py` | PNG, GIF and JPEG only (§6.1) |
| `THEME/views/image_server.py` | Other file types served as downloads (§6.1) |
| `THEME/tests/test_carousel/test_carousel.py` | New (D12) |
| `THEME/tests/test_package_links/test_package_links.py`, `THEME/tests/test_quick_links/test_quick_links.py` | One non-integer `order` test each (D14) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md`, `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | Migrated page; `c-image-upload` params; `config-item:add` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 089 status |

Not changed: `c-highlight-card`, `home/index.html`, the actions, `INITIAL_CAROUSEL_DATA`, the Package Links and
Products Menu pages and fields snippets, the organisation form, the components demo, and the v1
`admin/carousel.js` / `.css`, `admin-carousel-scripts`, `admin-scripts` and `admin-styles`. The v1 files stay on
disk; this page no longer loads them.

---

## 11. Implementation Checklist

1. Read the stored config on the local stack, after asking: item count, `/global/` vs static graphics and whether
   their files exist, string `newTab` / `embed`, empty URLs, `buttonText`.
2. Apply the §6.1 view changes (D14 in all three views) and add the tests.
3. Extend `c-image-upload`. Check that the organisation form's HTML is identical before and after.
4. Extend `config-item.js` and `config-item.less`. Check that the Package Links and Products Menu HTML is identical
   before and after, and that their behaviour is unchanged.
5. Add the fields snippet, replace `admin/carousel.html` and add the layout value to the base.
6. Run render-level checks, then hand the visual test to the user.
7. Update the docs in §10 and `STATUS.md`.

---

## 12. Risks & Edge Cases

| Case | Handling |
|---|---|
| A call fails mid-save | As 088: earlier calls stay applied, the alert shows, Save is re-enabled. A retry re-sends every chosen file, so a card whose update already succeeded uploads again; its first new file stays on disk unreferenced |
| Two sysadmins saving at once | As 088 §12 |
| An item another sysadmin deleted | Its update appends it again (D12) |
| Nothing stored yet | The eight defaults render as unsaved cards; Save stores them all; the homepage keeps showing the first three |
| Static graphics (`/images/homepage/...`) | Previewed; Delete only logs the failed file removal (unchanged) |
| A stored `/global/` file missing (e.g. a local filestore) | The preview falls back to the empty box |
| Sortable 1.3.0 dragging across two columns | Ordered as tiles in the row-wrapping list (D17); if it misbehaves, D5's one-column option |
| A thumbnail that is not exactly 550px wide (the 350×160 images in use) | Rejected unless the page URL has `overrideImage=true` (D4) |
| More than three items | Only the first three reach the homepage; the editor does not say so (D8) |
| No storage path configured | Uploads and file deletion still fail the call (unchanged; a configuration error) |
| Keyboard-only sysadmin needs to reorder | Not possible (088 D8) |
