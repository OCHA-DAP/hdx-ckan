// ============================================================
// alert.js — dismiss handling for the shared c-alert component
// Renders from templates/v2/components/alert.html.
// ============================================================
(function () {
  'use strict';

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-alert-close]');
    if (!btn) return;
    var alertEl = btn.closest('.c-alert');
    if (alertEl) alertEl.hidden = true;
  });

})();
