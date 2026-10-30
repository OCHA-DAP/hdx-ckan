# 087 — Sysadmin Dashboard: Package Links (v2 Migration)

**Scope:** `/ckan-admin/package-links/show` (`hdx_package_links.show`), moved onto the 084 sysadmin shell.
Also in scope:
- a new shared component `c-config-item` (+ list wrapper `c-config-item-list`) and its JS, built for this page and
  for the later Products Menu and Homepage Highlights editors, which use the same Figma card;
- three fixes in the kept v1 endpoints (D8);
- an optional `count` on `v2/list-header.html`;
- `window.hdxV2.setFieldError` in `utils.js`, replacing the copies in `login.js`, `forgot-password.js` and
  `form-validator.js`.

**Excluded:**
- The other sysadmin pages (Homepage Highlights, Custom Pages, Products Menu, QA Dashboard), which stay on v1
  `admin/base.html`.
- The dataset-page package links (`c-page-header` `links_list`, v1 `search/snippets/package_icons.html`).
- Keyboard reordering (D4), a success message (D15), an unsaved-changes warning (D21), an empty-state message
  (D22), new analytics events.

**Figma source:** `xl-sysadmin-package-links.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. Compared with `xl-sysadmin-products-menu.html` and
`xl-sysadmin-homepage-highlights.html` for the shared card (§3.3).

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `hdx_package_links.show` (`/ckan-admin/package-links/show`). Reached from the sysadmin menu, the header user menu and v1's admin tabs |
| Objective | v2 page on `v2/sysadmin-base.html` (`nav_active='package_links'`, `page_label=_('Package Links')`) with Figma's layout, keeping the endpoints, payloads, save order, auth and reload on success |
| Strategy | **Direct replacement** of `THEME/templates/admin/package_links.html` (no `?v2` gate, as 084 / 085 / 086) |
| Shared work | `c-config-item` + `config-item.js` carry every interaction, driven by data attributes, so Products Menu can reuse them unchanged |

---

## 2. Repository Audit Findings

### 2.1 Routes and auth

| Endpoint | URL | Notes |
|---|---|---|
| `hdx_package_links.show` | `/ckan-admin/package-links/show` (GET) | Renders the editor |
| `hdx_package_links.update` | `/ckan-admin/package-links/update` (POST) | Creates or replaces one item from form fields; returns the whole config as a JSON string |
| `hdx_package_links.delete` | `/ckan-admin/package-links/delete/<id>` (POST) | Removes one item; returns the whole config |

- **Auth:** every view calls `check_access('hdx_quick_links_update')` (`THEME/helpers/auth.py`:
  `Permissions(user).has_permission(PERMISSION_MANAGE_QUICK_LINKS)`) and aborts 403. Sysadmins pass through the
  CKAN bypass. Products Menu shares the same check.
- **Menu:** `hdx_get_sysadmin_nav_sections()` already lists `package_links` under that check (086 D1).
- **2FA:** `/ckan-admin/package-links/show` is not in `_before_request` `protected_urls`, so no redirect (unchanged).
- **CSRF:** v1 JS sends `hdxUtil.net.getCsrfTokenAsObject()` headers; `hdxV2.post` does the same.

### 2.2 Stored data and consumers

- System-info key `hdx.package_links.config`: a JSON list of
  `{id, title, url, label, order, newTab, package_list, buttonText?}`. Read by `hdx_package_links_settings_show`,
  written by `hdx_package_links_settings_update` (both in `THEME/helpers/actions.py`).
- `update()` (`THEME/views/package_links_custom_settings.py`) builds the item in `_process_request()`: `newTab`
  from `'true'`, `order` as int, spaces stripped from `package_list`, a uuid for a new item, `buttonText` only when
  posted. It then sorts the list by `order`.
- `buttonText` is a carousel leftover with no input on this page; a stored value survives a save only because v1 JS
  posts every model attribute.
- `hdx_package_links_by_id_list` feeds `links_list` in `hdx_package/views/dataset.py` and `light_dataset.py`,
  rendered by v2 `c-page-header` (label with "This dataset is part" → "Part", title, url, `newTab`) and v1
  `package_icons.html`. The stored shape is unchanged, so these stay as they are.

### 2.3 v1 page

- `admin/package_links.html` extends v1 `admin/base.html` (subtitle "Administration"). It uses Bootstrap rows /
  `col-*`, the config JSON in a hidden `#package_links-config-saved-data` div, an underscore
  `#package_links-item-tpl` template and a sidebar "Package Links Menu Setting" help panel. A leftover
  `data-module="hdx_custom_pages"` does nothing (that module's JS is not loaded).
- `fanstatic/admin/package_links.js` (Backbone):
  - **Card:** header "Package Links Item {order}" with drag icons, a trash link and a chevron that toggles the
    fields (`tab_open`, every card starts open); fields Title, URL, OPEN IN A NEW TAB (v1 select2, Yes / No),
    Text to be displayed, Datasets to highlight (`<textarea rows="10">`).
  - **New Item:** appended with `order = length + 1`, open.
  - **Delete:** removes the card at once; a saved item's id is queued and deleted on Save. No confirmation.
  - **Reorder:** Sortable on the list, the whole header as handle, `animation: 250`; `order` becomes the 1-based
    position.
  - **Save:** POST `/delete/<id>` for each queued id, then POST `/update` (`FormData` of every non-null attribute)
    for each item in order, one after the other; then `location.reload(true)`. Any rejection → `alert("Couldn't save,
    please check logs!")`; earlier calls stay applied.
- `fanstatic/admin/quick_links.js` is the same file apart from its fields (`archived` instead of `label` /
  `package_list`).

### 2.4 v1 bugs

| Bug | Cause | Fix |
|---|---|---|
| A new item with an empty "Datasets to highlight" → 500 | `FormData` skips the null `package_list`; `None.replace` | D8 |
| An untitled item disappears after Save | `update()` returns 200 `{"message": "Badly formatted data"}`; v1 JS treats it as success | D7, D8 |
| An unknown id overwrites the last item | `_find_package_links_item_by_id` returns -1; `existing_setting_list[-1] = item` | D8 |
| Duplicate ids (`title`, `url_field`, …) on every card | Static ids in the underscore template | §6.2 |

### 2.5 Assets

- `admin-scripts` (underscore, Backbone, `backbone-model-file-upload.js`, `vendor/sortable/Sortable.js` 1.3.0,
  `form_element_manager.js`) and `admin-package-links-scripts` (`admin/package_links.js`).
- `admin-styles` includes `admin/package_links.css` (header `cursor: all-scroll`, `.sortable-chosen` opacity 0.9,
  `.sortable-ghost` opacity 0.3).
- v2 already ships vendored libraries through v2 bundles (`v2-select2-scripts` = `vendor/select2-4/select2.min.js` +
  `v2/components/select.js`).

### 2.6 Analytics and tests

- No Mixpanel or GA events on the page. The `base.html` page view still fires; `pageTitle` changes from
  "Administration" to "Package Links | Sysadmin".
- `THEME/tests/test_package_links/test_package_links.py`: the actions end to end, guest / user `NotAuthorized` on
  update, 403 on all three routes for guests and token users, update and delete over HTTP with a sysadmin token.

### 2.7 Reusable v2 pieces

| Piece | Use here |
|---|---|
| `v2/sysadmin-base.html` | Shell, menu, crumb, `<title>` |
| `v2/list-header.html` | Page header (`title_tag='h1'`, `title_size='dashboard'`) |
| `text-field.html` (`label`, `required`, `multiline`, `input_attrs`, error span) | Title, URL, Text to be displayed, Datasets to highlight |
| `select.html` (`label`, `required`, `options`, `selected`) | Open in a new tab |
| `button.html` (`type='icon-only'`, styles), `text-button.html` | Collapse toggle, New Item, Save, Delete |
| `alert.html` (`hidden=True`, `extra_attrs`) | Save error |
| `c-form-field` | Field wrapper (label → control gap `--hdx-space-2`) |
| `hdxV2.post`, `hdxV2.showAlert`, `hdxV2.setDisabled`, `hdxV2.prefersReducedMotion` (`utils.js`) | Save, error, busy state, drag animation |
| `setFieldError` (copied in `pages/login.js` and `pages/forgot-password.js`; `form-validator.js` has its own add / remove with a checkbox branch) | Field errors (D10, D27) |
| Icons `format-paragraph-spacing.svg`, `delete.svg`, `plus.svg`, `chevron-up.svg` | Handle, Delete, New Item, toggle |

No existing v2 component renders an editable, reorderable item: the public Products dropdown items (plain links
in `.hdx-v2-navbar__products-panel`, `v2/header.html`) and the homepage `c-highlight-card` only display content.

---

## 3. Figma Design Analysis (XL)

### 3.1 Page

**Shell:** as 084: left "Sysadmin" menu, "Package Links" active (4px primary underline); breadcrumb
Home / Sysadmin / Package Links. The menu also lists "QA Dashboard" (`hdx_qa`, `/qa_dashboard`), which the v2
menu leaves out (084).

**Header** (padding 40 / 48): "Package Links" (Merriweather 24px bold); 6px below, "Manage datasets associated
with location Data Grid" (14px, neutral-85). **Hidden (`display:none`):** the count "28", "Results per page",
"Sort by", a right-hand chevron and a primary button.

**Body:** cards and the actions row in one column, 24px apart.

### 3.2 Card (`upload-files`)

| Element | Figma | v2 |
|---|---|---|
| Box | white, 1px `#c4d0d1`, radius 2, padding 15 / 20, 10px header → fields | `--hdx-neutral-0`, `--hdx-neutral-3`, `--hdx-radius-sm`, `--hdx-space-4` / `--hdx-space-5` (15 is off the scale), `--hdx-space-14` (D25) |
| Header | 25px row: 16px `format-paragraph-spacing` icon, 8px, "Package Links Item 1" (Roboto 16 medium, `#000`); 20px; right: "Delete" (14px `delete` icon, 2px, 12px medium underlined, neutral-8) | `.hdx-body-m-medium()`, `--hdx-neutral-10`; gap `--hdx-space-2` (D26); `text-button` tertiary `s` |
| Fields | Label (16 medium, `#4b5563`) 8px above the control; 8px between fields | `c-form-field` labels (neutral-9; `#4b5563` is not a token); `--hdx-space-2` |
| Title, URL, Text to be displayed | 37px, padding 8 / 12 / 8 / 16, 1px neutral-2, 16px value | `text-field` size `l` (40px) |
| Open in a new tab | 34px select, 14px, drop shadow, chevron-down | `select` size `m` |
| Datasets to highlight | Multi-line field, value wrapped, no scroll | `text-field` `multiline`: fixed 100px, scrolls (D18) |
| Required | Red `*` after Title, URL, Open in a new tab | `required=True` |

**Hidden in the card:** a `chevron-up` (20px) beside each card, an "e.g. https://example.com/…" hint, a search
icon and an eye-off icon inside the Title field.

### 3.3 Shared card across the sysadmin editors

| Export | Card | Fields | Layout |
|---|---|---|---|
| Package Links | as §3.2 | Title, URL, Open in a new tab, Text to be displayed, Datasets to highlight | One column |
| Products Menu | identical; one card at radius 4 | Title, URL, Open in a new tab, Archived | One column |
| Homepage Highlights | identical; adds a thumbnail area and "Upload file" | Title, Description, thumbnail, URL, Embed, Button text, New window | Two columns |

The header (handle, "… Item N", Delete) and the box are the same, so the box, header and list layout belong in one
component; each page supplies its fields.

### 3.4 Actions row

Below the last card, full card width: "New Item" left (white, 1px neutral-2, drop shadow, neutral-8 text, padding
8 / 12, 20px icon, 8px gap, 14px medium: v2 `tertiary`, D24) and "Save" right (primary).

**Artefacts:** the "New Item" icon layer is named `bell-icon` (v1: "+ New Item" → `plus.svg`); every card shows
the same Afghanistan dataset list; "Datasets to higlight" (typo).

---

## 4. Current vs Target Comparison Matrix

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 admin tabs, sidebar help panel | `v2/sysadmin-base.html`, menu at XL | Derived, D6 |
| Breadcrumb / `<title>` | None / "Administration" | Home / Sysadmin / Package Links / "Package Links \| Sysadmin" | Derived |
| Heading | None | `<h1>` "Package Links" + subtitle, no count | D5, D11 |
| Rendering | JSON blob → Backbone + underscore | Server-rendered cards + `<template>` for New Item | Derived |
| Card | Blue header bar, glyph icons, trash, chevron | `c-config-item`: handle icon, `<h2>` title, chevron toggle, Delete | D1, D3, D13 |
| Fields | Bootstrap inputs, v1 select2 | `text-field` / `select` in `c-form-field` | Derived |
| Required | Title, server-side, silent drop | Title + URL, client-side errors | D7 |
| Reorder | Sortable, mouse / touch | Sortable 1.3.0, mouse / touch | D4, D12 |
| Save | Sequential delete + update, reload, `alert()` | Same calls and reload; c-alert error | D2, D15 |
| Server | 500 / silent drop / overwrite bugs | Fixed | D8 |
| Assets | `admin-scripts`, `admin-package-links-scripts`, `admin-styles` | `v2-config-item-scripts`; styles in `v2-components-styles` | D12, D14 |

---

## 5. Component & System Reuse Strategy

### 5.1 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, menu, crumb, `<title>` | `v2/sysadmin-base.html` | Reuse | Derived |
| Page header | `v2/list-header.html` with **optional `count`** | Extend | D5, D9 |
| Card | **`c-config-item`** | New | D1, D13 |
| List, template, error, actions | **`c-config-item-list`** classes (page markup, as `c-user-item-grid`) | New | D13 |
| Fields | `text-field.html`, `select.html`, `c-form-field` | Reuse | Derived |
| Buttons | `button.html`, `text-button.html` | Reuse | Derived |
| Error | `alert.html` | Reuse | D2 |
| Behaviour | **`components/config-item.js`** + `vendor/sortable/Sortable.js` | New | D12, D14 |
| Field errors | **`hdxV2.setFieldError`** | Promote | D10 |

### 5.2 `c-config-item`

`THEME/templates/v2/components/config-item.html` + `LESS/components/config-item.less`.

| Param | Type | Default | Notes |
|---|---|---|---|
| `title` | string | required | Header text, e.g. "Package Links Item 1" |
| `id` | string | required | Unique prefix: body `<id>-body`, title `<id>-heading` (D23), Delete `<id>-delete` |
| `item_id` | string | `''` | Stored id → `data-config-item-id`; empty for a new item |
| `expanded` | bool | `True` | `False` renders `aria-expanded="false"` and the body `hidden` (D20) |
| `caller()` | block | — | The fields |

Markup:

```html
<div class="c-config-item" data-config-item data-config-item-id="…">
  <div class="c-config-item__header">
    <span class="c-config-item__handle" aria-hidden="true">{format-paragraph-spacing icon}</span>
    <h2 class="c-config-item__title" id="<id>-heading" data-config-item-title>{title}</h2>
    <div class="c-config-item__actions">
      {button.html: type='icon-only', style='tertiary', size='s', icon chevron-up,
        extra_classes='c-config-item__toggle',
        attrs: aria-expanded="{expanded}", aria-controls="<id>-body", aria-labelledby="<id>-heading",
               data-config-item-toggle}
      {text-button.html: style='tertiary', size='s', label 'Delete', icon delete.svg, tag='button',
        attrs: id="<id>-delete", aria-labelledby="<id>-delete <id>-heading", data-config-item-delete}
    </div>
  </div>
  <div class="c-config-item__body" id="<id>-body" {hidden unless expanded}>{caller()}</div>
</div>
```

The toggle and Delete take their accessible names from the visible title, so renumbering only rewrites the title
text. `aria-labelledby` overrides the `aria-label` that `button.html` sets from `label`.

### 5.3 `c-config-item-list` (page markup)

```html
<div class="c-config-item-list" data-config-item-list
     data-update-url="…" data-delete-url="…/delete/__id__"
     data-title-format="Package Links Item {n}" data-error-message="…">
  <ol class="c-config-item-list__items"><li>{c-config-item}</li>…</ol>
  <template data-config-item-template><li>{c-config-item, ids containing __index__}</li></template>
  {alert.html: hidden=True, extra_attrs='data-config-item-error'}
  <div class="c-config-item-list__actions">{New Item: data-config-item-add} {Save: data-config-item-save}</div>
</div>
```

### 5.4 Shared changes

| File | Change |
|---|---|
| `v2/list-header.html` | `count` optional: `{% set count = count if count is defined else none %}`; the count span renders only when `count is not none`. Header comment: "Number shown beside the title; omit for none". Every current caller passes a count, so their HTML is unchanged |
| `fanstatic/v2/utils.js` | `window.hdxV2.setFieldError(input, message, invalid)`: sets the error text of a `text-field.html` or `checkbox.html` control and toggles its `--error` modifier, on with a message or with `invalid` true (D27) |
| `fanstatic/v2/pages/login.js`, `forgot-password.js` | Local `setFieldError` removed; calls use `window.hdxV2.setFieldError` |
| `fanstatic/v2/form-validator.js` | `displayError` / `removeErrorMessages` removed; calls use `window.hdxV2.setFieldError` (`invalid` true keeps the border on fields without `data-validation-error`) |
| `fanstatic/webassets.yml` | `v2-config-item-scripts`: `vendor/sortable/Sortable.js`, `v2/components/config-item.js`. `v2/components/config-item.css` added to `v2-components-styles` |

---

## 6. Functional Requirements

### 6.1 Backend (`THEME/views/package_links_custom_settings.py`)

- `show()`: same auth and action; passes `items` (the list) instead of the JSON string.
- `_process_request()`: `'package_list': (request.form.get('package_list') or '').replace(' ', '')`.
- `update()`, existing id: replace when `_find_package_links_item_by_id` finds it, otherwise append.
- `update()`, no title: return the same `{"message": "Badly formatted data"}` with status 400.
- `delete()`, the actions, auth and the stored shape: unchanged.

### 6.2 Page template (`THEME/templates/admin/package_links.html`)

- Extends `v2/sysadmin-base.html`; `nav_active='package_links'`, `page_label=_('Package Links')`; the `scripts`
  block adds `hdx_theme/v2-config-item-scripts`.
- Header: `v2/list-header.html`, `list_title=page_label`, `list_subtitle` (§6.5), `title_tag='h1'`,
  `title_size='dashboard'`, `show_controls=False`, `show_filters=False`, no `count`.
- Body: §5.3. The snippet `THEME/templates/admin/snippets/package_link_fields.html` (`item`, `prefix`) renders one
  card's fields (D28); it is called for each stored item (prefix `package-link-<loop.index>`, title "Package Links
  Item <loop.index>") and once inside the `<template>` with no item (prefix `package-link-__index__`). Items render
  in stored order (the server sorts on every update).
- Fields, each in `<div class="c-form-field">`, names as v1, ids `<prefix>-<name>`:

| Field | Snippet | Name | Value | Placeholder (v1) |
|---|---|---|---|---|
| Title | `text-field` `l`, `required=True` | `title` | `item.title` | "Title" |
| URL | `text-field` `l`, `required=True` | `url` | `item.url` | "eg. https://..." |
| Open in a new tab | `select` `m`, `required=True`, `options={'true': _('Yes'), 'false': _('No')}` | `newTab` | `'true'` if `item.newTab` is true or `'true'`, else `'false'` | — |
| Text to be displayed | `text-field` `l` | `label` | `item.label` | "eg. This dataset can be viewed in the" |
| Datasets to highlight | `text-field` `l`, `multiline=True` | `package_list` | `item.package_list` | "dataset1,dataset2,..." |
| (hidden) | `<input type="hidden">` | `buttonText` | `item.buttonText`, only when set | — |

  Title and URL carry `data-required-message` through `input_attrs` (§6.5).
- New Item: `button.html` `style='tertiary'` (D24), `icon_src='v2/icons/plus.svg'`, label "New Item". Save:
  `button.html` `style='primary'`, label "Save".

### 6.3 Behaviour (`THEME/fanstatic/v2/components/config-item.js`)

On `DOMContentLoaded`, for each `[data-config-item-list]`:

- **Reorder:** `Sortable.create(items, {handle: '.c-config-item__header', animation:
  hdxV2.prefersReducedMotion() ? 0 : 250, ghostClass: 'is-dragging', onUpdate: renumber})`.
- **Renumber:** after add, delete and reorder, each card's title text = `data-title-format` with `{n}` = its
  1-based position.
- **Collapse:** the toggle flips `aria-expanded` and the body's `hidden`. Cards start as `expanded` sets them (the
  page keeps the default, so all open); the state is not stored.
