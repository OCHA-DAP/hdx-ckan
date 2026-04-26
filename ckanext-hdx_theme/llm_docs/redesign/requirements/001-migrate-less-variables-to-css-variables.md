# Task 001: Migrate V2 LESS design tokens to CSS custom properties

## Goal

Convert the existing V2 design foundation from LESS variables into CSS custom properties so the new HDX redesign can:

- inspect computed design tokens directly in browser dev tools
- compare Figma token values to live styles more easily
- support runtime theming and future CSS-first component work
- reduce dependency on LESS variable semantics for foundation tokens

## Why this is useful

The current redesign foundation lives in LESS files under `less/v2/`. Those variables are compiled away before runtime, which makes it hard to inspect the actual token values in the browser and compare them to Figma properties during implementation.

By migrating the foundation token layer to CSS variables, the browser will expose the live token values on `:root`, and component styles can continue to reference the same semantic tokens through a single source of truth.

## Scope

This task should focus on the design token foundation only, not on converting every component style from LESS to CSS.

### In scope

- `ckanext-hdx_theme/ckanext/hdx_theme/less/v2/foundation.less`
- Related `less/v2/*` foundation files if they are currently used as token-only libraries (`colors.less`, `spacing.less`, `radius.less`, `elevation.less`, `typography.less`)
- The resulting runtime CSS variables exposed in the V2 page bundle
- Documentation or comments that explain the new CSS variable mapping

### Out of scope

- Full rewrite of all `less/v2/components/*` files into CSS
- Changes to existing page or component templates unless needed to load the new root token CSS
- Refactoring legacy BEM blocks outside the V2 redesign scope

## Requirements

1. Create a CSS custom property layer for the V2 design foundation.
   - Prefer a single `:root` fallback root for all tokens.
   - Use clear, semantic names that map to the existing LESS naming convention.
   - Keep Figma semantics explicit: colors, spacing, radius, elevation, typography, font-families, font-sizes, weights, line-heights.

2. Preserve the existing V2 token naming intent.
   - Example: `@hdx-brand-5` becomes `--hdx-brand-5`.
   - Example: `@hdx-space-1` becomes `--hdx-space-1`.
   - Example: `@hdx-radius-md` becomes `--hdx-radius-md`.

3. Ensure the new CSS variables are usable from LESS.
   - When necessary, keep a small `foundation.less` shim that redefines LESS variables from CSS properties, for backward compatibility in existing LESS components.
   - Example: `@hdx-brand-5: var(--hdx-brand-5);`

4. Keep Figma reference metadata and inline documentation.
   - Preserve or improve the current file comments and section headings.
   - Document any changed or renamed tokens clearly.

5. Add a small verification step to the task definition.
   - Confirm that `:root` contains the expected CSS variables when the V2 page bundle is loaded.
   - Confirm that the browser dev tools show the correct token values for a sample V2 component.

## Implementation steps

1. Review the V2 LESS foundation files:
   - `less/v2/foundation.less`
   - `less/v2/colors.less`
   - `less/v2/spacing.less`
   - `less/v2/radius.less`
   - `less/v2/elevation.less`
   - `less/v2/typography.less`

2. Decide on a single source of truth.
   - Either migrate everything into `foundation.less` as CSS variables, or keep the modular files but ensure they all export a shared CSS variable root.

3. Create a `:root` block in the appropriate CSS/LESS entry file.
   - Create that root block directly in `less/v2/foundation.less`.
   - Load the compiled foundation CSS bundle (`v2/foundation.css`) before V2 component and V2 page styles so the variables are available at runtime.

4. Add LESS compatibility mappings if needed.
   - Existing V2 component LESS files can continue using legacy `@hdx-*` variables during migration.
   - Keep the LESS token definitions as compatibility shims until the component styles are fully migrated.
   - Verify that `:root` contains the expected CSS variables when the V2 page bundle is loaded.

5. Update asset bundle registration if needed.
   - Ensure the V2 page bundle loads the new foundation CSS before component styles.
   - Do not break the existing V2 page scaffold.

6. Test in browser.
   - Load a V2 page or component in the browser.
   - Inspect `:root` and verify key variables like `--hdx-brand-5`, `--hdx-space-4`, `--hdx-radius-md`.
   - Verify a V2 component still renders correctly and continues to use the same tokens.

## Expected outcome

- A new CSS custom property token layer available at runtime on `:root`.
- Existing V2 LESS components continue to compile and use token values via backward-compatible LESS shims.
- Browser dev tools can inspect Figma token values directly in live HDX V2 pages.
- The task file clearly documents the purpose, scope, steps, and validation criteria.

## Notes for future tasks

- Once the token layer is stable, future tasks can migrate individual V2 component styles from LESS variables directly to CSS variables.
- This foundation change should be treated as a low-risk enabling task, not a visual redesign of components.
- Keep the same naming convention across all v2 design system work to make later automation and theme variants easier.
