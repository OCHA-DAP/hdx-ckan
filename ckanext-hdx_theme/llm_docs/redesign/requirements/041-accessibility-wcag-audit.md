# 041 – Accessibility Audit (WCAG 2.1 AA) for v2

**Status**: requirement

**Standard**: WCAG 2.1 Level AA
**Browsers**: Chrome/Edge (Chromium), Firefox, Safari
**Screen readers**: NVDA + Chrome (Windows primary), VoiceOver + Safari (macOS), JAWS + Chrome/Edge (enterprise), TalkBack + Android Chrome (mobile)
**Refactoring scope**: Full structural changes allowed

---

## 1. Discovery Summary

### What was audited

The complete v2 implementation surface area across all pages, layout templates, reusable components, JS behaviors, and design tokens.

#### Pages (5)

| Template | Description |
|----------|-------------|
| `templates/home/index.html` | Homepage — hero, search bar |
| `templates/search/search.html` | Dataset search with filter sidebar/overlay |
| `templates/package/hdx_read.html` | Dataset detail page |
| `templates/package/resource_read.html` | Resource detail page |
| `templates/v2/components.html` | Component showcase (internal) |

#### Layout templates (7)

| Template | Description |
|----------|-------------|
| `templates/v2/page.html` | Base layout for all v2 pages |
| `templates/v2/header.html` | Site header + mobile navigation drawer (offcanvas markup inline) |
| `templates/v2/footer.html` | Site footer |
| `templates/v2/navbar-notifications.html` | Notifications dropdown panel |
| `templates/v2/navbar-user-menu.html` | User account dropdown panel |
| `templates/v2/components/page-header.html` | Dataset/resource page hero header |
| `templates/v2/search-filters.html` | Filter sidebar and mobile overlay |
| `templates/v2/search-nav-controls.html` | Sort and view controls for search results |

#### Components (41, under `templates/v2/components/`)

`accordion` · `activity-card` · `activity-item` · `anchor-links` · `autocomplete` · `avatar` · `breadcrumb` · `button` · `checkbox` · `content-card` · `copy-button` · `dataset-card` · `drawer` · `dropdown` · `dropdown-panel` · `file-type-icon` · `graph-point` · `highlight-card` · `info-icon` · `kpi-card` · `label` · `letter-anchor` · `list-item` · `nav-item` · `notification-item` · `org-list-card` · `page-header` · `pagination` · `radio` · `resource-card` · `search-input` · `selection-item` · `showcase-card` · `signal-card` · `signup-tier` · `step-pager` · `table` · `text-button` · `text-link` · `toggle` · `tooltip`

#### Data-transform snippets (2)

| Template | Used on |
|----------|---------|
| `templates/search/snippets/package_item_v2.html` | Search results list |
| `templates/package/snippets/resource_item_v2.html` | Dataset detail resources section |

#### JavaScript (9 files)

| File | Bundle | Pages |
|------|--------|-------|
| `fanstatic/v2/components/dropdown.js` | v2-components-scripts | All v2 pages |
| `fanstatic/v2/components/copy-button.js` | v2-components-scripts | Resource page |
| `fanstatic/v2/components/input-field.js` | v2-components-scripts | Auth pages |
| `fanstatic/v2/components/anchor-links.js` | v2-components-scripts | Dataset, resource pages |
| `fanstatic/v2/components/clamped-text.js` | v2-components-scripts | Search, dataset pages |
| `fanstatic/v2/components/page-header.js` | v2-components-scripts | Dataset, resource pages |
| `fanstatic/v2/navbar.js` | v2-page-scripts | All v2 pages |
| `fanstatic/v2/pages/search.js` | v2-search-scripts | Search page |
| `fanstatic/v2/pages/dataset.js` | v2-dataset-scripts | Dataset page |

#### Icons

60+ SVG icon files under `templates/v2/icons/`.

### What was excluded

- v1 templates and code paths (non-v2 branches)
- Legacy JS bundles loaded on all pages (`ckan` bundle, `page-scripts`) — they share the page but are outside the v2 redesign scope
- CKAN core admin pages

---

