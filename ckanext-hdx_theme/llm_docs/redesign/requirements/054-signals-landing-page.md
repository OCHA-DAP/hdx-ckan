# 054 — HDX Signals Landing Page (v2)

**Scope:** Migrate the Signals landing page to v2 — full page layout, all content sections,
sticky sidebar navigation (XL only), new `c-signal-card` component, shared carousel module,
signal cards section, data coverage grid, signals map iframe, resources, FAQ, partners.
**Excluded:** backend/data changes, signup form restyling (preserve as-is, font: Roboto only),
analytics changes (preserve all data attrs).
**Figma sources:** `signals-xl.html`, `signals-md.html`, `signals-sm.html`, `signal-card.html`

---

## Context

The Signals landing page (`/signals/`) currently extends `page_light.html` and uses the v1 BEM
block component system (Bootstrap-based). The v2 migration follows the same pattern as the
HAPI landing page (task 053), extending `v2/page.html` and using the shared v2 component set.

Key differences from HAPI v2:
- **New `c-signal-card` component** — distinct card type with chart placeholder, type tag, and
  two action buttons.
- **Featured signal cards section** — 3 static dummy cards at XL (flex row), carousel at MD/SM.
- **Shared carousel module** — `highlights-carousel.js` is refactored into a generic
  `carousel.js` reused by both the homepage and the signals page.
- **Anchor links XL only** — no `c-anchor-links-mobile` dropdown at MD/SM (also remove from HAPI).
- **CTA button in hero** — signup anchor button below description in `c-page-header`.
- **Signals Map section** — separate content section with iframe embed (`https://data.humdata.org/visualization/signals/`).

The v2 Signals page adds 5 anchor nav items: Sign up · Data Coverage ·
Signals Map · Resources · FAQ. (Partners section has no anchor nav item.)

---

## 1. Existing Page Audit

### Templates & Assets

| Item | Path |
|---|---|
| **Main template** | `ckanext-hdx_theme/ckanext/hdx_theme/templates/landing_pages/signals.html` |
| **Base template** | `page_light.html` — must be migrated to `v2/page.html` |
| **Constants** | `ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/landing_pages/signals.py` |
| **View** | `ckanext-hdx_theme/ckanext/hdx_theme/views/landing_pages.py` → `signals()` function |

**Current asset bundles:** `page-extra-light-styles`, `bem-blocks-styles`,
`hdx-signals-scripts`, `bem-blocks-scripts`

### Current Sections (v1, in order)

| Section | Anchor | Component |
|---|---|---|
| Hero | — | `bem.blocks/hero.html` — title, description (email link, impact story link), logo, jump nav |
| Signup | `#signup` | Mailchimp form embed — full form with checkboxes, datasets, locations |
| Data Coverage | `#data-coverage` | `bem.blocks/heading.html` + 6× `bem.blocks/card.html` in 2-col Bootstrap grid |
| Resources | `#resources` | `bem.blocks/heading.html` + 4× `bem.blocks/card.html` (Map, Dataset, Methodology, Repository) |
| FAQ | `#faq` | `bem.blocks/heading.html` + `bem.blocks/faq.html` (Bootstrap collapse) |
| Partners | — | `bem.blocks/heading.html` + `bem.blocks/partners.html` (6 logos) |

**Note:** No featured signal cards section or dedicated Signals Map section in v1.
In v1, "Signals Map" is one of the 4 Resources cards linking to an external URL.

### Template Variables (passed from view)

| Variable | Source | Notes |
|---|---|---|
| `CONST` | `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE']` | Hero text, section titles, resource card titles/links |
| `faq_data` | View (WordPress) | List of `{question, answer}` dicts |
| `partners` | `SIGNALS_PARTNERS_CONSTANTS` | 6 `(slug, label)` tuples |
| `sections` | `SIGNALS_SECTIONS_CONSTANTS` | 5 jump-nav items (currently external URL for Signals Map) |
| `data_coverage` | `SIGNALS_DATA_COVERAGE_CONSTANTS` | 6 dataset dicts `{title, organization, link}` |

### Existing SIGNALS_SECTIONS_CONSTANTS (v1 — needs update)

```python
SECTIONS_CONSTANTS = [
    {'name': 'Signup',        'url': '#signup'},
    {'name': 'Data Coverage', 'url': '#data-coverage'},
    {'name': 'Signals map',   'url': 'https://data.humdata.org/visualization/signals/'},  # external → change
    {'name': 'Resources',     'url': '#resources'},
    {'name': 'FAQ',           'url': '#faq'},
]
```

**Must update** to add Partners and change Signals Map to an internal anchor:
```python
SECTIONS_CONSTANTS = [
    {'name': 'Sign up',       'url': '#signup'},
    {'name': 'Data Coverage', 'url': '#data-coverage'},
    {'name': 'Signals Map',   'url': '#signals-map'},
    {'name': 'Resources',     'url': '#resources'},
    {'name': 'FAQ',           'url': '#faq'},
    {'name': 'Partners',      'url': '#partners'},
]
```

