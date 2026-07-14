# 056 — Organization Page (Datasets Tab): v2 Migration

**Scope:** Migrate the individual Organization page (`/organization/<name>`) Datasets tab to v2 —
breadcrumb, org header/hero (with permission-gated actions), a new minimal tabs component
(Datasets active), and full reuse of the existing v2 dataset search/filter/list/sort/pagination
stack, scoped to the organization. Standard orgs AND "custom"/branded orgs (WFP, UNHCR, etc.)
converge on ONE unified v2 template — no more parallel implementations.
**Excluded:** Activity Stream / Members / Stats / Requested Data tab *content* (tabs link to their
existing v1 routes for now); "You might also like" cross-sell section; the custom-org visualization/
embed block; the custom-org Follow button; per-org brand color theming; any backend/API changes;
the separate mobile "light" theme (`/m/organization/`) — untouched here, retirement is a separate
follow-up (D15); the "Group message" action and the contribute-flow JS wiring (D18);
promoting Figma's "Time period" / "Data type" / "Show only" sections into new filter
groupings — the existing filter sidebar/facet set is reused exactly as-is (see D12).
**Figma sources:** `xl-org-page.html`, `md-org-page.html`, `sm-org-page.html`, `xl-org-members-page.html`
(this fourth file exists only to reveal permission-gated header actions and confirmed tab CSS —
its Members-tab *content* is out of scope and not used below)

---

## Context

The Organization page has never been touched by the in-flight v2 redesign (tasks 001–055). The
sibling **All Organisations list** page (`/organization/`, task 049) was migrated already, but the
single-org **read/detail** page — what a visitor sees when they click into "3iS" or "WFP" — is still
full v1: Bootstrap tab markup, no design tokens, and a genuine architectural split between standard
orgs and ~a handful of large "custom" branded partners that render through an entirely different,
substantially duplicated template.

This doc scopes the migration to the **Datasets tab only** (the default/landing tab), reusing the
existing v2 dataset-search stack wholesale, while introducing the two pieces that don't exist yet:
an org-appropriate hero header and a minimal, reusable tabs component.

---

## 1. Existing Implementation Audit

### 1.1 Template inheritance (v1, today)

```
organization/read_base.html          extends page.html (v1 shell)
  └─ organization/read.html          STANDARD org Datasets tab (real hub template)
       ├─ organization/members.html          Members tab   ─┐
       ├─ organization/stats.html             Stats tab      ├─ all three extend read.html,
       └─ organization/activity_stream.html   Activity tab  ─┘  OUT OF SCOPE, must keep working

organization/custom/custom_org.html   extends read_base.html directly — CUSTOM org Datasets tab
                                       (parallel, ~90% duplicated template, not a subclass of read.html)
organization/custom/custom_org_header.html   (branded header partial, included by custom_org.html)
organization/custom_members.html / custom_stats.html / custom_activity_stream.html
                                       thin wrappers: extend the standard tab templates, override
                                       ONLY the header block to swap in custom_org_header.html — OUT OF SCOPE

light/organization/read.html          separate mobile theme at /m/organization/ — TO BE RETIRED
```

Routing: `ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py::read()` (`hdx_org`
blueprint, `/organization/<id>`) branches at the **Python level**:
```python
if read_logic.org_meta.is_custom:
    result = render('organization/custom/custom_org.html', template_data)
else:
    # ... render('organization/read.html', ...)
```
(`views/organization.py:67-90`). `is_custom` comes from the org extras flag `custom_org`
(`org_meta_dao.py::OrgMetaDao.__process_custom()`, lines 164-177) — a manually-toggled admin
checkbox ("Use custom organisation page"), not a hardcoded org list. It also unlocks two JSON
extras blobs: `customization` (image_sq, image_rect, highlight_color, logo_bg_color,
topline_resource) and `visualization_config` (embedded/embedded-preview iframe settings).

### 1.2 Header content (v1)

