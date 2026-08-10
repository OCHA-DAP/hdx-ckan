# v2 Audit & Standardization

**Type**: Analysis / Requirement Definition

---

## Context

Tasks 001–041 have implemented the v2 redesign across search, dataset, and resource pages. This document audits the current state of the entire v2 implementation — templates, components, snippets, styles, webassets, and JS — with the goal of identifying structural gaps, missing rules, code quality issues, and refactor opportunities.

**Nothing is implemented here. No behavior changes. No refactoring.**
Findings are documented so that decisions can be made deliberately, not silently.

---

## 1. Discovery Summary

### Scope Audited

| Layer | Paths covered |
|---|---|
| Base template | `templates/v2/page.html` |
| Layout sections | `templates/v2/header.html`, `templates/v2/footer.html`, `templates/v2/components/page-header.html` |
| Page templates | `templates/search/search.html`, `templates/package/hdx_read.html`, `templates/package/resource_read.html` |
| Components | All 27 files in `templates/v2/components/` |
| Snippets | `templates/v2/search-filters.html`, `templates/v2/search-nav-controls.html`, `templates/search/snippets/package_item_v2.html` |
| LESS source | `hdx-styles/src/common/less/v2/` (all files) |
| Compiled CSS | `fanstatic/v2/` (all files) |
| JS | `fanstatic/v2/*.js` + `fanstatic/v2/components/*.js` |
| Webassets config | `fanstatic/webassets.yml` lines 223–322 |

### What Was NOT Audited

- Navbar sub-panels (`navbar-notifications.html`, `navbar-user-menu.html`, `navbar-offcanvas.html`) — light review only
- Admin views (`package_item_admin.html`)
- Components not yet linked to any page: `showcase-card`, `tooltip`, `autocomplete`, `graph-point`, `toggle`, `radio`, `avatar`
- v1 templates (out of scope)
- Backend / Python helpers

---

## 2. Violations — Constraint Enforcement

### Existing rule
> Components must be called via `{% snippet 'v2/components/...' %}` from snippets or pages. Direct macro invocation is forbidden outside the design-system demo page.

### Findings

| Finding | Location | Severity |
|---|---|---|
| ✅ No violations — all components called via snippet | v2 page templates | — |
| ⚠️ Footer uses `{% include %}`, header uses `{% snippet %}` | `v2/page.html:132` vs `:50` | Low |
| ℹ️ SVG icons use `{% include h.url_for_static(...) %}` inside components | e.g. `button.html:116`, `label.html:59` | Informational |

**Footer include detail:**
```jinja2
{# header — correct #}
{% snippet 'v2/header.html' %}

{# footer — inconsistent #}
{% include "v2/footer.html" %}
```
`footer.html` is a layout section, not a component, so the snippet rule may not strictly apply. But the inconsistency is undocumented and creates ambiguity for future layout sections.

**SVG icon include:**
The `{% include h.url_for_static(...) %}` pattern for inline SVGs is intentional and correct — it inlines the SVG markup. This is distinct from the snippet system. However, there is no written rule that distinguishes "inline SVG = `{% include %}`" from "layout section = ambiguous".

### Design-system page exception
`templates/v2/components.html` renders component demos directly. This is the only legitimate exception to the snippet rule and is already documented implicitly by its standalone nature.

---

## 3. Missing Constraints — New Rules to Define

The following rules do not currently exist in writing. They are proposed here for review. **No decision has been made on any of them.**

---

### A. Layout variable completeness

**Proposed rule:**
Every v2 page template that extends `v2/page.html` and uses the two-column layout MUST set all four layout variables at the top of the template:

```jinja2
{% set outer_row_class = '...' %}
{% set columns_class   = '...' %}
{% set sidebar_class   = '...' %}
{% set content_class   = '...' %}
```

**Current gap:**
`search/search.html` sets only `sidebar_class` and `content_class`. The outer wrapper div and the columns modifier class have no page-specific class applied.