- **New Item:** the template's HTML with `__index__` replaced by a counter that starts above the rendered count is
  appended, renumbered, and its first text field focused.
- **Delete:** a card with `data-config-item-id` queues that id; the `<li>` is removed and the list renumbered;
  focus moves to the next card's toggle, or to New Item when no card follows. No confirmation; nothing is sent
  until Save.
- **Save:**
  1. Clear the field errors and hide the alert. For each `[required]` control with an empty trimmed value:
     `hdxV2.setFieldError(control, control.dataset.requiredMessage)`, expand its card. If any failed, focus the
     first and stop.
  2. `hdxV2.setDisabled(save, true)`.
  3. In sequence: `hdxV2.post(deleteUrl with __id__ → encoded id)` for each queued id; then, for each card in DOM
     order, `hdxV2.post(updateUrl, formData)` where `formData` holds every named control in the card body,
     `order` = position and `id` when the card has one. A finished delete leaves the queue. A card without
     `data-config-item-id` gets the one id its reply has that the previous reply (for the first call: the ids
     rendered on the page) lacked; a reply without exactly one new id counts as a failure (D17).
  4. Every reply an array → `window.location.reload()`. A non-array reply, a non-JSON reply (403 / 500 HTML) or a
     network error stops the chain → `hdxV2.showAlert(alert, data-error-message)`, Save re-enabled. Calls already
     made stay applied (v1); a retry neither recreates an item nor resends a finished delete (D17).
