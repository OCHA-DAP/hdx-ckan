# 075 — User Dashboard: My Activity Stream (v2 Migration)

**Scope:** `/user/activity/<id>` (core `activity.user_activity` view), moved into the 072 dashboard
shell and rendered through the existing v2 activity timeline (`v2/activity-stream.html` +
`c-activity-item`).

**Excluded:** the other v1 settings tabs. Also any change to
the `user_activity_list` action or its data model.

**Figma source:** `xl-user-setting-my-activity-stream.html` (XL only; there are no MD/SM exports)
in `ckanext-hdx_theme/llm_docs/redesign/figma_exports/`.

`THEME` = `ckanext-hdx_theme/ckanext/hdx_theme`. `ACTIVITY` = `ckanext/activity` (the CKAN core
activity plugin, enabled in every ini).

---

## 1. Audit Findings

### 1.1 Route and data
- **View:** core `user_activity()` in `ACTIVITY/views.py`, `/user/activity/<id>`. No HDX blueprint
  registers this rule.
  - It calls `check_access('user_show')`. With `ckan.auth.public_user_details = false`, anonymous
    users get 403 and **any logged-in user can open any user's stream**.
  - `_extra_template_variables()` (`ckan/views/user.py`) supplies `user_dict`, `is_myself`,
    `is_sysadmin` and `about_formatted`.
  - It calls `user_activity_list` with `before` / `after` (epoch timestamps from `request.args`)
    and `limit + 1`. `limit` = `ckan.activity_list_limit` (31; unset in prod, 15 in the test inis),
    capped by `ckan.activity_list_limit_max` (100).
  - It also passes `id` (the URL id), `activity_stream`, `newer_activities_url` and
    `older_activities_url`. `older_activities_url` is exact: it is `None` when the limit + 1 probe
    found nothing older. `newer_activities_url` is `None` on the first page.
- **Data:** activities **by** the user plus activities **about** the user, newest first. Private
  datasets are filtered by permission labels. The schema accepts `activity_types` /
  `exclude_activity_types`, but this action ignores them. There is no sort option and no total
  count.
- **Activity types emitted by CKAN 2.11** (`ACTIVITY/subscriptions.py`): new / changed / deleted
  package, new / changed / deleted resource view, new / changed / deleted organization and group,
  new / changed user. Older rows may still hold the legacy resource, tag and follow types.
- **`data.actor`:** only package activities store it. Organization, group, user and resource-view
  activities have no `actor` key.
- No HDX action, auth or view override touches `user_activity_list` or `user_show`.

### 1.2 Rendering (v1)
- **Template chain:** core `ACTIVITY/templates/user/activity_stream.html` (no HDX override) →
  `THEME/templates/user/read.html` → `THEME/templates/user/read_base.html` → v1 `page.html`.
  - `subtitle`: "Activity Stream | {display_name}". Hidden `<h1>` "Activity Stream".
  - Breadcrumb: Users / {display_name}.
  - BS5 tab bar: Datasets / Activity Stream / User Permission / API Tokens / Notifications /
    Profile and Password.
  - `row admin-two-col`. The col-3 profile card shows:
    - avatar, display name, Deleted label, bio
    - followers, plus a follow button when viewing someone else
    - dataset count, username, member since
    - email and API key, only when `is_myself`
  - Loads `hdx_theme/admin-styles`.
- **List:** core `ACTIVITY/templates/snippets/stream.html`.
  - `<ul class="activity">`. Each type has its own `snippets/activities/<type>.html`, with an
    FA icon stack, a sentence and a `time_ago` date.
  - The actor is `h.linked_user(activity.user_id, 0, 30)`: avatar plus **display name**, linked
    to the profile.
  - `can_show_activity_detail` is `check_access('activity_list', {'id', 'include_data': True,
    'object_type': 'user'})`. With `public_activity_stream_detail` unset, that means
    `user_update` on the stream's owner, so only the user or a sysadmin passes.
  - When it passes, each item gets links after the date:
    - new package: "View this version" (`activity.package_history`)
    - changed package: "View this version" | "Changes" (`activity.package_changes`)
    - changed organization / group: "Changes"
  - Opening a link needs `package_update` (or the org/group equivalent) on the object, checked
    by `activity_show`.
  - Empty: "No activity found for this type".
