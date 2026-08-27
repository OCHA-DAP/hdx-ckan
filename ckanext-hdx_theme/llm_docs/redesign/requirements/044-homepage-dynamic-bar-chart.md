# Homepage — Dynamic Data Visualization (HRP Bar Chart)

**Figma source**: `llm_docs/redesign/figma_exports/home-bar-chart.html`

---

## Context

The homepage (`home/index.html`) needs a dynamic data visualization showing dataset counts per HRP (Humanitarian Response Plan) country as an animated vertical bar chart.

The chart cycles through HRP countries — one is "active" at a time, highlighted with its country name and dataset count displayed. The animation is fully automatic (no interaction).

This is a **homepage-specific implementation**, not a reusable component.

The helper `hdx_get_locations` was added specifically for this visualization (commit `853c83d591`).

---

## 1. Data Mapping

### Source

```jinja
{% set locations = h.hdx_get_locations(hrp=True) %}
```

### Return structure

```python
[
  {
      'id': 'string',
      'name': 'slug',          # URL slug (e.g. 'nigeria')
      'display_name': 'string', # Human-readable (e.g. 'Nigeria')
      'package_count': int,     # Can be None
      'hrp': True,              # Always True when hrp=True is passed
  },
  ...
]
```

Sorted alphabetically by `display_name` ascending (server-side, no client sort needed).

### Filtering

Exclude locations where `package_count` is `None` or `0` before rendering:

```jinja
{% set filtered = locations | selectattr('package_count') | list %}
```

(`selectattr('package_count')` is falsy-safe: None, 0, and missing are all excluded.)

### Bar height calculation

Bar height is proportional to `package_count` relative to the maximum in the filtered set.

```jinja
{% set max_count = filtered | map(attribute='package_count') | max %}
```

Each bar's height as a percentage of the chart height:

```
bar_height_pct = (location.package_count / max_count) * 100
```

Pass `max_count` as a template variable so each bar can compute its own `style="--bar-height: {pct}%"`.

---

## 2. Rendering Strategy

### Template location

Add a new `<section>` in `ckanext-hdx_theme/ckanext/hdx_theme/templates/home/index.html`, between the hero and the `hdx-v2-intro` section.

No `{% if v2 %}` gate — the homepage template already extends `v2/page.html` exclusively.

### Empty state

If `filtered` is empty after the `selectattr` filter, hide the section entirely:

```jinja
{% if filtered %}
<section class="hdx-v2-barchart">
...
</section>
{% endif %}
```

### DOM structure

Renders inside the shared `.hdx-v2-hero-band` wrapper, immediately after the hero section (see
[024](024-homepage-hero-section.md)) — that wrapper is what paints the dark background now, not this
section itself:

```html
<section class="hdx-v2-barchart">
  <div class="hdx-v2-barchart__inner hdx-v2-container">

    <!-- Hidden announcer: JS updates its text as the active bar-group changes -->
    <span class="sr-only" aria-live="polite" aria-atomic="true" data-barchart-announcer></span>

    <!-- Bars container -->
    <div class="hdx-v2-barchart__bars" data-interval="2500">
      {% for loc in _hrp_filtered %}
      <div class="hdx-v2-barchart__bar-group"
           style="--bar-height: {{ (loc.package_count / _hrp_max * 100) | round(2) }}%"
           data-name="{{ loc.display_name | e }}"
           data-count="{{ loc.package_count }}">
        <div class="hdx-v2-barchart__label">
          <span class="hdx-v2-barchart__label-name">{{ loc.display_name | e }}</span>
          <span class="hdx-v2-barchart__label-count">{{ loc.package_count }} datasets</span>
          <span class="hdx-v2-barchart__dot" aria-hidden="true">{% include 'v2/icons/dot.svg' %}</span>
        </div>
        <div class="hdx-v2-barchart__bar"></div>
      </div>
      {% endfor %}
    </div>

  </div>
</section>
```

