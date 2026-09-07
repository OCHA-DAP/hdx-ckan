# Crisis Pages (v2) — Ongoing / Archived Listing

**Scope:** A new, dedicated listing page for crisis (`type='event'`) CMS pages, split into "Ongoing"
and "Archived" sections.

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

Separately, the intent is a new "Crisis Pages" concept: a page listing crisis (`type='event'`) CMS
pages specifically, split into Ongoing and Archived sections, using the `Page.status` field that
already exists and is already used for exactly this purpose in `/archive`'s and the admin pages
table's filtering logic. This is new scope — no such listing exists anywhere in the codebase today
(only single-page detail routes `/event/<id>` and `/dashboards/<id>` exist; there is no index).

Decisions confirmed with the requester are listed in §8.

---

## 1. Existing Implementation Audit

- **Data model** — `ckanext-hdx_pages/ckanext/hdx_pages/model.py`, table `page`:
  - `type`: `'event'` (crisis) or `'dashboards'`
  - `status`: `'ongoing'` / `'archived'`
  - `state`: standard CKAN state (`active`/`draft`)
- **`page_list` action** (`ckanext-hdx_pages/ckanext/hdx_pages/actions/get.py:68-107`) already
  supports a `status` filter (`query.filter_by(status=...)`) plus always-applied `state='active'`. No
  `type` filter exists — per D4, none is added; filter client-side/view-side instead.
- **Current live data** (confirmed via direct query against the local dev DB, 2026-09-07):
  - 3 ongoing `event` pages: Lebanon Crisis (`/event/lebanon-crisis`), COD (`/event/cod`), occupied
    Palestinian territory-Israel Hostilities (`/event/opt-israel-hostilities`)
  - 4 archived `event` pages: Türkiye/Syria Earthquakes (`/event/turkiye-syria-earthquakes`), Libya
    Floods (`/event/libya-floods`), Morocco Earthquake (`/event/morocco-earthquake`), Rohingya Refugee
    Crisis (`/event/rohingya-displacement`)
  - 1 ongoing `dashboards` page: Overview of Data Grids (`/dashboards/overview-of-data-grids`) — out
    of scope per D2
- **No existing listing/index route** for crisis pages — only detail routes exist:
  `/event/<id>`, `/dashboards/<id>` (desktop, `pages/read_page.html`) and `/m/event/<id>`,
  `/m/dashboards/<id>` (mobile-lite, untouched by v2).
- **Closest structural precedents:**
  - `ckanext-hdx_theme/ckanext/hdx_theme/views/archived_quick_links_custom_settings.py` — the
    `/archive` view, whose `_prepare_archived_page_list()` already queries `page_list` and filters by
    `status == 'archived'` in Python. The same approach, adding a `type == 'event'` filter, is the
    basis for this new page's data assembly.
  - `templates/admin/pages.html` — sysadmin table already rendering `type` / `status` / `state` per
    page, with an "Archived/Ongoing" column header confirming this is already the established
    user-facing vocabulary.
  - `templates/archived_quick_links/main.html` + `v2/components/text-button.html` row pattern (see
    `066-archived-dataviz-v2.md` §3) — the row-list rendering approach to reuse.
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
- **View**: call `page_list` (action) with `state='active'`, filter to `type == 'event'` in Python
  (mirrors the existing `_prepare_archived_page_list()` pattern), then split into two lists by
  `status`, each sorted by the `Page.modified` timestamp, newest first. (D10, D15)
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

---

## 7. Edge Cases

| Case | Handling |
|---|---|
| Zero ongoing or zero archived crisis pages in a given section | Follow the `066` D7 precedent: still show the section heading, plus a short empty-state message inside it ("No ongoing crisis pages." / "No archived crisis pages."). (D9, D18) |
| A crisis page with a missing/empty title | Assume the same data hygiene as `/archive`'s existing `_prepare_archived_page_list()`, which does no additional defensive handling today. |

---

## 8. Decisions Taken (confirmed with user during requirements drafting)

- **D1 — New dedicated page (confirmed):** A new, separate route/page — not a repurposing, retitling,
  or restructuring of the existing `/archive` page, which stays exactly as implemented in
  `066-archived-dataviz-v2.md`.
- **D2 — Scope: crisis pages only (confirmed):** `type == 'event'` pages only. `type == 'dashboards'`
  pages (currently just "Overview of Data Grids") are out of scope.
- **D3 — Ongoing / Archived split (confirmed):** Uses the existing `Page.status` column
  (`'ongoing'` / `'archived'`) — the same field already used by `/archive`'s
  `_prepare_archived_page_list()` and by the sysadmin `templates/admin/pages.html` table (whose
  "Archived/Ongoing" column is the existing precedent for this exact vocabulary).
- **D4 — No backend action changes (confirmed):** No new `type` filter is added to the `page_list`
  action (`ckanext-hdx_pages/ckanext/hdx_pages/actions/get.py`). Filter by `type` in the view layer
  instead, mirroring the pattern `archived_quick_links_custom_settings.py::_prepare_archived_page_list()`
  already uses to filter by `status` in Python.
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
- **D10 — Sort order (confirmed):** Within each section, rows are sorted newest first (see D15 for the
  field this uses).
- **D11 — No Figma requested (confirmed):** Proceed as a text-only first pass matching `/archive`'s
  existing pattern; no design is requested before this first implementation.
- **D12 — Analytics (confirmed):** No tracking, matching `/archive`'s precedent (`066` D4).
- **D13 — Page heading copy (confirmed):** "HDX Crisis Pages", no intro/subtitle copy.
- **D14 — Discoverability (confirmed):** Intentionally undiscoverable via UI for now — no link is
  planned from anywhere; reachable only by direct URL or a future admin-added Quick Links entry,
  consistent with D5.
- **D15 — Sort field (confirmed):** The `Page` model has no `created` column, only `modified`
  (defaults to creation time, updated on every edit via `update.py`). Sorting uses `modified`, newest
  first, as the closest available proxy — accepted even though an edited page moves back to the top of
  its section.
- **D16 — Row link icon (confirmed):** Rows use `arrow-right.svg`, right-positioned, no `target`
  attribute — the internal-navigation convention already used for `page_list` links in
  `page-header.html`, not `066`'s external-link icon/`target="_blank"` (its rows point off-site).
- **D17 — Section heading counts (confirmed):** No item count next to "Ongoing" / "Archived" — plain
  text headings only.
- **D18 — Empty-state copy (confirmed):** "No ongoing crisis pages." / "No archived crisis pages." —
  section-specific wording rather than a generic message reused for both.

---

## 9. Files Affected

- `ckanext-hdx_theme/ckanext/hdx_theme/views/crisis_pages.py` — new; blueprint `hdx_crisis_pages`,
  route `/crisis-pages`, builds the ongoing/archived lists per §3.
- `ckanext-hdx_theme/ckanext/hdx_theme/plugin.py` — registers `hdx_crisis_pages` in `get_blueprint()`.
- `ckanext-hdx_theme/ckanext/hdx_theme/templates/crisis_pages/main.html` — new page template.
- `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/pages/crisis-pages.less` — new
  page styles (compiles to `fanstatic/v2/pages/crisis-pages.css`).
- `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` — adds the
  `v2-crisis-pages-page-styles` bundle.
