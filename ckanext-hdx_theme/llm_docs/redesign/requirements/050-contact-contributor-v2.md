# 050 — Contact Contributor Page (v2)

**Scope:** Migrate `/dataset/<id>/contact/` (Contact Contributor) to v2 — page layout,
header text, form fields, dropdown, textarea, and button row.
**Excluded:** backend email logic, form submission flow, NAVL validation changes.
**Figma sources:** `contact-contributor-xl.html`, `contact-contributor-md.html`, `contact-contributor-sm.html`

---

## Context

The Contact Contributor page lets authenticated users send a question or comment about a
specific dataset directly to its contributor. The HDX team receives a CC copy.

This is a v2 visual migration — no functionality changes. The existing CKAN NAVL validation,
form POST, email sending, and analytics tracking must remain intact.

---

## 1. Existing Page Audit

### Templates

| Item | Path |
|---|---|
| **Main template** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/contact_contributor.html` |
| **Base template** | `page_light.html` |
| **Email (to contrib)** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/email/content/contact_contributor_request.html` |
| **Email (confirmation)** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/email/content/contact_contributor_request_confirmation_to_user.html` |

v1 renders four BEM form snippets directly inside the template:

```jinja2
{{ h.snippet('bem.blocks/select2_field.html', name="topic", ...) }}
{{ h.snippet('bem.blocks/input_field.html',   type="text",  name="fullname", ...) }}
{{ h.snippet('bem.blocks/input_field.html',   type="email", name="email", ...) }}
{{ h.snippet('bem.blocks/textarea_field.html', name="msg",  ...) }}
```

### View / Logic

| Item | Detail |
|---|---|
| **View class** | `DatasetContactContributorView` — `ckanext-hdx_package/ckanext/hdx_package/views/dataset.py` (lines 547–649) |
| **Logic class** | `DatasetContactContributorLogic` — `ckanext-hdx_package/ckanext/hdx_package/controller_logic/dataset_contact_contributor_logic.py` |
| **Email action** | `hdx_send_mail_contributor` — `ckanext-hdx_package/ckanext/hdx_package/actions/get.py` (lines 888–944) |
| **Auth** | `hdx_send_mail_contributor` — `ckanext-hdx_package/ckanext/hdx_package/actions/authorize.py` (lines 52–66): user must be authenticated |
| **Topics** | `ckanext-hdx_package/ckanext/hdx_package/helpers/membership_data.py` |
| **URL** | `/dataset/<id>/contact/` → named route `hdx_dataset.contact_contributor` |

**GET handler:** fetches `package_show`, checks auth, blocks request-data datasets (404),
redirects unauthenticated users to login with `came_from`.

**POST handler:** parses and validates form via `DatasetContactContributorLogic`;
on success sends email and re-renders with `message_sent=True`; on failure re-renders
with `errors` and `error_summary`.

### Form Fields

| Field name | Type | v1 snippet | Required | Pre-filled |
|---|---|---|---|---|
| `topic` | select | `bem.blocks/select2_field.html` | ✅ | — |
| `fullname` | text | `bem.blocks/input_field.html` | ✅ | `c.userobj.fullname` |
| `email` | email | `bem.blocks/input_field.html` | ✅ | `c.userobj.email` |
| `msg` | textarea | `bem.blocks/textarea_field.html` | ✅ | — |
| `pkg_title` | hidden | — | — | `pkg_dict.title` |
| `pkg_owner_org` | hidden | — | — | `pkg_dict.owner_org` |
| `pkg_id` | hidden | — | — | `pkg_dict.name or pkg_dict.id` |

**Topic options (static, from `membership_data.py`):**
- `general question` → "General question"
- `metadata` → "Metadata"
- `problem report` → "Problem report"
- `suggested edits` → "Suggested edits"

### Validation

CKAN NAVL system via `dictization_functions.validate()`. Schema:
```python
{
    'topic':    [not_empty, unicode_safe],
    'fullname': [not_empty, unicode_safe],
    'email':    [not_empty, email_validator, unicode_safe],
    'msg':      [not_empty, unicode_safe],
}
```

Errors are returned as `errors` dict and `error_summary` string to the template.
v1 renders `error_summary` in a Bootstrap `.alert.alert-danger` block above the form.

### Page States

**State 1 — Form view (default):** Shows header text, optional error alert, form fields,
Cancel + Submit buttons.

**State 2 — Success view (`message_sent=True`):** Header text changes to success variant.
Form is hidden. Two hidden inputs are injected for analytics:
```jinja2
<input type="hidden" id="message_sent"   value="{{ message_sent }}">
<input type="hidden" id="message_subject" value="{{ message_subject }}">
```

### Analytics JS

File: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/pages/contact-contributor.js`

