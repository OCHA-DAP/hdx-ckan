# 091 — Crisis Page Edit Form: Figma Alignment (v2)

**Scope:** the custom / crisis page Add and Edit form (`/page/new`, `/page/edit/<id>`, `hdx_custom_page.new` /
`.edit`), built in v2 by 090 without a form design, adjusted to the official exports. This covers the layout, step
links, header, field order, copy, section cards (including reordering), actions and the component extensions they
need (D2, D7, D8, D11).

**Excluded:**
- The Custom Pages listing (`/ckan-admin/pages/show`, 090) and the delete drawer snippet (reused unchanged).
- The read pages (`/event/<id>`, `/dashboards/<id>`, 060), the `page` model, the actions, auth and the POST contract.
  The only backend change is the section type labels (D9).
- New validation rules (D6) and the 082 org form, which keeps its `c-slug-preview` output.

**Figma sources:** `xl-edit-crisis-event-page.html`, `sm-edit-crisis-page-form.html` in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. There is no MD export (D16).

**Path abbreviations:**
- `THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`
- `LESS` = `THEME/hdx-styles/src/common/less/v2`
- `PAGES` = `ckanext-hdx_pages/ckanext/hdx_pages`

---

## 1. Overview & Objective

| | |
|---|---|
| Target | `THEME/templates/pages/edit_page.html` and its section snippet, as implemented by 090 |
| Objective | Match the Figma structure and look: step links in the left column, a page header with intro and required note, two numbered groups ("Describe crisis page", "Build sections"), Figma field order and copy, reorderable section cards and Figma's action row. Keep the routes, POST contract, auth, redirects and Lunr rebuild |
| Strategy | In-place edit of the 090 form. For this form, 091 supersedes 090 D5 (the menu column), D6 (no reordering), D10 (no help text), D13 (heading), D29 (button visual order), D30 (chip look) and the §6.9 copy |
| Shared work | A `c-anchor-links--numbered` modifier (D40); opt-in `c-config-item` options for move buttons, no collapse and a footer Delete (D2, D30); `description` on `radio.html`, `select.html`, `text-field.html` and `c-slug-preview` (D8, D11); c-label grey chips by default and a cyan `chip_color` on `select.html`, fed by c-label mixins (D7, D29, D37). Defaults keep every other caller's output unchanged (the demo's chips turn grey, D29) |

---

## 2. Repository Audit Findings

### 2.1 The form as built (090)

- **Shell:** extends `v2/sysadmin-base.html` (`nav_active='custom_pages'`), which renders the sysadmin menu in
  `secondary_content` (XL only, sticky) and the crumb Home / Sysadmin / Custom Pages / {page_label}. `page_label` is
  "Create custom page" / "Edit custom page".
- **Header:** `v2/list-header.html`, h1 with `title_size='dashboard'` (`.hdx-dashboard-title()`, 24px at every width).
  There is no intro.
- **Form** `#create_page_form.hdx-v2-custom-page-form` (100%, 80% from MD):
  - an error `c-alert` for keys other than `title` / `name` / `tag_string`;
  - h2 "Page details" (`.hdx-section-title()`) with Title (`text-field` m, required), URL (`c-slug-preview`, required,
    prefix follows Type), Display page title (`c-checkbox`), Type and Status (`c-radio` fieldsets, one-line labels
    "Event (URL: …)"), Location and Tags (`select.html` `multiple` + Select2, chips in the 090 D30 c-selection-item look)
    and Keywords (`text-field` m);
  - `<hr class="c-divider">`, then h2 "Sections": a `c-config-item-list` in form mode with `c-config-item` cards
    (`draggable=False`, h3 "Section N", collapse toggle and Delete in the header), the body from
    `THEME/templates/admin/snippets/custom_page_section_fields.html`, a `<template>`, and a tertiary
    "Add More Sections" (`plus.svg`) below the list;
  - actions: tertiary "Delete This Page" on the left (edit only, opens the `c-drawer`), then "Save This Page" (primary)
    and "Save As Draft" (secondary), visual = DOM (090 D29).
- **Page JS** `THEME/fanstatic/v2/pages/custom-page-form.js`: type → fields toggle, `hdx_counter` raised on
  `config-item:add`, slug prefix follows the Type radio. **Shared JS** `THEME/fanstatic/v2/components/config-item.js`:
  form mode (no Sortable, no Save), add / delete / collapse, `renumber()` rewrites titles from `data-title-format`.
- **Page LESS** `.hdx-v2-custom-page-form` in `LESS/pages/sysadmin.less` (bundle `v2-sysadmin-page-styles`).
- **Bundles loaded by the template:** `v2-select2-styles`, `v2-select2-scripts`, `v2-slug-preview-scripts`,
  `v2-config-item-scripts`, `v2-custom-page-form-page-scripts`.

### 2.2 Contract and behaviour to preserve

- POST names and ids, `hdx_counter`, `save_custom_page=active` / `save_as_draft_custom_page=draft`, `show_title`
  posting `on`, the `tag_string` list join, CSRF, auth (404 for non-holders), the redirects (090 D12), the Lunr
  rebuild and the 090 D19 / D27 server fixes. The type → fields mapping (`section_fields` in the template) and the
  `hidden` + `disabled` toggling.