## 2. Audit Findings (WCAG 2.1 AA)

Severity: **critical** / **major** / **minor**

---

### 2.1 Semantics & Structure

**Heading hierarchy** — AUDIT TARGET
Heading order across all five pages must be verified. The page-header component renders the dataset/resource title as `<h1>`. Subsequent section headings must follow a strict h2 → h3 hierarchy without skipping levels. This cannot be confirmed without rendering the full page tree.
*WCAG 1.3.1 Info and Relationships*

**SVG icons — MAJOR**
60+ SVG icons are included inline throughout v2 templates. Decorative icons (appearing beside text labels, inside labeled buttons) must carry `aria-hidden="true"` to prevent screen readers from reading out meaningless path data. Informative icons used as the sole accessible name of an action (icon-only buttons) require an accessible name via `<title>` inside the SVG or `aria-label` on the parent `<button>`.
Applies to all uses of icons from `templates/v2/icons/`.
*WCAG 1.1.1 Non-text Content*

**Form label association** — AUDIT TARGET
`checkbox.html` and `radio.html` components use visible `<label>` wrappers. Verify that rendered `<input>` elements have unique `id` attributes and that the `<label>` carries a matching `for` attribute in all page contexts (filter sidebar, search, auth pages). Programmatic association must not be assumed from visual proximity alone.
*WCAG 1.3.1 Info and Relationships*

**Language attribute** — AUDIT TARGET
Verify `<html lang="en">` (or appropriate locale) is set in `v2/page.html`. Without it, screen readers may apply incorrect pronunciation rules to all text.
*WCAG 3.1.1 Language of Page*

---

### 2.2 Keyboard Accessibility

**`dropdown.js` — CRITICAL**
The dropdown trigger opens and closes on `click` only. There is no `keydown` handler for `Enter` or `Space`. There is no arrow-key navigation within the open list. Affects every dropdown in v2: filter dropdowns (search page), sort dropdown (search nav controls), navigation dropdowns (navbar).
*WCAG 2.1.1 Keyboard*

**`copy-button.js` — MAJOR**
The copy trigger is bound to `click` only. If the rendered element is not a native `<button>`, keyboard users cannot activate it. Even if it is a `<button>`, verify the component template to confirm.
*WCAG 2.1.1 Keyboard*

**`clamped-text.js` — MAJOR**
The "Show more / Show less" toggle is bound to `click` on `.c-text-button`. No `keydown` handler for `Enter`/`Space` is present. Whether this is keyboard-accessible depends entirely on whether `.c-text-button` renders as a native `<button>`. Verify the template.
*WCAG 2.1.1 Keyboard*

**`page-header.js` tooltips — MAJOR**
Info icon tooltips are triggered by `click` only. There is no keyboard open (Enter/Space on the icon), no keyboard close (Escape), and no hover fallback. The tooltip content is also unreachable by keyboard navigation.
*WCAG 2.1.1 Keyboard*

**`input-field.js` password toggle — MINOR**
Password visibility toggle is `click`-bound. Same concern as above: verify it renders as `<button>`. The `aria-label` update ("Show/Hide password") is already implemented ✓.
*WCAG 2.1.1 Keyboard*

---

### 2.3 Focus Management

**`navbar.js` offcanvas — no focus trap — CRITICAL**
When the mobile offcanvas menu opens, focus is not trapped inside it. A keyboard user can Tab past the end of the offcanvas and interact with content behind the overlay. Focus is also not returned to the hamburger trigger when the menu closes.
*WCAG 2.1.2 No Keyboard Trap (inverse violation); best practice per ARIA Authoring Practices Guide*

**No skip navigation link — CRITICAL**
`v2/page.html` and `v2/header.html` contain no skip-to-main-content link. Every keyboard user must Tab through the full navbar (logo, top-bar, main nav items, search, user actions) before reaching page content on every page load.
*WCAG 2.4.1 Bypass Blocks*

**`dropdown.js` — no focus trap, no focus return — MAJOR**
When a dropdown opens, focus is not moved into it. When it closes (click-outside or button re-click), focus is not returned to the trigger. A keyboard user has no way to know the dropdown state has changed.
*WCAG 2.4.3 Focus Order*

