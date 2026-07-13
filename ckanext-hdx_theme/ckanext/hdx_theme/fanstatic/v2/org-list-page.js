(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('hdx-org-search-form');
    if (!form) return;

    form.addEventListener('keydown', function (e) {
      var input = e.target;
      if (input.name === 'q' && (e.key === 'Enter' || e.keyCode === 13)) {
        e.preventDefault();
        window.hdxSetNavParam('q', input.value.trim());
      }
    });

    // Same interception for real form submits — the search-input submit
    // icon and the clear button (input-field.js) go through requestSubmit;
    // keeps navigation on the shared nav-param path (resets `page`).
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = form.querySelector('input[name="q"]');
      window.hdxSetNavParam('q', input ? input.value.trim() : '');
    });
  });

})();
