# 055 — Notifications (Logged-in Users): v2 Migration

**Scope IN:** Bell-icon notification dropdown (header), v2-styled. Template consolidation of the 4 existing notification-type snippets into a shared v2 shell component. The 4 snippets are rewritten unconditionally (no `{% if v2 %}` branch) — the v1 Bootstrap dropdown is retired and left wired up as-is, unstyled.
**Scope OUT:** Notification *generation* logic (the DAOs/queries that decide what counts as a notification), the "Subscribe to Notifications" email opt-in system (`notification_platform/*`, `user/notifications.html` — separate feature, already migrated in task 051), any new notification types, any backend read/unread schema, a standalone notifications list page/route (dropped from scope — the dropdown keeps showing the full unfiltered list via scroll, same as today; see §6), the sysadmin All/Personal filter toggle (dropped — sysadmin entries are always shown, just highlighted).

---

## Context

This is a **migration, not a redesign** — the bell dropdown must match Figma exactly while preserving every existing notification type and behavior. The v1 legacy dropdown (Bootstrap, `light/notifications/notification_snippet.html`) is retired: the 4 shared snippets now render the new markup unconditionally, and `header-global.html`/`notification_snippet.html` are left untouched (see §3).

Two important framing corrections vs. the original task brief, confirmed with the user during planning:
1. **"Notifications" already names a different, unrelated feature.** `hdx_user.notifications` (route `views/user.py:227`, template `user/notifications.html`) is the "Subscribe to Notifications" hub — email opt-in/opt-out for dataset/org/location updates, entirely separate data model, already migrated to v2 drawers in task 051. This doc's subject — the bell-dropdown backlog (membership requests, HDX Connect requests, expired datasets, quarantined datasets) — is **unrelated** to it. The two must not be confused or merged.
2. **No read/unread state exists today**, in backend or Figma. This doc does not invent one.

---

## 1. Existing Implementation Audit

### 1.1 Data flow (unchanged by this task)

```
h.hdx_get_user_notifications()                        [ckanext-hdx_users/helpers/helpers.py:65]
  → get_notification_service()                        [helpers/notification_service.py:19]
    → NotificationService.get_notifications()          combines 4 sub-services, sorts by last_date desc
        MembershipRequestsService     → org_membership_snippet.html
        RequestDataService (+Sysadmin variant)  → requestdata_snippet.html
        ExpiredDatasetsService        → expired_datasets_snippet.html
        QuarantinedDatasetsService (+Sysadmin variant) → quarantined_datasets_snippet.html
  → returns { count, list, any_personal_notifications, is_sysadmin }
```

Each list entry carries an `html_template` field naming which of the 4 snippets renders it. This dispatch string is **hardcoded in `notification_service.py`** — per the consolidation decision (§3), this file is not edited, which is why the four templates stay as four separate files rather than becoming one data-driven template.

### 1.2 Templates (bell dropdown only — subscription templates excluded)

| Template | Role |
|---|---|
| `templates/light/notifications/notification_snippet.html` | v1 legacy dropdown shell (Bootstrap `dropstart`, still live for non-v2 sessions) |
| `templates/v2/navbar-notifications.html` | v2 dropdown panel shell (already exists — header/list/empty state, opened via `data-hdx-v2-panel="notifications"`) |
| `templates/light/notifications/org_membership_snippet.html` | Type: org membership request — **shared** by both shells above |
| `templates/light/notifications/requestdata_snippet.html` | Type: HDX Connect data request — **shared** |
| `templates/light/notifications/expired_datasets_snippet.html` | Type: dataset needs update — **shared** |
| `templates/light/notifications/quarantined_datasets_snippet.html` | Type: dataset under QA quarantine — **shared** |

The 4 type snippets are `{% include %}`'d by *both* the v1 and v2 shells (same file, not a v1/v2 pair) — this is the structural fact that drives the consolidation approach in §3.

### 1.3 JS behavior

| File | Role |
|---|---|
| `fanstatic/notifications/hdx_notifications_main.js` | CKAN module; two entry points: `type: 'header icon'` (fires on Bootstrap `shown.bs.dropdown`) and `type: 'item'` (click on a notification link) |
| `fanstatic/hdx_visibility_toggler.js` | Generic 2-state show/hide toggle (used for the v1 sysadmin All/Personal filter); fully generic via `data-module-*` selector options — no hardcoded class names, so it's directly reusable for v2 |
| `fanstatic/v2/navbar.js` | v2's generic panel open/close system (`data-hdx-v2-panel`); handles the notifications panel today with **no analytics hook** |