- `_populate_sections()` (`PAGES/views/light_page.py`) reads `field_section_<i>_*` for `i` in `0 … hdx_counter − 1`
  and skips missing or `empty` indices. **The saved order is the index order**, so reordering only needs the names
  renumbered to DOM order before submit (D2); the backend is unchanged.
- The section type labels come from `light_page.py` `data_dict['content_type']` and appear only in the form's select.
  `section_types`, which `_get_default_title()` reads, holds empty strings, so the labels never reach the read pages.
- The read pages print a section's `description` inside a plain `<span>` (`templates/pages/snippets/section_item.html`,
  `templates/light/custom_pages/read.html`), so line breaks don't survive (D12).
- Drafts (`state` other than `active`) pass only the sysadmin bypass: a permission holder can't list or open their own
  draft (D10 copy).
- `PAGES/tests/test_controller.py` asserts `Save This Page` on the new and edit GETs (D9).

### 2.3 Reusable v2 pieces

| Piece | Use here | Gap |
|---|---|---|
| `v2/components/anchor-links.html` + `components/anchor-links.js` (base bundle) | Step links in `secondary_content` (`package/hdx_read.html` precedent) | No numbering (D40) |
| `c-config-item` + `config-item.js` | Section cards | Move buttons, no collapse, footer Delete (D2) |
| `radio.html` | Type / Status | No second line (D8) |
| `select.html` + `select.js` + `dropdown.less` | Location / Tags / Section | No description (D11); one chip look (D7) |
| `text-field.html` | Text fields | No description above the control (D11) |
| `c-slug-preview` | URL | No description (D11) |
| `label.less` colour modifiers | Chip colours | Classes, not mixins (D7) |
| `.hdx-heading-h3()`, `.hdx-body-m-semibold()` | Group headings, note | — |
| `hdx-v2-content-columns--stack` + `__sidebar` / `__content` (`layout.less`, org Stats precedent) | Group heading beside its fields at XL | — |
| `button.html`, `text-button.html`, `c-checkbox`, `alert.html`, `custom_page_delete_drawer.html` | As today | — |
| `hdxV2.setDisabled()` (`fanstatic/v2/utils.js`) | Disabled Move buttons | — |

---

## 3. Figma Design Analysis

### 3.1 XL (`xl-edit-crisis-event-page.html`, 80rem frame)

**Page:** white body, padding 16 / 48 / 80, 24px gap between the left column (17.375rem) and the main column. Crumb
"Home / Edit crisis page". No sysadmin menu.

**Left column:** padding-top 40; a "Share data" label (dataset-form artefact; 16px medium, 16px gap, D39), then two
numbered items in the `c-anchor-links` look: "1. Describe crisis page" active (2px primary-5 bar, medium) and
"2. Build sections" (regular, neutral-85).

**Main column:** padding-top 40, a 48px gap between the header, each group and the actions row.
- **Header** (gap 16): h1 "Edit crisis page", Merriweather bold 32px, neutral-95. An intro in 16px neutral-85: v1's
  "How this page works" text with typos ("tor", "Have", "dran"), which still promises a preview. A note in 16px
  semibold error-5: "Required sections and fields are marked with an asterisk (*)." (v1 contribute-flow copy).
- **Groups:** each has a 1px neutral-3 top border and 24px vertical padding. On the left, a heading in a 260px column
  (18px semibold, numbered list: "Describe crisis page *", "Build sections"); 20px gap; the fields column (602px)
  with a 30px gap between fields.
- **Group 1, in order:**
  1. "Title of the page *" (16px medium neutral-85, asterisk error-5), input; "Display page title" checkbox below it.
  2. "This page is located under: *", two radios with two-line labels: "Event" (medium) over
     "URL:https://data.humdata.org/event/page_id" (regular); "Dashboards" over the dashboards URL.
  3. "URL/Slug *", a description line in regular grey: "This is how the URL will appear on HDX, you can change this
     below.", then an always-visible input with a joined prefix box "data.humdata.org/event/".
  4. "Status *", radios Ongoing / Archived.
  5. "Location *", a description line: "Describe the location(s) or country / countries that this dataset covers.",
     then a select with chips in brand-1 / brand-85, radius 4, padding 2 / 6, 14px (= c-label cyan s).
  6. "Keywords *", input.
  7. "Tags *", a select with chips in neutral-1 / neutral-95 (= c-label grey s).
  - Inputs: 37px, 16px text, padding 8 / 12 / 8 / 16, neutral-2 border, radius 2 (≈ size l). Selects: 34px, 14px,
    padding 8 / 8 / 8 / 10, `--hdx-shadow-sm` (= size m). No chip has a remove ×.
