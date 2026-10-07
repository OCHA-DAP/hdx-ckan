# 072 — User Dashboard: My Organisations (v2 Migration)

**Scope:** `/dashboard/organizations` (core `dashboard.organizations` view), plus a shared v2 shell
and left menu for the user dashboard and user settings pages, built now and adopted only by this page.
The v2 header user menu is aligned to the same menu (D6).

**Excluded:** Migrating the sibling dashboard/settings pages (Newsfeed, My Activity Stream,
HDX Connect Requests, User Permission, API Tokens, Notifications, Profile and Password). They stay v1
with their tab bars. My Datasets is task 073. Also excluded: pagination (D8), follower counts (D11), pending join requests, and
any backend/view change.

**Figma sources:** `xl-user-dashboard-my-organisation.html` (XL only; there are no MD/SM exports)
in `ckanext-hdx_theme/llm_docs/redesign/figma_exports/`.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`.

---

## Context

The page is still CKAN core's view rendering the v1 chain `user/dashboard_organizations.html` →
`user/dashboard.html` (BS5 horizontal tab bar) → core `user/edit_base.html` → v1 `page.html`. Figma
moves it onto the v2 shell with a left menu that repeats across every dashboard and settings page.
The menu is XL only; there is no menu on MD/SM. Nothing in the dashboard/settings area is v2 yet:
`070-v2-full-audit.md` deferred it to the next cycle.

Decisions confirmed with the user are listed in §8.

---

## 1. Audit Summary

### 1.1 Route and data
- Route: core `organizations()` in `ckan/views/dashboard.py`. No HDX blueprint defines `/organizations`;
  `hdx_user_dashboard` (`ckanext-hdx_users/.../views/dashboard.py`) only adds `/datasets`. Anonymous
  users are redirected to login (`before_request`).
- The view passes `user_dict`, `is_myself`, `is_sysadmin` and `about_formatted`, but no org list,
  and reads no `request.args`.
- The template fetches orgs itself via `h.hdx_organizations_available_with_roles()`
  (`THEME/helpers/helpers.py`):
  - Calls `organizations_available('read', include_dataset_count=True)`. Sysadmins get **every active
    org**.
  - Sets `org.role` to an untranslated `sysadmin` / `admin` / `editor` / `member`.
  - Sorts by `display_name`.
  - Calls `org_add_last_updated_field`, which sets `dataset_last_updated` from one collapsed
    `package_search` and falls back to `created`.
- There is no pagination, sort, limit or search.

### 1.2 Rendering (v1)
- Each row is `organization/snippets/organization_item.html`, wrapped by `organization_list.html`:
  - title link (`?sort=metadata_modified desc`)
  - "Last updated on – {render_datetime}"
  - an 80-char `markdown_extract`, or "This organization has no description"
  - "Your role: {role}"
  - Datasets (link) – Members (link, `h.get_group_members`) – Followers (`h.get_group_followers`)
- **Empty state** (`dashboard_organizations.html`, the no-orgs branch): "Thank you for becoming a registered user on
  HDX." plus 3 paragraphs and a "Request to join an org" button (`hdx_org_join.org_join`). When orgs
  exist, the same button floats top-right instead.
- **Assets:**
  - `popup-scripts` is redundant: `widget/contribute/details.html`, which `v2/page.html` renders for
    logged-in users, already loads it.
  - `onboarding-bulk-user-scripts` is not loaded by any v2 page.
- **Analytics:** nothing page-specific. The generic Mixpanel page view (`pageTitle` in `base.html`) uses the
  `subtitle` block: "Manage | {display_name} | Users", from core `edit_base.html`.

### 1.3 Menus today
- **Dashboard tabs:** `user/dashboard.html`.
  - Items: Newsfeed, My Datasets, My Organisations, My Locations, HDX Connect Requests.
  - Plus a sysadmin "More" dropdown. Its Carousel and COD links are `href="#"`; HDX Connect Dashboard
    and Custom/Event Page duplicate the v2 header's Sysadmin Dashboard menu.
- **Settings tabs:** `user/read_base.html`.
  - Items: Datasets, Activity Stream, User Permission (sysadmin), API Tokens, Notifications, Profile
    and Password.
- **v2 header user menu:** `h.hdx_get_user_menu_sections()` (`helpers.py`), used by
  `v2/navbar-user-menu.html` and `v2/header.html` (mobile offcanvas).
  - Sections: Sysadmin Dashboard, User Dashboard and User Settings.
  - Items carry no `active` flag.

### 1.4 Data that does not exist
No user→org join date is stored. The `member` table (`member_table` in `ckan/model/group.py`) has no `created`
column, and ytp-request deletes its `MemberExtra(key='created')` when a request is approved. Across
HDX, "Member since" means the **org's** `created` date (`c-org-list-card`, `v2/org-hero.html`).

### 1.5 Sibling endpoints (menu targets)
| Item | Endpoint |
|---|---|
| Newsfeed | `activity.dashboard` |
| My Activity Stream | `activity.user_activity` (`id=c.user`) |
| My Datasets | `hdx_user_dashboard.datasets` |
| My Organisations | `dashboard.organizations` |
| HDX Connect Requests | `requestdata.my_requested_data` (`id=c.user`) |
| User Permission | `hdx_user_permission.read` (`id=c.user`) |
| API Tokens | `user.api_tokens` (`id=c.user`) |
| Notifications settings | `hdx_user.notifications` (`id=c.user`) |
| Profile and Password | `hdx_user.edit` (`id=c.user`) |

---

## 2. Figma Design Analysis (XL)

- **Breadcrumb:** Home / Activity and Content / My Organisations.
- **Sidebar:**
  - A white column, flush to the frame's left edge (14.063rem wide, padding 40/48/0).
  - Two groups, 28px apart. Each has a label (Roboto 12px regular, `#101212`), then an 8px gap, then
    48px items (14px medium, `#3f4748`, padding 0 8px).
  - Active item: 4px `#1862d8` bottom border, `#101212` text. This is Figma's own `nav-item`
    component, the same one the navbar uses.