**Notes:**
- `__inner` uses `hdx-v2-container` like other sections.
- The dot uses `v2/icons/dot.svg` included inline (not `c-graph-point`).
- Each bar-group renders its own label directly (name/count as real text, not JS-injected) — the label never moves; only its opacity toggles when its group becomes/stops being active.
- A hidden `sr-only` node with `aria-live="polite"` is updated by JS on each cycle so screen readers still announce country/count changes, since the visible per-bar labels no longer swap text.
- `is-active` is applied purely by JS at load (`bar-chart.js` activates a random bar-group on `DOMContentLoaded`) — no bar-group is pre-marked active by Jinja.
- `data-name` and `data-count` on each bar-group: JS reads these to populate the hidden announcer — no separate JS data array needed.
- Label position (both horizontal and vertical): see section 3 (Animation Strategy).

---

## 3. Animation Strategy

### JS file

**New file**: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/bar-chart.js`

Plain vanilla JS IIFE, initialised on `DOMContentLoaded` (not a CKAN module — `ckan` global is not available when this bundle loads). No position math — every label already sits above its own bar via CSS; JS only toggles which bar-group is active and updates the hidden announcer:

```javascript
(function () {
  'use strict';

  function initBarchart(barsEl) {
    var groups    = barsEl.querySelectorAll('.hdx-v2-barchart__bar-group');
    var inner     = barsEl.closest('.hdx-v2-barchart__inner');
    var announcer = inner.querySelector('[data-barchart-announcer]');
    var interval  = parseInt(barsEl.getAttribute('data-interval'), 10) || 2500;
    var activeIdx = Math.floor(Math.random() * groups.length);

    function nextRandom() {
      if (groups.length <= 1) { return 0; }
      var next;
      do { next = Math.floor(Math.random() * groups.length); } while (next === activeIdx);
      return next;
    }

    function activate(idx) {
      groups[activeIdx].classList.remove('is-active');
      activeIdx = idx;
      groups[activeIdx].classList.add('is-active');
      if (announcer) {
        announcer.textContent = groups[activeIdx].getAttribute('data-name') + ', ' +
          groups[activeIdx].getAttribute('data-count') + ' datasets';
      }
    }

    activate(activeIdx);
    setInterval(function () { activate(nextRandom()); }, interval);
  }
})();
```

### Cycling behavior

- Starts at a **random** bar-group index.
- Each cycle picks a **different random** index (not sequential).
- Interval: 2500ms (read from `data-interval` on the bars container).
- Loops infinitely — no end condition.

### Dissolve transition

The bar itself cross-fades via `background-color`, symmetrically (300ms linear both when becoming active and when becoming inactive):

```less
.hdx-v2-barchart__bar {
background-color: var(--hdx-overlay-white-20);  // inactive
transition: background-color 300ms linear;
}
.hdx-v2-barchart__bar-group.is-active .hdx-v2-barchart__bar {
background-color: var(--hdx-overlay-white-90);
}
```

The label uses an **asymmetric** dissolve — fade out only, no fade in — via the "transition only on the rule entered when deactivating" pattern:

```less
.hdx-v2-barchart__label {
opacity: 0;
transition: opacity 300ms linear;  // fires when a group loses is-active
}
.hdx-v2-barchart__bar-group.is-active .hdx-v2-barchart__label {
opacity: 1;
transition: none;  // instant show, no fade-in
}
```

Real `prefers-reduced-motion` support is inert sitewide pending task 069's documented follow-up (see that doc §6) — not specific to this component.

### Label position

The label is **statically anchored to its own bar** via plain CSS — it never moves and JS never measures or sets its position:

```less
.hdx-v2-barchart__label {
position: absolute;
left: 50%;
bottom: calc(var(--bar-height, 10%) + 0.25rem);  // 4px above the bar's own top edge
transform: translateX(-50%);  // static horizontal centering, never animated
}
```

`--bar-height` is the same custom property already set on the bar-group by Jinja for the bar's own height, so the label's vertical offset tracks that bar's height automatically with no JS involved. Horizontal overflow for the first/last bar-groups is still clipped by the section's `overflow: hidden`, same as before.

---

## 4. Styling Strategy

### LESS file

**New file**: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/bar-chart.less`

Registered as `v2/bar-chart.css` in the `v2-home-page-styles` webassets bundle.

### Section container

```less
.hdx-v2-barchart {
    overflow: hidden;

    &__inner {
        position:    relative;
        padding-top: var(--hdx-space-20);
    }
}
```

### Bars container

