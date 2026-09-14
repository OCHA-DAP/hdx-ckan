# 062 — Error Pages (404, 5xx, Planned Maintenance) v2

**Scope:** Document and implement the v2 redesign of the 404 page, the 5xx server-error page, and
the standalone planned-maintenance page. `planned-maintenance.html` ships as a standalone static
file, since that page has a different deployment story (served by infra outside this repo,
independent of the CKAN app). The 404/5xx pages are implemented in `error_document_template.html`
(see §4).
**Excluded:** backend error-handling logic (Flask error-handler registration, HTTP status-code
routing); any change to `ckan/config/middleware/flask_app.py`; any nginx/infra config outside this
repo.
**Figma sources:** `xl-404.html`, `xl-server-error.html`, `xl-planned-maintenance.html`,
`sm-404.html`, `sm-server-error.html`, `sm-planned-maintenance.html`

---

## Context

Design has produced v2 mockups for three error states — 404, a generic server error, and a planned
maintenance page — at both XL and SM breakpoints. None of these are wired into any template, route,
or build step yet. Today, 404/403/500 all render through a single legacy template that inherits the
full v1 page chrome (header, footer, search styles, onboarding widgets, the entire site JS bundle) —
the opposite of what an error page needs. No maintenance-mode mechanism exists at all.

The planned-maintenance page is a special case: it must work as a single, self-contained static
file, servable independently of CKAN (potentially while the app itself is down), by infrastructure
that lives outside this repo. Everything else here — the 404/5xx redesign — follows the same
numbered-doc, audit-then-decide process as prior v2 tasks.

Decisions confirmed with the requester are listed in §10.

---

## 1. Existing Implementation Audit

### Current 404/5xx template — one file, no dedicated 503 handling

- `ckanext-hdx_theme/ckanext/hdx_theme/templates/error_document_template.html` overrides CKAN
  core's `ckan/templates/error_document_template.html`. It extends `page_light.html` → `base.html`.
- Branches on `h.hdx_check_http_response(code, N)` (`ckanext-hdx_theme/ckanext/hdx_theme/plugin.py:263`)
  for exactly `404`, `403`, and `500`; every other code (**including 503**) falls into a generic
  "Something went wrong" else-branch. There is no dedicated 503/other-5xx design today.
- Shows a `hdx_bot2.gif` image, a heading/copy pair, and a single "Back to homepage" button
  (`hdx_splash.index`). No distinct visual treatment per error type beyond the copy.
- Registered dynamically in `ckan/config/middleware/flask_app.py`, `_register_error_handler`
  (~line 518-552): `app.register_error_handler(code, error_handler)` for all default exceptions,
  plus a catch-all `Exception` handler outside debug/testing. `error_handler` calls
  `base.render('error_document_template.html', extra_vars)`. This is fully server-rendered per
  request — confirms 404/5xx cannot become static files without app changes (excluded from scope).

### Inherited chrome and asset payload (the core problem this task addresses)

`page_light.html` still includes the full v1 header (`header-mobile.html`, 158 lines) and footer
(`footer-wide.html` → `footer.html`), plus:
- Styles: `page-light-styles` (preloads `page-common-styles`, `search-styles`,
  `adaptive-page-styles`) + an onboarding bulk styles bundle depending on login state.
- Scripts: `page-light-scripts` (preloads the entire `hdx_theme/ckan` bundle — jquery.slug,
  header-init.js, contribute.js — plus `hdx-show-more`) + onboarding scripts.
- `base.html` itself also loads `hdx_theme/ckan` again in its own `scripts` block, plus a hardcoded
  Font Awesome CDN `<link>` (see below).

None of this is needed for a static error message with two buttons.

### Analytics

GTM (`GTM-MFNPQ7K`) and Mixpanel are injected globally by `base.html`'s `google_analytics_init` /
`mixpanel_init` blocks (lines ~16-88, ~191-195) — inherited automatically by every page that extends
`base.html`, including today's error pages. **There is no error-specific tracking** (e.g. no "user
hit a 404" event) — just the same sitewide analytics every page gets for free.

