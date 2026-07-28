(function () {
  'use strict';

  // Shared v2 utilities — loaded first in the v2-components-scripts bundle
  // so all component JS can reference window.hdxV2.*.

  window.hdxV2 = window.hdxV2 || {};

  var rootStyle = null;

  // Returns the raw (trimmed) computed value of a CSS custom property.
  window.hdxV2.token = function token(name) {
    if (!rootStyle) rootStyle = getComputedStyle(document.documentElement);
    return rootStyle.getPropertyValue(name).trim();
  };

  // Converts a design token to a plain px number. Rem-based tokens are
  // scaled by the actual computed root font-size (not a hardcoded 16),
  // so it stays correct under browser text-size/zoom settings.
  window.hdxV2.tokenPx = function tokenPx(name) {
    var raw = window.hdxV2.token(name);
    var value = parseFloat(raw);
    if (isNaN(value)) return 0;
    if (raw.indexOf('rem') !== -1) {
      var rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
      return value * rootFontSize;
    }
    return value;
  };

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
