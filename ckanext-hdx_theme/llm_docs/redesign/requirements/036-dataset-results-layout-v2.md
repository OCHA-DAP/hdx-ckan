# Dataset Results Page — Full Layout Requirements (v2)

## Context

The dataset search results page is being progressively redesigned as part of the v2 redesign effort (gated by `v2=true`). The individual pieces (cards, filters, header, pagination, search bar) are implemented. This task defines and implements the **full-page layout composition** that assembles these pieces correctly at every breakpoint, matching the Figma designs in `dataset-results-xl/md/sm.html`.

**Decisions:**
- Header / search bar / pagination move **inside the content column** (match Figma XL exactly)
- Use **page.html primary/secondary regions** (sidebar in `secondary_content` block, content in `primary_content`)
- Legacy `container mainContent` / `contentBackground` / `hdx-wrapper wrapper` removed from page.html
- Layout is **search-specific** — no generalization to other listing pages
- `hdx-v2-search-page` scoping class (originally planned) was not implemented — `hdx-v2-content-columns` in page.html serves the same role
- Border color: `--hdx-neutral-1` (not `--hdx-neutral-2`)
- Sidebar padding: `20px top / 40px right / 80px bottom / 48px left` (Figma-aligned)

---

## 1. Current Layout Audit

### Template chain (v2 path)

```
search/search.html  (extends v2/page.html)
  ├─ secondary_content block
  │    └─ form#search-page-filters-form
  │         └─ aside.hdx-v2-search-filters   (sidebar — hidden below XL)
  └─ primary_content block
       └─ search/snippets/search_results_wrapper.html
            ├─ search/snippets/package_list.html
            │    ├─ div.hdx-v2-list-header        (title + count + sort at XL)
            │    ├─ form.hdx-v2-search-bar-row     (search input)
            │    ├─ div.hdx-v2-search-filter-overlay  (fixed full-screen — MD/SM)
            │    └─ div#search-page-results
            │         └─ div.hdx-v2-dataset-list
            │              └─ div.hdx-v2-dataset-list__cards
            └─ div.hdx-v2-pagination-row
```

### v2/page.html scaffolding (current)

```html
<div id="content" class="hdx-v2-container">         <!-- 1rem→3rem padding, max 1320px -->
  <div class="toolbarRow">…breadcrumb…</div>
  <div class="dataset-light">…flash…</div>
  <div>
    <div class="[no-nav when secondary empty]">      <!-- v1 remnant, no v2 semantics -->
      <div class="hdx-v2-content-columns">           <!-- flex row — defined in page.html -->
        <div class="hdx-v2-search-sidebar wrapper-secondary">…sidebar…</div>
        <div class="hdx-v2-search-content wrapper-primary">…content…</div>
      </div>
    </div>
  </div>
</div>
```

Legacy `container mainContent` / `hdx-wrapper wrapper` / `contentBackground` removed. When `secondary_content` is empty, `no-nav` is added to the anonymous wrapper div (v1 remnant, no v2 semantics).

### Current CSS

| File | Class | Value |
|---|---|---|
| `v2/search.less` | `.hdx-v2-search-layout` | `display:flex; gap:24px; align-items:flex-start` |
| `v2/search.less` | `.hdx-v2-search-filters` (inside layout) | `flex-shrink:0; width:15rem (240px)` at ≥1280px; `display:none` at <1280px |
| `v2/layout.less` | `.hdx-v2-container` | SM: 1rem padding; MD+: 3rem padding; XXL: max-width 1320px |
| `v2/search.less` | `.hdx-v2-pagination-row` | `display:flex; justify-content:center; margin-top:32px` |

### Structural problems

1. `hdx-v2-list-header` and `hdx-v2-search-bar-row` are **outside** the two-column layout — span full container width at XL instead of living inside the content column
2. `hdx-v2-pagination-row` also outside (in wrapper snippet after package_list)
3. Sidebar width is **240px (`15rem`)** — Figma specifies 350px (`21.875rem`)
4. **24px gap** between sidebar and content — Figma: 0 gap + `border-right` separator
5. **No `border-right`** on sidebar — Figma: `1px solid #ebeff0`
6. `#search-page-results` has Bootstrap class `col-9` — meaningless in v2 flex context
7. Sidebar does not stretch to full height of content area

