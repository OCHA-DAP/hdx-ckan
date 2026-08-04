# Dataset Page – Activity Section (v2)

**Scope:** Activity section on the dataset page (`hdx_read.html`) — `c-activity-item` component + `activity_stream_v2.html` snippet

---

## Context

The v2 dataset page already has an activity accordion shell in
`templates/package/hdx_read.html` (lines 465–477). It is collapsible, starts closed
(`aria-expanded="false"`), and currently calls the **v1** `activity_stream.html` snippet,
which renders `<li>` elements with FontAwesome icon stacks. That markup is incompatible
with the Figma redesign.

The Figma design (`figma_exports/activity-item.html`) replaces FA icons entirely with a
**timeline** metaphor: a vertical line with a blue dot per item. All activity types
use the **same visual structure** — only the action text and subject link differ.

The activity data is loaded via **AJAX**, not server-side rendering. When the accordion is
opened, `dataset-page.js` calls `/api/3/action/hdx_package_activity_stream`, which renders a
Jinja snippet server-side and returns raw HTML. That HTML is injected into
`.dataset-activity-wrapper` via `$(wrapper).html(response.result)`. The `hdx_activities`
template variable in `dataset.py` is always `[]` and the static `{% snippet %}` call in
`hdx_read.html` is a dead call — it only renders an empty-state message at page load.

The real rendering path is: accordion opens → JS → API action (`helpers/actions.py:744`) →
renders `activity_stream_v2.html` → returns HTML → JS injects into wrapper.

---

## 1. Existing Activity Audit

### Template locations

| File | Purpose | Touched? |
|------|---------|---------|
| `ckanext-hdx_theme/.../templates/package/snippets/activity_stream.html` | v1 dispatcher with macros | ❌ Do not modify |
| `ckanext/activity/templates/snippets/activities/*.html` | 23 per-type v1 item templates | ❌ Do not modify |
| `ckanext-hdx_theme/.../templates/snippets/activity_item.html` | Legacy dashboard item | ❌ Do not modify |
| `ckanext-hdx_theme/.../templates/package/hdx_read.html` (line 474) | Dataset page — calls the snippet | ✅ Change snippet name only |

### v1 item HTML structure (for reference)

```html
<li class="item changed-package">
  <span class="fa-stack fa-lg">
    <i class="fa fa-circle fa-stack-2x icon"></i>
    <i class="fa fa-sitemap fa-stack-1x fa-inverse"></i>
  </span>
  {actor} updated the {dataset_type} {dataset}
  <br />
  <span class="date" title="...">42 minutes ago</span>
</li>
```

### v1 dispatcher logic

`activity_stream.html` defines Jinja2 macros — `actor()`, `dataset()`, `organization()`,
`user()`, `group()` — and routes each activity to a type-specific template via:

```jinja2
{% snippet "snippets/activities/{type}.html", "snippets/activities/fallback.html",
   activity=activity, can_show_activity_detail=False, ah={...} %}
```

The `ah` dict passes the macros into each type template.

### Activity data structure

Each activity dict in `activity_stream` has:

```python
{
    'id':            str,           # UUID
    'timestamp':     datetime,
    'user_id':       str,           # actor's CKAN user ID
    'user_name':     str,           # actor's display name (may be absent in older CKAN)
    'object_id':     str,           # ID of the affected object
    'activity_type': str,           # e.g. "changed_package", "new_resource"
    'data': {
        'package':  { 'id', 'title', 'type', ... },   # if applicable
        'group':    { 'id', 'title', ... },             # if applicable
        'resource': { 'id', 'name', 'package_id', ... },# if applicable
        'tag':      { 'name', ... },                    # for added_tag / removed_tag
    }
}
```

### Known 23 activity types

```
new_package        changed_package    deleted_package
new_resource       changed_resource   deleted_resource
new_resource_view  changed_resource_view  deleted_resource_view
new_organization   changed_organization   deleted_organization
new_group          changed_group          deleted_group
new_user           changed_user
added_tag          removed_tag
follow_dataset     follow_user            follow_group
```