- **Group 2:** first a primary button "Add more sections" with `file-plus` (20px), then the cards (30px gap). Each
  card: white, 1px neutral-3 border, radius 2, padding 15 / 20, gap 10, full column width.
  - **Header:** `format-paragraph-spacing` handle icon + "Section N" (16px medium); on the right, "Sort:" (14px) and
    two caret-in-square buttons (up, down). No collapse toggle.
  - **Fields:** "Section *" select ("Interactive data", "Data list"); "Data URL *"; "Title of the section";
    "Description" drawn as a 55px box; "Max height"; "Mobile max height".
  - **Footer:** "Delete this section" (14px medium, underlined, icon after the label), right-aligned.
- **Actions:** 1px neutral-3 top border, 24px padding; right-aligned, gap 16: "Save as draft" (secondary), then
  "Save this page" (primary), 16px text, padding 8 / 12. No delete action.

### 3.2 SM (`sm-edit-crisis-page-form.html`, 393px)

Built on the dashboard SM frame with its menu hidden: no step links. Crumb "Home / Edit crisis page". Padding 24 / 16.
- **Header:** h1 24px; intro 14px; note 16px semibold.
- **Groups:** stacked, heading above the fields (gap 20), fields gap 30.
- **Cards and buttons:** cards fill the width (361px); the add button reads "Add more files" (artefact); the action
  row is right-aligned as at XL.

### 3.3 Artefacts (ignored)

"Share data"; "Add more files"; the hidden contact-contributor paragraph; the hidden PII / Microdata / Terms of Service
checkboxes; the hidden info icons and aliceblue helper boxes ("Sub-national means…"); the SM count "28",
"Results per page" / "Sort by" and user-dashboard menu; the hidden "You might also like" block; both radios drawn
checked; the placeholders "ie.", "e.g. https://example.com/population-jan-2011.json" (also on Title of the section)
and "600px"; the sample values and the intro typos.

---

## 4. Current vs Figma Comparison

| Element | Current (090) | Figma | Decision |
|---|---|---|---|
| Left column (XL) | Sysadmin menu | Label + numbered step links to the two groups | D1, D39, D40 |
| Crumb | Home / Sysadmin / Custom Pages / {h1} | Home / {h1} | D1 (kept) |
| h1 | `list-header`, 24px, "Create / Edit custom page" | 24 → 32px, "Edit crisis page" | D9, D18 |
| Intro, required note | None | v1 help text + red note | D10 |
| Groups | h2 "Page details" / "Sections", `c-divider` between | Numbered headings, top borders, heading column at XL | D9, D16, D19 |
| Width | 100%, 80% from MD | Full main column | D21 |
| Field order | Title, URL, Display, Type, Status, Location, Keywords, Tags | Title, Display, Type, URL, Status, Location, Keywords, Tags | D17 |
| Field gap | 20px | 30px | D20 |
| Control sizes | m | Inputs and buttons ≈ l, selects m | D13 |
| URL | `c-slug-preview` (preview + Edit) | Always-visible input with a prefix box | D5 |
| Field descriptions | None | URL, Location | D11, D26, D27 |
| Type radio labels | One line | Two lines | D8 |
| Required markers | Title, URL | Also Type, Status, Location, Keywords, Tags, Section, Data URL | D6 |
| Chips | c-selection-item look, × | Cyan (Location), grey (Tags), no × | D7, D29 |
| Add sections | Tertiary, `plus.svg`, below | Primary, `file-plus`, above | D14 |
| Card header | Collapse + Delete | Handle + "Sort:" up / down | D2, D15 |
| Card Delete | Header, "Delete" | Footer, "Delete this section" | D2, D9 |
| Section Description | Single line | 55px box | D12 |
| Labels and buttons | v1 Title Case | Sentence case | D9, D28 |
| Delete page | Tertiary, left | Absent | D4 |
| Save buttons | Save This Page · Save As Draft | Save as draft · Save this page | D3, D9 |
| Actions row | Wrapping flex row | Top border, right-aligned | D20 |

---

## 5. Component & System Reuse Strategy

| Need | Mapping | Type | Decision |
|---|---|---|---|
| Shell, crumb, `<title>`, page styles | `v2/sysadmin-base.html` | Reuse | D1 |
| Step links | `anchor-links.html` in `secondary_content`, `heading`, `c-anchor-links--numbered` | Reuse + modifier | D1, D24, D39, D40 |
| Header | `v2/list-header.html` (`title_size='dashboard'`, `list_subtitle`) + note `<p>` | Reuse | D18 |
| Groups | `<section>`s on `hdx-v2-content-columns--stack` + page LESS | Reuse + page LESS | D19, D20, D34 |
| Type / Status | `radio.html` `description` | Extend | D8 |
| URL | `c-slug-preview` `description` | Extend | D5, D11 |
| Location / Tags | `select.html` `description` + `chip_color` | Extend | D7, D11, D29 |
| Chip look | c-label mixins in `LESS/mixins.less` | Refactor (output unchanged) | D7, D37 |
| Section cards | `c-config-item` move / no-collapse / footer-Delete options | Extend | D2, D30 |
| Reordering | `config-item.js` | Extend | D2, D32, D33 |
| Posted order | `custom-page-form.js` submit handler | Page JS | D31 |
| Add more sections | `button.html` primary m, `file-plus.svg` | Reuse | D14 |
| Save / Delete buttons | `button.html` | Reuse | D3, D4 |
| Type labels | `light_page.py` `content_type` | Copy | D9 |