- **Header:**
  - "My Organisations" (Merriweather 24px bold).
  - 6px below it, the subtitle "Organisations you belong to and your role in each" (14px regular,
    `#2f3536`).
  - To the right, 32px away: "Request to join an org" (primary, 4px 8px padding, 12px text, 14px mail
    icon).
  - 24px from the header to the list.
- **Cards:** org list cards with a 16px gap. Each shows:
  - the name (18px semibold, 2-line clamp)
  - "Member since 31 October 2023" (12px, single-line ellipsis)
  - "Show more"
  - "4.8k Datasets • 12 Members • 304 Subscribers"
- **Pager:** 10 cards, pages 1…31.
- **Hidden (`display:none`):** title count "28", "Results per page" / "Sort by" dropdowns, a collapse
  chevron, an activity-item list.

---

## 3. Current vs Target

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, heading "User Dashboard" | `v2/page.html` via the shared base (D1), left menu at XL (D2–D4) |
| Breadcrumb | Home / Dashboard | Home / Activity and Content → Newsfeed / My Organisations (D7) |
| Header | Floating BS button only | `<h1>` + subtitle + small primary button, always rendered (D9) |
| Row | `organization_item.html` | `c-org-list-card` with role + last-updated line (D10, D11) |
| Role | "Your role: admin" line | "Admin - Last updated on 31 October 2023" (D10) |
| Date | "Last updated on – {date}" | Same data, `hdx_format_date` format (D10) |
| Description | 80-char extract / placeholder | Full markdown behind "Show more"; nothing when empty (D11) |
| Counts | Datasets (link) – Members (link) – Followers | Datasets • Members, plain text (D11) |
| Pagination | None | None (D8) |
| Empty state | Copy + button, top button hidden | Header + button always; copy below, no second button (D12) |
| `<title>` | Manage \| {name} \| Users | My Organisations \| {name} \| Users (D13) |
| Sysadmin "More" | In tab bar | Dropped (D4) |

