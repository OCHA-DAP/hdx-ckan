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
  });

})();