Plus a `fallback.html` for unknown types.

### Existing v2 activity files

- `templates/v2/components/activity-card.html` — homepage promotional card; **unrelated**
  to the activity stream items. Do not confuse the two.
- `hdx-styles/src/common/less/v2/components/activity-card.less` — styles for the above

No v2 activity stream component or item snippet exists yet.

---

## 2. Activity Types Mapping

All 23 types map to the **same `c-activity-item` component**. The differences are only
`action_text` (plain) and `subject_label` / `subject_href`.

For **deleted** types the subject is shown as plain text (object no longer exists in CKAN).
For **`new_user` / `changed_user`** there is no subject at all.

| activity_type | action_text | subject_label source | subject_href | link? |
|---|---|---|---|---|
| `new_package` | "created the dataset" | `activity.data.package.title` | `pkg.read` via `object_id` | ✅ |
| `changed_package` | "updated the dataset" | `activity.data.package.title` | `pkg.read` via `object_id` | ✅ |
| `deleted_package` | "deleted the dataset" | `activity.data.package.title` | — | ❌ |
| `new_resource` | "added the resource" | `activity.data.resource.name` | `resource.read` | ✅ |
| `changed_resource` | "updated the resource" | `activity.data.resource.name` | `resource.read` | ✅ |
| `deleted_resource` | "deleted the resource" | `activity.data.resource.name` | — | ❌ |
| `new_resource_view` | "created resource view" | view title from `activity.data` | `resource.read` with view | ✅ |
| `changed_resource_view` | "updated resource view" | view title from `activity.data` | `resource.read` with view | ✅ |
| `deleted_resource_view` | "deleted resource view" | view title from `activity.data` | — | ❌ |
| `new_organization` | "created the organization" | `activity.data.group.title` | `organization.read` via `object_id` | ✅ |
| `changed_organization` | "updated the organization" | `activity.data.group.title` | `organization.read` via `object_id` | ✅ |
| `deleted_organization` | "deleted the organization" | `activity.data.group.title` | — | ❌ |
| `new_group` | "created the group" | `activity.data.group.title` | `group.read` via `object_id` | ✅ |
| `changed_group` | "updated the group" | `activity.data.group.title` | `group.read` via `object_id` | ✅ |
| `deleted_group` | "deleted the group" | `activity.data.group.title` | — | ❌ |
| `new_user` | "signed up" | — | — | — |
| `changed_user` | "updated their profile" | — | — | — |
| `added_tag` | "added the tag" | `activity.data.tag.name` | — | ❌ |
| `removed_tag` | "removed the tag" | `activity.data.tag.name` | — | ❌ |
| `follow_dataset` | "started following" | `activity.data.package.title` | `pkg.read` via `object_id` | ✅ |
| `follow_user` | "started following" | user display name / `object_id` | `user.read` | ✅ |
| `follow_group` | "started following the group" | `activity.data.group.title` | `group.read` via `object_id` | ✅ |
| unknown | `activity_type` humanized | pkg or group title if present | — | ❌ |

**Notes:**
- `resource.read` URL: `h.url_for('resource.read', id=resource.package_id, resource_id=resource.id)`
- `pkg.read` type: use `activity.data.package.type or 'dataset'` for the endpoint prefix
- `activity.data.actor` stores the username at creation time (resilient to user deletion); fall back to `activity.user_id`

---

## 3. Component Design: `c-activity-item`

### Figma reference

`figma_exports/activity-item.html` — two sections:
1. Standalone item (top of file)
2. Full accordion with open/closed states and 5 sample items (bottom of file)

The second section is the canonical design.

### HTML structure

