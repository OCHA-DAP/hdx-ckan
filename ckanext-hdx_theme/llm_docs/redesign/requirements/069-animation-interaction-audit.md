# Animation & Interaction Audit

## Context

The v2 redesign is functionally complete across the pages it covers; the motion layer (transition timing,
easing curves, animation mechanisms) was never audited as a system — each component shipped whatever
timing felt right in the moment. The user supplied an exact Figma-sourced spec (mechanism, easing curve,
duration, trigger) for 9 interactions spanning the homepage, location map, two carousels, mobile nav, and
the location data-grid drawer. This doc is an audit: current implementation vs. spec, options
considered, and the decisions taken for each — see §6.

Separately, and unrelated to any of the 9 items' own correctness: the OS-level "prefers-reduced-motion"
accessibility feature (added under task `041-accessibility-wcag-audit.md` to fix violations V-10/V-15) was
silently short-circuiting several of these animations during testing whenever the tester's own OS/browser
has reduced-motion enabled. It has been **temporarily commented out** (not removed) in all HDX-authored
locations so real animation behavior can be verified — see §4. This is a standing accessibility regression
while disabled and must be restored before anything ships; it is not part of the audit's own findings.

## Scope

**In scope** (compared against the supplied spec): homepage bar chart, signals carousel, highlights
carousel, mobile nav "profile" second-level panel, location map hover tooltip, anchor-link smooth scroll
(site-wide + the data-grid drawer's own anchor nav), and the location data-grid "legend" drawer.

**Out of scope, commented on only**: location map zoom (+/−). This is Leaflet's own built-in zoom
animation, not HDX-authored — see §1.2 for the reading, no options/recommendation are offered since fixing
it would mean overriding vendor library defaults rather than touching HDX code.

---

## 1. Audit Findings — current implementation per item

### 1.1 Homepage bar chart

- **Files**: `fanstatic/v2/bar-chart.js`, `hdx-styles/src/common/less/v2/bar-chart.less`.
- **Mechanism**: plain `setInterval`, no rAF/library. JS only toggles `is-active` on a bar-group and
  updates a hidden `aria-live` announcer's text — no position math, no `getBoundingClientRect`. Each
  bar-group renders its own label statically anchored above its own bar via CSS; the label never moves.
  ```js
  var interval = parseInt(barsEl.getAttribute('data-interval'), 10) || 2500;   // bar-chart.js
  setInterval(function () { activate(nextRandom()); }, interval);              // bar-chart.js
  ```
  `nextRandom()` picks a different random bar-group index each cycle (not sequential).
- **CSS**:
  ```less
  &__bar {
      background-color: var(--hdx-overlay-white-20);
      transition:       background-color 300ms linear;
  }
  &__bar-group.is-active &__bar { background-color: var(--hdx-overlay-white-90); }
  &__label {
      bottom:     calc(var(--bar-height, 10%) + 0.25rem);
      transform:  translateX(-50%);  // static, never animated
      opacity:    0;
      transition: opacity 300ms linear;  // fires on fade OUT only
  }
  &__bar-group.is-active &__label { opacity: 1; transition: none; }  // instant show, no fade-in
  ```
- **Values found**: interval **2500ms** (updated from 2000ms at the user's request, per a fresh
  Figma-sourced spec supplied after this audit's original pass), transition **300ms**, easing
  **`linear`**. The bar's background-color cross-fade stays symmetric (300ms both ways, unchanged by
  this revision); the label now uses an asymmetric fade — 300ms linear fade-out, instant (no-transition)
  show — matching the literal "dissolve: fade out, no fade in" spec.
- **Mechanism vs. spec label**: resolved as part of this revision — the label previously had no fade at
  all (only a `transform`/`top` slide between shared-element positions, which read as a moving "Pong"
  paddle rather than a dissolve). It's now a real per-bar-group opacity toggle; the bar's own
  `background-color` cross-fade is unchanged and was already judged close enough to a dissolve.
- **Position architecture**: the previous drift (`bar-chart.js`'s `MARGIN_PX = 5` vs. the doc's 4px) no
  longer applies — the label's position is now a pure CSS `calc()` off the same `--bar-height` custom
  property the bar itself uses, hardcoded to 4px, with no separate JS constant to drift.
- **Tokens**: uses color tokens (`--hdx-overlay-white-20/-90`) and the motion tokens
  (`--hdx-duration-base`, `--hdx-ease-linear`); the `2500` interval value remains a hardcoded literal
  (JS default + `data-interval` attribute), not a custom property.

### 1.2 Location map — zoom in/out (+/−) — *out of scope, comment only*

- **Files**: no HDX-authored zoom logic exists. `fanstatic/browse_/browse.js` constructs the Leaflet map
  with Leaflet's stock default zoom control, unmodified (`zoomAnimation`/`fadeAnimation` never overridden).
- **Actual animation**: vendor CSS, `fanstatic/vendor/leaflet-1.7.1/leaflet.css:186-193`:
  ```css
  .leaflet-zoom-anim .leaflet-zoom-animated {
      transition: transform 0.25s cubic-bezier(0,0,0.25,1);
  }
  ```
- **Reading**: **0.25s, `cubic-bezier(0,0,0.25,1)`** vs. spec's 300ms ease-out — close in shape (both are
  "ease-out-like" curves) but not identical, and it's a `transform` animation, not the spec's "dissolve."
  Changing this means overriding a third-party library's default, not editing HDX code — flagged for
  awareness only, no recommendation offered since it's out of scope.

