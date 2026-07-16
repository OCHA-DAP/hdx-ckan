# Task 043: Homepage — Curated Highlights Section

**Figma sources**: `llm_docs/redesign/figma_exports/hdx-highlights-xl.html`, `hdx-highlights-md.html`, `hdx-highlights-sm.html`

---

## Context

The v2 homepage (`templates/home/index.html`) is implemented except for the Curated Highlights section. The old v1 carousel markup is fully commented out (lines 50–95 of `home/index.html`). This task implements the replacement section using the v2 design system.

The existing carousel infrastructure (data backend, JS, analytics) is fully reusable — do not reimplement from scratch.

---

## 1. Component Definition — `c-highlight-card`

### New file locations

- **Template**: `ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/components/highlight-card.html`
- **Styles**: `ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles/src/common/less/v2/components/highlight-card.less`
- **Compiled CSS registered in**: `fanstatic/webassets.yml` → `v2-components-styles` → `v2/components/highlight-card.css`

### Props

| Prop | Type | Required | Default | Notes |
|------|------|----------|---------|-------|
| `image_url` | string | yes | — | Card hero image. `object-fit: cover`, height `10rem` |
| `title` | string | yes | — | 16px / 1rem semibold. Single-line truncate (`text-overflow: ellipsis; white-space: nowrap`) |
| `subtitle` | string | no | `''` | 14px / 0.875rem, color `var(--hdx-neutral-70)`. **Not rendered initially** (task spec), but the prop and DOM node must exist so layout is forward-compatible |
| `href` | string | yes | — | The entire card is a `<a>` link |
| `open_new_tab` | bool | no | `false` | Adds `target="_blank" rel="noopener noreferrer"` |
| `analytics_link_type` | string | no | `'carousel'` | Passed to `data-module-link_type` for `hdx_click_stopper` |

### BEM classes

```
.c-highlight-card              — outer <a> wrapper
.c-highlight-card__image       — <img> or placeholder <div>
.c-highlight-card__body        — flex column below image
.c-highlight-card__title       — heading text
.c-highlight-card__subtitle    — metadata row (hidden initially, space reserved)
```

### Card design tokens (from Figma)

| Property | Value | HDX token |
|----------|-------|-----------|
| Border | `1px solid #ebeff0` | `var(--hdx-neutral-1)` |
| Border-radius | `2px` | `var(--hdx-radius-sm)` |
| Box-shadow | `0px 1px 4px rgba(0,0,0,0.04)` | `var(--hdx-shadow-sm)` |
| Card padding | `1rem` | `var(--hdx-space-4)` |
| Image height | `10rem` | — |
| Gap (image → body) | `0.75rem` | `var(--hdx-space-3)` |
| Title font | Roboto 600, 1rem, line-height 130% | `.hdx-body-m-semibold()` mixin |
| Title color | `#101212` | `var(--hdx-neutral-95)` |
| Subtitle font | Roboto 400, 0.875rem | `.hdx-body-s()` mixin |
| Subtitle color | `#2f3536` | `var(--hdx-neutral-85)` |
| Body gap | `0.5rem` | `var(--hdx-space-2)` |

### Template skeleton

```jinja2
{% set open_new_tab = open_new_tab if open_new_tab is defined else false %}
{% set analytics_link_type = analytics_link_type if analytics_link_type is defined else 'carousel' %}
{% set subtitle = subtitle if subtitle is defined else '' %}

<a class="c-highlight-card"
   href="{{ href }}"
   {% if open_new_tab %}target="_blank" rel="noopener noreferrer"{% endif %}
   data-module="hdx_click_stopper"
   data-module-link_type="{{ analytics_link_type }}">

  {% if image_url %}
    <img class="c-highlight-card__image" src="{{ image_url }}" alt="{{ title }}" loading="lazy">
  {% else %}
    <div class="c-highlight-card__image c-highlight-card__image--placeholder"></div>
  {% endif %}

  <div class="c-highlight-card__body">
    <div class="c-highlight-card__title">{{ title }}</div>
    {% if subtitle %}
      <div class="c-highlight-card__subtitle">{{ subtitle }}</div>
    {% else %}
      <div class="c-highlight-card__subtitle" aria-hidden="true"></div>
    {% endif %}
  </div>
</a>
```