- **Pagination:** core `snippets/pagination.html`. Two server-rendered buttons, "Newer activities"
  and "Older activities", each disabled when its URL is `None`. No AJAX.
- **Detail links elsewhere:** HDX's v1 `package/snippets/activity_stream.html` and
  `organization/snippets/activity_stream.html` hard-code `can_show_activity_detail=False`. **This
  page is the only place the links appear today.** The history/changes pages themselves are v1
  (`THEME/templates/package/history.html`, `changes.html`).
- **Analytics:** nothing page-specific. The generic Mixpanel page view uses the `subtitle` block as
  `pageTitle`.
- **Tests:** `test_page_load.py` has no `activity.user_activity` row.
  `test_activity_list_properties.py` covers the action's auth and its email stripping.

### 1.3 Reusable v2 pieces
- **Shell:** `THEME/templates/v2/user-dashboard-base.html` (072).
  - It provides the sidebar, breadcrumb, `subtitle` and page styles.
  - The nav item already exists: `my_activity_stream` in `h.hdx_get_user_dashboard_nav_sections()`,
    linking to `activity.user_activity` with `id=c.user`.
  - It needs `user_dict`, which the view already provides.
- **Header:** `.hdx-v2-user-dashboard-header` (`pages/user-dashboard.less`), with title, subtitle
  and an optional action.
- **Timeline:** `THEME/templates/v2/activity-stream.html`, the type dispatcher shared by the dataset
  page (046) and the org Activity tab (057).
  - It takes `activity_stream`, `id` and `object_type`, and calls
    `v2/components/activity-item.html` per item.
  - `c-activity-item` params: `actor_href`, `actor_label`, `action_text`, `timestamp`, and optional
    `subject_label`, `subject_href`, `extra_classes`.
- **Load more:** `c-text-link`, `style='secondary'`, `size='xs'`, as on the org Activity tab.
- **Label:** `c-label` (`v2/components/label.html`). The dataset page-header's "Deleted" label passes
  `color='red'`, but `label.less` has no `--red` modifier, so it renders without a background.

### 1.4 Gaps in the shared timeline
- **No links row.** `c-activity-item` cannot render "View this version | Changes".
- **No `user` empty state.** The dispatcher handles `organization`, and every other value falls
  through to "No recent activity for this dataset."
- **The actor shows as a UUID (shipped bug).** The dispatcher's `_actor_label` falls back to
  `activity.user_id` when `data.actor` is missing, which is every non-package activity.
  - The local DB has `new resource view` (100), `new user` (26), `changed organization` (10),
    `changed user` (7) and `changed group` (4) activities with no actor.
  - The rendered `/organization/activity/unhcr` shows `af8a08c5-8877-4864-a8dc-c3bcdd5aa658` as
    the actor on every item.
  - On this page, "signed up" and "updated their profile" would show the same.
  - On this page every actor-less row has `user_id` = the stream owner: `user_changed` stores the
    edited user even when a sysadmin edits. Only legacy `follow user` rows by others differ.
- **`follow user` subject** is `activity.object_id` (a UUID). This affects legacy rows only; CKAN
  2.11 no longer emits follow activities.
- **Actor name:** v2 shows the username (`data.actor`, the 046 choice), not v1's display name and
  avatar. Figma also shows a username ("yumiendo").

---

## 2. Figma Analysis (XL)

- **Breadcrumb:** Home / **Account and Settings** / My Activity Stream.
- **Sidebar:** identical to 072.
  - Activity and Content: **My Activity Stream** (active: 4px `#1862d8` bottom border),
    My Datasets, My Organisations, HDX Connect Requests.
  - Account and Settings: API Tokens, Notifications settings, Profile and Password. User
    Permission doesn't appear because it is sysadmin-only.