### 1.3 Signals carousel

- **Files**: `fanstatic/v2/signals-carousel.js` (thin config, 8 lines) + shared engine
  `fanstatic/v2/carousel.js` (204 lines, `window.hdxCarousel.init()`) + LESS
  `hdx-styles/src/common/less/v2/components/signal-card.less`.
- **Config actually wired** (`signals-carousel.js:2-7`):
  ```js
  window.hdxCarousel.init({
      containerSelector: '.hdx-v2-signals-cards',
      slideSelector:     '.hdx-v2-signal-slide',
      dotsSelector:      '.hdx-v2-signals-dots',
      mediaQuery:        '(min-width: 80rem)',
  });
  ```
  No `prevBtnSelector`/`nextBtnSelector` is passed, and no arrow markup exists in `signal-card.less` or
  either consuming template. Confirmed against `054-signals-landing-page.md` §5, which states this
  explicitly: *"dots only — no arrows"* — a deliberate decision made when this carousel was built, not an
  oversight. **The premise that this carousel has arrow navigation does not hold today.**
- **Shared engine mechanism** (`carousel.js`, applies to both this and 1.4): CSS `transition` on the
  `left` property (a position offset, not `transform`/`opacity`), set via inline style, plus Hammer.js for
  touch swipe. Infinite loop via DOM-cloning + silent position "teleport" on landing on a clone.
  ```js
  inner.style.transition = 'left 350ms';                 // carousel.js:92, 141, 173
  window.setTimeout(settle, 400);                         // carousel.js:183 — fallback if transitionend doesn't fire
  ```
- **Values found**: duration **350ms**, **no easing keyword specified** anywhere (resolves to the CSS
  default `ease`, not `ease-out`). Arrow-click and swipe would drive the identical `goTo()` path if arrows
  existed — but they don't for this carousel.

### 1.4 Mobile nav — "profile" second-level slide-in

- **Files**: `templates/v2/header.html:282-408` (markup), `hdx-styles/src/common/less/v2/navbar.less:481-727`
  (styles, comment: "Offcanvas panel — task 019"), `fanstatic/v2/navbar.js:173-196` (behavior).