**`search.js` filter overlay — GOOD (reference pattern)**
The filter overlay correctly moves focus to the first focusable element on open and restores focus to the filter button on close. This is the correct pattern to replicate in `dropdown.js` and `navbar.js`.

---

### 2.4 Color & Contrast

**Brand green `#269777` as text — MAJOR**
The brand-5 color `#269777` has a contrast ratio of approximately **3.37:1** against white (`#ffffff`). This fails WCAG AA for normal-size text (minimum 4.5:1) and passes only for large text (≥ 18px regular / ≥ 14px bold, minimum 3:1).
Audit all uses of `var(--hdx-brand-5)` in text contexts: labels, badges (`c-label`), success states, "up-to-date" indicators in dataset and resource cards.
*WCAG 1.4.3 Contrast (Minimum)*

**Primary blue `#1862d8` on white — PASS**
Contrast ratio ≈ **5.15:1**. Passes AA for normal text. Used for links, focus indicators, CTAs.

**Focus indicator — PASS**
The established focus style (`outline: 2px solid var(--hdx-primary-5); outline-offset: 2px`) applied to buttons, checkboxes, dropdowns, and text-links passes WCAG 2.1 AA focus visibility requirements.

**Interactive state colors — AUDIT TARGET**
Hover and active color shifts for button-secondary, text-link-tertiary, and selection-item must each meet 3:1 against adjacent colors as UI component boundaries.
*WCAG 1.4.11 Non-text Contrast*

**Placeholder and disabled text — AUDIT TARGET**
Neutral grey values used for placeholder text in input fields and for disabled state text must be verified to meet 4.5:1 against the field background (or confirmed as intentionally excluded per WCAG exception for placeholder text).
*WCAG 1.4.3 Contrast (Minimum)*

---

### 2.5 ARIA Usage

**`page-header.js` tooltips — no ARIA — CRITICAL**
Tooltip elements rendered by `page-header.js` have no ARIA attributes. The tooltip content has no `role="tooltip"` and no `id`. The trigger has no `aria-describedby`. The tooltip is completely invisible to screen readers — users receive no indication that additional information is available.
*WCAG 1.3.1 Info and Relationships; 4.1.2 Name, Role, Value*

**`copy-button.js` — no status announcement — MAJOR**
When copy succeeds, the `.is-copied` class is added for visual feedback only. There is no `aria-live` region or `role="status"` element to announce the success state to screen readers.
*WCAG 4.1.3 Status Messages*

**`dropdown.js` — missing panel role — MAJOR**
Trigger correctly sets `aria-expanded` ✓. However, the dropdown panel has no `role` (`listbox`, `menu`, or `dialog` depending on context) and items have no corresponding child roles (`option`, `menuitem`). Without these, screen readers cannot communicate the composite widget structure.
Verify also that the trigger is a `<button>` element; if it is a `<div>`, add `role="button"` and `tabindex="0"`.
*WCAG 4.1.2 Name, Role, Value*

**`navbar.js` — GOOD (reference pattern)**
`aria-expanded`, `aria-hidden`, `aria-controls`, `aria-label` / `aria-label-close` are all correctly implemented. This is the reference pattern for ARIA on interactive panels.

**`anchor-links.js` — GOOD**
`aria-expanded` on the mobile toggle ✓. `aria-current` set/removed on the active link ✓.

**`dataset.js` collapsible sections — GOOD**
`aria-expanded` updated on section headers ✓. `keydown` handler for Enter/Space ✓.

**`clamped-text.js` — GOOD (partial)**
`aria-expanded` ✓. Verify the visible label ("Show more" / "Show less") is sufficient as an accessible name in context, or add `aria-label` that includes the dataset title (e.g., "Show more — [Dataset title]").

---

### 2.6 Interactive Elements

**Icon-only buttons — AUDIT TARGET**
Any button whose only visible content is an icon (e.g., close button in offcanvas, hamburger, copy icon) must have an accessible name. Verify `aria-label` is present on all such buttons in `header.html`, `page-header.html`, and `copy-button.html`.
*WCAG 4.1.2 Name, Role, Value*