```html
<div class="c-activity-item">

  <!-- Left column: vertical timeline -->
  <div class="c-activity-item__timeline" aria-hidden="true">
    <div class="c-activity-item__line"></div>
    <div class="c-activity-item__dot"></div>
  </div>

  <!-- Right column: content -->
  <div class="c-activity-item__content">
    <div class="c-activity-item__actor">
      <a href="{{ actor_href }}">{{ actor_label }}</a>
    </div>
    <div class="c-activity-item__action">
      <span>{{ action_text }}</span>
      {% if subject_label and subject_href %}
        <a href="{{ subject_href }}"><span>{{ subject_label }}</span></a>
      {% elif subject_label %}
        <span>{{ subject_label }}</span>
      {% endif %}
    </div>
    <div class="c-activity-item__time"
         title="{{ h.render_datetime(timestamp, with_hours=True) }}">
      {{ h.time_ago_from_timestamp(timestamp) }}
    </div>
  </div>

</div>
```

### Snippet parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `actor_href` | string | yes | — | URL of the actor's profile page |
| `actor_label` | string | yes | — | Display name of the actor |
| `action_text` | string | yes | — | Plain-text action phrase (e.g. "updated the dataset") |
| `subject_label` | string | no | `''` | Subject text (dataset/resource/etc. title) |
| `subject_href` | string | no | `''` | Subject URL — if empty and `subject_label` set, rendered as plain text |
| `timestamp` | datetime | yes | — | Activity timestamp from `activity.timestamp` |
| `extra_classes` | string | no | `''` | Additional CSS classes on the root element |

The `is_last` flag is **not** a parameter — last-item line termination is handled purely via CSS
(`.c-activity-stream > .c-activity-item:last-child`).

### File

`templates/v2/components/activity-item.html`

---

## 4. Refactor Strategy

### What is replaced

**`helpers/actions.py:744`** — the `hdx_package_activity_stream` action currently renders
`activity_stream.html`. This is the actual AJAX rendering path.

```python
# BEFORE
return tk.render('package/snippets/activity_stream.html', {...})

# AFTER
return tk.render('package/snippets/activity_stream_v2.html', {...})
```

**`hdx_read.html:474`** — the static snippet call is updated so the page-load empty state
also uses the v2 template:

```jinja2
{# BEFORE #}
{% snippet 'package/snippets/activity_stream.html',
    activity_stream=hdx_activities, id=pkg.id, object_type='package' %}

{# AFTER #}
{% snippet 'package/snippets/activity_stream_v2.html',
    activity_stream=hdx_activities, id=pkg.id, object_type='package' %}
```

**`hdx_read.html:475–477`** — the "See more in your dashboard" link is removed. It was
overwritten by AJAX anyway and is not part of the v2 design.

**`dataset-page.js:58`** — the empty-state check is updated from `.activity` to
`.c-activity-stream`:

```js
// BEFORE
var $activities = $(wrapper).find('.activity');

// AFTER
var $activities = $(wrapper).find('.c-activity-stream');
```

### What is preserved

- `activity_stream.html` — untouched; still called on org, group, user, dashboard pages
- All 23 per-type templates in `ckanext/activity/` — untouched
- The accordion shell in `hdx_read.html` (lines 464–471) — unchanged

### What is new

| New file | Purpose |
|---|---|
| `v2/components/activity-item.html` | Single reusable item snippet |
| `package/snippets/activity_stream_v2.html` | Loop + type dispatch + calls `activity-item` |
| `components/activity-item.less` | BEM styles + timeline layout |

---

## 5. Integration Plan

### `activity_stream_v2.html` structure

```jinja2
{# Accepts same params as v1: activity_stream, id, object_type #}
{% if not activity_stream %}
  <p class="c-activity-stream__empty">
    {{ _('No recent activity for this dataset.') }}
  </p>
{% else %}
  <div class="c-activity-stream">
    {% for activity in activity_stream %}

      {# ── resolve actor ── #}
      {% set _actor_href  = h.url_for('user.read', id=activity.user_id) if activity.user_id else '#' %}
      {% set _actor_label = activity.data.actor if (activity.data.actor is defined and activity.data.actor) else activity.user_id %}

      {# ── type dispatch: resolve action_text, subject_label, subject_href ── #}
      {# ... full if/elif chain (see §2 table) ... #}

      {% snippet 'v2/components/activity-item.html',
          actor_href    = _actor_href,
          actor_label   = _actor_label,
          action_text   = _action_text,
          subject_label = _subject_label,
          subject_href  = _subject_href,
          timestamp     = activity.timestamp
      %}
    {% endfor %}
  </div>
{% endif %}
```

