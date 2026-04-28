# Design V2 Implementation Progress

**Status**: In-progress
**Started**: 2026-04-16
**Last Updated**: 2026-04-28

---

## Overview

This document tracks the implementation of the HDX redesign (v2), a progressive migration from the legacy design system to a new BEM-component-based, fully responsive design sourced from Figma.

The migration strategy follows the plan outlined in [PLAN.md](PLAN.md): build the new design system as a parallel layer, then migrate pages one-by-one, leaving unmigrated pages untouched on the old stack.

> Task definitions, requirements, and implementation checklists are tracked in `llm_docs/redesign/requirements/`.
> Implementation status for each task is tracked in [`requirements/STATUS.md`](requirements/STATUS.md) — a markdown table mapping each requirement file to one of `not_started`, `in_progress`, or `implemented`. Update that file when a task changes state.

---

## Architecture

### Design Token Foundation

**Location**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)

**Status**: ✅ **Complete**

The foundation file contains all design tokens from Figma "Visual Redesign / Foundations":

#### 1. **Color Palettes** (6 palettes, 75+ color variables)
- `@hdx-brand-*` — Brand green (15 steps: 0–10)
- `@hdx-primary-*` — Primary blue (13 steps: 0–9)
- `@hdx-neutral-*` — Neutral grey (16 steps: 0–10)
- `@hdx-success-*` — Feedback success (11 steps: 0–9)
- `@hdx-warning-*` — Feedback warning (11 steps: 0–9)
- `@hdx-error-*` — Feedback error (11 steps: 0–9)

Each palette is documented with Figma step mappings and usage guidance for data visualization.

#### 2. **Layout Tokens**
- **Spacing scale**: 9 steps (4px base unit): `@hdx-space-1` to `@hdx-space-12`
- **Corner radius**: 2 levels: `@hdx-radius-sm` (2px), `@hdx-radius-md` (4px)
- **Elevation (shadows)**: 4 levels: `@hdx-shadow-none`, `@hdx-shadow-sm`, `@hdx-shadow-md`, `@hdx-shadow-lg`

#### 3. **Typography Tokens**
- **Font families**: `@hdx-font-display` (Merriweather, serif), `@hdx-font-body` (Roboto, sans-serif)
- **Font size scale**: 9 steps: `@hdx-fs-xs` (12px) to `@hdx-fs-5xl` (48px)
- **Font weights**: regular (400), medium (500), semibold (600), bold (700)
- **Line heights**: tight (120%), normal (130%)
- **Named type-style mixins** (reusable, composable):
  - Display styles: `.hdx-display-xl()` through `.hdx-display-xs()`
  - Heading styles: `.hdx-heading-h1()` through `.hdx-heading-h4()`
  - Body styles: `.hdx-body-l/m/s/xs()` × regular/medium/semibold
  - Link styles: `.hdx-link-xl()` through `.hdx-link-xs()`
  - Lead text: `.hdx-lead()`

**Naming Convention**: Variables follow `@hdx-<category>-<step>` pattern. Decimals use digit-only notation (0.1→01, 1.5→15).

**Structure**: Organized into logical sections with clear headers and Figma cross-references, making it easy to track updates back to design source.

---

### Layout Templates

**Location**: [`templates/v2/page.html`](../ckanext-hdx_theme/ckanext/hdx_theme/templates/v2/page.html)

**Status**: ⚠️ **Placeholder — Needs Implementation**

Currently, `templates/v2/page.html` extends the old `page_light.html` layout and loads legacy asset bundles. This is a temporary scaffold that needs to be replaced with proper v2 structure.

**What needs to be done**:
- Extend `base.html` directly (not `page_light.html`)
- Create new asset bundles: `hdx_theme/page-v2-styles`, `hdx_theme/page-v2-scripts`
- Create `header-v2.html` and `footer-v2.html` snippets
- Define responsive grid structure and key layout blocks