- **Content frame:** `border-top: 1px #ebeff0`, padding 32/48/48.
- **Header:**
  - Left: "My Activity Stream" (Merriweather 24px bold, `#101212`). The count "28" is
    `display:none`.
  - 6px below it: "A history of your actions" (14px regular, `#2f3536`).
  - Right, 32px away: "Results per page" is `display:none`. "Sort by" (14px, `#3f4748`) + a
    "Most Recent" select (12px, white, 1px `#d8e0e1` border, drop shadow, 2px radius, padding
    6/8/6/10, 14px chevron) is **visible**.
  - The collapse chevrons are `display:none`.
- **Header → list:** 24px.
- **Items:** 10 identical `changed package` rows, using the same `dataset-page-activity-item` layer
  as the dataset page export.
  - Timeline column: 1px `#c4d0d1` line; 12px `#1862d8` dot with a 0.5px `#c4d0d1` border, 21px
    from the top. Column-to-content gap 20px.
  - Content: padding 12px 0, rows 8px apart.
    1. Actor "yumiendo": 14px semibold.
    2. "updated the dataset " + underlined dataset title: 14px regular, `#2f3536`.
    3. **New row: "View this version | Changes":** 12px medium, underlined, inherits `#2f3536`.
       The separator is a pre-wrapped "  |  ".
    4. "42 minutes ago": 12px.
- **List → "Load more":** 24px. The link is 12px medium, underlined, `#101212`.
- **Not in the export:** activity-type variety, empty state, loading state, "Newer activities",
  MD/SM layouts.

---

## 3. Current vs Target / Component Mapping

| Element | Current (v1) | Target (v2) |
|---|---|---|
| Shell | v1 `page.html`, BS5 tab bar, col-3 profile card | `v2/user-dashboard-base.html`, left menu at XL, for every user's stream (D1, D10, D15) |
| Breadcrumb | Users / {name} | Own: Home / Activity and Content / My Activity Stream (D7). Others: Home / Users / {name} / Activity Stream (D14) |
| Header | Hidden `<h1>` | Visible `<h1>` + subtitle: "My Activity Stream" / "A history of your actions"; others: profile header, then an `<h2>` "Activity Stream" / "A history of {name}'s actions" (D6, D14) |
| Sort | None | None (D5) |
| Item | FA icon + sentence + date | `c-activity-item` timeline |
| Actor | Avatar + display name | Username; actor-less activities use the owner's name (D8) |
| Detail links | Inline after the date, owner/sysadmin only | Own row between action and time (D2, D3) |
| Pagination | Newer / Older buttons | Forward-only "Load more" (D4) |
| Empty | "No activity found for this type" | "No recent activity for this user." in the dashboard empty state (D9) |
| Deleted user | "Deleted" label on the profile card | Red `c-label` in the profile header (D17) |
| `<title>` | Activity Stream \| {name} | Base: {page_label} \| {name} \| Users (D11) |

| Need | Mapping |
|---|---|
| Shell, menu, breadcrumb, `subtitle` | **Reuse** `v2/user-dashboard-base.html` with `user_nav_active='my_activity_stream'` and `page_label` = "My Activity Stream" or "Activity Stream" (D14, D15) |
| Header | **Reuse** the `.hdx-v2-user-dashboard-header` markup (072), with no action (D6) |
| Timeline + type dispatch | **Reuse** `v2/activity-stream.html` with `object_type='user'`; **extend** it with opt-in `show_detail_links`, `actor_names` and `load_more_href` params (D2, D8, D16) |
| Empty | **Reuse** `.hdx-v2-user-dashboard-empty` (072), rendered by the page (D9) |
| Deleted label | **Reuse** `c-label` size s; **extend** `label.less` with a `--red` modifier (D17) |
| Item | **Extend** `c-activity-item` with an optional `links` param (`[{label, href}]`) rendering `__links` (D2, D3) |
| Load more | **Reuse** `c-text-link` secondary xs, rendered by the dispatcher (D4, D16) |
| List → Load more gap | Component LESS: `.c-activity-stream__load-more` in `components/activity-item.less` (D16) |
| Count, page size | Omitted: Figma hides them, and there is no total count (D5) |