**Confirmed gap:** `hdx_notifications_main`'s header-icon tracking listens for Bootstrap's `shown.bs.dropdown` event. The v2 bell button has no `data-module="hdx_notifications_main"` and uses the unrelated custom panel system in `navbar.js` — so **the "header icon opened" analytics event currently never fires in v2** (pre-existing regression, not introduced by this task). Item-click tracking is unaffected (same shared `<a data-module="hdx_notifications_main" data-module-type="item">` markup renders in both shells). This is fixed in this migration (§5).

**Confirmed gap:** v1's sysadmin-only All/Personal filter toggle (`hdx_visibility_toggler`, wired in `notification_snippet.html`) has **no v2 equivalent** — `v2/navbar-notifications.html` shows all items unfiltered with no toggle at all. Not restored — this migration keeps the unfiltered list; sysadmin entries are distinguished only by the `.c-notification-item--sysadmin` highlight (§5).

### 1.4 Read/unread state

**None exists.** No DB column, no API action, no localStorage. All 4 types are computed live each page load from current DB/SOLR state (pending membership row, open `requestdata` row, `due_date` passed, quarantine flag true) and disappear once the underlying condition resolves — not once "read." The only related CKAN-core action, `dashboard_mark_activities_old` (`ckanext/activity/logic/action.py:58`), is unused by this system. Figma exports show no unread indicator. **Out of scope — no read/unread concept is invented.**

### 1.5 Analytics (must be preserved exactly)

`hdxUtil.analytics.sendNotificationInteractionEvent(data)` (`fanstatic/google-analytics.js:445`) dispatches to both Mixpanel and GTM (`event: 'notification interaction hdx'`) with `type: 'header icon'|'item'`, `personal: boolean`, `count`, `destinationUrl`. Function signature and call sites are unchanged by this task — only the *wiring* that triggers the header-icon call is added for v2 (§1.3, §5).

### 1.6 No existing "list page" — and none is being built

Neither v1 nor v2 has a full-list/paginated view of these 4 notification types today. The dropdown itself already renders the *entire* unfiltered `notif.list` (scrollable, `max-height: 18.75rem`) — there is no truncation and no "View all" link anywhere in code or in the 3 given Figma exports. **No list page is built, and no "View all" link is added.** The dropdown's existing scroll-everything behavior already satisfies the requirement; see §6.

---

## 2. Notification Types Mapping

| Type | Source service | Cardinality | Sysadmin variant? | Fields used |
|---|---|---|---|---|
| Org membership request | `MembershipRequestsService` | One entry **per org** with pending requests | Yes — sysadmins additionally see orgs they don't admin (`for_sysadmin=True`) | `org_title`, `org_name`, `org_hdx_url`, `count`, `last_date` |
| HDX Connect data request | `RequestDataService` / `SysadminRequestDataService` | One aggregate entry (personal) + one **per org** for sysadmins | Yes | `my_requests_url`, `count`, `last_date`, `org_title` (sysadmin only) |
| Expired / needs-update datasets | `ExpiredDatasetsService` | At most one aggregate entry | No | `my_dashboard_url`, `count`, `last_date` |
| Quarantined (QA hold) datasets | `QuarantinedDatasetsService` / `SysadminQuarantinedDatasetsService` | One entry **per dataset** (not aggregated) + more per dataset for sysadmins outside their orgs | Yes | `dataset` (dict), `dataset_url`, `last_date` |

**Two distinct, similarly-named booleans — easy to conflate, must both be preserved exactly:**
- `is_sysadmin` — is the *viewing user* a sysadmin at all. Controls whether the `[type]` bracket tag prefix (e.g. `[membership]`) renders. Non-sysadmins never see these tags.
- `for_sysadmin` — is *this specific entry* being shown in the user's sysadmin oversight capacity (e.g., an org they don't personally admin). Controls the yellow highlight **and** which text branch (personal "You have…" vs. oversight "There is/are…") renders in the org-membership and requestdata snippets.

