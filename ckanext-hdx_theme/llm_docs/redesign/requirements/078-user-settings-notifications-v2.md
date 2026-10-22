# 078 — User Settings: Notifications Settings (v2 Migration)

**Scope:** `/user/notifications/<id>` (`hdx_user.notifications`), the list of a user's email-notification
subscriptions (the "Subscribe to Notifications" system of task 051). The page moves into the 072
dashboard shell, and Unsubscribe opens the 051 unsubscribe drawer on the same page.

**Excluded:**
- the bell-icon notifications (055, an unrelated feature);
- the subscribe flow and the object-page drawers (051), except moving the two unsubscribe drawers into a
  shared snippet;
- the subscription model, actions, auth rules, Novu sync and the unsubscribe endpoint;
- frequency and channel settings (no backend exists);
- the other settings pages.

**Figma source:** `figma_exports/xl-user-settings-notifications.html` (XL only).

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`. `USERS` = `ckanext-hdx_users/ckanext/hdx_users`.

---

## 1. Audit Findings

### 1.1 Route, access and data
- **View:** `notifications(id)` in `USERS/views/user.py`, rule `/notifications/<id>` on the `hdx_user`
  blueprint.
  - Anonymous → redirect to `user.login` with `came_from`.
  - `user_show` with `include_num_followers` (only the v1 profile card uses it); `NotFound` → 404,
    `NotAuthorized` → 403.
  - `hdx_notifications_subscription_list` with `user_id=id`. Its auth is core `user_update` on that
    user: another non-sysadmin user gets 403, a sysadmin passes.
  - Per subscription: `object_dict` (`package_show` / `group_show` / `organization_show` / `page_show`),
    `object_link` (`_generate_url_for`, external), `unsubscribe_token` and `unsubscribe_email` (the viewed
    user's email).
  - `ObjectNotFound` → warning, subscription dropped. Any other exception re-raises: `NotAuthorized`
    (a followed dataset that became private) reaches the outer handler, so **the whole page 403s**;
    anything else → 500.
  - Renders `user/notifications.html` with `subscriptions`, `user_dict` and `analytics`. It passes no
    `is_myself`.
- **Token defect:** tokens are looked up with `current_user.id`, not the subscription owner. On a
  sysadmin's view of another user, Unsubscribe carries an empty token, or the sysadmin's own token when
  they follow the same object.
- **Data** (`HDXNotificationsSubscription`): `object`, `object_type` (dataset / organization / group /
  crisis), `event_type` (`new-dataset-added` / `dataset-updated`), `state`, `created`, `updated`, and a
  unique unsubscribe token. The list is sorted by `updated` desc, page size 1000.
  - No channel or frequency fields exist. There is no update action, so unsubscribing is the only thing
    a user can change.
  - New subscriptions are always `new-dataset-added` (`subscription_confirmation` hard-codes
    `dataset_updates = False`); `dataset-updated` only exists on older subscriptions.
- **Entry points:** the v2 sidebar and header user menu (`notifications_settings` item of
  `h.hdx_get_user_dashboard_nav_sections()`, label "Notifications settings", shown when `is_own` or
  `user_update` passes), the v1 `read_base.html` "Notifications" tab and the v1 `header-global.html`
  link.
- **Tests:** none request the page. `USERS/tests/test_notification_platform/test_notification_platform.py`
  covers subscribe/unsubscribe.

### 1.2 Rendering (v1)
- **Chain:** `THEME/templates/user/notifications.html` → `user/read_base.html` → v1 `page.html`, plus
  the `bem-blocks-styles` and `hdx_theme/ckan` bundles.
- **Shell:** breadcrumb Users / {name}, heading "User Settings", BS5 tab bar, col-3 profile card.
- **Content:**
  - Heading "Subscriptions", then an hr.
  - **Empty:** "To set up notifications use the “Subscribe” button on dataset, crisis, organisation or
    location pages." The v2 opt-in button is labelled "Get Notified" (`OPT_IN_TEXT`).
  - **Row:** link "{Type}: {title}" to `object_link`. The type is `capitalize`d, and group shows as
    Location ("Dataset", "Organization", "Location", "Crisis").
  - **Action:** a red "Unsubscribe" link with a `fa-trash` icon, to
    `{object_link}?_unsubscribe_token={token}`.
  - **3 columns:**
    - Update type: "Dataset is updated" for any dataset. Others map by event type: `new-dataset-added`
      → "New dataset is added"; `dataset-updated` → two lines, "New dataset is added" and "Any dataset
      is updated"; anything else prints the raw value.
    - Receive notifications: "By Email" (static).
    - Update frequency: "As soon as possible" (static).
- `analytics_came_from` block (`analytics.came_from(request.args)`).

### 1.3 Unsubscribe today (051)
- **Hub:** the link navigates to the object page (051 D7).
- **Object page:** `add_unsubscribe_token` validates `_unsubscribe_token` (an invalid one flashes "Your
  token is invalid or has expired."). `unsubscribe.js` then opens `notificationsUnsubscribeDrawer`.
- **Drawers**, from `THEME/templates/notification_platform/modals.html`:
  - `notificationsUnsubscribeDrawer`: title "Unsubscribe", type-specific confirmation text, hidden
    `c-alert`, Cancel (`data-drawer-close`) / Unsubscribe. The Unsubscribe button is
    `#notificationsUnsubscribeButton`, carrying `data-unsubscribe-token`, `-email`, `data-object-id`,
    `-name`, `-type` and `data-is-authenticated`.
  - `notificationsUnsubscribedDrawer`: title "You have unsubscribed", type-specific success `c-alert`,
    Close.
  - All texts come from `UI_CONSTANTS.NOTIFICATION_PLATFORM`: the `_DATASET` variant for datasets, the
    `_SEARCH_RESULTS` variant formatted with the type for the rest (group → "location").
