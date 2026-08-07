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

  // Keeps a same-origin iframe's height matched to its content, for content
  // that loads/grows asynchronously (e.g. an async fetch inside the iframe).
  // Polls indefinitely on `load` rather than stopping after one recheck, so
  // late height growth is still caught. options: minHeight, padding,
  // interval (ms), onError(iframe) — all optional.
  window.hdxV2.initRecalibratingIframe = function initRecalibratingIframe(iframe, options) {
    options = options || {};
    var minHeight = options.minHeight || 400;
    var padding = options.padding != null ? options.padding : 30;
    var interval = options.interval || 200;
    var onError = options.onError;
    var intervalId;

    function getSameOriginBody() {
      try {
        return iframe.contentWindow.document.body || null;
      } catch (e) {
        return null;
      }
    }

    function recalibrate() {
      var body = getSameOriginBody();
      if (!body) return;
      var height = Math.max(body.scrollHeight, minHeight);
      iframe.style.height = (height + padding) + 'px';
    }

    function onLoad() {
      recalibrate();
      clearInterval(intervalId);
      if (getSameOriginBody()) {
        intervalId = setInterval(recalibrate, interval);
      }
    }

    iframe.addEventListener('load', onLoad);
    if (onError) {
      iframe.addEventListener('error', function () { onError(iframe); });
    }

    // Same-origin content that already finished loading before this ran
    // (fast/cached iframe) would otherwise miss the 'load' event above.
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      onLoad();
    }

    // Firefox caches iframes — force it to fetch fresh content.
    if (/#$/.test(iframe.src)) {
      iframe.src = iframe.src.slice(0, -1);
    } else {
      iframe.src = iframe.src + '#';
    }
  };

  // Currently a no-op pending task 069's follow-up — uncomment the
  // matchMedia check to re-enable prefers-reduced-motion support
  // everywhere this helper is called.
  window.hdxV2.prefersReducedMotion = function prefersReducedMotion() {
    // return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return false;
  };

})();