- Typing in a field clears its error (`setFieldError(control, '')`).

### 6.4 Styles (`LESS/components/config-item.less`)

| Selector | Rules |
|---|---|
| `.c-config-item` | Column flex, gap `--hdx-space-14`; padding `--hdx-space-4` `--hdx-space-5`; background `--hdx-neutral-0`; 1px `--hdx-neutral-3` border; `--hdx-radius-sm` |
| `&__header` | Flex, centred, gap `--hdx-space-2` (D26); `--hdx-neutral-10` (handle and title); `cursor: grab` |
| `&__handle` | 16px icon |
| `&__title` | `.hdx-body-m-medium()`, no margin, `flex: 1` |
| `&__actions` | Flex, centred, gap `--hdx-space-3`; `cursor: auto` |
| `&__toggle[aria-expanded="false"] svg` | `transform: rotate(180deg)` |
| `&__body` | Column flex, gap `--hdx-space-2`; `&[hidden]` `display: none` (the flex would override `hidden`) |
| `.c-config-item-list`, `&__items` | Column flex, gap `--hdx-space-6`; `__items` has no list styling |
| `&__items > .is-dragging` | `opacity: 0.3` (v1) |
| `&__actions` | Flex, `justify-content: space-between`, centred |

### 6.5 Copy

