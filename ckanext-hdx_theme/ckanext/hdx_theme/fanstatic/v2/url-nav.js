(function () {
  'use strict';

  // ── setNavParam ────────────────────────────────────────────────────────────
  // Sets a single URL param and reloads, resetting ?page to 1.
  // Used by any navigate-on-select dropdown (sort, page-size) and search inputs.

  function setNavParam(key, value) {
    var url = new URL(window.location.href);
    url.searchParams.set(key, value);
    url.searchParams.delete('page');
    window.location.href = url.toString();
  }

  // Expose for pages that wire their own search Enter handler.
  window.hdxSetNavParam = setNavParam;

  // ── Navigate-on-select dropdown handler ───────────────────────────────────
  // Handles clicks on [data-nav-key] [data-nav-value] items rendered by
  // v2/components/dropdown.html with navigate=True.

  document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
      var navItem = e.target.closest && e.target.closest('[data-nav-key] [data-nav-value]');
      if (navItem) {
        var dd    = navItem.closest('[data-nav-key]');
        var value = navItem.getAttribute('data-nav-value');
        setNavParam(dd.getAttribute('data-nav-key'), value);
      }
    });
  });

})();