### v2 gate

`hdx_read.html` already extends `v2/page.html` — the entire template is v2.
No `{% if v2 %}` wrapping is needed around the snippet call.

### "See more in your dashboard" link

The conditional link at `hdx_read.html:475–477` sits **inside** `.dataset-activity-wrapper`.
Because `$(wrapper).html(response.result)` replaces the entire wrapper contents on AJAX
success, this link is overwritten once activities load. **Decision: remove the link for v2.**
The accordion body will contain only the AJAX-injected activity stream.

---

## 6. Styling Plan

### Figma values → LESS tokens

| Figma value | Token | Value |
|---|---|---|
| `gap: 1.25rem` (item left–right) | `@hdx-space-5` | 20px |
| `padding: 0.75rem 0` (content) | `@hdx-space-3` | 12px |
| `gap: 0.5rem` (actor/action/time) | `@hdx-space-2` | 8px |
| `gap: 2rem` (section header) | `@hdx-space-8` | 32px |
| `font-size: 0.875rem` (body text) | `.hdx-body-s()` mixin | 14px |
| `font-size: 0.75rem` (timestamp) | `.hdx-body-xs()` mixin | 12px |
| `font-weight: 600` (actor) | `.hdx-body-s-semibold()` mixin | — |
| dot size `0.75rem` | — | 12px |
| dot top `1.313rem` | — | 21px (aligns to actor text) |
| line width `0.063rem` | — | ~1px |
| text color `#2f3536` | `@hdx-neutral-85` ✅ confirmed | darkslategray |
| dot color `#1862d8` | `var(--hdx-primary-5)` | royalblue |
| line color `#c4d0d1` | `var(--hdx-neutral-3)` ✅ confirmed | lightgray |

### `activity-item.less` structure

```less
// Local sizing tokens (no global equivalents)
@_dot-top:    1.313rem;
@_dot-size:   0.75rem;

.c-activity-item {
    width:       100%;
    display:     flex;
    align-items: flex-start;
    gap:         var(--hdx-space-5);

    &__timeline {
        align-self:     stretch;
        display:        flex;
        flex-direction: column;
        align-items:    center;
        position:       relative;
        isolation:      isolate;
        flex-shrink:    0;
        width:          @_dot-size;
    }

    &__line {
        width:            0.063rem;
        flex:             1;
        background-color: var(--hdx-neutral-3);
        z-index:          0;
        flex-shrink:      0;
    }

    &__dot {
        width:            @_dot-size;
        height:           @_dot-size;
        position:         absolute;
        top:              @_dot-top;
        left:             calc(50% - (@_dot-size / 2));
        border-radius:    50%;
        background-color: var(--hdx-primary-5);
        border:           0.5px solid var(--hdx-neutral-3);
        box-sizing:       border-box;
        z-index:          1;
        flex-shrink:      0;
    }

    &__content {
        flex:           1;
        display:        flex;
        flex-direction: column;
        align-items:    flex-start;
        padding:        var(--hdx-space-3) 0;
        gap:            var(--hdx-space-2);
        min-width:      0;
    }

    &__actor {
        align-self: stretch;
        .hdx-body-s-semibold();

        a {
            color:           inherit;
            text-decoration: none;

            &:hover { text-decoration: underline; }
        }
    }

    &__action {
        align-self:  stretch;
        .hdx-body-s();
        line-height: 130%;

        a {
            color:           inherit;
            text-decoration: underline;
        }
    }

    &__time {
        align-self:  stretch;
        .hdx-body-xs();
        line-height: 130%;
    }
}

// ── Stream container ─────────────────────────────────────────

.c-activity-stream {
    display:        flex;
    flex-direction: column;
    gap:            0;    // items must be flush — timeline line connects them

    // Terminate timeline on the last item
    > .c-activity-item:last-child {
        .c-activity-item__line { display: none; }
    }

    &__empty {
        .hdx-body-s();
        margin: 0;
    }
}
```

