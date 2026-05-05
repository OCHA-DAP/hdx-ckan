# Task 017: Implement v2 navbar

Implement the main navigation bar (`hdx-navbar`) in `v2/header.html` and CSS. This is the teal horizontal bar sitting directly below the top-bar, containing logo, search, nav items, and right-side actions.

**Figma source:** `llm_docs/redesign/figma_exports/navbar.html`

## Responsive layout

| State | XL (≥80rem) | MD (48–80rem) | SM (<48rem) |
|-------|-------------|---------------|------------|
| **Logged Out** | logo + search + nav + login | logo + search + hamburger | logo + search-icon + hamburger |
| **Logged In** | logo + search + nav + bell + avatar + add-data | logo + bell + add-data + hamburger (search hidden, avatar hidden) | logo + search-icon + bell + hamburger (avatar hidden, add-data hidden; to be replaced with icon) |

## Key features

- **Search centering**: Uses flex: 1 with max-width and margin: 0 auto to center between logo and nav/actions
- **Zero gaps between main sections**: Logo, search, nav use gap: 0; internal gaps (var(--hdx-space-3) / 0.75rem within nav, 1rem within actions on XL / 0.75rem on MD/SM)
- **Spacing on XL**: var(--hdx-space-3) margin-right on nav creates gap between Products nav-item and the right-side actions
- **Right alignment on MD/SM**: Actions pushed right with margin-left: auto when nav is hidden
- **Login state detection**: data-logged-in="true" attribute enables CSS-based visibility
- **Search icon on SM**: Search form hidden, search icon button shown inside `__actions` (d-md-none utility); shares same 2.125rem × 2.125rem size, border-radius: 2px, and hover styles as the bell button
- **Avatar dropdown**: Avatar hidden on MD/SM (moved to hamburger dropdown for logged-in users)

## Layout structure

```
navbar__inner (flex, gap: 0, padding: 0 3rem / 0 1rem on SM)
├── navbar__logo (flex: 0, 4.5rem × 1.5rem)
├── navbar__search (flex: 1 with max-width: 25rem/21.25rem, centered)
│   └── form (hidden on SM)
├── navbar__nav (flex: 0, gap: var(--hdx-space-3), margin-left: auto, margin-right: var(--hdx-space-3))
│   └── nav-items (Data, Locations, Organisations, Products)
└── navbar__actions (flex: 0, gap: 1rem on XL / 0.75rem on MD/SM, margin-left: auto on MD/SM)
    ├── search-icon (SM only, d-md-none — always first in DOM, outside logged-in/out if/else)
    ├── [if logged in]
    │   ├── bell
    │   ├── avatar (hidden on MD/SM, XL only)
    │   └── add-data button (XL and MD, hidden on SM)
    ├── [if logged out]
    │   └── login button (XL only)
    └── hamburger (hidden on XL, visible on MD/SM)
```

## CSS features

- **data-logged-in="true"**: Attribute on navbar enables login-state-aware CSS hiding (search on MD logged in)
- **margin: 0 auto on search**: Centers search input within flex space
- **margin-left: auto on nav/actions**: Pushes right-side elements to the right
- **form { display: none }**: Hides search form on SM
- **d-md-none on search-icon**: Bootstrap utility to hide search icon on MD and above; button lives inside `__actions` so it is naturally right-aligned

### `fanstatic/webassets.yml`

Add `v2/navbar.css` to `v2-page-styles` (before `v2/footer.css`):

```yaml
v2-page-styles:
  contents:
    - vendor/bootstrap5/css/bootstrap.css
    - v2/layout.css
    - v2/top-bar.css
    - v2/footer.css
    - v2/navbar.css
```

## Implementation notes

- Search bar is centered between logo and nav items using flex: 1 with max-width and margin: 0 auto
- Search icon button lives inside `__actions` (not between search and nav), so it is right-aligned with the bell and hamburger on SM
- Search icon styled identically to bell: 2.125rem × 2.125rem, border-radius: 2px, transparent background, same hover/focus styles
- Uses Bootstrap's d-md-none utility to hide search icon on MD and above
- data-logged-in attribute enables CSS-based hiding of search on MD when logged in
- Avatar hidden on MD/SM (to be moved to hamburger dropdown in task 019)
- Search form hidden on SM, search icon button shown instead