### Analytics Attributes to Preserve

| Element | Attribute | Value |
|---|---|---|
| Hero jump nav links | `data-module="hdx_click_stopper"` + `data-module-link_type` | `"signals jump nav"` |
| Signup subscribe button | `data-module="hdx_click_stopper"` + `data-module-link_type` + `data-module-just_send_event` + `data-module-label` | `"signals sign up"`, `"true"`, `"Subscribe"` |
| Resources card links | `data-module="hdx_click_stopper"` + `data-module-link_type` + `data-module-link_label` | `"signals resources"`, card title |
| Data coverage card links | `data-module="hdx_click_stopper"` + `data-module-link_type` + `data-module-link_label` | `"signals data coverage"`, card title |

### Existing BEM Components (v1 only — not reused)

| Component | v2 Replacement |
|---|---|
| `bem.blocks/hero.html` | `c-page-header` (extended with CTA button param) |
| `bem.blocks/faq.html` | `c-accordion` |
| `bem.blocks/partners.html` | Inline logo grid (signals-specific CSS) |
| `bem.blocks/card.html` | `c-content-card` (resources section) or inline data coverage items |
| `bem.blocks/heading.html` | Direct LESS token (`.hdx-v2-signals-section-heading`) |

---

## 2. Figma Mapping

### Page Sections (all breakpoints, in order)

| # | Section | Anchor | Status vs v1 |
|---|---|---|---|
| 1 | Page Header / Hero | — | Redesigned; `c-page-header` + CTA button param |
| 2 | Featured Signal Cards | — | **New in v2** — 3 static dummy cards |
| 3 | Signup Form | `#signup` | Preserved (Mailchimp form, font: Roboto only) |
| 4 | Data Coverage | `#data-coverage` | Redesigned (static grid, same 6 items) |
| 5 | Signals Map | `#signals-map` | **New in v2** — iframe embed (`https://data.humdata.org/visualization/signals/`) |
| 6 | Resources | `#resources` | Redesigned (4× `c-content-card`, same 4 cards) |
| 7 | FAQ | `#faq` | Redesigned (`c-accordion`, same FAQ data) |
| 8 | Partners | `#partners` | Redesigned (inline logo grid, same 6 logos) |

### XL Layout (`signals-xl.html`)

```
[navbar / breadcrumb]                  ← standard v2 chrome
[page-header / hero]
  Left (flex: 1):
    h1 "HDX Signals" (Merriweather 32px)
    description (regular): CONST.HERO_SECTION_DESCRIPTION (email + story links)
    CTA button: "Sign up" → href="#signup"
  Right (logo card):
    Signals logo image
[body]                                 ← two-column at XL, single-column at MD/SM
  [sidebar] (25%, left, sticky)
    c-anchor-links (6 items):
      • Sign up         → #signup
      • Data Coverage   → #data-coverage
      • Signals Map     → #signals-map
      • Resources       → #resources
      • FAQ             → #faq
      • Partners        → #partners
  [content] (flex: 1)
    [featured-signal-cards]
      (no section heading — match Figma)
      flex row of 3 c-signal-card (size: lg, static dummy data)
    [c-divider]
    [signup]
      section heading (CONST.SIGNUP_SECTION_TITLE)
      Mailchimp form (preserved as-is from v1, font: Roboto)
    [c-divider]
    [data-coverage]
      section heading "Data Coverage"
      CSS Grid 3-col (6 static items from DATA_COVERAGE_CONSTANTS)
        Each item: title + organization description + "Learn more" link (no chevron icon)
    [c-divider]
    [signals-map]
      section heading "Signals Map"
      iframe src="https://data.humdata.org/visualization/signals/" loading="lazy"
    [c-divider]
    [resources]
      section heading "Resources"
      CSS Grid 2-col (4× c-content-card) — Map, Dataset, Methodology, Repository
    [c-divider]
    [faq]
      section heading (CONST.FAQ_SECTION_TITLE)
      c-accordion (faq_data, first item open)
    [c-divider]
    [partners]
      section heading (CONST.PARTNERS_SECTION_TITLE)
      logo grid (3 per row, 6 logos = 2 rows of 3)
[footer]
```

### MD Layout (`signals-md.html`)

- Sidebar: **hidden** — no mobile dropdown (XL only per decision)
- Page header: same flex structure, narrower container (`49.5rem`)
- Featured signal cards: carousel (1 card visible, swipe/arrows)
- All other sections: full-width single-column
- Logo grid: 3 per row (same as XL — 6 logos fit in 2 rows)

### SM Layout (`signals-sm.html`)

