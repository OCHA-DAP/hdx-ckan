(function () {
  'use strict';

  // Closes all open dropdowns except `except` (pass null to close all).
  // Also resets any filter search input inside a closed panel.
  function closeAll(except) {
    document.querySelectorAll('.c-dropdown--open').forEach(function (dd) {
      if (dd === except) return;
      dd.classList.remove('c-dropdown--open');
      var panel   = dd.querySelector('.c-dropdown__panel');
      var trigger = dd.querySelector('.c-dropdown__trigger');
      if (panel) {
        panel.hidden = true;
        var si = panel.querySelector('[data-filter-search] input');
        if (si && si.value) { si.value = ''; si.dispatchEvent(new Event('input')); }
      }
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {

    // ── Toggle open/close on trigger click ───────────────────
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest && e.target.closest('.c-dropdown__trigger');
      if (!trigger) return;

      var dd     = trigger.closest('.c-dropdown');
      var panel  = dd && dd.querySelector('.c-dropdown__panel');
      var isOpen = dd && dd.classList.contains('c-dropdown--open');

      closeAll(dd);  // close all other open dropdowns first

      if (dd)    dd.classList.toggle('c-dropdown--open', !isOpen);
      if (panel) panel.hidden = isOpen;
      trigger.setAttribute('aria-expanded', String(!isOpen));
    });

    // ── Navigate item click → URL navigation ─────────────────
    // Items inside [data-nav-key] are handled by search.js (setNavParam).
    // All other navigate items navigate directly to the URL in data-nav-value.
    document.addEventListener('click', function (e) {
      var item = e.target.closest && e.target.closest('[data-nav-value]');
      if (!item) return;
      if (item.closest('[data-nav-key]')) return;
      var url = item.getAttribute('data-nav-value');
      if (url) window.location.href = url;
    });

    // ── Outside click → close all open dropdowns ─────────────
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('.c-dropdown')) return;
      closeAll(null);
    });

  });
})();