Quarantined-dataset entries only vary the bracket tag by `is_sysadmin`; message text doesn't branch on `for_sysadmin`. Expired-dataset entries have no sysadmin variant at all (`for_sysadmin` always `False`).

---

## 3. Consolidation Strategy

**Template-layer only — `notification_service.py` is not touched.**

True single-template consolidation (activity-item.html-style, where Python pre-builds `actor_label`/`action_text` and the template has zero conditionals) would require changing the dict shape `notification_service.py` returns — out of bounds per this decision.

**Chosen approach — shared v2 shell, unconditional (v1 dropdown retired, no `{% if v2 %}` branch):**

Each of the 4 shared snippets keeps its own text/link logic but now renders through one new shared component, `v2/components/notification-item.html`, instead of the previous ad hoc `<br><span class="date">` markup:

```jinja
{# org_membership_snippet.html #}
{% set sysadmin_tag = '[membership]' if notification.is_sysadmin else '' %}
{% set body %}
  {% if notification.for_sysadmin %}
    {{ _('There') }} {{ _('are') if notification.count > 1 else _('is') }}
    <a href="{{ notification.org_hdx_url }}" data-module="hdx_notifications_main"
       data-module-personal="false" data-module-type="item">
      {{ notification.count }} {{ _('membership') }} {{ _('requests') if notification.count > 1 else _('request') }}
    </a>
    {{ _('for') }} {{ notification.org_title }} {{ _('organisation.') }}
  {% else %}
    {{ _('You have') }}
    <a href="{{ notification.org_hdx_url }}" data-module="hdx_notifications_main"
       data-module-personal="true" data-module-type="item">
      {{ notification.count }} {{ _('membership') }} {{ _('requests') if notification.count > 1 else _('request') }}
    </a>
    {{ _('for') }} {{ notification.org_title }} {{ _('organisation.') }}
  {% endif %}
{% endset %}
{% snippet 'v2/components/notification-item.html',
    sysadmin_tag=sysadmin_tag, for_sysadmin=notification.for_sysadmin,
    date=notification.last_date, body=body,
    url=notification.org_hdx_url, data_personal=not notification.for_sysadmin %}
```

Notes:
- No `notification_service.py` change → zero risk to notification *generation* logic (explicitly excluded).
- `header-global.html` (v1 header) and `notification_snippet.html` (v1 shell) still include these 4 snippets but are not updated — non-v2 sessions see unstyled markup inside the old Bootstrap dropdown.
- Real visual/DOM consolidation is achieved: all 4 types render through one shell for spacing, the meta/date row, the arrow link, and the sysadmin highlight — satisfying "unified notification item" and "consistent item rendering" across all 4 types without touching business logic.

`url`/`data_personal` are per-type: `org_membership_snippet.html` passes `notification.org_hdx_url`; `requestdata_snippet.html` passes `notification.my_requests_url`; `expired_datasets_snippet.html` passes `notification.my_dashboard_url` with `data_personal=True` (no sysadmin variant, §2); `quarantined_datasets_snippet.html` passes `notification.dataset_url` with `data_personal=not notification.is_sysadmin` (this type has no `for_sysadmin` text branch, §2).

This *is* the "alternative (partial reuse)" the task asks for if full consolidation isn't safe — full consolidation isn't safe here only because of the backend-editing constraint, not because the four types are structurally incompatible (they are, in fact, structurally identical modulo text).

---

## 4. Component Definition

**New:** `templates/v2/components/notification-item.html` — shared shell used by all 4 types in the dropdown.

```jinja
{#
  c-notification-item — single notification row (v2)

  Required:
    date          (string) — pre-formatted date (notification.last_date)
    body          (string, HTML) — pre-rendered message incl. inline link(s); caller-supplied via {% set body %}
    url           (string) — destination URL; same href as body's inline link(s), used for the trailing arrow link
    data_personal (bool) — mirrors the inline link's data-module-personal value, applied to the arrow link too

  Optional:
    sysadmin_tag  (string, default='') — bracket tag e.g. '[membership]'; empty for non-sysadmin viewers
    for_sysadmin  (bool, default=False) — true → sysadmin oversight highlight
#}
<div class="c-notification-item{{ ' c-notification-item--sysadmin' if for_sysadmin }}">
  <div class="c-notification-item__title">
    {% if sysadmin_tag %}<span class="c-notification-item__tag">{{ sysadmin_tag }}</span>{% endif %}
    {{ body | safe }}
  </div>
  <div class="c-notification-item__meta">
    <span class="c-notification-item__date">{{ date }}</span>
    <a class="c-notification-item__arrow" href="{{ url }}" aria-label="{{ _('View details') }}"
       data-module="hdx_notifications_main"
       data-module-personal="{{ 'true' if data_personal else 'false' }}" data-module-type="item">
      {% include 'v2/icons/arrow-right.svg' %}
    </a>
  </div>
</div>
```