---

## 2. Carousel JS

### New file — `fanstatic/v2/highlights-carousel.js`

Registered in `fanstatic/webassets.yml` under `v2-page-scripts`. **Do not reuse `homepage-responsive.js`** — that file remains on the page for other legacy purposes but is not used by this section.

| Function | Selector | Behaviour |
|----------|----------|-----------|
| `hlInit()` | `.mobile-carousel` | Init Hammer.js swipe, arrow/dot click handlers, clone-based infinite track |
| `hlGoTo(target)` | `.mobile-carousel-inner` | Animates `left` to `-target * hlSlot`; teleports from clones to real cards |
| `hlSetDot(n)` | `.mobile-carousel .highlight-dots button` | Toggles `.active` on the nth dot |

**Selectors used** (custom — avoid Bootstrap class-name collisions):
- Carousel root: `.mobile-carousel`
- Inner sliding track: `.mobile-carousel-inner`
- Each slide: **`.highlight-slide`** (NOT `.carousel-item` — Bootstrap sets `display:none` on that globally)
- Dot container: **`.highlight-dots`** (NOT `.carousel-indicators` — Bootstrap sets `position:absolute` on that globally)
- Prev arrow: `.hdx-v2-highlights__arrow--prev` (via `extra_classes` on `c-button`)
- Next arrow: `.hdx-v2-highlights__arrow--next`

**Infinite loop — clone-based**:  
On init, the last real slide is prepended and the first is appended. Track: `[cloneLast | 1 | 2 … N | cloneFirst]`. The inner animates to the clone position, then silently teleports (`$inner.css('left', ...)`) to the matching real card — invisible because clone and real card look identical.

### Existing data backend

- **Helper**: `h.hdx_get_carousel_list()` in `ckanext-hdx_theme/ckanext/hdx_theme/helpers/helpers.py:895`
- **Action**: `hdx_carousel_settings_show` in `helpers/actions.py:348` — reads `hdx.carousel.config` from `system_info` table
- **Default data**: `helpers/initial_carousel_settings.py` — 8 sample items
- **Cap**: `max_items=3` — fixed, do not change
- **Item schema**: `id`, `title`, `description`, `order`, `graphic` (image URL), `url`, `embed`, `buttonText`, `newTab`

### Existing analytics

- Module: `hdx_click_stopper` (`fanstatic/hdx_click_stopper.js`)
- Event: `"link click"` with `linkType: "carousel"` — value is final, do not rename
- **Must be preserved** on all card `<a>` elements via `data-module="hdx_click_stopper"` + `data-module-link_type="carousel"`

### What cannot be reused

The old `hdx_carousel_item.html` snippet is v1 (Bootstrap grid, `.sub-item` classes, hover overlay button). It must not be used. The new `c-highlight-card` component replaces it entirely.

---

## 3. Integration Plan

### File to modify

`ckanext-hdx_theme/ckanext/hdx_theme/templates/home/index.html`

### Position

Insert the new section **after the alert bar** (`{% if alert_bar ... %}` block, line 47–49) and **before `#homepage-alerts`** (line 98). This replaces the commented-out block (lines 50–95) — delete the commented-out code.

### Section wrapper structure

Single carousel for all breakpoints. No separate static-grid div. CSS handles the XL vs MD/SM layout difference.

