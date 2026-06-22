(function () {
  'use strict';

  // Shared v2 utilities — loaded first in the v2-components-scripts bundle
  // so all component JS can reference window.hdxV2.*.

  window.hdxV2 = window.hdxV2 || {};

  // Selector for all natively focusable elements.
  // Used by focus-trap implementations (drawer, overlays, etc.).
  var FOCUSABLE = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  // Returns an array of visible focusable elements within `container` (DOM node).
  window.hdxV2.getFocusable = function getFocusable(container) {
    return Array.from(container.querySelectorAll(FOCUSABLE)).filter(function (el) {
      return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    });
  };

})();