### Maintenance mode

No functional mechanism exists anywhere in the repo. The only "maintenance" match is a comment in
the legacy `fabfile.py` (Fabric deploy script, unused by the current Docker/Unit setup) about
swapping an Apache vhost — not wired to anything live. There is no `nginx/` directory in this repo;
deployment uses **NGINX Unit** (`docker/unit.json`, `docker/unit-nr.json`, `docker/unit-elk.json`),
a simple WSGI-app listener config with no static-error-page directives.

### v2 template chain (relevant to the recommended 404/5xx approach)

- `v2/page.html` is the established base for every v2-redesigned page — `search/search.html`,
  `organization/*.html`, `package/resource_read.html`, `home/index.html`, etc. all extend it
  directly. It extends `base.html` directly (not `page_light.html`), and supplies its own
  `v2/header.html` (446 lines) / `v2/footer.html` (250 lines), Google Fonts (Merriweather +
  Roboto — the same families Figma uses here), and the `v2-page-styles`/`v2-page-scripts` asset
  bundles. `v2-page-styles` preloads `v2-components-styles`, which bundles **every** v2 component's
  CSS (accordion, activity-card, dataset-card, dropdown, checkbox, ... — dozens of files) — far more
  than an error page needs.
- Font Awesome's CDN `<link>` (`cdnjs.cloudflare.com/.../font-awesome/...`) is hardcoded directly in
  `base.html`'s `<head>`, outside any `{% block %}` (~line 177) — so every page that extends
  `base.html`, v1 or v2, pays for it. A repo-wide grep across `templates/v2/` and
  `hdx-styles/src/common/less/v2/` for `fa-`/`class="fa`/`"fas `/`"far `/`"fab ` returns **zero**
  matches: v2 does not use Font Awesome anywhere, it exclusively inlines SVGs (e.g.
  `v2/components/button.html`'s `{% include h.url_for_static(icon_src) %}` pattern, and the real
  HDX logo mark at `templates/v2/icons/hdx.svg`). No template anywhere overrides `links`/`styles` to
  drop it, and it isn't structurally possible to do so without editing `base.html` itself. **This is
  pre-existing dead weight, not something introduced or fixable by this task** — see §8.
- `c-button` (`hdx-styles/src/common/less/v2/components/buttons.less` +
  `templates/v2/components/button.html`) already maps 1:1 onto the Figma export's button colors —
  see §6.

---

## 2. Figma Mapping

All six exports share one DOM shape: a centered column of `.component-1` (the logo mark, split into
three `vector-icon`/`vector-icon2`/`vector-icon3` `<img>` slices — a Figma layer-export artifact of
the single real `hdx.svg`, not three separate assets) → heading (`<b>`) → body copy → CTA buttons.
XL renders this as an absolutely-positioned column on a full-height white page. Every SM export
additionally wraps the same content in a bordered "device-frame" box (`.home-dark` /
`.home-dark2`, `border: 1px solid black`, `border-bottom: 2px solid darkslateblue`, fixed
`24.688rem × 41.625rem`) — **confirmed Figma export scaffolding, not real page chrome, in all three
SM exports (404, server-error, maintenance)**. It must not be reproduced.

### `xl-404.html` / `sm-404.html`

```
.home-dark
├── .component-1-parent
│   ├── .component-1              ← logo (3 SVG slices)
│   └── .page-not-found-parent
│       ├── "Page not found"      ← <b>, Merriweather 700, 1.75rem XL / 1.5rem SM
│       ├── body copy (Roboto, 1rem/130%), "login" as an underlined inline link
│       └── .button-group         ← display:none, empty divs — Figma leftover, ignore
└── .button-group2                ← VISIBLE — real CTAs
    ├── "Browse Data"             ← primary, royalblue fill (#1862d8), white text
    └── "Go to homepage"          ← white bg, gainsboro border (#d8e0e1), drop shadow,
                                     darkslategray text (#3f4748)
```

