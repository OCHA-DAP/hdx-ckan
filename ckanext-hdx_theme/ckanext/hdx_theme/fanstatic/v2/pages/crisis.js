(function () {
  'use strict';

  // Vanilla port of the v1 CKAN `data-viewer` module (fanstatic/modules/data-viewer2.js)
  // for crisis/event page iframe sections (map / key_figures / interactive_data).
  var MIN_HEIGHT = 400;
  var PADDING = 30;
  var RECALIBRATE_INTERVAL = 200;

  function getSameOriginBody(iframe) {
    try {
      return iframe.contentWindow.document.body || null;
    } catch (e) {
      return null;
    }
  }

  function recalibrate(iframe) {
    var body = getSameOriginBody(iframe);
    if (!body) {
      // cross-origin (or not yet accessible) — leave the configured height
      // (admin max_height, or the 400px default) alone rather than clobber it
      return;
    }
    var height = Math.max(body.scrollHeight, MIN_HEIGHT);
    iframe.style.height = (height + PADDING) + 'px';
  }

  function showError(iframe) {
    var wrapper = iframe.closest('.hdx-v2-crisis-iframe');
    var errorEl = wrapper && wrapper.querySelector('[data-crisis-iframe-error]');
    if (errorEl) {
      errorEl.hidden = false;
      errorEl.textContent = 'This visualization could not be loaded.';
    }
    iframe.style.display = 'none';
  }

  function initIframe(iframe) {
    var intervalId;

    function onLoad() {
      recalibrate(iframe);
      clearInterval(intervalId);
      if (getSameOriginBody(iframe)) {
        intervalId = setInterval(function () { recalibrate(iframe); }, RECALIBRATE_INTERVAL);
      }
    }

    iframe.addEventListener('load', onLoad);
    iframe.addEventListener('error', function () {
      showError(iframe);
    });

    // Same-origin content that already finished loading before this script
    // ran (fast/cached iframe) would otherwise miss the 'load' event above.
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      onLoad();
    }

    // Firefox caches iframes — force it to fetch fresh content
    if (/#$/.test(iframe.src)) {
      iframe.src = iframe.src.slice(0, -1);
    } else {
      iframe.src = iframe.src + '#';
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var iframes = document.querySelectorAll('[data-crisis-iframe]');
    for (var i = 0; i < iframes.length; i++) {
      initIframe(iframes[i]);
    }
  });
})();
