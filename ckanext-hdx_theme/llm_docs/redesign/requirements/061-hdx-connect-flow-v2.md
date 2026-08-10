# 061 — HDX Connect Flow (Request Data Access) v2

**Scope:** Migrate the "Request Data Access" flow — destination form page and success/
confirmation state — from legacy `page_light.html`/Bootstrap BEM blocks to v2. Audit (not
rebuild) the dataset-page entry point, which is already v2. Close three analytics/visibility/
Figma-parity gaps identified between v1/Figma and the already-shipped v2 dataset page.
**Excluded:** backend changes — routes, view classes, logic classes, validators, email sending,
`ckanext-requestdata` model/actions all unchanged; no new business logic.
**Figma sources:** `dataset-page-hdx-connect-xl.html`, `request-access-form-xl.html`,
`request-access-form-sm.html`, `request-access-form-sent-xl.html`, `request-access-form-sent-sm.html`

---

## Context

"HDX Connect" (a.k.a. "Request Data Access") lets a logged-in user request access to a dataset
that is marked `is_requestdata_type` (a "metadata only" dataset with no downloadable resources).
It is the conceptual mirror image of the Contact Contributor flow (task 050, already migrated to
v2): a dataset is never both request-data-type and contact-eligible — the two flows 404 each
other's routes.

The dataset-page entry point (resource-card "Request data" button, "Request only data" page-
header label) is **already implemented in v2** and already matches the new Figma export. The
destination form page (`templates/package/request_access.html`) and its success state are
**still on the legacy `page_light.html` template** using Bootstrap-dependent `bem.blocks/*`
snippets — this is the actual migration target, following the same pattern already established
by Contact Contributor's v2 migration.

Three pre-existing gaps between v1/Figma and the current (already-shipped) v2 dataset page were
found during this audit and confirmed with the requester before drafting this doc — see §9 Risks
and §6 Dataset Page Integration for the resulting decisions.

---

## 1. Existing Implementation Audit

### Routing / backend (unchanged by this task — reference only)

| | Request Data Access | Contact Contributor |
|---|---|---|
| Route | `/dataset/<id>/request-access/` → `hdx_dataset.request_access` | `/dataset/<id>/contact/` → `hdx_dataset.contact_contributor` |
| View class | `DatasetRequestAccessView` — `ckanext-hdx_package/ckanext/hdx_package/views/dataset.py:651-769` | `DatasetContactContributorView` — same file, lines 547-648 |
| Logic class | `DatasetRequestAccessLogic` — `controller_logic/dataset_request_access_logic.py` | `DatasetContactContributorLogic` — `controller_logic/dataset_contact_contributor_logic.py` |
| Auth function | `hdx_request_access` — `actions/authorize.py:174-183` (any logged-in user) | `hdx_send_mail_contributor` — `actions/authorize.py:52-66` (any logged-in user) |
| 404 condition | `NOT pkg_dict.is_requestdata_type` → 404 | `pkg_dict.is_requestdata_type` → 404 |
| Anonymous user | Redirect to `hdx_signin.login`, `info_message_type='hdx-connect'`, `came_from` | Redirect to `hdx_signin.login`, `info_message_type='contact-contributor'`, `came_from` |
| Extra guard | Duplicate-request block: `h.hdx_pending_request_data(...)` (`helpers.py:1066-1067`) — form hidden, notice shown if a request is already pending | none |

These two flows are **mutually exclusive by dataset type** — confirmed exact-inverse 404 guards.
No changes to any of the above are in scope.

### Request Access form fields (current v1, `request_access.html:73-192`)

Schema: `request_create_schema()` — `src/ckanext-requestdata/ckanext/requestdata/logic/schema.py:18-31`.