---

## 4. Component & System Mapping

| Need | Mapping |
|---|---|
| Shell + layout | NEW base template `v2/user-dashboard-base.html` (D1) using the generic `hdx-v2-content-columns__*` classes (D3) plus the Search page's `hdx-v2-search-*` row/sidebar/content classes (D14) |
| Menu items | **Extend** `c-nav-item` with `size='s'` (D2) |
| Menu data | NEW helper `hdx_get_user_dashboard_nav_sections()` (D5), also feeding the header user menu (D6) |
| Group labels, `<nav>`, lists | Base-template markup + page LESS (`hdx-v2-user-dashboard-nav__*`) |
| Breadcrumb | Reuse `c-breadcrumb` |
| Header | Page LESS `hdx-v2-user-dashboard-header`, not `c-page-header` (hero padding, 16px semibold subtitle, size-m CTA below the text) (D9) |
| Button | Reuse `c-button` (`style='primary'`, `size='s'`, `tag='a'`, `icon_src='v2/icons/mail.svg'`); an exact Figma match |
| Org rows | **Extend** `c-org-list-card` with `role`, `member_since`, `last_updated` (D10); list wrapper `c-org-list-card-list` |
| Empty state | Page LESS using `.hdx-list-header-empty()` |
| Pagination / sort / page size | Not used (D8, D9) |

---

## 5. Functional & Preservation Rules

- **No view or backend change.**
  - Keep the core route, its login gate, and the in-template `h.hdx_organizations_available_with_roles()`
    call. The helper is unchanged: same role computation, same alphabetical order.
  - `member_count` is still `h.get_group_members(org.id)` per card, as on the All Orgs page.
- **"Request to join an org":** keep the `hdx_org_join.org_join` link and its label.
- **URLs:** every existing endpoint and URL still resolves. `url_for('dashboard.organizations')`
  callers (`first_login.py` `_compute_url`, `contribute_flow.py` `new`, the header menu) are unaffected.
- **Analytics:** no new tracking. The generic Mixpanel page view keeps firing; only its `pageTitle`
  value changes (D13).
- **v1 assets:** the page loads no v1 bundles. It adds only `v2-search-page-styles` and `v2-user-dashboard-page-styles`. The
  card's `clamped-text.js` comes from `v2-components-scripts`.
- **v1 siblings:** all v1 sibling pages keep `user/dashboard.html` / `user/read_base.html` untouched.

---

## 6. Responsive & Accessibility

- **XL (≥ 80rem):**
  - Sidebar column on the left, sticky, with `border-right` and the Search padding (D14).
  - Content column holds the header row (text left, button right) and the card list.
- **MD/SM (< 80rem):**
  - No menu (`--xl-only`); navigation is via the header user menu / offcanvas.
  - The header stacks: title, subtitle, then the button (auto width, left-aligned), `space-4` apart (D15).
  - Content padding follows Search: 32px vertical at MD, 24px at SM, container gutters at the sides.
  - Cards keep their own rules; SM shows only the title and the role/date line.
- **Accessibility:**
  - One `<nav aria-label="{{ _('User dashboard') }}">` landmark.
  - Each group label is an `<h2>` with an `id`; its `<ul>` uses `aria-labelledby`.
  - The active item carries `aria-current="page"`.
  - `c-nav-item` keeps its colour-only hover, plus `.hdx-focus-ring()` on `:focus-visible` (base class).
  - Its existing `.hdx-motion()` guard covers reduced motion.
  - The page has one `<h1>` (the title).

---

## 7. Risks & Edge Cases