- Sidebar: **hidden** — no mobile dropdown
- Page header: stacked (text block above, logo box full-width below; CTA button below description)
- Featured signal cards: carousel (1 card visible at a time, `c-signal-card` size `sm`)
- Data coverage: 2-col grid (same as MD)
- Logo grid: 3 per row (same)

### Breakpoint Summary

| Feature | XL (≥ 80rem) | MD (48–80rem) | SM (< 48rem) |
|---|---|---|---|
| Sidebar | Visible, left, 25% | Hidden | Hidden |
| Mobile nav dropdown | Hidden | **None** | **None** |
| Page header | Horizontal (text + button left, logo right) | Same, narrower | Stacked |
| Featured signal cards | 3-col flex row | Carousel | Carousel (`sm` card size) |
| Data coverage grid | 3-col | 3-col | 2-col |
| Resources grid | 2-col | 2-col | 2-col |
| Partner logos | 3-col (6 logos, 2 rows) | 3-col | 3-col |
| Container padding | 3rem sides | 3rem sides | 1rem sides |

### Colors (from Figma / Figma tokens → v2 tokens)

| Figma value | v2 token | Usage |
|---|---|---|
| `#fafbfb` | `var(--hdx-neutral-01)` | Hero background |
| `#f5f7f7` | `var(--hdx-neutral-1)` | Signal card background |
| `#ebeff0` | `var(--hdx-neutral-2)` | Card borders, section borders |
| `#d8e0e1` | `var(--hdx-neutral-3)` | Divider line |
| `#d4eae4` | `var(--hdx-brand-1)` | Label cyan background |
| `#101212` | `var(--hdx-neutral-95)` | Body text |
| `#2f3536` | `var(--hdx-neutral-85)` | Muted text |
| `#9db1b3` | `var(--hdx-neutral-50)` | Chart label muted |
| `#3f4748` | `var(--hdx-neutral-60)` | Hover border |
| `#1862d8` | `var(--hdx-primary-5)` | Active sidebar item, buttons, links |

---

## 3. Component Strategy

| UI Element | Decision | Justification |
|---|---|---|
| Page header / hero | **Extend** `c-page-header` | Add optional `cta_label`/`cta_href` params for the "Sign up" anchor button; same approach as HAPI's `subtitle` extension |
| Sidebar nav | **Reuse** `c-anchor-links` | XL only; same sticky pattern as HAPI; 6 items |
| Mobile nav | **None** | Per confirmed decision — no `c-anchor-links-mobile` on MD/SM |
| Featured signal cards | **New** `c-signal-card` | Unique structure (chart placeholder, type tag, 2 actions); see Section 4 |
| Signal cards carousel | **Refactor** `highlights-carousel.js` | Extract shared `carousel.js` module; see Section 5 |
| Signup form | **Preserve** inline | Full Mailchimp form kept as-is; only add Roboto font override |
| Data coverage | **Inline grid** | 6 static items; custom CSS grid in page LESS; reuse `c-text-link` for "Learn more"; no chevron icon |
| Signals map | **iframe** | `<iframe src="https://data.humdata.org/visualization/signals/" loading="lazy">` — same pattern as HAPI's data-availability iframe |
| Resources cards | **Reuse** `c-content-card` | 4 cards match HAPI's "Be Inspired" pattern exactly |
| FAQ | **Reuse** `c-accordion` | Same CSS-only pattern as HAPI; first item open |
| Partner logos | **Inline grid** | 6 static logos; signals-specific CSS (same pattern as HAPI partner grid) |
| Section dividers | **Reuse** `c-divider` | Between every major section |
| Section headings | Direct token | `.hdx-v2-signals-section-heading` class; `.hdx-display-xs()` + spacing |

### HAPI Side-Effect Change

The `c-anchor-links-mobile` dropdown must also be **removed from the HAPI landing page**
(`templates/landing_pages/hapi.html` + `less/v2/hapi-landing-page.less`) to apply the same
XL-only decision consistently. This is a breaking change to an already-shipped template —
verify no regression before merging.

---

## 4. c-signal-card Specification (NEW COMPONENT)

### Files

| File | Path |
|---|---|
| Template | `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/signal-card.html` |
| LESS | `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/signal-card.less` |
| Demo | Add section to `templates/v2/components.html` |

### BEM Structure

```html
<div class="c-signal-card">

  <!-- Header: location label → date+type row → title -->
  <div class="c-signal-card__header">
    {% snippet 'v2/components/label.html', text=location, color='cyan', size='s' %}
    <div class="c-signal-card__meta">
      <span class="c-signal-card__date">{{ date }}</span>
      {% snippet 'v2/components/label.html', text=type, color='light', size='s' %}
    </div>
    <p class="c-signal-card__title">{{ title }}</p>
  </div>

  <!-- Graph: description + chart image (or placeholder) -->
  <div class="c-signal-card__graph">
    {% if description %}<p class="c-signal-card__description">{{ description }}</p>{% endif %}
    {% if image_src %}
      <img class="c-signal-card__image" src="{{ image_src }}" alt="{{ image_alt }}" loading="lazy">
    {% else %}
      <div class="c-signal-card__image c-signal-card__image--placeholder"></div>
    {% endif %}
  </div>

  <!-- Footer: tertiary size-s buttons (not text-links) -->
  <div class="c-signal-card__footer">
    {% snippet 'v2/components/button.html',
        tag='a', href=source_href,
        style='tertiary', type='text', size='s', state='enabled',
        label=source_label %}
    {% snippet 'v2/components/button.html',
        tag='a', href=cta_href,
        style='tertiary', type='text', size='s', state='enabled',
        label=cta_label %}
  </div>

</div>
```

