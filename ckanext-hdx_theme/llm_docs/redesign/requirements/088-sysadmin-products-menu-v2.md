# 088 — Sysadmin Dashboard: Products Menu (v2 Migration)

**Scope:** `/ckan-admin/quick-links/show` (`hdx_quick_links.show`), moved onto the 084 sysadmin shell with the
087 `c-config-item` editor, whose page markup becomes the shared `admin/config-item-base.html` (D12). Also in scope:
three fixes in the kept v1 endpoints (D4, D11) and their test cases.

**Excluded:**
- The other v1 sysadmin pages (Homepage Highlights, Custom Pages).
- Any change to `c-config-item`, `c-config-item-list` or `config-item.js` (D8).
- The consumers of the stored list: the v2 header / offcanvas / footer Products menus, `/crisis-pages`, v1
  `header-mobile.html` (the stored shape is unchanged).
- Keyboard reordering, a success message, an unsaved-changes warning, an empty-state message (D8), new analytics
  events.

**Figma source:** `xl-sysadmin-products-menu.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. Compared with `xl-sysadmin-package-links.html` (§3.3).

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `hdx_quick_links.show` (`/ckan-admin/quick-links/show`). Reached from the sysadmin menu (`products_menu`), the header user menu, v1's admin tabs and the v1 header's "Quick Links" icon |
| Objective | v2 page on `v2/sysadmin-base.html` (`nav_active='products_menu'`, `page_label=_('Products Menu')`) with Figma's layout, keeping the endpoints, payloads, save order, auth and reload on success |
| Strategy | **Direct replacement** of `THEME/templates/admin/quick_links.html` (no `?v2` gate, as 084–087) |
| Shared work | `admin/config-item-base.html` (D12): the 087 page markup, now used by Package Links too. `c-config-item` and `config-item.js` (087) are reused unchanged through their data attributes |

---

## 2. Repository Audit Findings

### 2.1 Routes and auth

| Endpoint | URL | Notes |
|---|---|---|
| `hdx_quick_links.show` | `/ckan-admin/quick-links/show` (GET) | Renders the editor |
| `hdx_quick_links.update` | `/ckan-admin/quick-links/update` (POST) | Creates or replaces one item from form fields; returns the whole config as a JSON string |
| `hdx_quick_links.delete` | `/ckan-admin/quick-links/delete/<id>` (POST) | Removes one item; returns the whole config |

- **Auth:** every view calls `check_access('hdx_quick_links_update')` (`THEME/helpers/auth.py`:
  `Permissions(user).has_permission(PERMISSION_MANAGE_QUICK_LINKS)`, label "Manage Quick Links") and aborts 403.
  Sysadmins pass through the CKAN bypass. Package Links shares the same check.
- **Menu:** `hdx_get_sysadmin_nav_sections()` already lists `products_menu` → `hdx_quick_links.show` under that
  check, before `package_links` (086 D1).
- **2FA:** `/ckan-admin/quick-links/show` is not in `_before_request` `protected_urls`, so no redirect (unchanged).
- **CSRF:** v1 JS sends `hdxUtil.net.getCsrfTokenAsObject()` headers; `hdxV2.post` does the same.

### 2.2 Stored data and consumers

- System-info key `hdx.quick_links.config`: a JSON list of `{id, title, url, order, newTab, archived,
  buttonText?}`. Read by `hdx_quick_links_settings_show` (adds `archived: False` when missing), written by
  `hdx_quick_links_settings_update` (both in `THEME/helpers/actions.py`).
- `update()` (`THEME/views/quick_links_custom_settings.py`) builds the item in `_process_request()`: `newTab` and
  `archived` from `'true'`, `order` as int, a uuid for a new item, `buttonText` only when posted. It then sorts the
  list by `order`.
- `buttonText` is a carousel leftover with no input on this page; a stored value survives a save only because v1 JS
  posts every model attribute.
- Consumers (all unchanged):

| Consumer | Reads |
|---|---|
| `v2/page.html` → `v2/header.html` (Products panel, offcanvas subnav), `v2/footer.html` (Products column) | `h.hdx_get_quick_links_list(archived=False, exclude_crisis=True)`: non-archived items, without `/event`, `/m/event`, `/dashboards`, `/m/dashboards` URLs (two forced dashboard URLs kept) |
| `h.hdx_v2_main_nav_state(quick_links)` (083) | The same list, to mark the current product link |
| `THEME/views/crisis_pages.py` (`/crisis-pages`, 071) | `hdx_quick_links_settings_show`: Ongoing = non-archived `/event` / `/m/event` URLs; Archived = every `archived: true` item |
| v1 `header-mobile.html` | `h.hdx_get_quick_links_list(archived=False, exclude_crisis=True)` |

### 2.3 v1 page

- `admin/quick_links.html` extends v1 `admin/base.html` (subtitle "Administration"). It uses Bootstrap rows /
  `col-*`, the config JSON in a hidden `#quick_links-config-saved-data` div, an underscore `#quick_links-item-tpl`
  template and a sidebar "Quick Links Menu Setting" help panel. The panel's last line sends admins to the Custom
  Pages setting to archive quick links, although the Archived field is on this page. A leftover
  `data-module="hdx_custom_pages"` does nothing.
