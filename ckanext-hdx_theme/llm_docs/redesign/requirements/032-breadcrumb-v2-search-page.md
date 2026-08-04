# Task 032: Introduce c-breadcrumb on the v2 Search Page

**Scope:** Search/dataset-list page only (`/dataset` route, `v2=true` gate)

---

## Context

The v2 redesign uses a modern `c-breadcrumb` component (`templates/v2/components/breadcrumb.html`)
that follows the BEM + CSS-token architecture of the design system. However, all v2 pages —
including the search page — currently still render the **legacy Bootstrap-based breadcrumb**:
a `<ol class="breadcrumb">` inside a `.toolbarRow` gray bar, styled with LESS overrides and
populated via the `breadcrumb_content` Jinja block.

This task replaces the legacy breadcrumb with `c-breadcrumb` on the v2 search page, fixes a
pre-existing rendering bug in the component, and defines the canonical integration pattern that
future v2 page migrations will follow.

No other pages are in scope. Non-v2 pages are unaffected.

---

## Scope

### Included

- Fix the last-item rendering bug in `c-breadcrumb`: falsy `href` → `.c-breadcrumb__current` (non-linked)
- Add `show_home` param to `c-breadcrumb` (default `true`) — auto-prepends the Home crumb so callers don't repeat it
- Extend `c-text-link` with an `inner_attrs` param to support label-wrapping spans (needed for RDFa `property="name"`)
- Add RDFa / schema.org markup to `c-breadcrumb` using `c-text-link` (not inline `<a>`)
- Override the `toolbar` block in `search/search.html` to render `c-breadcrumb` instead of the legacy `.toolbarRow` structure
- Remove the now-redundant `breadcrumb_content` override from `search/search.html`
- Add `.hdx-v2-breadcrumb-row` wrapper + spacing in `search.less`
- Breadcrumb visible on all breakpoints (SM / MD / LG)

### Excluded

- No changes to `v2/page.html`
- No changes to non-v2 page templates or to the legacy breadcrumb system
- No other v2 pages (dataset, org, location, user — separate future tasks)
- No Mixpanel / analytics tracking
- No "show more" / truncation / overflow UI beyond what the existing CSS already handles
  (`max-width: 21.875rem`, `text-overflow: ellipsis`)

---

## Audit Findings

### Existing `c-breadcrumb` component

**Template:** `templates/v2/components/breadcrumb.html`

Parameters:

| Param | Type | Default | Description |
|---|---|---|---|
| `items` | list | `[]` | Ordered `{label, href}` dicts. Last item = current page. |
| `separator` | string | `'/'` | Separator between crumbs. |
| `extra_classes` | string | `''` | Additional CSS classes on the root `<nav>`. |

LESS: `navigation.less` lines 225–260 — flex row, 8px gap, 12px font, CSS custom properties.
No Bootstrap dependency. Classes: `.c-breadcrumb`, `.c-breadcrumb__item`,
`.c-breadcrumb__separator`, `.c-breadcrumb__current`.

**Bug:** The template renders ALL items via `c-text-link`, including the last (current) item.
The LESS defines `.c-breadcrumb__current` for a non-linked `<span>` but the template never
uses it. An item with `href=''` produces `<a href="">`, which is semantically wrong for the
current page and breaks accessibility expectations.

### Legacy breadcrumb (currently active on search page)

`v2/page.html` (lines 58–75) defines the `toolbar` block:

```
.toolbarRow > .hdx-v2-container > .toolbar
  {% block breadcrumb %}
    if breadcrumb_content is not empty:
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">
          home_breadcrumb_item.html   ← hardcoded Home item with position=1 RDFa
          {% block breadcrumb_content %}{% endblock %}
        </ol>
      </nav>
  {% endblock %}
```

`search/search.html` (lines 50–52) provides:

```jinja2
{% block breadcrumb_content %}
  {% snippet "snippets/active_breadcrumb_item.html", title=_('Datasets'), position=2 %}
{% endblock %}
```

Result: Bootstrap `<ol class="breadcrumb">` inside a gray toolbar bar. This is the old v1
visual language and does not match the v2 design system.

### RDFa / schema.org in legacy breadcrumb

Each legacy snippet includes schema.org RDFa: `typeof="ListItem"`, `property="item"` (link),
`property="name"` (text), `property="position"` (integer). This supports search engine
breadcrumb rendering. The new `c-breadcrumb` must carry equivalent markup.

### v2 search page layout context

