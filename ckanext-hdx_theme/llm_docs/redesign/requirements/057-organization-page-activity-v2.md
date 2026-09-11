# 057 — Organization Page (Activity Tab): v2 Migration

**Scope:** Migrate the Organization page's **Activity** tab (`/organization/activity/<name>`) to
v2 — reuse the org page-header/tabs shell from task 056, and render the activity feed through the
existing v2 activity-item component instead of the current v1 FA-icon-stack list. Standard AND
custom/branded orgs converge on the same template (matching 056's `read()` precedent).
**Excluded:** Datasets tab (056, done), Stats tab, Members tab, Requested Data tab, HDX Connect;
any activity **data-model**/action changes (no new fields, no new activity types, no schema
changes); GA/analytics instrumentation on activity items (D4 — stays consistent with the existing
gap on the dataset page); AJAX/infinite-scroll pagination (D1 — server-rendered link only).
**Figma sources:** `xl-org-activity-page.html`, `md-org-page.html` (Activity tab section only),
`sm-org-page.html` (Activity tab section only) — the latter two are full-page exports stacking
every tab's content; per the task brief, only their Activity sections are used below.

---

## Context

Task 056 gave the Organization page a v2 hero (`page-header.html`) and a new minimal
`v2/components/tabs.html`, but scoped its actual tab *content* migration to Datasets only. The
other four tabs — Activity included — still render through `organization/read_v1_base.html`, a
verbatim copy of the pre-056 template preserved so those tabs keep working unchanged until each is
migrated in turn (056 §8, D14). This doc scopes that next migration for Activity.

Unlike Datasets, this isn't a "build from scratch" job: a v2 activity-feed component
(`c-activity-item`) and its type-dispatch orchestrator already exist and are fully wired up — just
only for the dataset page's AJAX accordion (task 046). The core question this doc answers is
whether that existing component can be reused as-is for the org page (it can, visually) and what
has to change structurally to wire it in without duplicating the 23-type dispatch logic.

---

## 1. Existing Implementation Audit

### 1.1 Template inheritance (today)

```
organization/read_v1_base.html                    verbatim copy of pre-056 read.html (v1 shell/header/tabs)
  └─ organization/activity_stream.html             STANDARD org Activity tab
       └─ organization/custom_activity_stream.html CUSTOM org Activity tab
            (extends activity_stream.html; overrides `item_title_contrib` to swap in
             custom_org_header.html + `custom_styles` for brand theming)

organization/snippets/activity_stream.html         HDX's dispatcher — a near-duplicate of core's
                                                    ckanext/activity/templates/snippets/stream.html
                                                    (same macro/dispatch pattern, HDX-specific
                                                    `actor()` macro via `h.hdx_linked_username`)
```

`organization/activity_stream.html` (full contents):
```jinja
{% extends "organization/read_v1_base.html" %}
{% block subtitle_suffix %}{{ _('Activity Stream') }}{% endblock %}
{% block primary_content_inner %}
  <h2 class="hide-heading">{% block page_heading %}{{ _('Activity Stream') }}{% endblock %}</h2>
  {% block activity_stream %}
    {% snippet 'organization/snippets/activity_stream.html',
        activity_stream=group_activity_stream, id=org_dict.id, object_type='organization' %}
  {% endblock %}
{% endblock %}
```
Note this pulls in `read_v1_base.html`'s entire v1 header/tab-bar — the Activity tab today is
visually disconnected from the v2 hero a visitor just saw on the Datasets tab.

### 1.2 Routing / view (today) — the one `is_custom` branch task 056 did NOT unify

`ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py:237-278`:
```python
def activity(id):
    return activity_offset(id)

def activity_offset(id, offset=0):
    org_meta = org_meta_dao.OrgMetaDao(id, g.user, g.userobj)
    org_meta.fetch_all()
    org_dict = org_meta.org_dict
    ...
    group_activity_stream = get_action('organization_activity_list')(
        context, {'id': org_dict['id'], 'offset': offset})
    extra_vars = {'org_dict': org_dict, 'org_meta': org_meta,
                  'group_activity_stream': group_activity_stream}
    if org_meta.is_custom:
        template = 'organization/custom_activity_stream.html'
    else:
        template = lib_plugins.lookup_group_plugin('organization').activity_template()
    return render(template, extra_vars)

hdx_org.add_url_rule(u'/activity/<id>', view_func=activity)
hdx_org.add_url_rule(u'/activity/<id>/<int:offset>', view_func=activity_offset, defaults={'offset': 0})
```
Unlike `read()` (unified by 056 into one template for standard+custom orgs, `views/
organization.py:67-90`), `activity_offset()` **still branches on `org_meta.is_custom`** to pick
between two templates. Per D8, this branch is removed: the view renders one unified template
regardless of `is_custom`, the same template-selection-only edit 056 made to this same file for
`read()`.

The `offset` query param and `organization_activity_list` action are already fully functional —
**no new route or action is needed.**

### 1.3 Pagination (today) — action supports it, template never surfaces it

`organization_activity_list`'s limit defaults from `ckan.activity_list_limit`
(`ckanext/activity/logic/schema.py`, `default_pagination_schema()` composed into the org/group
activity schema — same `configured_default("ckan.activity_list_limit", 31)` validator used across
all activity-list schemas), upper-bounded by `ckan.activity_list_limit_max` (default 100). So
**each `activity_offset` call returns up to 31 items** unless the site config overrides it.

Core CKAN's own generic template renders `ckanext/activity/templates/snippets/pagination.html` —
"Newer activities" / "Older activities" buttons — but **HDX's `organization/activity_stream.html`
never includes it**, and never computes `newer_activities_url`/`older_activities_url`. Net effect:
**the org Activity tab has no pagination UI in production today**, even though the `/activity/
<id>/<offset>` route works if hit directly.

There is also a generic v2 numbered pager, `v2/components/pagination.html`, already used elsewhere
(org list page, search page — task 033), but it is **not used anywhere in the activity feed today**.

### 1.4 v2 activity component (today) — dataset-page-only

| File | Role |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/activity-item.html` | `c-activity-item` — single reusable timeline item (dot+line, actor/action/subject/time) |
| `.../templates/v2/activity-stream.html` | Orchestrator: loops `activity_stream`, dispatches all **23** CKAN activity types via one `{% if/elif %}` chain, calls `activity-item.html` per item, wraps in `.c-activity-stream` |
| `.../helpers/actions.py:737-748` (`hdx_package_activity_stream`) | AJAX action: `package_activity_list(limit=7)` → renders `v2/activity-stream.html` server-side → returns HTML |
| `.../fanstatic/v2/pages/dataset.js` (`fetchActivitiesIfNeeded`) | On the dataset page's collapsible Activity accordion first-open, POSTs to `hdx_package_activity_stream`, injects the HTML |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/activity-item.less` | `.c-activity-item` (`__timeline/__line/__dot/__content/__actor/__action/__time`) + `.c-activity-stream` (flex column, `__empty` state) |

**Crucially, the dispatch chain in `v2/activity-stream.html` is already type-generic, not
dataset-specific** — it already has branches for `new/changed/deleted organization`,
`new/changed/deleted group`, `new/changed user`, `added/removed tag`, and all three `follow *`
types, not just package/resource events:
```jinja
{% elif activity.activity_type == 'changed organization' %}
  {% set _ns.action_text   = _('updated the organization') %}
  {% set _ns.subject_label = activity.data.group.title if activity.data.group else _('unknown') %}
  {% set _ns.subject_href  = h.url_for('organization.read', id=activity.object_id) %}
```
This means **no new type-mapping logic is needed** to serve the org Activity tab — the file just
needs to be reachable from the org template without duplicating it (see §4, §6, D2).

Empty state: `v2/activity-stream.html` renders `<p class="c-activity-stream__empty">{{ _('No
recent activity for this dataset.') }}</p>` when the list is empty — dataset-specific copy that
gets the org-appropriate equivalent from D10 (see §9).

---

## 2. Figma Mapping

### XL (`xl-org-activity-page.html`)

```
[org hero — identical to 056's Datasets-tab hero]
[tabs — Activity active]
[.activity-accordion-parent]  border-top 1px solid whitesmoke, padding 2rem 3rem 3rem
  [.header]  "Activity" (bold) + chevron icon (display:none in this mock)
  [.dataset-page-activity-item] × 5, class shared with the standalone activity-item.html export:
    [timeline col]  vertical .line (1px, --color-lightgray) + .dot (12px circle, royalblue fill,
                     positioned top:1.313rem so it aligns with the first text line)
    [content col]   .user (bold, 14px, link) → .update-type (regular, 14px, "updated the dataset "
                     + underlined dataset link) → .time (12px, gray, "42 minutes ago")
  [.text-link7]  "Load more" — plain text link, 12px, gray, NOT a numbered pager, NOT prev/next buttons
```
Every one of the 5 mocked items uses the exact same copy (`hdx_bot_fs_check updated the dataset
HDX HAPI - Coordination & Context: Funding · 42 minutes ago`) — **no activity-type variety is shown
anywhere in Figma.** Type coverage must be sourced from the existing dispatch (§1.4), not from the
mockup.

This layout — timeline dot/line, bold actor, action sentence, underlined subject, small timestamp
— is essentially a 1:1 match for the existing `c-activity-item` component's markup and CSS classes
(`__timeline/__line/__dot`, `__actor`, `__action`, `__time`). No structural mismatch found.

### MD (`md-org-page.html`, Activity section only)

Same item markup/copy as XL. The one difference: the content wrapper has `padding: 0 0 0
15.375rem` — a ~246px **left indent**, aligning the list under the right-hand content column
(matching the org page's two-column layout at this breakpoint, same pattern the Datasets tab
already uses for its filter-collapse). Section header uses a `.chevron-up-icon` image variant of
the same non-functional chevron seen at XL. Ends with the same "Load more" link style.

### SM (`sm-org-page.html`, Activity section only)

Notably different treatment: the whole activity block sits inside a **bordered card**
(`border: 0.5px solid var(--color-lightgray)`, `padding: 1.5rem 1rem 2rem`) rather than a
borderless full-bleed section, with **symmetric** horizontal padding (`0 6.25rem`, i.e. 100px each
side) centering the timeline inside the card. This is a deliberate boxed/card treatment for the
narrow mobile width, distinct from both XL's full-bleed and MD's asymmetric left-indent. Ends with
the same "Load more" link.

### Section heading / chevron

All three breakpoints style the "Activity" section title with a chevron icon matching the dataset
page's collapsible-accordion header pattern — but per D3, this tab has no other content to collapse
against, so the heading renders as a static title with no toggle behavior (chevron icon omitted
entirely rather than rendered non-functional).

---

## 3. Activity Component Evaluation

**Current capabilities** (`v2/components/activity-item.html`):
```jinja
{# Required: actor_href, actor_label, action_text, timestamp
   Optional: subject_label (default ''), subject_href (default ''), extra_classes (default '') #}
```
Renders: timeline dot/line (`aria-hidden`) + actor link (bold) + action text + optional subject
link + relative timestamp (`h.time_ago_from_timestamp`, full datetime in `title=`).

**Gaps vs. Figma:** none found. Every visual element Figma shows (timeline dot/line, bold actor,
action sentence, underlined subject, small gray timestamp) already exists in the component as-is,
at the same relative sizing/spacing. Figma's per-breakpoint padding differences (§2) are container-
level concerns, not component-level — they belong on whatever wraps the activity list on the org
page, not inside `c-activity-item` itself.

**Extension strategy:** **none needed.** `c-activity-item` is reused completely unchanged. The
only real work is upstream of it — getting the org page's activity list rendered through the
existing dispatcher (§4) instead of the v1 FA-icon-stack macros.

---

## 4. Activity Rendering Strategy

1. Per D2/D6, the dispatch orchestrator `package/snippets/activity_stream_v2.html` is **relocated**
   to `v2/activity-stream.html` (root of `v2/`, alongside `header.html`/`footer.html`/`page.html` —
   not nested under `v2/components/` — the file was simply misfiled under `package/` when built for
   task 046). Its **one existing caller**,
   `helpers/actions.py:744` (`hdx_package_activity_stream`), is updated to the new path. No logic
   inside the file changes.
2. The new org Activity v2 template calls it exactly the way the dataset page does:
   ```jinja
   {% snippet 'v2/activity-stream.html',
       activity_stream=group_activity_stream, id=org_dict.id, object_type='organization' %}
   ```
   using the `group_activity_stream` variable the view already provides today (`views/
   organization.py:271`) — **no new view-layer data shape is needed**, just a new template
   consuming the existing `extra_vars`.
3. Because the dispatcher is already type-generic (§1.4), no new `{% elif %}` branches are required
   to support org-relevant activity types (org edits, dataset changes within the org, tag/follow
   events). One caveat: CKAN has no `new/changed/deleted membership` activity type — membership
   changes (a user joining/leaving an org) are not tracked activities in this system today, and
   that's a pre-existing platform constraint, not a gap introduced by this task.
4. Empty state: reuse the same `<p class="c-activity-stream__empty">` pattern, with the
   org-appropriate copy from D10 instead of the dataset-specific string.

---

## 5. Pagination Strategy

Per D1: a plain **server-rendered "Load more" link**, not AJAX-append and not the generic numbered
`v2/components/pagination.html`.

- **Next-offset link:** `h.url_for('hdx_org.activity_offset', id=org_dict.name, offset=offset + activity_stream|length)` —
  no backend/action change needed since `activity_offset()` already accepts `offset` (§1.2).
- **Has-more heuristic:** show the link only when `activity_stream|length == <configured limit>`
  (31 by default, §1.3) — i.e., a full page suggests there may be more; a short/empty page means
  we've reached the end. This is a **frontend-only heuristic** (D5) — deliberately chosen to avoid
  any backend/action change (task brief excludes those) — with a known, accepted edge case: if the
  org has *exactly* a multiple of the limit's worth of activity, one extra "Load more" click will
  land on an empty page.
- Each click is a full page navigation to `/organization/activity/<name>/<offset>`, re-rendering
  the whole Activity tab template with the new offset baked in — consistent with how the route
  already behaves today, just now actually reachable from the UI.
- Forward-only: no "Newer activities" back-navigation is added (D7) — matches Figma exactly, which
  shows a single forward "Load more" link and no back-navigation UI.

---

## 6. Component Strategy

| UI Element | Approach | Justification |
|---|---|---|
| Breadcrumb | **Reuse as-is** — `v2/components/breadcrumb.html` | Same 3-item usage as the Datasets tab (056 §Component Strategy) |
| Org hero | **Reuse as-is** — `v2/components/page-header.html` | Already extended by 056 with everything the org page needs (`member_since`, `header_actions`, `header_stats`); no new params required for Activity. (`header_stats` is no longer passed here — see 056's "KPI-style cards?" — the hero no longer shows a Datasets/Members count.) |
| Tabs bar | **Reuse as-is** — `v2/components/tabs.html`, mark `Activity` item `active: true` | Same `items` list already defined in `organization/read.html:110-117` (or its Activity-tab equivalent) — no component change, just which item gets `active` |
| Activity item | **Reuse as-is** — `v2/components/activity-item.html` (`c-activity-item`) | §3 — visually matches Figma exactly, zero extension needed |
| Activity dispatcher | **Relocate**, don't duplicate — `package/snippets/activity_stream_v2.html` → `v2/activity-stream.html` (D2, D6) | Already generic across all 23 types (§1.4/§4); relocating avoids a second copy of 23 type-branches while fixing the semantically-odd "package" naming for an org-page consumer |
| Section heading | **New, minimal** — static title, no accordion behavior (D3) | Figma's chevron styling doesn't apply once there's no sibling content to collapse against |
| Pagination | **New, minimal** — plain "Load more" anchor (D1, §5) | No existing pattern matches Figma's link styling; too small a UI element to justify pulling in the generic numbered pager or new JS |

---

## 7. Responsive Strategy

| Breakpoint | Section container | Activity item | "Load more" |
|---|---|---|---|
| XL (≥ 80rem) | Full-bleed, `border-top`, `padding: 2rem 3rem 3rem` | Full-width timeline | Plain text link, left-aligned under list |
| MD (< 80rem) | Same full-bleed container | Timeline indented ~246px left (aligns under the two-column content area, same pattern as the Datasets tab's filter-collapse column) | Same link style |
| SM (< 48rem) | Boxed card: `border: 0.5px solid`, `padding: 1.5rem 1rem 2rem` | Timeline centered via symmetric `0 6.25rem` padding | Same link style |

Tabs-row overflow behavior at SM is **not re-decided here** — it reuses 056's existing solution
(`.c-tabs { overflow-x: auto }` / `.c-tab { flex-shrink: 0 }`, doc 056 §4/D10), since the tab bar
itself doesn't change between tabs.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Breaking the dataset page's Activity accordion when relocating the shared dispatcher (D2) | Single known call site (`helpers/actions.py:744`); update it in the same change that moves the file; no logic inside the file is touched |
| `activity_offset()`'s `is_custom` branch unified into one template call (D8) leaves `custom_activity_stream.html` uncalled from this route | Accepted per D9 — the file is kept in place (unused/orphaned by this route) rather than deleted, matching the precedent of keeping superseded templates around until a dedicated cleanup pass |
| Missing activity types on the org feed | Not expected — the dispatcher is already generic and covers all 23 types (§1.4); confirmed by direct code audit, not inferred |
| "Load more" dead-end click when activity count is an exact multiple of the page limit (§5) | Documented as a known, accepted edge case (D5); not a blocking defect either way (worst case: one extra click shows an empty page) |

---

## 9. Edge Cases

| Case | Expected behavior |
|---|---|
| Org with zero activity | Empty-state message: *"No recent activity for this organization."* (D10), same `.c-activity-stream__empty` pattern as the dataset page |
| Activity referencing a deleted dataset/org/resource | Already guarded in the existing dispatcher (`activity.data.package.title if activity.data.package else _('unknown')`, etc.) — no new handling needed |
| Mixed activity types in one list | No visual differentiation between types today (single timeline-dot style for all) — same as the dataset page's existing v2 behavior, not a new gap introduced here |
| Very long actor username or dataset title | `c-activity-item` has no truncation/clamp — text wraps naturally, consistent with how it already behaves on the dataset page |
| Anonymous/logged-out visitor | No permission gate exists on activity visibility today (org activity streams are public); unchanged by this migration |
| `is_custom = True` org (branded partner) | Per D8 (mirroring 056's `read()` precedent), renders through the same unified template as any other org |

---

## Decisions Taken

| # | Decision | Rationale |
|---|---|---|
| D1 | Pagination is a server-rendered "Load more" anchor to the next offset (full page reload) — not AJAX-append, not the generic numbered `v2/components/pagination.html` | Matches Figma's plain-link styling with no new JS; requester's explicit choice over the AJAX and generic-pager alternatives |
| D2 | The type-dispatch orchestrator `package/snippets/activity_stream_v2.html` is relocated to `v2/activity-stream.html`; the dataset page's one call site (`helpers/actions.py:744`) is updated to match. No dispatch logic is duplicated. | Requester's explicit choice over calling the package-scoped file in place from the org template |
| D3 | The "Activity" section heading is a static title with no collapse/accordion behavior, despite Figma styling it like the dataset page's collapsible sections | The Activity tab is a full standalone page — collapsing its only content would hide everything with nothing else visible |
| D4 | No GA/analytics data-attributes are added to activity items in this task | Requester's explicit choice; stays consistent with the pre-existing gap on the dataset page's `c-activity-item`, flagged rather than silently perpetuated |
| D5 | The "Load more" has-more heuristic stays frontend-only (compare returned count to the configured limit) rather than adding a `has_more` boolean computed view-side | Requester's explicit choice; keeps the task within its "no backend/data changes" scope. Accepted edge case: an org with exactly a multiple of the limit's worth of activity gets one dead-end click on an empty page |
| D6 | The relocated dispatcher (D2) lives at `v2/activity-stream.html` — root of `v2/`, alongside `header.html`/`footer.html`/`page.html` — not nested under `v2/components/` | Requester's explicit choice over the doc's original `v2/components/activity-stream.html` proposal |
| D7 | Pagination is forward-only "Load more"; no "Newer activities" back-navigation is added | Matches Figma exactly — it shows only a single forward link, no back-navigation UI |
| D8 | `activity_offset()`'s `is_custom` branch (§1.2) is unified: the view renders one template regardless of `is_custom`, mirroring 056's `read()` precedent | Requester's explicit choice; template-selection-only edit to `views/organization.py`, consistent with how 056 edited the same file for `read()` |
| D9 | `custom_activity_stream.html` (and its `custom_org_header.html` override) is **kept in place**, not deleted, even though D8 means this route no longer calls it | Requester's explicit choice — left as unused/orphaned code for now rather than deleted; matches the precedent of preserving superseded templates (e.g. `read_v1_base.html`, 056 D14) until a dedicated cleanup pass |
| D10 | Empty-state copy for zero-activity orgs is *"No recent activity for this organization."* | Requester's explicit choice; mirrors the dataset page's existing copy pattern (*"No recent activity for this dataset."*) with the noun swapped |

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/package/snippets/activity_stream_v2.html` | Relocated to `v2/activity-stream.html` (D2, D6); contents unchanged |
| `ckanext-hdx_theme/ckanext/hdx_theme/helpers/actions.py:744` | `hdx_package_activity_stream` updated to render the new relocated path |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/activity_stream.html` | Replaced with a v2 template: extends `v2/page.html`, reuses `page-header.html` + `tabs.html` (Activity active), calls the relocated activity-stream snippet, adds the "Load more" link, empty-state copy per D10 |
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/organization/custom_activity_stream.html` | Kept in place, unused/orphaned by this route (D9) — no edit |
| `ckanext-hdx_org_group/ckanext/hdx_org_group/views/organization.py` (`activity_offset`) | `is_custom` branch removed; renders the new unified v2 template for all orgs (D8) |
| `hdx-styles/src/common/less/v2/pages/org.less` (or 056's equivalent) | New section-level styles for the Activity list container's per-breakpoint padding (§7); no changes to `activity-item.less` — the component itself is unchanged |
