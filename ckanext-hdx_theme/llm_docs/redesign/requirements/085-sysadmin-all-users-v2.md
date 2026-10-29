# 085 — Sysadmin Dashboard: All Users (v2 Migration)

**Scope:** `/user/` (core `user.index`), rendered by HDX's `user/list.html` override, moved onto the v2
sysadmin shell built by 084. Also the "All Users" label in the user dashboard base's crumb and `<title>` (D13).

**Excluded:** The core view, its parameters, defaults and auth. The other sysadmin pages, which stay on v1
`admin/base.html`. Sort and page-size controls (D3).

**Figma sources:** `xl-sysadmin-all-users.html` (XL only; there are no MD/SM exports) in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`.

---

## Context

The page is HDX's v1 `THEME/templates/user/list.html` inside v1 `admin/base.html` (BS tab bar,
`col-3`/`col-9`, `admin-styles` bundle). Figma moves it onto the sysadmin shell from 084
(`v2/sysadmin-base.html` on `v2/dashboard-base.html`): left menu at XL, a dashboard header with a count,
a search field, a two-column list of users with their email, and pagination. 084 already added the
`all_users` menu item and the `c-user-item` `meta` param this page needs.

Decisions confirmed with the user are listed in §10.

---

## 1. Audit Summary

### 1.1 Route, access and parameters
- Route: core `index()` in `ckan/views/user.py`, rule `/` on the `user` blueprint (`/user/`,
  `strict_slashes=False`). HDX's `hdx_user` blueprint (`url_prefix='/user'`) has no `/` rule.
- Access: auth `user_list` returns `restrict_anon` when `ckan.auth.public_user_details` is false (prod),
  so **any logged-in user** can open the page; otherwise 403. With the setting true (the test ini default),
  anonymous visitors get it too. The "Users" breadcrumb on another user's dashboard pages
  (`v2/user-dashboard-base.html`) and on v1 profile pages links here.
- 2FA: the rule `/user/` is in `protected_urls` of `THEME/plugin.py` `_before_request`.
- Parameters:
  - `q`: passed to `user_list`.
  - `order_by`: default `name` (username); any `User` column, ascending only; an unknown column falls back
    to display-name order; `edits` raises an uncaught `ValidationError` (500).
  - `limit`: default `ckan.user_list_limit` (20; not set in the repo). Parsed with a bare `int()`, so
    `abc`, `0` or a negative value is a 500; there is no upper bound.
  - `page`: `h.get_page_number` (400 on a non-positive or non-integer value).
- Template variables: `page` (a presliced CKAN `Page`), `q`, `order_by`.

### 1.2 Data
- `user_list` with `return_query` excludes the site user and deleted users (pending users stay) and
  searches `q` with `ilike` on name and fullname, plus email when the viewer is a sysadmin.
- The view dictizes only the current page with `user_dictize`: `name`, `display_name`, `created`, `state`
  and more. `email` is in the dict for a sysadmin viewer **and for the viewer's own row**.
- `page.item_count` is the matching total; with no `q` it equals the v1 tab's `h.hdx_user_count()`.

### 1.3 Rendering (v1)
- Shell (`admin/base.html`): "Sysadmin Dashboard" `<h2>`, the sysadmin tab bar ("All users [N]" with
  `h.hdx_user_count()`; tabs only for sysadmins or permission holders), `col-3` / `col-9` columns.
- Heading: "Users" `<h1>`; breadcrumb "Users"; `<title>` block "All Users".
- Rows: a `<ul class="user-list">` of `h.linked_user(user.name, maxlength=20)` (a Gravatar plus the display
  name cut to 20 characters + "...", linked to `user.read`), followed by `- {email}` when
  `g.userobj.sysadmin`.
- Pagination: core `page.pager(q=q, order_by=order_by)`; `limit` is not carried.
- Left column: core `user/snippets/user_search.html`: a GET form submitting only `q` ("Search Users"
  label, "Search" placeholder) and an "All Users" link.
- No sort or page-size controls, no empty state.

### 1.4 Analytics and tests
- **Analytics:** nothing page-specific. The generic Mixpanel page view takes `pageTitle` from the
  `subtitle` block ("All Users").
- **Tests:** `test_email_access.py::test_email_access_by_page` (`ckanext-hdx_users`) requests `/user` as a
  sysadmin, a normal user and a guest. It asserts the sysadmin sees emails and the v1 tab text
  `'All Sysadmins ['`, and that the normal user does not see their own email.

---

## 2. Figma Design Analysis (XL)

- **Shell:** as 084; the "All Users" menu item is active. Breadcrumb: Home / Sysadmin / All Users.
- **Header:**
  - "All Users" (Merriweather 24px bold) + count "10008" (Roboto 16px, `#3f4748`, 8px gap).
  - On the same row, right: "Results per page [10]" and "Sort by [Last added]" dropdowns (visible).
  - 6px below: "Search and manage all registered user accounts" (14px, `#2f3536`).