**Why extend `c-config-item` instead of page markup:** the cards keep add / delete / renumber / focus handling from
the shared script; the new options are general (any form-mode editor may want ordered items without drag). Without the
new params, 087–089 render and behave as today.

---

## 6. Functional Requirements

### 6.1 Backend

`PAGES/views/light_page.py` `data_dict['content_type']` texts become "Select content type", "Description/text",
"Map", "Key figures", "Interactive data", "Data list" (D9). Nothing else changes.

### 6.2 Template (`THEME/templates/pages/edit_page.html`)

- `page_label` = "Edit crisis page" when `data.id`, else "Create crisis page" (D9). The crumb stays Home / Sysadmin /
  Custom Pages / `page_label`.
- `{% block secondary_content %}` overrides the menu with `anchor-links.html`: items "Describe crisis page" →
  `#describe-crisis-page` (`active`), "Build sections" → `#build-sections`; `heading` "On this page",
  `extra_classes='c-anchor-links--numbered'`, `with_mobile_dropdown` false (D1, D24, D39, D40).
- **Header:** `list-header` as today, with the intro as `list_subtitle` (D10, D18). Below it, a
  `<p class="hdx-v2-custom-page-form__note">` "Required sections and fields are marked with an asterisk (*)." (D23).
- **Form** (ids, names, `enctype`, CSRF and the error alert as today):
  1. `<section id="describe-crisis-page" class="hdx-v2-content-columns hdx-v2-content-columns--stack hdx-v2-custom-page-form__group">`:
     - **Heading:** h2 `__sidebar __group-title` "Describe crisis page" + `<span class="c-form-field__required" aria-hidden="true"> *</span>`.
     - **Fields** (in `__content __fields`, D17):

| Field | Snippet / change |
|---|---|
| Title of the page | `text-field` m, `required`, placeholder v1 |
| Display page title | `c-checkbox` inside the Title's `c-form-field` (D41) |
| This page is located under | Fieldset, legend + asterisk (D6). Radios `label` "Event" / "Dashboards", `description` "URL: {event URL}" / "URL: {dashboards URL}" (D8); `data-slug-prefix` as today |
| URL | `c-slug-preview` as today, `description` (D11, D27) |
| Status | Fieldset, legend + asterisk (D6); radios as today |
| Location | `select` as today, `description` (D11), `chip_color='cyan'` (D29) |
| Keywords | `text-field` m as today |
| Tags | `select` as today (default grey chips, D29) |

  2. `<section id="build-sections">`, classed and split like group 1:
     - **Heading:** h2 "Build sections".
     - **Add button:** "Add more sections" (`button.html` primary m, `file-plus.svg`, `data-config-item-add`), placed
       before the `c-config-item-list__items` and still inside the list wrapper (D14).
     - **Cards:** each `c-config-item` gets `draggable=False`, `title_tag='h3'`, `move_buttons=True`,
       `collapsible=False`, `delete_position='footer'` and `delete_label` "Delete this section" (D2, D30), from one
       `section_card` dict (D44).
     - **Move status:** an sr-only `aria-live="polite"` span in the list wrapper, with the message on a list data
       attribute (D33).
     - **Template, `hdx_counter`, `data-section-fields`, `data-title-format`:** as today.
  3. **Actions row** `__actions`: "Delete this page" (tertiary m, edit only, opens the drawer) on the left. On the
     right, `__save` holds "Save this page" (primary, first in DOM) then "Save as draft" (secondary), shown reversed
     (D3).
- After `</form>`: the delete drawer as today.

### 6.3 Section fields snippet (`THEME/templates/admin/snippets/custom_page_section_fields.html`)

Labels: "Section", "Data URL", "Title of the section", "Description", "Long description", "Max height", "Mobile max
height" (D9). Placeholders, names, ids, the Markdown hint and the hide / disable rules stay as today. The Description
stays a single-line `text-field` (D12).

### 6.4 Component extensions

All params are optional; with their defaults every other caller's HTML is unchanged.