**Touch target size — AUDIT TARGET**
Interactive elements on mobile (SM breakpoint, < 768px) must meet a minimum touch target of 44×44px. Verify all buttons, links, checkboxes, and form controls in `search-filters.html`, `header.html`, and `resource-card.html`.
*WCAG 2.5.5 Target Size (AAA, but 44px is the practical AA-compatible baseline)*

**`hdx_clickable_div.js` (legacy) — AUDIT TARGET**
This legacy JS module makes `<div>` elements clickable with no keyboard equivalent. Verify whether it is invoked anywhere within v2 templates. If so, treat as a keyboard accessibility violation.
*WCAG 2.1.1 Keyboard*

---

### 2.7 Responsive & Zoom

**Content reflow at 400% zoom — AUDIT TARGET**
At 400% browser zoom the effective viewport is approximately 320px wide. Verify that all v2 pages reflow without horizontal scrolling. The v2 SM breakpoint at 48rem (768px) is designed for small screens, but zoom behavior must be tested independently.
*WCAG 1.4.10 Reflow*

**Text resize — LOW RISK**
All v2 typography uses `rem`-based font sizes via LESS tokens (no `px` font sizes in component styles). Text resize by user agent setting should not break layouts.

---

### 2.8 Motion & Animation

**`anchor-links.js` smooth scroll — MAJOR**
The 500ms custom `easeInOutCubic` scroll animation in `anchor-links.js` has no `prefers-reduced-motion` guard. For users with vestibular disorders, unexpected scrolling motion can cause nausea or disorientation.
*WCAG 2.3.3 Animation from Interactions*

**CSS transitions (0.15s) — MINOR**
All hover/focus state transitions (`background-color`, `border-color`, `color`, `box-shadow` at `0.15s ease`) are not wrapped in `@media (prefers-reduced-motion: no-preference)`. The short duration reduces risk, but is technically non-compliant.
*WCAG 2.3.3 Animation from Interactions*

---

### 2.9 Content & Readability

**Format badges and abbreviations — AUDIT TARGET**
Resource format badges (e.g., "CSV", "XLSX", "JSON") are displayed as short-form labels. For screen readers these are read as individual letters. Verify whether `<abbr title="...">` or `aria-label` expansions are needed, or whether the abbreviated form is considered an industry standard that does not require expansion.
*WCAG 3.1.4 Abbreviations (AAA) — informational, not blocking*

**ARIA labels and i18n — AUDIT TARGET**
`aria-label` strings in v2 JS files (e.g., `aria-label="Open menu"` in `navbar.js`) are currently hardcoded English strings. Verify whether these pass through CKAN's i18n system (`_('...')`) or require explicit translation handling for non-English deployments.
*WCAG 3.1.1 Language of Page*

**"Show more / Show less" link purpose — MINOR**
In context these labels are sufficient when the truncated content is immediately adjacent. If these links ever appear in isolation (e.g., in a summary list), add `aria-label="Show more — [Dataset title]"` to provide unique accessible names.
*WCAG 2.4.6 Headings and Labels*

---

## 3. Violations

