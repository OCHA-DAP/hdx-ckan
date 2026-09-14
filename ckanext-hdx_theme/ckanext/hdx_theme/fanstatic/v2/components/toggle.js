/**
 * toggle.js
 *
 * Generic visual-state handler for the c-toggle component.
 * Keeps c-toggle--on / c-toggle--off classes in sync with the
 * hidden checkbox state via event delegation.
 */

(function () {
    'use strict';

    document.addEventListener('change', function (e) {
        var checkbox = e.target;
        if (!checkbox || checkbox.type !== 'checkbox') return;
        var label = checkbox.closest('.c-toggle');
        if (!label) return;
        if (checkbox.checked) {
            label.classList.remove('c-toggle--off');
            label.classList.add('c-toggle--on');
        } else {
            label.classList.remove('c-toggle--on');
            label.classList.add('c-toggle--off');
        }
    });

}());
