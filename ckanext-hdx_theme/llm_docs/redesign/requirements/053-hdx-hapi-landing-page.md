# 053 — HDX HAPI Landing Page (v2)

**Scope:** Migrate the HAPI landing page to v2 — full page layout, all content sections,
sticky sidebar navigation, new `c-accordion` component, partner logo grid.
**Excluded:** backend data changes, new business logic, analytics changes, Data Availability
iframe content (keep as-is).
**Figma sources:** `hapi-xl.html`, `hapi-md.html`, `hapi-sm.html`

---

## Context

The HAPI landing page (`/hapi/`) currently extends `page_light.html` and uses the v1 BEM
block component system (Bootstrap-based). The v2 redesign migrates it to `v2/page.html`,
introduces a sticky sidebar for jump navigation. The accordion (FAQ) and partner logo grid
are rebuilt using v2 patterns. The Data Coverage section (present in constants) is out of
scope and not rendered.

This is the first v2 landing page, so the patterns established here — custom hero section,
`c-accordion` component, inline logo grid — may influence future landing pages.

---

## 1. Existing Page Audit

### Templates & Assets

| Item | Path |
|---|---|
| **Main template** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/hapi.html` |
| **Base template** | `page_light.html` — must be migrated to `v2/page.html` |
| **Constants** | `ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/landing_pages/hapi.py` |
| **JS** | `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/landing_pages/hdx_hapi.js` |

**Current asset bundles:** `page-extra-light-styles`, `bem-blocks-styles`,
`hdx-hapi-scripts`, `bem-blocks-scripts`

### Current Sections (v1, in order)

| Section | Anchor | Component |
|---|---|---|
| Hero | — | `bem.blocks/hero.html` — title, description (email link), HAPI logo image, jump nav links |
| Data Availability | `#data-availability` | Full-width `<iframe src="/visualization/hapi-availability-v2/">` (866px) |
| Be Inspired | `#be-inspired` | `bem.blocks/heading.html` + `bem.blocks/paragraph.html` + 4× `bem.blocks/card.html` (Bootstrap grid) |
| FAQ | `#faq` | `bem.blocks/heading.html` + `bem.blocks/faq.html` (Bootstrap collapse) |
| Partners | — | `bem.blocks/heading.html` + `bem.blocks/partners.html` (v1 carousel, 10 logos) |

### Template Variables

| Variable | Source | Notes |
|---|---|---|
| `CONST` | `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['HAPI_LANDING_PAGE']` | Hero title/desc, card titles/texts/links, section labels |
| `faq_data` | Passed from view | List of `{question, answer}` dicts |
| `partners` | `PARTNERS_CONSTANTS` via view | 10 `(slug, label)` tuples |
| `sections` | `SECTIONS_CONSTANTS` via view | 4 jump-nav items (Data Availability, Be Inspired, FAQ, Docs) |
| `data_coverage` | **Not currently passed** | `DATA_COVERAGE_CONSTANTS` — 12 rows in `hapi.py`, never rendered |

### DATA_COVERAGE_CONSTANTS (unused in v1)

12 rows, each with `{category, subcategory, contributor, link}`:

| Category | Subcategory | Contributor |
|---|---|---|
| Affected People | Humanitarian Needs | OCHA offices |
| Affected People | Internally-Displaced Persons | IOM |
| Affected People | Refugees and Persons of Concern | UNHCR |
| Affected People | Returnees | UNHCR |
| Coordination & Context | Conflict Events | ACLED |
| Coordination & Context | Funding | OCHA FTS |
| Coordination & Context | National Risk | INFORM |
| Coordination & Context | Operational Presence | OCHA offices |
| Food Security & Nutrition | Food Prices | WFP |
| Food Security & Nutrition | Food Security | FSNWG |
| Population & Socio-economy | Baseline Population | UNFPA / OCHA |
| Population & Socio-economy | Poverty Rate | OPHI |