```
.hdx-v2-container  (wraps all main content inside <div role="main">)
  ├── [toolbar block]            ← c-breadcrumb replaces this
  ├── [flash messages]
  └── .container.mainContent
        └── .hdx-wrapper
              └── .contentBackground
                    └── .wrapper-primary
                          └── primary_content → search_results_wrapper
                                └── package_list.html (v2 branch):
                                      [filter overlay]        (MD/SM)
                                      [filter btn row]        (MD/SM)
                                      .hdx-v2-search-layout
                                        [sidebar filters]     (LG)
                                        .hdx-v2-dataset-list
                                          [dataset cards]
```

The breadcrumb belongs inside `.hdx-v2-container`, above the `container mainContent` section.

---

## Integration Strategy

### Options considered

**Option A — Override `toolbar` in `search/search.html`** *(recommended)*

Replace the entire toolbar block (and its `.toolbarRow` wrapper) with `c-breadcrumb` in the
search page template only. Zero change to `v2/page.html`.

**Option B — Modify `v2/page.html` to use `c-breadcrumb` natively**

Replace the `breadcrumb` block logic and use a `breadcrumb_items` context variable set by child
templates. Risk: CKAN's Jinja implementation evaluates child blocks after parent blocks;
variables set in a child block are not visible to parent rendering.

**Option C — Add a `{% block page_breadcrumb %}` block in `v2/page.html`**

Introduce a new block above the toolbar. Child templates override it. Requires also emptying
`breadcrumb_content` to avoid showing both old and new breadcrumbs simultaneously.

### Recommendation: Option A

Override `toolbar` in `search/search.html`. This:
- Removes the legacy `.toolbarRow` structure entirely from the v2 search page
- Renders `c-breadcrumb` inside `.hdx-v2-container` (horizontally aligned with page content)
- Makes zero impact on `v2/page.html` or any non-search template
- Establishes the canonical pattern: each v2 page migration overrides `toolbar` the same way

When all pages are migrated to v2, the old `toolbar` block in `v2/page.html` can be removed.

---

## Requirements

### 1. Fix `c-breadcrumb` template — last item rendering + `show_home` param

**File:** `templates/v2/components/breadcrumb.html`

**Last-item fix:** Items are rendered differently based on `item.href`:

- **Truthy href** → render via `c-text-link` snippet (linked crumb)
- **Falsy href** (`''` or absent) → render `<span class="c-breadcrumb__current">` (non-linked)

The separator never appears after the last item (existing `if not is_last` logic).
`.c-breadcrumb__current` already exists in `navigation.less` — no LESS changes needed.

**`show_home` param:** Add a boolean param (default: `true`) that automatically prepends
`{'label': _('Home'), 'href': '/'}` as the first item. This avoids callers having to repeat
the Home item on every page. Set `show_home=false` only when a template manages the first
crumb itself.

**Updated component API:**

| Param | Type | Default | Description |
|---|---|---|---|
| `items` | list | `[]` | `{label, href}` dicts. Last item = current page (falsy href). |
| `show_home` | bool | `true` | When true, Home is prepended automatically. |
| `separator` | string | `'/'` | Separator between crumbs. |
| `extra_classes` | string | `''` | Extra CSS classes on the root `<nav>`. |

### 2. Extend `c-text-link` with `inner_attrs` param

**File:** `templates/v2/components/text-link.html`

Add an `inner_attrs` param (dict, default `{}`). When provided, the label is wrapped in a
`<span>` carrying those attributes instead of being rendered as bare text:

```html
<!-- inner_attrs={'property': 'name'} -->
<a class="c-text-link ..." href="...">
  <span property="name">Label text</span>
</a>
```

This allows `c-breadcrumb` to pass RDFa attributes into the link label without inlining the
`<a>` element manually. The `<span>` wrapper is purely semantic — no visual effect.

### 3. Add RDFa / schema.org markup to `c-breadcrumb`

**File:** `templates/v2/components/breadcrumb.html`

Add schema.org RDFa via the existing component primitives:

- `<nav>`: add `vocab="https://schema.org/"` and `typeof="BreadcrumbList"`
- Each `.c-breadcrumb__item`: add `property="itemListElement"` and `typeof="ListItem"`
- Linked item: call `c-text-link` with `attrs={'property': 'item', 'typeof': 'WebPage'}` and
  `inner_attrs={'property': 'name'}` — no inline `<a>` needed