### Snippet Parameters

| Param | Type | Default | Notes |
|---|---|---|---|
| `location` | string | `''` | Location name shown as cyan label |
| `date` | string | `''` | Pre-formatted date string |
| `type` | string | `''` | Signal type shown as light label |
| `title` | string | `''` | Card title; 2-line clamp in CSS |
| `description` | string | `''` | Short chart description |
| `image_src` | string | `''` | Chart image URL; omit for placeholder |
| `image_alt` | string | `''` | Alt text for chart image |
| `source_label` | string | `''` | Footer left button label |
| `source_href` | string | `'#'` | Footer left button href |
| `cta_label` | string | `''` | Footer right button label |
| `cta_href` | string | `'#'` | Footer right button href |

### Variants

| Variant | Class modifier | Title font |
|---|---|---|
| default | (none) | `.hdx-body-l-semibold()` |
| small | `.c-signal-card--sm` | `.hdx-body-m-medium()` |

### States

| State | Selector | Visual |
|---|---|---|
| Default | `.c-signal-card` | `border: 1px solid var(--hdx-neutral-1)`, no box-shadow |
| Hover | `.c-signal-card:hover` | `border-color: var(--hdx-neutral-8)` — color-only transition, no width change |

### LESS Structure

```less
.c-signal-card {
    display:          flex;
    flex-direction:   column;
    gap:              var(--hdx-space-6);
    padding:          var(--hdx-space-6);
    border:           1px solid var(--hdx-neutral-1);
    border-radius:    var(--hdx-radius-sm);
    background-color: var(--hdx-neutral-0);
    transition:       border-color 150ms;

    &:hover { border-color: var(--hdx-neutral-8); }  // color-only, no width/shadow change

    &__header {
        display:        flex;
        flex-direction: column;
        align-items:    flex-start;  // keeps location label at intrinsic width
        gap:            var(--hdx-space-3);
    }

    &__meta {
        display:         flex;
        justify-content: space-between;
        align-items:     center;
        gap:             var(--hdx-space-2);
        width:           100%;  // required: parent has align-items:flex-start
    }

    &__date {
        color:       var(--hdx-neutral-50);
        flex-shrink: 0;
    }

    &__title {
        .hdx-body-l-semibold();
        color:              var(--hdx-neutral-95);
        margin:             0;
        display:            -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow:           hidden;
    }

    &__graph {
        display:        flex;
        flex-direction: column;
        gap:            var(--hdx-space-6);
        flex:           1;  // pushes footer to bottom
    }

    &__description {
        .hdx-body-s();
        color:  var(--hdx-neutral-60);
        margin: 0;
    }

    &__image {
        width:            100%;
        aspect-ratio:     3 / 1;  // proportional placeholder frame
        object-fit:       contain;
        background-color: var(--hdx-neutral-2);
        display:          block;
    }

    &__footer {
        display:  flex;
        gap:      var(--hdx-space-14);
        flex-wrap: wrap;
    }

    &--sm {
        .c-signal-card__title { .hdx-body-m-medium(); }
    }
}
```

### Dummy Data (Static, for v2 launch)

Add 3 dummy card constants to `signals.py`:

```python
SIGNAL_CARDS_CONSTANTS = [
    {
        'location': 'Ukraine',
        'date': 'Dec 30, 2025',
        'type': 'Armed conflict',
        'title': 'Lorem ipsum dolor sit amet consectetur',
        'description': '8.7K fatalities since Nov 30, 2025',
        'image_src': 'https://picsum.photos/seed/signals1/320/130',   # external placeholder
        'source_label': 'Source',
        'source_href': '#',
        'cta_label': 'See this signal',
        'cta_href': '#',
    },
    # ... 2 more dummy cards
]
```

Pass as `signal_cards` from the `signals()` view function.

### Demo Page

Add a demo section to `templates/v2/components.html`:

