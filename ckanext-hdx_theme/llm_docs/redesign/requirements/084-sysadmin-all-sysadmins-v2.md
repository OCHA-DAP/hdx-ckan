# 084 — Sysadmin Dashboard: All Sysadmins (v2 Migration)

**Scope:** `/ckan-admin` (core `admin.index`), plus a v2 sysadmin shell (left menu, breadcrumb, `<title>`)
that only this page adopts now. The v2 header user menu's Sysadmin Dashboard section is aligned to the
same menu (D2). Every v2 avatar takes its initials from one shared helper, and an unlabelled avatar is
hidden from assistive tech (D16, D17).

**Excluded:** The other sysadmin pages, All Users (`/user/`, `user/list.html`) included; later tasks
handle them. v1 `admin/base.html` stays as it is for them. QA Dashboard is not added to the menu.

**Figma sources:** `xl-sysadmin-all-sysadmins.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. The sibling `xl-sysadmin-*.html` exports were
read for the shared shell only.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`.

---

## Context

The page is CKAN core's `admin/index.html` rendered inside HDX's v1 `THEME/templates/admin/base.html`
(BS5 tab bar, `col-3`/`col-9` layout, `admin-styles` bundle). Figma moves it onto the same shell as the
v2 user dashboard (072–079): a left menu at XL, a dashboard header with a count, and a two-column list
of users with a Remove action, followed by a Promote form. `070-v2-full-audit.md` deferred the sysadmin
dashboard to this cycle.

Decisions confirmed with the user are listed in §10.

---

## 1. Audit Summary

### 1.1 Route, access and data
- Route: core `index()` in `ckan/views/admin.py`, blueprint `admin` (`url_prefix='/ckan-admin'`).
  HDX does not override the blueprint, the view, `user.sysadmin` or the `sysadmin` auth.
- Access: the blueprint's `before_request` runs `check_access('sysadmin')` and aborts 403 otherwise.
- 2FA: the rule `/ckan-admin/` is in `protected_urls` of `THEME/plugin.py` `_before_request`; with
  `hdx.security.2fa.redirect` on, a sysadmin without TOTP is redirected to set it up.
- Data: the view passes only `sysadmins = [a.name for a in _get_sysadmins()]` — **usernames**.
  `_get_sysadmins()` filters `sysadmin IS TRUE AND state == 'active'`, has no `ORDER BY`, and includes
  the site user (`ckan.site_id`, `default` in prod).
- There is no pagination, sort, search or empty state (the viewer is always in the list).

### 1.2 Promote / Remove (POST)
- Both forms POST to core `user.sysadmin` (`ckan/views/user.py` `sysadmin()`): `username`, `status`
  (`1` promote, `0` revoke) and `h.csrf_input()`.
- The view calls `user_patch` (`{'id': username, 'sysadmin': status}`), which merges `user_show` into
  `user_update`. HDX chains `user_update` with the onboarding update schema, so the **target's** email
  and fullname are re-validated on every call (`not_empty`, format, duplicate email, fullname regex).
- Outcomes, all redirecting to `admin.index`:
  - success: "Promoted {display_name} to sysadmin" / "Revoked sysadmin permission from {display_name}";
  - unknown user: "User not found";
  - `ValidationError` (e.g. a target with an empty or duplicate email): the error as a flash;
  - `NotAuthorized`: 403.
- No guards exist: a sysadmin can remove themselves, the last sysadmin or the site user. The site user
  is created without an email, so revoking it most likely fails validation.

### 1.3 Rendering (v1)
- "Current Sysadmins" `<h2>`, then a BS table: `h.linked_user(name)` per row (`User.get` + `user_show`
  per row; a Gravatar, prod `ckan.gravatar_default = identicon`) and a red icon-only revoke button
  (`title="Revoke Sysadmin permission"`), submitted with **no confirmation**.