Fires `hdxUtil.analytics.sendMessagingEvent('dataset', 'contact contributor', topic)`
when `message_sent=True`. Reads `#message_sent` and `#message_subject` from the DOM.
Loaded via `{% asset 'hdx_theme/contact-contributor-scripts' %}` only when `message_sent`.

---

## 2. Figma Mapping

### HTML Structure (identical across all breakpoints)

```
.intro-hdx
├── .header-parent           ← page header block
│   ├── .header              ← h1: "Contact the contributor"
│   ├── .container           ← p: "Use the form to ask a question…"
│   └── .container           ← p: "This form sends feedback…hdx@un.org."
└── .form                    ← form section
    ├── .container           ← dataset name (bold)
    ├── .label-what-is-your-name-parent   ← field group × 4
    │   ├── .label-what-container         ← label + required *
    │   └── .dropdown / .form-field / .form-field3   ← input element
    └── .buttons-parent
        ├── .buttons         ← Cancel (tertiary)
        └── .buttons2        ← Submit (primary blue)
```

### Dimensions per Breakpoint

| Property | XL | MD | SM |
|---|---|---|---|
| Outer padding | `2rem 3rem` | `2rem 3rem` | `1.5rem 1rem` |
| Content max-width | `36.25rem` (580px) | `36.25rem` | full width |
| Title font-size | `2rem` Merriweather | `2rem` | `1.5rem` Merriweather |
| Section gap (header ↔ form) | `1.5rem` | `1.5rem` | `1.5rem` |
| Form field gap | `1.25rem` | `1.25rem` | `1.25rem` |
| Label–input gap | `0.5rem` | `0.5rem` | `0.5rem` |
| Input height (text) | `2.313rem` | `2.313rem` | `2.313rem` |
| Dropdown height | `2.125rem` | `2.125rem` | `2.125rem` |
| Textarea height | `9.375rem` | `9.375rem` | `9.375rem` |
| Input padding | `0.5rem 0.75rem 0.5rem 1rem` | same | same |
| Border | `1px solid #d8e0e1` (`--hdx-neutral-2`) | same | same |
| Border-radius | `2px` (`--hdx-radius-sm`) | same | same |
| Buttons align | `flex-end` | `flex-end` | `flex-end` |

### Label Styling

- Font weight: `500` (medium)
- Color: `--hdx-neutral-85` (`#2f3536`)
- Required asterisk: separate `<span>` in `--hdx-error-6` (`#c44536`)
- Pattern: `"Your name "` + space + `"*"` in error color

### Figma Gaps

| Gap | Detail |
|---|---|
| No error state in Figma | Must preserve v1 per-field and summary error behavior |
| No success state in Figma | Must preserve v1 success copy and analytics inputs |
| No focus/active states in Figma | Follow v2 token conventions (`:focus-within`, border 2px) |

---

## 3. Form Component Strategy

| Field | Figma element | Existing v2 component | Decision |
|---|---|---|---|
| Topic dropdown | `.dropdown` / `.select` (2.125rem height) | `c-dropdown` (JS, size-m: 2.125rem ✅) | **Use the separate `select.html` component (native `<select>`-backed field), not `c-dropdown` — no `native` param exists on `c-dropdown`** |
| Your name | `.form-field` (2.313rem height) | `c-search-input` size-l: 2.5rem (≈ Figma 2.313rem) | **Use `text-field.html` size-l, `type='text'`, wrapped in `c-form-field`** |
| Your email | `.form-field` (2.313rem height) | same | **Use `text-field.html` size-l, `type='email'`, wrapped in `c-form-field`** |
| Comments | `.form-field3` (9.375rem height) | none | **Use `text-field.html` with `multiline=True`, wrapped in `c-form-field`** |
| Cancel button | `.buttons` (tertiary, bordered) | `c-button` style=tertiary size=m tag=a ✅ | Reuse directly |
| Submit button | `.buttons2` (primary blue) | `c-button` style=primary size=m button_type=submit ✅ | Reuse directly |

---

## 4. Textarea Strategy

No v2 textarea component exists. The old BEM `bem.blocks/textarea_field.html` is Bootstrap-
dependent and uses v1 classes — it must not be reused.

### Approach: `text-field.html` with `multiline=True`

`text-field.html` (the generic form-field component, distinct from the search-only `search-input.html`) supports a `multiline` parameter. When `True`:
- Render `<textarea name rows>` instead of `<input>`
- Skip the icon / password-toggle / clear-button block entirely
- Accept a `rows` parameter (default: `4`)

**Snippet usage:**