- **Search:** 12px below the header, a full-width field "Search for users" (14px placeholder `#3f4748`,
  1px border, 2px radius, padding 8px 12px, right icon). 24px from the search to the list.
- **List:**
  - Two columns of 28.25rem, 32px apart; rows 8px apart, filled column by column.
  - Row: a 24px round avatar (initials 12px teal on `#bee0d6`), 6px gap, then one line of 14px
    `#2f3536` text: the display name as an underlined link to `/user/<name>`, then "- {email}".
  - No row actions.
- **Pagination:** 32px below the list, centred: prev chevron, 1 (current, bold), 2, 3, …, 31, next chevron.
- **Artefacts and inconsistencies:**
  - 36 rows against "Results per page 10"; 31 pages against a count of 10008.
  - Some rows split the name over a plain "A" span and a link ("A|lexandru Artimon") and use "..." instead
    of "-" before the email.
  - The rows are in username order (v1's default), although "Sort by" says "Last added".
  - "011dd0a94025aed63672..." is v1's 20-character cut.
  - Each avatar carries a red 6px badge dot (as in 084).

---

## 3. Current vs Target

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS tab bar, `col-3`/`col-9` | `v2/sysadmin-base.html`, menu at XL (D1, D2) |
| Breadcrumb | "Users" | Home / Sysadmin / All Users; non-sysadmins Home / All Users (D2) |
| Header | "Sysadmin Dashboard" `<h2>` + "Users" `<h1>` | `<h1>` "All Users" + count + subtitle (D4) |
| Sort / page size | None | None (D3) |
| Search | Left-column box | Full-width search field below the header (D5) |
| Row | Gravatar + name cut to 20 chars + "- email" | `c-user-item`: initials avatar + full name (ellipsis) + "- email" meta (D6) |
| Layout | Bulleted list | `c-user-item-grid`: one column at SM, two from MD (D6) |
| Pagination | Core `page.pager` | `c-pagination` (D7) |
| Empty result | Empty list | "No users found." (D8) |
| Flash | v1 alert | `c-alert` via the `v2/page.html` `flash` block |
| `<title>` | All Users | All Users \| Sysadmin; non-sysadmins All Users (D10) |

---

## 4. Component & System Mapping

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `<title>` | Reuse `v2/sysadmin-base.html` with `nav_active='all_users'`, `page_label` (D1) |
| Header | Reuse `v2/list-header.html` (D4) |
| Search | Reuse `c-search-input` (`v2/components/search-input.html`) in a form with the `hdx-v2-search-bar-row` class from `pages/search.less` (D5) |
| Rows + grid | Reuse `c-user-item` with `meta`, in `c-user-item-grid` (D6) |
| Avatar | `c-avatar` `size='xs'` inside `c-user-item`, initials from `h.hdx_initials` (an exact match) |
| Pagination | Reuse `c-pagination` in the `hdx-v2-pagination-row` wrapper from `pages/search.less` (D7) |
| Empty state | Reuse the user dashboard's empty state, moved to `pages/dashboard.less` as `.hdx-v2-dashboard-empty` (D8) |
| Flash | `v2/page.html` renders `c-alert`; no work |
| Not reused | `c-member-list-card` (card chrome, 32px avatar, meta lines). `c-table`: the design is a list of name links, not tabular data |

`pages/search.less` and `pages/dashboard.less` are already loaded by the dashboard base, so the
page adds no bundle and no JavaScript.

---

## 5. Functional & Preservation Rules

- **No backend change:** core `user.index`, `user_list`, their auth, parameters (`q`, `order_by`, `limit`,
  `page`) and defaults stay as they are.
- **Access:** unchanged (D2). The 2FA redirect keeps working (same rule).
- **Emails:** shown only to sysadmins, as v1 (D6).
- **Search:** submits only `q`, as v1; core's matching is unchanged (D5).
- **Pagination:** carries `q` and `order_by`, as v1's pager (D7).
- **v1 shell:** `admin/base.html` and the other pages extending it are unchanged.
- **Analytics:** no new tracking; only the generic page view's `pageTitle` value changes, here for sysadmins
  (D10) and on every user dashboard page (D13).
- **v1 assets:** the page loads no v1 bundles (`admin-styles`).

---

## 6. Responsive Behaviour (inferred; no MD/SM exports)

- **XL (≥ 80rem):** for sysadmins, the sticky 25% sidebar with the menu; the content column holds two list
  columns. Header row: title + count, subtitle below, search below that.
- **MD (48–80rem):** no menu (`--xl-only`); navigation via the header user menu / offcanvas. Two list
  columns.
- **SM (< 48rem):** one list column. The search field stays full width.
- **Non-sysadmins:** no sidebar at any width; the content spans the row.
- **Long names and emails:** one line; the name and the meta shrink together with an ellipsis; the full
  name stays in the link text.

---

## 7. Accessibility

- One `<h1>` (list-header `title_tag='h1'`).
- The search field has an accessible name ("Search for users", `aria-label`); its icon is a submit
  `<button>` (`icon_submit`); Enter submits without JavaScript.
- The rows are a `<ul class="c-user-item-grid">` of `<li>`. The avatar is hidden from assistive tech next
  to the visible name (`c-avatar` without `aria_label`).
- `c-pagination` is a `<nav aria-label="Pagination">`; the current page has `aria-current="page"`;
  disabled prev/next are not links.
- The sysadmin menu keeps 084's landmark and `aria-current` markup.
- Focus rings and reduced-motion guards come from the reused components.

---

## 8. Risks & Edge Cases

| Case | Handling |
|---|---|
| Non-sysadmin viewer | Same page without menu, subtitle or emails (D2, D4, D6) |
| Non-sysadmin's own row | No email: the gate is the viewer's sysadmin flag, not the email key (D6) |
| Anonymous viewer (`public_user_details` true) | As a non-sysadmin (D2) |
| Search with no match | "No users found." below the header and search (D8) |
| `?page=` past the last page | Core clamps to the last page with no rows: "No users found." and pagination (D8) |
| Hand-typed `limit` | Honoured on the first page, dropped by the pagination links, as v1 (D7) |
| Hand-typed bad `limit` or `order_by=edits` | 500 from core, unchanged (D3) |
| `?page=0` or a non-integer page | 400 from core, unchanged |
| Pending users | Listed, as v1 |
| Long names / emails | Ellipsis (D6) |
| JavaScript off | Search works (Enter or the submit icon); the × clear needs JavaScript |

---

## 9. Options Considered — Sort and Page Size

Figma shows "Sort by [Last added]" and "Results per page [10]". Core can only sort ascending, so
newest-first needs backend code.

| Option | Change | Pros | Cons |
|---|---|---|---|
| **A** HDX `index` view on `/user/` (built on core `user_list`): Last Added / Name Ascending / Name Descending, 10/25/50/100, unknown values fall back | New view + `url-nav.js` bundle | Matches Figma; bad `limit` no longer a 500 | New backend code and tests for a page that had no controls |
| **B** Core view, core sorts only: Name / Oldest first, 20/50/100 | Template + `url-nav.js` bundle | No backend change | No "Last added"; labels must explain username order; bad `limit` still a 500 |
| **C** No controls: search and pagination, as v1 | Template only | No backend change, no JavaScript, v1 behaviour kept | Figma's controls not built |

**Chosen:** C (D3).

---

## 10. Decisions Taken

| # | Decision |
|---|---|
| D1 Template | HDX `THEME/templates/user/list.html` is rewritten: it extends `v2/sysadmin-base.html`, sets `nav_active = 'all_users'` and `page_label = _('All Users')`, and fills `primary`. The core view is used as it is; there is no HDX view override. |
| D2 Access | Unchanged: every viewer core admits gets the page. For non-sysadmins `h.hdx_get_sysadmin_nav_sections()` holds only the items they may open (086 D1), never All Users, so no item is active, the breadcrumb is Home / All Users and the `<title>` is "All Users". The template's sysadmin check (`g.userobj and g.userobj.sysadmin`) treats an anonymous viewer as a non-sysadmin. |
| D3 Controls | No "Sort by" and no "Results per page" (`show_controls=False`); the page keeps v1's search and pagination. Core defaults stay (`name` order, 20 per page). A hand-typed `order_by` or `limit` is still honoured by core, and its 500 cases are accepted. |
| D4 Header | `v2/list-header.html` with `list_title=page_label`, `count=page.item_count` (the matches when `q` is set), `title_tag='h1'`, `title_size='dashboard'`, `show_controls=False`, `show_filters=False`. The count keeps list-header's `h.localised_number` format ("10,008"). `list_subtitle=_('Search and manage all registered user accounts')` for sysadmins only. |
| D5 Search | A GET form to `user.index` with `class="hdx-v2-search-bar-row"`, submitting only `q` (as v1). `search-input.html` with `size='m'`, `name='q'`, `value=q`, `icon_submit=True`, `state='filled' if q else 'enabled'`, `placeholder=_('Search for users')`, `input_attrs={'aria-label': _('Search for users')}`, `extra_classes='c-search-input--block'`. The shared spacing (list-header's 16px above, the row's 16px below) replaces Figma's 12px / 24px. The × clear (`input-field.js`) resubmits an active search. |
| D6 Rows | One `c-user-item` per `page.items` row, each in an `<li>` of `<ul class="c-user-item-grid">`: `name=user.display_name`, `href=h.url_for('user.read', id=user.name)`, and `meta='- ' ~ user.email` only for a sysadmin viewer with an email on the row. The grid keeps its 24px column gap (as All Sysadmins) and row-by-row fill. Names and emails use the component's CSS ellipsis; there is no 20-character cut, Gravatar, badge dot or action. |
| D7 Pagination | `c-pagination` `size='md'`, `current_page=page.page`, `total_pages=page.page_count`, `base_url=h.url_for('user.index', q=q, order_by=order_by) ~ '&page='` (v1's pager parameters; the view always sets `order_by`, so the URL always has a query string), inside `<div class="hdx-v2-pagination-row">` (centred, 32px above), rendered only when `page.page_count > 1` (as on the org list and dataviz gallery). |
| D8 Empty state | With no rows: `<div class="hdx-v2-dashboard-empty">` with a `__text` paragraph "No users found." in place of the grid. Pagination sits outside that branch (as on the org list and /archive), so a page past the last one can page back. The user dashboard's `.hdx-v2-user-dashboard-empty` moves from `pages/user-dashboard.less` to `pages/dashboard.less` as `.hdx-v2-dashboard-empty`, shared by both bases; the user pages switch to the new name. |
| D9 Dropped | The v1 tab bar and "Sysadmin Dashboard" heading, the "Users" heading, core's `user_search.html` box and its "All Users" link, Gravatars, the 20-character cut and Figma's badge dot. |
| D10 Analytics, `<title>` | No new tracking. The `<title>` and Mixpanel `pageTitle` become "All Users \| Sysadmin" for sysadmins (built by the sysadmin base) and stay "All Users" for others. |
| D11 Tests | `test_email_access.py` (`ckanext-hdx_users`) is extended. `test_email_access_by_page` swaps the `'All Sysadmins ['` assert for `'aria-label="Sysadmin dashboard"'` (the header user menu prints "All Sysadmins" on every page). New cases, with plain `in body` asserts: a sysadmin gets the "All Users" `<h1>`, the count, the subtitle and the "- email" meta; a normal user gets none of the menu, subtitle or email meta; `?q=doe&limit=1` lists only matches and its page-2 link carries `q=doe`; a search with no match shows "No users found."; `?limit=1&page=99` shows "No users found." and pagination. |
| D12 Assets | No new bundle and no JavaScript; the D8 rule moves to `pages/dashboard.less`. |
| D13 "All Users" label | `v2/user-dashboard-base.html` uses "All Users" for the crumb on another user's pages (Home / All Users / {name}) and for the `<title>` suffix on every user dashboard page ("{page} \| {name} \| All Users"). The Mixpanel `pageTitle` change on those pages is accepted. v1 `user/read_base.html` and `user/edit.html` keep "Users". |

---

## 11. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/list.html` | Rewritten on `v2/sysadmin-base.html`: header, search, user grid, pagination, empty state (D1–D8) |
| `THEME/templates/v2/user-dashboard-base.html` | "All Users" crumb label and `<title>` suffix (D13) |
| `THEME/hdx-styles/src/common/less/v2/pages/dashboard.less`, `pages/user-dashboard.less` | `.hdx-v2-user-dashboard-empty` moved and renamed `.hdx-v2-dashboard-empty` (D8) |
| `THEME/templates/user/read_organizations.html`, `activity_stream.html`, `api_tokens.html`, `notifications.html` | Empty-state class renamed (D8) |
| `THEME/hdx-styles/src/common/less/v2/components/user-item.less` | All Users export added to the header's Figma line |
| `ckanext-hdx_users/ckanext/hdx_users/tests/test_emails/test_email_access.py` | Assert swap and new cases (D11) |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md`, `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated page entry; the user dashboard crumb wording (D13); the dashboard bundle's empty state (D8) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/` 072–079 | The user dashboard crumb and `<title>` wording (D13) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/` 074, 075, 077, 078, 080 | The empty-state class name (D8) |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 085 status |