- **JS handler** (`navbar.js:173-183`) — a pure `hidden`-attribute swap, nothing else:
  ```js
  var levelTrigger = e.target.closest('[data-hdx-v2-offcanvas-level]');
  if (levelTrigger) {
      ...
      if (primary) primary.hidden = true;
      if (levelEl) levelEl.hidden = false;
      return;
  }
  ```
- **CSS for the second level** (`navbar.less:676-687`):
  ```less
  &__level {
      position: absolute;
      inset:    0;
      background: var(--hdx-brand-85);
      ...
      &[hidden] { display: none; }
  }
  ```
  **No `transform`, no `transition` property exists on this block at all.** Confirmed directly against the
  file — there is nothing for CSS to animate even if the `hidden` swap were changed to a class toggle.
- **The outer offcanvas sheet** (level 1, the whole mobile-nav sheet) does have a transform, but it is
  **not a right-margin slide** — it drops from the top — and its transition is **commented out in the
  shipped LESS** (`navbar.less:485-497`):
  ```less
  .hdx-v2-offcanvas {
      transform:  translateY(-110%);
      visibility: hidden;
      //transition: transform 0.25s ease, visibility 0.25s;
      &.is-open { transform: translateY(0); visibility: visible; }
  }
  ```
- **Reading**: this is the single biggest gap in the audit. Today, opening the "profile" second level is
  **fully instant** — no transition, no transform, nothing to tune. Even the parent sheet's own
  (different-direction, top-drop) slide is presently dead code. There is no existing "slide in from the
  right margin" mechanism anywhere in this component to compare against a spring curve.

### 1.5 Highlights carousel

- **Files**: `fanstatic/v2/highlights-carousel.js` (config) + the same shared `carousel.js` engine as 1.3 +
  `hdx-styles/src/common/less/v2/pages/home.less:157-256`.
- **Config** (`highlights-carousel.js:2-9`) — this carousel *does* wire arrow buttons:
  ```js
  window.hdxCarousel.init({
      containerSelector: '.mobile-carousel',
      slideSelector:     '.highlight-slide',
      prevBtnSelector:   '.hdx-v2-highlights__arrow--prev',
      nextBtnSelector:   '.hdx-v2-highlights__arrow--next',
      mediaQuery:        '(min-width: 80rem)',
      dotsSelector:      '.highlight-dots',
  });
  ```
- **Values found**: identical engine to 1.3 — **350ms**, no easing keyword (default `ease`). Arrow click
  and swipe drive the same `goTo()` path.
- **Since 054's refactor, signals and highlights share one carousel engine** — there is no duplicated,
  divergently-tuned carousel code. The only difference between the two is configuration (arrows wired vs.
  not), not mechanism. A timing/easing fix to `carousel.js` affects both simultaneously.

### 1.6 Location map — hover tooltip

- **Files**: `fanstatic/browse_/browse.js` (event wiring), `hdx-styles/src/common/less/browse_/browse.less:193-196`
  (fill transition), vendor `fanstatic/vendor/leaflet-1.7.1/leaflet.css` (popup fade).
- **Wiring** (`browse.js:134-140`) — listens on `mousemove` (not `mouseover`), opens a real Leaflet
  `L.Popup`:
  ```js
  layer.on({ mousemove: highlightFeature, mouseout: resetFeature, click: featureClicked });
  ```
- **Two separate animated effects are present, confirmed directly**:
  - Country fill-color change (HDX-authored, `browse.less:194-195`):
    ```css
    path { transition: fill 200ms; }
    ```
  - Popup fade-in (vendor Leaflet, `leaflet.css:172-177`):
    ```css
    .leaflet-fade-anim .leaflet-popup { opacity: 0; transition: opacity 0.2s linear; }
    ```
- **Reading**: spec says **instant**; the actual behavior runs two roughly-200ms animations (one HDX,
  one vendor) rather than snapping immediately.

### 1.7 Anchor links (site-wide, incl. the data-grid drawer's own anchor nav)