```less
&__bars {
    display:         flex;
    align-items:     flex-end;
    justify-content: space-between;
    gap:             var(--hdx-space-13);  // 6px SM
    height:          17.625rem;            // 282px — chart height (all breakpoints)
    position:        relative;

    @media (min-width: @hdx-bp-md) { gap: var(--hdx-space-3); }   // ~12px MD
    @media (min-width: @hdx-bp-xl) { gap: var(--hdx-space-5); }   // 20px XL
}
```

### Individual bar

```less
&__bar {
    // --bar-height is set per-element by Jinja: style="--bar-height: {pct}%"
    width:            var(--hdx-space-2);  // 8px, uniform at every breakpoint
    height:           var(--bar-height, 10%);
    background-color: var(--hdx-overlay-white-20);  // inactive
    transition:       background-color var(--hdx-duration-base) var(--hdx-ease-linear);
    .hdx-motion();   // guards the transition under prefers-reduced-motion
}

&__bar-group.is-active &__bar {
    background-color: var(--hdx-overlay-white-90);
}
```

Color swaps via `background-color` only — there is no separate `opacity` property on the bar itself.

### Label

```less
&__label {
    position:       absolute;
    left:           50%;
    bottom:         calc(var(--bar-height, 10%) + 0.25rem);
    transform:      translateX(-50%);  // static centering, never animated
    width:          max-content;  // bypasses shrink-to-fit against the narrow bar-group's tiny available width
    display:        flex;
    flex-direction: column;
    align-items:    center;
    text-align:     center;
    gap:            0.187rem;        // 3px
    color:          var(--hdx-neutral-0);
    font-family:    var(--hdx-font-body);
    font-size:      var(--hdx-fs-s);
    opacity:        0;
    transition:     opacity var(--hdx-duration-base) var(--hdx-ease-linear);  // fires on fade OUT only
    pointer-events: none;
    .hdx-motion();
}

&__bar-group.is-active &__label {
    opacity:    1;
    transition: none;  // instant show, no fade-in
}

&__label-name,
&__label-count {
    line-height: var(--hdx-lh-normal);
    text-shadow: 3px 0 0 var(--hdx-brand-7), 0 3px 0 var(--hdx-brand-7),
                 -3px 0 0 var(--hdx-brand-7), 0 -3px 0 var(--hdx-brand-7);
}

&__label-name {
    font-weight: var(--hdx-fw-semibold);
    max-width:   9rem;  // wrap onto a 2nd line rather than overflow for very long country names
}

&__label-count {
    white-space: nowrap;  // always short ("N datasets") — never wrap
}
```

Without `width: max-content` on `.hdx-v2-barchart__label`, the browser computes the label's width via
shrink-to-fit bounded by the narrow bar-group as containing block — collapsing to just a few pixels of
"available space" and forcing even short text (e.g. "43 datasets") to wrap at the word boundary. The
`max-width`/`white-space: nowrap` pair above then controls *intentional* wrapping: the count never
wraps (always short), the name wraps only past 9rem (real HRP names run up to ~35-40 chars, e.g.
"Democratic Republic of the Congo", so long outliers wrapping to a 2nd line is expected).

### Dot indicator — inline SVG

The dot uses `v2/icons/dot.svg` included directly in the template (not `c-graph-point`). The SVG contains a 24px white halo ring (20% opacity) and an 8px white inner dot (90% opacity) — both rendered white on the teal background. Sized via `__dot` CSS class (`var(--hdx-space-6)` × `var(--hdx-space-6)`).

---

## 5. Responsive Behavior

All three breakpoints use the same chart height (282px = `17.625rem`). Only bar width, gap, and section padding change.

Bar width is **uniform across all breakpoints**: `var(--hdx-space-2)` (8px). Only the gap changes:

### XL (≥ 80rem)
- Gap: `var(--hdx-space-5)` (20px)

### MD (≥ 48rem, < 80rem)
- Gap: `var(--hdx-space-3)` (~12px)

### SM (< 48rem)
- Gap: `var(--hdx-space-13)` (6px)

### LESS breakpoint overrides

Mobile-first — SM values are the unprefixed default on `&__bars`, MD/XL layer on top via `min-width`
(see the "Bars container" snippet above). Bar width has no override at any breakpoint — it stays
`var(--hdx-space-2)` throughout.

```less
&__bars {
    gap: var(--hdx-space-13);  // 6px — SM default

    @media (min-width: @hdx-bp-md) { gap: var(--hdx-space-3); }  // ~12px MD
    @media (min-width: @hdx-bp-xl) { gap: var(--hdx-space-5); }  // 20px XL
}
```