Body copy (verbatim): "Sorry, the page you are looking for could not be found. Please check the
URL or **login** to HDX if you know that you have a permission to see this page."

### `xl-server-error.html` / `sm-server-error.html`

Identical structure to 404, heading "Server Error", same visible CTA pair. Body copy (verbatim):
"Sorry, there was a server error. Please check the URL, try the search or go back to our homepage"
— no inline link, plain text only.

### `xl-planned-maintenance.html` / `sm-planned-maintenance.html`

```
.home-dark (XL) / .sm-planned-maintenance (SM device-frame wrapper)
└── .component-1-parent
    ├── .component-1                              ← logo (3 SVG slices)
    └── .hdx-is-undergoing-a-planned-ma-parent
        ├── "HDX is undergoing a planned          ← <b>, Merriweather 700, 1.75rem XL / 1.5rem SM
        │    maintenance upgrade"
        ├── "We will announce on X @humdata       ← Roboto, 1rem/130%; "@humdata" medium-weight +
        │    when we are back up."                   underlined in the export — implemented as a
        │                                             real link to https://www.x.com/humdata,
        │                                             confirmed with requester (target="_blank")
        └── .button-group                         ← display:none, EMPTY child divs
```

**No visible CTA anywhere in this export** — its only `.button-group` is `display: none` with two
empty `<div>`s (no button text at all), unlike 404/server-error where the visible CTAs live in a
*separate* `.button-group2`. This maintenance export has no `.button-group2`. Confirmed: the
maintenance page is logo + heading + body copy only.

### Colors used (all three page types, verified against the exported `:root` custom properties)

| Figma variable | Hex | Matches `--hdx-*` token |
|---|---|---|
| `--color-royalblue` | `#1862d8` | `--hdx-primary-5` |
| `--color-darkslateblue` | `#0e3b82` | `--hdx-primary-7` |
| `--color-gainsboro` | `#d8e0e1` | `--hdx-neutral-2` |
| `--color-darkslategray` / `-100` | `#3f4748` | `--hdx-neutral-8` |
| `--color-darkslategray-200` (maintenance body text) | `#2f3536` | `--hdx-neutral-85` (exact match, confirmed directly against `colors.less`) |
| `--color-gray` (headings/logo) | `#101212` | `--hdx-neutral-95` |
| `--color-white` | `#fff` | `--hdx-neutral-0` |

---

## 3. Asset Strategy

**For the 404/403/Server Error pages:** `error_document_template.html` extends `v2/page.html`, so
`v2-page-styles` (which preloads `v2-components-styles` — design tokens, `buttons.css`, and every
other component's CSS) loads via the inherited `styles` block. Page-specific layout (the centered
logo/heading/body/CTA column) lives in its own small bundle, `v2-error-page-styles`
(`v2/error-page.css` only), registered in `webassets.yml`. **No JS bundle** — the page has no
interactive behavior, so `{% block scripts %}` is emptied out entirely.

**For the maintenance page:** no build pipeline involvement whatsoever — see §5.

---

## 4. Implementation Strategy

`error_document_template.html` extends `v2/page.html` directly:

- `{% block header %}` and `{% block footer %}` are emptied out — no nav chrome.
- `{% block scripts %}` is emptied out — no JS.
- `{% block styles %}` calls `{{ super() }}` (inherited fonts + `v2-page-styles`), then loads
  `v2-error-page-styles` (§3).
- `{% block main_content %}` is replaced with the centered logo/heading/body/CTA layout.
- Analytics (`google_analytics_init`/`mixpanel_init` blocks) keeps working automatically, since those
  live in `base.html` and aren't gated behind any v2/v1-specific block.
- `h.hdx_check_http_response` branches the heading/body copy: 404 gets its own copy (with a real
  `login` link to `user.login`), 403 keeps its own distinct copy, and 500/503/any other code collapse
  into a single "Server Error" copy.