- **Shared component**: `fanstatic/v2/components/anchor-links.js` — header comment states the intended
  behavior directly: *"Smooth scroll on anchor-link click (500ms, cubic-bezier(0.6, 0, 0.3, 1))"*.
  ```js
  var ease = cubicBezier(0.6, 0, 0.3, 1);                       // anchor-links.js:52
  function smoothScrollTo(target, container, extraOffset) {
      ...
      var duration = 500;                                       // anchor-links.js:77
      function step(timestamp) {
          var pos = start + distance * ease(progress);
          ...
      }
      requestAnimationFrame(step);
  }
  ```
  **Mechanism**: a custom `requestAnimationFrame` loop — not native `scroll-behavior: smooth` — so
  duration and easing are fully explicit and match the spec exactly: **500ms, `cubic-bezier(0.6,0,0.3,1)`**.
  Exposed globally as `window.hdxSmoothScrollTo` for reuse.
- **Consumers, all going through the same function**: dataset page (`hdx_read.html`), resource page
  (`resource_read.html`), Signals/HAPI landing pages, and the location data-grid drawer's own mobile
  anchor nav (`location-datagrid-drawer.html`). The locations-list page's own sidebar anchors
  (`pages/locations-list.js:8-22`) explicitly delegate to `window.hdxSmoothScrollTo` rather than
  reimplementing anything.
- **Hash-on-load correction** (site-wide, not Signals-specific): `initHashOnLoadCorrection` re-runs
  `smoothScrollTo` on `window.load` when the page was loaded with a `location.hash` matching an element,
  correcting scroll drift from content (e.g. images) that finishes loading after the browser's native
  fragment-scroll already fired. Exposed as `window.hdxScrollToHashTarget`.
- **"Access via API" rescroll**: `fanstatic/v2/pages/resource.js:20-23`, fired on the Data Explorer iframe's
  `load` event and again after the AJAX-built data-dictionary table renders:
  ```js
  function scrollToApiAccessIfActive() {
      if (location.hash !== '#api-access') return;
      setTimeout(window.hdxScrollToHashTarget, 100);
  }
  ```
  Goes through the shared component via `window.hdxScrollToHashTarget` (`anchor-links.js`), which looks up
  `location.hash`'s target and calls `smoothScrollTo` on it — same 500ms/bezier function as every other
  anchor-link scroll. It's a different trigger (programmatic post-load reposition, not a click) than the
  spec's "on click" anchor-link case, but no longer a divergent implementation.

### 1.8 Data-grid "legend" drawer

- Note on naming: the button that opens this overlay is labelled **"Definitions"** in the live template
  (`templates/v2/location-datagrid-drawer.html`, triggered from `templates/country/country.html:280`,
  `onclick="hdxV2Drawer('location-datagrid-drawer').open()"`), not "Legend." Flagged as a naming
  observation only — it does not affect the animation audit.
- **Component**: the generic, app-wide `c-drawer` component —
  `templates/v2/components/drawer.html` / `fanstatic/v2/components/drawer.js` /
  `hdx-styles/src/common/less/v2/components/drawer.less`.
- **Open/close JS** (`drawer.js:15-34`) is a class toggle only, no manual animation code:
  ```js
  $drawer.addClass('is-open').attr('aria-hidden', 'false');   // open()
  $drawer.removeClass('is-open').attr('aria-hidden', 'true'); // close()
  ```
- **CSS** (`drawer.less:26-52`), confirmed directly:
  ```less
  &__overlay { background: var(--hdx-overlay-black-25); }
  &__container {
      transform: translateX(100%);
      transition: transform 0.3s ease-out;
      .c-drawer.is-open & { transform: translateX(0); }
  }
  ```
  `--hdx-overlay-black-25` resolves (`overlays.less:29`) to `rgba(0, 0, 0, 0.25)`.
- **Values found**: slide **0.3s (300ms), `ease-out`** — exact match to spec. Backdrop **black at 25%
  opacity**, via a design token rather than an inline literal — exact match to spec.