### Existing BEM Components Used (v1 only)

| Component | File | Status in v2 |
|---|---|---|
| `bem.blocks/hero.html` | `templates/bem.blocks/hero.html` | Not reused — replaced by custom v2 hero section |
| `bem.blocks/faq.html` | `templates/bem.blocks/faq.html` | Not reused — replaced by new `c-accordion` |
| `bem.blocks/partners.html` | `templates/bem.blocks/partners.html` | Not reused — replaced by inline logo grid |
| `bem.blocks/card.html` | `templates/bem.blocks/card.html` | Not reused — replaced by page-specific card snippet |
| `bem.blocks/heading.html` | `templates/bem.blocks/heading.html` | Not reused — section headings via tokens directly |

---

## 2. Figma Mapping

### Page Sections (all breakpoints, in order)

| # | Section | Anchor | Status |
|---|---|---|---|
| 1 | Page Header / Hero | — | Redesigned (uses `c-page-header` with subtitle + logo) |
| 2 | Data Availability | `#data-availability` | Kept (iframe unchanged) |
| 3 | Be Inspired | `#be-inspired` | Redesigned (new card style) |
| 4 | FAQ | `#faq` | Redesigned (new `c-accordion`) |
| 5 | Partners | `#partners` | Redesigned (v2 logo grid) |

### XL Layout (`hapi-xl.html`)

```
[navbar / breadcrumb]              ← standard v2 chrome
[page-header / hero]
  Left (flex: 1):
    h1 "HDX HAPI" (Merriweather) — CONST.HERO_SHORT_TITLE
    subtitle (semibold): CONST.HERO_SECTION_TITLE
    description (regular): CONST.HERO_SECTION_DESCRIPTION (email link)
  Right (logo card):
    HAPI logo image
[body]                             ← hdx-v2-content-columns, bg: var(--hdx-neutral-01)
  [sidebar] (25%, left, sticky via .c-anchor-links-wrapper)
    c-anchor-links (no heading):
      • Data Availability   (active)
      • Be Inspired
      • FAQ
      • Partners
      • Documentation       (external link, new tab)
  [content] (flex: 1)
    [data-availability]
      <iframe src="/visualization/hapi-availability-v2/"> (no section heading)
    [c-divider]
    [be-inspired]
      section heading
      card grid (2 per row at all breakpoints):
        4 c-content-card components — title + desc + c-text-link
    [c-divider]
    [faq]
      section heading "FAQ"
      c-accordion (flattened from faq_data, first item open by default)
    [c-divider]
    [partners]
      section heading
      logo grid (5 per row, direct img — no container)
[footer]
```

### MD Layout (`hapi-md.html`)

- Sidebar: **hidden** — `c-anchor-links-mobile` dropdown provides jump navigation
- Page header: same structure, narrower container
- Be Inspired cards: 2 per row (flex-wrap)
- Partner logos: 6 per row (same as XL, smaller logo box height: 5.568rem)
- FAQ accordion: full-width, same 8 items

### SM Layout (`hapi-sm.html`)

- Sidebar: **hidden** — `c-anchor-links-mobile` dropdown
- Page header: stacked (title + desc + logo box full-width, then sign-up button)
- Be Inspired cards: 2 per row
- Partner logos: **4 per row** (logo box height: 4.131rem)
- FAQ accordion: full-width

### Breakpoint Summary

| Feature | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Sidebar | Visible, left, 25% | Hidden | Hidden |
| Mobile nav dropdown | Hidden | Visible | Visible |
| Content | `flex: 1` | Full width | Full width |
| Page header | Horizontal (text left, logo right) | Adjusted widths | Stacked |
| Be Inspired cards | 2 per row | 2 per row | 2 per row |
| Partner logos | 5 per row, 7.5rem height | 5 per row | 5 per row |
| Container padding | 3rem sides | 3rem sides | 1rem sides |

### Colors (from Figma)