| Variable | search.html | hdx_read.html | resource_read.html |
|---|---|---|---|
| `outer_row_class` | ✅ `hdx-v2-search-row` | ✅ `hdx-v2-dataset-row` | ✅ `hdx-v2-resource-row` |
| `columns_class` | ❌ unset | ✅ `hdx-v2-content-columns--gap-xl` | ✅ `hdx-v2-content-columns--gap-xl hdx-v2-resource-columns` |
| `sidebar_class` | ✅ generic `__sidebar --xl-only --sticky` + `hdx-v2-search-sidebar` | ✅ generic `__sidebar --xl-only` + `hdx-v2-dataset-sidebar` | ✅ generic `__sidebar --xl-only` + `hdx-v2-resource-sidebar` |
| `content_class` | ✅ generic `__content` + `hdx-v2-search-content` | ✅ generic `__content` | ✅ generic `__content` + `hdx-v2-resource-content` |

---

### B. `{% snippet %}` vs `{% include %}` rule

**Proposed rule (to confirm):**

| Usage | Method | Rationale |
|---|---|---|
| v2 components | `{% snippet 'v2/components/...' %}` | Always — enables parameterization |
| v2 layout sections (header, footer) | `{% snippet '...' %}` | Consistency (currently inconsistent) |
| Inline SVG icons | `{% include h.url_for_static(...) %}` | Intentional — inlines SVG markup |
| Non-parameterized partials | TBD — see Open Questions | Undecided |

---

### C. Webassets dependency encoding

**Proposed rule:**
Page-level style dependencies MUST be declared via `preload:` in `webassets.yml`, not via `{% asset %}` calls in templates.

**Current gap:**
`resource_read.html` manually loads two asset bundles:
```jinja2
{% asset 'hdx_theme/v2-dataset-styles' %}
{% asset 'hdx_theme/v2-resource-styles' %}
```
The dependency between resource styles and dataset styles is encoded in the template, not in the webassets config. By contrast:
```yaml
# v2-search-styles — correct pattern
v2-search-styles:
  extra:
    preload:
      - hdx_theme/v2-page-styles
  contents:
    - v2/search.css
```
The resource page should follow the same pattern, with `v2-resource-styles` preloading `v2-dataset-styles`.

---

### D. `v2=True` gate policy

**Proposed rule (to confirm):**
Define when `{% if v2 %}` guards are required vs when a template is always-v2.

**Current state:**

| Template | v2 gate used? |
|---|---|
| `search/search.html` | ✅ — `{% if v2 %}` present |
| `search/snippets/package_list.html` | ✅ — entire layout switched |
| `search/snippets/search_results_wrapper.html` | ✅ — pagination layout switched |
| `package/hdx_read.html` | ❌ — always v2 |
| `package/resource_read.html` | ❌ — always v2 |

There is no rule for when a page is promoted from "gated" to "always v2".

---

### E. Toolbar block override rule

**Proposed rule:**
Every template extending `v2/page.html` MUST override `{% block toolbar %}`. The fallback in `v2/page.html` uses v1 class names (`toolbarRow`, `.toolbar`) and should never render on a v2 page.

**Current state:** All three v2 pages already override this block. The rule is followed in practice but not written.

---

## 4. Structural Inconsistencies

### 4.1 Page-level layout variable coverage

See Section 3A table. Search page is missing `outer_row_class` and `columns_class`.

### 4.2 `secondary_right_side` sidebar class gap

In `v2/page.html:113–117`:
```jinja2
{% if secondary_block_output|trim != '' and secondary_right_side %}
  <div>                          {# ← no class applied here #}
    {{ secondary_block_output }}
  </div>
{% endif %}
```
When `secondary_right_side=True`, the sidebar wrapper renders with no class. `sidebar_class` is only applied to the left-side variant (line 106). This means any future page using `secondary_right_side` will get an unclassed wrapper.

**Current impact:** Zero — no v2 page sets `secondary_right_side`. Latent bug.

### 4.3 Feature comparison across pages

| Feature | Search | Dataset | Resource |
|---|---|---|---|
| `pre_primary` block (page header) | ❌ | ✅ | ✅ |
| Mobile anchor navigation | ❌ (filter overlay instead) | ✅ sticky dropdown | ✅ sticky dropdown |
| Sidebar border-right | ✅ | ✅ | ❌ |
| `v2=True` gate | ✅ | ❌ | ❌ |
| Dedicated script bundle | ✅ `v2-search-scripts` | ✅ `v2-dataset-scripts` | ❌ none |

