# Resource Card Component

**Task:** resource-card  
**Status:** implemented

---

## Props

| Prop | Type | Default | Notes |
|------|------|---------|-------|
| `title` | string | `''` | Resource display name |
| `title_href` | string | `'#'` | Resource detail page URL (`url_for('dataset_resource.read', ...)`) |
| `format_text` | string | `''` | Format string rendered uppercase (e.g. `'GEOJSON'`). Pass `res.format`. |
| `format_category` | string | `'neutral'` | `neutral \| geo \| tabular \| document \| web`. Drives icon colour. Use `h.hdx_format_to_icon_category(res.format)`. |
| `description` | string | `''` | Full description text; clamped by default. The "Show more" button is always rendered when description is present; JS hides it if the text is short enough not to be clamped. |
| `pcoded` | bool | `false` | Render a "P-coded" label chip. |
| `api_available` | bool | `false` | Render an "API available" label chip. |
| `preview_available` | bool | `false` | Show the "More information" secondary action button linking to `title_href`. |
| `download_url` | string | `'#'` | URL for the primary Download button. |
| `download_size` | string | `''` | Human-readable file size (e.g. `'14.2K'`). Appended to the Download button label when set. |
| `extra_classes` | string | `''` | Extra CSS classes on the root element. |

---

## Structure

```
.c-resource-card  [data-module="clamped-text" if description]
  .c-resource-card__header
    .c-resource-card__top
      .c-resource-card__file-type
        file-type-icon snippet  (format=format_category, size='m')
        .c-resource-card__format-text   ← format_text (uppercase)
      .c-resource-card__tags            ← if pcoded or api_available
        c-label "P-coded"               ← if pcoded
        c-label "API available"         ← if api_available
    a.c-resource-card__title[href=title_href]
    .c-resource-card__desc              ← if description
      p[data-clamped-content]           ← description text
  .c-resource-card__footer
    c-text-button "Show more"           ← if description (hidden by CSS; JS shows when clamped)
    .c-resource-card__actions
      c-button (secondary) "More information" [href=title_href]  ← if preview_available
      c-button (primary)   "Download (size)"  [href=download_url]
```

---

## Behavior

### Description clamping
- Description is **always visible** (never hidden entirely).
- Default: clamped to **7 lines** at SM, **3 lines** at MD+.
- Expanded: `is-open` class on `[data-clamped-content]` and on the root removes the clamp.
- The chevron icon in the show-more button rotates 180° on expand via CSS `.c-resource-card.is-open .c-text-button__icon`.

### Show more / less toggle
- Powered by the shared `clamped-text.js` module.
- `data-module="clamped-text"` is placed on the **root `.c-resource-card`** element (not on `__desc`) so the module can find both the `[data-clamped-content]` `<p>` and the `.c-text-button` in `__footer` in a single `querySelectorAll` pass.
- Only added when `description` is truthy.
- The `.c-text-button` is **hidden by default via CSS** (`.c-resource-card .c-text-button { display: none }`).
- On DOMContentLoaded, `clamped-text.js` checks `scrollHeight > clientHeight` (or `is-open` already on the container for pre-opened cards). If the text is actually clamped, it adds `is-clamped` to the container, which CSS uses to reveal the button (`.c-resource-card.is-clamped .c-text-button { display: inline-flex }`). Short descriptions are never shown a button.

### Conditional rendering
| Prop | What it shows |
|------|--------------|
| `pcoded` | "P-coded" label chip |
| `api_available` | "API available" label chip |
| `preview_available` | "More information" secondary button → `title_href` |
| `download_url` | "Download" primary button → always rendered |
| `download_size` | Appended to Download button label: "Download (14.2K)" |

---

## Dependencies

| Dependency | Usage |
|-----------|-------|
| `v2/components/file-type-icon.html` | File type icon badge (square, coloured) |
| `v2/components/label.html` | P-coded / API available chips (color='light', size='s', icon=False) |
| `v2/components/button.html` | "More information" (secondary) and "Download" (primary) action buttons |
| `v2/components/text-button.html` | "Show more / Show less" toggle (tertiary, icon-right chevron) |
| `clamped-text.js` | Generic show-more/less JS module (shared with dataset-card, dataset-page-header) |
| `h.hdx_format_to_icon_category()` | Python helper — maps `res.format` string to icon category |

---

## Shared Refactors Included

### `clamped-text.js` (new shared module)
Replaces `dataset-card.js`. Generic IIFE that handles show-more/less for any
`[data-module="clamped-text"]` container:
- Selector: `[data-module="clamped-text"]`
- Content: `[data-clamped-content]`
- Button: `.c-text-button` (first found within container)

Affected components: `dataset-card.html`, `dataset-page-header.html`, `resource-card.html`.

### `h.hdx_format_to_icon_category(format_str)` (new Python helper)
Maps resource format string → icon category. Registered in `plugin.py`.
Used to simplify the inline format-mapping logic in `package_item_v2.html`.

---

## Constraints

- **Hover**: CSS `:hover` only. No `is-hovered`, `state-hovered`, or `--hovered` classes.
- **JS**: no jQuery; plain vanilla JS via IIFE.
- **Responsive**: breakpoint `@hdx-bp-md` (48rem). File-type icon shrinks from 32px to 24px at SM via CSS override.
- **No hardcoded colors/spacing**: all via `var(--hdx-*)` tokens.

---

## Decisions Taken

| Question | Decision |
|----------|----------|
| What does `preview_available` render? | Controls visibility of "More information" secondary action button |
| Where does the show-more button live relative to description? | In `__footer`, outside `__desc`; `data-module` placed on root card element to bridge both |
| Shared JS or separate? | New shared `clamped-text.js` covering dataset-card + dataset-page-header + resource-card |
| Format mapping? | New `h.hdx_format_to_icon_category()` Python helper; `package_item_v2.html` simplified to use it |
| How is "Show more" hidden when description is short? | CSS hides `.c-text-button` by default; `clamped-text.js` adds `is-clamped` on the container after detecting overflow (`scrollHeight > clientHeight`); CSS re-shows on `is-clamped`. Same pattern applied to dataset-card and dataset-page-header. `show_show_more` prop removed — callers no longer need to determine truncation manually. |
