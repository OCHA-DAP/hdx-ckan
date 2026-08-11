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

```html
<section class="hdx-v2-barchart">
<div class="hdx-v2-barchart__inner">

  <!-- Label: updates via JS as active bar changes -->
  <div class="hdx-v2-barchart__label" aria-live="polite" aria-atomic="true">
    <span class="hdx-v2-barchart__label-name"></span>
    <span class="hdx-v2-barchart__label-count"></span>
    <span class="hdx-v2-barchart__dot" aria-hidden="true">{% include 'v2/icons/dot.svg' %}</span>
  </div>

  <!-- Bars container: JS reads data-count on each bar -->
  <div class="hdx-v2-barchart__bars"
       data-interval="2000">

    {% for loc in _hrp_filtered %}
    <div class="hdx-v2-barchart__bar{% if loop.first %} is-active{% endif %}"
         style="--bar-height: {{ (loc.package_count / _hrp_max * 100) | round(2) }}%"
         data-name="{{ loc.display_name | e }}"
         data-count="{{ loc.package_count }}">
    </div>
    {% endfor %}

  </div>

</div>
</section>
```

**Notes:**
- `__inner` uses `hdx-v2-container` like other sections.
- The dot uses `v2/icons/dot.svg` included inline (not `c-graph-point`).
- `aria-live="polite"` on the label: screen readers announce country/count changes without interrupting.
- `is-active` is pre-set to the first bar by Jinja2 so the chart is meaningful before JS loads.
- `data-name` and `data-count` on each bar: JS reads these to populate the label — no separate JS data array needed.
- Label position (both horizontal and vertical): see section 3 (Animation Strategy).

---

## 3. Animation Strategy

### JS file

**New file**: `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/bar-chart.js`

Plain vanilla JS IIFE, initialised on `DOMContentLoaded` (not a CKAN module — `ckan` global is not available when this bundle loads):

```javascript
(function () {
  'use strict';

  function initBarchart(barsEl) {
    var bars      = barsEl.querySelectorAll('.hdx-v2-barchart__bar');
    var inner     = barsEl.closest('.hdx-v2-barchart__inner');
    var label     = inner.querySelector('.hdx-v2-barchart__label');
    var nameEl    = label.querySelector('.hdx-v2-barchart__label-name');
    var countEl   = label.querySelector('.hdx-v2-barchart__label-count');
    var interval  = parseInt(barsEl.getAttribute('data-interval'), 10) || 2000;
    var activeIdx = Math.floor(Math.random() * bars.length);

    function positionLabel(bar) { /* centers label over the active bar */ }

    function nextRandom() {
      if (bars.length <= 1) { return 0; }
      var next;
      do { next = Math.floor(Math.random() * bars.length); } while (next === activeIdx);
      return next;
    }

    function activate(idx) {
      bars[activeIdx].classList.remove('is-active');
      activeIdx = idx;
      bars[activeIdx].classList.add('is-active');
      nameEl.textContent  = bars[activeIdx].getAttribute('data-name');
      countEl.textContent = bars[activeIdx].getAttribute('data-count') + ' datasets';
      positionLabel(bars[activeIdx]);
    }

    activate(activeIdx);
    setInterval(function () { activate(nextRandom()); }, interval);
  }
})();
```

### Cycling behavior

- Starts at a **random** bar index.
- Each cycle picks a **different random** index (not sequential).
- Interval: 2000ms (read from `data-interval` on the bars container).
- Loops infinitely — no end condition.

### Dissolve transition

CSS drives the fade via `background-color` transition:

```less
.hdx-v2-barchart__bar {
background-color: var(--hdx-overlay-white-20);  // inactive
transition: background-color 300ms linear;
}
.hdx-v2-barchart__bar.is-active {
background-color: var(--hdx-overlay-white-90);
}
@media (prefers-reduced-motion: reduce) {
.hdx-v2-barchart__bar { transition: none; }
}
```

`prefers-reduced-motion` keeps the 2000ms cycle but removes the 300ms transition — the state change is instant.