### 4.4 Breadcrumb row — container handling

All three pages override `{% block toolbar %}` with:
```jinja2
<div class="hdx-v2-breadcrumb-row">
  {% snippet 'v2/components/breadcrumb.html', ... %}
</div>
```
This is consistent. The breadcrumb row is full-width; the breadcrumb component manages its own internal padding. The v1 fallback toolbar in `v2/page.html` wraps its content in `hdx-v2-container` — but since all pages override the block, this fallback is never used.

---

## 5. Layout Recommendations

### 5.1 Standard layout model (current — no change proposed)

The container hierarchy is consistent across all three pages:

```
<div class="{{ outer_row_class }}">           ← full-width row
  <div class="hdx-v2-container">              ← max-width + padding
    <div class="hdx-v2-content-columns        ← flex, stretch
                {{ columns_class }}">
      <div class="{{ sidebar_class }}">       ← secondary block (left)
        [sidebar content]
      </div>
      <div class="{{ content_class }}">       ← primary block
        [main content]
      </div>
    </div>
  </div>
</div>
```

This model is sound. The only gap is search missing the top two classes (Section 3A).

### 5.2 Flash messages

`v2/page.html:77–89` — flash messages use Bootstrap 5 classes:
```jinja2
<div class="alert alert-dismissible fade show {{ category }}">
```

Bootstrap 5 is loaded in `v2-page-styles`, so this renders correctly. However:
- The flash messages block has not been redesigned for v2 (no design tokens, no v2 component)
- Bootstrap `.alert` classes are outside the v2 design system
- The v2 constraint doc (`prompt-template.md`) prohibits Bootstrap class usage: `❌ No Bootstrap`

This is a known gap, not a new finding. See Open Question 5.

### 5.3 Toolbar fallback in v2/page.html

`v2/page.html:58–75` — the default `{% block toolbar %}` uses v1 class names:
```jinja2
<div class="toolbarRow">
  <div class="hdx-v2-container">
    <div class="toolbar">
```

Since all v2 pages override this block, the fallback is dead code within the v2 context. Updating it to use v2 naming would be low-risk. See Refactor Opportunities.

### 5.4 `secondary_right_side` wrapper

If any future page uses `secondary_right_side=True`, the sidebar wrapper div needs `sidebar_class` applied. Current code applies `sidebar_class` only to the left-side variant. This is a one-line fix. See Refactor Opportunities.

---

## 6. Webassets Recommendations

### 6.1 Current v2 bundle hierarchy

```
v2-components-styles
  ← foundation.css
  ← [15 component CSS files]

v2-page-styles
  ← preloads: v2-components-styles
  ← Bootstrap5, layout.css, top-bar.css, footer.css, navbar.css, styles.css

v2-search-styles
  ← preloads: v2-page-styles
  ← search.css

v2-dataset-styles
  ← preloads: v2-page-styles
  ← dataset.css

v2-resource-styles
  ← preloads: v2-page-styles        ← gap: should preload v2-dataset-styles
  ← resource-page.css
```

### 6.2 Resource styles dependency gap

`resource_read.html` loads:
```jinja2
{% asset 'hdx_theme/v2-dataset-styles' %}
{% asset 'hdx_theme/v2-resource-styles' %}
```

The correct pattern (matching search/dataset) would be:
```yaml
v2-resource-styles:
  extra:
    preload:
      - hdx_theme/v2-dataset-styles   # ← add this
  contents:
    - v2/resource-page.css
```
Then the template loads only `v2-resource-styles` and the preload chain handles the rest.

### 6.3 Missing `v2-resource-scripts` bundle

Dataset page has `v2-dataset-scripts` (preloads `v2-page-scripts` + `dataset.js`).
Resource page has no equivalent bundle. Resource-page JS is currently served only via the component scripts preloaded in `v2-page-scripts`. If resource-specific JS grows, there is no dedicated bundle to add it to.

### 6.4 Legacy assets in v2/page.html

```jinja2
{# v2/page.html:181 #}
{% asset 'hdx_theme/page-scripts' %}   {# TODO comment present #}

{# v2/page.html:12–16, 185–189 #}
{% asset 'hdx_theme/onboarding-bulk-user-styles' %}
{% asset 'hdx_theme/onboarding-bulk-anon-styles' %}
{# and corresponding scripts #}        {# TODO comment present #}
```