- **Reuse note**: this exact mechanism (same duration/easing/backdrop) is shared by every other drawer in
  the app (notification subscribe/unsubscribe, org member-removal/leave-org confirmation, group-message) —
  it is not bespoke to this page.

### 1.9 Data-grid legend anchor links

- The drawer's own "jump to" anchor nav (`location-datagrid-drawer.html`) renders the same
  `v2/components/anchor-links.html` snippet and loads the same `anchor-links.js` module as §1.7 — same
  500ms/`cubic-bezier(0.6,0,0.3,1)` mechanism, exact match to spec.

---

## 2. Comparison — spec vs. current, at a glance

| Item | Spec | Current | Verdict |
|---|---|---|---|
| Homepage bar chart | Dissolve (fade out, no fade in) · linear · 300ms · 2500ms cycle | Bar: symmetric `background-color` cross-fade · Label: asymmetric `opacity` fade-out/instant-show · **linear** · **300ms** · **2500ms** | Exact match after revision |
| Map zoom *(out of scope)* | Dissolve · ease-out · 300ms | Vendor Leaflet `transform` · `cubic-bezier(0,0,0.25,1)` · 0.25s | Close, not exact; vendor default |
| Signals carousel | Smart Animate · ease-out · 300ms, arrow-triggered | Shared engine · default `ease` · 350ms — **no arrow buttons exist** | Mismatch on timing/easing; premise (arrows) doesn't hold |
| Mobile nav "profile" slide-in | Smart Animate · custom spring (4/1/0.01) · from right margin | **Instant `hidden` swap, no transition/transform at either level** | Full gap |
| Highlights carousel | Smart Animate · ease-out · 300ms, arrow-triggered | Shared engine · default `ease` · 350ms; arrows do exist | Timing/easing mismatch only |
| Map hover tooltip | Instant | Two ~200ms animations (HDX fill + vendor popup fade) | Not instant |
| Anchor links (site-wide + drawer) | Smart Animate · custom bezier(0.6,0,0.3,1) · 500ms | Custom rAF loop · **bezier(0.6,0,0.3,1)** · **500ms** | Exact match (one unrelated call site diverges, §1.7) |
| Data-grid drawer ("Definitions") | Move in · ease-out · 300ms · backdrop #000 @25% | `translateX` · **ease-out** · **0.3s** · **`--hdx-overlay-black-25`** | Exact match |
| Data-grid anchor links | Same as anchor links | Same shared component as above | Exact match |

---

## 3. Cross-cutting finding: no motion tokens exist

A full-repo grep for `--hdx-duration-*`, `--hdx-ease-*`, `--hdx-transition-*`, `--hdx-motion-*` returns
**zero results**. `.claude/skills/hdx-v2-styles/references/tokens.md` has no motion section at all (only
Colors, Overlays, Spacing, Typography, Radius, Elevation, Breakpoints, Layout mixins). Every component
above hardcodes its own literal. Cataloguing what exists today, for standardization reference:

| Value | Where (sample) |
|---|---|
| `0.15s ease` (most common, ~25 occurrences) | Buttons, dropdown, input-field, checkbox, selection, card components, text-link, anchor-links (hover states), nav-item |
| `0.2s ease` | Accordion, top-bar, dataset/search sections |
| `0.3s ease-out` | `drawer.less` (the one component matching spec exactly) |
| `300ms linear` | `bar-chart.less` |
| `350ms` (no easing → default `ease`) | Shared `carousel.js` engine |
| `500ms`, `cubic-bezier(0.6, 0, 0.3, 1)` | `anchor-links.js` (JS constant, not a CSS token) |
| `200ms` / `0.2s` (no easing → default `ease`) | Map country-fill hover, vendor Leaflet popup fade |
| `0.25s cubic-bezier(0,0,0.25,1)` | Vendor Leaflet zoom |

`0.15s ease` is the de-facto (undeclared) standard for small hover/focus states elsewhere in the app;
none of it is tokenized.

