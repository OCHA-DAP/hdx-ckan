# Task 015: Implement v2 footer

Implement the redesigned footer in `v2/footer.html` as part of the `hdx-v2` page layout. Replaces the legacy two-section dark template with a single dark-teal panel matching the Figma design.

**Figma source:** `llm_docs/redesign/figma_exports/footer.html`

## Responsive breakpoints

| Label | Range         | Padding       | Layout                                                    |
|-------|---------------|---------------|-----------------------------------------------------------|
| SM    | < 48rem       | `3.5rem 1rem` | Fully stacked                                             |
| MD    | 48rem – 79rem | `4rem 3rem`   | Newsletter + social on same row; nav columns side by side |
| XL    | ≥ 80rem       | `5rem 3rem`   | Two-column: branding left / nav grid right                |

## What to update

### `templates/v2/footer.html`

Full implementation. Four sections:

1. **Branding** (`__branding`) — HDX logo (lazy-loaded), tagline, MailChimp newsletter form, GitHub + LinkedIn social links. (The "Related to" external link that used to sit here is commented out — see below.)
2. **Navigation grid** (`__nav`) — three columns: Data, Products, Resources. Internal links use `{% snippet 'v2/components/text-link.html' %}`. External links (Open source, Blog, Contact) are written as raw `<a>` elements carrying `c-text-link` classes plus `hdx-v2-footer__ext-link` to inline the SVG icon inside the anchor. All links carry `data-module="hdx_click_stopper"` and `data-module-link_type="footer"`.
3. **Divider** (`__divider`) — 1px white `<hr>`.
4. **Bottom bar** (`__bottom`) — OCHA service block (logo + description), CC license icon + text, Terms of service + Privacy policy links.

Key decisions:
- X/Twitter removed (Figma intentional).
- Version string (`hdx_version()`) removed.
- Cookie consent banner excluded (handled separately).
- Subscribe button: `<button type="submit">` with `hdx-v2-footer__subscribe-btn` modifier (ghost variant scoped to footer.less, not a new `c-button` style).
- Email input: native `<input type="email">` — preserves MailChimp JS hooks (`id="mce-EMAIL"`, `name="EMAIL"`).
- Archived items excluded from the Products column entirely (`h.hdx_get_quick_links_list(archived=False, exclude_crisis=True)`), not rendered as a badge.
- Dataviz Gallery & HDX Dataviz Guidelines: shown unconditionally, not gated behind `display:none`.
- The `__related` block ("Related to" / "Centre for Humanitarian Data" link) is commented out — "Centre for Humanitarian Data" no longer appears as a standalone link anywhere in the footer (the MD/SM Figma duplication in the Resources column was already omitted on the grounds it was covered by this row; that row is now gone too).

### `hdx-styles/src/common/less/v2/footer.less` (new file)

BEM block `.hdx-v2-footer`. Uses shared tokens (`var(--hdx-brand-85)`) and shared breakpoints from `mixins.less` — no local LESS variables declared.

Elements: `__top`, `__branding`, `__logo-wrap`, `__logo`, `__tagline`, `__actions`, `__newsletter`, `__newsletter-label`, `__newsletter-row`, `__email-input`, `__subscribe-btn`, `__social`, `__social-link`, `__social-icon`, `__social-label`, `__related`, `__related-label`, `__ext-link`, `__ext-icon`, `__nav`, `__nav-col`, `__nav-heading`, `__nav-list`, `__divider`, `__bottom`, `__service`, `__service-label`, `__service-detail`, `__ocha-logo`, `__ocha-text`, `__license`, `__license-icon`, `__license-text`, `__legal`.

Scoped override: `.hdx-v2-footer .c-text-link { color: var(--hdx-neutral-0) }` — white text on dark background.

### `fanstatic/v2/footer.css` (new file — compiled from footer.less)

### `fanstatic/webassets.yml`

Add `v2/footer.css` to `v2-page-styles` after `v2/layout.css`:

```yaml
v2-page-styles:
  contents:
    - vendor/bootstrap5/css/bootstrap.css
    - v2/layout.css
    - v2/footer.css
```

## Decisions Taken

| # | Question | Decision |
|---|----------|----------|
| 1 | Privacy policy URL | `https://docs.humdata.org/about/hdx-terms-of-service#privacy-notice` |
| 2 | Documentation URL | `https://docs.humdata.org` |
| 3 | Data column URLs | Resolved to real CKAN routes: `h.url_for('dataset.search')`, `h.url_for('group.index')`, `h.url_for('organization.index')` |
| 4 | Products column URLs | Driven by `h.hdx_get_quick_links_list(archived=False)` helper — real URLs from the quick-links registry, no hardcoded placeholders |

## Why

The existing footer uses a Bootstrap grid with two hardcoded background sections and a flat link row. The v2 design uses a single dark-teal background, a structured nav grid with Merriweather bold headings, and a cleaner bottom bar. All `hdx_click_stopper` analytics are preserved. The implementation is self-contained: no new shared components, no changes to existing LESS files outside this block.