Both are explicitly flagged by the developer with `# TODO: check whether we still need these once the redesign has been completed`. They load v1 assets into every v2 page. See Open Question 3.

### 6.5 CSS duplicate — `.hdx-v2-content-columns`

The selector is declared as a top-level rule in two LESS files:

| File | Line | Purpose |
|---|---|---|
| `layout.less` | 38 | Canonical definition: `display: flex; align-items: stretch` |
| `search.less` | 128 | Re-declaration to nest `.hdx-v2-search-sidebar` inside it |

The `search.less` usage is a valid LESS nesting pattern, but it emits a duplicate top-level selector in the compiled CSS. The sidebar styles could instead be placed outside the `.hdx-v2-content-columns` wrapper.

### 6.6 Empty CSS token files in bundle

The following files in `v2-components-styles` compile to zero output lines:

```
v2/breakpoints.css, v2/colors.css, v2/typography.css,
v2/spacing.css, v2/elevation.css, v2/radius.css, v2/overlays.css
```

Only `v2/foundation.css` (120 lines) emits `:root` CSS custom properties. The individual token files are LESS build artifacts — they contain only LESS variable definitions that compile to nothing. Including them in the bundle adds no CSS but does add entries to the webassets manifest. See Open Question 8.

---

## 7. Code Quality Findings

### 7.1 Legacy primary block in `v2/page.html`

`v2/page.html:142–178` contains the default `{% block primary %}` — inherited verbatim from `page.html` (v1). It includes:
- `module-content` class
- `nav nav-tabs` navigation
- `content_action` block
- `page_primary_action` block

None of these are used by current v2 pages. All three page templates override `{% block primary_content_inner %}` or define the full primary block themselves. The v1 sub-blocks remain as dead code within the v2 context.

**Risk of removing:** Any v2-extended template that does NOT override the primary block would lose its fallback structure. Likely safe to simplify, but needs confirmation of full page inventory.

### 7.2 `secondary_right_side` class gap

`v2/page.html:114` renders `<div>` with no class when `secondary_right_side=True`:
```jinja2
{% if secondary_block_output|trim != '' and secondary_right_side %}
  <div>                  {# sidebar_class not applied #}
    {{ secondary_block_output }}
  </div>
{% endif %}
```
Compare to left-side variant at line 106:
```jinja2
<div class="{{ sidebar_class if sidebar_class else '' }}">
```
Currently unreachable — no v2 page sets `secondary_right_side`. One-line fix.

### 7.3 Legacy script loading order

```jinja2
{# v2/page.html:180–183 #}
{% block scripts %}
  {% asset 'hdx_theme/page-scripts' %}    {# v1 jQuery-based modules first #}
  {{ super() }}
  {% asset 'hdx_theme/v2-page-scripts' %} {# v2 vanilla JS second #}
```
The v1 legacy scripts load before v2 scripts. If v1 jQuery modules and v2 JS modules target the same DOM elements, ordering could cause behavioral conflicts. This is flagged, not confirmed as a bug.

### 7.4 `components.html` design system page

`templates/v2/components.html` renders the design token documentation (colors, typography, spacing, shadows, radius). It renders directly without extending `v2/page.html`. This is intentional for a standalone demo page, but it is not documented anywhere as a special exception to the layout rule. No action required — informational only.

### 7.5 Onboarding assets loading

Onboarding assets are loaded on every v2 page for all users (either user or anonymous variant). This was appropriate during v1 when onboarding was universally active. The developer's TODO comment suggests these may no longer be needed once the redesign is complete. See Open Question 3.

---

## 8. Refactor Opportunities (NOT Implemented)

These are identified safe improvements. **None should be implemented without resolving the relevant Open Questions first.**