---

## 4. Reduced-motion — temporarily disabled for this audit

All 6 HDX-authored occurrences have been commented out (not deleted) so testing reflects true animation
behavior regardless of the tester's own OS/browser setting. Vendor code (Bootstrap, Leaflet, FontAwesome,
MapLibre) is untouched.

| File | What was commented out |
|---|---|
| `hdx-styles/src/common/less/v2/foundation.less` | Global `*` kill-switch (`animation-duration`/`transition-duration: 0.01ms !important`, etc.) |
| `hdx-styles/src/common/less/v2/bar-chart.less` | The two `@media (prefers-reduced-motion: reduce) { transition: none; }` blocks |
| `fanstatic/v2/charts.js` | `reducedMotion()` body — hardcoded to `return false` |
| `fanstatic/v2/components/anchor-links.js` | The `matchMedia` guard that made anchor-link scroll jump instantly |

**This is a real accessibility regression while active** (it re-opens WCAG violations V-10/V-15, closed
under task 041) and must be resolved before anything ships. It is not a finding of the audit itself —
purely a testing-visibility fix requested separately. Per §6, the resolution is not a verbatim restore of
this kill-switch — reduced-motion handling moves into per-component motion mixins instead.

---

## 5. Options Considered (per gap)

- **Homepage bar chart** — revisited after this audit's original pass, at the user's request, against a
  fresh Figma-sourced spec (2500ms cycle; asymmetric dissolve — fade out only, no fade in). Two structural
  options were considered for the label, which was the actual source of the "Pong"/swerving read (it had
  no fade at all — only a `transform`/`top` slide between one shared element's positions): (a) restructure
  so every bar-group renders its own statically CSS-anchored label, with JS reduced to a class toggle —
  no position math, no ghost elements needed for the fade-out-while-new-appears overlap; (b) minimal patch
  keeping the single shared, JS-positioned label, snapping its position instantly and layering in a
  JS-timed opacity sequence around the reposition. (a) was chosen.
- **Signals carousel** — (a) leave arrow-less (matches the deliberate task-054 decision) and treat the
  spec's arrow-trigger note as not applicable to this carousel; (b) add arrow buttons to match the spec's
  stated trigger, mirroring highlights' markup/config. Independently of (a)/(b): the shared engine's
  **350ms/default-ease** could be changed to **300ms/ease-out** to match spec — this affects highlights too
  since they share one engine (see next item).
- **Mobile nav "profile" slide-in** — this is the only item needing net-new work, not a timing tweak:
  (a) implement a `translateX` slide-in from the right on the second-level panel with a plain CSS
  `ease-out`/cubic-bezier transition (loses the literal spring feel but stays consistent with the drawer's
  existing 0.3s ease-out pattern); (b) approximate the spring visually with an overshoot cubic-bezier (e.g.
  something like `cubic-bezier(0.34, 1.56, 0.64, 1)`) — CSS transitions cannot express stiffness/damping/mass
  directly, only a fixed-shape curve; (c) implement true spring physics via a custom rAF loop (the same
  pattern `anchor-links.js` already uses for its bezier easing could be extended with a spring-integration
  function) to closely replicate the given stiffness 4 / damping 1 / mass 0.01 parameters. Separately: the
  outer offcanvas sheet's own commented-out top-drop transition is dead code today — whether to reactivate
  it (as a top-drop) or reconsider it as part of this same fix is an open question, not assumed either way.
- **Highlights carousel** — same shared-engine question as signals: change `carousel.js`'s 350ms/default
  to 300ms/ease-out (fixes both carousels at once since they share one engine), or leave as-is.
- **Map hover tooltip** — (a) force it truly instant per spec by setting `transition: none` on both the
  HDX fill rule and (via a Leaflet option/CSS override) the vendor popup fade; (b) keep the current ~200ms
  animations, reading the spec's "instant" as describing response latency (no delay before the tooltip
  starts appearing) rather than a literal zero-duration transition.