- "Promote user to Sysadmin" `<h2>`, then a text input with the v1 `data-module="autocomplete"`
  (vendored `autocomplete.js`, source `/api/2/util/user/autocomplete?ignore_self=true&q=?`; it submits
  the user's `name`) and a "Promote" button.
- Left column: core's "Administer CKAN" box (sysadmin-guide link), via `secondary_content`.
- Heading "Sysadmin Dashboard"; `<title>` block "Administration".
- Tab bar (`admin/base.html`): "All Sysadmins [N]" with
  `h.hdx_user_count(only_sysadmin=True, include_site_user=True)`, which filters `state != 'deleted'`.
  The list filters `state == 'active'`, so a pending/shadow sysadmin makes the two numbers differ.

### 1.4 Shared v1 shell
`admin/base.html` is shared by every other sysadmin page and by All Users (`user/list.html`). It is
not touched by this task. `test_email_access_by_page` (`ckanext-hdx_users`) asserts `'All Sysadmins ['`
on `/user`, so it keeps passing.

### 1.5 Menus today
- **v1 tab bar:** All Sysadmins, All users, Carousel, HDX Connect Dashboard, Custom/Event Pages, and a
  sysadmin "More" dropdown (Quick Links, Package Links, Email, Config). Carousel, HDX Connect Dashboard
  and Custom/Event Pages are also shown to non-sysadmins holding `hdx_carousel_update`,
  `hdx_request_data_admin_list` or `admin_page_list`.
- **v2 header user menu:** `h.hdx_get_user_menu_sections()` (`THEME/helpers/helpers.py`) adds, for
  sysadmins only, section `{'id': 'sysadmin', 'label': 'Sysadmin Dashboard'}` (DOM ids `desk-sysadmin`
  / `offcanvas-user-sysadmin`): All Sysadmins, All Users, Carousel, HDX Connect Dashboard, Custom/Event
  Pages, Quick Links, Package Links, Email, Config.
- **Global nav (083):** `hdx_v2_main_nav_state` gives `/ckan-admin` no On state; nothing changes.

### 1.6 User autocomplete endpoints
| Endpoint | Action | Returns | Notes |
|---|---|---|---|
| `/api/2/util/user/autocomplete` (core, v1 source) | `user_autocomplete` | `[{id, name, fullname}]` | `q`, `limit` (20), `ignore_self` |
| `/util/user/hdx_autocomplete` (HDX, used by the v2 org-members invite field) | `hdx_user_autocomplete` | `[{id, name, fullname}]` | same params plus `org`; `limit` applies only with `org`, so a one-letter term returns ~25k users locally |

Both match name and fullname (and email for a sysadmin caller), keep `state != 'deleted'` (pending
users included) and do not exclude existing sysadmins.

### 1.7 Analytics and tests
- **Analytics:** nothing page-specific. The generic Mixpanel page view takes `pageTitle` from the
  `subtitle` block ("Administration"). Autocomplete calls are not tracked. The offcanvas user-menu items
  keep their `hdx_click_stopper` attributes.
- **Tests:** no HDX test requests `/ckan-admin` or `user.sysadmin`. `test_page_load.py` has a `pages`
  list with `usertype: 'sysadmin'` rows. Core has `test_admin.py::test_index` and the `test_user.py`
  sysadmin tests (flash texts).

---

## 2. Figma Design Analysis (XL)

- **Shell:** identical to the user dashboard exports.
  - Sidebar: white, 14.063rem, padding 40/48/0, 28px between groups. One group: label "Sysadmin"
    (Roboto 12px regular, `#101212`), 8px gap, 48px items (14px medium, `#3f4748`, padding 0 8px).
  - Active item: 4px `#1862d8` bottom border, `#101212` text.
  - Items: All Sysadmins, All Users, Homepage Highlights, HDX Connect Dashboard, Custom Pages, Products
    Menu, Package Links. The package-links export adds QA Dashboard.
- **Breadcrumb:** Home / Sysadmin / All sysadmins (lower-case "s").
- **Header:**
  - "All Sysadmins" (Merriweather 24px bold) + count "38" (Roboto 16px, `#3f4748`, 8px gap).
  - 6px below: "View and manage who has sysadmin-level access" (14px, `#2f3536`).
  - 24px from the header to the list.
  - Hidden (`display:none`): "Results per page" and "Sort by" dropdowns, a search field.
- **List:** two columns (flex 1 each, 24px gap), rows 8px apart, filled column by column. Each row:
  - a 24px round avatar, initials 12px teal on `#bee0d6`;
  - 6px gap;
  - the display name: 14px regular, underlined link to `/user/<name>`, `#2f3536`, fixed 285px;
  - 6px gap;
  - "Remove": 14px `user-close` icon, 2px gap, 12px medium underlined, `#1862d8`.
- **Promote:** 3rem below the list, a right-aligned 23.813rem block:
  - "Promote user to sysadmin:" (14px, `#2f3536`);
  - 6px below, a select-style field: placeholder "Username", chevron-down, 1px border, 2px radius,
    drop shadow;
  - 12px below, a right-aligned primary "Promote" button (padding 8px, white text on `#1862d8`);
  - a divider (1px, 50% opacity) at the bottom.
- **Artefacts and inconsistencies:**
  - 44 rows vs a count of 38 (duplicated demo data).
  - Each avatar carries a red 6px badge dot (top right).
  - Some names are links, others plain spans inside a link wrapper.
  - The fixed 285px name width leaves no room for long names.

---

## 3. Current vs Target

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS tab bar, `col-3`/`col-9` | `v2/page.html` via the generic dashboard base (D1), left menu at XL |
| Menu | Tabs + "More", counts in labels | One "Sysadmin" group of `c-nav-item size='s'`, no counts (D2, D3) |
| Breadcrumb | None | Home / Sysadmin / All Sysadmins (D11) |
| Header | "Sysadmin Dashboard" `<h2>` + "Current Sysadmins" `<h2>` | `<h1>` "All Sysadmins" + count + subtitle (D11) |
| Row | Gravatar + display-name link in a table | `c-avatar` initials + name link in a two-column list (D4–D6, D12) |
| Remove | Red icon-only button, one click, on every row | "Remove" text button, one click, not on the site user or your own row (D7, D8) |
| Promote | `<h2>` + v1 autocomplete input + button | Label + searchable user picker + primary button (D9, D10) |
| "Administer CKAN" box | Left column | Dropped (D12) |
| Flash | v1 alert | `c-alert` via the `v2/page.html` `flash` block |
| `<title>` | Administration | All Sysadmins \| Sysadmin (D11) |

---

## 4. Component & System Mapping

| Need | Mapping |
|---|---|
| Shell + layout | NEW `v2/dashboard-base.html` holding the shell that `v2/user-dashboard-base.html` has today (`hdx-v2-search-*` row/sidebar/content, sticky 25% sidebar, breadcrumb, nav markup); the user and sysadmin bases extend it (D1) |
| Menu items | Reuse `c-nav-item` `size='s'`, `status='active'` (existing base markup) |
| Menu data | NEW helper `h.hdx_get_sysadmin_nav_sections()`, also feeding the header user menu (D2, D3) |
| Row data | Reuse `h.hdx_get_user_info(name)` per row (D4) |
| Breadcrumb | Reuse `c-breadcrumb` via the base's `breadcrumb_items` (Home / section → its first item / `page_label`) |
| Header | Reuse `v2/list-header.html` — the dashboard header "with a count" (D11) |
| Rows + grid | NEW `c-user-item` in a `c-user-item-grid` (D6, D14) |
| Avatar | Reuse `c-avatar` `size='xs'` (24px, 12px initials, brand-15 background: an exact match) inside `c-user-item` (D12, D14, D16) |
| Initials | NEW helper `h.hdx_initials()`, shared by every v2 avatar (D17) |
| Name link | Reuse `c-text-link` `style='secondary'`, `size='s'` inside `c-user-item` (D12, D14) |
| Remove | Reuse `c-text-button` `style='primary'`, `size='s'`, `tag='button'`, `button_type='submit'`, `icon_src='v2/icons/user-close.svg'` (12px, 14px icon, 2px gap: an exact match) in a per-row form (D7) |
| Promote field | Extend `c-select` `searchable` (Select2, `components/select.js`) with an AJAX source (D9) |
| Promote button | Reuse `c-button` `style='primary'`, `button_type='submit'` |
| Flash | `v2/page.html` renders `c-alert`; no work |
| Promote block | Page LESS `pages/sysadmin.less` (D10, D15) |
| Not reused | `c-member-list-card`: card chrome, 32px avatar, "name \| username" and meta lines — a modifier would override nearly every property. `c-page-header`: hero layout |

---

## 5. Functional & Preservation Rules

- **No backend change** to core: the `admin.index` view, its 403 gate, the `user.sysadmin` endpoint,
  its field names (`username`, `status`), CSRF and flash texts stay as they are.
- **2FA:** the `/ckan-admin/` redirect keeps working (same rule).
- **v1 shell:** `admin/base.html` and every page extending it are unchanged.
- **Header menu:** section id `sysadmin` and its DOM ids stay; the offcanvas tracking attributes stay.
- **Analytics:** no new tracking. Only the generic page view's `pageTitle` value changes (D11).
- **v1 assets:** the page loads no v1 bundles (`admin-styles`, the v1 `autocomplete` module).

---

## 6. Responsive Behaviour (inferred; no MD/SM exports)

- **XL (≥ 80rem):** sticky 25% sidebar with the menu; the content column is about 848–878px wide,
  so two columns of about 412px hold Figma's 285px name. Header row: title + count, subtitle below.
- **MD (48–80rem):** no menu (`--xl-only`); navigation via the header user menu / offcanvas. Content
  is 672–1183px wide: two columns. The header follows list-header's stacking.
- **SM (< 48rem):** one column. The promote block spans the full width (D10).
- Long names: single-line ellipsis; the full name stays in the link text.

---

## 7. Accessibility

- One `<nav>` landmark with a sysadmin `aria-label` (D1); each group label is an `<h2>` with an `id`,
  its `<ul>` uses `aria-labelledby`; the active item has `aria-current="page"` (existing markup).
- One `<h1>` (list-header `title_tag='h1'`).
- The rows are a `<ul class="c-user-item-grid">` of `<li>` (D14). The avatar is hidden from
  assistive tech next to the visible name (D16).
- Remove is a submit `<button>` with `aria-label` "Remove {display_name}", so repeated "Remove" labels
  are distinguishable (D7).
- The promote field has a visible `<label for>`; `select.js` copies the label onto the Select2
  selection and search field (`labelIds()`).
- Focus rings (`.hdx-focus-ring()`) and reduced-motion guards come from the reused components.

---

## 8. Risks & Edge Cases

| Case | Handling |
|---|---|
| Removing yourself | No Remove on your own row (D8) |
| Removing the last sysadmin | Not possible from the page: the viewer is always a sysadmin and cannot remove themselves (D8) |
| Site user (`default`) | Listed, without Remove (D8) |
| Target with a bad / duplicate email or fullname | `flash_error` from HDX's `user_update` schema, unchanged |
| Pending/shadow sysadmin | Not listed and not counted (D11) |
| Promoting an existing sysadmin | Success flash, no change (unchanged) |
| Unknown username | "User not found" flash (unchanged) |
| Autocomplete suggests pending users / existing sysadmins | Unchanged endpoint behaviour (D9) |
| JavaScript off | Select2 does not initialise; the picker has no options, so nothing can be promoted (D9) |
| Long names | Ellipsis (D6) |

---

## 9. Options Considered — Shell

Figma's sysadmin shell is the user-dashboard shell with a different menu: same sidebar, nav item,
label, breadcrumb and header styles. The base's breadcrumb branch already renders
Home / {section} / {page_label} from whichever section holds `user_nav_active`.

| Option | Change | Pros | Cons |
|---|---|---|---|
| **A** Generic `v2/dashboard-base.html`; the user and sysadmin bases both extend it | 2 new files, user base rewritten | Neutral naming | Extra layer, largest diff, every user dashboard/settings page re-tested |
| **B** New `v2/sysadmin-base.html` extending `v2/user-dashboard-base.html`. The base takes an optional `nav_sections` (else it calls the user helper with `user_dict.name`) and a nav `aria-label` variable; the sysadmin base sets both and overrides `subtitle` | 1 new file, a few lines in the base | One shell to maintain; breadcrumb, layout and styles reused as they are; user pages render unchanged | Sysadmin pages sit on a "user-dashboard" base and reuse `user_nav_active` / `hdx-v2-user-dashboard-*` names |
| **C** Standalone `v2/sysadmin-base.html` copying the shell | 1 new file | No change to the user base | Copies the layout variables, nav markup and breadcrumb (a fork) |

**Chosen:** A (D1).

---

## 10. Decisions Taken

| # | Decision |
|---|---|
| D1 Shell | **Generic dashboard base** `THEME/templates/v2/dashboard-base.html`, extending `v2/page.html`, holds the shared shell. `v2/user-dashboard-base.html` and a new `v2/sysadmin-base.html` both extend it. The dashboard base owns the layout vars, the `v2-search-page-styles` and `v2-dashboard-page-styles` bundles, the left menu (built from `nav_sections`, `nav_active` and `nav_aria_label`: "User dashboard" / "Sysadmin dashboard") and the breadcrumb Home / {section of `nav_active` → its first item} / {`page_label`}. The user base computes its sections with `h.hdx_get_user_dashboard_nav_sections(user_dict.name)`, keeps its `subtitle`, `user_profile_header` and `v2-user-dashboard-page-styles`, and overrides `breadcrumb_items` only for its other-user branch (else `super()`). The sysadmin base sets its sections, `aria-label` and `subtitle`. Children set `nav_active` (the user children's `user_nav_active` is renamed). The menu classes are `hdx-v2-dashboard-nav*`, in a new `pages/dashboard.less`; `user-dashboard.less` keeps the header, empty state, divider and form rules. |
| D2 Menu | New helper `h.hdx_get_sysadmin_nav_sections()` (registered in `plugin.py`) returns `[{id: 'sysadmin', label: _('Sysadmin'), items: [{id, label, href}]}]`. It feeds the sysadmin base and replaces the inline Sysadmin Dashboard list in `hdx_get_user_menu_sections()` (section id and DOM ids unchanged), so both menus stay identical. Items (Figma labels): All Sysadmins (`all_sysadmins`, `admin.index`), All Users (`all_users`, `user.index`), Homepage Highlights (`homepage_highlights`, `hdx_carousel.show`), HDX Connect Dashboard (`hdx_connect_dashboard`, `requestdata_ckanadmin.requests_data`), Custom Pages (`custom_pages`, `hdx_custom_pages.index`), Products Menu (`products_menu`, `hdx_quick_links.show`), Package Links (`package_links`, `hdx_package_links.show`). Email and Config leave both menus; their pages stay reachable by URL and from the v1 "More" tab. The group label "Sysadmin" is also the middle breadcrumb and the header menu section label. |
| D3 Gating | Per item (086 D1): sysadmins get every item, other logged-in users the items whose page access check passes, and `[]` when none passes. |
| D4 Row data | Per row, `h.hdx_get_user_info(name)` (existing helper; about four queries per row against v1's three for `h.linked_user`) supplies `display_name` and `name` for the initials, the link text, the Remove accessible name and the profile URL (`user.read`). No new helper; the core view is unchanged. |
| D5 Order | Database order, as v1 (`_get_sysadmins()` has no `ORDER BY`). |
| D6 Grid | CSS grid `repeat(2, minmax(0, 1fr))` from MD (filled row by row), one column at SM; `space-6` column gap, `space-2` row gap. In each row the name takes the free width with a single-line ellipsis, so Remove sits at the column's right end on every row. |
| D7 Remove | One click, as v1 and API token Revoke: each row's Remove is the submit `c-text-button` of its own POST form to `user.sysadmin` (`username`, `status=0`, CSRF), with `aria-label` "Remove {display_name}". No confirmation drawer. |
| D8 Guards | No Remove on the site user's row (`name == g.site_id`) or on the viewer's own row (`name == c.user`). The endpoint is unchanged. |
| D9 Promote picker | `c-select` `searchable`, `name='username'`, placeholder "Username", with the source URL passed as `data-source` through the existing `select_attrs` (no new param). `components/select.js` gains an opt-in Select2 `ajax` branch when that attribute is present (300 ms request delay, minimum one character, option value = `name`, text = "fullname (name)", or `name` alone without a fullname). Source: core `/api/2/util/user/autocomplete?ignore_self=true` (v1's source; HDX's endpoint has no limit without `org`, §1.6). The page loads `v2-select2-styles` and `v2-select2-scripts`. Without JavaScript nothing is selectable. |
| D10 Promote block | A POST form to `user.sysadmin` (`status=1`, CSRF), `space-12` below the list, pushed right (`margin-left: auto`); width 100% at SM, 80% at MD, 50% at XL. The label "Promote user to sysadmin" (no colon) is the picker's `<label for>`; below the field, the primary `c-button` "Promote" is right-aligned. Figma's trailing divider is dropped. The picker is not `required` (as v1): an empty Promote gets core's "User not found" flash. |
| D11 Header, title, breadcrumb | Header: `v2/list-header.html` with `list_title=page_label`, `count=sysadmins \| length`, `list_subtitle=_('View and manage who has sysadmin-level access')`, `title_tag='h1'`, `title_size='dashboard'`, `show_controls=False`, `show_filters=False`. `<title>`: "All Sysadmins \| Sysadmin" (`{page_label} \| {group label}` with `g.template_title_delimiter`, built by the sysadmin base); the Mixpanel `pageTitle` change is accepted. Breadcrumb: Home / Sysadmin / All Sysadmins (`page_label`). |
| D12 Row visuals | Name: `c-text-link` `style='secondary'`, `size='s'` (as the request card's "Maintained by" link). Avatar: `c-avatar` `size='xs'`, initials only, no badge. Dropped: the badge dot, Gravatars, core's "Administer CKAN" box, the tab counts and the "Current Sysadmins" heading. |
| D13 Tests | No new tests. |
| D14 User row component | NEW `c-user-item` (`THEME/templates/v2/components/user-item.html` + `components/user-item.less`, listed in `v2-components-styles`). Params: `name` (link text; also the source of the avatar initials, D17), `href`, optional `meta` (text after the name, e.g. " - email"; unused on this page), `extra_classes`, and an optional `caller()` actions block (the Remove form here). It renders the `c-avatar` (D12), the `c-text-link` name with the ellipsis (D6) and the actions. The list wrapper `<ul class="c-user-item-grid">` carries the D6 grid. A components-demo entry shows rows with and without an action and a long name. |
| D15 Page LESS | NEW `pages/sysadmin.less` (compiles to `fanstatic/v2/pages/sysadmin.css`) and a `v2-sysadmin-page-styles` bundle loaded by `v2/sysadmin-base.html`. It holds the promote block (D10); later sysadmin pages add their rules there. |
| D16 Avatar a11y | Without `aria_label`, `c-avatar` renders `aria-hidden="true"` instead of `role="img"` (base default, no new param); `c-user-item` passes no label. The unlabelled header/offcanvas and sign-in avatars follow, with no visible change; `login.js` no longer sets `aria-label` on the returning-user avatar. |
| D17 Initials | NEW `h.hdx_initials(name)` (`helpers.py`, registered in `plugin.py`): the uppercased first letters of the first two words that start with a letter or digit ("HDX - Tag Bot" → "HT"); with no such word, the first non-space character; empty or `None` → `''`; it never raises. Every server-rendered v2 avatar takes its initials from it; `fanstatic/v2/pages/login.js` applies the same rule in JS to the returning-user avatar. |

---

## 11. Files Affected

| File | Change |
|---|---|
| `THEME/templates/admin/index.html` | NEW: overrides core's template; extends the sysadmin base; header, list with per-row Remove forms, promote form |
| `THEME/templates/v2/dashboard-base.html` | NEW: shared shell (D1) |
| `THEME/templates/v2/sysadmin-base.html` | NEW: extends the dashboard base; sysadmin menu, `subtitle`, nav label (D1) |
| `THEME/templates/v2/user-dashboard-base.html` | Extends the dashboard base; keeps only the user-specific parts (D1) |
| User dashboard/settings child templates (`THEME/templates/user/*.html`, `requestdata/my_requested_data.html`) | `user_nav_active` → `nav_active` (D1) |
| `THEME/hdx-styles/src/common/less/v2/pages/dashboard.less`, `pages/user-dashboard.less`, `THEME/fanstatic/webassets.yml` | NEW `hdx-v2-dashboard-nav*` rules and `v2-dashboard-page-styles` bundle; menu rules leave `user-dashboard.less` (D1) |
| `requirements/072`–`079` and `083` docs, `ckanext-hdx_theme/llm_docs/redesign/CONVENTIONS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | `user_nav_active` → `nav_active`; base description (D1) |
| `THEME/helpers/helpers.py`, `THEME/plugin.py` | `hdx_get_sysadmin_nav_sections()`, reused by `hdx_get_user_menu_sections()` (D2, D3); `hdx_initials()` (D17) |
| `THEME/templates/v2/components/avatar.html` | Unlabelled → `aria-hidden`; header comment (D16) |
| `THEME/templates/v2/header.html`, `THEME/templates/organization/members.html`, `THEME/templates/v2/hdx-connect-request.html`, `THEME/templates/v2/user-dashboard-base.html`, `THEME/fanstatic/v2/pages/login.js` | Initials from `h.hdx_initials()`; `login.js` mirrors the rule and drops its `aria-label` (D16, D17) |
| `THEME/fanstatic/v2/components/select.js`, `THEME/templates/v2/components/select.html` | AJAX branch and header comment (D9) |
| `THEME/templates/v2/components/user-item.html`, `THEME/hdx-styles/src/common/less/v2/components/user-item.less`, `THEME/fanstatic/webassets.yml` | NEW `c-user-item` + `c-user-item-grid`; added to `v2-components-styles` (D14) |
| `THEME/templates/v2/components.html` | `c-user-item` demo (D14) |
| `THEME/hdx-styles/src/common/less/v2/pages/sysadmin.less`, `THEME/fanstatic/webassets.yml` | NEW promote block rules; `v2-sysadmin-page-styles` bundle (D15) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/018-navigation-dropdown.md`, `072-user-dashboard-my-organisations-v2.md` (D6) | Header menu sysadmin section: source, label and items (D2) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/019-navbar-open.md`, `073-user-dashboard-my-datasets-v2.md` (D27), `074-user-dashboard-hdx-connect-requests-v2.md` | Avatar initials via `h.hdx_initials()` (D17) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated page entry; `c-user-item` component line; page bundles |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 084 status |