| Element | Standard org (`browse/snippets/org_item_read.html`) | Custom org (`custom_org_header.html`) |
|---|---|---|
| Title | `h1.itemTitle` | `h1.org-title` |
| Logo | none | square (75×75) + large rect (300×125) |
| Description | `h.markdown_extract`, no length limit | `h.render_markdown`, `hdx_show_more points=320` |
| "Get notified" | ✅ `notification_platform/buttons.html` | ✅ same snippet |
| "Visit Website" | ✅ plain text link (`org_url` extra) | ✅ same, plus a **floating sticky** duplicate |
| Datasets / Members / Followers counts | plain text | plain text (no Followers on custom) |
| Follow button | ❌ never (hard-disabled, see below) | ✅ `h.hdx_follow_button('group', ...)`, **floating header only** |
| Share | ❌ | present but **broken** (points at a non-existent panel — confirmed dead) |
| Edit / Add Dataset / Request Membership | `organization/snippets/org_actions_menu.html` dropdown | same shared snippet |
| Visualization/embed block | ❌ | iframe or static preview image (**broken "Embed data" popup**; "Key Figures" KPI row fully commented out of the HTML even though its backend still computes it) |

`org_actions_menu.html` (extends `package/snippets/base_actions_menu.html`, which hard-codes
`hide_follow = true` and `hide_contact_contributor = true` for orgs):
```jinja
{% if can_create_dataset %}
  <li><a href="#" onclick="contributeAddDetails(null, 'org')">{{_('Add Dataset')}}</a></li>
{% endif %}
{% if can_edit %}
  <li>{% link_for _('Edit'), controller='organization', action='edit', id=organization.name %}</li>
{% endif %}
{% if request_membership and request_membership_flag == 'true' %}
  <li><a href="{{h.url_for('hdx_org_join.find_organisation', selected=org_id)}}">{{ _("Request Membership") }}</a></li>
{% endif %}
```
Plus, from the parent `base_actions_menu.html`: a **"Group message"** action gated on
`membership.display_group_message`.

**"Add Dataset" is genuinely functional today** — `onclick="contributeAddDetails(null, 'org')"`
triggers an existing JS-driven flow. v2 must call the exact same handler, unchanged.

### 1.3 Permissions (all pre-computed as booleans, Python-side, then re-checked in templates)

| Boolean | Check | Computed in |
|---|---|---|
| `can_edit` | `check_access('organization_update', {'id': org_id})` | `organization_read_logic.py:104`, `org_meta_dao.py:125` |
| `can_create_dataset` | `check_access('package_create', {'organization_id': org_id, 'owner_org': org_id})` | `organization_read_logic.py:105-108`, `org_meta_dao.py:126-128` |
| `allow_basic_user_info` | `check_access('hdx_basic_user_info')` (= just logged in) | `organization_read_logic.py:101`; auth fn in `hdx_theme/helpers/auth.py:39-41` |
| `allow_req_membership` | `not user_in_org_or_group(org_id) and allow_basic_user_info` | `organization_read_logic.py:102` |
| `display_group_message` | current user is themselves a member (`hdx_member_list`) | `org_meta_dao.py::fetch_group_message_topics()` → `hdx_package/helpers/membership_data.py:50` |
| "Get notified" visible | `hdx_supports_notifications('organization', org_id, org_dict)` — a **business rule**, not an ACL | `hdx_theme/helpers/helpers.py:1167` |
| Requested Data tab visible | `check_access('organization_update', {'id': org_dict.id})` (same as `can_edit`) | `custom_org.html:53` / `read_base.html` equivalent |

The pattern is belt-and-braces: computed once in `OrgReadLogic`/`OrgMetaDao`, passed as plain
booleans into templates, and in a few spots re-checked with `h.check_access(...)` directly. v2
**reuses these exact booleans** — no new permission logic.

### 1.4 Tabs (v1)

