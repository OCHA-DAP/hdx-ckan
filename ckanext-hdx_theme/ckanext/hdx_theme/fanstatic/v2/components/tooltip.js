/**
 * tooltip.js
 *
 * Site-wide positioning + open/close behaviour for every `.c-tooltip-anchor`
 * (icon + tooltip pair). Visibility itself stays CSS-driven (hover /
 * focus-visible / .is-open toggle opacity+visibility in label.less) — this
 * module only computes WHERE the tooltip goes, via Popper.js's flip +
 * preventOverflow modifiers, so it always stays inside the viewport instead
 * of the old fixed right-anchored-above-icon default.
 *
 * Requires window.Popper (vendor/popperjs.js, loaded on every page via
 * hdx_theme/vendor-vendor — see fanstatic/webassets.yml).
 *
 * Popper instances are created lazily on first show and destroyed once
 * nothing is keeping the tooltip open (hover / focus-visible / click), so
 * pages with many anchors (e.g. completeness-item grids) don't pay for
 * dozens of idle scroll/resize listeners.
 */
(function (window, document) {
    'use strict';

    if (!window.Popper) return;

    var rootStyle = null;

    function tokenPx(name) {
        if (!rootStyle) rootStyle = getComputedStyle(document.documentElement);
        var value = parseFloat(rootStyle.getPropertyValue(name));
        return isNaN(value) ? 0 : value * 16;
    }

    document.addEventListener('DOMContentLoaded', function () {
        var anchorEls = document.querySelectorAll('.c-tooltip-anchor');
        if (!anchorEls.length) return;

        var gap = tokenPx('--hdx-space-1') || 4;
        var instances = [];

        anchorEls.forEach(function (anchor) {
            var icon = anchor.querySelector('.c-info-icon');
            var tooltip = anchor.querySelector('.c-tooltip');
            if (!icon || !tooltip) return;

            var arrow = tooltip.querySelector('.c-tooltip__arrow');
            var popper = null;

            var instance = {
                icon: icon,
                isWanted: function () {
                    return icon.classList.contains('is-open') ||
                        icon.matches(':hover') ||
                        document.activeElement === icon;
                },
                show: function () {
                    if (popper) {
                        popper.update();
                        return;
                    }
                    var modifiers = [
                        { name: 'offset', options: { offset: [0, gap] } },
                        { name: 'flip', options: { fallbackPlacements: ['bottom'], rootBoundary: 'viewport', padding: 8 } },
                        { name: 'preventOverflow', options: { altAxis: true, rootBoundary: 'viewport', padding: 8 } }
                    ];
                    if (arrow) modifiers.push({ name: 'arrow', options: { element: arrow, padding: 8 } });
                    popper = window.Popper.createPopper(icon, tooltip, {
                        placement: 'top',
                        modifiers: modifiers
                    });
                },
                refresh: function () {
                    if (this.isWanted()) {
                        this.show();
                    } else if (popper) {
                        popper.destroy();
                        popper = null;
                    }
                }
            };
            instances.push(instance);

            icon.addEventListener('mouseenter', function () { instance.refresh(); });
            icon.addEventListener('mouseleave', function () { instance.refresh(); });
            icon.addEventListener('focusin', function () { instance.refresh(); });
            icon.addEventListener('focusout', function () { instance.refresh(); });

            icon.addEventListener('click', function (e) {
                e.stopPropagation();
                var isOpen = icon.classList.contains('is-open');
                closeAllTooltips();
                if (!isOpen) {
                    icon.classList.add('is-open');
                    icon.setAttribute('aria-expanded', 'true');
                    instance.refresh();
                }
            });
        });

        function closeAllTooltips() {
            instances.forEach(function (instance) {
                instance.icon.classList.remove('is-open');
                instance.icon.setAttribute('aria-expanded', 'false');
                instance.refresh();
            });
        }

        // Escape closes any open tooltip and returns focus to its trigger.
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            var openIcon = document.querySelector('.c-tooltip-anchor .c-info-icon.is-open');
            if (openIcon) {
                closeAllTooltips();
                openIcon.focus();
            }
        });

        document.addEventListener('click', closeAllTooltips);
    });
})(window, document);