- **JS:** `fanstatic/notification_platform/util.js` `onUnsubscribeSubmit` sends the POST, then:
  - on success: closes the Unsubscribe drawer, opens the Unsubscribed one, removes the localStorage
    subscribed target, and fires the confirm event;
  - on error: shows the message in the drawer's `c-alert`.

  `unsubscribe.js` holds the object-page token logic, the open event and the click binding on
  `#notificationsUnsubscribeButton`.
- **Endpoint:** POST `/notifications/unsubscribe-confirmation` (`token` + CSRF header), `ignore_auth`,
  `hdx_notifications_subscription_delete` (marks the subscription deleted, invalidates the token,
  removes it from Novu). JSON `{success: true}` or `{success: false, error: {message}}`, HTTP 200 either
  way.
- **Bundles:** `notification-platform-util-scripts` (`util.js`) and
  `notification-platform-unsubscribe-scripts` (`unsubscribe.js`, preloads util). Neither depends on a
  v1 bundle.
- The object-page opt-out button and the email links keep using `?_unsubscribe_token` / `_u` on object
  pages. Only the hub link is in scope.

### 1.4 Analytics
- `hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(type, 'unsubscribe from notifications', null, objectId, objectName, objectType, emailHash, authenticated)`:
  - `'show popup'` when the drawer opens (emailHash `null`);
  - `'confirm popup'` on success (hash of `data-unsubscribe-email`).
  - Both are sent to Mixpanel and GTM.
- Object pages send `objectId` = the object's id and `objectName` = its `name`.
- localStorage subscribed-objects is re-synced from the server on every object page for a logged-in user,
  so the hub never needs to update it beyond what `onUnsubscribeSubmit` already does.
- Page-level: `cameFrom` through the `analytics_came_from` block of `base.html`, which `v2/page.html`
  extends.

### 1.5 Reusable v2 pieces
- **Shell:** `THEME/templates/v2/user-dashboard-base.html` (072): menu, breadcrumb, `<title>`, page
  styles, opt-in `user_profile_header` block. Needs `user_dict` and `is_myself`.
- **Header / empty:** `.hdx-v2-user-dashboard-header`, `.hdx-v2-user-dashboard-empty`
  (`pages/user-dashboard.less`).
