# Task 001: Migrate V2 LESS design tokens to CSS custom properties

Convert the V2 design foundation from LESS variables to CSS custom properties so token values are visible in browser dev tools at runtime.

## Goal

Expose Figma design tokens as CSS custom properties on `:root` so they are inspectable in browser dev tools and available to components that prefer CSS variables over LESS compilation.

## Scope

**In:**
- `less/v2/foundation.less` and related foundation files (`colors.less`, `spacing.less`, `radius.less`, `elevation.less`, `typography.less`)
- Runtime CSS variables exposed in the V2 page bundle (`v2/foundation.css`)

**Out:**
- Full rewrite of `less/v2/components/*` from LESS to CSS
- Changes to legacy BEM blocks outside V2 scope

## Requirements

1. Create a `:root` block with all foundation tokens as `--hdx-*` CSS custom properties.
   - Naming maps directly from LESS: `@hdx-brand-5` → `--hdx-brand-5`, `@hdx-space-1` → `--hdx-space-1`, etc.
2. Keep a LESS compatibility shim in `foundation.less` redefining `@hdx-*` variables from `var(--hdx-*)` so existing component LESS files continue to compile unchanged.
3. Load `v2/foundation.css` before component styles in the V2 page bundle.
4. Preserve all existing Figma reference comments and section headings.

## Implementation notes

- Single `:root` block defined directly in `foundation.less`, compiled to `v2/foundation.css`.
- LESS shim example: `@hdx-brand-5: var(--hdx-brand-5);`
- `v2/foundation.css` is the first entry in the `v2-components-styles` bundle.