```jinja2
<section class="demo-section" id="signal-card">
  <h1 class="demo-section__title">Signal Card</h1>
  <p class="demo-section__subtitle">size: lg / sm</p>
  <div class="demo-row">
    {% snippet 'v2/components/signal-card.html', location='Ukraine', date='Dec 30, 2025',
        type='Armed conflict', title='Lorem ipsum dolor sit amet consectetur adipiscing elit',
        description='8.7K fatalities since Nov 30, 2025', size='lg' %}
    {% snippet 'v2/components/signal-card.html', location='Somalia', date='Jan 15, 2026',
        type='Food insecurity', title='Acute food insecurity rising in southern regions',
        description='3.2M people in Crisis or worse', size='sm' %}
  </div>
</section>
```

### Accessibility Notes

- Location icon in label: `aria-hidden="true"` on the icon `<img>` — the text "Ukraine" already conveys the meaning
- Card is not a link itself (unlike `c-highlight-card`) — individual text-link actions are the interactive targets
- `c-text-link` buttons have sufficient click targets per v2 button size `s`

---

## 5. Carousel Strategy

### Rationale

The homepage `highlights-carousel.js` hardcodes selectors (`.mobile-carousel`, `.highlight-slide`,
`.hdx-v2-highlights__arrow--prev/next`). Reusing it for signals cards requires hardcoding a
second set of selectors, creating fragile coupling. The agreed approach: extract a generic
`carousel.js` module that accepts configurable selectors, then update the homepage to call
it and add a signals-specific call.

### New File: `fanstatic/v2/carousel.js`

Generic carousel factory accepting a config object:

```javascript
function initCarousel(config) {
    // config: {
    //   containerSelector:  string,  // wrapping element
    //   slideSelector:      string,  // individual slide items
    //   prevBtnSelector:    string,  // previous arrow button
    //   nextBtnSelector:    string,  // next arrow button
    //   mediaQuery:         string,  // e.g. '(min-width: 80rem)' — above this = no carousel
    // }
}
window.hdxCarousel = { init: initCarousel };
```

### Homepage Migration

`highlights-carousel.js` becomes a thin wrapper:

```javascript
document.addEventListener('DOMContentLoaded', function () {
    window.hdxCarousel.init({
        containerSelector: '.mobile-carousel',
        slideSelector:     '.highlight-slide',
        prevBtnSelector:   '.hdx-v2-highlights__arrow--prev',
        nextBtnSelector:   '.hdx-v2-highlights__arrow--next',
        mediaQuery:        '(min-width: 80rem)',
    });
});
```

### Signals Carousel Init

In `fanstatic/v2/signals-landing-page.js`:

```javascript
document.addEventListener('DOMContentLoaded', function () {
    window.hdxCarousel.init({
        containerSelector: '.hdx-v2-signals-cards',
        slideSelector:     '.hdx-v2-signal-slide',
        dotsSelector:      '.hdx-v2-signals-dots',   // dots only — no arrows
        mediaQuery:        '(min-width: 80rem)',
    });
});
```

### Carousel Behavior

- **XL (≥ 80rem):** static flex row — 3 cards visible, no carousel JS active
- **MD/SM (< 80rem):** carousel — Hammer.js `swipeleft`/`swiperight`, dot indicators, infinite loop
- Dots auto-populated by `carousel.js` into `.hdx-v2-signals-dots` container
- Each slide wraps the `c-signal-card` in a `.hdx-v2-signal-slide` div (carousel needs a wrapping element distinct from the card component class)
- `__inner` requires `position: relative` for JS `left` animation
- JS adds `.is-carousel-clone` to cloned slides; hide at XL with `.hdx-v2-signal-slide.is-carousel-clone { display: none; }`

### LESS: Carousel Container

```less
.hdx-v2-signals-cards {
    position: relative;
    @media (max-width: @hdx-bp-xl) { overflow: hidden; }

    &__inner {
        position: relative;  // required for JS `left` animation
        display:  flex;
        @media (min-width: @hdx-bp-xl) { gap: var(--hdx-space-5); }
    }
}

.hdx-v2-signal-slide {
    flex-shrink: 0;
    @media (min-width: @hdx-bp-xl) {
        flex: 1; min-width: 0;
        &.is-carousel-clone { display: none; }
    }
    @media (max-width: @hdx-bp-xl) {
        width: 19.938rem; margin-right: var(--hdx-space-4);
    }
    // MD: percentage width (~1.8 cards visible) so dot navigation pages one
    // card at a time — a fixed width left 2.5–3 cards on screen, so clicking
    // a dot skipped a card. Same approach as the homepage highlights slides.
    @media (min-width: @hdx-bp-md) and (max-width: @hdx-bp-xl) {
        width: calc(56% - var(--hdx-space-4));
    }
}

.hdx-v2-signals-carousel-footer {
    display: flex; justify-content: center; margin-top: var(--hdx-space-4);
    @media (min-width: @hdx-bp-xl) { display: none; }
}

.hdx-v2-signals-dots {
    display: flex; justify-content: center; align-items: center; gap: var(--hdx-space-1);
    button {
        width: var(--hdx-space-8); height: var(--hdx-space-2);
        border-radius: var(--hdx-radius-sm); border: none; cursor: pointer; padding: 0;
        background-color: var(--hdx-neutral-1);
        &.active { background-color: var(--hdx-primary-5); }
    }
}
```