| Element | Text |
|---|---|
| Page title | Package Links |
| Subtitle | Manage datasets associated with location Data Grid |
| Card title | Package Links Item {n} |
| Labels | Title\*, URL\*, Open in a new tab\*, Text to be displayed, Datasets to highlight |
| Options | Yes, No |
| Buttons | Delete, New Item, Save |
| Required errors | Title is required · URL is required |
| Save error | There was an error saving the package links. Please try again. |

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Sysadmin / quick-links holder access, 403 for others | Unchanged |
| Endpoints, field names, `order` = position, `newTab` `'true'` / `'false'` | Unchanged |
| Delete on Save, deletes before updates, one call at a time | Unchanged (D2) |
| Reload on success | Unchanged (D15) |
| Collapse toggle, cards open on load | Kept (D3) |
| Drag reordering, mouse / touch | Kept (D4) |
| Stored `buttonText` | Kept through a hidden input |
| Placeholders | Kept (D6) |
| Dataset-page package links | Unchanged (stored shape unchanged) |
| Page view | Still fires; new `pageTitle` (§2.6) |

**Intentional differences:** the help panel is dropped (D6); URL becomes required and both required fields are
checked before any call (D7); the server bugs are fixed (D8); a c-alert replaces `alert()`; a retry after a failed
save creates no duplicates (D17); card ids are unique.