### Label position

On each cycle JS sets two CSS custom properties on the label:

- `--label-offset` — horizontal: centers the label over the active bar (`barCenter - label.offsetWidth / 2`). No JS clamping; the section's `overflow: hidden` clips the label at the left/right edges for the first/last bars.
- `--label-top` — vertical: positions the label so the dot's bottom sits 4px above the bar's top edge (`barTop - 4 - label.offsetHeight`), clamped to `0` so it never escapes the section's top.

Both drive CSS `transition` (300ms linear) for smooth movement.

---

## 4. Styling Strategy

### LESS file

**New file**: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/bar-chart.less`

Registered as `v2/bar-chart.css` in the `v2-page-styles` webassets bundle.

### Section container

```less
.hdx-v2-barchart {
background-color: var(--hdx-brand-7);
overflow: hidden;
position: relative;
}
```

### Bars container

```less
.hdx-v2-barchart__bars {
display: flex;
align-items: flex-end;
justify-content: space-between;
gap: 1.25rem;       // 20px — XL
height: 17.625rem;  // 282px — chart height (all breakpoints)
position: relative;
}
```

### Individual bar

```less
.hdx-v2-barchart__bar {
width: 0.5rem;     // 8px — XL
height: calc(var(--bar-height, 10%));  // CSS var set by Jinja inline style
background-color: rgba(255, 255, 255, 0.3);  // inactive — exact value TBD from Figma
opacity: 0.3;
transition: opacity 300ms linear;
flex-shrink: 0;

&.is-active {
  opacity: 0.9;
  background-color: rgba(255, 255, 255, 0.9);
}

@media (prefers-reduced-motion: reduce) {
  transition: none;
}
}
```

⚠️ **Exact inactive bar opacity/color to verify from Figma.** The Figma CSS does not set explicit `background-color` on bar elements — they are `<img>` tags with colors baked into the image. The `rgba(255,255,255, ...)` approach is the implementation interpretation; confirm with designer.

### Label

```less
.hdx-v2-barchart__label {
position: absolute;
top: 6.5rem;
display: flex;
flex-direction: column;
align-items: center;
gap: 0.187rem;        // 3px — var(--gap-3)
color: #fff;
font-family: Roboto, Arial, sans-serif;
font-size: 0.875rem;  // 14px
transform: translateX(var(--label-offset, 0px));
transition: transform 300ms linear;

@media (prefers-reduced-motion: reduce) {
  transition: none;
}
}

.hdx-v2-barchart__label-name {
font-weight: 600;
line-height: 1.3;
text-shadow: 3px 0 0 #18614c, 0 3px 0 #18614c, -3px 0 0 #18614c, 0 -3px 0 #18614c;
}

.hdx-v2-barchart__label-count {
line-height: 1.3;
}
```

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

```less
// MD
@media (max-width: @hdx-bp-xl - 1) {
.hdx-v2-barchart__bars {
  gap: 0.756rem;
}
.hdx-v2-barchart__bar {
  width: 0.375rem;  // verify
}
}

// SM
@media (max-width: @hdx-bp-md - 1) {
.hdx-v2-barchart__bars {
  gap: 0.375rem;
}
.hdx-v2-barchart__bar {
  width: 0.25rem;
}
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
| Very long `display_name` | Full name displayed — no truncation. Text wraps naturally inside the label. |
| Label overflows chart at first/last bar | Label stays centered over the bar; the half that would extend outside is clipped by `overflow: hidden` on the section |
| JS disabled | First bar stays `is-active` (pre-set by Jinja); label is empty (no text injected); section is still visible but static |

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
| D1 | Does the label move or stay fixed? | **Moves** — JS sets `--label-offset` on each cycle; CSS `translateX` follows the active bar, clamped to chart bounds |
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
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/v2/bar-chart.js` | **New** — CKAN module `hdx_barchart` |
| `ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml` | `v2/bar-chart.css` added to `v2-page-styles`; new `v2-home-page-scripts` bundle containing `bar-chart.js` |