**States:** default, and `--sysadmin` (yellow highlight, `var(--hdx-warning-1)` — closest match to today's `lightyellow`, §7). No unread/hover-content-change state — per §1.4, only the browser's native link hover applies.

**Click targets:** two independent clickable elements per row — the inline text link inside `body`, and the trailing arrow, both pointing at the same destination and firing the same `item`-type analytics event (duplicate tracking on the same destination is expected/acceptable, matching two distinct click affordances). The row/card background itself is **not** a click target — Figma's arrow does not imply whole-row click.

**Reuse:** `arrow-right.svg` already exists at `templates/v2/icons/arrow-right.svg` — no new icon asset needed. Typography reuses `.hdx-body-s()` (title/body) and `.hdx-body-xs()` (date), consistent with `c-activity-item`'s own use of these mixins.

---

## 5. Dropdown Strategy

`v2/navbar-notifications.html`'s existing header/list/empty-state shell is kept as-is, including its scroll-everything behavior (no truncation, no "View all" link, §1.6/§6). The sysadmin All/Personal filter toggle from v1 is **not** restored — sysadmins see every notification inline, with sysadmin-oversight entries highlighted via `.c-notification-item--sysadmin`; no toggle markup, no `hdx_visibility_toggler` reuse, no empty-personal placeholder.

One functionality-parity fix is added: **the missing "header icon opened" analytics event** (§1.3 gap, user-confirmed in scope). A `data-notification-count="{{ notif.count }}"` attribute is added to the bell button, and `fanstatic/v2/navbar.js`'s `showPanel(name)` calls `hdxUtil.analytics.sendNotificationInteractionEvent({type: 'header icon', count: <read from the trigger's data attribute>})` when `name === 'notifications'`. Same event/schema as v1 — this restores intended existing tracking, it does not change what's tracked.

No changes to how the panel opens/closes (`data-hdx-v2-panel="notifications"` mechanism in `navbar.js` is untouched) or to `v2/header.html`'s integration. No "View all" link and no navigation entry point to a full list page (§1.6/§6).

---

## 6. List Page — Out of Scope (decision)

**No list page is built.** The dropdown already shows the entire unfiltered notification list via scroll (`max-height: 18.75rem`, §1.6) and this migration keeps that behavior as-is. Consequently, none of the following are part of this task:

- No new template (no `user/dashboard_notifications.html` or equivalent).
- No new route/view on the `hdx_user_dashboard` blueprint, no `/dashboard/notifications` URL.
- No in-memory pagination of `notif.list`, no reuse of `v2/components/pagination.html` for this feature.
- No "View all" link anywhere in the dropdown (§5).

This also removes the naming/URL collision risk with the unrelated `hdx_user.notifications` (Subscriptions) route that an earlier draft of this doc flagged (previously §8) — there is no new route to collide.

If a full-list page is wanted later, this section's original design (standalone `{% extends "v2/page.html" %}` page, reusing `h.hdx_get_user_notifications()` and the same `notification-item.html` shell) remains a valid starting point — it is deferred, not rejected on technical grounds.

---

## 7. Styling Strategy

| v1 | v2 |
|---|---|
| `background-color: lightyellow;` (`.for-sysadmin`, `_global-header.less:249`; `.hdx-v2-notifications__item--sysadmin`, `navbar.less:472`, also hardcoded `lightyellow`) | `var(--hdx-warning-1)` (`#f6e9d4`) on the new `.c-notification-item--sysadmin` — closest token to the current pale-yellow look. Moves from the dropdown-specific `.hdx-v2-notifications__item` wrapper to the shared shell. |
| Plain inline text, `<br>`, `.date { color: @grayColor }` | `.c-notification-item__title` uses `.hdx-body-s()`; `.c-notification-item__meta`/`__date` uses `.hdx-body-xs()`; flex row layout matching Figma's `.time-parent` |
| No per-item icon | `.c-notification-item__arrow` — now an `<a>` (§4, second click target), reuses existing `v2/icons/arrow-right.svg`, sized `1rem` per Figma |

