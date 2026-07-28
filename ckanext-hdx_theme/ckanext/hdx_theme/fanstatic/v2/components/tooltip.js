/**
 * tooltip.js
 *
 * Site-wide positioning + open/close behaviour for every `.c-tooltip-anchor`
 * (trigger + tooltip pair, trigger marked with `.c-tooltip-trigger`).
 * Visibility itself stays CSS-driven (hover / focus-visible / .is-open
 * toggle opacity+visibility in label.less) — this module only computes
 * WHERE the tooltip goes, via Popper.js's flip + preventOverflow modifiers,
 * so it always stays inside the viewport instead of a fixed side.
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

    document.addEventListener('DOMContentLoaded', function () {
        var anchorEls = document.querySelectorAll('.c-tooltip-anchor');
        if (!anchorEls.length) return;

        var gap = window.hdxV2.tokenPx('--hdx-space-1') || 4;
        var instances = [];

        anchorEls.forEach(function (anchor) {
            var trigger = anchor.querySelector('.c-tooltip-trigger');
            var tooltip = anchor.querySelector('.c-tooltip');
            if (!trigger || !tooltip) return;

            var arrow = tooltip.querySelector('.c-tooltip__arrow');
            var popper = null;

            var instance = {
                trigger: trigger,
                isWanted: function () {
                    return trigger.classList.contains('is-open') ||
                        trigger.matches(':hover') ||
                        document.activeElement === trigger;
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
                    popper = window.Popper.createPopper(trigger, tooltip, {
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

            trigger.addEventListener('mouseenter', function () { instance.refresh(); });
            trigger.addEventListener('mouseleave', function () { instance.refresh(); });
            trigger.addEventListener('focusin', function () { instance.refresh(); });
            trigger.addEventListener('focusout', function () { instance.refresh(); });

            trigger.addEventListener('click', function (e) {
                e.stopPropagation();
                var isOpen = trigger.classList.contains('is-open');
                closeAllTooltips();
                if (!isOpen) {
                    trigger.classList.add('is-open');
                    trigger.setAttribute('aria-expanded', 'true');
                    instance.refresh();
                }
            });
        });

        function closeAllTooltips() {
            instances.forEach(function (instance) {
                instance.trigger.classList.remove('is-open');
                instance.trigger.setAttribute('aria-expanded', 'false');
                instance.refresh();
            });
        }

        // Escape closes any open tooltip and returns focus to its trigger.
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            var openTrigger = document.querySelector('.c-tooltip-anchor .c-tooltip-trigger.is-open');
            if (openTrigger) {
                closeAllTooltips();
                openTrigger.focus();
            }
        });

        document.addEventListener('click', closeAllTooltips);
    });
})(window, document);