| # | Component / File | WCAG Criterion | Severity | Description |
|---|------------------|----------------|----------|-------------|
| V-01 | `v2/page.html` | 2.4.1 Bypass Blocks | CRITICAL | No skip-to-main-content link. Keyboard users must tab through the full navbar on every page. |
| V-02 | `navbar.js` offcanvas | 2.1.2 No Keyboard Trap | CRITICAL | Focus not trapped inside open offcanvas. Focus not returned to trigger on close. |
| V-03 | `page-header.js` tooltip | 1.3.1 Info and Relationships | CRITICAL | Tooltip has no `role="tooltip"`, no `id`, trigger has no `aria-describedby`. Invisible to screen readers. |
| V-04 | `dropdown.js` | 2.1.1 Keyboard | CRITICAL | Dropdown trigger is click-only. No Enter/Space activation. No arrow-key navigation within open list. |
| V-05 | `dropdown.js` | 4.1.2 Name, Role, Value | MAJOR | Dropdown panel has no `role`. Items have no child role. Widget structure unannounced to AT. |
| V-06 | `dropdown.js` | 2.4.3 Focus Order | MAJOR | No focus trap within open dropdown. No focus return to trigger on Escape or close. |
| V-07 | Brand green `#269777` | 1.4.3 Contrast (Minimum) | MAJOR | ~3.37:1 contrast — fails AA for normal-size text. |
| V-08 | `copy-button.js` | 4.1.3 Status Messages | MAJOR | Copy success state (`.is-copied`) is visual-only. No `aria-live` announcement. |
| V-09 | `copy-button.js` | 2.1.1 Keyboard | MAJOR | Trigger is click-only. Activation depends on element being a native `<button>`. |
| V-10 | `anchor-links.js` | 2.3.3 Animation from Interactions | MAJOR | 500ms smooth scroll has no `prefers-reduced-motion` guard. |
| V-11 | SVG icons | 1.1.1 Non-text Content | MAJOR | Decorative icons missing `aria-hidden="true"`. Informative icon-only buttons may lack accessible name. |
| V-12 | `clamped-text.js` | 2.1.1 Keyboard | MAJOR | Toggle is click-only. Keyboard access depends on element being a native `<button>`. |
| V-13 | `page-header.js` tooltip | 2.1.1 Keyboard | MAJOR | Tooltip has no keyboard trigger (Enter/Space) and no keyboard close (Escape). |
| V-14 | `input-field.js` password toggle | 2.1.1 Keyboard | MINOR | Toggle is click-only. Depends on element being a native `<button>`. |
| V-15 | CSS transitions | 2.3.3 Animation from Interactions | MINOR | 0.15s transitions not guarded by `prefers-reduced-motion`. |

---

## 4. Recommendations

All fixes follow the **reuse-first, minimal-disruption** principle. Existing correct patterns (navbar.js ARIA, search.js focus management) serve as the templates for all fixes.

---

### R-01 — Skip navigation link

Add as the **first element inside `<body>`** in `v2/page.html`:

```html
<a href="#hdx-v2-main" class="sr-only sr-only--focusable">Skip to main content</a>
```

Add `id="hdx-v2-main"` to the `<main>` element (or the equivalent main content wrapper) in `v2/page.html`.

Add `.sr-only` and `.sr-only--focusable` utility classes to `foundation.less` if not already present:

```less
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
.sr-only--focusable:focus {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    clip: auto;
    white-space: normal;
}
```

---

### R-02 — Focus trap utility (shared module)

Create `fanstatic/v2/components/focus-trap.js` — a single lightweight `FocusTrap` class consumed by both `navbar.js` (offcanvas) and `dropdown.js`.

Minimal interface:

```js
class FocusTrap {
    constructor(element, triggerElement) { ... }
    activate() { /* move focus to first focusable child, trap Tab/Shift+Tab */ }
    deactivate() { /* remove trap, return focus to triggerElement */ }
}
```

Reuse the selector list already implied by `search.js`: `'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'`.

---

### R-03 — `dropdown.js` — keyboard activation, focus, ARIA roles

**Keyboard activation**: Add `keydown` handler on `.c-dropdown__trigger` for `Enter` and `Space` to toggle the dropdown.

**Escape to close**: Add `keydown` handler on the document (while open) for `Escape` → close and return focus to trigger.

**Arrow-key navigation**: Add `ArrowDown` / `ArrowUp` handlers to move focus between items within the open panel.

**Focus return**: On close (any method), return focus to `.c-dropdown__trigger`.

**ARIA roles**: Determine the semantic role of each dropdown type:
- Navigation-style list → `role="menu"` on panel, `role="menuitem"` on items
- Value-selection list → `role="listbox"` on panel, `role="option"` on items

**Element type**: Verify `.c-dropdown__trigger` renders as `<button>`. If it is a `<div>`, update `dropdown.html` template to use `<button>`.

---

### R-04 — `navbar.js` offcanvas — focus trap and return

Apply the `FocusTrap` from R-02 to the offcanvas element.