| Field | Type/widget (v1) | Required | Validators | Prefill |
|---|---|---|---|---|
| `package_id` | hidden | — | `not_empty`, `package_id_exists`, `pending_request_validator` | `pkg_dict.id` |
| `sender_name` | text | ✅ | `not_empty`, `unicode_safe` | `c.userobj.fullname` |
| `email_address` | email | ✅ | `not_empty`, `email_validator` | `c.userobj.email` |
| `sender_organization_id` | select2 + "Other" free text | ✅ | `not_empty`; `sender_organization_id_other`: `not_empty_if_other_selected` | `h.hdx_user_orgs_dict(g.userobj.id, include_org_type=True)` |
| `sender_organization_type` | select2 + "Other" free text | ✅ | `not_empty`; `sender_organization_type_other`: `not_empty_if_other_selected` | `h.hdx_organization_type_dict()` |
| `sender_country` | select2 (**no** "Other") | ✅ | `not_empty` | `h.hdx_location_dict(include_world=False)` |
| `sender_intend` | select2 + "Other" free text | ✅ | `not_empty`; `sender_intend_other`: `not_empty_if_other_selected` | inline dict: Humanitarian Assistance / Academic / Advocacy / Other |
| `message_content` | textarea | ✅ | `not_empty`, `unicode_safe` | — |
| `user_info_accept_terms` | checkbox | ✅ (HTML `required` attr only) | **not present in `request_create_schema()`** — not enforced server-side | unchecked |

`user_info_accept_terms` being client-only-enforced is **existing behavior, not a bug to fix** —
preserved as-is per the "do not change validation logic" constraint (decision confirmed, §11).

v1 also auto-fills `sender_organization_type` from the selected `sender_organization_id`'s known
type: `hdx_user_orgs_dict(..., include_org_type=True)` attaches a `data-org_type` attribute to
each option, and `request-access.js` syncs the type `<select>` on select2's `select`/`clear`
events. See §4/§11 for the v2 equivalent.

### Submission handling

Standard HTML form POST (no AJAX) to `hdx_dataset.request_access`. On success, the view
re-renders the same template with `request_sent=True` (`views/dataset.py:691-696`); on
validation error, re-renders with `errors`/`data`/`error_summary` (`views/dataset.py:682-712`);
unhandled exceptions show a generic "contact an administrator" message (`views/dataset.py:719-722`).

### Success state (current v1)

Same template toggles on `request_sent` (`request_access.html:34-52`), injecting
`<input type="hidden" id="request_sent" value="{{ request_sent }}">` for the analytics script.

Current copy (`helpers/ui_constants/request_access/__init__.py`) — **verified identical to the
new Figma exports, no content changes needed**:
- `PAGE_TITLE_REQUEST_SENT`: "Your request was sent"
- `BODY_MAIN_TEXT_REQUEST_SENT`: `Go back to the <a href="{0}">previous page</a>.`

### Analytics (current v1 + current v2 entry point)