| Token / Value | Usage |
|---|---|
| `#fafbfb` | Page header / hero background |
| `var(--hdx-neutral-2)` (`#ebeff0`) | Card borders, accordion item borders |
| `#e9f5f1` (mint) | Partner logo box background |
| `var(--hdx-primary-5)` | Active sidebar item border, links, buttons |
| `var(--hdx-neutral-95)` | Body text |
| `var(--hdx-neutral-8)` | Muted / description text |

---

## 3. Component Strategy

| UI Element | Decision | Justification |
|---|---|---|
| Page header / hero | **Reuse** `c-page-header` | Extended with `subtitle` param (semibold paragraph) and conditional divider/metadata strip (hidden when no dataset meta is passed). Background `var(--hdx-neutral-01)`. |
| Sidebar nav | **Reuse** `c-anchor-links` | Wrapper now always renders (sticky regardless of heading). `nav_items` at top-level template scope, no heading passed. |
| Section dividers | **Reuse** `c-divider` | Exists; matches Figma 1px `var(--hdx-neutral-3)` rule |
| Be Inspired cards | **New `c-content-card` component** | New reusable component: title (2-line clamp) + description + `c-text-link`. Added to `v2-components-styles` bundle. |
| Data Coverage | **Out of scope** | Not rendered in v2; `DATA_COVERAGE_CONSTANTS` not passed to template |
| FAQ / Accordion | **New `c-accordion` component** | No v2 accordion exists; `bem.blocks/faq.html` uses Bootstrap collapse — incompatible with v2; reusable for future landing pages |
| Partner logos | **Inline grid** in page template | 10 static logos, HAPI-only use case; extract to `c-logo-grid` component only when a second page needs it |
| Text links (description) | **Reuse** `c-text-link` | Standard v2 hyperlink styling |
| Breadcrumb | Standard v2 breadcrumb block | No change from v2 page base |
| Mobile nav section indicator | **Reuse** `c-anchor-links-mobile` | Already part of `anchor-links.html`; handles SM/MD navigation |

---

## 4. c-accordion Specification (NEW COMPONENT)

### Approach: `<details>` / `<summary>`

Native HTML. No JS needed for open/close. Accessible by default (keyboard: Enter/Space;
screen readers announce expanded/collapsed state). CSS handles chevron rotation and
body reveal animation.

### Files

| File | Path |
|---|---|
| LESS | `hdx-styles/src/common/less/v2/components/accordion.less` |
| Template | `templates/v2/components/accordion.html` |
| JS | None (CSS-only) |

### BEM Structure

```html
<div class="c-accordion">

  <details class="c-accordion__item" open>   <!-- `open` for default-open -->
    <summary class="c-accordion__trigger">
      <span class="c-accordion__title">Question text here</span>
      <img class="c-accordion__chevron" src="..." alt="">
    </summary>
    <div class="c-accordion__body">
      <div class="c-accordion__content">
        Answer text here. May include links.
      </div>
    </div>
  </details>

  <details class="c-accordion__item">
    ...
  </details>

</div>
```

### States

| State | CSS selector | Visual |
|---|---|---|
| Closed | `.c-accordion__item` (default) | `border-top: 1px solid var(--hdx-neutral-2)`, padding `var(--hdx-space-8)`, chevron pointing down |
| Open | `.c-accordion__item[open]` | Same border/padding, chevron pointing up (CSS `rotate(180deg)`), body visible |
| Focus | `.c-accordion__trigger:focus-visible` | Standard v2 focus ring |
| Hover | `.c-accordion__trigger:hover` | Background `var(--hdx-neutral-1)` or title color shift |

No `is-open` or `is-closed` class — rely entirely on the native `[open]` attribute.

### Animation

```less
.c-accordion__body {
    overflow: hidden;
}

// CSS-only height transition via interpolation
// (use max-height trick if ::details-content not supported cross-browser)
.c-accordion__item:not([open]) .c-accordion__body {
    display: none; // fallback; progressive enhancement adds transition
}

.c-accordion__chevron {
    transition: transform 0.2s ease;
}
.c-accordion__item[open] .c-accordion__chevron {
    transform: rotate(180deg);
}
```