- On `openOffcanvas()`: call `focusTrap.activate()`
- On `closeOffcanvas()`: call `focusTrap.deactivate()` to return focus to the hamburger trigger

The Escape key handler already present in `navbar.js` is sufficient for keyboard close ✓. Only focus management is missing.

---

### R-05 — Tooltip ARIA (page-header.js + `tooltip.html`)

**In `tooltip.html` component template:**

```html
<div id="{{ tooltip_id }}" role="tooltip" class="c-tooltip" hidden>
    {{ tooltip_content }}
</div>
```

**On the trigger element** (info icon):

```html
<button class="c-info-icon" aria-describedby="{{ tooltip_id }}" aria-expanded="false">
    ...
</button>
```

**In `page-header.js`**: add `aria-expanded` toggle on the trigger, and an `Escape` key handler to close the open tooltip and return focus to the trigger.

Unifying with the existing `tooltip.html` component ensures one pattern across all tooltip usages. The `bs_tooltip.js` Bootstrap pattern handles hover/keyboard natively but is Bootstrap-bound — prefer the v2 custom pattern for consistency.

---

### R-06 — `copy-button.js` — live region for status

Add a visually hidden `aria-live="polite"` region adjacent to the copy button (in `copy-button.html`):

```html
<span class="sr-only" aria-live="polite" data-copy-status></span>
```

In `copy-button.js`, on successful copy:

```js
statusEl.textContent = 'Copied to clipboard';
setTimeout(() => { statusEl.textContent = ''; }, 2000);
```

The empty reset prevents the message from being re-read on subsequent interactions.

---

### R-07 — `anchor-links.js` — prefers-reduced-motion

Wrap the smooth scroll in a motion preference check:

```js
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
element.scrollIntoView({
    behavior: prefersReducedMotion ? 'instant' : 'smooth',
    block: 'start'
});
```

---

### R-08 — Brand green text color

Audit all usages of `var(--hdx-brand-5)` (`#269777`) as text color across v2 components and templates.

For any use on normal-size text (< 18px regular / < 14px bold):
- Replace with a darker green step. Brand step 6 or 7 from `colors.less` must be verified to achieve ≥ 4.5:1 contrast against white; select the minimum step that passes.
- Alternatively, restrict brand-5 to large-text contexts only and document this constraint in `colors.less` inline comments.

---

### R-09 — SVG icons — aria-hidden and accessible names

**Decorative icons** (icon appears beside a visible text label, or inside a button that has an `aria-label`):

```html
<svg aria-hidden="true" focusable="false" ...>
```

`focusable="false"` prevents IE/Edge legacy focus on SVG elements.

**Informative icons** (icon-only button with no other accessible name):

```html
<button aria-label="Close menu">
    <svg aria-hidden="true" focusable="false" ...>
    </svg>
</button>
```

Apply consistently across all icon usages in v2 templates. The icon template files under `templates/v2/icons/` should be updated to accept an `aria_hidden` parameter defaulting to `"true"`.

---

### R-10 — CSS transitions — prefers-reduced-motion

Add a `prefers-reduced-motion` guard in `foundation.less` or as a LESS mixin. Apply to all component LESS files that define `transition:` declarations:

```less
@media (prefers-reduced-motion: no-preference) {
    transition: background-color 0.15s ease, border-color 0.15s ease,
                color 0.15s ease, box-shadow 0.15s ease;
}
```

Document this pattern in `CONVENTIONS.md` so all future tasks follow it.

---

## 5. Global Accessibility Constraints

These are **mandatory** for all future v2 tasks, all components, and all pages. They are non-negotiable additions to the existing v2 conventions.

---

### C-01 — Keyboard-first interactions

Every interactive element must be fully operable by keyboard alone. `click` handlers must be paired with `keydown` handlers for `Enter` and `Space`. No click-only interactions.

---

### C-02 — Semantic element for role

Use `<button>` for actions that do not navigate. Use `<a href>` for navigation. Never use `<div>` or `<span>` as an interactive target without adding:
- `role="button"` (or the appropriate role)
- `tabindex="0"`
- `keydown` handler for Enter and Space

---

### C-03 — ARIA for every dynamic state