| Event | Trigger | Implementation | Present in v2 entry point? |
|---|---|---|---|
| `sendMessagingEvent('dataset', 'data request', null, null, true)` | Form submitted successfully | `fanstatic/v2/pages/request-access.js:5-11`, reads `#request_sent` | N/A — fires from the destination page, unaffected by entry-point version |
| `hdx_click_stopper` → `sendLinkClickEvent({linkType:'dataset resources', label:'Request data', ...})` | Click on "Request data" CTA | v1: `resources_list.html:59-61` / `resource_req_item.html`; v2: `resource_item_v2.html`'s `request_attrs` dict, forwarded to `resource-card.html`'s button `attrs` (also wired in `resources_list.html`'s empty-resources branch) | ✅ Present |
| `hdx-onboarding-flow` state priming (`data-start-page-type="hdx-connect"`) | Anonymous user clicks CTA | v1: `resources_list.html:59-61`, consumed by `fanstatic/hdx-onboarding-flow.js`; v2: same `request_attrs` dict, added only when `not current_user.is_authenticated` | ✅ Present |

See §8 for the full analytics table.

### Permissions / visibility

- CTA rendered only when `pkg.is_requestdata_type` is true (both v1 and v2).
- `custom_validator.py:710-712` (`hdx_resources_not_allowed_if_requested_data`) blocks uploaded
  file resources on `is_requestdata_type` datasets at the schema level (unrelated to this task,
  reference only).
- Access to the form itself: any authenticated user, no org-membership/role gate.

### Entry point (dataset page, already v2 — audit only, not a rebuild target)

- `templates/package/snippets/resource_item_v2.html:26-27,48` sets `hdx_connect =
  pkg.is_requestdata_type` and `request_href`.
- `templates/v2/components/resource-card.html:198-206,221-225` renders the primary "Request
  data" button + eye-off icon overlay in place of the Download button.
- Empty-resources case: `templates/package/snippets/resources_list.html:38-45` renders the same
  card with `hdx_connect=True` and description "To access data please use the request button."
- Page header: `templates/v2/components/page-header.html:133-137` renders a "Request only data"
  yellow label chip (via `page-header.html:24,135`) when `pkg.is_requestdata_type`.
- **Confirmed via `grep`: this label chip exists in exactly one place in the current codebase**
  (`page-header.html:135`) — see §2/§6/§11 for the second location Figma shows and the decision
  to add it.

---

## 2. Figma Mapping

### `request-access-form-xl.html` / `request-access-form-sm.html`

Identical structure at both breakpoints (single centered column, no responsive field reflow):

```
.intro-hdx
├── .header-parent              ← "Request access" (h1) + 2 intro paragraphs
├── .container-wrapper          ← contributing org logo
└── .form
    ├── .container              ← "[Dataset] <title>" banner (bold)
    ├── .container6/7           ← "* indicates mandatory fields"
    ├── .label-what-is-your-name-parent  × 6   ← label + required-asterisk + field
    │     (Your name, Your email address, Your organization, Your organization type,
    │      Where are you located?, Intended use of this data)
    ├── .label-what-is-your-name-parent        ← Comments (textarea, `.form-field3`)
    ├── .container7/8                          ← checkbox + acknowledgment text
    └── .buttons-parent
        ├── Cancel (tertiary)
        └── Submit (primary)
```

Field order, labels, and placeholder copy all match the current v1 `CONSTANTS` dict verbatim —
**no field additions, removals, or copy changes**, confirmed by direct comparison. One exception:
the Figma export literally renders the submit button as "Submit," while `CONST.BUTTON_SUBMIT` is
"Send request" — confirmed with requester to keep the existing copy.

### `request-access-form-sent-xl.html` / `request-access-form-sent-sm.html`

Minimal success state — no dataset banner, no org logo, no form:
```
.intro-hdx
└── .header-parent
    ├── "Your request was sent" (h1)
    └── "Go back to the previous page." (link)
```
Matches current v1 `CONST.PAGE_TITLE_REQUEST_SENT` / `CONST.BODY_MAIN_TEXT_REQUEST_SENT` exactly.

### `dataset-page-hdx-connect-xl.html`

Full dataset-page export for an `is_requestdata_type` dataset. Confirms:
- Resource card renders "Request data" primary button + eye-off icon + "To access data please
  use the request button" description — **matches current v2 `resource-card.html` exactly**.
- "Request only data" label chip appears in the title area (`.label` with lock icon) — **matches
  current `page-header.html:135`**.
- **Gap found:** a *second* "Request only data" chip (`.label5`, lock icon) appears in the "Data
  and resources" accordion section header. Grepping the current codebase found the label string
  in exactly one place (`page-header.html:135`) — this second chip does not currently exist
  anywhere in code. **Decision: in scope** — add as a third dataset-page fix alongside §6's two
  decisions, confirmed with requester.
- **Gap found:** a "Contact organisation" button is shown in the top-right org card, even though
  this is an `is_requestdata_type` dataset whose Contact Contributor route 404s. See §6 and §9.
- Two further lock icons appear in the export — next to the "View all" locations link, and next to
  the downloads count in the Metadata tab — outside the three confirmed dataset-page fixes.
  Confirmed with requester as Figma export artifacts, not implemented.

---

## 3. Form Structure Definition

No field structure changes. Full field list (visible + hidden), types, and validators are the
table in §1 above, sourced directly from `request_create_schema()` and the current template —
carried forward unchanged. Restated for clarity per the task's explicit constraints:

- **8 visible fields**, in the exact order Figma and v1 both show: name, email, organization,
  organization type, location, intended use, comments, acknowledgment checkbox.
- **3 hidden fields**: `package_id`, CSRF token (`h.csrf_input()`), plus the analytics hidden
  input injected only on the success state (`request_sent`).
- **No new fields, no removed fields, no changed validators** — this is a pure presentational/
  component migration.

---

## 4. Component Mapping

| Field | Figma element | v2 component | Notes |
|---|---|---|---|
| Your name | `.form-field` | `v2/components/search-input.html` (`type='text'`, `show_icon=False`) | Direct reuse — identical to Contact Contributor's `fullname` field |
| Your email address | `.form-field` | `v2/components/search-input.html` (`type='email'`, `show_icon=False`) | Direct reuse — identical to Contact Contributor's `email` field |
| Your organization | `.dropdown` | `v2/components/select.html` | Reuse Contact Contributor's `select.html` pattern; **"Other" free-text extension** — see decision below. Each `<option>` also carries the org's known type as a `data-org-type` attribute (via a new `option_attrs` param), read by `request-access.js` to auto-fill "Your organization type" below — preserves the v1 org→org-type auto-select behavior |
| Your organization type | `.dropdown` | `v2/components/select.html` | Same as above — "Other" extension; auto-filled from the organization field's `data-org-type` |
| Where are you located? | `.dropdown` | `v2/components/select.html` | Direct reuse — **no** "Other" variant needed (matches current schema) |
| Intended use of this data | `.dropdown` | `v2/components/select.html` | "Other" extension (same as organization fields) |
| Comments | `.form-field3` | `v2/components/search-input.html` (`multiline=True`) | Direct reuse of the extension already built for Contact Contributor — no new component work |
| Acknowledgment checkbox | `.container7`/`.input` + label | `v2/components/checkbox.html` | First use inside a real form — needs `errors`/required-state and a required-asterisk, see decision below |
| Cancel | `.buttons2` (tertiary) | `v2/components/button.html` (`style='tertiary'`, `tag='a'`) | Direct reuse |
| Submit | `.buttons3` (primary) | `v2/components/button.html` (`style='primary'`, `button_type='submit'`) | Direct reuse |

**No new components required.** Four extensions to existing components, all decided below (§11):
the "Other → free text" conditional reveal for 3 of the 4 dropdowns; `errors`/required-asterisk
support on `checkbox.html`; a per-option `data-*` attribute param (`option_attrs`) on
`select.html`, for the organization → organization-type auto-fill; and an
`errors`-driven visible state on `select.html` itself (it previously rendered error text with no
way to make it visible).

**Decision — "Other" conditional reveal:** a conditionally-shown `v2/components/search-input.html`
field next to the `select.html` dropdown, toggled via JS when "Other" is selected. This is the
closest existing-component extension (no new component), confirmed with requester.

**Decision — checkbox errors/required state:** `checkbox.html` gets an `errors` param, mirroring
the `search-input.html`/`dropdown.html` convention — adds a `c-checkbox--error` modifier class and
populates the existing `.c-checkbox__error` span (`checkbox.less:122-140` already defines the
modifier and its sibling-selector display rule). It also gets a required-asterisk span
(`c-checkbox__required`), mirroring `c-search-input__required`/`c-form-field__required` — the
component had no visible required indicator at all before this task, only the native
`required` HTML attribute.

**Decision — organization → organization-type auto-fill:** v1's destination page auto-fills
"Your organization type" from the selected organization's known type (a `data-org_type` attribute
populated via `h.hdx_user_orgs_dict(..., include_org_type=True)`, wired through select2 events).
Confirmed with requester to preserve this. `select.html` gets a new `option_attrs`
param (`{value: {attr_name: attr_value}}`, rendered as extra attributes on each `<option>`), and
`request-access.js` wires a native `change` listener that reads the selected option's
`data-org-type` and sets the organization-type `<select>`'s value, replacing the select2-specific
event handling.

