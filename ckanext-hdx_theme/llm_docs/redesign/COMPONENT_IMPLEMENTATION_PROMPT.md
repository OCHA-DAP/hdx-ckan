You are a senior frontend engineer experienced with CKAN theming, BEM methodology, and Bootstrap 5.2.3.
## Context
I am working on a redesign of a CKAN website using a custom theme (`hdx_theme`).
The design source is Figma, and I already have:
- Design foundations (colors, spacing, typography, etc.)
- Existing CKAN structure and templates
- HTML + CSS exported from Figma (this is only a visual reference and must NOT be used as-is)
Your job is to transform the design into production-ready, reusable BEM components that integrate cleanly into CKAN.
---
## Task
Implement the **[COMPONENT NAME]** as a reusable BEM component.
This is part of the v2 component library:
"Implement base building blocks (most common reusable UI components)"
---
## Requirements
### 1. Architecture
- Use **BEM methodology strictly**
- Follow this structure:
  - `templates/v2/components/buttons/`
  - `fanstatic/src/less/v2/components/`
- Separate:
  - HTML (CKAN snippets using Jinja2)
  - LESS styles
- Use CKAN snippet system for rendering components
---
### 2. Styling Rules
- **Do not** use Bootstrap component or utility classes. The v2 design system is standalone:
  - Use `var(--hdx-*)` design tokens and `mixins.less` typography/layout mixins exclusively
  - Bootstrap is bundled for legacy pages only and must not be relied on in new v2 components
- Use values from **design foundations** (colors, spacing, radius, typography)
- Match the Figma design **pixel-perfectly**
- Do NOT introduce new styles, spacing, or assumptions
---
### 3. Components to Implement
#### Buttons
Properties:
- style: `primary | secondary | tertiary`
- type: `text | icon-only`
- size: `S | M | L`
- state: `enabled | hover | active | disabled`
- icon: `true | false`
#### Text Buttons
Properties:
- style: `primary | secondary | tertiary`
- size: `S | M | L`
- state: `enabled | hover | active | disabled`
- icon position: `left | right`
---
### 4. BEM Naming
Use a consistent naming convention, for example:
- `.c-button`
- `.c-button--primary`
- `.c-button--size-m`
- `.c-button--icon-only`
- `.c-button__icon`
---
### 5. Icons
- There is an existing icons directory containing SVG files.
- All icons MUST be used from this directory.
- Do NOT recreate or inline SVG paths manually unless explicitly necessary.
Available icon example:
- `placeholder.svg` (used in Figma as a generic icon reference)
### Icon rules:
- Icons must be included via reusable markup (e.g. <img>, <use>, or CKAN-compatible include/snippet system depending on existing project conventions).
- Do NOT hardcode SVG markup inside components.
- Ensure icons are fully scalable and inherit correct sizing from BEM modifiers.
- Icon positioning (left/right) must follow component props exactly.
### Specific requirement for this task:
- If an icon is required for demonstration or fallback states, use `placeholder.svg` from the icons directory.
### 6. Deliverables
Provide:
#### A. LESS
- Component styles using variables from foundations
- Organized, readable, scalable
#### B. CKAN Snippet (Jinja2)
- Reusable snippet with parameters for all props
- Example usage
#### C. Example Rendering
- A `placeholder.html` page that:
  - Imports and renders all button variations
  - Uses CKAN `{% snippet %}` calls
---
### 7. Constraints
- Do NOT:
  - Add extra features or redesign anything
  - Simplify or reinterpret the design
- Do:
  - Follow the Figma export visually, but rewrite code cleanly
  - Ensure scalability and reusability
---
### 8. Input
I will provide:
- Figma-exported HTML + CSS (reference only)
- Foundation variables (colors, spacing, etc.)
---
### 9. Output Format
Structure your answer clearly:
1. Explanation of approach (brief)
2. LESS code
3. CKAN snippet (Jinja2)
4. Example `placeholder.html`
5. Notes on how props map to classes
---
Focus on correctness, structure, and maintainability over verbosity.