Note: Smooth `height` transition with `<details>` requires `::details-content` (limited
browser support as of 2025) or a JS-added max-height approach. Implement CSS-only first;
add JS enhancement if animation is required per design review.

### Snippet Parameters

| Param | Type | Required | Notes |
|---|---|---|---|
| `items` | list | yes | List of `{question, answer, open}` dicts |

`open` field on an item: set `<details open>` for that item (default-open state). The **first item is open by default** on the HAPI page — set `open: True` on the first FAQ entry in `faq_data`.

### Analytics

Add `data-ga-event` attributes to `.c-accordion__trigger` to carry over v1 FAQ analytics. Reuse the same GA event names from `bem.blocks/faq.html` so existing tracking remains consistent.

```html
<summary class="c-accordion__trigger"
         data-ga-event="accordion_toggle"
         data-ga-label="{{ item.question }}">
```

### Template

```jinja2
<div class="c-accordion">
  {% for item in items %}
    <details class="c-accordion__item"{% if item.open %} open{% endif %}>
      <summary class="c-accordion__trigger">
        <span class="c-accordion__title">{{ item.question }}</span>
        {% snippet 'v2/icons/chevron-down.html' %}
      </summary>
      <div class="c-accordion__body">
        <div class="c-accordion__content">
          {{ item.answer }}
        </div>
      </div>
    </details>
  {% endfor %}
</div>
```

### Accessibility Notes

- `<details>` / `<summary>` have native ARIA semantics (`role="group"`, `role="button"`)
- Keyboard: Tab focuses `<summary>`; Enter/Space toggles
- Screen readers: announce "summary, collapsed/expanded"
- The `<summary>` must NOT contain other interactive elements (links break the pattern)
- Answer text may contain links — these are inside `.c-accordion__body`, not `<summary>`, so no conflict

---

## 5. Partner Logos Strategy

**Decision: inline in HAPI template** (not a standalone component).

Rationale: 10 static logos, used only on the HAPI page. No need for a generic `c-logo-grid`
component yet. If a second landing page introduces partner logos, extract at that point.

### Logo Grid Layout

```less
.hdx-v2-hapi-partners-grid {
    display:               grid;
    grid-template-columns: repeat(5, 1fr);   // 5 per row: 10 logos = 2 even rows
    gap:                   var(--hdx-space-8);  // 32px
}

.hdx-v2-hapi-partner-logo {
    width:      100%;
    height:     7.5rem;
    object-fit: contain;
}
```

No container div, no background, no border/shadow/padding — raw images as direct grid children.

### Logo Images

- Image path: `h.url_for_static('images/landing_pages/partners/{slug}.png')`
- Alt text: logo label from `PARTNERS_CONSTANTS`

### Template snippet (inline)

```jinja2
<div class="hdx-v2-hapi-partners-grid">
  {% for slug, label in partners %}
    <img class="hdx-v2-hapi-partner-logo"
         src="{{ h.url_for_static('images/landing_pages/partners/' ~ slug ~ '.png') }}"
         alt="{{ label }}" loading="lazy">
  {% endfor %}
</div>
```

---

## 6. Sidebar Strategy

**Decision: reuse `c-anchor-links`; make wrapper always render for consistent sticky.**

The component has two modes:
- `.c-anchor-links-wrapper` — desktop sticky vertical list (visible at XL); now always rendered regardless of whether a `heading` is passed. `position: sticky; top: var(--hdx-space-12)`.
- `.c-anchor-links-mobile` — mobile dropdown with toggle button (visible at MD/SM)

`nav_items` is defined at the template's top-level scope (accessible from both `{% block secondary %}` and `{% block primary %}`):