**Decision — dropdown error display:** `select.html`'s `errors` param interpolates error text
into a `<span>` but the wrapper never carried a modifier class, so the sibling-selector CSS that
reveals `.c-search-input__error` never matched — error text was always invisible for every native
dropdown on any page, not just this one. `select.html` gets its own
`c-dropdown--error`/`c-dropdown__error` pair (reusing the modifier styles already defined in
`dropdown.less`), matching the `checkbox`/`search-input` convention of each component owning its
error class.

---

## 5. Submission Flow

```
[Dataset page — entry point]
        │  click "Request data" (any logged-in user; anonymous → sign-in redirect, came_from)
        ▼
[Request Access form — GET /dataset/<id>/request-access/]
        │  fields prefilled (name/email from user profile)
        │
        │  submit (POST, standard form submit, no AJAX)
        ▼
   ┌─────────────┴─────────────┐
   │                           │
[Validation error]      [Validation success]
   │                           │
   ▼                           ▼
Re-render same page      Re-render same page with
with `errors` +           `request_sent=True` —
`error_summary`;          form replaced by success
form fields retain        message; analytics hidden
submitted values           input injected; GA event
   │                       fires once on load
   ▼                           │
(user corrects & resubmits)    ▼
                          [User navigates back via
                           "previous page" link]
```

