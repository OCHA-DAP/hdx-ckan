(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
      var button = e.target.closest('[data-copy-value]');
      if (!button) return;
      if (!navigator.clipboard) return;

      var value = button.dataset.copyValue;

      navigator.clipboard.writeText(value).then(function () {
        button.classList.add('is-copied');
        setTimeout(function () {
          button.classList.remove('is-copied');
        }, 1000);
      });
    });
  });
})();
