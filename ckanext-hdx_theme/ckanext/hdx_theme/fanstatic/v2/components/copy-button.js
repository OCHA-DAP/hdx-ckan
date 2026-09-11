(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
      var button = e.target.closest('[data-copy-value]');
      if (!button) return;
      if (!navigator.clipboard) return;

      var value    = button.dataset.copyValue;
      var statusEl = button.querySelector('[data-copy-status]');

      navigator.clipboard.writeText(value).then(function () {
        button.classList.add('is-copied');
        // Announce success to screen readers via the live region (V-08)
        if (statusEl) statusEl.textContent = 'Copied to clipboard';
        setTimeout(function () {
          button.classList.remove('is-copied');
          if (statusEl) statusEl.textContent = '';
        }, 2000);
      }).catch(function () {
        // Silent no-op on failure (e.g. insecure context / permission denied)
      });
    });
  });
})();
