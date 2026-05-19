# 021 — v2 LESS/CSS Architecture Standardization

## Background

The v2 LESS system has a solid foundation: 105 CSS custom properties organized into
clean token files, consistent BEM naming, and good documentation. However, a code
audit identified recurring inconsistencies that reduce maintainability and make the
system harder to reason about. This document specifies what must be fixed without
breaking existing design or functionality.

See [CONVENTIONS.md](../CONVENTIONS.md) for general naming and token rules.

## Issues Fixed

### 1. Breakpoint Variables — Consolidate to Single Source

**Problem:** The same breakpoint values are defined independently in 5 files.
Two naming schemes coexist (`@hdx-bp-*` in rem and `@breakpoint-*` in px).

Files affected:
- `layout.less` — defines both `@hdx-bp-md/xl` (rem) AND `@breakpoint-md/xxl` (px)
- `navbar.less` — redefines `@hdx-bp-md`, `@hdx-bp-xl`
- `footer.less` — redefines `@hdx-bp-md`, `@hdx-bp-xl`
- `top-bar.less` — redefines `@hdx-bp-md`

**Requirements:**
- Define all breakpoint LESS variables **once only**, in `layout.less`
- Remove all local redefinitions from `navbar.less`, `footer.less`, `top-bar.less`
- Use a single naming scheme: `@hdx-bp-*` in `rem` units only
- Standardize to three named breakpoints:
  - `@hdx-bp-md: 48rem` (768px)
  - `@hdx-bp-xl: 80rem` (1280px)
  - `@hdx-bp-xxl: 87.5rem` (1400px) — currently only in `layout.less` as px
- Remove `@breakpoint-md` and `@breakpoint-xxl` from `layout.less`
- Any file that uses breakpoints must import or depend on `layout.less`

---

### 2. Hardcoded rgba Overlay Values — Tokenize

**Problem:** Dark-background sections (navbar, footer, top-bar) use hardcoded
`rgba(255, 255, 255, ...)` and `rgba(0, 0, 0, ...)` values for borders, hovers,
and overlays. These values repeat across files with no shared token.

Hardcoded values found:
- `rgba(255, 255, 255, 0.10)` — subtle white overlay (hover states on dark bg)
- `rgba(255, 255, 255, 0.15)` — light white overlay
- `rgba(255, 255, 255, 0.30)` — medium white border/divider
- `rgba(255, 255, 255, 0.90)` — near-opaque white text/icon
- `rgba(0, 0, 0, 0.40)` — dark scrim/overlay

**Requirements:**
- Add an `overlays.less` token file with LESS variables for these semantic values
- Export them as CSS custom properties in `foundation.less` (`:root` block)
- Replace all inline `rgba(...)` overlay values in `navbar.less`, `footer.less`,
  and `top-bar.less` with the corresponding token
- Suggested naming:
  - `--hdx-overlay-white-10`, `--hdx-overlay-white-15`, `--hdx-overlay-white-30`
  - `--hdx-overlay-white-90`, `--hdx-overlay-black-40`

---

### 3. Hardcoded Box Shadows — Use Existing Tokens

**Problem:** Shadow tokens exist in `elevation.less` and are exported as CSS custom
properties, but some files hardcode the same values directly.

Offending values:
- `navbar.less`: `0px 4px 10px rgba(0, 0, 0, 0.12)` — matches `--hdx-shadow-md`
- `top-bar.less`: `0 4px 16px rgba(0, 0, 0, 0.3)` — no matching token exists

**Requirements:**
- Replace `0px 4px 10px rgba(0, 0, 0, 0.12)` in `navbar.less` with `var(--hdx-shadow-md)`
- For `top-bar.less`: add a new named token (e.g. `--hdx-shadow-overlay`) in
  `elevation.less` and use it, or align with the closest existing token
- No shadow value should be hardcoded inline if an equivalent token exists

---

### 4. Hardcoded Hex Color — Replace with Token

**Problem:** `dropdown.less` uses a hardcoded hex color for a border value.

Offending value: `1px solid #ebeff0` — this corresponds to `--hdx-neutral-1`

**Requirements:**
- Replace `#ebeff0` with `var(--hdx-neutral-1)` in `dropdown.less`
- Audit all component files for remaining hardcoded hex colors and replace with
  CSS custom properties from the token system

---

### 5. Non-Standard Border Widths — Document or Standardize

**Problem:** Several components use sub-pixel or non-standard border widths that
are undocumented and inconsistent:
- `1.5px` — in `dropdown.less` (hover/active states) and `navbar.less`
- `0.75px` — in `input-field.less`

**Requirements:**
- If these are intentional design choices (e.g. sharper rendering on HiDPI), add a
  short inline comment explaining the reason
- If they are not intentional, replace with `1px`
- If they should become system tokens, add them to a borders token file
  (e.g. `@hdx-border-width-thick: 1.5px`) and export as `--hdx-border-width-thick`

---

### 6. Spacing Tokens 13–16 — Document Rationale

**Problem:** `spacing.less` includes 4 tokens that fall outside the standard 4px-base
grid, with no explanation of why they were added:
- `@hdx-space-13: 0.375rem` (6px) — on-grid ✓
- `@hdx-space-14: 0.625rem` (10px) — off-grid
- `@hdx-space-15: 0.125rem` (2px) — on-grid ✓
- `@hdx-space-16: 0.875rem` (14px) — off-grid

**Requirements:**
- Add a comment above tokens 14 and 16 referencing the Figma spec or component that
  requires the off-grid value
- If any of these tokens are unused, remove them
- Do not renumber the sequence (would break existing references)

---

## Out of Scope

- Component LESS variables (`@c-*`) remain LESS-only; they are not to be exported
  as CSS custom properties
- No visual or layout changes — refactoring must be purely structural
- No renaming of existing CSS custom properties (`--hdx-*`) or class names
- The compiled CSS output must be functionally identical before and after

---

