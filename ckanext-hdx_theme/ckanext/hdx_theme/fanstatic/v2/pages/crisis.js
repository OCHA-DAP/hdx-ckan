(function () {
  'use strict';

  // Iframe recalibration (map / key_figures / interactive_data sections)
  // delegates to the shared window.hdxV2.initRecalibratingIframe (v2/utils.js).
  var MIN_HEIGHT = 400;
  var PADDING = 30;
  var RECALIBRATE_INTERVAL = 200;

  function showError(iframe) {
    var wrapper = iframe.closest('.hdx-v2-crisis-iframe');
    var errorEl = wrapper && wrapper.querySelector('[data-crisis-iframe-error]');
    if (errorEl) {
      errorEl.hidden = false;
      errorEl.textContent = 'This visualization could not be loaded.';
    }
    iframe.style.display = 'none';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var iframes = document.querySelectorAll('[data-crisis-iframe]');
    for (var i = 0; i < iframes.length; i++) {
      window.hdxV2.initRecalibratingIframe(iframes[i], {
        minHeight: MIN_HEIGHT,
        padding: PADDING,
        interval: RECALIBRATE_INTERVAL,
        onError: showError
      });
    }
  });
})();