| Component | Change | Decision |
|---|---|---|
| `LESS/components/anchor-links.less` | `c-anchor-links--numbered` (through `extra_classes`): a CSS counter prints "1. ", "2. " … before each label, in the label's weight and colour | D40 |
| `v2/components/config-item.html` | `collapsible` (default `True`): `False` omits the toggle, the body is always shown and the title gets `tabindex="-1"` (D32). `move_buttons` (default `False`): adds a header group, `aria-hidden` "Sort:" text plus two `button.html` icon-only tertiary s (`chevron-up.svg` / `chevron-down.svg`), ids `<id>-move-up` / `<id>-move-down`, `aria-label` "Move up" / "Move down", `aria-labelledby` = own id +
`<id>-heading`, `data-config-item-move="up"` / `"down"`. `delete_position` (default `'header'`): `'footer'` puts the header's Delete (`text-button.html` tertiary s, `delete.svg` before the label) in a right-aligned row after the body. `delete_label` (default "Delete") | D2, D15, D30, D38 |
| `fanstatic/v2/components/config-item.js` | Move: swap the card's `<li>` with its neighbour, `renumber()`, refresh the Move buttons' disabled state (first up / last down, through `hdxV2.setDisabled()`) on load, add, delete and move, and keep focus on the pressed button, or on the card's other Move button when the pressed one becomes disabled. Write the list's move message to its live region (D33). **Delete** without a toggle focuses the next card's title, else the Add button (D32). Without move buttons nothing changes | D2, D32, D33 |
| `LESS/components/config-item.less` | Header layout for the move group; footer row (`justify-content: flex-end`); an items list without cards is hidden | D2, D43 |
| `v2/components/radio.html` + `LESS/components/selection.less` | `description` (default `''`): a `c-radio__description` line under the label (body-s, neutral-7), inside the `<label>` with `aria-hidden="true"` and an id, referenced by the input's `aria-describedby`. The name stays the label, the URL becomes the description. `c-radio--has-description` puts the circle at the first line and wraps the body | D8, D35, D36 |
| `v2/components/select.html` | `description` (default `''`): a `c-form-field__description` line between the label and the control, id `<id>-description`, referenced by the select's `aria-describedby` (`select.js` already carries it to Select2). `chip_color` (default `''`, grey chips): `'cyan'` adds `c-dropdown--chips-cyan` on the `c-dropdown` wrapper | D7, D11, D29 |
| `v2/components/text-field.html` | `description`: same element and wiring, merged with the `hint` id in `aria-describedby` | D11 |
| `v2/components/slug-preview.html` + `LESS/components/slug-preview.less` | `description`: passed to its `text-field` and repeated above the preview row. Only one of the two is visible at a time (the field or the preview is `hidden`) | D11 |
| `LESS/components/form-field.less` | `__description`: body-m, neutral-8 (Figma regular grey; the nearest token) | D11 |
| `LESS/components/dropdown.less` | Multiple-selection chips: the c-label base, size s and grey look, cyan under the modifier, all from the c-label mixins; the × stays. The `.hdx-chip*()` calls go | D7, D29, D37 |
| `LESS/mixins.less` + `LESS/components/label.less` | `.hdx-label()`, `.hdx-label-size-s()`, `.hdx-label-grey()`, `.hdx-label-cyan()`; `label.less` calls them (compiled CSS unchanged). The `.hdx-chip*()` mixins go back into `selection.less` | D7, D37, D42 |

### 6.5 Page script (`THEME/fanstatic/v2/pages/custom-page-form.js`)

The type → fields toggle and the slug-prefix follow are unchanged. The `config-item:add` counter hook goes. On submit,
the script renames each card's `field_section_<i>_` controls to its position (`0 … n − 1`, DOM order) and sets
`hdx_counter` to the card count (D31).

### 6.6 Page LESS (`LESS/pages/sysadmin.less`, `.hdx-v2-custom-page-form`)