---

## 4. Dashboard Integration

- **Template:** a new HDX override at `THEME/templates/user/activity_stream.html`. HDX templates
  already take priority over the activity plugin's.
- **Base:** it extends `v2/user-dashboard-base.html` for every user's stream (D1). It sets
  `user_nav_active='my_activity_stream'` and a `page_label` that depends on `is_myself`.
  - The menu follows the viewed user and marks its Activity Stream item active, with
    `aria-current="page"` (D15).
  - The `subtitle` and the breadcrumb come from the base (D14).
- **Content:** `{% block primary %}` holds the profile header (another user's stream only), the header, the
  `v2/activity-stream.html` call (which also renders "Load more") or the empty state.
- **Assets:** the base's `v2-search-page-styles` + `v2-user-dashboard-page-styles`. No page
  scripts, no v1 bundles.
- **Menus:** the header user menu and the sidebar already link here. The v1 profile tab bar's
  "Activity Stream" tab also lands on the v2 page, for any user.

---

## 5. Behavior and Logic

- **No view or action change.** Same route, the same 403 for anonymous users, the same
  `user_activity_list` call, page size and `before`/`after` semantics.
- **Types:** the dispatcher already covers all 23 types (046/057), so no new type branches are
  needed. Figma's single type is not a spec for type coverage.
- **Detail links (D2):**
  - Types and endpoints are exactly core's:
    - new package: history
    - changed package: history + changes
    - changed organization / group: changes
  - Gated by core's `check_access('activity_list', {'id': id, 'include_data': True,
    'object_type': 'user'})`.
  - The dataset and org pages stay without links unless they opt in.
- **Pagination (D4):**
  - "Load more" links to `older_activities_url` (passed as `load_more_href`) and renders only
    when it is not `None`. No heuristic is needed, unlike 057's count-equals-limit check.
  - Forward-only: `newer_activities_url` is not used.
  - Each click is a full page load that replaces the list, the same as 057.
- **Actor (D8):**
  - Label order: `data.actor`, then `actor_names[user_id]`, then `user_id`, then
    `_('unknown user')`. The page passes `actor_names={user_dict.id: user_dict.name}`.
  - No query: the owner's name covers every CKAN 2.11 row (§1.4).
  - The `follow user` subject uses the same dict, falling back to `object_id`.
- **Empty (D9):** the header always renders. With no activity, the page renders
  `.hdx-v2-user-dashboard-empty` below it and does not call the dispatcher.
- **Analytics:** no new tracking. Only `pageTitle` changes (D11).

### Risks & Edge Cases

| Case | Handling |
|---|---|
| A sysadmin edits the user's profile | `user_changed` stores the edited user as `user_id`, so the owner shows as the actor, as in v1 |
| Legacy `follow user` row by another user | Actor and unresolved subject fall back to the UUID, as today (D8) |
| Deleted dataset/org in an activity | Already guarded in the dispatcher (`_('unknown')`, no link) |
| Detail link for a dataset the user can no longer edit | The link renders; opening it gives 403 (v1 parity) |
| Exactly `limit` activities | `older_activities_url` is `None`, so no dead-end "Load more" |
| Stale `before`/`after` past the end | Core behavior, unchanged |
| Viewing another user's stream | v2 page with "Activity Stream" labels (D14); the menu is that user's, with Activity Stream active (D15) |
| Sysadmin viewing another user | As above, plus the detail links (the sysadmin passes the check) |
| Deleted user | Red "Deleted" label in the profile header (D17) |
| Long titles | Wrap; the component has no clamp |

---

## 6. Responsive Behavior & Accessibility

- **XL (≥ 80rem):** sticky 25% menu on the left (072 D3/D14). The content column has the header
  row, then the timeline, then the pager.
- **MD/SM (< 80rem):** no menu; navigation is through the header user menu / offcanvas.
  - The header stacks (title, subtitle), using the 072 rules.
  - Content padding follows Search.
  - Items stay full width with the same timeline at every size.
  - This is inferred, since there are no MD/SM exports. It follows the 072–074 siblings rather
    than 057's org-specific SM card.
- **Accessibility:**
  - One `<h1>` (the page title). The menu is a `<nav>` landmark with `<h2>` group labels (base).
  - The timeline column is `aria-hidden`. Times are `<time datetime>` with the full date in
    `title`.
  - Links-row separators are `aria-hidden` text. "View this version" / "Changes" get their
    purpose from the item sentence (WCAG 2.4.4, in context).
  - `c-text-link` has a focus ring on `:focus-visible`. Hover uses the pseudo-class only.
  - The pager is a plain link navigation, so there is no live region. `role="feed"` does not
    apply: this is not infinite scroll.
  - List semantics: the timeline stays `div`s (D13).

---

## 7. Decisions Taken

| # | Decision |
|---|---|
| D1 Scope | **v2 for every user's stream.** One HDX override, `THEME/templates/user/activity_stream.html`, extends `v2/user-dashboard-base.html`. No conditional `extends`, no view change. |
| D2 Detail links | **Kept, on this page only.** `v2/activity-stream.html` gets an opt-in `show_detail_links` (default False, so the dataset and org pages are unchanged). This page passes core's `h.check_access('activity_list', {'id': id, 'include_data': True, 'object_type': 'user'})`. Types and endpoints as core: new package → View this version (`activity.package_history`); changed package → View this version + Changes (`activity.package_changes`); changed organization / group → Changes (`activity.organization_changes` / `activity.group_changes`). |
| D3 Link style | `c-activity-item` gets an optional `links` param (`[{label, href}]`). It renders a `__links` row between the action and the time: `c-text-link` secondary xs, `aria-hidden` "\|" separators, `space-13` gap, `.hdx-body-xs()`. Figma's `#2f3536` becomes `#101212`. |
| D4 Pagination | **Forward-only "Load more"** (`c-text-link` secondary xs) linking to `older_activities_url`, rendered only when it is not `None`. No "Newer activities" link (057 D7). |
| D5 Sort | Figma's "Sort by: Most Recent" is omitted, and so are the hidden count and page size. |
| D6 Header | The 072 `.hdx-v2-user-dashboard-header` markup (`<h1>`, or `<h2>` below another user's profile header, + subtitle), with no action. |
| D7 Breadcrumb (own) | The base's Home / Activity and Content / My Activity Stream, not Figma's "Account and Settings". |
| D8 Actor | No helper, no query. `v2/activity-stream.html` gets an optional `actor_names` dict (`{user_id: username}`, default `{}`); this page passes `{user_dict.id: user_dict.name}`. Label order: `data.actor`, `actor_names`, `user_id`, `_('unknown user')`. The `follow user` subject uses the same dict, else `object_id`. The dataset page and the org Activity tab pass nothing, so their UUID actors (resource-view and org-change rows) are unchanged and left for a follow-up. |
| D9 Empty | **Dashboard empty state.** The page renders `.hdx-v2-user-dashboard-empty` (072) with "No recent activity for this user." and calls the dispatcher only when there is activity. No `user` branch in the dispatcher. |
| D10 Profile card | On another user's stream, 073's profile header (D27) replaces it. |
| D11 Title | The base's "{page_label} \| {display_name} \| Users". The Mixpanel `pageTitle` change is accepted. |
| D12 Tests | None. |
| D13 Markup | The timeline stays `div`s. |
| D14 Other users | `page_label` = "Activity Stream" when not `is_myself`. Subtitle: "A history of {display_name}'s actions". Below the profile header (073 D27), so the title is an `<h2>`. Breadcrumb: Home / Users / {name} (→ their Datasets page) / Activity Stream. |
| D15 Menu | `user_nav_active='my_activity_stream'` on every stream, including other users', whose menu is theirs (072 D5). The item keeps `aria-current="page"` there. |
| D16 Load more | `v2/activity-stream.html` gets an optional `load_more_href` (default `''`) and renders the "Load more" link after the stream in `.c-activity-stream__load-more` (`margin-top: var(--hdx-space-6)`, `components/activity-item.less`). This page passes `older_activities_url`. The org Activity tab passes its offset URL, and its `.hdx-v2-org-activity__body` rule is dropped so the gap stays 24px. |
| D17 Deleted user | When `user_dict.state == 'deleted'` (v1's condition), a `c-label` (`_('Deleted')`, `color='red'`, `size='s'`, as on the dataset page-header) sits in the profile header (073 D26). `label.less` gets a `--red` modifier (`--hdx-error-1` background, `--hdx-error-8` text, the file-type `--web` pair) and `label.html`'s docblock lists 'red'. This also fixes the dataset page-header's "Deleted" label, which passes `red` but had no rule. |

---

## 8. Files Affected

| File | Change |
|---|---|
| `THEME/templates/user/activity_stream.html` | NEW HDX override: dashboard base, profile header on another user's stream, header, timeline or empty state, Load more (D1, D4, D6, D9, D14, D15) |
| `THEME/templates/v2/activity-stream.html` | `show_detail_links` + per-type links, `actor_names`, `load_more_href`, header comment (D2, D8, D16) |
| `THEME/templates/v2/components/activity-item.html` | Optional `links` param, header comment (D3) |
| `THEME/hdx-styles/src/common/less/v2/components/activity-item.less` | `&__links` row (D3), `.c-activity-stream__load-more` (D16) |
| `THEME/templates/organization/activity_stream.html`, `THEME/hdx-styles/src/common/less/v2/pages/org.less` | "Load more" URL passed as `load_more_href`; `.hdx-v2-org-activity__body` rule removed (D16) |
| `THEME/hdx-styles/src/common/less/v2/components/label.less`, `THEME/templates/v2/components/label.html` | `--red` colour modifier; 'red' in the docblock (D17) |
| `THEME/templates/v2/components.html` | Activity-item demo with detail links, stream demo with Load more, usernames as actors; Red in the label demo |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/046-dataset-activity-section.md`, `057-organization-page-activity-v2.md` | Item `links`, dispatcher `show_detail_links`, `actor_names` and `load_more_href` |
| `ckanext-hdx_theme/llm_docs/redesign/PROGRESS.md` | Migrated-pages row. Also fixes the activity-card line (it is used on the homepage, not the org Activity tab) and the Label colour count |
| `ckanext-hdx_theme/llm_docs/LLM_CONTEXT_HDX_DESIGN.md` | Key-pages entry |
| `ckanext-hdx_theme/llm_docs/redesign/requirements/STATUS.md` | 075 status |

---

## 9. Verification

- The dataset page activity and `/organization/activity/unhcr` render unchanged, with no detail
  links. The org tab's "Load more" stays 24px below the list.
- Own stream:
  - "My Activity Stream" header and breadcrumb, menu item active
  - usernames, not UUIDs, on "signed up", "updated their profile" and org changes
  - detail links on package / org changes
  - "Load more" only when older activity exists
  - the dashboard empty state when there is none
- Another user's stream: "Activity Stream" + "A history of {name}'s actions", breadcrumb
  Home / Users / {name} / Activity Stream, that user's menu with the item active. Detail links only for a sysadmin.
- A deleted user's stream shows a red "Deleted" label in the profile header. The dataset page's "Deleted"
  label is now red too.
- Anonymous: 403, as before.
- MD/SM: no menu; header stacks; timeline full width.