---

## 8. Responsive & Accessibility Considerations

### 8.1 Breakpoints (MD/SM inferred)

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Menu | Sticky left column | Header user menu only | Same as MD |
| Header | Title + subtitle | Same | Same, wrapping per list-header |
| Cards | Full content width, one field column | Same | Same |
| Actions row | New Item left, Save right | Same | Same |

### 8.2 Accessibility

- **Headings:** `<h1>` page; `<h2>` per card.
- **Labels:** every control has a `<label for>`; ids unique per card.
- **Toggle:** `aria-expanded`, `aria-controls`; named by the card title.
- **Delete:** named "Delete Package Links Item N" through `aria-labelledby`; focus moves as §6.3.
- **New Item:** focus moves to the new card's Title.
- **Errors:** inline field errors; focus on the first invalid field; the Save error is a `role="alert"` c-alert.
- **Busy state:** Save disabled during the calls.
- **Reordering:** mouse and touch only. Keyboard users cannot reorder (WCAG 2.1.1), accepted as v1 parity (D4).
  The handle icon is `aria-hidden`.
- **Motion:** Sortable animation follows `hdxV2.prefersReducedMotion()` (currently always `false`, CONVENTIONS).
- CSS `:hover` / `:focus-visible` only; no Bootstrap classes or data attributes.

