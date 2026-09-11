# Crisis Pages (v2) — Ongoing / Archived Listing

**Scope:** A new, dedicated listing page for crisis pages, sourced from the Quick Links config, split
into "Ongoing" and "Archived" sections.

**Excluded:** The existing `/archive` page (`066-archived-dataviz-v2.md`), which mixes archived Quick
Links entries with archived CMS pages of any type — unchanged by this task. `type == 'dashboards'`
pages (currently just "Overview of Data Grids"). Any nav/header wiring for the new page (see D5).

**Figma sources:** None — no crisis-pages-listing export exists in
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/`. Per D11, this ships as a text-only first pass
without requesting a design.

---

## Context

The v2 Products header dropdown previously carried a hardcoded "Archived Dataviz" link to `/archive`
— a page that mixes admin-flagged archived Quick Links entries (e.g. external viz tools) with
archived CMS pages of *any* type. That link has been removed outright (desktop dropdown + mobile
offcanvas in `v2/header.html`) as an immediate, separate change in this same work session — it was
**not** renamed or repointed here.

Separately, the intent is a new "Crisis Pages" concept: a page listing crisis pages, split into
Ongoing and Archived sections, sourced from the Quick Links config (`hdx_quick_links_settings_show`)
— specifically its items whose `url` starts with `/event` or `/m/event` — split by each item's own
`archived` flag. This is new scope — no such listing exists anywhere in the codebase today (only
single-page detail routes `/event/<id>` and `/dashboards/<id>` exist; there is no index).

Decisions confirmed with the requester are listed in §8.

---

## 1. Existing Implementation Audit

- **Data model** — Quick Links (`hdx_quick_links_settings_show` action,
  `ckanext-hdx_theme/ckanext/hdx_theme/helpers/actions.py`), a JSON list stored under CKAN's generic
  `system_info` key `hdx.quick_links.config`. Each item: `{id, title, url, order, newTab, archived,
  buttonText (optional)}` — no category/type field. "Crisis-ness" is inferred purely from `url`
  starting with `/event` or `/m/event`, the same heuristic already used (inverted, to exclude these
  URLs from the Products nav menu) by `hdx_get_quick_links_list(exclude_crisis=True)` in
  `helpers/helpers.py`.
- **Underlying CMS pages** — crisis page *content* itself (the individual `/event/<id>` pages) still
  lives in the separate `Page` model (`ckanext-hdx_pages/ckanext/hdx_pages/model.py`, `type='event'`,
  `status` `'ongoing'`/`'archived'`) via the unrelated `read_event`/`page_list` code paths; this
  listing page does not read that model at all.
- Not every `type='event'` Page has a corresponding Quick Links entry — Quick Links is curated
  separately from Page creation/archival, so this listing can lag behind the full set of `event`
  Pages until an admin adds an entry for each one — see D20.
- **No existing listing/index route** for crisis pages — only detail routes exist:
  `/event/<id>`, `/dashboards/<id>` (desktop, `pages/read_page.html`) and `/m/event/<id>`,
  `/m/dashboards/<id>` (mobile-lite, untouched by v2).
- **Closest structural precedents:**
  - `templates/admin/pages.html` — sysadmin table rendering `type` / `status` / `state` per page,
    with an "Archived/Ongoing" column header — the existing precedent for this vocabulary, even
    though this listing sources from Quick Links rather than that table.
  - `templates/archived_quick_links/main.html` + `v2/components/text-button.html` row pattern (see
    `066-archived-dataviz-v2.md` §3) — the row-list rendering approach reused here.
- The v2 Products header/footer "Archived Dataviz" link (`v2/header.html`, desktop dropdown + mobile
  offcanvas) was removed outright in this same work session, per D1/D5 — not repointed here.

---

## 2. Figma Mapping

**No Figma export exists for a crisis-pages listing view.** Checked
`ckanext-hdx_theme/llm_docs/redesign/figma_exports/` — the only crisis/event-related exports are for
the *individual* crisis page (`crisis-page-sm.html`,
`crisis-page-dataviz-maps-etc-{sm,md,xl}.html`, task 060), not a listing/index of multiple pages. No
comparison against Figma is possible for this feature — per D11, §3's confirmed structure ships as
the first-pass implementation rather than being held pending a design.

---

## 3. Confirmed Structure

- **Route**: `/crisis-pages`, blueprint `hdx_crisis_pages` — a single view, no params. (D7)
- **View**: call `hdx_quick_links_settings_show` (action), keep items whose `url` starts with
  `/event` or `/m/event`, split into two lists by each item's own `archived` flag, each sorted by the
  item's own `order` field, ascending. (D10, D15, D20)
- **Template**: extends `v2/page.html`, no-sidebar single-column layout — same base pattern as
  `archived_quick_links/main.html` (066).
- **Two stacked sections** (not a `c-tabs` toggle), "Ongoing" first, "Archived" second — each a plain
  `<h2>` heading (`.hdx-section-title()`, no item count) above a row list using the same
  `v2/components/text-button.html` + `c-divider` pattern established in `066-archived-dataviz-v2.md`
  §3, each row linking to `item.url` (`/event/<name>`) with the internal-navigation icon convention
  (`arrow-right.svg`, right-positioned, no `target` attribute) rather than 066's external-link icon,
  rows ordered per D10. (D8, D16)
- **Breadcrumb**: `Home / Products / Crisis Pages`, mirroring 066's `Home / Products / Archived
  Dataviz` pattern — "Products" unlinked, per the `060-crisis-event-pages-v2.md` D9 precedent.
- **Page heading**: "HDX Crisis Pages", no intro/subtitle copy. (D13)

---

## 4. Component & System Mapping

Reuse only — no new components proposed:

| Component | Usage |
|---|---|
| `v2/page.html` | Base template, no-sidebar pattern (per 066 precedent) |
| `v2/components/breadcrumb.html` | `Home / Products / Crisis Pages` |
| `v2/components/page-header.html` | Page title only, no `title_count` badge |
| `v2/components/text-button.html` | Each row, same pattern as 066 §3 |
| `c-divider` | Row separators within each section |

Section headings ("Ongoing" / "Archived") — a plain `<h2>` styled with `.hdx-section-title()`, no item
count next to it, per the stacked-sections decision (D8, D17).

---

## 5. Responsive Strategy

Follows the `066-archived-dataviz-v2.md` §6 precedent directly (single-column at all breakpoints, no
reflow concerns — this is a text row list, not a grid), per the stacked-sections decision (D8).

---

## 6. Risks

| Risk | Detail | Mitigation |
|---|---|---|
| No Figma reference | Building without one risks visual mismatch once real designs arrive. | Proceeding with §3 as the confirmed first-pass layout per D11; revisit if/when Figma designs arrive. |
| Content overlap with `/archive` | Both pages can list archived crisis pages, through independent code paths with no shared logic. | Deliberate separation per D1/D2; future changes to one will not automatically apply to the other — worth remembering, not a defect. |
| Quick Links coverage | A crisis page only appears on `/crisis-pages` once an admin adds a matching Quick Links entry; `Page`-level creation/archival alone has no effect on this listing. | Deliberate per D20 — Quick Links is the sole, curated source; gaps are addressed via `/ckan-admin/quick-links`, not code. |

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| Zero ongoing or zero archived crisis pages in a given section | Follow the `066` D7 precedent: still show the section heading, plus a short empty-state message inside it ("No ongoing crisis pages." / "No archived crisis pages."). (D9, D18) |
| A Quick Links entry with a missing/empty title | No defensive handling beyond `.strip()`ing whitespace — an empty title renders as an empty row label, matching the admin-curated data as entered. |

---

## 8. Decisions Taken (confirmed with user during requirements drafting)

- **D1 — New dedicated page (confirmed):** A new, separate route/page, not a repurposing or
  retitling of `/archive`'s own v2 UI (`066-archived-dataviz-v2.md`, unchanged in the codebase). Once
  this page exists, `/archive` itself permanently redirects (301) here rather than rendering that UI —
  see D19.
- **D2 — Scope: crisis pages only (confirmed):** Quick Links items whose `url` starts with `/event`
  or `/m/event` only. `/dashboards`-prefixed items (currently just "Overview of Data Grids") are out
  of scope.
- **D3 — Ongoing / Archived split (confirmed):** Uses each Quick Links item's own `archived` boolean
  field.
- **D4 — No backend action changes (confirmed):** No changes to `hdx_quick_links_settings_show`
  (`ckanext-hdx_theme/ckanext/hdx_theme/helpers/actions.py`) or its schema. Filter by `url` prefix and
  split by `archived` in the view layer.
- **D5 — No hardcoded nav entry (confirmed):** No link to this new page is added to the v2 header
  (desktop dropdown or mobile offcanvas) or footer. Discovery is via the admin-managed Quick Links
  list only — the same mechanism as any other Products-menu item — consistent with the removal in D1
  above.
- **D6 — Naming (confirmed):** "Crisis Pages" is the working name for this new feature/page. It
  replaces "Archived Dataviz" as a *concept* in the Products-menu context, but is a distinct page —
  not a rename of `/archive`.
- **D7 — Route/blueprint (confirmed):** `/crisis-pages`, blueprint `hdx_crisis_pages`.
- **D8 — Section UI pattern (confirmed):** Two stacked labeled sections (Ongoing above Archived), not
  a `c-tabs` toggle.
- **D9 — Empty-state handling (confirmed):** Follows the `066` D7 precedent — still show the section
  heading, plus a short empty-state message inside it, if a section has zero pages.
- **D10 — Sort order (confirmed):** Within each section, rows are sorted by the Quick Links item's
  own `order` field, ascending — the same ordering the admin sets via drag-and-drop in
  `/ckan-admin/quick-links`.
- **D11 — No Figma requested (confirmed):** Proceed as a text-only first pass matching `/archive`'s
  existing pattern; no design is requested before this first implementation.
- **D12 — Analytics (confirmed):** No tracking, matching `/archive`'s precedent (`066` D4).
- **D13 — Page heading copy (confirmed):** "HDX Crisis Pages", no intro/subtitle copy.
- **D14 — Discoverability (confirmed):** No link to this page is added anywhere in the v2 header,
  footer, or other UI; reachable via `/archive`'s redirect (D19), direct URL, or a future
  admin-added Quick Links entry, consistent with D5.
- **D15 — Row title source (confirmed):** Each row's label is the Quick Links item's own `title`
  field, verbatim (`.strip()`'d defensively), with no lookup against the underlying `Page.title`.
- **D16 — Row link icon (confirmed):** Rows use `arrow-right.svg`, right-positioned, no `target`
  attribute — the internal-navigation convention already used for `page_list` links in
  `page-header.html`, not `066`'s external-link icon/`target="_blank"` (its rows point off-site).
- **D17 — Section heading counts (confirmed):** No item count next to "Ongoing" / "Archived" — plain
  text headings only.
- **D18 — Empty-state copy (confirmed):** "No ongoing crisis pages." / "No archived crisis pages." —
  section-specific wording rather than a generic message reused for both.
- **D19 — `/archive` redirect (confirmed):** `/archive` (`hdx_archived_quick_links` blueprint)
  permanently redirects (301) to `/crisis-pages`, via the `check_redirect_needed`-style pattern
  (`ckan.plugins.toolkit.redirect_to` with `response.status_code` forced to `301`) already used
  elsewhere in this codebase for permanent URL retirement. `/archive`'s own data (archived Quick
  Links entries, and archived pages of any `type` other than `event`) has no other listing page —
  accepted as a deliberate loss of reachability, not carried over into `/crisis-pages`. The old
  `show()` view function, its helpers, and `archived_quick_links/main.html` stay in the codebase
  unused (see `066-archived-dataviz-v2.md` D10) rather than being deleted.
- **D20 — Data source: Quick Links, not `Page`/`page_list` (confirmed):** The listing reads
  `hdx_quick_links_settings_show` exclusively; `Page`/`page_list` plays no role in this view. Quick
  Links is the sole, curated source — a crisis page shows up only once an admin adds a matching Quick
  Links entry via `/ckan-admin/quick-links`; pages without one simply don't appear, which is expected
  and addressed by curating Quick Links, not by code.

---

## 9. Files Affected

- `ckanext-hdx_theme/ckanext/hdx_theme/views/crisis_pages.py` — blueprint `hdx_crisis_pages`, route
  `/crisis-pages`, builds the ongoing/archived lists from Quick Links per §3.
- `ckanext-hdx_theme/ckanext/hdx_theme/plugin.py` — registers `hdx_crisis_pages` in `get_blueprint()`.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/crisis_pages/main.html` — new page template.
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/pages/crisis-pages.less` — new
  page styles (compiles to `fanstatic/v2/pages/crisis-pages.css`).
- `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` — adds the
  `v2-crisis-pages-page-styles` bundle.
- `ckanext-hdx_theme/ckanext/hdx_theme/views/archived_quick_links_custom_settings.py` — `/archive`'s
  route function is `redirect_to_crisis_pages`, a 301 redirect to `hdx_crisis_pages.show` (D19); the
  original `show()` and its helpers remain, unused.
- `ckanext-hdx_theme/ckanext/hdx_theme/tests/test_pages/test_page_load.py` — the `/archive` smoke-test
  rows are replaced with `hdx_crisis_pages.show` rows.