**Current scaffold usage**:
- `templates/v2/components.html` renders the current v2 component demo page

---

## Pages Migrated to V2

| Page | Template | Status | Notes |
|------|----------|--------|-------|
| Signup | `ckanext/contribute_flow/signup.html` | ✅ Using BEM | Uses the temporary v2 scaffold; needs re-evaluation |
| Landing pages | `landing_pages/*.html` | ✅ Using BEM | Uses the temporary v2 scaffold; needs re-evaluation |
| Contact contributor | `contribute_flow/contact_contrib.html` | ✅ Using BEM | Uses the temporary v2 scaffold; needs re-evaluation |
| Find/join org | `org/join_org.html` | ✅ Using BEM | Uses the temporary v2 scaffold; needs re-evaluation |

**Note**: These pages are using BEM components as mentioned, but the current v2 scaffold in `templates/v2/page.html` is still a temporary wrapper. Once the new layout is complete, these should be re-validated.

---

## Component Library (V2 Components)

**Location**: `templates/v2/components/`, `less/v2/components/`

**Status**: 🔄 **In Progress** (Buttons and core component styles implemented)

The v2 component library uses the current `templates/v2/components/` directory with matching styles in `less/v2/components/`.
- HTML snippets: `templates/v2/components/*.html`
- LESS styles: `less/v2/components/*.less`
- Compiled CSS: `fanstatic/v2/components/*.css`

**Implemented components**:
- [x] Buttons
- [x] Label
- [x] Avatar + badge
- [x] Dropdown
- [x] Input field
- [x] Navigation
- [x] Selection
- [x] Text link
- [x] Breadcrumb
- [x] Checkbox
- [x] List item
- [x] Letter anchor
- [x] Divider
- [x] Search + autocomplete
- [x] File type indicators
- [x] Tooltips

Each component file should have:
1. **HTML template** (`templates/v2/components/component-name.html`) — reusable snippet with BEM markup
2. **LESS styles** (`less/v2/components/component-name.less`) — styles referencing foundation tokens
3. **Compiled CSS** (`fanstatic/v2/components/component-name.css`) — pre-compiled CSS for webassets

---

## Asset Bundles & Webassets

**Location**: [`fanstatic/webassets.yml`](../ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/webassets.yml)

Bundle configuration:
- `hdx_theme/v2-components-styles` — contains all v2 component CSS files
  - Current contents: `v2/components/avatar-badge.css`, `v2/components/buttons.css`, `v2/components/dropdown.css`, `v2/components/input-field.css`, `v2/components/label.css`, `v2/components/navigation.css`, `v2/components/selection.css`, `v2/components/text-link.css`
  - Will be updated as new components are added

Still needed:
- `hdx_theme/page-v2-styles` — foundation + layout reset + responsive grid + header-v2/footer-v2 styles
- `hdx_theme/page-v2-scripts` — responsive header behavior, shared v2 JS utilities
- `hdx_theme/v2-components-scripts` — any JS needed by v2 components

Page-specific bundles will be created as pages are migrated (e.g., `hdx_theme/homepage-v2-styles`).

---

## Design Token References

**Location**: implemented directly in `less/v2/` and `less/v2/components/`

**Status**: ✅ **Released into the current v2 implementation**

The current Figma-derived foundation and component tokens are implemented in the `less/v2/` files.

Use the design foundations in `less/v2/foundation.less`, `less/v2/colors.less`, `less/v2/spacing.less`, `less/v2/radius.less`, `less/v2/elevation.less`, and `less/v2/typography.less` as the source of truth for the redesign.

---

## Implementation Checklist

### Phase 1: Foundation ✅ (In Progress)
- [x] Create `less/v2/foundation.less` with all design tokens
- [x] Export design tokens from Figma for reference
- [ ] Set up `templates/v2/page.html` to extend `base.html` (not `page_light.html`)
- [ ] Create `header-v2.html` and `footer-v2.html` snippets
- [ ] Register v2 asset bundles in `webassets.yml`
- [ ] Test foundation tokens in a simple test page