---

## 9. Decisions Taken

Every decision was asked and confirmed with the user.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Item card | New shared c-component / sysadmin page class / page-only markup | New component | **New shared component** (§5.2); Products Menu and Homepage Highlights reuse it |
| D2 | Save mechanism | v1 endpoints / one bulk endpoint / plain form + redirect | v1 endpoints | **v1 endpoints**, same order, c-alert on failure (§6.3) |
| D3 | Collapse toggle (v1; hidden in Figma) | Keep / drop | Keep | **Keep**; cards open on load |
| D4 | Keyboard reordering | Handle button + arrow keys / Move up / down buttons / drag only | Handle + arrows | **Drag only** (v1 parity); the WCAG 2.1.1 gap is accepted |
| D5 | Count (hidden in Figma; shown on 084–086) | Show / hide | Show | **Hide** |
| D6 | v1 help panel | Field hints / c-info-box / drop | Field hints | **Drop**; v1 placeholders kept |
| D7 | Required fields | Title + URL client-side / Title only / none | Title + URL | **Title + URL**, checked before any call |
| D8 | v1 server bugs (§2.4) | Server + JS / JS only / leave | Server + JS | **Server + JS** (§6.1, §6.3); three cases in the existing test file |
| D9 | Hiding the count | Optional `count` / `show_count` param | Optional `count` | **Optional `count`** |
| D10 | `setFieldError` (two copies; third consumer) | Promote to `utils.js` / third copy | Promote | **`hdxV2.setFieldError`**; `login.js` and `forgot-password.js` use it |
| D11 | Copy (Figma vs v1 labels, typo, subtitle) | Figma with typo fixed / Figma + general subtitle / v1 labels | Figma, typo fixed | **Figma, typo fixed** (§6.5) |
| D12 | Drag library | Vendor Sortable 1.3.0 / native HTML5 / newer Sortable | Vendor Sortable | **`vendor/sortable/Sortable.js`** in a v2 bundle |
| D13 | Names | `c-config-item` / `c-sortable-item` / `c-edit-item` | `c-config-item` | **`c-config-item`**, wrapper **`c-config-item-list`** |
| D14 | JS location | Component JS for everything / component UI + page save / page JS | Component JS | **`components/config-item.js`** for everything; no page JS |
| D15 | After a successful save | Reload / reload + success alert / no reload + alert | Reload | **Reload**, no message |
| D16 | Doc file | Numbered / brief's name | Numbered | **`087-sysadmin-package-links-v2.md`** |
| D17 | Retry after a partial save failure (new items got ids on the server only; v1 duplicates them) | Record new ids / lock Save after a failure / v1 | Record new ids | **Record new ids** (§6.3 step 3) |
| D18 | "Datasets to highlight" height (v2 textareas are a fixed 100px; `rows` has no effect) | Component default / auto-grow / taller fixed height | Component default | **Component default**; scrolls past about 4 lines |
| D19 | Save-error copy | HDX Connect's "There was an error …" / "Couldn't save …" | "There was an error …" | **"There was an error …"** (§6.5) |
| D20 | Demo of a collapsed card (no way to render one) | Two open cards / `expanded` param / working toggle on the demo page | Two open cards | **`expanded` param**, default `True` (§5.2) |
| D21 | Unsaved-changes warning | None / `beforeunload` prompt | None | **None** (v1 parity) |
| D22 | Empty-state message | None / shared `.hdx-v2-dashboard-empty` line | None | **None**; New Item is the call to action |
| D23 | Card title id `<id>-title` equals the Title field id `<prefix>-title` | Heading id `-heading` / field ids `<prefix>-field-<name>` / a different id per call | `-heading` | **`<id>-heading`** (§5.2); every editor has a Title field |
| D24 | New Item style (Figma: white, neutral-2 border, neutral-8 text) | `tertiary` / `secondary` (blue border) | `tertiary` | **`tertiary`** |
| D25 | Header → fields gap (Figma 10px) | `--hdx-space-14` (10px) / `--hdx-space-3` (12px) | `--hdx-space-14` | **`--hdx-space-14`** |
| D26 | Header spacing (handle → title 8px, title → Delete 20px, sibling flex items) | Gap 8px / gap 8px + actions margin / handle + title wrapper | Gap 8px | **Gap `--hdx-space-2`**; the title's `flex: 1` pushes the actions right |
| D27 | `form-validator.js`'s own error add / remove (checkboxes; border without text on fields without `data-validation-error`) | Leave / unify | Leave | **Unify**: `setFieldError` gains the checkbox branch and `invalid` (§5.4) |
| D28 | Card fields mechanism (no v2 page uses a Jinja macro) | Snippet next to the page / page macro / snippet under `templates/v2/` | Snippet next to the page | **`admin/snippets/package_link_fields.html`** |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/package_links.html` | Full v2 replacement (§6.2) |
| `THEME/templates/admin/snippets/package_link_fields.html` | New: one card's fields (§6.2) |
| `THEME/views/package_links_custom_settings.py` | `items` for the template; D8 fixes (§6.1) |
| `THEME/templates/v2/components/config-item.html` | New (§5.2) |
| `LESS/components/config-item.less` | New (§6.4); compiled `fanstatic/v2/components/config-item.css` |
| `THEME/fanstatic/v2/components/config-item.js` | New (§6.3) |
| `THEME/fanstatic/webassets.yml` | `v2-config-item-scripts`; `config-item.css` in `v2-components-styles` |
| `THEME/templates/v2/list-header.html` | Optional `count` + header comment |
| `THEME/fanstatic/v2/utils.js`, `THEME/fanstatic/v2/pages/login.js`, `THEME/fanstatic/v2/pages/forgot-password.js`, `THEME/fanstatic/v2/form-validator.js` | `hdxV2.setFieldError` |
| `THEME/tests/test_package_links/test_package_links.py` | Empty `package_list` → 200 and `''`; unknown id → appended, others untouched; no title → 400, config unchanged |
| `THEME/templates/v2/components.html` | `c-config-item` demo (two cards, one with `expanded=False`) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md`, `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md` | Migrated page, new component, `hdxV2.setFieldError` |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 087 status |