### Asset Bundle

`carousel.js` is loaded via the `v2-carousel-scripts` preload bundle. Signals adds
`hdx_signals.js` (vanilla JS form logic) alongside the carousel init:

```yaml
v2-signals-landing-page-scripts:
  output: ckanext-hdx_theme/%(version)s_v2-signals-landing-page-scripts.js
  <<: *common-js
  extra:
    preload:
      - hdx_theme/v2-carousel-scripts
  contents:
    - v2/signals-landing-page.js
    - landing_pages/hdx_signals.js
```

---

## 6. Sidebar Strategy (XL Only)

### Decision

Anchor links are visible **only at XL**. No `c-anchor-links-mobile` dropdown at MD or SM.
This is a deliberate departure from HAPI v2 (which currently has a mobile dropdown) —
apply the same change to HAPI when implementing this task.

### nav_items (5 items — Partners has no anchor nav item)

```jinja2
{% set nav_items = [
    {'label': _('Sign up'),       'href': '#signup',       'active': True},
    {'label': _('Data Coverage'), 'href': '#data-coverage','active': False},
    {'label': _('Signals Map'),   'href': '#signals-map',  'active': False},
    {'label': _('Resources'),     'href': '#resources',    'active': False},
    {'label': _('FAQ'),           'href': '#faq',          'active': False},
] %}
```

### Sidebar LESS

```less
.hdx-v2-signals-sidebar {
    display: none;

    @media (min-width: @hdx-bp-xl) {
        display: block;
        .v2-sidebar-flex();   // flex: 0 0 25%; min-width: 0
        padding: var(--hdx-space-10) 0;
    }
}
```

### HAPI Regression Fix (same PR)

From `templates/landing_pages/hapi.html` — remove the `{% block primary %}` mobile anchor
dropdown call:

```jinja2
{# Remove this from the HAPI primary block: #}
{% snippet 'v2/components/anchor-links.html', items=nav_items, mobile_only=True %}
```

From `less/v2/hapi-landing-page.less` — remove any `.c-anchor-links-mobile` responsive rules.

---

## 7. c-page-header Extension (CTA Button)

The Signals hero includes a "Sign up" CTA button below the description text. This sits
inside the left column of the page header. Extend `c-page-header` with optional params:

| New Param | Type | Default | Usage |
|---|---|---|---|
| `cta_label` | string | `""` | CTA button text |
| `cta_href` | string | `""` | CTA button href (anchor) |
| `cta_icon_src` | string | `""` | Optional icon SVG path (e.g. `'v2/icons/bell.svg'`) |

In `page-header.html`, inside the left column, after `description`:
```jinja2
{% if cta_href %}
  {% set cta_has_icon = cta_icon_src != '' %}
  {% snippet 'v2/components/button.html',
      tag='a', href=cta_href,
      style='primary', type='text', size='m',
      state='enabled',
      icon=cta_has_icon,
      icon_src=cta_icon_src if cta_icon_src else 'v2/icons/placeholder.svg',
      label=cta_label,
      extra_classes='c-page-header__cta-link' %}
{% endif %}
```

LESS: `.c-page-header__cta-link { display: inline-flex; margin-top: var(--hdx-space-1); }`

Signals call:
```jinja2
cta_label=_('Subscribe to notifications'),
cta_icon_src='v2/icons/bell.svg',
cta_href='#signup'
```

---

## 8. Responsive Strategy

### Page Header / Hero

| Breakpoint | Layout |
|---|---|
| XL | Flex row: left block (title + desc + CTA button), logo box right (~17.375rem) |
| MD | Same flex row, narrower container |
| SM | Stacked: text block above full-width, logo box below full-width, CTA button below description |

### Featured Signal Cards

| Breakpoint | Layout |
|---|---|
| XL | Flex row, 3 cards visible (`c-signal-card` size `lg`), no carousel |
| MD | Carousel, 1 card visible at a time (`c-signal-card` size `lg`) |
| SM | Carousel, 1 card visible at a time (`c-signal-card` size `sm`) |

### Data Coverage Grid

```less
.hdx-v2-signals-coverage-grid {
    display:               grid;
    grid-template-columns: repeat(2, 1fr);   // SM: 2 columns
    gap:                   var(--hdx-space-4);

    @media (min-width: @hdx-bp-md) {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### Resources Grid

Wrapped in the shared `c-content-card-grid` component class (2 columns at all
breakpoints, `gap: var(--hdx-space-4)`) — no page-specific grid LESS.

### Signals Map iframe

```less
.hdx-v2-signals-map-iframe {
    width:   100%;
    height:  600px;
    border:  none;
    display: block;
}
```

### Partner Logos

Same `max-width`/`max-height` approach as HAPI:

```less
.hdx-v2-signals-partners-grid {
    display:               grid;
    grid-template-columns: repeat(3, 1fr);
    gap:                   var(--hdx-space-8);
}