```jinja2
{% set nav_items = [
    {'label': _('Data Availability'), 'href': '#data-availability', 'active': True},
    {'label': _('Be Inspired'),       'href': '#be-inspired',       'active': False},
    {'label': _('FAQ'),               'href': '#faq',               'active': False},
    {'label': _('Partners'),          'href': '#partners',          'active': False},
    {'label': _('Documentation'),     'href': 'https://hdx-hapi.readthedocs.io/', 'active': False, 'external': True},
] %}
{# Secondary block: #}
{% snippet 'v2/components/anchor-links.html', items=nav_items %}
{# Primary block (mobile): #}
{% snippet 'v2/components/anchor-links.html', items=nav_items, mobile_only=True %}
```

No `heading` is passed — the Figma shows no sidebar heading on the HAPI page.

### Sidebar LESS

```less
.hdx-v2-hapi-sidebar {
    display: none;

    @media (min-width: @hdx-bp-xl) {
        display: block;
        .v2-sidebar-flex();   // flex: 0 0 25%; min-width: 0
        padding: var(--hdx-space-10) 0;
    }
}
```

Sticky is handled by `.c-anchor-links-wrapper` inside the sidebar (not container-level).
The `.v2-sidebar-sticky()` mixin in `mixins.less` is available for non-anchor-links sidebars
(e.g. Search filters, Locations letter grid).

### "Documentation" External Link

The `Documentation` entry opens in a new tab (`target="_blank" rel="noopener"`) with a
visual external-link icon. The `anchor-links.html` snippet requires an `external` flag
added to its API: when `external: True`, the rendered `<a>` gets `target="_blank"
rel="noopener"` and an icon appended. The `external: True` is already in the `nav_items`
definition above — the snippet implementation must honour it.

---

## 7. Responsive Strategy

### Page Header / Hero

| Breakpoint | Layout |
|---|---|
| XL | Flex row: description block (flex: 1) left, logo white-box (~17.375rem) right |
| MD | Same flex row, narrower container |
| SM | Stacked: description above, logo box full-width below |

### Sidebar

| Breakpoint | Behaviour |
|---|---|
| XL | Visible, sticky left, 25% flex width |
| MD | Hidden; `c-anchor-links-mobile` dropdown available in content |
| SM | Hidden; `c-anchor-links-mobile` dropdown available in content |

### Content Sections

All sections (`#data-availability`, `#data-coverage`, `#be-inspired`, `#faq`,
`#partners`) occupy `flex: 1` in the content column. Each is full-width within that
column at all breakpoints.

### Be Inspired Cards

Wrapped in the shared `c-content-card-grid` component class (2 per row at all
breakpoints, `gap: var(--hdx-space-4)`) — no page-specific grid LESS.

4 cards → 2×2 grid at every breakpoint.

### Partner Logos

See Section 5 — CSS Grid `repeat(5, 1fr)` at all breakpoints.
10 logos → 2 even rows of 5. Fixed height `7.5rem`, `object-fit: contain`.

---

## 8. Template Structure

### Base Template Migration

The page must extend `v2/page.html` instead of `page_light.html`.

### Page-Level Variables

```jinja2
{% extends "v2/page.html" %}

{% set outer_row_class      = 'hdx-v2-hapi-row' %}
{% set columns_class        = '' %}
{% set sidebar_class        = 'hdx-v2-hapi-sidebar' %}
{% set content_class        = 'hdx-v2-hapi-content' %}
{% set breadcrumb_row_class = '' %}

{% set CONST = h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['HAPI_LANDING_PAGE'] %}
```

### Block Overrides

```
{% block subtitle %}       → 'HDX HAPI'
{% block breadcrumb_content %} → Home / Products / HDX HAPI
{% block styles %}         → v2-page-styles + v2-hapi-landing-page-styles
{% block scripts %}        → super() [+ v2-hapi-scripts if accordion needs JS]
{% block pre_primary %}    → page header / hero section (full-bleed or scoped)
{% block secondary %}      → c-anchor-links sidebar
{% block primary %}        → all 6 content sections
```

