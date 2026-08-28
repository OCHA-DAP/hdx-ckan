# v2 Redesign — Full Implementation Audit

Audit of the v2 redesign as shipped after tasks 001–069. Covers duplication, unification
candidates, convention drift, requirement-doc accuracy, and the `/components` showcase page.

Every finding carries a proposed fix. §7 records the decision on each. The code-level fixes (§1, §2, most of §3, §5) have since landed in a follow-up implementation pass — only B4 (Mailchimp embed Bootstrap classes in `signals.html`) remains outstanding, deferred to next cycle (nothing is visually broken; the form still renders correctly off Bootstrap's own CSS, this is an architectural cleanup only). Documentation corrections (§4, plus a few catalog/convention gaps in §3 and §6) were applied directly in this doc and the files it touches.

## Scope

**Audited:** all `less/v2/**`, `fanstatic/v2/**`, `templates/v2/**`, the v2-extending page
templates, `webassets.yml`'s v2 section, and `requirements/001–069`.

**Excluded** (next cycle, per the task owner): sysadmin dashboard, user settings, user dashboard,
requested data (org page), contribute flow, find/request org.

**Method.** Every count below is reproducible by the grep quoted next to it. Every file path was
resolved against the filesystem. No claim here rests on a requirement doc alone — where a doc and
the code disagreed, the code was treated as the truth and the disagreement recorded as a finding.

---

## 1. Duplication

### A1 — Line-clamp block copy-pasted across 9 component files

`display: -webkit-box; -webkit-line-clamp: N; -webkit-box-orient: vertical; overflow: hidden`
appears as 11 separate declarations in `content-card`, `showcase-card`, `dataviz-card`,
`org-list-card`, `signal-card` (×2), `resource-card`, `page-header`, `dataset-card`, plus a
`-webkit-inline-box` variant in `label.less`. The paired un-clamp
(`-webkit-line-clamp: unset; overflow: visible`) is repeated in `page-header`, `resource-card`
and `dataviz-card`.

```
grep -rc "\-webkit-line-clamp" less/v2/ --include=*.less
```

**Proposed fix.** `.hdx-line-clamp(@lines)` and `.hdx-line-clamp-off()` in `mixins.less`; migrate
all 11 sites. `label.less`'s inline-box variant takes a separate mixin or stays inline.

### A2 — Focus ring repeated 14×

`outline: 2px solid var(--hdx-primary-5); outline-offset: 2px` appears 10 times across
`buttons` (×2), `accordion`, `checkbox`, `drawer`, `dropdown`, `selection`, `signal-card`,
`text-link`, `pages/home`. The dark-surface variant `outline: 2px solid var(--hdx-neutral-0)`
appears 4 times in `navbar` (×3) and `top-bar`.

**Proposed fix.** `.hdx-focus-ring()` / `.hdx-focus-ring-inverse()` in `mixins.less`.

### A3 — Icon `svg {}` block repeated 40×

40 `svg { … }` blocks across 24 files, all doing some subset of `width` / `height` /
`display: block` / `flex-shrink: 0`. Sizes are genuinely divergent (`--hdx-space-4`,
`--hdx-space-5`, `--hdx-space-6`, `1rem`, `1.25rem`, `1.5rem`, `0.9375rem`, `100%`), so this is a
**shape** dedupe, not a value dedupe.

**Proposed fix.** `.hdx-icon-size(@size)` emitting width/height/`display: block`, called with the
existing per-site value. Note the by-product: it makes the divergent sizes visible in one grep,
which may be worth reviewing separately.

### A4 — `nav-controls.less` ships four times

`nav-controls.less` is `@import`ed by `pages/search.less`, `pages/org.less`,
`pages/org-list.less` and `pages/dataviz-gallery.less`, so `.hdx-v2-nav-controls` is compiled into
four separate page bundles. A fifth copy sits in the unbundled `fanstatic/v2/nav-controls.css`,
and `overlay.css` (which *is* in `v2-components-styles`) carries a nested fragment that overrides
a base block only present in the page bundles — so the overlay's nav-controls styling silently
depends on whichever page bundle happens to be loaded.

```
grep -c "hdx-v2-nav-controls" fanstatic/v2/pages/{search,org,org-list,dataviz-gallery}.css
```

**Proposed fix.** Ship it once — add `v2/nav-controls.css` to `v2-page-styles` (it is chrome, not
page-specific) and drop the four `@import`s.

### A5 — Org index hand-rolls the nav-controls markup

`templates/organization/index.html:89-110` writes `hdx-v2-nav-controls` / `hdx-v2-nav-ctrl-pair` /
`hdx-v2-nav-ctrl-label` markup by hand. `templates/dataviz/index.html`,
`templates/organization/members.html` and `templates/search/snippets/package_list.html` all call
`v2/search-nav-controls.html` instead — the snippet that task 059 D4 generalized precisely so that
callers could supply their own option lists and param names.

**Proposed fix.** Route org index through the snippet.

### A6 — FocusTrap implemented twice

`navbar.js:7` defines a `FocusTrap` prototype. `components/drawer.js:11-60` re-implements
focus containment inline, in jQuery. `.claude/skills/hdx-v2-styles/references/conventions.md`
currently instructs authors to *copy* the class when a new component needs one — the duplication
is documented policy, not an accident. A third file, `focus-trap.js`, existed as a shared module
until commit `21a91f2b6e` deleted it.

**Proposed fix.** Promote to `window.hdxV2.FocusTrap` in `utils.js`. The "inline single-consumer
utilities" rule that justified folding it into `navbar.js` no longer holds at two consumers.
`conventions.md` and the skill both need the "copy it" instruction replaced.

---

## 2. Unification candidates

### B1 — `c-kpi-card` and `c-stats-card` are two stat tiles

Both are label + value on a white surface with a row wrapper. `c-kpi-card` adds an info-icon
(hidden below MD); `c-stats-card` adds sublabel/unit plus `--plain` and `--divided` variants.
`c-kpi-card-row` (flex row, `nowrap`, `flex: 1 1 0` children) and
`c-stats-card-list--divided` (flex row, `flex: 1` children, `border-left` separators) are the same
shape.

**This one has history.** Task 058 D14 explicitly chose to build `c-stats-card` as a new component
"over reusing/extending the visually-different `c-kpi-card`", and task 063 D8 then extended
`c-stats-card` rather than `c-kpi-card` for the same reason. A merge reverses two recorded
decisions, so it needs a deliberate call rather than being treated as cleanup.

**Blast radius.** All Locations (`light/group/index.html`), All Organisations
(`organization/index.html`), org Stats tab, location page KPI row.

**Options.**
- (a) Merge into one component with variants — smallest surface, largest change.
- (b) Keep both, unify only the row wrappers (`c-kpi-card-row` → `c-stats-card-list--divided`).
- (c) Leave as-is; record 058 D14 / 063 D8 as the standing answer and close the question.

### B2 — `c-signup-tier` has no component-owned wrapper

**This is the cause of the reported "signup tier looks different in the demo than on the
value-proposition page".** The real layout contract lives in page LESS:
`pages/signup.less:48-62` — `.hdx-v2-signup-tiers-page__tiers`, column at SM, `flex-direction: row`
+ `align-items: stretch` at MD, wider gap at XL. The showcase has no access to it and wraps the
cards in `.demo-row` instead (row, `flex-wrap: wrap`, `align-items: flex-start`, 1.5rem gap), so
the two render at different widths and alignment.

This violates the documented **component wrapper ownership** rule: containers that lay out a set
of `c-*` components belong in that component's own LESS file as `c-<name>-list` / `-grid` / `-row`,
never in page LESS.

**Proposed fix.** Add `c-signup-tier-row` to `components/signup-tier.less`, use it on both the
value-proposition page and the showcase. Worth a sweep for other components in the same position.

---

## 3. Convention drift

| # | Finding | Detail |
|---|---|---|
| B3 | `hdx-v2-*` page class inside `components/` | `components/signal-card.less:108-178` defines `.hdx-v2-signals-cards`, `.hdx-v2-signal-slide`, `.hdx-v2-signals-carousel-footer` and `.hdx-v2-signals-dots`. LESS rules put `hdx-v2-*` patterns at the top level of `less/v2/`, not in `components/`. It also hard-codes `width: 19.938rem` below XL, against "no fixed layout column widths" — contained today only because the parent sets `overflow: hidden` below XL |
| B4 | Bootstrap classes on v2 pages — **one is documented, one is not** | `country/country.html:102-186` (`row`, `col-4`, `col-12`, `d-none`, `mTop35`) is the "Key Figures" block that **063 D5 explicitly left rendering as v1, untouched** — deliberate, not drift; recorded here only so it isn't rediscovered as a bug. `landing_pages/signals.html:95` (`col-12 col-md-10 col-lg-8 mx-auto`) and `:102` (`indicates-required mb-3`) wrap the vendored Mailchimp embed and carry no such decision |
| B5 | jQuery in v2 | `components/drawer.js`, `pages/dataset.js`, `pages/shape-view.js`. Conventions allow the existing few but forbid adding more; `drawer.js` is the only *component* still on it |
| B6 | Direct `breakpoints.less` import | `pages/signals-landing.less:8` imports it alongside `mixins.less`, which already re-exports it. Single-import rule |
| B7 | Unbundled compiled CSS in the repo | `fanstatic/v2/{typography,mixins,radius,overlays,motion,spacing,elevation,breakpoints,colors}.css` are compiled artifacts of token/mixin-only sources that no bundle references. `nav-controls.css` is in the same directory but is a real stylesheet — see A4 |
| B8 | `select.html` has no `/components` demo | Used by `v2/group-message-drawer.html`, `package/contact_contributor.html`, `package/request_access.html`, `organization/members.html`. It has its own row in the skill's component catalog (`dropdown.html`'s row no longer claims a `native` mode); the missing showcase demo itself is tracked as D1 |
| B9 | Layout variable `columns_class` | `v2/page.html:98` reads `columns_class`, a 4th layout var alongside `outer_row_class` / `sidebar_class` / `content_class`. Documented in `CONVENTIONS.md`'s "Layout variable completeness" section and the skill's `workflows.md` |
| B10 | **Not a defect** — inert motion helpers | `.hdx-motion()` (51 call sites) and `window.hdxV2.prefersReducedMotion()` return nothing / `false` by design, per **069's Reduced-motion decision**, at the task owner's request. Restoring real behavior is a one-line uncomment in `mixins.less:243` and `utils.js:108`. Listed as an open follow-up, not a finding |