Not a shared component — each template hand-rolls a `<ul class="nav nav-tabs">` via
`h.build_nav_icon()` / `h.bs5_build_nav_icon()`. Standard `read.html` wires only 2 items
(Datasets, Activity); `custom_org.html` wires the real 5-item set:
```jinja
{{ h.bs5_build_nav_icon('hdx_org.read', _('Datasets'), id=org_dict.name, class_='nav-link hdx-tab-button') }}
{{ h.bs5_build_nav_icon('hdx_org.activity', _('Activity Stream'), id=org_dict.name, class_='nav-link hdx-tab-button') }}
{% if c.user %}{{ h.bs5_build_nav_icon('hdx_members.members', _('Members'), ...) }}{% endif %}
{% if h.check_access('organization_update', {'id': org_dict.id}) %}
  {{ h.bs5_build_nav_icon('requestdata_organization_requests.requested_data', _('Requested Data'), id=org_dict.name, class_='nav-link') }}
{% endif %}
{{ h.bs5_build_nav_icon('hdx_org.stats', _('Stats'), ...) }}
```
This standard/custom drift (2 tabs vs. 5) is a real bug the v2 migration fixes by using one
shared, permission-gated tab list for every org.

### 1.5 Dataset listing (v1) — the big reuse win

The org page **already** renders its dataset list through the same shared component the main
search page uses:
```jinja
{% snippet 'search/snippets/search_results_wrapper.html', tracking_enabled=g.tracking_enabled,
    my_c=org_dict.search_template_data %}
```
`search_results_wrapper.html` → `search/snippets/package_list.html` → (v2 branch, currently never
taken here) `package_item_v2.html` / `v2/components/dataset-card.html`, `v2/search-filters.html`,
`v2/components/dropdown.html`, `v2/components/pagination.html`. **The only reason the org page
doesn't already show the v2 list/filters/sort/pagination is that `v2=True` is never threaded into
this call today** — only `search/search.html` does that. Org-scoping itself is a pure backend
concern, unrelated to the template: `OrganizationSearchLogic` (subclass of the same
`SearchLogic` engine `search.html` uses) adds `additional_fq='organization:"<name>"'`
(`ckanext-hdx_org_group/.../organization_search_logic.py`).

### 1.6 Analytics (must preserve exactly)

Both `read.html` and `custom_org.html` define identical page-level Jinja blocks:
```jinja
{% block analytics_org_name %}{{ org_dict.name }}{% endblock %}
{% block analytics_org_id %}{{ org_dict.id }}{% endblock %}
{% block analytics_came_from %}{{ analytics.analytics_came_from }}{% endblock %}
{% block analytics_supports_notifications %}{{ analytics.analytics_supports_notifications }}{% endblock %}
```
No further per-button GA data-attributes were found on header actions beyond these page-level
blocks — these four blocks are the entire analytics surface to preserve verbatim.

---

## 2. Figma Mapping

Two integrity caveats that shape how these files are used: `xl-org-page.html`'s `<style>` block is
incomplete (33 rules for 270 used classes — no layout/color/active-state CSS at all, only `:root`
vars and two popup modals), so XL styling is verified against `md-org-page.html` /
`xl-org-members-page.html` instead (both fully-defined, 0 missing classes). Also, `md-org-page.html`
and the corrected `sm-org-page.html` stack **all tabs' content** in one long page — only the
`Datasets` section of each is used below, per the task's own instruction to ignore other tabs.

### XL (`xl-org-page.html`, cross-checked against `xl-org-members-page.html`)

```
[top-bar] [navbar: search + Data/Locations/Organisations/Products + Log in]
[breadcrumb: Home / Organisations / {org.title}]
[org hero]
  [left]  {org.title} · "Member since {date}" · description (3-line clamp + "Show more")
          [CTA] "Get notified" button
  [right] logo · action row (see below) · divider · "Datasets {N}" / "Members {N}"
  [tabs]  Datasets | Activity | Members | Requested Data | Stats   (permission-gated, see §4)
[body]
  [sidebar, always visible]  Filter by: Location / Organisation (pinned chip = current org) /
                              Time period / Data type / Format / Topics / Advanced filters /
                              Show only (Active/Archived)
  [results]  "Datasets {N}" + Results-per-page + Sort-by + search box + active-filter pills
             → 10 dataset cards (org/title/description/location/date/format tags — identical
               shape to the existing v2 dataset-card component)
             → pagination
  [OUT OF SCOPE] "You might also like" cross-sell row (excluded per task scope)
[footer]
```