Duplicate-request case: if `h.hdx_pending_request_data(...)` finds an existing pending request
for this user+dataset, the form is hidden and a notice is shown instead (`request_access.html:69`,
`views/dataset.py:670-672`) — this is a third page state to preserve, not shown in the Figma
exports (which only cover default-form and sent states) — see Edge Cases §10.

---

## 6. Dataset Page Integration

### Entry point (already implemented, v2) — document only

- Resource-card "Request data" button and page-header "Request only data" chip are already built
  and already match Figma — no changes needed to their layout/visuals.

### Three in-scope fixes, confirmed with requester before drafting this doc

1. **Contact-organisation visibility guard.** `page-header.html:300-305` (MD+ card) and
   `:226-230` (SM-only card) render the "Contact organisation" button whenever `org_name` is set,
   with no check on `is_requestdata_type` — unlike v1's `base_actions_menu.html`, which computes
   `hide_contact_contributor = pkg.is_requestdata_type` and hides the link. Since the Contact
   Contributor route 404s for `is_requestdata_type` datasets, the current v2 page header can
   render a button that dead-ends in a 404. **Decision: add the same `is_requestdata_type` guard
   to `page-header.html`'s two "Contact organisation" render blocks**, matching v1 behavior. This
   is an explicit, confirmed deviation from the literal Figma export (which still shows the
   button) — the underlying backend 404 cannot be changed (excluded from scope), so hiding the
   button is the only option that doesn't regress existing functionality.
2. **Entry-point analytics parity.** Add the missing v1-parity click-tracking
   (`hdx_click_stopper` equivalent → `sendLinkClickEvent` with `linkType: 'dataset resources'`,
   `label: 'Request data'`) and anonymous-user onboarding-flow priming
   (`data-start-page-type="hdx-connect"` equivalent) to the v2 "Request data" resource-card
   button, matching what v1 had. **Decision: confirmed in scope**, since "preserve all existing
   analytics/functionality" is a stated critical constraint and this is a real, unintentional gap
   versus v1 — not a deliberate v2 design change.