```jinja2
{% snippet 'v2/components/text-field.html',
    multiline   = True,
    name        = 'msg',
    id          = 'field-msg',
    placeholder = 'Ask a question or provide comments',
    value       = data.get('msg'),
    rows        = 4 %}
```

**CSS:** Add `.c-search-input--textarea` modifier to `input-field.css` (same file as the
base component). This modifier overrides the base styles for the textarea case:
- Fixed `height: @c-input-textarea-l-h` (6.25rem — 4 rows + padding), a Figma size spec matching the `@c-input-l-h` pattern for regular inputs; border-width stays constant across states (color-only)
- `align-items: flex-start` on the wrapper (so padding aligns to the top)
- `height: 100%; resize: none; overflow-y: auto` on the `<textarea>` element
- All other tokens (border, border-radius, padding, font, `:focus-within`) inherit from
  the base `.c-search-input` rules unchanged

---

## 5. Rendering Strategy

### Template placement

Rewrite `contact_contributor.html` in-place to extend `v2/page.html` directly. No `{% if v2 %}` gate — this page had no v1 re-use requirement. All v1 content removed; analytics blocks preserved.

This page's layout CSS (row/content/column/header/form/dataset-name/buttons) lives in the shared
`message-form-page.less` (`v2-message-form-page-styles` bundle), also used by Request Access —
this page has no page-specific LESS file of its own.

### Data flow (unchanged from v1)

| Template var | Source | v2 usage |
|---|---|---|
| `pkg_dict` | view GET handler | dataset name, id/name for form action |
| `contact_topics` | `membership_data.py` | dropdown options |
| `data` | form data on POST error | pre-fill fields |
| `errors` | NAVL validation | per-field error messages |
| `error_summary` | NAVL validation | top-level error display |
| `message_sent` | view POST handler | toggle success state |
| `message_subject` | view POST handler | analytics hidden input |
| `CONST` | `HDX_CONST('UI_CONSTANTS')['CONTACT_CONTRIBUTOR']` | labels and strings |
| `c.userobj` | CKAN user context | pre-fill fullname and email |

### Form skeleton (v2)

```jinja2
<form method="post"
      action="{{ h.url_for('hdx_dataset.contact_contributor', id=pkg_dict.name or pkg_dict.id) }}"
      id="contact-contributor-form">

  {{ h.csrf_input() }}

  {# hidden fields — must not be removed #}
  <input type="hidden" name="pkg_title"     value="{{ pkg_dict.title }}">
  <input type="hidden" name="pkg_owner_org" value="{{ pkg_dict.owner_org }}">
  <input type="hidden" name="pkg_id"        value="{{ pkg_dict.name or pkg_dict.id }}">

  {# topic dropdown #}
  {# name input #}
  {# email input #}
  {# textarea #}
  {# buttons #}
</form>
```

### Success state (v2)

When `message_sent=True`, render the success text using the same `CONST` strings as v1,
and preserve the two hidden inputs for the analytics script:

```jinja2
{% if message_sent %}
  <input type="hidden" id="message_sent"    value="{{ message_sent }}">
  <input type="hidden" id="message_subject" value="{{ message_subject }}">
{% endif %}
```

The analytics JS asset is loaded unchanged — only inside the `{% if message_sent %}` block.

### Error display (v2)

v1 uses a Bootstrap `.alert.alert-danger`. v2 renders:
- **Top-level summary** above the form: the shared `c-alert` snippet
  (`{% snippet 'v2/components/alert.html', message=error_summary %}`) styled with
  `--hdx-error-6` tint and red border. Reused unchanged by drawer forms.
- **Per-field errors** inside each component: `text-field.html` takes an `errors` parameter — when
  set, a `<span class="c-search-input__error">` is appended inside the wrapper (BEM class carried
  over from `search-input.html`), styled in `--hdx-error-6`, CSS in `input-field.css`. `select.html`
  gets its own equivalent pair: a `c-dropdown--error` modifier on the wrapper, and a
  `c-dropdown__error` span rendered *after* (outside) the wrapper — the modifier class is what the
  sibling-selector CSS keys off to make the span visible, in `dropdown.css`.

---

## 6. Responsive Strategy

The form column is a single centered block. No multi-column layout at any breakpoint.

| Breakpoint | Container behavior | Outer padding | Title size |
|---|---|---|---|
| XL (`≥ 80rem`) | fixed `36.25rem`, centered | `2rem 3rem` | `2rem` Merriweather bold |
| MD (`≥ 48rem`) | `80%` width, flex-centered | `2rem 3rem` | `2rem` Merriweather bold |
| SM (`< 48rem`) | full width | `1.5rem 1rem` | `1.5rem` Merriweather bold |