### Phase 2: Component Library 🔄 (Next Priority)
- [x] Create `templates/v2/components/` directory ✓
- [x] Create `less/v2/components/` directory ✓
- [x] Create `fanstatic/v2/components/` directory ✓
- [x] Build Button component (primary, secondary, tertiary) ✓
- [x] Build Label component (3 sizes × 6 colors) ✓
- [x] Build Badge component (indicator dot) ✓
- [x] Build Divider component (horizontal separator) ✓
- [x] Build Avatar component ✓
- [x] Build Dropdown component ✓
- [x] Build Input field component ✓
- [x] Build Navigation component ✓
- [x] Build Selection component ✓
- [x] Build Text link component ✓
- [x] Build remaining components (File type indicator, Tooltip)
- [x] Register `v2-components-styles` bundle in webassets.yml ✓
- [ ] Create `v2-components-scripts` bundle (if needed)
- [x] Add placeholder demo page with all components ✓

### Phase 3: Page Migrations 🔲 (Sequential)
- [ ] Signup page
- [ ] Landing pages (signals, hapi)
- [ ] Contact contributor page
- [ ] Find/join org page
- [ ] Homepage
- [ ] Dataset list (light)
- [ ] Dataset list (desktop)
- [ ] Remaining pages (org, user, dataset read, etc.)

### Phase 4: Cleanup 🔲 (Final)
- [ ] Delete old layout templates (`page.html`, `page_light.html`)
- [ ] Delete old BEM blocks (`bem.blocks/`)
- [ ] Remove old asset bundles from `webassets.yml`
- [ ] Rename `templates/v2/page.html` → `page.html`, `templates/v2/components/` → `templates/components/`
- [ ] Update [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md) to reflect final structure

---

## Quality Checklist — Before Continuing

✅ **foundation.less**
- [x] Proper file location: `less/v2/foundation.less` ✓
- [x] Descriptive section headers with Figma references ✓
- [x] Consistent naming convention (`@hdx-<category>-<step>`) ✓
- [x] All color palettes documented with usage guidance ✓
- [x] Layout tokens (spacing, radius, elevation) complete ✓
- [x] Typography tokens as reusable mixins ✓
- [x] Line count: 460 lines (reasonable size) ✓

⚠️ **templates/v2/page.html**
- [ ] Should extend `base.html`, not `page_light.html`
- [ ] Needs new v2 asset bundle registration
- [ ] Needs responsive header/footer snippets
- [ ] Current references in signup/landing/contact pages should be re-validated after template update

---

## Next Steps

1. **Update `templates/v2/page.html`** to properly extend `base.html` and load v2 bundles
2. **Create responsive header/footer** templates for v2 (`header-v2.html`, `footer-v2.html`)
3. **Register v2 asset bundles** in `webassets.yml`
4. **Build component library** (`templates/v2/components/`) starting with core components (button, input, card)
5. **Migrate first simple page** (signup or landing page) as proof-of-concept
6. **Iterate** through remaining pages

---

## Notes for Developers

- **Use foundation tokens** in all v2 component styles — never hardcode colors, spacing, or typography values
- **Test on multiple breakpoints** — v2 is fully responsive (desktop, tablet, mobile)
- **Keep old stack untouched** during migration — unmigrated pages should not be affected by v2 changes
- **Update [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)** as architecture evolves
- **Use BEM naming** for all v2 components: `.component__element--modifier`

---

## References

- **Design Source**: 2055_HDX_delivery (HDX Internal)
- **Migration Strategy**: [PLAN.md](PLAN.md)
- **Design Context**: [LLM_CONTEXT_HDX_DESIGN.md](../LLM_CONTEXT_HDX_DESIGN.md)
- **Foundation Tokens**: [`less/v2/foundation.less`](../ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less)