3. **Second "Request only data" chip.** Add a second lock-icon chip (matching the existing
   `page-header.html:135` chip's copy/styling) to the "Data and resources" accordion section
   header, matching `dataset-page-hdx-connect-xl.html`. **Decision: confirmed in scope** — treated
   as a genuine Figma-confirmed gap, not an export artifact.

---

## 7. Responsive Strategy

| Aspect | XL | SM |
|---|---|---|
| Layout | Single centered column, matching Contact Contributor's pattern | Full-width single column |
| Dataset banner + org logo | Shown | Shown |
| Field stacking | All fields full-width, vertically stacked (same as XL — Figma shows no field reflow) | Same |
| Buttons | Side-by-side, right-aligned (`.buttons-parent`, `flex-end`) | Side-by-side, right-aligned — **Figma does not stack buttons at SM**, matches Contact Contributor's SM behavior |
| Success state | Centered column, header + link only | Same, full width |

No breakpoint-specific field or component differences beyond container width — same pattern
already established by Contact Contributor's v2 migration (`50%`/`80%`/full-width column).

---

## 8. Analytics Preservation

| Event | Source | Must preserve | Status after migration |
|---|---|---|---|
| `sendMessagingEvent('dataset', 'data request', null, null, true)` on success | `request-access.js:5-11`, reads `#request_sent` | ✅ | Unchanged — same hidden-input + JS pattern as Contact Contributor's `#message_sent` |
| Click-tracking on "Request data" CTA (`sendLinkClickEvent`, `linkType: 'dataset resources'`, `label: 'Request data'`) | v1 `hdx_click_stopper` data-module | ✅ | Present in v2 via `resource_item_v2.html`'s `request_attrs` dict, forwarded to `resource-card.html`'s button `attrs` |
| Anonymous onboarding-flow priming (`data-start-page-type="hdx-connect"`) | v1 `hdx-onboarding-flow` data-module, `hdx-onboarding-flow.js` | ✅ | Present in v2 via the same `request_attrs` dict, added only when `not current_user.is_authenticated` |
| Sign-in banner copy for anonymous users (`info_message_type='hdx-connect'`) | `ui_constants/signin/__init__.py:3` | ✅ | Unchanged — server-side redirect logic untouched |

---

## 9. Risks

| Risk | Detail | Mitigation |
|---|---|---|
| Breaking NAVL validation | Renaming any form `name` attribute breaks `request_create_schema()` | Never rename field names; keep exact same `name=` values as v1 |
| Losing "Other" free-text data | The 3 "Other"-enabled dropdowns have no existing v2 conditional-reveal pattern; a naive implementation could fail to submit `*_other` values | Implement per §11 decision (conditional `c-search-input`); test submission of each "Other" path |
| Duplicating components | Building a new dropdown/textarea/checkbox pattern instead of reusing Contact Contributor's established `select.html`/`multiline=True` extensions | Explicit component mapping in §4 reuses existing extensions everywhere except the new "Other" behavior |
| UX inconsistency with Contact Contributor | Diverging field/button/error styling between the two "message the org" flows would look inconsistent | Follow Contact Contributor's v2 template structure (`contact_contributor.html`) as the direct pattern; the shared row/content/column/header/form/dataset-name/buttons LESS lives in one file, `message-form-page.less` (`v2-message-form-page-styles` bundle), loaded by both pages — Contact Contributor has no page-specific LESS of its own beyond that shared set |
| Scope creep from the three dataset-page fixes | §6's three decisions touch already-shipped v2 code (page header, resource card, accordion) outside the literal "form + success page" migration | All three were explicitly surfaced to and confirmed by the requester before drafting — not assumed |
| `user_info_accept_terms` not server-validated | Existing gap (client-only enforcement); fixing it would be a backend/business-logic change | Explicitly out of scope — preserved as-is, called out in §11 for stakeholder awareness |

---

## 10. Edge Cases

| Case | Behavior (preserve as-is) |
|---|---|
| Required field left empty | Server-side NAVL `not_empty` error; re-render with `errors` dict |
| Invalid email format | `email_validator` error; per-field error shown |
| "Other" selected, free-text left blank | `not_empty_if_other_selected` fires; per-field error on the `_other` field |
| Pending request already exists | Form hidden entirely; notice/message shown instead (`hdx_pending_request_data` check) |
| Long comments text | Textarea wraps/scrolls; no character limit enforced today — preserve |
| Anonymous user clicks entry point | Redirect to sign-in with `came_from` + `info_message_type='hdx-connect'` |
| Mobile (SM) layout | Full-width column, fields stacked, buttons side-by-side (not stacked) |
| JS disabled | Form still submits natively (standard POST, no AJAX dependency) |
| Acknowledgment checkbox unchecked | Blocked by HTML5 `required` attribute only (not server-enforced) — existing v1 behavior, preserved; requires the form to not carry `novalidate` (§11.7) |

---

## 11. Decisions Taken

1. **"Other" free-text conditional reveal.** Three dropdowns (organization, organization type,
   intended use) need a free-text field that appears when "Other" is selected. **Decision:** a
   conditionally-shown `v2/components/search-input.html` next to the `select.html` dropdown,
   toggled via JS — the closest existing-component extension, no new component built.
2. **Second "Request only data" chip.** **Decision: in scope** — see §6/§9. Added to the "Data
   and resources" accordion section header, matching the existing `page-header.html:135` chip.
3. **`user_info_accept_terms` server-side enforcement.** Confirmed this field is validated
   client-side only (HTML `required` attr) and is absent from `request_create_schema()`.
   **Decision: preserve as-is** — fixing server-side validation is a backend change, explicitly
   excluded from this task's scope. No follow-up task created; called out here for stakeholder
   awareness only.
4. **Checkbox component fit.** `v2/components/checkbox.html` exists but has not yet been used
   inside a real submitted form. **Decision:** extend it with an `errors` param mirroring the
   established `search-input.html`/`dropdown.html` convention — adds a `c-checkbox--error`
   modifier class and populates the existing `.c-checkbox__error` span. `checkbox.less:122-140`
   already defines the `--error` modifier and its sibling-selector display rule, so this is a
   direct match to existing convention (verified before confirming), not a new pattern. It also
   gets a `c-checkbox__required` asterisk span, matching `search-input.html`/`dropdown.html` —
   the component had no visible required indicator at all.
5. **Dropdown error display.** `select.html`'s `errors` param never actually became visible —
   no modifier class was added for the sibling-selector CSS to key off. **Decision:** give
   `select.html` its own `c-dropdown--error`/`c-dropdown__error` pair (reusing the modifier styles
   already defined in `dropdown.less`), same shape as `checkbox`/`search-input`. This affects
   every page using `select.html` + `errors`, not just this one.
6. **Organization → organization-type auto-fill.** Confirmed to preserve v1's behavior (see §1).
   **Decision:** `select.html` gets a new `option_attrs` param (per-option `data-*`
   attributes); `request-access.js` reads the selected option's `data-org-type` and sets the
   organization-type `<select>`'s value via a native `change` listener, replacing v1's
   select2-event wiring.
7. **`novalidate` removed from both "message the org" forms.** Contact Contributor and Request
   Access both had `novalidate` on their `<form>` with no compensating validation (neither loads
   `v2-form-validator-scripts`), so native HTML5 `required` validation — including the
   acknowledgment checkbox in §11.3 — was silently non-functional. **Decision:** drop `novalidate`
   from both forms. The "Other" free-text fields toggle their `required` attribute in lockstep
   with visibility (not just a CSS hidden class), so a hidden field can't block submission.

---

## Constraints (carried forward)

- No Bootstrap classes (`container`, `row`, `col-*`, `d-*`, etc.)
- No explicit hover-state classes (`is-hovered`) — use CSS `:hover`/`:focus-within`
- Design tokens (`--hdx-*`) and BEM `c-*` component conventions throughout
- No backend/business-logic changes of any kind
- All existing analytics preserved (plus the two v1-parity gaps closed per §6/§8, confirmed in scope)