### Why `gap: 0` on the stream

The vertical line is continuous across items. Any gap between items would create a
visible break in the timeline. The content area's `padding: 12px 0` provides the
visual breathing room.

### Last-item line termination

CSS-only: `.c-activity-stream > .c-activity-item:last-child .c-activity-item__line { display: none }`.
No template parameter needed. Handles single-item lists automatically.

### Asset registration

Add to `fanstatic/webassets.yml` in the `v2-components-styles` bundle,
after `v2/components/activity-card.css`:

```yaml
- v2/components/c-activity-item.css
```

The `v2-components-styles` bundle is included by `v2-page-styles`, which is loaded by
`v2/page.html` (the base for `hdx_read.html`). No additional `{% asset %}` tag needed.

---

## 7. Edge Cases

### Empty activity stream

`hdx_activities = []` is the current production state (API call commented out).
The v2 snippet renders `<p class="c-activity-stream__empty">No recent activity…</p>`.
The accordion shell remains (header + chevron visible), body shows the message.

### Missing `activity.data.package`

Can happen if the package was hard-deleted after the activity was logged.
Guard: `activity.data.package.title if activity.data.package else _('unknown')`.
Subject shown as plain text "unknown", no link.

### Missing resource data (`package_id` or `id` absent)

Guard: `h.url_for(...) if (_pkg_id and _res_id) else ''`.
Resource shown as plain text label with no link.

### `activity.user_id` is `None`

Unlikely but possible on corrupted records.
Guard: `actor_href = h.url_for('user.read', id=activity.user_id) if activity.user_id else '#'`.

### `activity.user_name` absent

Not all CKAN versions include `user_name` in the activity dict.
Fall back: `activity.user_name if (activity.user_name is defined and activity.user_name) else activity.user_id`.

### `follow_user` subject

`activity.object_id` is the followed user's CKAN ID, not their display name.
The subject label uses `activity.object_id` as text (same behavior as v1 `user()` macro
for anonymous viewers). The subject href is `h.url_for('user.read', id=activity.object_id)`.

### Unknown/future activity types

The `{% else %}` fallback branch:
- `action_text`: `activity.activity_type | replace('_', ' ')` (humanized raw type string)
- `subject_label`: pkg title if `activity.data.package`, else group title if `activity.data.group`, else `''`
- `subject_href`: `''` (no link for unknown types — safe default)

### Long text

`__content` has `min-width: 0`, allowing text to wrap. No truncation is applied on
activity items (unlike dataset cards). Long dataset titles wrap naturally.

### Single item in the list

`:last-child` CSS rule hides the line, so the dot appears alone without a dangling line.

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `activity.data.actor` absent in legacy records | Low | Fallback to `activity.user_id` covered in template |
| `activity.data` shape varies between CKAN versions | Low | All accesses guarded with `if activity.data.X` |
| `h.url_for` raises on missing route for unknown types | Low | Only called for known types; fallback has no URL call |
| Breaking v1 rendering on org/group/user pages | None | `activity_stream.html` unchanged; v2 snippet only called from `hdx_read.html` |
| Missing LESS typography mixins (`hdx-body-xs`) | Low | Confirmed: `.hdx-body-s-semibold()`, `.hdx-body-s()`, `.hdx-body-xs()` all exist |
| `#c4d0d1` token resolved | None | Used as `var(--hdx-neutral-3)` CSS custom property in LESS component |
| `dataset-page.js` empty-state check targets old `.activity` class | High (will break) | Updated `dataset-page.js:58` to `.find('.c-activity-stream')` |
| `hdx_package_activity_stream` renders v1 HTML | High (blocks v2) | Changed `helpers/actions.py:744` to render `activity_stream_v2.html` |