Use existing breakpoint tokens `@hdx-bp-xl` and `@hdx-bp-md` (do not introduce new breakpoints).

---

## 6. Edge Cases

| Case | Behavior |
|---|---|
| Filtered list is empty (all HRP have no datasets) | `{% if filtered %}` guard hides the section entirely |
| Single location after filtering | One bar shown; animation starts but does nothing (one-element cycle) |
| All locations have equal `package_count` | All bars render at equal height (100%); animation still cycles the label |
| `max_count` is 0 or None | Cannot occur — filtered list excludes `package_count ≤ 0`; guard prevents rendering |
| Very long `display_name` | Full name displayed — no truncation. Name wraps onto a 2nd line past `max-width: 9rem`; the dataset-count line never wraps. |
| Label overflows chart at first/last bar | Label stays centered over the bar; the half that would extend outside is clipped by `overflow: hidden` on the section |
| JS disabled | No bar-group is ever marked `is-active` (only `bar-chart.js` applies it, on `DOMContentLoaded`). All bars render at their inactive token color with no highlight; all labels stay `opacity: 0`. Chart is still visible and static, just without the highlighted-country presentation. |

---

## 7. Reuse Audit

| Element | Existing | Decision |
|---|---|---|
| Dot indicator | `v2/icons/dot.svg` template | **Inline SVG** — 24px halo + 8px dot baked into the SVG as white ellipses; no `c-graph-point` |
| Animation cycling | None in v2 | **New** — `setInterval` + CSS opacity transition, minimal vanilla JS |
| Vertical bar chart | None (C3.js/D3 exist but are heavyweight) | **New** — pure CSS flex + height percentage; no chart library |
| Fade `@keyframes` reference | `fadeInAnimation` in `onboarding.less` | Reference only — use CSS `transition` instead of `@keyframes` for cycling |
| Homepage carousel JS | `homepage-responsive.js` uses Hammer.js + jQuery `.animate()` | Do NOT reuse — this chart has no swipe, no jQuery animation needed |

---

## 8. Decisions Taken

| # | Question | Decision |
|---|---|---|
| D1 | Does the label move or stay fixed? | **Fixed** — each bar-group renders its own label, statically CSS-anchored above its own bar (`bottom: calc(var(--bar-height) + 4px)`); JS only toggles which group is active, no position math, no movement |
| D2 | Inactive bar color/opacity? | **Active**: `var(--hdx-overlay-white-90)` · **Inactive**: `var(--hdx-overlay-white-20)` (new token added to overlays.less + foundation) |
| D3 | `--on-dark` modifier location? | **Shared** `selection.less` — added `.c-graph-point--on-dark` modifier reusable for future dark-background contexts |
| D4 | MD bar width? | **8px** (same as XL) — SM=4px (`--hdx-space-1`), MD/XL=8px (`--hdx-space-2`) |
| D5 | Analytics tracking? | **None** for now |
| D6 | Error guard for `hdx_get_locations`? | **Helper-level `try/except`** — catches any exception and returns `[]`; template guard `{% if _hrp_filtered %}` hides section when empty |

---

## Files Affected

| File | Action |
|---|---|
| `ckanext-hdx_theme/ckanext/hdx_theme/templates/home/index.html` | Added `<section class="hdx-v2-barchart">` between hero and alert bar; `{% asset 'hdx_theme/v2-home-page-scripts' %}` in `head_extras` |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/bar-chart.less` | **New** — all chart LESS; compiles to `fanstatic/v2/bar-chart.css` |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/overlays.less` | Added `@hdx-overlay-white-20` token |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/foundation.less` | Exported `--hdx-overlay-white-20` as CSS custom property |
| `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/selection.less` | Added `.c-graph-point--on-dark` modifier |
| `ckanext-hdx_theme/ckanext/hdx_theme/helpers/helpers.py` | Added `try/except` to `hdx_get_locations` — returns `[]` on any exception |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/bar-chart.js` | **New** — plain vanilla IIFE, initialised on `DOMContentLoaded` (not a CKAN module, see §3) |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` | `v2/bar-chart.css` added to `v2-home-page-styles`; new `v2-home-page-scripts` bundle containing `bar-chart.js` |
