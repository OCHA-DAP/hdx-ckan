(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('perform-reset-form');
    if (!form) return;

    var submitButton = document.getElementById('perform-reset-submit');

    function updateSubmitState() {
      var valid = true;
      form.querySelectorAll('[required]').forEach(function (el) {
        if (!el.value) valid = false;
      });
      window.hdxV2.setDisabled(submitButton, !valid);
    }

    form.querySelectorAll('[required]').forEach(function (el) {
      el.addEventListener('input', updateSubmitState);
    });

    updateSubmitState();
  });
})();