.hdx-v2-signals-partner-logo {
    max-width:  10rem;
    max-height: 4rem;
    width:      100%;
    height:     auto;
    object-fit: contain;
    display:    block;
    margin:     0 auto;
}
```

6 logos in a 3×2 grid at all breakpoints.

---

## 9. Template Structure

### Base Template

```jinja2
{% extends "v2/page.html" %}

{% set outer_row_class      = 'hdx-v2-signals-row' %}
{% set columns_class        = '' %}
{% set sidebar_class        = 'hdx-v2-signals-sidebar' %}
{% set content_class        = 'hdx-v2-signals-content' %}
{% set breadcrumb_row_class = '' %}

{% set CONST = h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE'] %}
```

### Block Overrides

```
{% block subtitle %}        → 'HDX Signals'
{% block breadcrumb_content %} → Home / Products / HDX Signals
{% block styles %}          → {{ super() }} + {% asset 'hdx_theme/v2-signals-landing-page-styles' %}
{% block scripts %}         → {{ super() }} + {% asset 'hdx_theme/v2-signals-landing-page-scripts' %}
{% block pre_primary %}     → page header / hero row (full-bleed)
{% block secondary %}       → c-anchor-links sidebar (XL only)
{% block primary %}         → 8 content sections
```

### Signup Form

The Mailchimp form HTML is preserved from v1. The form JS (`fanstatic/landing_pages/hdx_signals.js`)
was fully rewritten in vanilla JS (jQuery removed):
- Targets `.hdx-v2-signals-form-card` only (v1 no longer supported)
- Per-region "Select all" / "Clear all" buttons use `c-button c-button--tertiary c-button--size-s`
- Alert visibility via `alert.style.display` (not Bootstrap `d-none`)
- "Step 2: Locations of interest" top buttons (`#select-all-locations`,
  `#select-all-hrp-locations`, `#clear-all-locations`) use `button.html` snippets; the HRP
  tooltip uses `info-icon.html` (placed adjacent to the HRP button); wrapper changed from
  `<p>` to `<div>` to allow `info-icon.html`'s div output
- Submit button (`#mc-embedded-subscribe`) uses `button.html` snippet with `state='disabled'`,
  `button_type='submit'`; JS toggles `is-disabled` class (not `disabled`)

### Data Coverage Items (inline, not c-accordion)

```jinja2
<div class="hdx-v2-signals-data-coverage">
  {% for item in data_coverage %}
    <div class="hdx-v2-signals-coverage-item">
      <p class="hdx-v2-signals-coverage-item__title">{{ item.title }}</p>
      <p class="hdx-v2-signals-coverage-item__org">{{ item.organization }}</p>
      {% snippet 'v2/components/text-link.html',
          label=_('Learn more'),
          href=item.link,
          style='tertiary',
          size='s',
          target='_blank',
          attrs={'data-module': 'hdx_click_stopper',
                 'data-module-link_type': 'signals data coverage',
                 'data-module-link_label': item.title} %}
    </div>
  {% endfor %}
</div>
```

### Signals Map Section

```jinja2
<div id="signals-map" class="hdx-v2-signals-section">
  <h2 class="hdx-v2-signals-section-heading">{{ _('Signals Map') }}</h2>
  <iframe class="hdx-v2-signals-iframe"
          src="https://data.humdata.org/visualization/signals/"
          title="{{ _('Signals Map') }}"
          loading="lazy"></iframe>
</div>
```

### View Function Changes

In `views/landing_pages.py`, the existing `signals()` function needs one addition:

```python
from ckanext.hdx_theme.helpers.ui_constants.landing_pages.signals import \
    ..., SIGNAL_CARDS_CONSTANTS as SIGNALS_SIGNAL_CARDS_CONSTANTS

def signals():
    ...
    template_data = {
        ...
        'signal_cards': SIGNALS_SIGNAL_CARDS_CONSTANTS,  # Add
    }
```

### Asset Bundles