```jinja2
{% if carouselItems %}
<section class="hdx-v2-highlights">
  <div class="hdx-v2-highlights__inner hdx-v2-container">

    <div class="hdx-v2-highlights__header">
      <span class="hdx-v2-highlights__label">{{ _('HDX highlights') }}</span>
      <h2 class="hdx-v2-highlights__heading">{{ _('Curated highlights on current events') }}</h2>
    </div>

    <div class="hdx-v2-highlights__carousel mobile-carousel">
      <div class="mobile-carousel-inner">
        {% for item in carouselItems %}
          <div class="highlight-slide">
            {% snippet 'v2/components/highlight-card.html',
                image_url=item.graphic, title=item.title,
                href=item.url, open_new_tab=item.newTab %}
          </div>
        {% endfor %}
      </div>
      <div class="hdx-v2-highlights__carousel-footer">
        <div class="highlight-dots"></div>
        <div class="hdx-v2-highlights__arrows">
          {% snippet 'v2/components/button.html',
              style='tertiary', type='icon-only', size='l', state='enabled',
              icon=True, icon_src='v2/icons/arrow-left.svg',
              label=_('Previous'), extra_classes='hdx-v2-highlights__arrow--prev' %}
          {% snippet 'v2/components/button.html',
              style='tertiary', type='icon-only', size='l', state='enabled',
              icon=True, icon_src='v2/icons/arrow-right.svg',
              label=_('Next'), extra_classes='hdx-v2-highlights__arrow--next' %}
        </div>
      </div>
    </div>

  </div>
</section>
{% endif %}
```

The footer (dots + arrows) is hidden at XL via CSS. At XL the carousel becomes a plain `overflow:visible` flex row with `flex:1` on each slide and the two JS-cloned slides hidden via `.highlight-slide.is-carousel-clone { display:none }`.

### LESS

Section styles are inlined directly in `hdx-styles/src/common/less/v2/styles.less` (no separate partial). The highlight-dots rule is nested inside the `.hdx-v2-highlights {}` block.

---

## 4. Responsive Behavior

### Breakpoints

- SM: `< @hdx-bp-md` (48rem / 768px)
- MD: `@hdx-bp-md` to `@hdx-bp-xl` (48rem–80rem)
- XL: `≥ @hdx-bp-xl` (80rem / 1280px)

### XL (≥80rem)

- Same carousel DOM — JS skips init (`matchMedia` check). CSS makes it a static flex row.
- `overflow: visible` on carousel, `flex: 1` + `min-width: 0` on each `.highlight-slide`
- JS-added clones hidden via `.highlight-slide.is-carousel-clone { display: none }`
- Section padding: `6rem` vertical
- Header gap: `var(--hdx-space-10)` below header before cards
- Heading: Merriweather bold, `var(--hdx-fs-4xl)` / line-height 130%
- Label: Roboto 400, `var(--hdx-fs-l)`, color `var(--hdx-neutral-85)`
- No arrows, no dots (footer `display: none` at XL)

### MD (48rem–80rem)

- Carousel, `overflow: hidden`, card width `calc(56% - var(--hdx-space-5))` (~1.8 cards visible)
- `margin-right: var(--hdx-space-5)` on each slide (not `gap`) so `outerWidth(true)` gives accurate slot width
- Section padding: `5rem` vertical
- Heading: `var(--hdx-fs-3xl)`
- **Dots**: 3 dots — one per real card, centered row
- **Arrows**: `c-button` `style=tertiary`, `type=icon-only`, `size=l` — right-aligned row below dots

### SM (<48rem)

- Carousel, `overflow: hidden`, card width `calc(90% - var(--hdx-space-5))` (~1.1 cards visible)
- Section padding: `4rem` vertical
- Heading: `var(--hdx-fs-2xl)`
- **Dots**: 3 dots — same design as MD
- **Arrows**: same as MD

---

## 5. Data Strategy

### Current source

`h.hdx_get_carousel_list()` → `hdx_carousel_settings_show` action → `hdx.carousel.config` system_info key → JSON list of items.

Admin UI: `/ckan-admin/carousel/show` (managed via `views/custom_settings.py`).

### Fields used by `c-highlight-card`

| Data field | Card prop | Notes |
|------------|-----------|-------|
| `item.graphic` | `image_url` | URL path like `/images/homepage/mVAM.png` |
| `item.title` | `title` | Direct use |
| `item.url` | `href` | Direct use |
| `item.newTab` | `open_new_tab` | Direct use |
| `item.description` | *(unused in new design)* | Still in data model, ignored by new card |

### Subtitle — this iteration

The Figma shows a subtitle row ("4.8k Datasets • 65 organisations") under the title. This data does not exist in the current carousel data model and is **not shown in this iteration**.