---

## 9. Decisions Taken

All questions resolved — no open items remain.

1. **Activity types** — Support all 23 types in the v2 snippet for correctness. The full
   if/elif dispatch chain covers every known type; unknown types fall back to humanized
   `activity_type` text with no subject link.

2. **Actor label** — `activity.data.actor` stores the username at activity creation time
   (resilient to user deletion). Use it as the display label; fall back to `activity.user_id`
   for legacy records that predate the field. Template guard:
   `activity.data.actor if (activity.data.actor is defined and activity.data.actor) else activity.user_id`.

3. **LESS mixin names** — confirmed from `mixins.less`:
   - Actor semibold: `.hdx-body-s-semibold()`
   - Action body: `.hdx-body-s()`
   - Timestamp: `.hdx-body-xs()`

4. **Token for `#c4d0d1`** — global token exists: `@hdx-neutral-3: #c4d0d1` (colors.less).
   Use `@hdx-neutral-3` directly; no local variable needed.

5. **Token for `#2f3536`** — confirmed: `@hdx-neutral-85: #2f3536` (colors.less). Use
   `var(--hdx-neutral-85)` for text color.

6. **AJAX architecture** — Activities are loaded via AJAX through `hdx_package_activity_stream`
   (`helpers/actions.py:744`). This file IS in scope. The fix is to change the rendered
   snippet from `activity_stream.html` to `activity_stream_v2.html`. The `hdx_activities`
   static path in `dataset.py` remains `= []` and is not restored in this task.

7. **Pagination** — `limit=7` is enforced by the JS call
   (`dataset-page.js:54`: `limit: 7`). All returned items are rendered; no
   additional pagination needed in the template.

8. **"See more in your dashboard" link** — **Removed for v2.** The link lived inside
   `.dataset-activity-wrapper`, which is fully replaced by AJAX on accordion open. It is
   not part of the v2 design.

9. **Section header styling** — Confirmed unchanged. The accordion header already uses
   `hdx-v2-dataset-section__title`; no modifications needed.

10. **JS empty-state check** — Update `dataset-page.js:58` from `.find('.activity')` to
    `.find('.c-activity-stream')` to match the v2 container class.

---

## 10. Files Affected

### Files to Create

| File | Description |
|---|---|
| `ckanext-hdx_theme/.../templates/v2/components/activity-item.html` | Reusable single-item snippet |
| `ckanext-hdx_theme/.../templates/package/snippets/activity_stream_v2.html` | v2 stream orchestrator |
| `ckanext-hdx_theme/.../hdx-styles/src/common/less/v2/components/activity-item.less` | BEM LESS source |
| `ckanext-hdx_theme/.../fanstatic/v2/components/activity-item.css` | Compiled CSS (committed) |

### Files to Modify

| File | Change |
|---|---|
| `ckanext-hdx_theme/.../templates/package/hdx_read.html` | Line 474: change snippet name to `activity_stream_v2.html`; remove lines 475–477 (dashboard link) |
| `ckanext-hdx_theme/ckanext/hdx_theme/helpers/actions.py` | Line 744: render `activity_stream_v2.html` instead of `activity_stream.html` |
| `ckanext-hdx_theme/.../fanstatic/v2/dataset-page.js` | Line 58: `.find('.activity')` → `.find('.c-activity-stream')` |
| `ckanext-hdx_theme/.../fanstatic/webassets.yml` | Add `v2/components/activity-item.css` to `v2-components-styles` bundle |

## Files NOT to Touch

- `templates/package/snippets/activity_stream.html`
- `ckanext/activity/templates/snippets/activities/*.html`
- `templates/snippets/activity_item.html`
- `ckanext-hdx_theme/.../templates/organization/` and `group/` activity templates
- `ckanext-hdx_package/.../views/dataset.py` (hdx_activities stays `= []`)

---

