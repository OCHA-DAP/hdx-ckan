/**
 * location-page.js
 *
 * Location (single-country/group) page — Data Grid Availability (task 063):
 *   - Global expand/collapse toggle (rendered twice — next to the title on
 *     SM/MD, next to the chart on XL, only one visible at a time — both
 *     driven together) that forces every category card's native <details>
 *     open/closed at once. Per-card expand/collapse is handled by the
 *     browser itself (each card is a <details>/<summary>, task 063 round 4)
 *     and isn't tracked here; the global toggle always forces all cards to
 *     the same state rather than reading back any mixed per-card state.
 *   - Definitions drawer jump-nav scroll wiring, scoped to the drawer's own
 *     internal scroll container (not the page/window).
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initExpandCollapse();
        initDesktopJumpLinks();
        initStickyTopOffset();
    });

    // ── 1. Expand/collapse — global toggle(s) drive every card at once ────

    function initExpandCollapse() {
        var toggles = document.querySelectorAll('.hdx-v2-location-datagrid-section__toggle');
        if (!toggles.length) return;

        function setAll(nextOpen) {
            document.querySelectorAll('[data-datagrid-details]').forEach(function (details) {
                details.open = nextOpen;
            });
            toggles.forEach(function (toggle) {
                toggle.setAttribute('aria-expanded', String(nextOpen));
                var label = toggle.querySelector('.c-text-button__label');
                if (label) label.textContent = nextOpen ? 'Show less' : 'Show more';
            });
        }

        toggles.forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                setAll(toggle.getAttribute('aria-expanded') !== 'true');
            });
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