**Column implementation:** outer wrapper (`.hdx-v2-contact-content`) uses `align-items: center` at MD+; inner column (`.hdx-v2-contact-column`) uses `width: 80%` at MD and `width: 50%` at XL. No `max-width` — flex centering matches the existing single-column page pattern.

All form fields are `width: 100%` inside the column — no horizontal layout change needed.

**Button row:** always `display: flex; justify-content: flex-end; gap: 1rem`.
At SM, buttons remain right-aligned side-by-side — matching Figma.

---

## 7. Edge Cases

| Case | Behavior |
|---|---|
| Required field empty | Server-side NAVL error; re-render form with `errors` dict |
| Invalid email format | `email_validator` returns error; show per-field error |
| Long dataset name | Wraps inside container; no truncation |
| Topic not selected | `not_empty` validator fires; dropdown should show error state |
| Authenticated but no dataset | View returns 404 |
| Request-data dataset type | View returns 404 (blocked explicitly in GET handler) |
| Anonymous user | View redirects to login with `came_from` param |
| Message sent success | Form replaced with success text; analytics JS fires once |
| JS disabled | Form submits natively (no JS required for form POST) |

---

## 8. Risks

| Risk | Detail | Mitigation |
|---|---|---|
| Breaking form POST | Renaming fields or removing hidden inputs breaks NAVL validation | Never rename form `name` attrs; always include hidden fields and CSRF |
| Dropdown not submitting | `c-dropdown` is JS-powered and doesn't write to a native `<select>` — CKAN expects `topic` in POST data | Use the `select.html` component, which renders a plain `<select>` |
| Analytics JS breaking | `#message_sent` and `#message_subject` IDs must exist in the DOM when `message_sent=True` | Keep hidden inputs in v2 success block |
| Textarea not existing | No v2 textarea | Use `text-field.html` with `multiline=True` |
| Text input height | `text-field.html` size-m is 2.125rem vs Figma 2.313rem — minor visual delta | Accepted; also aligns the text inputs' height with the topic dropdown's (`size='m'`, 2.125rem) on the same form |
| Error display without Bootstrap | v1 `.alert.alert-danger` cannot be used in v2 | Top-level: shared `c-alert` snippet; per-field: `c-search-input__error` inside component (underlying BEM class kept from `search-input.html`, now used by `text-field.html`) |
| v1 regression | Template was fully rewritten to extend `v2/page.html` — no v1 fallback | Accepted; page_light.html version removed |

---

## 9. Decisions Taken

1. **Dropdown:** Use the `select.html` component (native `<select>`-backed field, distinct from `c-dropdown`), which renders a styled `<select>` element (+ chevron), making the field POST-safe without JS. Takes an `errors` param for per-field error display.

2. **Text input:** Use `text-field.html` with `size='m'`, `type='text'` / `type='email'`, wrapped in `c-form-field`. (Aligned from the original `size='l'` to `size='m'` for visual consistency with Request Access's fields.)

3. **Textarea:** Use `text-field.html` with a `multiline=True` parameter and a `rows`
   param (default 4). When `multiline=True` the snippet renders `<textarea>` instead of `<input>` and
   skips the icon/toggle/clear block. A `.c-search-input--textarea` CSS modifier in
   `input-field.css` sets a fixed `height: @c-input-textarea-l-h` (6.25rem for 4 rows),
   `align-items: flex-start`, and `height: 100%; resize: none; overflow-y: auto` on the inner `<textarea>`. Fixed height is a Figma size spec, same as `@c-input-l-h`; border state changes are color-only.

4. **Error display:** Both per-field and top-level summary, matching v1 behavior.
   - Top-level: the shared `c-alert` snippet above the form, styled with
     `--hdx-error-6` tint and red border — reused unchanged by drawer forms.
   - Per-field: `text-field.html` and `select.html` both take an `errors` param; when set, a
     `<span class="c-search-input__error">` is rendered inside the wrapper (BEM class carried
     over from `search-input.html`). CSS in `input-field.css`.

5. **Success state:** Same centered column layout as the form. Uses `CONST.PAGE_TITLE_MESSAGE_SENT`
   and `CONST.BODY_MAIN_TEXT_MESSAGE_SENT` strings unchanged from v1.

6. **Textarea CSS location:** `input-field.css` — textarea is a mode of `text-field.html`, which
   shares `search-input.html`'s underlying BEM classes, so its modifier lives in the same file.

7. **Button row on SM:** Side-by-side at all breakpoints, matching Figma. No stacking.

8. **Dataset name display:** Inline markup directly in the template — no snippet. Renders
   `CONST.DATASET_NAME_TEXT.format(pkg_dict.title)` inside a `<p>` with semibold styling.