Not changed: v1 `admin/package_links.js` / `.css`, `admin-package-links-scripts`, `admin-scripts`, `admin-styles`
(kept on disk; this page no longer loads them), the dataset-page consumers, the actions.

---

## 11. Implementation Checklist

1. Save "before" HTML with the in-container test client: `/ckan-admin`, `/user`, `/ckan-admin/requests_data`,
   `/dataset`, the login and forgot-password pages.
2. Make `count` optional in `v2/list-header.html`.
3. Move `setFieldError` to `utils.js`; update `login.js`, `forgot-password.js` and `form-validator.js`.
4. Add `c-config-item` (template, LESS; the IDE compiles it) and `config-item.js`; register the bundles.
5. Apply the D8 fixes and `items` in the view; add the three test cases.
6. Replace `admin/package_links.html`.
7. Add the components demo entry.
8. Run the §12 checks, then hand the visual test to the user.
9. Update the docs in §10 and `STATUS.md`.

---

## 12. Verification

- **Render:** `/ckan-admin/package-links/show` as a sysadmin and as a quick-links holder → 200, one card per
  stored item, unique ids; as an ordinary user and anonymously → 403.
- **Unchanged HTML** (asset hashes aside): the step-1 pages.
- **Tests:** `test_package_links.py` on the repo test stack, after asking.
- **Visual (user):** drag, collapse, Delete, New Item; Save success; Save with an empty Title / URL; Save failure
  (e.g. an expired session) and a retry (no duplicates); login and forgot-password field errors; signup,
  change-email and notification-signup validator errors (text, checkbox, border-only); a dataset page that lists a
  package link.

---

## 13. Risks & Edge Cases

| Case | Handling |
|---|---|
| A call fails mid-save | Earlier calls stay applied (v1); the alert shows, Save re-enabled; a retry skips finished deletes and recreates nothing (D17) |
| Two sysadmins saving at once | Last writer wins per item (v1). An item the other adds during your save gives your new card's reply two new ids, which counts as a failure (D17), so a retry creates that card's item again |
| Item without `order` in stored config | Rendered in stored order; `update()`'s sort is unchanged v1 behaviour |
| Stored `newTab` as a string | `'true'` / `'false'` handled in §6.2 |
| Stored `buttonText` | Hidden input keeps it |
| Keyboard-only sysadmin needs to reorder | Not possible (D4) |
| Products Menu / Homepage Highlights adopting the component | Supply their fields, data attributes and title format; Highlights needs a two-column list variant and file fields, decided in its own task |