- `fanstatic/admin/quick_links.js` (Backbone) is v1 `package_links.js` with other fields:
  - **Card:** header "Quick Links Item {order}" with drag icons, a trash link and a chevron that toggles the
    fields (every card starts open); fields Title, URL, OPEN IN A NEW TAB (v1 select2, Yes / No), ARCHIVED (No /
    Yes).
  - **New Item** ("+ New Item"): appended with `order = length + 1`, open; `newTab` and `archived` default to No.
  - **Delete:** removes the card at once; a saved item's id is queued and deleted on Save. No confirmation.
  - **Reorder:** Sortable on the list, the whole header as handle, `animation: 250`; `order` becomes the 1-based
    position.
  - **Save:** POST `/delete/<id>` for each queued id, then POST `/update` for each item in order, one after the
    other; then `location.reload(true)`. Any rejection → `alert("Couldn't save, please check logs!")`.

### 2.4 v1 bugs

| Bug | Cause | Fix |
|---|---|---|
| An untitled item disappears after Save | `update()` returns 200 `{"message": "Badly formatted data"}`; v1 JS treats it as success | D3, D4 |
| An unknown id overwrites the last item (e.g. an item another sysadmin deleted meanwhile) | `_find_quick_links_item_by_id` returns -1; `existing_setting_list[-1] = item` | D4 |
| A link without a URL breaks every v2 page | v1 posts no `url` for an untouched field, so `url: null` is stored; `hdx_get_quick_links_list` calls `.lower()` on it | D11 |
| Duplicate ids (`title`, `url_field`, …) on every card | Static ids in the underscore template | §6.2 |

### 2.5 Assets

- `admin-scripts` (preloaded) and `admin-quick-links-scripts` (`admin/quick_links.js`).
- `admin-styles` includes `admin/quick_links.css`.
- `v2-config-item-scripts` (vendored Sortable 1.3.0 + `v2/components/config-item.js`) and `config-item.css` in
  `v2-components-styles` already exist (087).

### 2.6 Analytics and tests

- No Mixpanel or GA events on the page. The `base.html` page view still fires; `pageTitle` changes from
  "Administration" to "Products Menu | Sysadmin". The header / footer Products links keep their
  `hdx_click_stopper` tracking (unchanged consumers).
- `THEME/tests/test_quick_links/test_quick_links.py`: the actions end to end, guest / user `NotAuthorized` on
  update, 403 on all three routes for guests and token users, update and delete over HTTP with a sysadmin token.

### 2.7 Reusable v2 pieces

| Piece | Use here |
|---|---|
| `v2/sysadmin-base.html` | Shell, menu, crumb, `<title>` |
| `v2/list-header.html` (optional `count`) | Page header (`title_tag='h1'`, `title_size='dashboard'`, no count) |
| `v2/components/config-item.html` + `c-config-item-list` page markup | Cards, list, New Item `<template>`, error alert, actions row |
| `fanstatic/v2/components/config-item.js` | Drag, collapse, renumber, New Item, Delete, required check, Save chain, retry without duplicates |
| `text-field.html`, `select.html`, `c-form-field` | Title, URL, Open in a new tab, Archived |
| `button.html`, `alert.html` | New Item, Save, Save error |
| `admin/package_links.html` | Page markup, moved into the shared base (D12) |

