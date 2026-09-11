# Task 026: Homepage intro section

Implement the intro section of the homepage (v2), directly after the hero. Contains an eyebrow label, heading, and two activity cards side by side. Cards stack vertically at the SM breakpoint. This is a homepage-specific layout block — not a shared component.

**Figma sources:**
- `llm_docs/redesign/figma_exports/homepage-intro-lg.html`
- `llm_docs/redesign/figma_exports/homepage-intro-md.html`
- `llm_docs/redesign/figma_exports/homepage-intro-sm.html`

---

## Activity card changes (prerequisite)

Two extensions to `activity-card.html` are required before this section can be built. Both are backwards-compatible — existing call sites are unaffected.

### 1. `button_style` parameter

The "Share and contribute" card needs a secondary button. Add `button_style` (default: `'primary'`) and forward it as `style` to `button.html`.

### 2. `size='responsive'` variant

Use `size='responsive'` in the intro section so the card self-sizes based on the viewport — no overrides needed in the section LESS. The card component handles sm/md/lg tokens at the appropriate breakpoints.

See requirement 025 for implementation details of both.

---

## Responsive breakpoints

| Label | Viewport | Section padding | Section gap | Cards layout | Cards gap |
|-------|----------|----------------|-------------|--------------|-----------|
| SM | < 48rem (`@hdx-bp-md`) | `4rem 1rem` | `2rem` | column (stacked) | `0.75rem` |
| MD | 48rem – 79.9375rem | `6rem 3rem` | `2rem` | row (side by side) | `1.25rem` |
| LG | ≥ 80rem (`@hdx-bp-xl`) | `7rem 3rem` | `2.5rem` | row (side by side) | `1.25rem` |

Card sizing is handled entirely by `c-activity-card--size-responsive` — no card overrides in section LESS.

---

## Header typography

| Element | SM | MD | LG |
|---------|-----|-----|-----|
| Eyebrow label | `var(--hdx-fs-s)`, `var(--hdx-neutral-85)` | `var(--hdx-fs-m)` | `var(--hdx-fs-l)` |
| Heading | `var(--hdx-fs-2xl)`, Merriweather bold | `var(--hdx-fs-3xl)` | `var(--hdx-fs-4xl)` |
| Header internal gap | `0.5rem` | `0.75rem` | `0.75rem` |

Heading color: `var(--hdx-neutral-95)`. Verify token values against `foundation.less` before coding.

---

## Content

| Element | Value |
|---------|-------|
| Eyebrow label | "About HDX" |
| Heading | "An open platform for sharing data across crises and organisations" |
| Card 1 heading | "Find data" |
| Card 1 subtitle | "Search our catalogue of more than 20,000 datasets to find and download the data you need" |
| Card 1 icon | `v2/icons/search.svg` |
| Card 1 button | "Search data", `href=h.url_for('dataset.search')`, `button_style='primary'` |
| Card 2 heading | "Share data" |
| Card 2 subtitle | "Join the 200+ humanitarian organisations sharing data on HDX - contribute your organisation's data to support humanitarian response" |
| Card 2 icon | `v2/icons/upload.svg` |
| Card 2 button | "Learn More", `href=docs_links['QA_PROCESS']` (from `h.HDX_CONST('DOCUMENTATION_LINKS')`), `button_style='secondary'`, opens in a new tab |

---

## Files Affected

### 1. `ckanext/hdx_theme/templates/v2/components/activity-card.html`

Add `button_style` and `size='responsive'` support (see requirement 025).

### 2. `ckanext/hdx_theme/templates/home/index.html`

Intro section markup (order relative to other homepage sections has since shifted — bar-chart/alert/highlights/signals sections were added between hero and intro by later tasks):