**Header action row** (only visible once `xl-org-members-page.html` populated it — the plain
`xl-org-page.html`/`md-org-page.html` exports leave this row's labels empty, which is what
triggered a clarifying round):
```html
<div class="text-buttons-parent">
  [Visit website] [Edit org page] [Add dataset] [Group message]
</div>
```
Each item = icon + text link, always includes "Visit website" (if `org_url` set), the other three
conditionally rendered per the permission booleans in §1.3. This directly matches
`org_actions_menu.html`'s existing conditions — just rendered inline instead of in a dropdown.

**Tabs active-state CSS** (confirmed via `xl-org-members-page.html`'s complete stylesheet):
```css
.tabs   { height: 4rem; display:flex; align-items:center; justify-content:center; padding: 0 0.5rem; }
        /* inactive: text color inherited, var(--color-darkslategray-100) #3f4748, no border */
.tabs3  { height: 4rem; border-bottom: 4px solid var(--color-royalblue); box-sizing:border-box;
          display:flex; align-items:center; justify-content:center; padding: 0 0.5rem; }
.tabs-frame { color: var(--color-gray-200); }  /* active: near-black text */
```
(Figma's own captured "active" tab varies between exports — Members in two of them — because
each export just froze whatever was selected when captured. Per the task brief, **Datasets** is
the tab that gets the active treatment in this implementation.)

### MD (`md-org-page.html`)

Hero content identical to XL. Two changes: (1) nav collapses to logo + search + hamburger; (2)
the entire filter **sidebar is replaced by a single condensed control**:
```html
<div class="dropdown"><div class="select">
  <img class="chevron-down-icon"><div class="heading-h1">Filter</div><div class="text11">(10)</div>
</div></div>
```
i.e. a "Filter (10)" button — matching exactly how the main v2 search page already collapses its
sidebar into an overlay below `@hdx-bp-xl` (1280px). No individual filter controls are inlined in
the MD markup — they belong in the (already-built) overlay.

### SM (`sm-org-page.html`, corrected export)

Hero stacks vertically: title → member-since → description+"Show more" → logo/Visit-Website/stats
card → "Get notified" CTA → tabs. Filter sidebar collapses to the same "Filter (10)" button as MD.
Dataset cards keep the same 4-field shape as the existing SM search-results card (contributor,
title, one location tag, date range) — **not** further reduced. Pagination uses the same
numbered-pager pattern as XL/MD.

One gap: the tab bar's overflow behavior at ~393px (5 labels including "Requested Data") isn't
resolved by Figma's static export — the row simply doesn't wrap, scroll, or collapse in the
markup/CSS as exported. See Open Questions.

### KPI-style cards?

No — `Datasets {N}` / `Members {N}` in the hero are a plain inline label/value pair inside one
card, not individual bordered KPI tiles (contrast with the All-Organisations list page's
`kpi-locations-card`, which is a different, unrelated pattern).

---

## 3. Component Strategy

| UI Element | Approach | Justification |
|---|---|---|
| Breadcrumb | **Reuse as-is** — `v2/components/breadcrumb.html` | `Home → Organisations → {org.title}`, standard 3-item usage identical to existing dataset-page pattern |
| Org hero | **Extend** `v2/components/page-header.html` with generic optional params (`member_since`, `header_actions`, `header_stats`) | Same integration technique as the HAPI/Signals landing pages: pass only the params the page needs, each self-gating — no mode flag. Hero metrics (title sizes, gaps, card width) inherit the dataset header defaults, no org-specific style overrides |
| Header action row | **New generic param** `header_actions` on `page-header.html`, rendered inside the existing right card | Data-driven list of `{label, href, icon_src, attrs, show}` items (Visit website / Edit org page / Add dataset / Request membership), each gated by the existing booleans from §1.3 — mirrors `org_actions_menu.html`'s conditions, rendered inline per Figma instead of in a v1 dropdown |
| Tabs bar | **New minimal component**, `v2/components/tabs.html` | No reusable tabs component exists anywhere in the v2 system today (confirmed — searched all `ckanext-hdx_theme` templates/LESS/JS and the v2 component demo page). Closest relatives (`c-anchor-links` scroll-spy, `c-button state=active` toggle) solve different problems. See §4. |
| Filters sidebar + MD/SM overlay | **Reuse as-is** — `v2/search-filters.html` | Facet-driven, already produces the exact facet dict for org-scoped search; Figma even shows the "Organisation" facet present with the current org pinned as a chip, confirming no special-casing is wanted |
| Dataset cards | **Reuse as-is** — `search/snippets/package_item_v2.html` → `v2/components/dataset-card.html` | Figma's card matches this component's fields exactly (org/title/description/location/date/formats) |
| Sort + pagination | **Reuse as-is** — `v2/search-nav-controls.html`, `v2/components/pagination.html`, `fanstatic/v2/url-nav.js` | Same components already used on the main search page; org page just needs `v2=True` threaded through |
| "Get notified" | **Reuse as-is** — `notification_platform/buttons.html` + `v2/components/drawer.html` | Already supports `object_type='organization'` at the data layer (task 051 gave the drawer chrome to every object type; only the dataset page's *trigger* UI was restyled). Org hero just needs to call it the same way `page-header.html` does |
| Number formatting | **Reuse as-is** — `h.hdx_format_number_si()` | Same helper task 049 introduced for the org-list-card; apply to both the Datasets and Members counts in the new hero |

---

## 4. Tabs Component Evaluation

**Exists or not:** Does not exist. No `c-tabs`/`hdx-tabs`/`page-nav` component anywhere in the v2
templates, LESS, JS, or the `v2/components.html` component-demo catalog page.

**Reuse vs. create:** Create — minimal, generic, permission-agnostic (the caller passes an
already-filtered list).

**Minimal API:**
```jinja
{# v2/components/tabs.html — params: items (list of {label, href, active, show=True}), extra_classes #}
{% set items = items if items is defined else [] %}
<nav class="c-tabs {{ extra_classes if extra_classes is defined else '' }}">
  {% for item in items %}
    {% if item.show is not defined or item.show %}
      <a class="c-tab {{ 'is-active' if item.active else '' }}" href="{{ item.href }}">{{ item.label }}</a>
    {% endif %}
  {% endfor %}
</nav>
```
```jinja
{# call site, in the new organization/read.html #}
{% snippet 'v2/components/tabs.html', items=[
    {'label': _('Datasets'), 'href': h.url_for('hdx_org.read', id=org_dict.name), 'active': True},
    {'label': _('Activity'), 'href': h.url_for('hdx_org.activity', id=org_dict.name)},
    {'label': _('Members'), 'href': h.url_for('hdx_members.members', id=org_dict.name), 'show': true if c.user else false},
    {'label': _('Requested Data'), 'href': h.url_for('requestdata_organization_requests.requested_data', id=org_dict.name), 'show': can_edit},
    {'label': _('Stats'), 'href': h.url_for('hdx_org.stats', id=org_dict.name)},
] %}
```
CSS: `.c-tab` — height `4rem`, centered text, no border, secondary text color; `.c-tab.is-active` —
`border-bottom: 4px solid` the v2 accent token matching Figma's `--color-royalblue` (#1862d8;
confirm exact token name in `tokens.less` at implementation time), primary/darker text color. At
SM, `.c-tabs { overflow-x: auto; }` with `.c-tab { flex-shrink: 0; }` (horizontal scroll) —
confirmed default; Figma's SM export doesn't encode a working overflow strategy for 5 tab labels,
so this is the implementation's own solution rather than a Figma-sourced one (see D10).

**Future-extension support:** Any future tab migration (e.g. Activity) just adds `{'active': True}`
to its own item and renders the same snippet — no shared-template coupling required (see the
`read_base.html` re-pointing note in §8, which is what makes this decoupling possible).

**Constraint satisfied:** UI-only for now — every non-Datasets item is a plain link to its existing,
already-working v1 route. No tab-switching JS.

---

## 5. Dataset Integration Strategy

1. The new `organization/read.html` calls `search/snippets/search_results_wrapper.html` exactly as
   v1 does today, with one change: **`v2=True` is passed unconditionally** (hardcoded in the
   template/view context, not sourced from a `?v2=true` query flag, per the "direct replacement"
   rollout decision — see Decisions Taken). This is the same mechanism `search.html` already uses
   to reach the v2 branch of `package_list.html` — just always-on here instead of gated.
2. Org-scoping is already handled entirely server-side by `OrganizationSearchLogic`
   (`additional_fq='organization:"<name>"'`) — **zero template changes needed** for scoping itself.
3. No new dataset-card, filter, sort, or pagination code. The only "adaptation for org context" is
   making sure the org page passes the same `my_c`/`search_template_data` shape
   `search_results_wrapper.html` already expects (it already does, today, in v1).
4. Figma's "Time period" / "Data type" / "Show only" filter sections are out of scope for this task
   (D12) — the existing `v2/search-filters.html` facet set is reused unchanged, with no new
   top-level dropdowns or regrouping. Any redesign of that grouping is deferred to a future task.

---

## 6. Permissions Mapping

| Action | Permission check | Preserved from |
|---|---|---|
| Edit org page | `can_edit` → `organization_update` | `org_actions_menu.html`, unchanged |
| Add dataset | `can_create_dataset` → `package_create`; click still calls existing `contributeAddDetails(null, 'org')` JS | `org_actions_menu.html`, unchanged |
| Group message | `display_group_message` (current user is a member of this org) | `base_actions_menu.html`, unchanged |
| Get notified | `hdx_supports_notifications('organization', ...)` business rule (not an ACL) | `notification_platform/buttons.html`, unchanged |
| Members tab visibility | `c.user` (logged in) | v1 `read.html` tab gate, unchanged |
| Requested Data tab visibility | `can_edit` → `organization_update` | same check as Edit, unchanged |
| Visit website | no permission — hidden only if `org_url` is empty | `org_dict.org_url`, unchanged |

No new permission logic anywhere in this task — every gate above is an existing boolean computed
by `OrgReadLogic`/`OrgMetaDao`, threaded into the new template unchanged.

---

## 7. Responsive Strategy

| Breakpoint | Hero | Tabs | Filters | Dataset list |
|---|---|---|---|---|
| XL (≥ 80rem) | Title/description/CTA left, logo+actions+stats card right, side by side | Full label row, Datasets active | Full sidebar, always visible | Cards + pagination, standard grid |
| MD (< 80rem) | Same structure as XL (no stacking evidenced in Figma at this width) | Same row (may need overflow handling — see Open Questions) | Collapses to single "Filter (N)" button → existing MD/SM overlay | Same cards, same pagination |
| SM (< 48rem) | Stacks vertically: title → meta → description → logo/actions/stats card → CTA → tabs | Same row, proposed horizontal scroll | Same "Filter (N)" button → overlay | Same cards (4-field shape preserved, not reduced), same pagination |

This is the same sidebar/overlay breakpoint contract already established for the main search page
(`@hdx-bp-xl` = 1280px) — reused verbatim, not redefined.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| **Breaking permissions logic** | Reuse the exact existing booleans (§1.3/§6); no new checks written |
| **Duplicating the dataset list** | Explicitly reuse `search_results_wrapper.html` unchanged, just with `v2=True` always on (§5) |
| **Inconsistent tabs implementation** | One shared `v2/components/tabs.html`, one permission-gated item list, used identically regardless of org type — fixes the existing 2-tab-vs-5-tab v1 drift (§1.4) |
| **Regression in filters** | Zero changes to `v2/search-filters.html`; org-scoping stays a backend `additional_fq` concern |
| **Breaking out-of-scope tabs (Members/Stats/Activity/Requested Data)** — *found during audit, not in original brief* | Four templates extend the old `organization/read.html` (`members.html`, `stats.html`, `activity_stream.html`, `requestdata/organization_requested_data.html`) and inherit their entire v1 header from it. Fix: the old `read.html` is kept verbatim as `organization/read_v1_base.html` and only the four `{% extends %}` lines are repointed to it — zero visual/behavioral change to those tabs; each copy gets deleted as its tab is migrated in future tasks (D14). |
| **Custom-org feature regression** (visualization embed, follow button, brand theming) | Explicitly accepted and scoped out per the Decisions Taken below — not a silent regression, a deliberate, Figma-matching simplification |
| **Temporary visual inconsistency navigating Datasets → Activity/Members/Stats** | Unavoidable with incremental tab-by-tab migration (same pattern used elsewhere in this v2 project); those tabs keep the v1-styled header (via `custom_org_header.html`/standard header, whichever the org needs) until each gets its own future migration |

---

## 9. Edge Cases

| Case | Expected behavior |
|---|---|
| Org with zero datasets | Preserve v1 message ("There are no datasets currently uploaded to this organisation.") + "Add Data" link, styled with v2 tokens |
| Org without a website (`org_url` empty) | Hide the "Visit website" link entirely (cleaner than v1's current self-referential fallback to the org's own page — flagged as a minor, low-risk improvement, not a functional change worth a blocking question) |
| No permissions (anonymous/non-member visitor) | Header action row shows only "Visit website" (if set); Members and Requested Data tabs hidden; matches `xl-org-page.html`'s 3-tab (Datasets/Activity/Stats) capture exactly |
| Notifications disabled for this org | Hide "Get notified" CTA entirely, per existing `hdx_supports_notifications()` result |
| Very long org name | Title wraps naturally (no clamp), consistent with how `page-header.html` handles dataset/resource titles today |
| Very long description | 3-line clamp + "Show more"/"Show less" via existing `clamped-text.js`, same pattern as `page-header.html` and the org-list-card |
| `is_custom = True` org (branded partner) | Renders through the exact same unified template as any other org — logo, hero, tabs, action row all identical; only the logo image source differs (its configured square/rect image vs. the default) |

---

## Decisions Taken

| # | Decision | Rationale |
|---|---|---|
| D1 | Figma gap (task-named files `xl-org-page.html`/`md-org-page.html`/`sm-org-page.html` did not exist at task start) resolved by the requester adding the real exports mid-planning; doc drafted against the final, corrected set of 4 files | — |
| D2 | Both standard AND custom/branded orgs unify into ONE v2 template; the separate mobile "light" theme is retired outright | Explicit requester instruction; v2 is responsive so the light theme is redundant |
| D3 | Tabs link to existing v1 routes (Activity/Members/Stats/Requested Data) with new v2 styling; only Datasets gets full v2 content | Preserves working navigation; avoids dead links |
| D4 | Direct template replacement, no `?v2=true` gate | Matches the 048/049 list-page precedent; chosen over the dataset-search-style gradual gate |
| D5 | Custom-org visualization/embed block dropped | Not shown in any Figma export; its "Embed data" popup is already broken in v1 today |
| D6 | Custom-org Follow button dropped everywhere | Not shown in any Figma export/card variant; matches how standard orgs already behave |
| D7 | Custom-org brand color theming (highlight color, logo background color) dropped; all orgs render on standard v2 tokens | Not shown in any Figma export; required by the task's "MUST use v2 design tokens" / "MUST match Figma exactly" constraints |
| D8 | Dead "Key Figures" topline-KPI backend computation removed (not resurrected) | Already fully commented out of the v1 UI; reviving it would be new scope, not preservation |
| D9 | Header action row (Visit website / Edit org page / Add dataset / Group message) rendered inline per Figma, not as a v1-style dropdown | Directly confirmed by `xl-org-members-page.html` |
| D10 | SM tabs overflow handled with horizontal scroll (`.c-tabs { overflow-x: auto; }`, `.c-tab { flex-shrink: 0; }`) | Confirmed by the requester; Figma's SM export doesn't encode a working overflow strategy for 5 tab labels at ~393px, so this is the implementation's own solution |
| D11 | No pre-implementation `organization_list` query for live `custom_org=True` count | Requester chose to skip it — D5-D7 already accept the custom-org feature regression regardless of how many orgs are affected, so the count doesn't change the plan |
| D12 | Figma's "Time period" / "Data type" / "Show only" filter sections are out of scope for this task; the existing `v2/search-filters.html` facet set is reused unchanged, with no new top-level dropdowns or regrouping | Requester decision; avoids scope creep into a filter-layout redesign not required by this task |
| D13 | "Request Membership" is included in the header action row (gated on the existing `allow_req_membership`), rendered as "Request membership" | Its absence from Figma is a permission-state artifact — the populated export was captured as an org admin, who can never see it; dropping it would remove the page's only membership-request entry point |
| D14 | The four tab templates that extended the old `read.html` (`members.html`, `stats.html`, `activity_stream.html`, `requestdata/organization_requested_data.html`) now extend `organization/read_v1_base.html`, a verbatim copy of the old file | They inherit their entire v1 header from that base; the copy preserves their rendering exactly with a 1-line change each |
| D15 | The mobile "light" theme (`/m/organization/*`) is NOT retired in this task — `light_organization.py` and `light/organization/*` are untouched; retirement is a separate follow-up | Requester decision; keeps this change focused on the org page itself |
| D16 | Tab label is "Activity" (Figma) rather than v1's "Activity Stream"; the "Member since" date keeps the `h.render_datetime()` default format ("May 25, 2017") used by the v2 org-list card rather than Figma's "25 May 2017" | Requester decisions, one per Figma-vs-convention conflict |
| D17 | The hero reuses `v2/components/page-header.html` extended with generic self-gating params (`member_since`, `header_actions`, `header_stats`) — no mode flag, landing-page integration style; hero metrics inherit the dataset header defaults with no org-specific style overrides; the hero band border is a single `--hdx-neutral-1` at all breakpoints; the logo uses the component's `object-fit: contain` | Requester decisions during implementation review |
| D18 | "Group message" is not part of this task (no action link, no popups) — a separate implementation will cover it. The "Add dataset" / empty-state "Add Data" links keep their v1 `contributeAddDetails()` onclick but `contribute.js` is not bundled on v2 pages yet — the contribute flow is also tackled separately | Requester decision |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/read.html` | Replaced with v2 template; extends `v2/page.html` |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/read_v1_base.html` | New — verbatim copy of the old `read.html`, extension target for the four out-of-scope tab templates (D14) |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/members.html`, `stats.html`, `activity_stream.html`, `requestdata/organization_requested_data.html` | `{% extends %}` repointed to `organization/read_v1_base.html` — no other change |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/custom/custom_org.html` | No longer rendered — the read route renders the unified template for custom orgs too; `custom_org_header.html`/`custom_style.html` and the `custom_members.html`/`custom_stats.html`/`custom_activity_stream.html` wrappers untouched (still used by out-of-scope tabs) |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/page-header.html` | Extended with generic `member_since` / `header_actions` / `header_stats` params (D17) |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/tabs.html` | New minimal tabs snippet |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/page-header.less` | `__member-since`, `__card-actions`, `__card-stats` element styles added |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/tabs.less` | New |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/org-page.less` | New — hero band border + empty state only |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` | `v2-org-page-styles` bundle added; `v2/components/tabs.css` added to `v2-components-styles` |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py` | `read()`: single unified path for standard and custom orgs; `org_meta` passed into the template context |