---

## 4. Requirement docs vs implementation

### 4.1 Stale file paths — mechanical

**43 distinct paths, 74 references, across 30 docs — corrected.** Almost all traced to two
refactors: commit `21a91f2b6e` ("refactor webassets", split `styles.less` / `navigation.less`,
folded `focus-trap.js` and `password-toggle.js` into other files) and `6a16ed33f2` ("reorganize
page level styles", the `-page` suffix → `pages/` move).

Reproduce (now clean) with:

```
grep -ohE '(ckanext-hdx_theme/)?(ckanext/hdx_theme/)?(templates|fanstatic|hdx-styles)/[A-Za-z0-9_./-]+\.(html|less|css|js|svg)' requirements/*.md
```

**Straight renames** (`-page` suffix → `pages/` subdirectory):

| Referenced in docs | Current path |
|---|---|
| `fanstatic/v2/search.js`, `fanstatic/v2/search-page.js` | `fanstatic/v2/pages/search.js` |
| `less/v2/search.less`, `less/v2/search-page.less` | `less/v2/pages/search.less` |
| `fanstatic/v2/dataset.js`, `fanstatic/v2/dataset-page.js` | `fanstatic/v2/pages/dataset.js` |
| `fanstatic/v2/dataset.css` | `fanstatic/v2/pages/dataset.css` |
| `less/v2/dataset.less`, `less/v2/dataset-page.less` | `less/v2/pages/dataset.less` |
| `fanstatic/v2/resource-page.css` | `fanstatic/v2/pages/resource.css` |
| `fanstatic/v2/all-locations-page.js` | `fanstatic/v2/pages/locations-list.js` |
| `less/v2/locations-list-page.less` | `less/v2/pages/locations-list.less` |
| `fanstatic/v2/org-list-page.js` | `fanstatic/v2/pages/org-list.js` |
| `fanstatic/v2/org-members-page.js` | `fanstatic/v2/pages/org-members.js` |
| `less/v2/org-page.less` | `less/v2/pages/org.less` |
| `less/v2/signup-page.less` | `less/v2/pages/signup.less` |
| `less/v2/hapi-landing-page.less` | `less/v2/pages/hapi-landing.less` |
| `fanstatic/v2/signals-landing-page.css` | `fanstatic/v2/pages/signals-landing.css` |
| `fanstatic/v2/crisis-page.css` / `.js` | `fanstatic/v2/pages/crisis.css` / `.js` |
| `less/v2/crisis-page.less` | `less/v2/pages/crisis.less` |
| `fanstatic/v2/location-page.js` | `fanstatic/v2/pages/location.js` |
| `less/v2/location-page.less` | `less/v2/pages/location.less` |
| `fanstatic/v2/perform-reset-page.js` | `fanstatic/v2/pages/perform-reset.js` |
| `fanstatic/shape-view.js` | `fanstatic/v2/pages/shape-view.js` |
| `fanstatic/datasets/contact-contributor.js` | `fanstatic/v2/pages/contact-contributor.js` |
| `fanstatic/datasets/request-access.js` | `fanstatic/v2/pages/request-access.js` |
| `fanstatic/onboarding/verify-email.js` | `fanstatic/v2/pages/verify-email.js` |
| `fanstatic/homepage/bar-chart.js` | `fanstatic/v2/bar-chart.js` |
| `fanstatic/javascript/v2/drawer.js` | `fanstatic/v2/components/drawer.js` |
| `templates/v2/page-header.html` | `templates/v2/components/page-header.html` |
| `fanstatic/v2/components/table.less` | `less/v2/components/table.less` (source vs compiled path error) |
| `hdx-styles/.../v2/components/activity-item.less` | written out in full in 057 as `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/activity-item.less` |

**Superseded, not renamed** — these need a rewritten sentence, not a path swap:

| Referenced in docs | What happened |
|---|---|
| `fanstatic/v2/components/password-toggle.js` | folded into `components/input-field.js` |
| `fanstatic/v2/components/focus-trap.js` | deleted; inlined into `navbar.js` (see A6) |
| `fanstatic/v2/components/dataset-card.js` | superseded by `components/clamped-text.js` |
| `less/v2/components/navigation.less`, `fanstatic/v2/components/navigation.css` | split into `anchor-links` / `breadcrumb` / `nav-item` / `pagination` |
| `less/v2/styles.less`, `fanstatic/v2/styles.css` | split into `components/page-header.less` + `pages/home.less` |
| `less/v2/components.less`, `less/v2/components/index.less` | no aggregator exists; `webassets.yml` lists files individually |
| `templates/v2/navbar-offcanvas.html` | markup lives in `templates/v2/header.html` |
| `templates/package/snippets/activity_stream_v2.html` | relocated to `templates/v2/activity-stream.html` (057 D2/D6 — the doc records the move but still cites the old path elsewhere) |

**Stale class name:** `c-kpi-row` in `048` and `049`; the real class is `c-kpi-card-row`.

### 4.2 Behavior drift — page docs 056–069

| Doc | Finding |
|---|---|
| **056** D3 | Activity, Members, Stats and Datasets tabs are full v2 (057/058/059); Requested Data is the only tab still on v1, matching the excluded-scope list. Doc corrected |
| **056** D14 | Only `requestdata/organization_requested_data.html` extends `organization/read_v1_base.html`; `members.html`, `stats.html` and `activity_stream.html` extend `v2/page.html`. Doc corrected |
| **056** D17 / Files Affected | The hero renders via `templates/v2/org-hero.html`, a shared wrapper used by all four org tabs that calls `page-header.html`. Doc corrected |
| **056** D18 | `contribute.js` is bundled on v2 pages: `v2/contribute.js` is in `v2-page-scripts`. Doc corrected |
| **061** D5 / D6 | The `errors` param, the `c-dropdown--error` / `c-dropdown__error` pair and `option_attrs` live in `v2/components/select.html` (`dropdown.less` carries the error styles, which `select.html` reuses). Doc corrected to name `select.html` throughout, including its Component Mapping table |
| **061** D7 | No `novalidate` remains on either form |
| **062** | `planned-maintenance.html` is not in this repo and has no git history here — it ships from infra outside `hdx-ckan`, per the doc's own deployment story (§Scope, §Context). Not a discrepancy |
| **064** Decision 6 | `widget/onboarding/login.html` has no `h.csrf_input()` and is orphaned (referenced only from commented-out lines in `page.html` / `page_light.html`). The live v2 login form is `user/signin.html:53-56`, which does have it. Doc corrected to name `signin.html` |
| **065** | The only page doc in 056–069 with no "Decisions Taken" section — its decisions are distributed through §§4–7 instead. Structural inconsistency; flagged, no content problem found |
| **068** | All three headline decisions are shipped: D1 (`res.datastore_active` branch in `resource_read.html`), D2 (`validate_csrf` override in `ckanext-hdx_package/.../authorize.py:190-266`), D3 (Data Dictionary AJAX section, `pages/resource.js:48-79`). STATUS.md now reads `implemented`; a `c-spinner` component (D11) was later built and is wired into the Data Dictionary AJAX load and the TDE fetch — doc references corrected accordingly |

Docs **057, 058, 059, 060, 063, 066, 067, 069** re-verified with no behavior drift found beyond the
path staleness in §4.1. Spot-confirmed: 059 D4 (`search-nav-controls.html` generalized and reused
by three callers), 060 D6 (iframe sections container-constrained via `hdx-v2-container`), 063 D8
(`c-stats-card--divided` / `--plain`), 067 D4 (page sizes 12/24/36 in `dataviz/index.html:57`),
069 (motion tokens shipped, reduced-motion deliberately inert).

### 4.3 STATUS.md

All rows read `implemented`. No row exists for any of the six excluded-scope areas, which is
consistent: none of them were ever opened as tasks.

---

## 5. `/components` showcase page

### D1 — Missing demos

`select.html` (4 real call sites, see B8), `c-form-field`, `c-divider`. `graph-point.html` and
`table.html` appear *only* in the showcase — `c-table` reaches real pages via the DataTables path
rather than the snippet, and `c-graph-point` via the charts; worth confirming that is intended
rather than an orphan.

### D2 — Undefined classes

`demo-section__heading` on the Drawer (`components.html:2377`) and Alert (`:2482`) sections, and
`dl-h2` on Avatars (`:1013`), are never defined in the page's `<style>` block. The real classes are
`demo-section__title` and `demo-subsection__heading`.

### D3 — Inconsistent section anchors

17 of ~40 sections carry an `id`; the rest cannot be linked to. There is no table of contents.

### Recorded but out of scope this round

The 250-line inline `<style>` block uses raw hex and raw rem throughout rather than `--hdx-*`
tokens; there are 153 inline `style=` attributes, including the Content Card and Signal Card demos
hand-rolling grids while `c-content-card-grid` already exists; the drawer demos wire behavior with
inline `onclick`. All left untouched by owner's decision.

---

## 6. Conventions inventory

The task brief asked for the conventions in use to be documented on the showcase page; the owner
elected not to add that section this round, so the inventory lands here instead. The authority
remains `CONVENTIONS.md` plus `.claude/skills/hdx-v2-styles/references/conventions.md`.

**In the code, absent from both convention docs:**

- `c-<name>-row` as a third wrapper suffix (`c-kpi-card-row`, `c-selection-item-row`) alongside
  `-list` and `-grid`. Present in the skill; absent from `CONVENTIONS.md`.
- The inert-by-design state of `.hdx-motion()` / `prefersReducedMotion()` (B10) is recorded in 069
  but nowhere a component author would look.

**Documented but violated in shipped code:**

- "No fixed layout column widths" — `signal-card.less:137` (B3).
- "`hdx-v2-*` patterns go at the top level of `less/v2/`, not in `components/`" — same file (B3).
- "Component wrapper ownership" — `c-signup-tier`'s row lives in `pages/signup.less` (B2).
- "Single import: `mixins.less`" — `pages/signals-landing.less:8` (B6).
- "Vanilla JS for all new code" — `components/drawer.js` (B5).
- "Copy the FocusTrap class if a new component needs one" is itself the anti-pattern (A6); the
  rule should be replaced rather than followed.

---

## 7. Decisions

| # | Decision | Rationale |
|---|---|---|
| Scope | Every code-level fix below (§1, §2, most of §3, §5) was decided in this pass and implemented in a follow-up pass. Documentation-only corrections (doc-accuracy fixes, catalog/convention additions) were applied directly in this pass. | Matches how prior docs (061, 065, 067) were finalized before implementation |
| A1 | Apply the proposed fix: `.hdx-line-clamp(@lines)` / `.hdx-line-clamp-off()` in `mixins.less`, migrate all 11 sites. | Landed |
| A2 | Apply the proposed fix: `.hdx-focus-ring()` / `.hdx-focus-ring-inverse()` in `mixins.less`. | Landed |
| A3 | Apply the proposed fix: `.hdx-icon-size(@size)` mixin, called with each site's existing value. | Landed |
| A4 | Apply the proposed fix: ship `nav-controls.css` once via `v2-page-styles`, drop the four page-bundle `@import`s. | Landed |
| A5 | Route `organization/index.html` through `v2/search-nav-controls.html` instead of hand-rolled markup. | Landed |
| A6 | Promote `FocusTrap` to `window.hdxV2.FocusTrap` in `utils.js`; replace the "copy the class" instruction in `conventions.md` and the skill. | Landed |
| B1 | Merge `c-kpi-card` and `c-stats-card` into one component with variants, preserving the exact current visual output on every call site (All Locations, All Organisations, org Stats tab, location page KPI row). | Landed — supersedes 058 D14 / 063 D8. Since then, 3 of those 4 call sites (All Locations, All Organisations, location page KPI/`header_stats` row) have been commented out in a later polish pass — only the org Stats tab still renders the merged component live. |
| B2 | Add `c-signup-tier-row` to `components/signup-tier.less`; use it on both the value-proposition page and the showcase. | Landed |
| B3 | Relocate `.hdx-v2-signals-*` out of `components/signal-card.less` to the top level of `less/v2/`; remove the hardcoded `19.938rem` width at every breakpoint. | Landed |
| B4 | Wrap the Mailchimp embed in `landing_pages/signals.html` with v2-equivalent layout classes instead of Bootstrap grid classes. | Deferred to next cycle — nothing is visually broken today (Bootstrap's own CSS still styles the form); this is an architectural cleanup on a live, complex third-party embed with no existing v2 CSS to build on |
| B5 | Rewrite `components/drawer.js` in vanilla JS, closing the last component-level jQuery dependency. | Landed |
| B6 | Drop the direct `breakpoints.less` import in `pages/signals-landing.less` (keep the `mixins.less` import only). | Landed |
| B7 | Leave the nine unbundled compiled CSS files in `fanstatic/v2/` in place. | No cleanup needed |
| B8 | Documented: `select.html` added to the skill's component catalog; `dropdown.html`'s row no longer claims a `native` mode. | Done in this pass |
| B9 | No action needed — `columns_class` is already documented in `CONVENTIONS.md`'s "Layout variable completeness" section and the skill's `workflows.md`. | Not a live finding |
| B10 | No action — inert motion helpers are intentional per 069. | Standing decision |
| 4.1 | Stale file paths corrected across affected requirement docs; stale `c-kpi-row` class name corrected to `c-kpi-card-row` in 048/049. | Done in this pass |
| 4.2 | Behavior-drift corrected in 056 (D3, D14, D17, D18), 061 (D5/D6 filename + Component Mapping table), 064 (Decision 6). | Done in this pass |
| 062 | `planned-maintenance.html` ships from infra outside this repo — not a discrepancy, no doc change needed beyond the note already added to this audit. | Resolved |
| 068 | STATUS.md updated to `implemented`; a `c-spinner` component was later built and wired into the Data Dictionary AJAX load and the TDE fetch — doc references corrected accordingly. | Done in this pass |
| D1 | Add showcase demos for `select.html`, `c-form-field`, `c-divider`. `table.html` / `graph-point.html` confirmed intentionally showcase-only — no orphan cleanup needed. | Landed |
| D2 | Rename the undefined showcase classes (`demo-section__heading` → `demo-subsection__heading`, `dl-h2` → the real class) to match what's actually defined. | Landed |
| D3 | Add `id`s to every showcase section plus a table of contents. | Landed |