| Case | Handling |
|---|---|
| Sysadmin | Every active org, unpaged, with one `member_list` call per card. Accepted with D8 (parity with v1, which also made a follower query). |
| No orgs | Header + button, then v1's copy verbatim (D12). |
| Missing / unparseable date | The date part renders `_('Unknown')`, the card's existing fallback (D10). |
| Unknown role value | Falls back to the raw value; no role part when it is empty. |
| Long org name | 2-line clamp (existing card). |
| No description | No "Show more" (existing card). |
| All Orgs page regression | Must still render "Member since {org.created}" by passing `member_since=org.created` (D10). |
| Menu links to v1 pages | Expected until the siblings migrate; each keeps its v1 tab bar. |
| Settings pages viewed for another user (sysadmin) | Not in scope. The menu always targets `c.user`; revisit when settings pages adopt the base. |
| Header-menu change | Affects every v2 page: My Locations and Datasets (profile) leave the header menu (D4, D6). |

---

## 8. Decisions Taken

| # | Decision |
|---|---|
| D1 Shell | **Shared base template** `THEME/templates/v2/user-dashboard-base.html`, extending `v2/page.html`. It owns all four layout vars, the sidebar (`secondary_content`), the breadcrumb, the `subtitle` block and the page styles bundle. Children set `user_nav_active` (an item id) and `page_label` and fill the content. Only My Organisations adopts it now. |
| D2 Nav items | **`c-nav-item` + new `size` param**: `'m'` (default, 4rem) / `'s'` (3rem), emitted as `c-nav-item--size-*` like `c-button`. The base becomes `display:flex` + `justify-content:flex-start` (no visible change in horizontal rows), so items fill their `<li>` without a modifier. `status='active'` now also outputs `aria-current="page"` (the navbar never passes `active`). Group labels, `<nav>` and `<ul>` live in the base template. |
| D3 Width | Generic `hdx-v2-content-columns__sidebar` (25% at XL) + `--xl-only` + `--sticky`, not Figma's fixed 14rem. |
| D4 Items | **Activity and Content:** Newsfeed, My Activity Stream, My Datasets, My Organisations, HDX Connect Requests. **Account and Settings:** User Permission (sysadmin only, as today, first), API Tokens, Notifications settings, Profile and Password. My Locations, Datasets (profile) and the sysadmin "More" dropdown are dropped. |
| D5 Data | New helper `h.hdx_get_user_dashboard_nav_sections()` returns `[{id, label, items:[{id, label, href}]}]` and is registered in `plugin.py`. Section ids are `dashboard` and `settings`. Item ids: `newsfeed`, `my_activity_stream`, `my_datasets`, `my_organisations`, `hdx_connect_requests`, `user_permission`, `api_tokens`, `notifications_settings`, `profile_and_password`. It returns `[]` when there is no `c.userobj`. |
| D6 Header menu | `hdx_get_user_menu_sections()` keeps its Sysadmin Dashboard section and builds its dashboard/settings sections from the new helper, so both menus stay identical, labels included ("Activity and Content", "Account and Settings", "Notifications settings"). Section ids are unchanged (DOM ids `desk-*` / `offcanvas-user-*` keep working). |
| D7 Breadcrumb | Home / Activity and Content (links to `activity.dashboard`, the group's first item) / My Organisations. |
| D8 Pagination | None (parity). Figma's pager is dropped; no view is added. |
| D9 Header | `<h1>` uses `.hdx-dashboard-title()` (`.hdx-display-s()`, fixed 24px, as in Figma) in neutral-95. Subtitle uses `.hdx-dashboard-subtitle()` (`.hdx-body-s()`) in neutral-85, `space-13` below the title. The button sits `space-8` from the text; header to list is `space-6`. Figma's hidden count, "Results per page", "Sort by" and chevron are omitted. v1's untranslated `title` on the button is dropped. |
| D10 Card API | `c-org-list-card` gets optional `role` (a translated label), `member_since` and `last_updated` (raw dates). **Each part renders only when passed**, joined with `' - '`: "Admin - Last updated on 31 October 2023". Dates use `h.hdx_format_date`, with `_('Unknown')` for an empty or unparseable value. My Organisations passes `role` (mapping `sysadmin`/`admin`/`editor`/`member` → `_('Sysadmin')`/`_('Admin')`/`_('Editor')`/`_('Member')`) and `last_updated=org.dataset_last_updated`. All Orgs and the components demo pass `member_since=org.created`, so their output is unchanged. |
| D11 Card content | Subscribers/followers are omitted. The rest of the card's behaviour is accepted as-is: plain-text counts, title link without a sort param, description behind "Show more" and nothing when empty. Card visuals stay as 049 shipped them (no Figma width/ellipsis/alignment deltas). |
| D12 Empty state | The header and button always render. Below them, v1's four lines of copy appear verbatim as four `<p>` (no heading) with no second button, styled with `.hdx-list-header-empty()`. |
| D13 Title | `subtitle` = "My Organisations \| {display_name} \| Users", using `g.template_title_delimiter` and built by the base from `page_label`. The Mixpanel `pageTitle` change is accepted. |
| D14 Layout | Reuses the Search page's `hdx-v2-search-row` / `hdx-v2-search-sidebar` / `hdx-v2-search-content` (loads `v2-search-page-styles`, as the Org/Country/Crisis pages do). Sidebar at XL: `border-right: 1px solid var(--hdx-neutral-1)`, padding `space-5` / `space-10` / `space-20` / 0, grey canvas (no white panel). Content: `space-10` 0 `space-10` `space-10` at XL, `space-8` 0 at MD, `space-6` 0 at SM. Menu groups are `space-6` apart (there is no 28px token); label to list is `space-2`. Group label: `.hdx-body-xs()`, neutral-95. |
| D15 MD/SM | No menu. The header stacks at MD and SM: title, subtitle, then the button, `space-4` apart. |
| D16 Tests | No new tests. The `dashboard.organizations` row in `test_page_load.py` covers the page load. |

---

## 9. Files Affected

| File | Change |
|---|---|
| `THEME/templates/v2/user-dashboard-base.html` | NEW: shell (D1, D3, D7, D13, D14); layout via the `hdx-v2-search-*` classes |
| `THEME/templates/user/dashboard_organizations.html` | Full replacement extending the base; header, card list, empty state (D8–D12); v1 assets removed |
| `THEME/templates/v2/components/nav-item.html` | `size` param, `aria-current` on active, header comment (D2) |
| `THEME/hdx-styles/src/common/less/v2/components/nav-item.less` | `&--size-m`/`&--size-s`, base `display:flex` + `flex-start`, `:focus-visible` ring (D2) |
| `THEME/templates/v2/components/org-list-card.html` | `role`, `member_since`, `last_updated` params, header comment (D10) |
| `THEME/templates/organization/index.html` | Pass `member_since=org.created` (D10) |
| `THEME/templates/v2/components.html` | Org-card demos pass `member_since`; add a dashboard-variant card and a size-s nav-item demo |
| `THEME/helpers/helpers.py` | New `hdx_get_user_dashboard_nav_sections()`; `hdx_get_user_menu_sections()` reuses it (D5, D6) |
| `THEME/plugin.py` | Register the new helper |
| `THEME/hdx-styles/src/common/less/v2/pages/user-dashboard.less` | NEW: nav groups, header, empty state (compiles to `fanstatic/v2/pages/user-dashboard.css`) |
| `THEME/fanstatic/webassets.yml` | NEW `v2-user-dashboard-page-styles` bundle |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/018-navigation-dropdown.md` | Helper description (implementation notes): dashboard/settings sections come from the new helper |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Migrated-pages table, org list card line and page-bundle list |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Migrated-pages sentence and a Key pages entry |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/049-organizations-list-v2.md` | Card params table and loop example pass `member_since` |
| `.claude/skills/hdx-v2-styles/references/components.md` | `nav-item` `size` param; `org-list-card` params |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 072 → `implemented` when done |