- Current item: add `property="name"` to the `.c-breadcrumb__current` span
- All items: add `<meta property="position" content="{{ loop.index }}">` as a sibling inside
  the `.c-breadcrumb__item` span (after the link/span, before the separator)

### 4. Override `toolbar` block in `search/search.html`

**File:** `templates/search/search.html`

Replace the `breadcrumb_content` block with a `toolbar` block override. Since `show_home`
defaults to `true`, only the page-specific crumbs need to be in `items`:

```jinja2
{% block toolbar %}
  <div class="hdx-v2-breadcrumb-row">
    {% snippet 'v2/components/breadcrumb.html',
        items=[{'label': _('Datasets'), 'href': ''}] %}
  </div>
{% endblock %}
```

Remove the `breadcrumb_content` block — it is superseded by the toolbar override.

**Effective crumb trail:**

| Position | Label | href | Rendered as |
|---|---|---|---|
| 1 | `Home` (auto) | `'/'` | `c-text-link` (linked) |
| 2 | `_('Datasets')` | `''` | `.c-breadcrumb__current` (non-linked) |

"Datasets" is the terminal crumb on the search page and must never be linked.

### 4. Add `.hdx-v2-breadcrumb-row` spacing wrapper

**File:** `hdx-styles/src/common/less/v2/search.less`

Add a layout wrapper that provides vertical spacing between the header and the breadcrumb,
and between the breadcrumb and the search content below. The component itself already has
`padding: var(--hdx-space-2) 0` (8px top/bottom) via `.c-breadcrumb`. The wrapper may add
additional margin if needed.

The wrapper must NOT use `.container`, `.row`, `.col-*`, or any Bootstrap grid classes.
It must NOT define a max-width (already constrained by the parent `.hdx-v2-container`).

Exact spacing values should match the v2 design spacing scale (`--hdx-space-*` tokens).
If no additional spacing beyond the component's own padding is needed, the wrapper can be
a structural-only div with no additional styles.

---

## Architecture Constraints

### No Bootstrap dependencies

The `c-breadcrumb` component uses pure BEM + CSS custom properties. No Bootstrap classes
must be introduced in the new template or LESS.

### No `container`, `row`, `col-*` layout classes

Horizontal alignment is handled by the parent `.hdx-v2-container` (already in `v2/page.html`).

### No duplicate Jinja blocks

CKAN's Jinja inheritance does not allow re-defining the same block in a template. The
`breadcrumb_content` block must be removed when `toolbar` is overridden (they are in the same
inheritance chain and `breadcrumb_content` is a descendant of `toolbar`).

### No impact on non-v2 pages

`package/search.html` (extends `page.html`) retains its `breadcrumb_content` override and
the legacy breadcrumb system. It is not touched by this task.

### No impact on `v2/page.html`

The `toolbar` block override in `search/search.html` takes precedence; `v2/page.html` is
unchanged. All other pages that extend `v2/page.html` continue using the legacy toolbar.

---

## Files Affected

| File | Change |
|---|---|
| `templates/v2/components/breadcrumb.html` | Fix last-item rendering; add `show_home` param; add RDFa markup |
| `templates/v2/components/text-link.html` | Add `inner_attrs` param for label-wrapping span |
| `templates/search/search.html` | Override `toolbar` block; remove `breadcrumb_content` block |
| `hdx-styles/src/common/less/v2/search.less` | Add `.hdx-v2-breadcrumb-row` wrapper styles |

**Unchanged:**
- `templates/v2/page.html`
- `templates/package/search.html` (v1 search)
- `templates/snippets/home_breadcrumb_item.html`
- `templates/snippets/active_breadcrumb_item.html`
- `templates/snippets/other_breadcrumb_item.html`
- `hdx-styles/src/common/less/v2/components/navigation.less`
- All other templates and components

---

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| D1 | Spacing above breadcrumb: additional top margin beyond component's own `padding: 8px 0`? | Yes — `.hdx-v2-breadcrumb-row` adds `margin-top: var(--hdx-space-2)` (8px) and `margin-bottom: var(--hdx-space-2)` (8px) |
| D2 | Separator character: `/` or different character/icon? | `/` — default kept; no change |
| D3 | Long label truncation: `max-width: 21.875rem` sufficient, or exempt "Datasets" crumb? | Existing truncation kept as-is; "Datasets" is always short so no special exemption needed |
| D4 | Future pages — `href` for "Datasets" link on dataset detail page: `/dataset` or with filters? | Deferred — out of scope for this task (search page only) |