- **Card:** `c-dataset-card`. Its frame equals Figma's card (neutral-0, neutral-1 border, `radius-sm`,
  `shadow-sm`, 16px padding). Its `labels` top row (org left, labels right) is Figma's hidden top row.
  `caller()` gives an actions row below the body.
  - `c-resource-card` (Figma's layer name) was checked first. It is built around a file-type icon, a
    description clamp and a download footer.
- **Metadata shape:** `c-page-header` `meta_items` (label, value, `tooltip`, `chip`), the same pattern as
  Figma's columns (label + hidden info icon, value + hidden cyan chip).
- **Drawer:** `c-drawer` + `window.hdxV2Drawer(id)` (focus trap, ESC, overlay, `[data-drawer-close]`,
  `drawer:close` event, focus returns to the trigger), `.c-drawer-form` / `__text` / `__buttons`.
- **One drawer, many triggers:** 074's `hdx-connect-drawers.html` + `fanstatic/v2/pages/hdx-connect.js`
  (trigger JSON → fill → open → POST → reload).
- **Button:** `button.html` tertiary s with `icon_src='v2/icons/delete.svg'`.

---

## 2. Figma Analysis (XL)

- **Breadcrumb:** Home / Account and Settings / Notifications Settings. The sidebar is the pre-072 menu;
  the 072 menu applies.
- **Header:** "Notifications Settings" (display-s) + subtitle "Set how often you receive email
  notifications, or unsubscribe entirely" (body-s, neutral-85), 6px apart. A count ("28"), "Results per
  page" and "Sort by" are hidden.
- **List:** cards 24px apart and 24px below the header, full content width (961px), min-height 130px.
- **Card:**
  - Hidden top row: org name + two labels (light, yellow).
  - Title row: title 16px semibold neutral-95, one line with ellipsis, then "Unsubscribe" on the right.
    The button is white, with a neutral-2 border, `shadow-sm`, 4/8 padding, a 14px delete icon, a 12px
    medium label and a 6px gap. A second button is hidden.
  - Cards 3–4 (variant B) add a "Dataset" chip (neutral-05, 12px) under the title. Their title still
    reads "Dataset:…".
  - 20px gap, then the meta row: 3 equal columns 20px apart. Each column has a label (16px semibold,
    neutral-85, hidden 16px info icon), then 8px, then the value (16px regular). "By Email" has a
    hidden cyan chip.
  - Copy is v1's: "Update type:", "Receive notifications:", "Update frequency:", "Dataset is updated",
    "New dataset is added", "By Email", "As soon as possible".
- **Not in Figma:** the drawer, empty state, errors, pagination, another user's page, MD and SM.

---

## 3. Current vs Target / Component Mapping

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, col-3 profile card | `v2/user-dashboard-base.html` |
| Identity | Profile card for every user | Profile header on another user's page only |
| Breadcrumb | Users / {name} | Own: Home / Account and Settings / Notifications Settings. Others: Home / Users / {name} / Notifications Settings |
| Label | Tab "Notifications"; v2 menu "Notifications settings" | "Notifications Settings" (D6) |
| Header | "User Settings" + "Subscriptions" | Title + subtitle (D7, D9) |
| Item | Bootstrap row, red text link | `c-dataset-card` with `meta_items` and a title action (D4) |
| Title | "{Type}: {title}" link | Same (D5, D21) |
| Unsubscribe | Link to the object page | Same-page 051 drawer (D1–D3); none on another user's page (D8) |
| Empty | v1 text with "Subscribe" | Dashboard empty state, "Get Notified" (D10) |
| Inaccessible object | Whole page 403 | Dropped with a warning (D11) |
| Assets | `bem-blocks-styles`, `hdx_theme/ckan` (v1) | Base styles + a page script bundle; no v1 bundles |

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `<title>` | **Reuse** the base, `user_nav_active='notifications_settings'`, `page_label=_('Notifications Settings')` |
| Profile header | **Reuse** the base's `user_profile_header` block |
| Header | **Reuse** `.hdx-v2-user-dashboard-header` markup |
| Card | **Extend** `c-dataset-card`: `meta_items` + a title-row action (D4) |
| Unsubscribe button | **Reuse** `button.html` tertiary s, `delete.svg` |
| Drawers | **Extract** 051's two unsubscribe drawers from `modals.html` into a shared snippet (D1) |
| Submit + analytics | **Reuse** `util.js` `onUnsubscribeSubmit` unchanged (D1, D13) |
| Hub behaviour | **New** `fanstatic/v2/pages/notifications-settings.js` (D1, D2) |
| Empty state | **Reuse** `.hdx-v2-user-dashboard-empty` (D10) |
| List | **Reuse** `c-dataset-card-list` (D23) |

---

## 4. Template Strategy

- `THEME/templates/user/notifications.html` is replaced wholesale. It extends
  `v2/user-dashboard-base.html`, as 076's `user/permission.html` and 077's `user/api_tokens.html` do,
  and keeps the `analytics_came_from` block. No shared v1 snippet changes, so no `{% if v2 %}` / `v2=true`.
- `THEME/templates/notification_platform/unsubscribe_drawers.html` (new) holds the two drawers from
  `modals.html`, with the confirmation text, the success text and the submit-button attrs as params.
  `modals.html` includes it with the values it computes today, so object pages render the same markup.
- The hub renders the drawers snippet once (own page with subscriptions only). It never includes
  `modals.html` (no signup drawers, no `#notification_platform_data`, no reCAPTCHA) and never loads
  `unsubscribe.js`.
- **Assets:** the base's `v2-search-page-styles` + `v2-user-dashboard-page-styles`. The template loads
  `notification-platform-util-scripts`, then a new page bundle with `notifications-settings.js` (D24).
  The drawers need `v2-components-scripts`, which every v2 page loads.
- The "Notifications" tab of `user/read_base.html` now lands on the v2 page.

---

## 5. Page Structure

- **Content** (`{% block primary %}`):
  1. Another user's page only: `{{ self.user_profile_header() }}`.
  2. `.hdx-v2-user-dashboard-header`: title "Notifications Settings" (`<h1>` on your own page, `<h2>`
     under the profile header) + subtitle (D7 / D9).
  3. With subscriptions: a `<ul class="c-dataset-card-list">` (D23), one `<li>` + `c-dataset-card` per
     subscription:
     - `title` = "{Type}: {object title}" (D5, D21), `title_href` = `object_link`;
     - `meta_items` = Update type / Receive notifications / Update frequency, with v1's values (D19);
     - own page with an active token only (D20), the title action: Unsubscribe (tertiary s, `delete.svg` left) with a JSON
       data attribute holding the token, object id, name, type, email and the two type-specific texts
       (D3).
  4. Without subscriptions: `.hdx-v2-user-dashboard-empty` (D10).
  5. Own page with subscriptions: the drawers snippet.
- **New `c-dataset-card` params** (D4):
  - `meta_items` {list}: `label`, `value`, optional `tooltip` {text, id, aria_label} and `chip`
    {text, color}, as in `c-page-header`. It renders a `<dl>` below the title, in the left column
    (D25, D26).
  - `title_action` {dict}: `button.html` params, rendered right of the title.
- **Spacing (tokens):**
  - list: `c-dataset-card-list` as is (`gap: var(--hdx-space-4)`) plus a list reset (D23);
  - title row → meta row: `var(--hdx-space-5)`;
  - meta columns: `gap: var(--hdx-space-5)`;
  - label → value: `var(--hdx-space-2)`;
  - meta text: `.hdx-body-s-semibold()` label / `.hdx-body-s()` value, neutral-85 (D12).

---

## 6. Behavior and Logic

- **Hub JS** (`notifications-settings.js`):
  - **Open:** a click on an Unsubscribe trigger keeps its data, sets the drawer's
    `.c-drawer-form__text` and the Unsubscribed drawer's `c-alert` message, and hides a previous error.
    It then opens `notificationsUnsubscribeDrawer` and fires the `'show popup'` event (D13).
  - **Confirm:** a click on `#notificationsUnsubscribeButton` calls `onUnsubscribeSubmit` with the kept
    data and the button's `data-is-authenticated`.
  - **After success:** `drawer:close` on `notificationsUnsubscribedDrawer` (Close, X, overlay or ESC)
    reloads the page (D2).
- **View** (`notifications()`):
  - `NotAuthorized` from `_get_object_dict` is handled like `ObjectNotFound`: `log.warning`, and the
    subscription is dropped (D11).
  - `user_dict` and `is_myself` come from `_extra_template_variables()` (D15).
  - Tokens and the email are looked up on your own page only (D8).
- **Unchanged:**
  - the anonymous redirect, the list action, its auth and order;
  - the unsubscribe endpoint, the delete action and the Novu removal;
  - CSRF;
  - the 051 drawer texts, buttons and error handling;
  - the object-page and email-link flows;
  - both analytics events and `cameFrom`.

### Risks & Edge Cases

| Case | Handling |
|---|---|
| Unsubscribe fails (invalid/used token, network) | Error text in the Unsubscribe drawer's `c-alert` (051 behaviour); the drawer stays open |
| Object deleted | Dropped with a warning, as today |
| Object no longer readable (private, left the org) | Dropped with a warning (D11) |
| No active token for a subscription | Card without Unsubscribe (D20) |
| Sysadmin on another user's page | Profile header, read-only list, no drawers or JS (D8) |
| Deleted user | 404 for non-sysadmins; a sysadmin sees the profile header's "Deleted" label (D15) |
| Several subscriptions | One pair of drawers; each trigger refills them before opening |
| `modals.html` refactor | Same rendered output on dataset, org, location and crisis pages; verify by diffing the rendered drawers before/after |
| Long titles | Card title 2-line clamp (D4) |

---

## 7. Responsive Behavior & Accessibility

- **XL (≥ 80rem):** sticky 25% menu on the left (072). Cards at full content width (D14). Meta in 3 equal
  columns. Unsubscribe beside the title.
- **MD:** no menu (the header user menu navigates). Meta in 3 columns (D17).
- **SM:** meta stacked (D17). Unsubscribe wraps under the title (D16).
- **Drawer:** `c-drawer` widths 100% SM / 80% MD / 50% XL, unchanged.
- **Accessibility:**
  - One `<h1>`: the page title on your own page, the profile header's title on another user's.
  - The list is a `<ul>`; each Unsubscribe button names its object (D18); the delete icon is decorative.
  - The drawer is a labelled `role="dialog"` with `aria-modal`, a focus trap, ESC and overlay close, and
    focus returns to the clicked Unsubscribe.
  - Errors are visible text in the drawer's `c-alert`.
  - `:focus-visible` rings come from the components.

---

## 8. Decisions Taken

| # | Decision |
|---|---|
| D1 Drawer flow | Same-page drawer, reversing 051 D7 for the hub. Reuse 051's Unsubscribe + Unsubscribed drawers via a shared `notification_platform/unsubscribe_drawers.html` (included by `modals.html`). A new `notifications-settings.js` fills and opens them; `onUnsubscribeSubmit` posts unchanged. |
| D2 After success | The Unsubscribed drawer shows; closing it reloads the page. |
| D3 Drawer content | 051 as-is: "Unsubscribe", the type-specific confirmation text, Cancel / Unsubscribe; no object-name line. The texts follow the clicked card's type, from the same constants as object pages. |
| D4 Card | Extend `c-dataset-card` with `meta_items` (c-page-header item shape) and a title-row action. The title keeps the card's 16/18px 2-line clamp. |
| D5 Title | v1's "{Type}: {title}" link; no type chip. |
| D6 Label | "Notifications Settings" in `h.hdx_get_user_dashboard_nav_sections()`: both menus, breadcrumb, page title and `<title>`. |
| D7 Subtitle | Figma's: "Set how often you receive email notifications, or unsubscribe entirely". |
| D8 Other user | Read-only for a sysadmin on another user's page: no Unsubscribe, no drawers, no hub JS. |
| D9 Other-user subtitle | "Email notifications {name} receives" (display name); the title is an `<h2>` under the profile header. |
| D10 Empty | `.hdx-v2-user-dashboard-empty`. Own: "To set up notifications use the “Get Notified” button on dataset, crisis, organisation or location pages." Others: "{name} hasn't set up any email notifications." |
| D11 Inaccessible object | `NotAuthorized` is treated like `ObjectNotFound`: warning, subscription dropped; no page 403. |
| D12 Meta text | 14px: `.hdx-body-s-semibold()` label, `.hdx-body-s()` value, neutral-85. |
| D13 Analytics | Both events identical to the object pages': object id and `name`, popupSource `null`, hashed email on confirm. `analytics_came_from` kept. |
| D14 Widths | The card list is 100% of the content column at every width. |
| D15 View data | `notifications()` takes `user_dict` and `is_myself` from HDX `_extra_template_variables()` (bare `user_show`, deleted user 404 for non-sysadmins); `include_num_followers` is dropped. |
| D16 SM action | At SM, Unsubscribe wraps under a full-width title. |
| D17 Meta layout | 3 equal columns at MD+, stacked at SM. |
| D18 Button name | Each Unsubscribe has `aria-label` "Unsubscribe from {Type}: {title}". |
| D19 Update type | v1's mapping. `dataset-updated` is one value with a line break between "New dataset is added" and "Any dataset is updated". |
| D20 Missing token | A subscription without an active token gets no Unsubscribe; the card still renders. |
| D21 Type label | "Organisation", the v2 spelling: an explicit type → label map (Dataset / Organisation / Location / Crisis) replaces `capitalize`. |
| D22 Tests and demo | Extend `USERS/tests/test_notification_platform/test_notification_platform.py`: own GET 200 with the token, another user 403, a sysadmin on another user 200 without Unsubscribe, anonymous → login, a `NotAuthorized` object dropped. `components.html` gets a `c-dataset-card` demo with `meta_items` + a title action. |
| D23 List | `<ul class="c-dataset-card-list">`, the component's own wrapper: 16px gap, as on My Datasets, not Figma's 24px. The wrapper gets `list-style: none` and zero margin and padding. |
| D24 util.js | Loaded explicitly in the template before the page bundle, which declares no preload. |
| D25 Meta markup | A `<dl>`: one `<div>` per item, with `<dt>` for the label (+ info-icon) and `<dd>` for the value (+ chip). |
| D26 Meta position | Inside `__left`, after the description. The 20px gap is `calc(var(--hdx-space-5) - var(--hdx-space-13))` on top of the column's 6px gap. |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/notifications.html` | Rewritten: dashboard base, profile header, header, card list, empty state, drawers (D1–D10) |
| `THEME/templates/notification_platform/unsubscribe_drawers.html` | New: the two 051 unsubscribe drawers (D1) |
| `THEME/templates/notification_platform/modals.html` | Includes the new snippet; output unchanged (D1) |
| `THEME/templates/v2/components/dataset-card.html` | `meta_items` + title-row action params, header comment (D4) |
| `THEME/templates/v2/components.html` | Card demo: `meta_items` + title action (D22) |
| `THEME/hdx-styles/src/common/less/v2/components/dataset-card.less` | Title row and meta row (D4, D12, D16, D17, D26); list reset (D23) |
| `THEME/fanstatic/v2/pages/notifications-settings.js` | New: fill/open, confirm, reload (D1, D2, D13) |
| `THEME/fanstatic/webassets.yml` | Page script bundle (D24) |
| `USERS/views/user.py` | `notifications()`: `NotAuthorized` skip, `_extra_template_variables()`, own-page token lookup (D8, D11, D15) |
| `THEME/helpers/helpers.py` | Menu label (D6) |
| `USERS/tests/test_notification_platform/test_notification_platform.py` | View tests (D22) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/051-subscribe-notifications-drawer-v2.md` | D7, §4.3 and the `notifications.html` row (D1) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/029-implement-dataset-card-component.md` | New params (D4) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/072-user-dashboard-my-organisations-v2.md` | Menu label (D6) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated-page entries |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 078 status |