Every state change that affects the user's understanding of the UI must update a corresponding ARIA attribute on the controlling element:

| State | Attribute |
|-------|-----------|
| Open / closed | `aria-expanded="true/false"` |
| Checked / unchecked | `aria-checked="true/false"` |
| Selected / unselected | `aria-selected="true/false"` |
| Hidden / visible (structural) | `aria-hidden="true/false"` |
| Current item in nav/list | `aria-current="true"` |

---

### C-04 — Focus trap in overlays

Any component that visually overlaps and blocks page content (offcanvas drawer, modal dialog, popover, full-screen overlay) must:
1. Move focus inside the overlay on open
2. Trap `Tab` / `Shift+Tab` within the overlay while open
3. Close on `Escape`
4. Return focus to the triggering element on close

Use the shared `FocusTrap` module from R-02.

---

### C-05 — Live regions for status messages

Any user action that produces a success, error, or loading state must announce the result via:
- `role="status"` or `aria-live="polite"` for non-urgent messages (copy, save, load)
- `role="alert"` or `aria-live="assertive"` for errors requiring immediate attention

Live region elements must be in the DOM before the message is injected.

---

### C-06 — Focus indicator — never suppress

All interactive elements must show the established focus style on `:focus-visible`:

```less
outline: 2px solid var(--hdx-primary-5);
outline-offset: 2px;
```

Never use `outline: none` without a visible replacement. This applies to every component regardless of design intent.

---

### C-07 — prefers-reduced-motion — all animations

All CSS transitions and JS-driven animations must be guarded:

- CSS: wrap `transition:` declarations in `@media (prefers-reduced-motion: no-preference)`
- JS: check `window.matchMedia('(prefers-reduced-motion: reduce)').matches` before starting any animation

---

### C-08 — Icon accessibility

| Icon context | Required |
|--------------|----------|
| Decorative (beside text label) | `aria-hidden="true"` on `<svg>` |
| Decorative (inside labeled button) | `aria-hidden="true"` on `<svg>` |
| Informative (icon-only button) | `aria-label` on `<button>`, `aria-hidden="true"` on `<svg>` |
| Informative (standalone SVG) | `<title>` inside `<svg>`, `role="img"`, `aria-labelledby` pointing to `<title>` id |

---

### C-09 — Skip navigation on every page

Every page that renders `v2/header.html` must include the skip-to-main-content link (R-01) as the first focusable element in the DOM.

---

### C-10 — Contrast minimums (AA)

| Content type | Minimum contrast |
|--------------|-----------------|
| Normal text (< 18px regular / < 14px bold) | 4.5:1 |
| Large text (≥ 18px regular / ≥ 14px bold) | 3:1 |
| UI boundaries (buttons, inputs, focus rings) | 3:1 against adjacent color |
| Placeholder / disabled text | WCAG exempts placeholder — but target 3:1 as good practice |

---

## 6. Refactor Needs

### RF-01 — Shared focus trap module

Create `fanstatic/v2/components/focus-trap.js` as a standalone class (see R-02). Import into `navbar.js` and `dropdown.js`. Prevents duplication of focus-trap logic across multiple files.

### RF-02 — `sr-only` utility in `foundation.less`

Add `.sr-only` and `.sr-only--focusable` to `foundation.less` (see R-01). These are fundamental accessibility utilities needed for skip links, live regions, and screen-reader-only text. They belong alongside other foundational styles.

### RF-03 — Tooltip unification

`page-header.js` implements its own click-tooltip pattern independently of the `tooltip.html` component. The v2 `tooltip.html` component exists but is not wired up in the page header context.

Unify to a single tooltip pattern: update `tooltip.html` with full ARIA support (R-05), and replace the custom `page-header.js` tooltip logic with a call to the shared component. This removes a second divergent tooltip implementation before it proliferates.

### RF-04 — `prefers-reduced-motion` convention in CONVENTIONS.md

Add a section to `llm_docs/redesign/CONVENTIONS.md` documenting the required pattern for transitions and JS animations (see R-07, R-10). Without a documented convention, each future task will independently decide whether to add the guard — leading to inconsistency.