- The `c-highlight-card` component **must include the subtitle element** in the DOM (prop + CSS class) so layout is forward-compatible when the field is introduced later.
- Pass no `subtitle` prop from the homepage template. The empty `<div class="c-highlight-card__subtitle">` renders with zero height and does not affect layout.
- No changes to the carousel data model, admin UI, or backend in this task.

---

## 6. Risks / Edge Cases

| Risk | Mitigation |
|------|------------|
| Zero carousel items configured | Wrap entire section in `{% if carouselItems %}` — section not rendered |
| 1 or 2 items (fewer than 3) | XL flex row still works. Carousel JS creates dots based on actual item count. Test with 1 and 2 items. |
| Long titles | Figma mandates `white-space: nowrap; overflow: hidden; text-overflow: ellipsis` — test with 80+ char titles at SM width |
| Missing image | Use placeholder div with neutral bg (follow `showcase-card.html:30` pattern). Do not break layout with broken `<img>`. |
| JS selector collision | `homepage-responsive.js` binds to `.mobile-carousel` globally. Confirmed no conflict — old Bootstrap carousel markup is fully deleted. Only one `.mobile-carousel` element in the DOM. |
| Analytics regression | Forgetting `data-module="hdx_click_stopper"` on the card `<a>` breaks analytics silently. Verify in browser console after implementation. |
| Carousel `left` animation overflow | `.mobile-carousel-inner` must have `position: relative` and `.mobile-carousel` must have `overflow: hidden` for the JS animation to clip correctly |
| Swipe on desktop | Hammer.js swipe is registered on all touch devices; on desktop this is harmless. Arrow buttons are the primary desktop interaction. |

---

## 7. Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Subtitle content source | Not shown in this iteration. DOM element present but always empty. No backend change. |
| 2 | Subtitle timeline | Deferred. Implement the component slot now; populate later. |
| 3 | Carousel autoplay | No autoplay. |
| 4 | Infinite loop | Yes — clone-based. Last slide cloned and prepended; first slide cloned and appended. After animating to a clone, JS silently resets position to the matching real card. Implemented in `fanstatic/v2/highlights-carousel.js` — `homepage-responsive.js` is not modified. |
| 5 | Card click target | Entire card (`<a>` wrapper) links to `item.url`. No "Explore" button. |
| 6 | Number of items | Cap stays at 3 (`max_items=3`). |
| 7 | Touch swipe | Yes — preserve Hammer.js swipe behavior. |
| 8 | Analytics `linkType` | Keep `"carousel"`. Do not rename. |
| 9 | XL layout | Single carousel DOM for all breakpoints. At XL, CSS makes it a static 3-card flex row via `flex:1` + `min-width:0`; clones hidden; footer `display:none`. |
| 10 | Admin UI label | No change to admin carousel UI in this task. |

---

## Prerequisites (already implemented — do not re-implement)

- `v2/components/button.html` — used for prev/next arrow buttons (`style=tertiary, type=icon-only, size=l`)
- `v2/components/activity-card.html` — reference for snippet parameter pattern
- `v2/components/showcase-card.html` — reference for image + body card layout
- `fanstatic/v2/highlights-carousel.js` — carousel JS (new, v2-only)
- `h.hdx_get_carousel_list()` — data helper (reuse, do not duplicate)
- `hdx_click_stopper.js` — analytics module (reuse, do not duplicate)
- `hdx-styles/src/common/less/v2/styles.less` — section styles inlined here

---

## Verification

After implementation, verify:

1. **XL**: 3 highlight cards render in a row with equal widths. No carousel controls visible.
2. **MD**: Carousel renders with 1.5 visible cards, 2 dots, prev/next arrows. Arrows navigate correctly.
3. **SM**: Carousel renders with ~1 visible card + peek, 3 dots, arrows work.
4. **Swipe**: Swipe left/right navigates carousel on a touch device (or DevTools mobile emulation).
5. **Empty state**: With 0 carousel items configured, the section does not render.
6. **Analytics**: Click a card → open browser console → confirm a "link click" event fires with `linkType: "carousel"`.
7. **No regression**: Hero section, alert bar, intro section all render correctly above and below.
8. **Accessibility**: Tab through carousel; dots and arrow buttons are keyboard-reachable and have visible focus states. Arrow buttons have `aria-label`.
