# Task 024: Homepage hero section

Implement the first section of the homepage (v2). Displays a heading, subtitle, large search field with autocomplete panel (UI only, no logic), and a secondary CTA button. Layout is full-width, column-stacked, centered. Homepage-specific BEM block — not a shared component.

**Figma source:** `llm_docs/redesign/figma_exports/homepage-xl.html`, `homepage-md.html`, `homepage-sm.html`

---

## Responsive breakpoints

| Label | Range | `__inner` padding | `__inner` gap | Heading size | Subtitle size | `__actions` |
|-------|-------|-------------------|---------------|--------------|---------------|-------------|
| SM | < 48rem | `8rem 1.25rem 4rem` | `2.5rem` | `var(--hdx-fs-4xl)` | `var(--hdx-fs-m)` | column, `width: 100%` |
| MD | 48rem – 79.9375rem | `6rem 3rem 4rem` | `3rem` | `var(--hdx-fs-4xl)` | `var(--hdx-fs-m)` | row, `width: 60%` |
| XL | ≥ 80rem | top: `10rem` (rest unchanged) | `5rem` | `3rem` | `var(--hdx-fs-l)` | row, `width: 60%` |

Breakpoint variables: `@hdx-bp-md: 48rem`, `@hdx-bp-xl: 80rem` (from `breakpoints.less`).

---

## Content

| Element | Value |
|---------|-------|
| Heading (`h1`) | "The Humanitarian Data Exchange" |
| Subtitle (`p`) | "Find, share and use humanitarian data all in one place" |
| Search placeholder | "Search for datasets, locations or organisations" |
| Button label | "Explore data" |

---

## What to create or update

### `templates/home/index.html`

Extends `v2/page.html`. The hero section markup uses `autocomplete.html` only — it already renders the search input internally, so do not include `search-input.html` separately.

```html
<section class="hdx-v2-hero">
  <div class="hdx-v2-hero__inner hdx-v2-container">

    <div class="hdx-v2-hero__header">
      <h1 class="hdx-v2-hero__heading">{{ _('The Humanitarian Data Exchange') }}</h1>
      <p class="hdx-v2-hero__subtitle">{{ _('Find, share and use humanitarian data all in one place') }}</p>
    </div>

    <div class="hdx-v2-hero__actions">

      <div class="hdx-v2-hero__search">
        {% snippet 'v2/components/autocomplete.html',
            placeholder=_('Search for datasets, locations or organisations'),
            value='', state='enabled' %}
      </div>

      {% snippet 'v2/components/button.html',
          style='secondary', type='text', size='l',
          state='enabled', icon=False,
          label=_('Explore data'),
          tag='a', href=h.url_for('dataset.search') %}

    </div>

  </div>
</section>
```

### `hdx-styles/src/common/less/v2/pages/home.less`

BEM block: `hdx-v2-hero`. Dark background token: `@hdx-v2-hero-bg: var(--hdx-brand-7)`.

Media queries are nested directly inside each element block (see [CONVENTIONS.md](../CONVENTIONS.md)).

```less
@import "breakpoints.less";

@hdx-v2-hero-bg: var(--hdx-brand-7);

.hdx-v2-hero {
    width:            100%;
    background-color: @hdx-v2-hero-bg;
    padding-top: 8rem;

    @media (min-width: @hdx-bp-md) { padding-top: 6rem; }
    @media (min-width: @hdx-bp-xl) { padding-top: 10rem; }

    &__inner {
        // .container handles horizontal padding; vertical padding is on the outer block
        display:        flex;
        flex-direction: column;
        align-items:    center;
        text-align:     center;
        gap:            2.5rem;

        @media (min-width: @hdx-bp-md) { gap: 3rem; }
        @media (min-width: @hdx-bp-xl) { gap: 5rem; }
    }

    &__header {
        display:        flex;
        flex-direction: column;
        align-items:    center;      // centers heading/subtitle within the stretched header
        align-self:     stretch;
        gap:            var(--hdx-space-3);
    }

    &__heading {
        font-family: var(--hdx-font-display);  // Merriweather
        font-size:   var(--hdx-fs-4xl);
        font-weight: var(--hdx-fw-bold);
        line-height: var(--hdx-lh-normal);
        color:       var(--hdx-neutral-0);
        margin:      0;

        @media (min-width: @hdx-bp-xl) { font-size: 3rem; }
    }

    &__subtitle {
        font-family: var(--hdx-font-body);     // Roboto
        font-size:   var(--hdx-fs-m);
        font-weight: var(--hdx-fw-regular);
        line-height: var(--hdx-lh-normal);
        color:       var(--hdx-neutral-0);
        margin:      0;

        @media (min-width: @hdx-bp-xl) { font-size: var(--hdx-fs-l); }
    }

    &__actions {
        display:        flex;
        flex-direction: column;
        align-items:    center;
        gap:            var(--hdx-space-3);
        width:          100%;

        @media (min-width: @hdx-bp-md) { flex-direction: row; width: 36.375rem; }
    }

    &__search {
        width:          100%;              // full width in SM column layout
        display:        flex;
        flex-direction: column;
        align-items:    flex-start;
        position:       relative;          // anchor for autocomplete panel

        @media (min-width: @hdx-bp-md) { flex: 1; width: auto; }
    }

    // Dark-surface overrides for c-button--secondary.
    // No --on-dark modifier exists in buttons.less; scoped here to avoid global side-effects.
    .c-button--secondary {
        background-color: transparent;
        border-color:     var(--hdx-neutral-2);
        color:            var(--hdx-neutral-0);

        &:hover  { background-color: var(--hdx-overlay-white-10); }
        &:active {
            background-color: var(--hdx-overlay-white-15);
            border-color:     var(--hdx-neutral-0);
            color:            var(--hdx-neutral-0);
        }
    }
}
```

### Compiled CSS

`fanstatic/v2/pages/home.css` — auto-compiled by the IDE from `home.less`. Already bundled in `v2-page-styles` via `webassets.yml`; no separate asset group needed.

---

## Constraints

- Do not implement search/autocomplete JS logic — UI markup only.
- Do not create shared components; this block is homepage-specific.
- Use `var(--hdx-*)` CSS custom properties throughout — no hardcoded values except `@hdx-v2-hero-bg`.
- `autocomplete.html` renders the search input internally; do not include `search-input.html` separately.
