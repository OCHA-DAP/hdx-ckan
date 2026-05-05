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

1. **Branding** (`__branding`) — HDX logo (lazy-loaded), tagline, MailChimp newsletter form, GitHub + LinkedIn social links, "Related to" external link.
2. **Navigation grid** (`__nav`) — three columns: Data, Products, Resources. Internal links use `{% snippet 'v2/components/text-link.html' %}`. External links (Open source, Blog, Contact, Centre for Humanitarian Data) are written as raw `<a>` elements carrying `c-text-link` classes plus `hdx-v2-footer__ext-link` to inline the SVG icon inside the anchor. All links carry `data-module="hdx_click_stopper"` and `data-module-link_type="footer"`.
3. **Divider** (`__divider`) — 1px white `<hr>`.
4. **Bottom bar** (`__bottom`) — OCHA service block (logo + description), CC license icon + text, Terms of service + Privacy policy links.

Key decisions:
- X/Twitter removed (Figma intentional).
- Version string (`hdx_version()`) removed.
- Cookie consent banner excluded (handled separately).
- Subscribe button: `<button type="submit">` with `hdx-v2-footer__subscribe-btn` modifier (ghost variant scoped to footer.less, not a new `c-button` style).
- Email input: native `<input type="email">` — preserves MailChimp JS hooks (`id="mce-EMAIL"`, `name="EMAIL"`).
- "Archived" in Products rendered as `{% snippet 'v2/components/label.html' %}` badge (not a link).
- Dataviz Gallery & HDX Dataviz Guidelines: present in DOM with `style="display:none"` (Figma spec, future activation).
- MD/SM Figma duplication of "Centre for Humanitarian Data" in Resources column omitted; already in "Related to" row (follows XL pattern).

### `hdx-styles/src/common/less/v2/footer.less` (new file)

BEM block `.hdx-v2-footer`. Local tokens: `@hdx-footer-bg: #0b2d24`, `@hdx-footer-bp-md: 48rem`, `@hdx-footer-bp-xl: 80rem`.

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

## Open items

| # | Item                 | Notes                                          |
|---|----------------------|------------------------------------------------|
| 1 | Privacy policy URL   | Using `#` placeholder                          |
| 2 | Documentation URL    | Using `#` placeholder                          |
| 3 | Data column URLs     | Explore data / Locations / Organisations — `#` |
| 4 | Products column URLs | All 5 active product links — `#`               |

## Why

The existing footer uses a Bootstrap grid with two hardcoded background sections and a flat link row. The v2 design uses a single dark-teal background, a structured nav grid with Merriweather bold headings, and a cleaner bottom bar. All `hdx_click_stopper` analytics are preserved. The implementation is self-contained: no new shared components, no changes to existing LESS files outside this block.
