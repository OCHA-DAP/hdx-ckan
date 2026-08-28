# 059 — Organization Page (Members Tab): v2 Migration

**Scope:** Migrate the Organization page's **Members** tab (`/organization/members/<id>`) to v2 —
reuse the org hero/tabs shell from tasks 056–058, rebuild the member list around a new reusable
**`member-list-card`** component, and migrate the right-hand sidebar ("Your role", "Add / invite
colleagues") to v2 styling. Standard AND custom/branded orgs converge on the same template
(matching 056 `read()` / 057 `activity_offset()` precedent — confirmed, D1).
**Excluded:** Datasets tab (056), Activity tab (057), Stats tab (058), Requested Data tab;
backend/data changes (no new actions, no schema changes, no changes to `member_list` /
`group_member_create` / `member_request_process` semantics).
**Figma sources:** `xl-org-members-page.html`, `md-org-page.html` (Members section only),
`sm-org-page.html` (Members section only) — the latter two are full-page exports stacking every
tab's content; per the task brief, only their Members sections are used below.

---

## Context

Tasks 056–058 migrated the Datasets, Activity and Stats tabs to v2. The org hero
(`v2/org-hero.html` → `page-header.html` + `tabs.html`) **already renders a Members tab item**
pointing at `hdx_members.members`, gated on `c.user` — so today a logged-in visitor clicks from a
v2 hero straight into a v1 Bootstrap page (`organization/members.html` extending
`read_v1_base.html`, with `col-8`/`col-4`, select2, `btn hdx-btn`). This task closes that gap.

Unlike Activity (which had a ready-made v2 component), Members has **no existing v2 list-row
component** — the new `member-list-card` is the main build. Everything around it (hero, tabs,
search input, dropdowns, drawer, buttons, avatar) exists in the v2 library and is reused.

Two structural conflicts between Figma and the current implementation drove most of the open
questions — **all resolved 2026-07-12** (§12): production's **role-grouped, unpaginated,
name-sorted list is kept** (Figma's flat, paginated, "Last added"-sorted list is not implemented
— D2/D3/D6), and all three pieces of live functionality Figma's sidebar omits are **kept**
(Pending approval, Leave this organisation, Group message — D5/D6/D7).

---

## 1. Existing Implementation Audit

### 1.1 Routing / view

`ckanext-hdx_org_group/ckanext/hdx_org_group/views/members.py` — blueprint
`hdx_members = Blueprint('hdx_members', __name__, url_prefix='/organization')`:

| Rule | View | Notes |
|---|---|---|
| `GET /organization/members/<id>` | `members(id)` (line 42) | Page render; **login required** (`if not g.user: raise NotAuthorized`, lines 55–56) |
| `POST /organization/member_delete/<id>` | `member_delete(id)` (line 153) | Remove member / leave org |
| `POST /organization/member_new/<id>` | `member_new(id)` (line 215) | Single add / **change role** (modal posts here) |
| `POST /organization/bulk_member_new/<id>` | `bulk_member_new(id)` (line 299) | The visible "Add / invite" box posts here |

`members()` template context (lines 92–104): `q`, `sort_by_selected`, `members`,
`member_groups` (OrderedDict `role → [(user_id, user, translated_role, role, user_name,
sysadmin), …]`), `allow_view_right_side` (sysadmin OR has any role), `allow_approve` (sysadmin OR
role == `'admin'`), `current_user` (`h.hdx_get_user_info` dict + injected `role`), `org_meta`,
`group_dict`, `request_list` (pending join requests), `non_sysadmin_admins` (last-admin guard).

Template selection still branches (lines 112–115): `custom_members.html` when `org_meta.is_custom`
else `members.html` — the same branch 056/057 removed for `read()`/`activity_offset()` (→ D1).

### 1.2 Data source

`member_list` is **HDX-overridden** in `ckanext-hdx_theme/ckanext/hdx_theme/helpers/actions.py:39`:
queries `Member` ⋈ `User` (active members), filters `q` server-side
(`User.fullname ILIKE %q% OR User.name ILIKE %q%`), returns tuples — **no membership timestamp**.
The core `member` table has **no created/modified column at all**
(`ckan/model/group.py:29–35`: id, table_name, table_id, capacity, group_id, state), so "date
added to org" does not exist anywhere in the data model (→ D3).

Per-row enrichment: `member_item.html` calls `h.hdx_get_org_member_info(id, group_name)`
(`helpers/helpers.py:259`) **once per member** — user info + datasets/orgs/countries counts +
maintainer-package list. N+1-shaped; relevant for large orgs (§10, §11).

### 1.3 Templates (today)

```
organization/read_v1_base.html                 v1 shell (Bootstrap header/tab-bar)
  └─ organization/members.html                  STANDARD org Members page (272 lines)
       └─ organization/custom_members.html      CUSTOM org override (header/branding only)

organization/snippets/member_item.html          member row (avatar, links, role line, counters, actions)
organization/snippets/edit_member.html          "Change role" Bootstrap modal (posts to member_new)
snippets/confirmation_member_delete.html        remove/leave confirmation Bootstrap modal (posts to member_delete)
organization/snippets/add_member.html           legacy add-member modal — appears unused by members.html
snippets/search_form_new.html                   shared v1 search + order-by dropdown (type='members')
```

`members.html` structure: GA blocks `analytics_org_name`/`analytics_org_id` (lines 5–6) →
breadcrumb (Organisations / org / Members) → left column (`col-8`, or `col-12` when
`allow_view_right_side` is false): search/sort snippet (line 41, `count=members|length`,
default sort `'title asc'`), then **per-role sections** (lines 43–70): uppercase header
`"{{role_name}}s [{{count}}]"`, optional **"Group message to all {role}s"** link (select2 +
reCAPTCHA popup, gated by `org_meta.group_message_info.display_group_message`), then a `<ul>` of
`member_item.html` rows → right column (`col-4`, gated `allow_view_right_side`): "Your role"
header + current-user card + "Pending approval" list + "Add / invite" form.
`page_pagination` block is **empty** (lines 251–252) — the full member list renders on one page.

### 1.4 Member row rendering (`member_item.html`)

- Avatar: `h.user_image(member.name, 20)` — **gravatar image**, not initials (→ D11).
- Name: two links to the user profile — `display_name` `|` `name` (username).
- Role line: `{{ translated_role }} - Registered {{ h.render_datetime(member.created) }}`,
  plus `- Sysadmin` suffix when `sysadmin` (→ D16). `member.created` = **user registration
  date**, not date-added-to-org.
- Counters: `{ds_num} Datasets - {org_num} Organisations - {grp_num} Countries` via
  `h.hdx_show_singular_plural`.
- No email is shown anywhere on the row.
- Actions (only when `authorized` = `allow_approve`): **"Change role"** (opens `edit_member`
  modal) `|` **"Remove from this organization"** (opens delete-confirmation modal). Guards:
  - `disable_change` — actions suppressed when the target is an admin and removing/demoting would
    leave the org without a non-sysadmin admin; replaced by the text *"Please add another admin to
    be able to change this user"*.
  - **Maintainer guard** — if the member maintains datasets in the org, deletion is disabled and
    `edit_member.html` marks the `member` role option `disabled` (with a `*` + dataset list).

Roles come from `h.hdx_member_roles_list()` → `[Admin/admin, Editor/editor, Member/member]`.

### 1.5 Search / sort / pagination (today)

- **Search: server-side.** GET form, param `q`, full page reload; ILIKE filter inside the
  `member_list` action (§1.2). No autocomplete, no client-side filtering.
- **Sort: server-side, name only.** Param `sort`; the view sorts in Python on display-name
  lowercase, `reverse` only when `sort == 'title desc'` (members.py:58–59, 74). The shared v1
  order-by dropdown renders more options, but **only `title asc` / `title desc` have any
  effect** on members.
- **Pagination: none.** Entire list rendered; no `page`/`limit` params, no results-per-page.

### 1.6 Sidebar (today)

Gated by `allow_view_right_side`; contains:

1. **"Your role for this organisation: {role}"** header.
2. **Current-user card**: `h.user_image(name, 70)`, display name `|` username links,
   `Registered {date}`, same 3 counters, then **"Edit profile"** — which actually opens the
   *change-role modal* (`#edit-member-div-…`), not the profile editor (→ D8) — `|`
   **"Leave this organization"** (self-delete confirmation modal; self-removal is authorized by
   the HDX `member_delete` auth override,
   `ckanext-hdx_org_group/.../actions/authorize.py:17–28`). Blocked with *"Please add another
   admin…"* when the current user is the last non-sysadmin admin.
3. **"Pending approval [N]"** (only `allow_approve` and `request_list` non-empty): per request —
   avatar, user links, `Requested {date}`, **Approve** (role dropdown) / **Decline** buttons →
   AJAX `POST /api/action/member_request_process` (`fanstatic/organization_/members.js`), inline
   "User has been approved as ROLE." confirmation. Requests are created by the separate
   `hdx_org_join` flow (`/org/join`, ckanext-ytp-request backend) — that flow is NOT part of this
   task; only this approval list is.
4. **"Add / invite colleagues to this organisation"** (only `allow_approve`): form POSTing to
   `bulk_member_new` — one `emails` field (a **select2 tags-autocomplete** input, source
   `/util/user/hdx_autocomplete`, accepts emails/names/usernames, comma tokenizer), one `role`
   select (select2), Submit button. Backend: existing users are added directly
   (`group_member_create`); unknown emails get a PENDING account via `hdx_user_invite` + an
   invitation email; confirmation emails go to user + org admins.

### 1.7 Assets (today)

`hdx_theme/search-scripts`, `hdx_theme/organization-members-scripts`
(= `organization_/members.js`: approve/decline AJAX + analytics), Google reCAPTCHA (used only by
the group-message popup), `hdx_theme/base-dashboard-styles`. All v1 — none of these bundles may be
loaded by the v2 page (v1-assets-untouched rule).

### 1.8 Analytics (today)

- **Server-side** (`ckanext-hdx_org_group/.../helpers/analytics.py`): `RemoveMemberAnalyticsSender`
  (event `member remove`, fired in `member_delete`), `ChangeMemberAnalyticsSender`
  (`member change`, fired in `member_new`), `AddMemberAnalyticsSender` (`member add`,
  `add method: 'by invitation'`, fired per address in `bulk_member_new`). Mixpanel + GA meta
  (org name/id). **These fire in the POST views and survive the template migration untouched.**
- **Client-side**: `members.js` → `hdxUtil.analytics.sendMemberAddRejectEvent('by request',
  approved)` on Approve/Decline (`google-analytics.js:602` — Mixpanel `member add` /
  `member rejected` + GA dataLayer push). Depends on the `analytics_org_name`/`analytics_org_id`
  template blocks. Whatever replaces the approve/decline UI must keep firing these (§10).

---

## 2. Figma Mapping

Token mapping used below: `#ebeff0`→`--hdx-neutral-1` · `#d8e0e1`→`--hdx-neutral-2` ·
`#9db1b3`→`--hdx-neutral-5` · `#3f4748`→`--hdx-neutral-8` · `#2f3536`→`--hdx-neutral-85` ·
`#101212`→`--hdx-neutral-95` · `#bee0d6`→`--hdx-brand-15` · `#18614c`→`--hdx-brand-7` ·
`#1862d8`→`--hdx-primary-5` · `#d48f2a`→`--hdx-warning-5` · `#c44536`→`--hdx-error-5`.

### XL (`xl-org-members-page.html`)

```
[org hero + tabs — identical to 056/057/058, Members active]
[section]  border-top 1px neutral-1, padding 2rem 3rem 3rem, gap 1.5rem   (same container
           treatment as the Activity/Stats tabs)
  [heading row — width of LEFT column only (53.5rem)]
      "Members" (`.hdx-section-title()`, Merriweather 600, 20px) · count "13" (Roboto 1rem, neutral-8), gap 0.5rem
      right-aligned, gap 1rem:  "Results per page" [10 ▾] · "Sort by" [Last added ▾]
      (label Roboto 0.875rem neutral-8; select: 0.75rem/500, white bg, 1px neutral-2 border,
       radius 2px, shadow 0 1px 4px rgba(0,0,0,.04), padding 6px 8px 6px 10px, 14px chevron)
  [two columns, gap 1.5rem]
    LEFT (53.5rem):
      search bar  — full-width, placeholder "Search for members", 1px neutral-2 border,
                    radius 2px, padding 8px 12px, 16px search icon right  (≈ c-search-input)
      member list — member-list-card × page-size, column gap 1rem
      pagination  — centered, 2rem above; ‹ 1 2 3 … 31 › (≈ existing c-pagination exactly)
    RIGHT (flex:1 ≈ 24.5rem):
      "Your role" bio card (§6)
      "Add / invite colleagues" card (§6), width 19rem, padding 1rem, gap 1rem
```

member-list-card @ XL — horizontal, two inner columns (gap 2.5rem), white bg, 1px neutral-1
border, radius 2px, shadow 0 1px 4px rgba(0,0,0,.04), padding 1rem:

```
[info col — 24.5rem, rows gap 0.5rem]
  row1: avatar 32px round (brand-15 bg, brand-7 initials, 0.875rem)
        display name (1rem, 600, neutral-95, ellipsis)  |  username (600, ellipsis)
        ("|" separator in neutral-5)
  row2: "Admin - Registered 2 August 2017"          (0.75rem, neutral-8, ellipsis)
  row3: "48 Datasets - 4 Organisations - 0 Countries" (0.875rem, ellipsis nowrap)
[actions col — flex:1, right-aligned, vertically centered, gap 1rem]
  "Change role" (underlined, 0.875rem, 500, + 16px trailing icon — chevron-down in the MD
   export; icon asset unresolved in XL)  |  "Remove from this organisation" (underlined)
```

Name/username are 1rem/600 — `.hdx-body-m-semibold()`, same as the org-list-card name (the
export's name nodes set no font-size of their own and inherit the card wrapper's 1rem).

Also present but `display:none` in the export: a `search-autocomplete` overlay under the search
bar (D15: not in scope — plain GET search, v1 parity) and a chevron-up collapse icon in the
heading row (not implemented — 057 D3 precedent: full-page tabs don't collapse their only
content).

### MD (`md-org-page.html`, Members section only)

Single column, order changes vs XL:

```
title row ("Members" `.hdx-section-title()`, 20px + count) →
search bar →
controls row ("Results per page" / "Sort by", space-between) →
member cards (gap 1rem) →
pagination →
"Your role" card →
"Add / invite" card          (sidebar cards stack full-width BELOW pagination, gap 1.5rem)
```

member-list-card @ MD: **same horizontal two-column layout as XL** (info col + right-aligned
actions, gap 2.5rem). Note: the export shows `+1` between name and username where every other
breakpoint shows `|` — confirmed a Figma export artifact; `|` is canonical everywhere (D13).

### SM (`sm-org-page.html`, Members section only)

The export renders Members as one accordion section of the stacked page (padding
`1.5rem 1rem 2rem`). Content shown: controls row ("Results per page" / "Sort by",
space-between) → member cards. **The SM export contains no search bar, no pagination, and no
sidebar cards** — decided (D14): the search bar and the stacked sidebar cards ARE included at
SM anyway, MD-style (feature parity; pagination is dropped at all breakpoints per D2).

member-list-card @ SM: **stacks vertically** — info block full-width, then the actions row
below it, left-aligned (card is flex-column, gap 1rem, padding 1rem).

Tab-bar behavior at MD/SM is not re-decided here — the accordion chrome in these exports predates
056's decision that each tab is a separate page with `c-tabs` (overflow-x scroll at SM).

---

## 3. Member List Card Definition (`member-list-card` — NEW)

New component pair, following the established convention:

- `templates/v2/components/member-list-card.html` — class `.c-member-list-card`, strict BEM
- `hdx-styles/src/common/less/v2/components/member-list-card.less` (compiled CSS picked up by
  the IDE; add to `v2-components-styles` bundle)

### Structure / fields (verified against Figma + real data, §1.4)

| Element | BEM | Source (real data) |
|---|---|---|
| Avatar | `__avatar` | reuse `v2/components/avatar.html` (`c-avatar`), initials-only (D11 — gravatar dropped on this page) |
| Display name (link) | `__name` | `member.display_name` → user profile URL |
| Separator `|` | `__sep` | static, `--hdx-neutral-5` |
| Username (link) | `__username` | `member.name` → user profile URL |
| Role + registered line | `__meta` | `translated_role` + `h.render_datetime(member.created)` (user registration date — the only date available, §1.2); bold `- Sysadmin` suffix rendered by the component from the separate `sysadmin` bool param (D16) |
| Stats line | `__stats` | `ds_num` / `org_num` / `grp_num` via `h.hdx_show_singular_plural` |
| Actions | `__actions` | caller-provided `{% call %}` body — change-role/approve as `c-dropdown--link` one-click dropdowns, remove/leave/decline as `text-button`s (size m) |

### Snippet API (data-only; the component computes NO permissions)

```jinja
{% call h.snippet('v2/components/member-list-card.html',
    avatar_initials=...,                            {# initials-only, D11 #}
    name=..., username=..., profile_url=...,
    meta_text=...,                                  {# pre-rendered "Admin - Registered …" line #}
    sysadmin=...,                                   {# bool — appends bold "- Sysadmin" (D16) #}
    stats_text=...,                                 {# pre-rendered "N Datasets - …" line #}
    disabled_note=...,                              {# replaces actions when last-admin guard trips #}
    extra_classes=...)                              {# e.g. 'c-member-list-card--stacked' #}
%}
  ...actions markup...
{% endcall %}
```

- The actions area is a `caller()` body (no actions column renders without one, unless
  `disabled_note` is set), so the page wires the one-click change-role dropdown
  (`data-change-role-user` wrapper + `data-role-value` items submitting a hidden POST form to
  `member_new`) and the remove-drawer trigger without the component knowing about dropdowns,
  drawers or permissions. `disabled_note` covers the v1 *"Please add another admin…"*
  replacement text (§1.4).
- Pre-rendered `meta_text`/`stats_text` strings keep the card dumb and reusable (matches how
  `page-header.html` receives `member_since` pre-rendered, 056 precedent).

### Behavior / states

- **Size is breakpoint-dependent, NOT a parameter**: horizontal two-column ≥ `@hdx-bp-md`
  (48rem, per the SM/MD boundary shown in Figma), stacked column below. One markup, LESS
  media queries only.
- **States: default + `:hover`** (pseudo-class only — never an `is-hovered`/parameter). Figma
  shows no explicit hover spec; apply the standardized card hover treatment (task 028 /
  `dataset-card`/`org-list-card` pattern) (D17: confirmed).
- No JS of its own. WCAG: links are real `<a>`; action controls are `<button>`s (dropdown
  triggers for change-role/approve, drawer opener for remove — D9); ellipsized
  names keep full value in `title=`.

### Reusability check

- **Pending-approval rows** (§1.6.3) share the avatar/name/date left side and reuse the card
  via the `caller()` body (Approve = one-click `c-dropdown--link` firing the AJAX, Decline =
  text button) with the `--stacked` variant for the narrow sidebar column (D5: the Pending
  approval block stays, sidebar v1 position).
- **The sidebar "Your role" bio card** is visually a borderless variant with a bio text block —
  NOT forced into this component; §6 keeps it as page-level markup reusing `c-avatar` (D18:
  confirmed).
- No existing component overlaps: `org-list-card`/`dataset-card` are structurally similar but
  content-incompatible (checked before creating the new component — no duplication).

---

## 4. Search & Sorting Strategy

- **Search — reuse `v2/components/search-input.html`** (`c-search-input`, size `m`) inside a GET
  form preserving the existing param name `q` (server-side filtering stays in the `member_list`
  action untouched). Same submit-on-enter, full page reload as v1 and as the datasets tab's
  search bar (`hdx-v2-search-bar-row` pattern from `package_list.html`). Placeholder:
  *"Search for members"* (Figma). Preserve `sort` as a hidden input so searching doesn't reset
  it (no pagination params — D2). The magnifier is a submit button (`icon_submit=True`) and a
  clear `×` resets an active search — shared `c-search-input` behavior.
- **Sorting — server-side reload, reusing the v2 navigate-dropdown pattern.** The existing
  `v2/search-nav-controls.html` is hardcoded to the *dataset-search* option set and
  `ext_page_size` semantics, so it is **not directly reusable**; per D4 it is **generalized** —
  parameterized to accept caller-provided option lists / param names, with the per-page dropdown
  optional (this page doesn't render one, D2). Existing callers (search page, org datasets tab)
  keep their current behavior via defaults and **must be regression-checked**. No new dropdown
  component is built.
- **Sort options (decided, D3):** Figma's default "Last added" is **not implementable** — the
  `member` table stores no timestamp (§1.2) and backend changes are excluded. Ship exactly
  **Name Ascending** (default, = existing `title asc`) and **Name Descending** (`title desc`),
  matching the existing v2 nav-controls labels; "Last added" is dropped.
- Sorting continues to be applied in the existing view (`members.py:74`) — no logic change, the
  new UI just submits the same `sort` values (`title asc` / `title desc`).

---

## 5. Pagination Strategy

**Decided (D2): no pagination — v1 parity, a deliberate deviation from Figma.** The entire
role-grouped member list (D6) renders on one page, exactly as today:

- No `c-pagination` on this page and **no "Results per page" dropdown** — Figma's pager and
  per-page control are both dropped; the heading row keeps only title + count + "Sort by".
- No new GET params, no slicing in `members()`, in the template, or anywhere else; the view is
  untouched beyond the D1 template-selection edit.
- Count semantics unchanged: `members|length` = filtered count.
- Consequence for large orgs: full-list rendering and the per-row `hdx_get_org_member_info`
  enrichment (§1.2) stay v1-parity — flagged in §10, not worsened.

---

## 6. Sidebar Strategy

- **Placement:** Figma puts the sidebar on the **right at XL**, stacked **below the list at
  MD/SM**. The existing v2 sidebar pattern (`hdx-v2-search-sidebar`) is left-side,
  border-right, hidden below XL — reusing its *mechanics* (flex column siblings inside
  `.hdx-v2-content-columns`, XL-only media query, `v2/page.html`'s
  `outer_row_class`/`columns_class`/`sidebar_class`/`content_class` vars +
  `secondary_content` block) but with **new page-scoped classes** (e.g.
  `hdx-v2-org-members-sidebar`, right-ordered via flex `order`/DOM order, no border-right) —
  not by overriding search-page CSS (style-override avoidance, 056 precedent).
- **Visibility:** the whole sidebar stays gated by `allow_view_right_side`; when hidden the list
  takes full width (v1 parity).
- **Card 1 — "Your role":** `Your role for this organisation: {role}` + current-user block
  (reuse `c-avatar`; name `|` username profile links; `Registered {date}`, counters,
  "Edit profile" link). Figma's avatar badge (warning-5 ring + error-5 dot) is **omitted** —
  nothing in the data model drives it (D12). V1's **"Leave this organization"** action is
  **kept** in the card (D7), and **"Edit profile" keeps its v1 change-role behavior** — the
  change-role UI is the one-click `c-dropdown--link` role dropdown (no dialog), rendered for
  every sidebar viewer (D8/D9).
- **Card 2 — "Add / invite colleagues":** gated by `allow_approve` (v1 parity). v2 build from
  existing primitives: intro paragraphs (Figma copy matches v1 copy almost verbatim), input:
  the select2 tags-autocomplete is **ported to v2** (D10) — new JS building on the existing
  `c-autocomplete` component (`v2/components/autocomplete.html`, 045), same source
  `/util/user/hdx_autocomplete`, same comma tokenizer / email support,
  role select via `v2/components/dropdown.html` **`native=True`** (real `<select
  name="role">` — POST-safe, no JS), submit via `c-button` primary. Form target unchanged:
  `POST /organization/bulk_member_new/{id}` + `h.csrf_input()`. Backend flow, invite emails and
  analytics remain untouched (§1.6.4, §1.8).
- **Pending approval:** absent from Figma but live functionality — **kept in its v1 position**
  (between the "Your role" card and the invite card), restyled with v2 primitives (D5); the
  permission gate (`allow_approve` + non-empty `request_list`) and the
  `member_request_process` AJAX + analytics contract survive unchanged.
- **Group message (list column, role-section headers) — kept (D6):** the per-role "Group
  message to all {role}s" links stay, and the v1 select2 + reCAPTCHA popup is rebuilt as a
  `c-drawer` (contact-contributor pattern) with v2 form primitives in this task. The Google
  reCAPTCHA script (an external script, not a v1 bundle) is loaded on the page for it.

---

## 7. Permissions Strategy

All gates are **existing booleans computed in the view — reused verbatim, no new logic**:

| Gate | Controls | v2 treatment |
|---|---|---|
| route-level `g.user` check | whole page (403 for anonymous) | unchanged; tab item already gated `show: c.user` in `org-hero.html` |
| `allow_view_right_side` (sysadmin OR any role) | sidebar column; list column width | unchanged; full-width list variant when false |
| `allow_approve` (sysadmin OR admin) | row actions (`authorized`), Pending approval, Add/invite card | unchanged; passed into `member-list-card` as an empty/populated `actions` list |
| `disable_change` / `non_sysadmin_admins < 2` / `no_admins` | last-admin protection on rows + "Leave" | unchanged; card renders `disabled_note` instead of actions |
| maintainer guard (`maint_orgs_pkgs`) | blocks removal / demotion-to-member of dataset maintainers | unchanged; disabled option (+tooltip) in the change-role dropdown, dataset list in the remove drawer |
| `member_delete` auth override (self-removal) | "Leave this organization" | unchanged backend; UI kept in the bio card (D7) |

**UI per role** (unchanged from v1, restated as the acceptance matrix):

- **Anonymous:** no tab, direct URL → 403.
- **Logged-in non-member:** list only (no sidebar, no actions), full-width.
- **Member / Editor:** list without row actions + sidebar Card 1 only (own card, leave-org
  kept per D7). No invite card, no pending approvals.
- **Admin / Sysadmin:** everything — row actions, pending approvals, invite card.

Nothing in this task may alter the POST views or auth functions — this migration is
template/asset-layer plus the D1 template-selection edit in `members()` (no slicing — D2
dropped pagination).

---

## 8. Component Strategy

| UI element | Approach | Justification |
|---|---|---|
| Breadcrumb | **Reuse** — `v2/components/breadcrumb.html` via `breadcrumb_items`, same 3 ancestors + "Members" active | Same pattern as 056–058 |
| Org hero (header + tabs) | **Reuse as-is** — `v2/org-hero.html` with `active_tab='members'`, same `header_stats` | Zero new params needed; Members item already in the tabs list. (`header_stats` is no longer passed here — see 056's "KPI-style cards?" — the hero no longer shows a Datasets/Members count.) |
| Tabs | **Reuse as-is** — `v2/components/tabs.html` (via org-hero) | — |
| Search bar | **Reuse** — `c-search-input` in a GET form (§4) | Existing component matches Figma's input 1:1 |
| Sort by (no per-page — D2) | **Generalize** `v2/search-nav-controls.html` (D4): caller-provided option lists / param names; per-page dropdown optional | Existing callers (search page, org datasets tab) keep behavior via defaults — regression-check both |
| Member row | **NEW — `member-list-card`** (§3) | No existing component renders a user row; org-list-card/dataset-card checked and content-incompatible |
| Avatar | **Reuse** — `c-avatar`, initials-only (D11), no badge (D12) | — |
| Pagination | **Not implemented** (D2) — full list, v1 parity | §5 |
| Row actions / links | **Reuse** — `c-dropdown--link` one-click dropdowns (change role / approve) + `text-button` size m (remove / leave / decline) | Trigger typography matches `c-text-button--secondary`; per-item attrs via the generalized `dropdown-panel.html` |
| Role select (invite) | **Reuse** — `c-dropdown` `native=True` | POST-safe real `<select>`, no JS |
| Submit button | **Reuse** — `c-button` primary | — |
| Remove/leave confirmation + group-message dialogs | **Reuse `c-drawer`** (`v2/components/drawer.html` + `fanstatic/v2/components/drawer.js`) with explicit Confirm/Cancel | Change-role is NOT a dialog — one-click `c-dropdown--link` (D9); drawer is the established pattern (contact contributor, 051) |
| Invite input | **Port** — tags-autocomplete rebuilt on `c-autocomplete` (045) + new v2 JS; source `/util/user/hdx_autocomplete`, comma tokenizer (D10) | Keeps the username/email lookup convenience without select2 |
| Group message popup | **Rebuild in `c-drawer`** + v2 form primitives + reCAPTCHA (D6) | Replaces the v1 select2/reCAPTCHA popup; links stay on role-section headers |
| Sidebar bio card | Page-level markup (`hdx-v2-org-members-*`), composing `c-avatar` + text links (D18: confirmed) | One-off; promote to a component only if reused later |

Asset wiring: page CSS into `v2/org-page.css` (LESS source `v2/org-page.less`) like 056–058;
component CSS/JS into `v2-components-styles`/`-scripts`; reuse `v2-search-page-scripts` for
`url-nav.js`, which the generalized nav controls keep using (D4 — matching how the datasets tab
already loads it). New JS (approve/decline AJAX port, invite tags-autocomplete, drawer content
wiring for change-role / remove / group message) goes under `fanstatic/v2/` — v1 bundles
(`organization-members-scripts`, `search-scripts`) are never loaded on the v2 page.

---

## 9. Responsive Strategy

| Breakpoint | Layout | Heading/controls | member-list-card | Sidebar |
|---|---|---|---|---|
| **XL (≥ 80rem)** | Two columns (list 53.5rem-equivalent + right sidebar), gap 1.5rem | Title+count left, "Sort by" right (no per-page — D2), in one row above the search bar | Horizontal: info col + right-aligned actions | Right column: Your role card, pending approvals, invite card |
| **MD (48–80rem)** | Single column | Title+count row → search bar → "Sort by" row | Horizontal (same as XL) | Stacked full-width below the member list |
| **SM (< 48rem)** | Single column | Same order as MD (D14: search bar included) | **Stacked**: info block, then actions row left-aligned below | Stacked below the list (D14: included) |

- Member cards render inside the v1 role-grouped sections (D6) at all breakpoints.
- Breakpoints via `@hdx-bp-*` LESS variables only; layout lives in `org-page.less` page classes +
  `member-list-card.less` media queries. No Bootstrap classes anywhere.
- Ellipsis behavior (name/username/meta/stats single-line truncation) applies at all breakpoints
  per Figma; full values exposed via `title=`.
- The heading-row chevron and SM accordion chrome from the exports are not implemented (separate
  full pages per tab — 056/057 precedent).

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Breaking permission logic** ❗ — last-admin guard, maintainer guard, self-removal, approve gates are spread across view + row snippet | §7 matrix is the acceptance checklist; all booleans reused verbatim from the view; `member-list-card` receives pre-computed action lists and never re-derives permissions |
| **Losing live functionality Figma omits** ❗ — Pending approval, Leave organisation, Group message, sysadmin suffix, select2 invite autocomplete | All explicitly decided (D5–D10, D16): **everything is kept** — Pending approval (v1 position), Leave, Group message (drawer rebuild), sysadmin suffix, invite autocomplete (v2 port) |
| **Inconsistent member rendering** ❗ — role-grouped (v1) vs flat (Figma) lists diverge in counts, headers, group-message anchors | Resolved (D6): role-grouped v1 structure kept; count semantics (`members|length` = filtered count) preserved |
| **Pagination mismatch** ❗ — full-list rendering today vs numbered pager in Figma | Resolved (D2): no pagination — v1-parity full list, no slicing anywhere; deliberate Figma deviation |
| **Generalizing `search-nav-controls.html`** (D4) touches the search page + org datasets tab | Backwards-compatible defaults for existing callers; regression-check both pages after the change |
| **Invite autocomplete port** (D10) — new v2 JS replacing select2 on a POST-critical form | Build on `c-autocomplete` (045); behavior-parity checklist: comma tokenizing, email + username entries, unchanged `emails` field payload to `bulk_member_new` |
| **Duplication of components** ❗ — user-row/bio-card/approval-row look-alikes | §3 reusability check done up front; single `member-list-card` with caller-provided actions; bio card stays page-level (D18) |
| Sidebar inconsistency ❗ — first right-side sidebar in v2 (search pattern is left-side) | New page-scoped layout classes; no overrides of `hdx-v2-search-*`; same `v2/page.html` block/vars mechanism |
| Analytics regressions — approve/decline events live in v1 `members.js`; add/change/remove senders live in POST views | POST-view senders unaffected; the approve/decline AJAX port to `fanstatic/v2/` must keep calling `sendMemberAddRejectEvent` with identical args; GA org name/id blocks re-exposed on the v2 page |
| Performance on large orgs — `hdx_get_org_member_info` per rendered row (N+1) | No pagination (D2) — v1-parity full-list enrichment; flagged, not worsened |
| Drawer-based dialogs (D9) carry destructive actions (remove member) | Explicit Confirm/Cancel step mandatory in the drawer; keyboard/focus management per WCAG checklist |

---

## 11. Edge Cases

| Case | Expected behavior |
|---|---|
| Search with zero matches | List area renders an empty-state message (D17: search-page empty-state pattern, "No members found" copy); count shows `0`; sidebar unaffected |
| Org where the viewer has no role and isn't sysadmin | Full-width list, no sidebar, no actions (v1 parity) |
| Sysadmin viewing an org they're not a member of | Sidebar visible; `current_user.role` is `None` — v2 renders the raw role value like v1 (empty for sysadmin non-members — D17) |
| Last non-sysadmin admin | Row actions replaced by the "add another admin" note; "Leave" (kept, D7) blocked with the existing message |
| Member who maintains datasets in the org | Cannot be removed; `member` role option disabled (with tooltip) in the change-role dropdown; the dataset list is shown in the remove drawer (v1 behavior, D9) |
| Invited-but-not-signed-up user (PENDING account) | Appears in the member list like any member (v1 behavior); name may equal the generated username |
| User with no fullname | v1 shows username twice (`display_name` falls back to `name`) — carried over; ellipsis prevents overflow |
| Very long names/usernames (Figma's "Alberto Castillo Aroca…" case) | Single-line ellipsis on name, username, meta and stats lines; full value in `title=` |
| Missing avatar | Always initials (D11: initials-only — no image path on this page) |
| Large orgs (hundreds of members) | Full list rendered (D2: no pagination) — v1 parity |
| Zero pending requests / non-approver | Pending block absent entirely (not an empty shell) |
| Sysadmin member rows | `- Sysadmin` suffix kept (D16) |
| `is_custom = True` org | Same unified template as standard orgs (D1: confirmed, 056/057 precedent) |

---

## 12. Decisions Taken

All open questions were resolved with the product owner; the decisions below are final for this
task and are folded into §§2–11 (D-numbers are kept as reference ids used throughout the doc):

| # | Decision |
|---|---|
| **D1** | Unify — remove the `is_custom` branch in `members()` (`views/members.py:112-115`); `custom_members.html` left orphaned like `custom_activity_stream.html` (057 D9) |
| **D2** | **No pagination** — v1 parity, deliberate Figma deviation; no "Results per page" dropdown, no view/template slicing, no new GET params |
| **D3** | Sort ships **Name Ascending / Descending only** (existing `title asc`/`title desc`), default ascending; "Last added" dropped (no timestamp in the data model) |
| **D4** | **Generalize `v2/search-nav-controls.html`** — caller-provided option lists / param names, per-page dropdown optional; regression-check the search page + org datasets tab |
| **D5** | **Pending approval kept, v1 position** (sidebar, between "Your role" and the invite card), restyled with v2 primitives; AJAX + analytics contract (§1.8) preserved |
| **D6** | **Role-grouped v1 list structure kept** ("ADMINS [N]"-style headers); **Group message kept** — popup rebuilt as a `c-drawer` (contact-contributor pattern) in this task |
| **D7** | **"Leave this organization" kept** in the bio card; last-admin block message follows it |
| **D8** | "Edit profile" **keeps the v1 change-role behavior** as the one-click change-role dropdown — no modal/dialog; rendered for every sidebar viewer (v1 parity) |
| **D9** | **`c-drawer` for confirmations** — remove/leave and the group-message form, with explicit Confirm/Cancel; **change-role and approve ship as one-click `c-dropdown--link` dropdowns** (selection applies immediately: hidden-form POST to `member_new` / AJAX `member_request_process`) |
| **D10** | **Invite tags-autocomplete ported to v2** — new JS on top of `c-autocomplete` (045); same `/util/user/hdx_autocomplete` source, comma tokenizer, email support |
| **D11** | **Initials-only avatars** (`c-avatar`); gravatar dropped on this page |
| **D12** | Figma bio-card avatar **badge omitted** — nothing in the data model drives it |
| **D13** | MD `+1` is an **export artifact** — `\|` separator is canonical at all breakpoints |
| **D14** | Search bar + stacked sidebar cards **included at SM** anyway, MD-style (feature parity) |
| **D15** | Member-search autocomplete **out of scope** — plain GET search, v1 parity; the hidden Figma layer is a leftover from the global search component |
| **D16** | **`- Sysadmin` suffix kept** (v1 parity) |
| **D17** | Empty search: search-page empty-state pattern, "No members found" copy; hover: standard 028 card treatment; sysadmin non-member: "Your role…" renders the raw role value, empty when none — v1 parity |
| **D18** | Sidebar bio card stays **page-level markup**; promote to a component only if another page needs it |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/.../templates/organization/members.html` | Replaced with v2 template: extends `v2/page.html`, org hero (`active_tab='members'`), search form, role-grouped member list via the new card, right sidebar, change-role / remove / group-message drawers |
| `ckanext-hdx_theme/.../templates/organization/custom_members.html` | Orphaned per D1 (kept in place, 057 D9 precedent) |
| `ckanext-hdx_theme/.../templates/v2/search-nav-controls.html` | Generalized per D4 (caller-provided option lists / param names, per-page optional); search page + org datasets tab regression-checked |
| `ckanext-hdx_theme/.../templates/v2/components/member-list-card.html` | **NEW** — §3 |
| `hdx-styles/src/common/less/v2/components/member-list-card.less` | **NEW** — §3 (compiled CSS added to `v2-components-styles`) |
| `hdx-styles/src/common/less/v2/pages/org.less` | Members-page layout classes (`hdx-v2-org-members-*`), sidebar/two-column rules |
| `ckanext-hdx_theme/.../fanstatic/v2/pages/org-members.js` | Approve/decline AJAX port, change-role hidden-form POST wiring, remove/leave + group-message drawer wiring incl. invisible reCAPTCHA (D6/D9), invite tags-autocomplete JS (D10) |
| `ckanext-hdx_theme/.../fanstatic/webassets.yml` | `member-list-card.css` appended to `v2-components-styles`; new `v2-org-members-page-scripts` bundle (`url-nav.js` + `org-members-page.js`) |
| `ckanext-hdx_org_group/.../views/members.py` | D1 template unification only — no page slicing (D2: no pagination). **No other view/auth/action changes** |
| v1 files (`member_item.html`, `edit_member.html`, `add_member.html`, `search_form_new.html`, `organization_/members.js`, v1 bundles) | **Untouched** — superseded for this page, never edited |