| Opportunity | File | Open Question |
|---|---|---|
| Add `outer_row_class` + `columns_class` to `search.html` | `search/search.html` | D2 |
| Apply `sidebar_class` to right-side secondary wrapper | `v2/page.html:114` | D10 |
| Move `v2-dataset-styles` preload to `webassets.yml` | `webassets.yml` + `resource_read.html` | D4 |
| Add `v2-resource-scripts` bundle | `webassets.yml` | D8 |
| Remove empty token CSS from `v2-components-styles` bundle | `webassets.yml` | D8 |
| Replace `{% include "v2/footer.html" %}` with `{% snippet %}` | `v2/page.html:132` | D1 |
| Update fallback `{% block toolbar %}` to use v2 class names | `v2/page.html:59–61` | — |
| Audit and remove `page-scripts` + `onboarding-bulk-*` | `v2/page.html:12–16, 181, 185–189` | D3 |
| Remove unused v1 sub-blocks from `{% block primary %}` | `v2/page.html:142–178` | D6 |
| Define `v2=True` promotion policy; evaluate removing gate | `search/search.html` + snippets | D7 |
| Document inline SVG `{% include %}` as an explicit rule | CONVENTIONS.md or comments | — |

---

## 9. Decisions Taken

---

**D1 — `{% snippet %}` vs `{% include %}` for layout sections** → **Require `{% snippet %}` everywhere**
All v2 layout sections including `footer.html` must use `{% snippet %}`. Fix `{% include "v2/footer.html" %}` in `v2/page.html:132`.

---

**D2 — Layout variable completeness rule** → **Enforce all four variables**
Every v2 page using the two-column layout must set `outer_row_class`, `columns_class`, `sidebar_class`, and `content_class`. Add the missing `outer_row_class` and `columns_class` to `search/search.html` in this task.

---

**D3 — Legacy assets in `v2/page.html`** → **Comment out, do not remove**
`page-scripts` and `onboarding-bulk-*` assets are commented out in place. They are not removed — their status (still needed or not) is not yet confirmed. The existing TODO comments stay.

---

**D4 — Webassets preload chain for resource styles** → **Separate resource and dataset styles entirely**
`v2-resource-styles` does not declare a preload dependency on `v2-dataset-styles`. The two bundles are independent. The manual `{% asset %}` calls in `resource_read.html` remain as-is and are now a deliberate, documented choice, not a gap.

---

**D5 — Flash messages redesign** → **Remove Bootstrap classes**
Replace `.alert .alert-dismissible .fade .show` with v2 token-based styling. Bootstrap is not used for flash messages on v2 pages.

---

**D6 — Backward compatibility with v1** → **Gradual — keep for now, flag for removal**
Unused v1 sub-blocks in `v2/page.html` (Section 7.1) and v1 asset patterns (Section 7.3) are retained but annotated with `{# TODO: remove when v1 is retired #}` comments. No removal in this task.

---

**D7 — `v2=True` gate policy** → **Define a policy; search stays gated for now**
Policy: pages are gated with `{% if v2 %}` during rollout and promoted to always-v2 when v1 is retired for that page. `search.html` and its related snippets remain gated. The policy is documented but no gate is removed in this task.

---

**D8 — Webassets reorganization scope** → **Aggressive, v2 entries only**
Any safe structural change to v2-related webassets entries is acceptable: remove empty token file entries from `v2-components-styles`, add `v2-resource-scripts` bundle, clean up v2 bundle hierarchy. v1 bundle entries are not touched.

---

**D9 — Layout breaking changes** → **Acceptable**
Class-level changes to v2 layout wrappers are acceptable. No external CSS depends on these classes.

---

**D10 — `secondary_right_side` feature** → **Remove entirely**
No planned v2 page uses `secondary_right_side`. Remove the feature and its conditional branch from `v2/page.html`. Simplifies the template.

---

## Files Affected

| File | Change |
|---|---|
| `templates/v2/page.html` | Replace `{% include "v2/footer.html" %}` with `{% snippet %}`; remove `secondary_right_side` branch; replace Bootstrap flash classes with v2 tokens; add `{# TODO: remove when v1 is retired #}` to v1 sub-blocks and v1 asset calls; update toolbar fallback class names |
| `templates/search/search.html` | Add `outer_row_class` and `columns_class` |
| `fanstatic/webassets.yml` | Remove empty token file entries from `v2-components-styles`; add `v2-resource-scripts` bundle; v2 scope only |

No new components, snippets, or LESS files are required.
