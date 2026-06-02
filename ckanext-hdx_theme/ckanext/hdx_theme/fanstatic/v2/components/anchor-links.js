/**
 * anchor-links.js
 *
 * Behaviour for the c-anchor-links component:
 *   - Smooth scroll on anchor-link click (500ms, easeInOutCubic)
 *   - Mobile anchor-nav dropdown toggle
 *   - Active-section tracking via IntersectionObserver
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initSmoothScroll();
        initAnchorDropdown();
        initActiveTracking();
    });

    // ── Easing ──────────────────────────────────────────────────

    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    // ── Smooth scroll ────────────────────────────────────────────
    // Offset is read from the target's CSS scroll-margin-top so the same
    // value governs both native anchor navigation and smooth scroll.

    function smoothScrollTo(target) {
        // Respect the user's motion preference (V-10 / C-07)
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            target.scrollIntoView({ block: 'start' });
            return;
        }

        var start        = window.scrollY;
        var targetTop    = target.getBoundingClientRect().top + window.scrollY;
        var scrollMargin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0;
        var destination  = Math.max(0, targetTop - scrollMargin);
        var distance     = destination - start;
        var duration     = 500;
        var startTime    = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var elapsed  = timestamp - startTime;
            var progress = Math.min(elapsed / duration, 1);
            window.scrollTo(0, start + distance * easeInOutCubic(progress));
            if (elapsed < duration) {
                requestAnimationFrame(step);
            }
        }

        requestAnimationFrame(step);
    }

    function initSmoothScroll() {
        document.addEventListener('click', function (e) {
            var link = e.target.closest(
                '.c-anchor-links__item, .c-anchor-links-mobile__item'
            );
            if (!link) return;
            var href = link.getAttribute('href');
            if (!href || href.charAt(0) !== '#') return;
            var target = document.getElementById(href.slice(1));
            if (!target) return;

            e.preventDefault();
            smoothScrollTo(target);
            closeMobileDropdown();

            // Update URL hash without jumping
            if (history.pushState) {
                history.pushState(null, '', href);
            }
        });
    }

    // ── Mobile anchor-nav dropdown ────────────────────────────────

    function closeMobileDropdown() {
        var nav = document.querySelector('[data-module="anchor-dropdown"]');
        if (!nav) return;
        var toggle = nav.querySelector('.c-anchor-links-mobile__toggle');
        var panel  = nav.querySelector('.c-anchor-links-mobile__panel');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
        if (panel)  panel.hidden = true;
    }

    function initAnchorDropdown() {
        var nav = document.querySelector('[data-module="anchor-dropdown"]');
        if (!nav) return;

        var toggle = nav.querySelector('.c-anchor-links-mobile__toggle');
        var panel  = nav.querySelector('.c-anchor-links-mobile__panel');
        if (!toggle || !panel) return;

        // Toggle on button click
        toggle.addEventListener('click', function () {
            var isOpen = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!isOpen));
            panel.hidden = isOpen;
        });

        // Close when item clicked (scroll handled by initSmoothScroll)
        panel.addEventListener('click', function (e) {
            var item = e.target.closest('.c-anchor-links-mobile__item');
            if (!item) return;
            var label = nav.querySelector('.c-anchor-links-mobile__label');
            if (label) label.textContent = item.textContent.trim();
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (!nav.contains(e.target)) {
                closeMobileDropdown();
            }
        });

        // Close on Escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeMobileDropdown();
        });
    }

    // ── Active-section tracking ───────────────────────────────────

    function setActiveLink(id) {
        // Desktop anchor links
        document.querySelectorAll('.c-anchor-links__item').forEach(function (link) {
            var href     = link.getAttribute('href');
            var isActive = href === '#' + id;
            link.classList.toggle('c-anchor-links__item--active',   isActive);
            link.classList.toggle('c-anchor-links__item--inactive', !isActive);
            if (isActive) {
                link.setAttribute('aria-current', 'true');
            } else {
                link.removeAttribute('aria-current');
            }
        });

        // Mobile dropdown items
        document.querySelectorAll('.c-anchor-links-mobile__item').forEach(function (item) {
            var href     = item.getAttribute('href');
            var isActive = href === '#' + id;
            item.classList.toggle('is-active', isActive);

            // Update mobile toggle label
            if (isActive) {
                var label = document.querySelector('.c-anchor-links-mobile__label');
                if (label) label.textContent = item.textContent.trim();
            }
        });
    }

    function initActiveTracking() {
        var sections = document.querySelectorAll('.hdx-v2-dataset-section[id]');
        if (!sections.length || !('IntersectionObserver' in window)) return;

        var observer = new IntersectionObserver(function (entries) {
            var visible = [];
            entries.forEach(function (entry) {
                if (entry.isIntersecting) visible.push(entry);
            });
            if (visible.length) {
                var top = visible.reduce(function (best, e) {
                    return e.boundingClientRect.top < best.boundingClientRect.top ? e : best;
                });
                setActiveLink(top.target.id);
            }
        }, {
            rootMargin: '-10% 0px -80% 0px',
            threshold: 0
        });

        sections.forEach(function (section) { observer.observe(section); });
    }

}());