---

## 2. v2 Layout System Audit

### page.html regions

- **`secondary` block**: renders `<div class="[wrapper_secondary_class] wrapper-secondary">` when non-empty; placed left of primary
- **`primary` block**: renders `<div class="[wrapper_primary_class] wrapper-primary">`; always rendered
- **`wrapper_secondary_class` / `wrapper_primary_class`**: template variables set in the child template (before block definitions) that inject extra CSS classes onto the wrappers
- **`wrapper_class` block**: adds extra class to the outer `<div class="hdx-wrapper wrapper …">` — used for page-level CSS scoping

### Relevant design tokens

```less
@hdx-bp-md:  48rem;     // 768px
@hdx-bp-xl:  80rem;     // 1280px
@hdx-bp-xxl: 87.5rem;   // 1400px

@hdx-space-5:  1.25rem; // 20px
@hdx-space-6:  1.5rem;  // 24px
@hdx-space-8:  2rem;    // 32px
@hdx-space-10: 2.5rem;  // 40px
@hdx-space-12: 3rem;    // 48px

var(--hdx-neutral-2)    // #ebeff0  (whitesmoke — sidebar border)
```

---

## 3. Figma Analysis

**Files:** `llm_docs/redesign/figma_exports/dataset-results-{xl,md,sm}.html`

### XL layout structure

```
.dataset-results  {display:flex; align-items:flex-start; justify-content:space-between}
  ├─ .sidebar           {align-self:stretch; padding-top: 1.25rem}
  │    └─ .filter-no-scroll
  │         width: 21.875rem (350px)
  │         padding: 1.25rem 2.5rem 5rem 3rem   (t:20px r:40px b:80px l:48px)
  │         border-right: 1px solid #ebeff0
  │         display:flex; flex-direction:column; gap:1.5rem
  └─ .dataset-lists     {width: 58.125rem (930px); flex-direction:column}
       └─ .header-parent
            padding: 2.5rem 3rem 2.5rem 2.5rem  (t:40px r:48px b:40px l:40px)
            gap: 1.5rem
            contains: title + count row, sort controls, search bar
       └─ [dataset cards area]
       └─ .pagination
```

Total XL frame width: 350 + 930 = 1280px (Figma XL frame at full viewport width).

**No gap** between sidebar and content — visual separation from `border-right` only.

### MD layout

- Sidebar **absent** from DOM
- `.dataset-lists` width: `49.5rem` (792px)
- Content padding: `2rem 3rem` (32px top/bottom, 48px sides)
- Filter button visible in header (already implemented)

### SM layout

- Sidebar **absent** from DOM
- Full-width wrapper: `padding: 1.5rem 1rem; flex-direction:column; gap:1.5rem`

### Responsive summary

| Breakpoint | Sidebar | Layout | `hdx-v2-container` padding |
|---|---|---|---|
| SM < 768px | Hidden (overlay) | 1-column | 1rem sides |
| MD 768–1280px | Hidden (overlay) | 1-column | 3rem sides |
| XL ≥ 1280px | Visible left 350px | 2-column flex | 3rem sides |
| XXL ≥ 1400px | Visible left 350px | 2-column flex | max-w 1320px, 12px sides |

---

## 4. Gap Analysis

| Aspect | Current | Figma | Action |
|---|---|---|---|
| Sidebar width | 240px (15rem) | 350px (21.875rem) | **Update** |
| Sidebar–content gap | 24px | 0 | **Remove gap** |
| Sidebar separator | None | `border-right: 1px solid #ebeff0` | **Add** |
| Sidebar height | `align-items:flex-start` | `align-self:stretch` | **Update** |
| Sidebar padding | None | `1.25rem 2.5rem 5rem 3rem` | **Add** |
| Header position | Full-width above 2-col | Inside content column | **Fix** (structural) |
| Search bar position | Full-width above 2-col | Inside content column | **Fix** (structural) |
| Pagination position | Full-width below 2-col | Inside content column | **Fix** (structural) |
| Results column class | `col-9` (Bootstrap) | — | **Remove** |

---