---

## 3. Figma Design Analysis (XL)

### 3.1 Page

**Shell:** as 084: left "Sysadmin" menu (All Sysadmins, All Users, Homepage Highlights, HDX Connect Dashboard,
Custom Pages, Products Menu, Package Links: the helper's order), "Products Menu" active (4px primary underline);
breadcrumb Home / Sysadmin / Products Menu.

**Header** (padding 40 / 48): "Products Menu" (Merriweather 24px bold); 6px below, "Manage the links shown under
“Products” in the navigation" (14px, neutral-85). **Hidden (`display:none`):** the count "28", "Results per page",
"Sort by", a right-hand chevron and a primary button.

**Body:** cards and the actions row in one column, 24px apart.

### 3.2 Card

The box, header (16px `format-paragraph-spacing` handle, "Products Menu Item N", Delete), field typography and
spacing match Package Links (087 §3.2), mapped by `c-config-item` as built.

| Field | Figma | v2 |
|---|---|---|
| Title \* | 37px text field, value "HDX HAPI" | `text-field` `l`, required |
| URL \* | 37px text field, value "/hapi" | `text-field` `l`, required |
| Open in a new tab \* | 34px select showing "Select" | `select` `m`, required, Yes / No, a new card on No (D2) |
| Archived | 34px select showing "No", no asterisk | `select` `m`, No / Yes |

**Hidden in the card:** a `chevron-up` (20px) beside each card, an "e.g. https://example.com/…" hint, a search
icon and an eye-off icon inside the Title field.

### 3.3 Differences from the Package Links export

| | Package Links | Products Menu | v2 |
|---|---|---|---|
| Fields | Title, URL, Open in a new tab ("No"), Text to be displayed, Datasets to highlight | Title, URL, Open in a new tab ("Select"), Archived | Per-page fields snippet (D5) |
| Add button | "New Item" | "New Menu" | "New Item" (D1) |
| Menu | Lists "QA Dashboard" | No QA Dashboard | The helper's items |
| Card radius | 2 | 2, two cards at 4 | `--hdx-radius-sm` |

**Artefacts:** the "New Menu" icon layer is named `bell-icon` (v1: "+ New Item" → `plus.svg`); two cards are
titled "Products Menu Item 3"; the second card's URL shows an "e.g. https://example.com/…" placeholder.

### 3.4 Actions row

As Package Links: "New Item" left (`tertiary`, `plus.svg`) and "Save" right (primary), full card width.

---

## 4. Current vs Target Comparison Matrix

| Element | Current (v1) | Target (v2) | Decision |
|---|---|---|---|
| Shell | v1 admin tabs, sidebar help panel | `v2/sysadmin-base.html`, menu at XL | Derived, D6 |
| Breadcrumb / `<title>` | None / "Administration" | Home / Sysadmin / Products Menu / "Products Menu \| Sysadmin" | Derived |
| Heading | None | `<h1>` "Products Menu" + subtitle, no count | D7, D9 |
| Rendering | JSON blob → Backbone + underscore | Server-rendered cards + `<template>` for New Item | Derived |
| Card | Blue header bar, glyph icons, trash, chevron | `c-config-item` | Derived (087 D1) |
| Copy | "Quick Links Item N", uppercase labels, "+ New Item" | "Products Menu Item N", sentence-case labels, "New Item" | D1 |
| Fields | Bootstrap inputs, v1 select2 | `text-field` / `select` in `c-form-field` | D5 |
| New card defaults | Open in a new tab No, Archived No | Same | D2 |
| Required | Title, server-side, silent drop | Title + URL, client-side errors | D3 |
| Reorder / collapse / save / reload | Sortable, chevron, sequential calls, reload, `alert()` | `config-item.js`, c-alert error | D8 |
| Server | Silent drop / overwrite / null-URL bugs | Fixed | D4, D11 |
| Assets | `admin-scripts`, `admin-quick-links-scripts`, `admin-styles` | `v2-config-item-scripts`; styles in `v2-components-styles` | Derived |

---

## 5. Component & System Reuse Strategy

### 5.1 Mapping

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, menu, crumb, `<title>` | `v2/sysadmin-base.html` | Reuse | Derived |
| Page header | `v2/list-header.html` without `count` | Reuse | D7 |
| List, template, error, actions, bundle | New `admin/config-item-base.html` (the 087 page markup) | New shared base | D12 |
| Card | `c-config-item` | Reuse | D8 |
| Fields | New `admin/snippets/quick_link_fields.html` with `text-field.html`, `select.html`, `c-form-field` | New page snippet | D5 |
| Buttons, error | `button.html`, `text-button.html`, `alert.html` | Reuse | Derived |
| Behaviour | `components/config-item.js` + `vendor/sortable/Sortable.js` (`v2-config-item-scripts`) | Reuse | D8 |

No LESS, JS or bundle changes. `admin/package_links.html` moves onto the base with unchanged HTML;
`package_link_fields.html` is not touched.

---

## 6. Functional Requirements

### 6.1 Backend (`THEME/views/quick_links_custom_settings.py`)

- `show()`: same auth and action; passes `items` (the list) instead of the JSON string in `data`.
- `update()`, existing id: replace when `_find_quick_links_item_by_id` finds it, otherwise append.
- `update()`, no title or no URL: return the same `{"message": "Badly formatted data"}` with status 400
  (`_process_request()` returns `None` for either).
- The unused `_remove_file_by_path()` and its `GlobalUpload` import: removed (D13).
- `delete()`, the rest of `_process_request()`, the actions, auth and the stored shape: unchanged.

### 6.2 Page templates (`THEME/templates/admin/config-item-base.html`, `admin/quick_links.html`)

- Base (D12): extends `v2/sysadmin-base.html`; the `scripts` block adds `hdx_theme/v2-config-item-scripts`.
  Children set, at top level, `nav_active`, `page_label`, `list_subtitle`, `update_url`, `delete_url` (with
  `__id__`), `title_format` (with `{n}`), `error_message`, `id_prefix` and `fields_snippet`, optionally
  `list_layout` (089 D20); the view passes `items`.
- Header: `v2/list-header.html`, `list_title=page_label`, `list_subtitle`, `title_tag='h1'`,
  `title_size='dashboard'`, `show_controls=False`, `show_filters=False`, no `count`.
- Body: the `c-config-item-list` markup (087 §5.3) with the child's URLs, title format and error message. One
  `c-config-item` per item (`id` `<id_prefix>-<loop.index>`, title from `title_format`, `item_id=item.id`) and one
  inside the `<template>` (`<id_prefix>-__index__`, no item), each with `fields_snippet` (`item`, `prefix`). Items
  render in stored order (the server sorts on every update).
- New Item: `button.html` `style='tertiary'`, `icon_src='v2/icons/plus.svg'`, label "New Item",
  `data-config-item-add`. Save: `button.html` `style='primary'`, label "Save", `data-config-item-save`.
- `admin/quick_links.html`: `products_menu`, `_('Products Menu')`, the §6.4 subtitle, card title and save error,
  `h.url_for('hdx_quick_links.update')`, `h.url_for('hdx_quick_links.delete', id='__id__')`, `'quick-link'`,
  `'admin/snippets/quick_link_fields.html'`. `admin/package_links.html` sets its 087 values; its HTML is unchanged.

### 6.3 Fields snippet (`THEME/templates/admin/snippets/quick_link_fields.html`)

Params `item` (default `{}`) and `prefix` (required), header comment in the `package_link_fields.html` format.
Each field sits in `<div class="c-form-field">`; names as v1, ids `<prefix>-<name>`:

| Field | Snippet | Name | Value | Placeholder (v1) |
|---|---|---|---|---|
| Title | `text-field` `l`, `required=True` | `title` | `item.title` | "Title" |
| URL | `text-field` `l`, `required=True` | `url` | `item.url` | "eg. https://..." |
| Open in a new tab | `select` `m`, `required=True`, `options={'true': _('Yes'), 'false': _('No')}` | `newTab` | `'true'` if `item.newTab` is true or `'true'`, else `'false'` | — |
| Archived | `select` `m`, `options={'false': _('No'), 'true': _('Yes')}` | `archived` | `'true'` if `item.archived` is true or `'true'`, else `'false'` | — |
| (hidden) | `<input type="hidden">` | `buttonText` | `item.buttonText`, only when set | — |

Title and URL carry `data-required-message` through `input_attrs` (§6.4).

### 6.4 Copy

| Element | Text |
|---|---|
| Page title | Products Menu |
| Subtitle | Manage the links shown under “Products” in the navigation and on the Crisis Pages list |
| Card title | Products Menu Item {n} |
| Labels | Title\*, URL\*, Open in a new tab\*, Archived |
| Options | Yes, No |
| Buttons | Delete, New Item, Save |
| Required errors | Title is required · URL is required |
| Save error | There was an error saving the products menu. Please try again. |

### 6.5 Behaviour and styles

`config-item.js` and `config-item.less` as built (087 §6.3, §6.4): drag on the card header, renumbering, collapse
(all cards open on load), New Item (focus on its Title), Delete queued until Save (focus to the next card's toggle
or New Item), required check of Title / URL before any call, Save as sequential deletes then one update per card
(`order` = position), reload on success, error c-alert and a retry that recreates nothing otherwise. No page JS or
page LESS.

---

## 7. Preserved Functionality & Analytics Inventory

| v1 behaviour | v2 |
|---|---|
| Sysadmin / quick-links holder access, 403 for others | Unchanged |
| Endpoints, field names, `order` = position, `newTab` / `archived` `'true'` / `'false'` | Unchanged |
| Delete on Save, deletes before updates, one call at a time | Unchanged |
| Reload on success | Unchanged |
| Collapse toggle, cards open on load | Kept |
| Drag reordering, mouse / touch | Kept |
| New card defaults (Open in a new tab No, Archived No) | Kept (D2) |
| Stored `buttonText` | Kept through a hidden input |
| Placeholders | Kept (D6) |
| Header / offcanvas / footer Products menus, nav "On" state, `/crisis-pages` | Unchanged (stored shape unchanged) |
| Page view | Still fires; new `pageTitle` (§2.6) |

**Intentional differences:** the help panel is dropped (D6); URL becomes required and both required fields are
checked before any call (D3); the server bugs are fixed (D4, D11); a c-alert replaces `alert()`; a retry after a failed
save creates no duplicates; card ids are unique.

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
- **Delete:** named "Delete Products Menu Item N" through `aria-labelledby`.
- **Errors:** inline field errors; focus on the first invalid field; the Save error is a `role="alert"` c-alert.
- **Busy state:** Save disabled during the calls.
- **Reordering:** mouse and touch only; keyboard users cannot reorder (WCAG 2.1.1), accepted as on Package Links
  (D8). The handle icon is `aria-hidden`.
- CSS `:hover` / `:focus-visible` only; no Bootstrap classes or data attributes.

---

## 9. Decisions Taken

Every decision was asked and confirmed with the user.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Copy (Figma vs v1) | Figma with "New Item" / Figma throughout ("New Menu") / v1 ("Quick Links Item N", uppercase labels) | Figma with "New Item" | **Figma, add button "New Item"** (§6.4); each card is one link, not a menu |
| D2 | New card's Open in a new tab (Figma: "Select" placeholder) | Default No / required placeholder (needs select errors in `hdxV2.setFieldError`) | Default No | **Default No** (v1, Package Links) |
| D3 | Required fields | Title + URL client-side / Title only | Title + URL | **Title + URL**; an empty URL would render an empty link in the Products menus |
| D4 | v1 server bugs (§2.4) | Package Links' fixes + tests / `items` only / shared code for both views | Fixes + tests | **Fixes + tests** (§6.1); two cases in the existing test file |
| D5 | Fields (Title, URL, Open in a new tab and `buttonText` repeat `package_link_fields.html`) | Shared link-fields snippet / own snippet per page | Shared snippet | **Own snippet** `admin/snippets/quick_link_fields.html`: a different page with its own scope |
| D6 | v1 help panel | Drop / new-tab tip as a field hint | Drop | **Drop**; v1 placeholders kept |
| D7 | Count (hidden in Figma) | Hide / show | Hide | **Hide** |
| D8 | `c-config-item` behaviour (collapse, drag only, reload, no success message / unsaved warning / empty state) | Keep as Package Links / revisit (shared component) | Keep | **Keep**; no component change |
| D9 | Subtitle (the list also feeds `/crisis-pages`) | Figma as-is / mention crisis pages | Figma as-is | **Mention crisis pages** (§6.4) |
| D10 | Names | — | — | **Doc `088-sysadmin-products-menu-v2.md`; ids `quick-link-<n>`; Archived options No / Yes (v1 order); save-error and required-error copy as §6.4** |
| D11 | Missing URL on the server (a stored `url: null` 500s every v2 page through `hdx_get_quick_links_list`) | 400 on missing URL / 400 + `or ''` guard in the helper / leave | 400 on missing URL | **400 on missing URL** (§6.1), one more test case; the helper is unchanged |
| D12 | Page templates (`admin/quick_links.html` repeated `admin/package_links.html` except its values) | Two page templates / shared base | Two templates | **Shared base** `admin/config-item-base.html`; each page sets its values (§6.2) |
| D13 | Unused code in the view (`_remove_file_by_path` + `GlobalUpload` import, commented-out fields, unused `h` / `log`) | Leave / remove the function + import / remove all | Leave | **Remove the function + import** (§6.1) |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/config-item-base.html` | New: shared editor base (§6.2) |
| `THEME/templates/admin/quick_links.html` | Full v2 replacement, on the base (§6.2) |
| `THEME/templates/admin/package_links.html` | Moved onto the base, same HTML (§6.2) |
| `THEME/templates/admin/snippets/quick_link_fields.html` | New: one card's fields (§6.3) |
| `THEME/views/quick_links_custom_settings.py` | `items` for the template; D4 / D11 fixes; unused function removed (§6.1) |
| `THEME/tests/test_quick_links/test_quick_links.py` | Unknown id → appended, others untouched; no title → 400, config unchanged; no URL → 400, config unchanged |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md`, `ckanext-hdx_theme/llm_docs/redesign/requirements/087-sysadmin-package-links-v2.md` | Migrated page; Package Links on the base |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 088 status |

Not changed: `c-config-item` (template, LESS, JS), `package_link_fields.html`, v1
`admin/quick_links.js` / `.css`, `admin-quick-links-scripts`, `admin-scripts`, `admin-styles` (kept on disk; this
page no longer loads them), the actions, the consumers in §2.2, the components demo.

---

## 11. Implementation Checklist

1. Read the stored config on the local stack (item count, `buttonText`, string `newTab` / `archived`, null `url`),
   after asking.
2. Apply the D4 and D11 fixes and `items` in the view, remove the unused function (D13); add the three test cases.
3. Add `admin/snippets/quick_link_fields.html`.
4. Add `admin/config-item-base.html`, move `admin/package_links.html` onto it (same HTML), replace
   `admin/quick_links.html`.
5. Run render-level checks, then hand the visual test to the user.
6. Update the docs in §10 and `STATUS.md`.

---

## 12. Risks & Edge Cases

| Case | Handling |
|---|---|
| A call fails mid-save | Earlier calls stay applied (v1); the alert shows, Save re-enabled; a retry skips finished deletes and recreates nothing |
| Two sysadmins saving at once | Last writer wins per item (v1). An item the other adds during your save makes your new card's reply carry two new ids, which counts as a failure, so a retry creates that card's item again (087 §12) |
| An item another sysadmin deleted | Its update appends it again (D4) instead of overwriting the last item |
| `/event` or `/dashboards` links | Listed here; hidden from the Products menus by `exclude_crisis`; non-archived `/event` links show as Ongoing on `/crisis-pages` |
| Archived set to Yes | The link leaves the Products menus and shows under Archived on `/crisis-pages`, whatever its URL |
| Stored `newTab` / `archived` as strings | `'true'` / `'false'` handled in §6.3 |
| Stored `buttonText` | Hidden input keeps it |
| A `url: null` already stored | Still 500s every v2 page (the helper is unchanged, D11); the §11 step 1 check confirms there is none |
| Keyboard-only sysadmin needs to reorder | Not possible (D8) |