The v1 All/Personal toggle is not carried forward — see §5.

**New file:** `hdx-styles/src/common/less/v2/components/notification-item.less`, registered as `v2/components/notification-item.css` in the `v2-components-styles` bundle in `webassets.yml` (same pattern 051 used to add `drawer.css`). Structure mirrors `activity-item.less`: BEM nesting, `var(--hdx-*)` tokens throughout, no raw rem/hex values where a token exists.

**Modified:** `hdx-styles/src/common/less/v2/navbar.less` — remove the `&--sysadmin` rule from `.hdx-v2-notifications__item` (superseded by the shell's own modifier, avoiding duplicate/conflicting highlight logic).

---

## 8. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| v1 legacy dropdown renders unstyled/broken markup now that the shared snippets emit v2-only classes | Accepted | v1 dropdown is retired as part of this task — not mitigated by design (§3) |
| Analytics silently regressed further | ❗ Critical | Item-click tracking untouched (shared markup); header-icon tracking gap is *fixed*, not just preserved (§5) |
| Sysadmin highlight or bracket-tag logic swapped (`is_sysadmin` vs `for_sysadmin`) | ❗ Critical | Both flags threaded through unchanged from `notification_service.py`; §2 documents the distinction explicitly for implementers |
| A notification type silently dropped during template rewrite | High | All 4 snippets updated individually; no shared/generic loop that could skip a type |
| Arrow link and inline text link get out of sync (different `href`/`data-module-personal`) since a row now has two independently-marked-up click targets | Medium | Both derive from the same snippet-level variables at the call site (§3); no separate lookup for the arrow |

---

## 9. Edge Cases

| Case | Handling |
|---|---|
| Long messages (long org/dataset title) | `.c-notification-item__title` wraps naturally (flex column, no `white-space: nowrap`); no truncation in Figma exports, so none is added |
| Missing/null `last_date` | `notification_service.py` already defaults unparseable dates to "now" (membership) or omits the field; `notification-item.html`'s `date` param renders whatever string is passed — no new null-handling needed since the service layer already normalizes this |
| Unknown/new notification type (no matching `html_template`) | Out of scope to defensively handle — would require a `notification_service.py` change (excluded); a new type added later must ship its own snippet, same as today |
| Many notifications (sysadmin with many orgs/quarantined datasets) | Existing scrollable `max-height` behavior unchanged — no pagination, no list page (§6) |
| Empty state (zero notifications) | Existing "No notifications" message, reused as-is |

---

## 10. Open Questions

### Resolved during planning (recorded for traceability)

1. **List page vs. existing "Notifications" (Subscriptions) tab** → Confirmed unrelated; this doc's feature is a bell-dropdown migration only, does not touch `notification_platform`/`user/notifications.html` (Context, §6).
2. **Consolidation depth** → Template-layer only; `notification_service.py` untouched (§3).
3. **Read/unread state** → Document as out of scope; no read/unread concept invented (§1.4).
4. **v2 header-icon analytics gap** → Fixed in this migration, restoring v1 parity (§5).
5. **Sysadmin highlight token** → `var(--hdx-warning-1)` (§7).
6. **Click target** → Inline text link stays clickable; the trailing arrow becomes a second, independent link to the same destination (same analytics attributes). The row/card itself is not clickable (§4).
7. **List page scope** → Dropped entirely. No "View all" link, no `/dashboard/notifications` route/template, no new nav entry point anywhere (user menu included). The dropdown keeps its existing scroll-everything behavior (§1.6, §5, §6). Page-size/pagination questions are moot as a result.
8. **v1 legacy dropdown** → Retired. The 4 shared snippets render the new markup unconditionally; `header-global.html`/`notification_snippet.html` are left wired up as-is, unstyled (§3).
9. **Sysadmin All/Personal filter toggle** → Dropped. Sysadmins see every notification inline; oversight entries are distinguished only by the `.c-notification-item--sysadmin` highlight (§5).

### Still open

None — all open items from initial planning have been resolved above.