### Asset Bundles

| Bundle | Contents |
|---|---|
| `v2-hapi-landing-page-styles` | `hapi-landing-page.less` (imports accordion.less, divider.less) |
| `v2-hapi-landing-page-scripts` | Only if accordion JS enhancement is needed |

### Data Passed to Template

| Variable | Source | Change vs v1 |
|---|---|---|
| `CONST` | `UI_CONSTANTS` | Unchanged |
| `faq_data` | View | Unchanged |
| `partners` | View (`PARTNERS_CONSTANTS`) | Unchanged |
| `sections` | View (`SECTIONS_CONSTANTS`) | **Update**: add Partners entry (v2 has 5 nav items vs 4 in v1) |

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| `<details>` smooth animation not cross-browser | Implement CSS-only first; add JS `max-height` animation via small script if review requires smooth transition |
| Custom hero section sets no reusable pattern | Document the pattern in the requirements; if a second landing page is needed, propose a `c-landing-hero` component at that point |
| Partner logo grid at SM: 10 logos = 2×4 + 2 orphans | The last 2 logos will stretch (`flex: 1`) and may look visually unbalanced. Verify against Figma; if unacceptable, use `max-width` cap on logo items or `justify-content: center` on the row |
| `SECTIONS_CONSTANTS` outdated | v1 has 4 jump nav items; v2 has 5. Must update constants to add Partners and ensure view passes updated `sections` |
| `c-anchor-links` needs `external` flag | The snippet does not currently support `target="_blank"` or an external icon. This must be added before the Documentation link works correctly |
| First landing page pattern — sets precedent | Document decisions clearly; keep components minimal so they can be evolved without breaking this page |

---

## 10. Decisions Taken

**D1 — Be Inspired cards**
Keep the 4 existing v1 cards only. The extra XL-only cards in Figma are not real content.
Card count is the same at all breakpoints — no new entries in `hapi.py` constants.

**D2 — Accordion default state**
The **first item is open by default** on every page load. No URL hash persistence.
Implemented via `<details open>` on the first entry in `faq_data` — CSS-only, no JS needed.

**D3 — Analytics**
Carry over v1 GA events. Add `data-ga-event` / `data-ga-label` attributes to
`.c-accordion__trigger` for accordion toggles, and to sidebar link `<a>` elements for
sidebar navigation clicks.

**D4 — "Documentation" sidebar link**
Opens in a new tab (`target="_blank" rel="noopener"`) with a visual external-link icon.
The `c-anchor-links` snippet must be extended with an `external` flag that triggers this
behaviour. See Section 6 for the updated snippet API.

**D5 / D6 — Data Coverage section**
**Out of scope.** The Data Coverage section is not rendered in v2. `DATA_COVERAGE_CONSTANTS`
is not passed to the template; the `#data-coverage` anchor and its `c-divider` are omitted;
no view changes needed for this section.

**D7 — SM "You might also like" section**
**Out of scope.** Not rendered.

**D8 — Hero section**
Replaced bespoke hero HTML with `c-page-header` component. `title='HDX HAPI'` (short),
`subtitle=CONST.HERO_SECTION_TITLE` (full title rendered as semibold paragraph below the h1),
`description=CONST.HERO_SECTION_DESCRIPTION` (HTML link). `c-page-header` gained a new
`subtitle` param and a conditional `_has_dataset_meta` flag that suppresses the divider
and metadata strip when no dataset fields are passed (as on this landing page).

**D9 — Be Inspired card component**
New `c-content-card` component created (`content-card.html` + `content-card.less`).
Params: `title`, `description`, `link_label`, `link_href`, `link_new_tab`, `link_attrs`.
The link is rendered via `c-text-link` snippet (style `tertiary`, size `s`). No bespoke
`__link` LESS rule — the snippet handles its own styling.