## 5. Architecture: Use page.html primary/secondary

Sidebar moves to the `secondary` block. page.html already handles the two-column split when secondary is non-empty.

### New structure

```
v2/page.html
    wrapper-secondary.hdx-v2-search-sidebar   ← SIDEBAR (search.html secondary block)
    wrapper-primary.hdx-v2-search-content     ← CONTENT (primary_content block)
      hdx-v2-list-header
      hdx-v2-search-bar-row
      hdx-v2-search-filter-overlay (fixed-position, stays here)
      hdx-v2-dataset-list
        hdx-v2-dataset-list__cards
      hdx-v2-pagination-row
```

`hdx-v2-search-layout` is removed entirely.

---

## 6. Implementation Plan

### Files to change

| File | Change |
|---|---|
| `ckanext-hdx_theme/.../templates/search/search.html` | Add `secondary` block with sidebar form; set `sidebar_class`, `content_class` |
| `ckanext-hdx_theme/.../templates/search/snippets/package_list.html` | Remove `hdx-v2-search-layout` div and its sidebar form; remove `col-9` from results wrapper |
| `ckanext-hdx_theme/.../hdx-styles/src/common/less/v2/search.less` | Remove `hdx-v2-search-layout`; add `hdx-v2-search-sidebar`, `hdx-v2-search-content` rules; update sidebar width variable |

---

### 6a. `search/search.html` changes

Add before any block definitions:

```jinja2
{% set sidebar_class = 'hdx-v2-search-sidebar' %}
{% set content_class = 'hdx-v2-search-content' %}
```

Add secondary block with sidebar filters:

```jinja2
{% block secondary %}
  <form id="search-page-filters-form" autocomplete="off">
    <aside class="hdx-v2-search-filters">
      {% snippet 'v2/search-filters.html',
          facet_list=(data or c).full_facet_info.get('facets', {}) %}
      {% set ext_after_metadata_modified = h.hdx_get_request_param('ext_after_metadata_modified', None) %}
      {% if ext_after_metadata_modified %}
        <input id="ext_after_metadata_modified" type="hidden"
               name="ext_after_metadata_modified" value="{{ ext_after_metadata_modified }}"/>
      {% endif %}
      {% set ext_batch = h.hdx_get_request_param('ext_batch', None) %}
      {% if ext_batch %}
        <input id="ext_batch" type="hidden" name="ext_batch" value="{{ ext_batch }}"/>
      {% endif %}
    </aside>
  </form>
{% endblock %}
```

`primary_content` block is unchanged.

---

### 6b. `package_list.html` v2 block changes

**Remove** the `hdx-v2-search-layout` opening div and its sidebar form (current lines 177–190):

```html
{# REMOVE THIS BLOCK: #}
<div class="hdx-v2-search-layout">
  <form id="search-page-filters-form" autocomplete="off">
    <aside class="hdx-v2-search-filters">
      ...
    </aside>
  </form>
```

**Remove** the matching closing `</div>` at line 274 (which closes `hdx-v2-search-layout`).

**Update** the results wrapper (line 215) to remove Bootstrap `col-9`:

```jinja2
{# Before: #}
<div id="search-page-results" class="col-9">

{# After: #}
{% if v2 %}<div id="search-page-results">{% else %}<div id="search-page-results" class="col-9">{% endif %}
```

And the corresponding close tag:

```jinja2
{% if v2 %}</div>{% else %}</div>{% endif %}
```

(Or simply `</div>` since the close tag is identical — only the open tag needs the conditional.)

---

### 6c. `search.less` CSS changes

**Remove** the `hdx-v2-search-layout` block (lines 137–165). The `.hdx-v2-dataset-list { flex:1 }` rule nested inside it moves to the new `.hdx-v2-search-content` block.

**Update** sidebar width variable:

```less
@hdx-v2-sf-sidebar-width: 21.875rem;  // 350px — was 15rem (240px)
```

**Add** after the removed block:

```less
// ────────────────────────────────────────────────────────
// hdx-v2-search-sidebar — sidebar column
// Applied via sidebar_class in search/search.html
// ────────────────────────────────────────────────────────

.hdx-v2-search-sidebar {
    @media (min-width: @hdx-bp-xl) {
        flex-shrink:  0;
        width:        @hdx-v2-sf-sidebar-width;          // 350px
        border-right: 1px solid var(--hdx-neutral-2);   // #ebeff0
        padding:      var(--hdx-space-5)                 // 20px top
                      var(--hdx-space-10)                // 40px right
                      5rem                               // 80px bottom (Figma)
                      var(--hdx-space-12);               // 48px left
    }

    @media (max-width: @hdx-bp-xl) {
        display: none;
    }
}


// ────────────────────────────────────────────────────────
// hdx-v2-search-content — content column (wrapper-primary)
// Applied via wrapper_primary_class in search/search.html
// ────────────────────────────────────────────────────────

.hdx-v2-search-content {
    flex:      1;
    min-width: 0;   // prevent flex blowout

    .hdx-v2-dataset-list {
        flex:      1;
        min-width: 0;
    }
}
```

---

## 7. Responsive Behavior

### XL (≥ 1280px)
- Sidebar visible: `width: 21.875rem`, `border-right`, full-height stretch
- Content: `flex: 1`, fills remaining width
- Header (title + count + sort), search bar, cards, and pagination all inside content column

### MD (768–1280px)
- Sidebar: `display: none`
- Content: full width
- Filter button visible in `hdx-v2-list-header__filter-btn` (existing)
- Filter overlay triggered by filter button (existing)

### SM (< 768px)
- Same as MD: sidebar hidden, single column
- `hdx-v2-container` provides `1rem` side padding

---

## 8. Background & Spacing

### Backgrounds
- Page, sidebar, and content area: all white (inherit from body)
- No distinct background separation — sidebar and content divided by `border-right` only

### Key spacing values

| Element | Property | Token / Value |
|---|---|---|
| Sidebar padding top | `padding-top` | `@hdx-space-5` (20px) |
| Sidebar padding right | `padding-right` | `@hdx-space-10` (40px) |
| Sidebar padding bottom | `padding-bottom` | `5rem` (80px) — verify visually |
| Sidebar padding left | `padding-left` | `@hdx-space-12` (48px) |
| Sidebar filter item gap | `gap` | `@hdx-space-6` (24px) — existing |
| Pagination margin-top | `margin-top` | `@hdx-space-8` (32px) — existing |
| Pagination margin-bottom | `margin-bottom` | `@hdx-space-10` (40px) — existing |

⚠️ **Container padding stacking**: At XL, `hdx-v2-container` applies `3rem` side padding and the Bootstrap `.container.mainContent` inside it may add its own padding. Verify the rendered output and add overrides if double-padding occurs.

---

## 9. Legacy Page Wrappers

The following v1-era wrappers have been **removed** from `v2/page.html`:

- `container mainContent` (Bootstrap) — removed; `hdx-v2-container` handles max-width and padding
- `hdx-wrapper wrapper` — removed
- `contentBackground` — removed

Remaining v1 remnants (no active CSS depending on them in v2):

- Anonymous `<div class="[no-nav …]">` wrapping `hdx-v2-content-columns` — cleanup deferred
- `wrapper-primary` / `wrapper-secondary` token classes — kept as DOM hooks; actual sizing via `hdx-v2-search-sidebar` / `hdx-v2-search-content`

---

## 10. Decisions Taken

1. **`secondary_content` facet data**: `(data or c).full_facet_info` is available at template level before the secondary block renders — no timing issue.

2. **Sidebar bottom padding (5rem)**: Intentional — prevents the last filter item from appearing clipped at the bottom of a long viewport.

3. **`hdx-v2-search-page` scoping class**: Not implemented. `hdx-v2-content-columns` in page.html is the flex container; sidebar and content rules nest under it in `search.less`. No need for an additional scoping class.

4. **`@hdx-v2-sf-sidebar-width` references**: No other references to this variable exist (overlay width is not derived from it).

5. **`no-nav` on anonymous wrapper div**: Left as-is — it's a v1 remnant in page.html with no active v2 CSS depending on it. Removing it is a separate cleanup task.

6. **Content column right padding**: Currently 0 (right padding relies on `hdx-v2-container`). Acceptable — no additional right padding needed.