```html
<section class="hdx-v2-intro">
  <div class="hdx-v2-intro__inner hdx-v2-container">

    <div class="hdx-v2-intro__header">
      <span class="hdx-v2-intro__label">{{ _('About HDX') }}</span>
      <h2 class="hdx-v2-intro__heading">{{ _('An open platform for sharing data across crises and organisations') }}</h2>
    </div>

    {% set docs_links = h.HDX_CONST('DOCUMENTATION_LINKS') %}
    <div class="c-activity-card-list">

      {% snippet 'v2/components/activity-card.html',
          size='responsive',
          icon_src='v2/icons/search.svg',
          heading=_('Find data'),
          subtitle=_('Search our catalogue of more than 20,000 datasets to find and download the data you need'),
          button_label=_('Search data'),
          button_href=h.url_for('dataset.search'),
          button_style='primary' %}

      {% snippet 'v2/components/activity-card.html',
          size='responsive',
          icon_src='v2/icons/upload.svg',
          heading=_('Share data'),
          subtitle=_("Join the 200+ humanitarian organisations sharing data on HDX - contribute your organisation's data to support humanitarian response"),
          button_label=_('Learn More'),
          button_href=docs_links['QA_PROCESS'],
          button_style='secondary',
          button_attrs={'data-module': 'hdx_click_stopper', 'data-module-link_type': 'homepage body', 'target': '_blank', 'rel': 'noopener noreferrer'} %}

    </div>

  </div>
</section>
```

### 3. `hdx-styles/src/common/less/v2/pages/home.less`

Add an `hdx-v2-intro` block after `hdx-v2-hero`. Card sizing is owned by the component — the section only sets layout and `flex: 1` for equal-width columns.

```less
.hdx-v2-intro {
    width:   100%;
    padding: 4rem 1rem;

    @media (min-width: @hdx-bp-md) { padding: 6rem 3rem; }
    @media (min-width: @hdx-bp-xl) { padding: 7rem 3rem; }

    &__inner {
        display:        flex;
        flex-direction: column;
        align-items:    flex-start;
        gap:            2rem;

        @media (min-width: @hdx-bp-xl) { gap: 2.5rem; }
    }

    &__header {
        display:        flex;
        flex-direction: column;
        align-items:    flex-start;
        gap:            0.5rem;

        @media (min-width: @hdx-bp-md) { gap: 0.75rem; }
    }

    &__label {
        font-family: var(--hdx-font-body);
        font-size:   var(--hdx-fs-s);
        line-height: var(--hdx-lh-normal);
        color:       var(--hdx-neutral-85);

        @media (min-width: @hdx-bp-md) { font-size: var(--hdx-fs-m); }
        @media (min-width: @hdx-bp-xl) { font-size: var(--hdx-fs-l); }
    }

    &__heading {
        font-family: var(--hdx-font-display);
        font-size:   var(--hdx-fs-2xl);
        font-weight: var(--hdx-fw-bold);
        line-height: var(--hdx-lh-normal);
        color:       var(--hdx-neutral-95);
        margin:      0;

        @media (min-width: @hdx-bp-md) { font-size: var(--hdx-fs-3xl); }
        @media (min-width: @hdx-bp-xl) { font-size: var(--hdx-fs-4xl); }
    }

}
```

The card row uses the component-owned `.c-activity-card-list` wrapper (in `less/v2/components/activity-card.less`): flex column with `gap: var(--hdx-space-3)`, row with `gap: var(--hdx-space-5)` at MD+, and `> .c-activity-card { flex: 1; }`.

---

## Constraints

- No hardcoded colours, spacing, or font sizes — use `var(--hdx-*)` tokens throughout.
- Card sizing is owned entirely by `--size-responsive` in the component. The section LESS does not override any card internals.
- The `button_style` and `size='responsive'` extensions to `activity-card.html` must be backwards-compatible.
- Wrap all user-visible strings in `_()`.
- No explicit `background-color` on the section — inherits the default page background.
- Follow the full-bleed two-layer layout pattern from CONVENTIONS.md (`section.hdx-v2-intro` outer + `div.hdx-v2-intro__inner.container` inner).