`link_attrs` (dict, forwarded to `c-text-link`'s `attrs`) was added after launch to fix a
regression: v1's Be Inspired cards carried `data-module="hdx_click_stopper"` +
`data-module-link_type="hapi tools"` + `data-module-link_label=<card title>` (see commit
`8032c54a4c`, "add analytics"), which the v2 migration dropped because `content-card.html`
had no way to pass attrs through to its link. Restored via `link_attrs` on all 4 Be Inspired
card calls in `hapi.html`, matching the same fix applied to Signals' Resources cards.

**D10 — Partner logos with no container**
Partner logos are direct `<img>` grid children — no wrapper `<div>`. CSS Grid on
`.hdx-v2-hapi-partners-grid` + `width: 100%; height: 7.5rem; object-fit: contain` on
`.hdx-v2-hapi-partner-logo`. No background, border, shadow, or padding.

**D11 — Sticky sidebar via wrapper always rendering**
Root issue: `.c-anchor-links-wrapper` (the sticky element) was only rendered when `heading`
or `with_mobile_dropdown` was passed. HAPI passes neither. Fixed by removing the condition
so the wrapper always renders; the heading text inside remains conditional. This makes every
anchor-links desktop nav self-sticky, consistent with the dataset page. The separate
`.v2-sidebar-sticky()` mixin in `mixins.less` is for non-anchor-links sidebars only
(Search, Locations).

---

## Files Affected

| File | Change |
|---|---|
| `ckanext-hdx_theme/…/templates/landing_pages/hapi.html` | Replace v1 with v2; extend `v2/page.html`; render all sections; `nav_items` at top-level scope |
| `ckanext-hdx_theme/…/templates/v2/components/accordion.html` | **New** — `c-accordion` component snippet |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/components/accordion.less` | **New** — accordion LESS |
| `ckanext-hdx_theme/…/templates/v2/components/content-card.html` | **New** — `c-content-card` component snippet (title + desc + `c-text-link`) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/components/content-card.less` | **New** — content-card LESS (no `__link` block — link via `c-text-link` snippet) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/pages/hapi-landing.less` | **New** — page LESS; cards `repeat(2, 1fr)`; partners CSS Grid `repeat(5, 1fr)`; bg `var(--hdx-neutral-01)` |
| `ckanext-hdx_theme/…/fanstatic/webassets.yml` | Add `v2-hapi-landing-page-styles` bundle |
| `ckanext-hdx_theme/…/helpers/ui_constants/landing_pages/hapi.py` | Added `HERO_SHORT_TITLE`; `FAQ_SECTION_TITLE` = `'FAQ'`; `HERO_SECTION_TITLE` used as subtitle |
| `ckanext-hdx_theme/…/templates/v2/components/anchor-links.html` | Add `external` flag; wrapper always renders (sticky unconditional) |
| `ckanext-hdx_theme/…/templates/v2/components/page-header.html` | Add `subtitle` param + `_has_dataset_meta` flag for conditional divider/metadata strip |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/components/page-header.less` | Add `__subtitle` block (`.hdx-body-m-semibold()`, `var(--hdx-neutral-85)`) |
| `ckanext-hdx_theme/…/fanstatic/v2/components/anchor-links.js` | `initActiveTracking()` derives watched sections from nav item hrefs (generic, not page-specific) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/mixins.less` | Add `.v2-sidebar-sticky()` mixin (`position: sticky; top: var(--hdx-space-12); align-self: flex-start`) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/pages/search.less` | Apply `.v2-sidebar-sticky()` at XL; normalise to mobile-first (`display: none` base) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/pages/locations-list.less` | Replace inline `position: sticky; top: 0` with `.v2-sidebar-sticky()` (also fixes wrong `top: 0`) |
| `ckanext-hdx_theme/…/hdx-styles/src/common/less/v2/pages/dataset.less` | Minor cleanup: `.v2-sidebar-flex()` moved inside XL media query |