```yaml
v2-signals-landing-page-styles:
  output: ckanext-hdx_theme/%(version)s_v2-signals-landing-page-styles.css
  <<: *common-css
  contents:
    - v2/signals-landing-page.css
    - v2/components/signal-card.css

v2-signals-landing-page-scripts:
  output: ckanext-hdx_theme/%(version)s_v2-signals-landing-page-scripts.js
  <<: *common-js
  extra:
    preload:
      - hdx_theme/v2-carousel-scripts   # includes carousel.js + Hammer.js
  contents:
    - v2/signals-landing-page.js
    - landing_pages/hdx_signals.js
```

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| **Carousel refactor regresses homepage** ❗ | `highlights-carousel.js` becomes a wrapper around `carousel.js` — test highlights carousel on homepage before merging |
| **HAPI regression from mobile dropdown removal** ❗ | Verify HAPI page at MD/SM after removing `c-anchor-links-mobile` — anchor links simply disappear, which is correct |
| **Signal card type tag reuses `c-label`** | Verify `color='light'` variant of `c-label` matches Figma's neutral gray tag background |
| **Analytics breakage** ❗ | All `data-module="hdx_click_stopper"` attrs preserved from v1; map event names explicitly in Section 1 |
| **Mailchimp form + v2 font injection** | v2 page layout adds `font-family: Roboto` globally — verify this reaches the form inputs without `!important` conflicts from Bootstrap classes |
| **Partner logos: 6 logos, 3 per row** | 6 logos = exactly 2 even rows of 3, no orphan issue (unlike HAPI's 10 logos with 5 per row) |
| **`c-page-header` extension side effects** | Adding `cta_label`/`cta_href` params is conditional — all existing pages pass neither, so no regression |
| **Signal card placeholder image** | Uses external picsum.photos service — fine for dev/staging; replace with real chart thumbnails when available |

---

## 11. Decisions

1. **Signals logo image** — Use `h.url_for_static('images/landing_pages/logo_hdx_signals.png')`.
   File confirmed at `hdx-styles/src/common/images/landing_pages/logo_hdx_signals.png` — same
   pattern as HAPI which is already working.

2. **Signal card placeholder image** — Use an external placeholder image service.
   `image_src` in dummy card constants uses `https://picsum.photos/seed/signalsN/320/130`
   (unique seed per card). No static asset to create.

3. **Featured signal cards section title** — **No section heading.** Match Figma directly;
   the featured cards section starts immediately with the cards (or carousel at MD/SM) without
   a preceding heading element.

4. **Data coverage chevron** — **Removed.** No chevron icon in coverage items — no equivalent
   in v1 with tooltip. Coverage item layout: title + organization text + "Learn more" link only.

5. **Signals Map** — Load an `<iframe>` pointing to
   `https://data.humdata.org/visualization/signals/` with `loading="lazy"`, using class
   `hdx-v2-signals-iframe`. Same pattern as HAPI's `hdx-v2-hapi-iframe`.

6. **Partner logos images** — All 6 PNGs confirmed: `acaps`, `european_comission`, `acled`,
   `ipc`, `idmc`, `wfp` exist in `hdx-styles/src/common/images/landing_pages/partners/`.
   Reference via `h.url_for_static('images/landing_pages/partners/' ~ slug ~ '.png')`.

7. **Resources section description** — Show `RESOURCES_SECTION_DESCRIPTION` above the 4 cards
   and `RESOURCES_SECTION_PARAGRAPH` (closing email-link paragraph) below — same structure as
   v1. Both text blocks are preserved; only the card components are upgraded to `c-content-card`.

8. **CONST access key** — Confirmed. `CONSTANTS` in `signals.py` is registered as
   `SIGNALS_LANDING_PAGE` in `landing_pages/__init__.py`. The accessor
   `h.HDX_CONST('UI_CONSTANTS')['LANDING_PAGES']['SIGNALS_LANDING_PAGE']` resolves correctly.

---

## Files Affected

### New Files

| File | Purpose |
|---|---|
| `templates/v2/components/signal-card.html` | New `c-signal-card` component snippet |
| `less/v2/components/signal-card.less` | Signal card LESS |
| `less/v2/signals-landing-page.less` | Page-specific LESS |
| `fanstatic/v2/signals-landing-page.css` | Compiled output (generated) |
| `fanstatic/v2/carousel.js` | Generic shared carousel module |
| `fanstatic/v2/signals-landing-page.js` | Thin init wrapper for signals carousel |

### Modified Files

| File | Change |
|---|---|
| `templates/landing_pages/signals.html` | Replace v1 with v2; extend `v2/page.html` |
| `helpers/ui_constants/landing_pages/signals.py` | Update `SECTIONS_CONSTANTS` (add Partners, change Signals Map URL); add `SIGNAL_CARDS_CONSTANTS` (3 dummy cards) |
| `views/landing_pages.py` | Pass `signal_cards` from `SIGNAL_CARDS_CONSTANTS` |
| `fanstatic/v2/highlights-carousel.js` | Refactor to thin wrapper calling `carousel.js` |
| `fanstatic/webassets.yml` | Add `v2-signals-landing-page-styles` and `v2-signals-landing-page-scripts` bundles |
| `templates/v2/components.html` | Add `c-signal-card` demo section |
| `templates/v2/components/page-header.html` | Add optional `cta_label`/`cta_href` params |
| `less/v2/components/page-header.less` | Add `.c-page-header__cta` styles |
| `templates/landing_pages/hapi.html` | Remove `c-anchor-links-mobile` call from primary block |
| `less/v2/hapi-landing-page.less` | Remove mobile dropdown styles |