- Font Awesome CDN stays inherited via `base.html` — unavoidable without editing that shared file
  (out of scope here, see §1/§8).

---

## 5. Maintenance Page Strategy

`planned-maintenance.html` (this task's deliverable) is a single, fully self-contained static file —
no CKAN template, no route, no build step, no dependency on this repo's asset pipeline:

- Inline `<style>` block only — no external stylesheet.
- Inline `<svg>` — the real `templates/v2/icons/hdx.svg` content embedded directly (three
  `fill="currentColor"` paths in one `<svg viewBox="0 0 121 40">`), not an `<img src>` reference.
- One `<link>` to Google Fonts (Merriweather 700 + Roboto 400/500) — the **only** permitted external
  network request, per the requester's explicit decision (§10).
- "@humdata" is a real link to `https://www.x.com/humdata` (`target="_blank"`, `title="X"`,
  `rel="noopener"`), per the requester — a navigable link, not a loaded external resource, so it
  doesn't conflict with the "only Google Fonts as an external request" constraint above.
- No JS, no analytics/tracking of any kind.
- One responsive file covering both XL and SM via a single CSS media-query breakpoint (heading
  1.75rem → 1.5rem, spacing adjustments) — not two separate files, and not the SM "device-frame"
  wrapper from the Figma export (confirmed scaffolding, see §2).

**Hand-off / nginx compatibility:** the actual serving infrastructure for this file lives outside
this repo (confirmed with requester — this repo only has NGINX Unit's `docker/unit.json`, not a raw
nginx config). This doc hands off the finished static file; a generic reference recipe for serving
it is included below for whoever owns that layer, not applied to anything in this repo:

```nginx
# Reference only — not part of this repo's deploy config.
# Example: serve a static maintenance page and 503 everything else while it's toggled on.
location / {
    if (-f /path/to/maintenance.flag) {
        return 503;
    }
}
error_page 503 /planned-maintenance.html;
location = /planned-maintenance.html {
    root /path/to/static;
    internal;
}
```

---

## 6. Component Usage

**Reuse:**
- `c-button` styling values — `--hdx-primary-5`/`--hdx-primary-7`/`--hdx-neutral-2`/`--hdx-neutral-8`
  already match the Figma export's button colors exactly (§2 table). "Browse Data" maps to
  `c-button--primary`; "Go to homepage" maps to `c-button--tertiary` (white bg, `--hdx-neutral-2`
  border, `--hdx-neutral-8` text, `--hdx-shadow-sm`) — **not** `c-button--secondary`, which uses a
  royalblue border and darkslateblue text that don't match this export's gainsboro border /
  darkslategray text. Both use `size='l'` — the closest c-button size match to Figma's font-size and
  padding.
- `--hdx-*` typography and color tokens generally.
- The real `hdx.svg` logo mark (§1) instead of recreating Figma's three-slice image artifact.

**Avoid:**
- `v2/header.html`, `v2/footer.html` — full nav chrome, not needed (blocks emptied out).
- Font Awesome — already unused dead weight sitewide; this task does not add a new dependency on it,
  and does not attempt to remove the inherited one either (out of scope, needs a `base.html` change).
- Any JS bundle — nothing on any of the three pages is interactive.

---

## 7. Responsive Strategy

| Aspect | XL | SM |
|---|---|---|
| Layout | Flex column, centered, full-viewport-height page | Same, natural content height |
| Logo + heading + body | Same DOM, same gap spacing (2.5rem XL / 1.5rem SM between logo and text block) | Same |
| Heading size | 1.75rem | 1.5rem |
| Body size | 1rem (unchanged) | 1rem (unchanged) |
| CTA buttons | Side-by-side | Side-by-side (Figma does not stack at SM) |
| SM "device-frame" border/box | N/A | Present in the Figma export — **confirmed scaffolding, do not reproduce** |

One markup structure, one breakpoint-driven stylesheet for all three page types — no separate SM
template/file.

---

## 8. Risks

| Risk | Detail | Mitigation |
|---|---|---|
| Font Awesome CDN is inherited, unfixable-here dead weight | Confirmed unused by any v2 page, hardcoded in `base.html` outside any block (§1) | Out of scope for this task (editing `base.html` is a shared, sitewide file); flagged here for future cleanup awareness, not silently ignored |
| 503 (and any other unhandled code) has no dedicated Figma design | Figma only exports one "Server Error" mockup; current code's `h.hdx_check_http_response` only special-cases exactly `500` | Confirmed with requester: 503 and any other unhandled code collapse into the same "Server Error" template as 500 — §4's proposal is final |
| Maintenance page hand-off | The real serving infra (nginx or equivalent) isn't visible from this repo, so the recipe in §5 is generic reference, not a verified working config | Confirmed with requester as the correct scope boundary; the static file itself is the deliverable, not the infra wiring |

---

## 9. Edge Cases

| Case | Handling |
|---|---|
| Long/localized error copy | Body copy wraps naturally in a `flex-direction: column` centered block — no fixed-width truncation in any export |
| No-JS environment | Already satisfied — no page in this task loads or needs any JS |
| Slow network / partial CSS load | Maintenance page: fully inlined CSS, nothing to partially load. 404/403/Server Error pages: depend on `v2-page-styles`/`v2-error-page-styles` loading like any other v2 page; a FOUC is possible but no worse than on any other v2 page |
| Google Fonts request fails/blocked | Figma's `font-family` stacks already include system fallbacks (`Merriweather, Arial, sans-serif` / `Roboto, Arial, sans-serif`) — degrades gracefully to Arial/sans-serif, no layout break |
| Maintenance page served while the app is fully down | By design, has zero dependency on CKAN, the database, or any app process — a static file only depends on whatever serves it |

---

## 10. Decisions Taken

1. **Task scope.** This task delivers this requirements doc, the standalone
   `planned-maintenance.html` draft, and the 404/403/Server Error implementation in
   `error_document_template.html` + `webassets.yml`. `flask_app.py` is not modified —
   error-handler registration and status-code routing are out of scope.
2. **404/403/Server Error base template.** `error_document_template.html` extends `v2/page.html`
   directly, with the `header`/`footer`/`scripts` blocks emptied out. Font Awesome's CDN link
   remains inherited from `base.html` and is explicitly not addressed by this task.
3. **Maintenance page hand-off.** The real serving infrastructure lives entirely outside this repo
   (confirmed: this repo only has NGINX Unit's `docker/unit.json`, no raw nginx config). This doc
   hands off the finished static file with a generic nginx recipe (§5) as reference only.
4. **Maintenance page constraints.** Fully self-contained: inline `<style>`, inline SVG logo, one
   responsive file for both breakpoints via a media query, zero analytics/tracking. The only
   permitted external network request is the Google Fonts stylesheet link.
5. **503/other unhandled codes.** Collapse into the same "Server Error" template as 500 — §4's
   proposal is final, not left open for the follow-up implementation task to reconsider.
6. **`--color-darkslategray-200` token match.** `#2f3536` is an exact match for `--hdx-neutral-85`
   (confirmed directly against `colors.less`), not an approximation in the neutral-9 range — §2/§8
   corrected accordingly. Body copy uses `--hdx-neutral-85` on all three page types, at every
   breakpoint.
7. **403 handling.** Keeps its own distinct copy — only 500/503/any other unhandled code collapse
   into the "Server Error" copy.
8. **404 "login" text.** A real link to `user.login` (plain, no `came_from` redirect-back).

---

## Constraints (carried forward)

- No full header/footer nav chrome on any of the three error pages
- No JS on any of the three error pages, matching §3/§4
- Maintenance page must remain a single, self-contained `.html` file with no external dependencies
  beyond the Google Fonts request
- `--hdx-*` design tokens and BEM `c-*` component conventions wherever tokens/components are reused
- Must match Figma exactly — see §2 for verified copy, structure, and the hidden-vs-visible
  button-group distinction
