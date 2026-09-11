/**
 * anchor-links.js
 *
 * Behaviour for the c-anchor-links component:
 *   - Smooth scroll on anchor-link click (500ms, cubic-bezier(0.6, 0, 0.3, 1))
 *   - Mobile anchor-nav dropdown toggle
 *   - Active-section tracking via IntersectionObserver
 *   - Hash-on-load scroll correction (any page, not just anchor-links pages)
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initSmoothScroll();
        initAnchorDropdown();
        initActiveTracking();
        initHashOnLoadCorrection();
    });

    // Expose smoothScrollTo/closeMobileDropdown/scrollToHashTarget for reuse by other page scripts
    window.hdxSmoothScrollTo = smoothScrollTo;
    window.hdxCloseAnchorDropdown = closeMobileDropdown;
    window.hdxScrollToHashTarget = scrollToHashTarget;


    // ── Easing ──────────────────────────────────────────────────

    function cubicBezier(x1, y1, x2, y2) {
        function coord(t, a1, a2) {
            var c = 3 * a1;
            var b = 3 * (a2 - a1) - c;
            var a = 1 - c - b;
            return ((a * t + b) * t + c) * t;
        }
        function slope(t, a1, a2) {
            var c = 3 * a1;
            var b = 3 * (a2 - a1) - c;
            var a = 1 - c - b;
            return (3 * a * t + 2 * b) * t + c;
        }
        return function (x) {
            if (x <= 0) return 0;
            if (x >= 1) return 1;
            var t = x;
            for (var i = 0; i < 8; i++) {
                var s = slope(t, x1, x2);
                if (Math.abs(s) < 1e-6) break;
                t -= (coord(t, x1, x2) - x) / s;
            }
            return coord(t, y1, y2);
        };
    }

    function parseCubicBezier(value) {
        var match = /cubic-bezier\(([^)]+)\)/.exec(value || '');
        var parts = (match ? match[1] : '0.6, 0, 0.3, 1').split(',').map(parseFloat);
        return cubicBezier(parts[0], parts[1], parts[2], parts[3]);
    }

    var ease = parseCubicBezier(window.hdxV2.token('--hdx-ease-emphasized'));

    // ── Smooth scroll ────────────────────────────────────────────
    // Offset is read from the target's CSS scroll-margin-top so the same
    // value governs both native anchor navigation and smooth scroll.
    // container defaults to the window; pass a scrollable element (e.g. a
    // drawer's own scroll container) to animate its scrollTop instead.

    function smoothScrollTo(target, container, extraOffset) {
        var isWindow     = !container;
        var start        = isWindow ? window.scrollY : container.scrollTop;
        var containerTop = isWindow ? 0 : container.getBoundingClientRect().top;
        var targetTop    = target.getBoundingClientRect().top - containerTop + start;
        var scrollMargin = (parseFloat(getComputedStyle(target).scrollMarginTop) || 0) + (extraOffset || 0);
        var destination  = Math.max(0, targetTop - scrollMargin);

        // Respect the user's motion preference (V-10 / C-07): jump instantly,
        // but still honor scrollMargin + extraOffset (scrollIntoView cannot).
        if (window.hdxV2.prefersReducedMotion()) {
            if (isWindow) { window.scrollTo(0, destination); }
            else          { container.scrollTop = destination; }
            return;
        }

        var distance     = destination - start;
        var duration     = window.hdxV2.tokenPx('--hdx-duration-slow');
        var startTime    = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var elapsed  = timestamp - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var pos      = start + distance * ease(progress);
            if (isWindow) {
                window.scrollTo(0, pos);
            } else {
                container.scrollTop = pos;
            }
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
        var navItems = document.querySelectorAll('.c-anchor-links__item[href^="#"]');
        var sections = Array.prototype.map.call(navItems, function (link) {
            return document.getElementById(link.getAttribute('href').slice(1));
        }).filter(Boolean);
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

    // ── Hash-on-load scroll correction ────────────────────────────

    function scrollToHashTarget() {
        var target = document.getElementById(window.location.hash.slice(1));
        if (target) smoothScrollTo(target);
    }

    function initHashOnLoadCorrection() {
        if (!window.location.hash) return;
        window.addEventListener('load', scrollToHashTarget);
    }

}());