- **Width:** the 80%-from-MD rule goes, and the form fills the content column (D21).
- **Note:** `__note` uses `.hdx-body-m-semibold()` in error-5, `--hdx-space-4` below the header (Figma 16px).
- **Spacing:** 48px (`--hdx-space-12`) between the note and the form; the form's own `--hdx-space-12` gap stays
  between the groups and the actions row (Figma's 48px).
- **Groups (`__group`):**
  - 1px neutral-3 top border, padding `--hdx-space-6` 0.
  - A CSS counter on the form, `counter-increment` per group; the heading prints `counter(…) ". "` before its text
    (D19).
  - The heading uses `.hdx-heading-h3()` in neutral-95.
  - The layout comes from `hdx-v2-content-columns--stack`: a column below XL, a row from XL with the heading as
    `__sidebar` (25%) and the fields as `__content`, gap `--hdx-space-6` (D16, D34).
- **Fields (`__fields`):** column, gap `--hdx-space-8` (D20). The checkbox, fieldset and options rules stay as today.
- **Actions (`__actions`):** 1px neutral-3 top border, padding `--hdx-space-6` 0, flex, wrap, gap `--hdx-space-4`.
  `__save` takes `margin-left: auto` and `flex-direction: row-reverse` (D3).
- **Removed:** the `__section-title` rule and the `<hr class="c-divider">`.

### 6.7 Copy

| Element | Text |
|---|---|
| h1 / crumb / `<title>` | Create crisis page · Edit crisis page |
| Intro | You can use this form to create a custom page for different sections of the site (such as an event page). When you finish, save the page, or save it as a draft that only sysadmins can see. |
| Note | Required sections and fields are marked with an asterisk (*). |
| Step-links heading | On this page |
| Step links / group headings | Describe crisis page · Build sections |
| Labels | Title of the page, Display page title, This page is located under, URL, Status, Location, Keywords, Tags |
| Radio labels / descriptions | Event — URL: {event URL} · Dashboards — URL: {dashboards URL} · Ongoing · Archived |
| Descriptions | URL: This is how the URL will appear on HDX. · Location: Describe the location(s) or country / countries that this page covers. |
| Section labels | Section, Data URL, Title of the section, Description, Long description, Max height, Mobile max height |
| Section type options | Select content type, Description/text, Map, Key figures, Interactive data, Data list |
| Card | Section {n} · Sort: · Move up / Move down (accessible names) · Delete this section · Moved to position {n} of {total} (announced) |
| Buttons | Add more sections, Delete this page, Save as draft, Save this page |
| Placeholders, Markdown hint, drawer | v1 / 090, unchanged |

### 6.8 Behaviour

- **Create:** empty form, Event / Ongoing / Display page title on, no sections (as today).
- **Step links (XL):** clicking scrolls to the group; the active link follows scrolling (`anchor-links.js`).
- **Sections:**
  - "Add more sections" appends "Section N" at the bottom of the list and focuses its Section select.
  - Move up / down reorders the cards and their titles and announces the new position; the first card's up and the
    last card's down are disabled.
  - Delete this section removes the card and focuses the next card's title, or Add more sections (D32).
- **Save:** the posted sections follow the visual order (D2). Enter in a text field submits "Save this page" (D3).
- **Unchanged:** the error re-render, the redirects, the delete drawer and the slug preview.

---

## 7. Preserved Functionality

| Behaviour | 091 |
|---|---|
| Access, 404s, POST contract, field ids the tests read | Unchanged |
| Draft vs publish by submit button; Enter publishes | Unchanged (D3) |
| Type → fields, disabled when hidden | Unchanged |
| Add / delete sections, `empty` sections skipped | Unchanged |
| Slug preview following Title and Type | Unchanged (D5) |
| Location / Tags Select2, tag autocomplete, comma Keywords | Unchanged; chip colours (D7) |
| Delete page from the form, drawer | Unchanged (D4) |
| Redirects, Lunr, page view | Unchanged; `pageTitle` becomes "Create / Edit crisis page \| Sysadmin" |

**Intentional differences:**
- Step links replace the sysadmin menu on this page (D1).
- Sections can be reordered and have no collapse toggle (D2).
- An intro paragraph and a required note come back (D10).
- Sentence-case copy (D9).

---

## 8. Responsive & Accessibility

### 8.1 Breakpoints

| | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Left column | Heading + numbered step links, sticky | None (header user menu) | Same as MD |
| h1 | 24px | 24px | 24px |
| Intro | 14px | 14px | 14px |
| Groups | Heading column 25% + fields | Heading above fields (D16) | Same as MD |
| Cards | Fields-column width | Full width | Full width |
| Actions | Delete left, saves right | Same, wraps | Same, wraps |

### 8.2 Accessibility

- **Landmarks / headings:** step links are the component's `<nav aria-label="Page sections">` with `aria-current`
  kept in sync by `anchor-links.js`. Headings run h1 → h2 per group → h3 per card. The group and step-link numbers
  are generated content; the h2 and link texts carry the names.
- **Move buttons:** real buttons named "Move up Section N" / "Move down Section N" (own `aria-label` + heading).
  They are disabled at the ends with `aria-disabled` and `disabled`, and the focus rule is in §6.4. The "Sort:" text
  is `aria-hidden`. Each move is announced through the list's polite live region (D33).
- **Descriptions:** radio descriptions and field descriptions are referenced by `aria-describedby`. The radio's
  accessible name stays "Event" / "Dashboards".
- **Required:** asterisks are `aria-hidden`; Title and URL keep native `required`. Type and Status are radio groups
  that always have a value.
- **Order:** the save buttons' DOM order (primary first) differs from their visual order. This is accepted for Enter
  safety (D3).
- **Motion:** the step links' smooth scroll goes through `hdxV2.prefersReducedMotion()`, which is a no-op until the 069
  follow-up re-enables it.
- **Chips:** brand-85 on brand-1 and neutral-95 on neutral-1 both pass AA. The × keeps its accessible name.
- **States:** CSS `:hover` / `:focus-visible` only; no Bootstrap classes.

---

## 9. Decisions Taken

D17, D19–D22 and D24 are derived defaults written into the approved plan; the others were asked and confirmed on
2026-11-04.

| # | Question | Options considered | Recommendation | Decision |
|---|---|---|---|---|
| D1 | Shell (Figma: step links, crumb Home / {h1}) | Step links + 4-level crumb / Figma literally / keep sysadmin menu | Step links + 4-level crumb | **Step links + 4-level crumb**: `anchor-links.html` in `secondary_content`, heading per D39, no mobile dropdown |
| D2 | Section cards (Figma: handle, Sort up / down, footer Delete, no collapse) | Up / down buttons / up / down + drag / Figma layout without reorder / keep | Up / down buttons | **Up / down buttons**, no drag or handle, no collapse, footer "Delete this section"; names renumbered on submit |
| D3 | Save order (Figma: primary last; Enter submits the first button) | Figma look with the primary first in DOM / DOM = visual (Enter drafts) / keep | Primary first in DOM | **Figma look, primary first in DOM** (`row-reverse`) |
| D4 | Delete this page (absent in Figma) | Keep / drop | Keep | **Keep**, left of the actions |
| D5 | URL field (Figma: always-visible prefixed input) | Figma prefixed input / keep `c-slug-preview` | Figma input | **Keep `c-slug-preview`** |
| D6 | Required markers (Figma: nine fields) | Match the server / Figma + new validation / Figma asterisks, browser only | Match the server | **Match the server**: Title, URL; asterisk on the Type and Status legends |
| D7 | Chips (Figma: cyan / grey, no ×) | Figma colours, keep × / one grey look / keep 090 D30 | Figma colours | **Figma colours, × kept**, through c-label colour mixins |
| D8 | Type radio labels (Figma: two lines) | `description` param / one line | `description` | **`description`** on `radio.html` |
| D9 | Copy | Figma sentence case / Figma headings only / keep 090 | Figma sentence case | **Figma sentence case** (§6.7); placeholders v1; URL label "URL"; test assert updated |
| D10 | Intro (Figma: v1 text with typos and a preview claim) | Corrected intro + note / note only / nothing | Corrected + note | **Corrected intro + note** |
| D11 | Field descriptions (Figma: URL, Location) | Both via `description` / Location only / none | Both | **Both**, through a `description` param; Location says "page" |
| D12 | Section Description (Figma: 55px box) | Single line / textarea | Single line | **Single line** |
| D13 | Control sizes (Figma: inputs and buttons ≈ l) | Figma mix / m everywhere | Figma mix | **m everywhere** |
| D14 | Add more sections | Figma primary above / tertiary below | Figma | **Primary m, `file-plus.svg`, above the list** |
| D15 | Sort icons (Figma caret-square not in the set) | chevron-up / down / arrow-up / down / add the Figma icons | chevrons | **`chevron-up.svg` / `chevron-down.svg`** |
| D16 | MD (no export) | Stacked below XL / two-column from MD | Stacked | **Stacked below XL** |
| D17 | Field order | — | — | Figma: Title, Display page title, Type, URL, Status, Location, Keywords, Tags |
| D18 | Header (Figma: h1 32px at XL, intro, note) | `list-header` dashboard / `list-header` page scale / own header | `list-header` dashboard | **`list-header`**, `title_size='dashboard'` (24px), intro as `list_subtitle`, note as a page `<p>` |
| D19 | Group markup | — | — | `<section id>`s, h2 `.hdx-heading-h3()`, CSS-counter number, no `c-divider` |
| D20 | Spacing | — | — | Field gap `--hdx-space-8` (Figma 30); group padding `--hdx-space-6`; heading column and gap per D34; actions gap `--hdx-space-4` |
| D21 | Width | — | — | Full content column (the 80% rule goes) |
| D22 | Card padding | — | — | `c-config-item` as is (16 / 20 vs Figma 15 / 20) |
| D23 | Required note (Figma: "Required sections and fields…", asterisk on group 1) | Figma / "Required fields…", no group asterisk | Fields only | **Figma**: always shown, asterisk on the group 1 heading |
| D24 | Step-link labels | — | — | Group headings without numbers in the text (numbers per D40) |
| D25 | Components demo | Per visible variant | — | **Radio and field `description`, cyan chips, numbered anchor links**; no `c-config-item` entry |
| D26 | Help-text param (Figma: above the control; text-field `hint` renders below) | Reuse `hint` below / new `description` above | `hint` | **`description` above** (§6.4) |
| D27 | URL description (D5 keeps the preview + Edit) | Drop / corrected copy / Figma copy | Drop | **Corrected copy** (§6.7) |
| D28 | "This page is located under" (Figma adds a colon) | No colon / colon | No colon | **No colon** |
| D29 | Chip base (`multiple` has no other real caller) | Grey base + cyan param / 090 D30 default + colour param | Grey base | **Grey base**, `chip_color='cyan'` on Location |
| D30 | `c-config-item` params | `reorder` replacing `draggable` / `draggable` + `move_buttons` | `reorder` | **`draggable` kept** + `move_buttons`, `collapsible`, `delete_position`, `delete_label` |
| D31 | Submit renumbering | Page JS / generic in `config-item.js` | Page JS | **Page JS** (§6.5) |
| D32 | Focus after Delete without a toggle | Next card's title / next card's Delete / next card's Section select | Title | **Next card's title** (`tabindex="-1"`), else Add more sections |
| D33 | Move feedback for screen readers | Polite live region / none | Live region | **Polite live region**: "Moved to position {n} of {total}" |
| D34 | XL heading column (Figma 260px; CONVENTIONS forbids fixed column widths) | Generic column classes / 30% in page LESS / 16.25rem (location.less precedent) | Generic classes | **`hdx-v2-content-columns--stack`**, org Stats precedent: 25% (≈212px at 1280), gap `--hdx-space-6` (Figma 20) |
| D35 | Radio description look (radio labels are 14px regular) | body-s neutral-7 / body-s neutral-8 / body-m / Figma 16px radios | body-s neutral-7 | **body-s, neutral-7**: one step lighter than the label |
| D36 | Two-line radio layout | `c-radio--has-description` / base default for all radios | Modifier | **`c-radio--has-description`**: top-aligned circle, wrapping body; other radios unchanged |
| D37 | Chip mixins | Base + size s + grey / cyan / all 7 colours / colours only | Base + size s + grey / cyan | **`.hdx-label()`, `-size-s()`, `-grey()`, `-cyan()`**; the other colours stay in `label.less` |
| D38 | Footer Delete icon (Figma: after the label) | After / before, as the header Delete | After | **Before the label**, as the header Delete |
| D39 | Step-links heading (Figma: "Share data", a dataset-flow artefact) | On this page / Page sections / Page content / Form steps | On this page | **On this page** through `heading`; its existing style matches Figma's label |
| D40 | Step-link numbers (Figma: numbered list) | `c-anchor-links--numbered` modifier / numbers in the label text / `numbered` param with a number span | Modifier | **`c-anchor-links--numbered`**: a CSS counter like the group headings (D19), through `extra_classes` |
| D41 | "Display page title" spacing (32px under the Title input; Figma 8px) | Checkbox inside the Title's `c-form-field` / negative margin / page wrapper | Inside `c-form-field` | **Inside the Title's `c-form-field`**: its `--hdx-space-2` gap (Figma 8px) |
| D42 | `.hdx-chip*()` mixins (after D37, `selection.less` is their only consumer) | Inline into `selection.less` / keep | Inline | **Inline**: declarations in place, compiled CSS unchanged; the mixins go |
| D43 | Empty section list on Create (its flex gap doubles the space under Add more sections) | Hide the empty `__items` in `config-item.less` / leave | Hide | **Hide** (`:not(:has(> li))`); also the 087–089 empty state |
| D44 | Card params repeated in the loop and the `<template>` | One dict + `**` / both written out | One dict | **One `section_card` dict** (`v2/hdx-connect-request.html` `**params` precedent) |

---

## 10. Files Affected

| File | Change |
|---|---|
| `THEME/templates/pages/edit_page.html` | §6.2 |
| `THEME/templates/admin/snippets/custom_page_section_fields.html` | §6.3 |
| `LESS/components/anchor-links.less`, `THEME/templates/v2/components/anchor-links.html` (docstring) | `c-anchor-links--numbered` (D40) |
| `THEME/templates/v2/components/config-item.html`, `THEME/fanstatic/v2/components/config-item.js`, `LESS/components/config-item.less` | §6.4 (D2, D43) |
| `THEME/templates/v2/components/radio.html`, `LESS/components/selection.less` | `description` (D8) |
| `THEME/templates/v2/components/select.html`, `LESS/components/dropdown.less` | `description`, `chip_color` (D7, D11, D29) |
| `THEME/templates/v2/components/text-field.html`, `THEME/templates/v2/components/slug-preview.html`, `LESS/components/form-field.less`, `LESS/components/slug-preview.less` | `description` (D11) |
| `LESS/mixins.less`, `LESS/components/label.less`, `LESS/components/selection.less` | c-label colour mixins (D7); `.hdx-chip*()` inlined (D42) |
| `THEME/fanstatic/v2/pages/custom-page-form.js` | §6.5 |
| `LESS/pages/sysadmin.less` | §6.6 |
| `PAGES/views/light_page.py` | Type labels (§6.1) |
| `PAGES/tests/test_controller.py` | `Save this page` assert (reordering is client-side; the server already saves in index order) |
| `THEME/templates/v2/components.html` | D25 entries |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | New params, config-item move mode |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 091 status |

Not changed: the listing template, the delete drawer snippet, the model and actions, `anchor-links.js`,
the 087–089 editors' templates, the 082 org form templates.

---

## 11. Implementation Checklist

1. Extend `config-item.html` / `.js` / `.less` (D2). Check that the Package Links, Products Menu and Homepage
   Highlights HTML is identical before and after.
2. Add `description` to `radio.html`, `select.html`, `text-field.html` and `slug-preview.html` and the c-label colour
   mixins with the grey chip default and `chip_color` (D7, D8, D11, D29). Diff the org edit / new, All Sysadmins, search filters and Profile HTML:
   no change expected.
3. Update the section snippet, the form template, the page JS and the page LESS; change the type labels.
4. Update the test assert.
5. Run render checks; hand the visual test to the user.
6. Update the §10 docs and `STATUS.md`.

---

## 12. Risks & Edge Cases

| Case | Handling |
|---|---|
| JS off | Cards post in rendered order; Move, Add, type switching and Select2 need JS (as today) |
| Validation re-render | The server rebuilds `data.sections` in posted (renumbered) order, so the order survives |
| Hidden section fields | Renamed with the rest; `disabled` keeps them out of the post |
| Gaps from deleted cards | Gone: renumbering posts `0 … n − 1`, and `hdx_counter` = n |
| Step links in the dashboard's sticky column | The column (`--sticky`) holds them at the wrapper's own 48px offset; check at XL |
| Long URL descriptions in the radios | Wrap inside `c-radio__body` (`overflow-wrap: anywhere`) |
| Location ids that differ from names (090 D27) | Unchanged |
