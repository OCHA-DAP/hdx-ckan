/**
 * location-page.js
 *
 * Location (single-country/group) page — Data Grid Availability (task 063):
 *   - The category grid itself is a native <details>/<summary> reveal
 *     ([data-datagrid-reveal]), hidden until "Show more" is clicked, so it
 *     stays reachable with JavaScript disabled. Its `toggle` event (fires on
 *     both a native click and a scripted `.open` change) forces every
 *     category card's own native <details> open/closed at once, in step
 *     with the reveal. Per-card expand/collapse is otherwise handled by the
 *     browser itself (each card is a <details>/<summary>, task 063 round 4)
 *     and isn't tracked here.
 *   - Per-card click-to-expand is desktop-disabled (>= @hdx-bp-md, 48rem):
 *     only the reveal toggle above works there. Below that width, per-card
 *     click/keyboard toggling stays native and untouched.
 *   - Definitions drawer jump-nav scroll wiring, scoped to the drawer's own
 *     internal scroll container (not the page/window).
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initExpandCollapse();
        initDesktopCardClickDisable();
        initDesktopJumpLinks();
        initStickyTopOffset();
    });

    // ── 1. Expand/collapse — the reveal's native `toggle` event drives
    // every category card at once. Listening on `toggle` (not `click`)
    // means this fires the same way whether the reveal was opened by a
    // real click/keyboard activation on its <summary> or a no-JS browser
    // handling the native disclosure itself — one code path either way.

    function initExpandCollapse() {
        var reveal = document.querySelector('[data-datagrid-reveal]');
        if (!reveal) return;

        var label = reveal.querySelector('.c-text-button__label');

        reveal.addEventListener('toggle', function () {
            var nextOpen = reveal.open;
            document.querySelectorAll('[data-datagrid-details]').forEach(function (details) {
                details.open = nextOpen;
            });
            if (label) label.textContent = nextOpen ? 'Show less' : 'Show more';
        });
    }

    // ── 1b. Per-card click disabled on desktop (>= @hdx-bp-md, 48rem) ─────
    // Same click event covers both a mouse click and a keyboard-triggered
    // one (Enter/Space on a focused <summary>), so preventDefault() on it
    // blocks the native <details> toggle for both. tabindex is toggled
    // alongside it so a disabled card isn't a dead stop in the tab order.
    // Listener is capture-phase (not bubble) so it runs before any inner
    // element's own click handler — e.g. tooltip.js's handler on the card
    // title (.c-tooltip-trigger) calls stopPropagation(), which would
    // otherwise stop a bubble-phase listener on the summary from ever
    // firing when the click lands on the title.

    function initDesktopCardClickDisable() {
        var summaries = document.querySelectorAll('.hdx-v2-location-datagrid-card__summary');
        if (!summaries.length || !window.matchMedia) return;

        var mql = window.matchMedia('(min-width: 48rem)');

        function apply(isDesktop) {
            summaries.forEach(function (summary) {
                if (isDesktop) {
                    summary.setAttribute('tabindex', '-1');
                } else {
                    summary.removeAttribute('tabindex');
                }
            });
        }

        summaries.forEach(function (summary) {
            summary.addEventListener('click', function (e) {
                if (mql.matches) e.preventDefault();
            }, true); // capture phase — runs before tooltip.js's stopPropagation() on inner triggers
        });

        apply(mql.matches);
        mql.addEventListener('change', function (e) {
            apply(e.matches);
        });
    }

    // ── 2. Drawer jump-nav — scrolls within the drawer, not the window ────

    function scrollWithinDrawer(target) {
        if (!target) return;
        var container = document.querySelector('#location-datagrid-drawer .c-drawer__container');
        if (!container) return;
        var stickyTop = container.querySelector('.hdx-v2-location-datagrid-drawer__sticky-top');
        var extraOffset = stickyTop
            ? stickyTop.getBoundingClientRect().bottom - container.getBoundingClientRect().top
            : 0;
        window.hdxSmoothScrollTo(target, container, extraOffset);
    }

    // ── 3. Sticky sub-header offset — measures the drawer's own title bar
    // height so the sticky-top block (intro + jump-nav) can sit right below
    // it without overlapping, via a self-contained observer (no drawer.js
    // changes) since the drawer is display:none until it opens.

    function initStickyTopOffset() {
        var drawer = document.getElementById('location-datagrid-drawer');
        if (!drawer) return;

        function measure() {
            var container = drawer.querySelector('.c-drawer__container');
            var header = container && container.querySelector('.c-drawer__header');
            if (container && header) {
                container.style.setProperty('--drawer-header-height', header.offsetHeight + 'px');
            }
        }

        if (drawer.classList.contains('is-open')) measure();

        new MutationObserver(function () {
            if (drawer.classList.contains('is-open')) measure();
        }).observe(drawer, { attributes: true, attributeFilter: ['class'] });
    }

    // Desktop per-category text-button links (plain <a href="#...">, not
    // .c-anchor-links__item, so anchor-links.js's own delegated handler
    // never matches these — no conflict, no capture-phase needed here).
    function initDesktopJumpLinks() {
        document.addEventListener('click', function (e) {
            var link = e.target.closest('.hdx-v2-location-datagrid-drawer__jump-link');
            if (!link) return;
            var href = link.getAttribute('href');
            if (!href || href.charAt(0) !== '#') return;
            var target = document.getElementById(href.slice(1));
            if (!target) return;
            e.preventDefault();
            scrollWithinDrawer(target);
        });
    }

    // SM mobile dropdown reuses c-anchor-links-mobile (anchor-links.html,
    // mobile_only=True). anchor-links.js's own bubble-phase document click
    // handler matches .c-anchor-links-mobile__item globally and would
    // window.scrollTo() to the target — wrong here, since the drawer scrolls
    // internally. A capture-phase listener scoped to the drawer runs first
    // and stops the event from ever reaching that bubble-phase handler.
    document.addEventListener('click', function (e) {
        var item = e.target.closest('#location-datagrid-drawer .c-anchor-links-mobile__item');
        if (!item) return;
        var href = item.getAttribute('href');
        if (!href || href.charAt(0) !== '#') return;
        e.preventDefault();
        e.stopPropagation();
        scrollWithinDrawer(document.getElementById(href.slice(1)));
        window.hdxCloseAnchorDropdown();
    }, true);

})();