- **Anchor links** — (a) leave `resource.js`'s divergent `#api-access` rescroll as-is, since it's a
  different trigger (programmatic post-load reposition, not a user-clicked anchor link) than what the spec
  describes; (b) route it through the shared `window.hdxSmoothScrollTo` for full consistency across every
  scroll-animation call site in the app.
- **Data-grid drawer** — no gap found; no options needed. (Naming-only aside: rename the "Definitions"
  button/heading to "Legend" if that's the intended user-facing term, unrelated to animation.)
- **Motion tokens (cross-cutting)** — (a) introduce a small `--hdx-duration-*`/`--hdx-ease-*` token set
  (e.g. matching the spec's own recurring values: 300ms/ease-out, 500ms/custom-bezier) and migrate the
  components this audit touches onto it; (b) fix each component's literal values in place without adding a
  token layer, consistent with how the other ~20+ hardcoded `0.15s ease` instances already work elsewhere
  in the codebase; (c) middle ground — tokenize only the plain-CSS `transition:` declarations (bar chart,
  drawer, mobile nav, map fill) and leave the two JS-driven curves (carousel duration, anchor-links bezier)
  as named JS constants rather than round-tripping them through CSS custom properties.

---

## 6. Decisions

- **Homepage bar chart**: restructured so every bar-group renders its own statically CSS-anchored label
  (no more shared/JS-positioned label element). The bar's `background-color` cross-fade stays symmetric
  and unchanged; the label now uses an asymmetric `opacity` fade — 300ms linear on fade-out, instant
  (`transition: none`) on show — matching the fresh spec's "dissolve: fade out, no fade in" literally.
  Cycle interval updated to 2500ms.
- **Signals carousel**: add arrow buttons, mirroring highlights' markup/config. This reverses the task-054
  "dots only" decision, per the spec's arrow-trigger note.
- **Shared carousel engine** (`carousel.js`): change from 350ms/default-ease to **300ms/ease-out**. This
  updates both the signals and highlights carousels at once, since they share one engine.
- **Mobile nav "profile" slide-in**: implement a plain CSS `ease-out` transition (`translateX` slide-in
  from the right), consistent with the drawer's existing 0.3s ease-out pattern — not a literal spring.
  Additionally, reactivate the outer offcanvas sheet's commented-out top-drop transition as part of this
  same fix.
- **Highlights carousel**: covered by the shared-engine decision above (300ms/ease-out).
- **Map hover tooltip**: force it truly instant — set `transition: none` on both the HDX country-fill rule
  and the vendor Leaflet popup fade, as a bundle-order CSS override in `less/v2/pages/locations-list.less`
  rather than editing the v1-authored `browse_/browse.less` directly.
- **Anchor links**: route `resource.js`'s "Access via API" rescroll through the shared
  `window.hdxScrollToHashTarget` helper (which itself calls `window.hdxSmoothScrollTo`), for full
  consistency across every scroll-animation call site.
- **Data-grid drawer**: no gap found; no change needed.
- **Motion tokens (cross-cutting)**: introduce a `--hdx-duration-*`/`--hdx-ease-*` token set (new
  `motion.less`) and migrate the components touched by this audit onto it.
- **Reduced-motion**: do not restore the old global `foundation.less` `*` kill-switch verbatim. Replace it
  with a per-component `.hdx-motion()` mixin (`mixins.less`) plus a shared `window.hdxV2.prefersReducedMotion()`
  helper (`utils.js`), and migrate every HDX-authored transition sitewide onto them (widened from the 6 named
  components to all `less/v2/**` transitions during implementation, so nothing loses coverage when the global
  switch is removed). Both currently ship **commented out or returning false** — inert — at the task owner's
  request; restoring real `prefers-reduced-motion` behavior is a one-line uncomment in each file, left as a
  follow-up rather than completed in this pass.
