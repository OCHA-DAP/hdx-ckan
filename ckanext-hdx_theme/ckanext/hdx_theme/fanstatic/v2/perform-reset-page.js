(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('perform-reset-form');
    if (!form) return;

    var submitButton = document.getElementById('perform-reset-submit');

    function setButtonDisabled(btn, disabled) {
      btn.disabled = disabled;
      btn.classList.toggle('is-disabled', disabled);
      btn.setAttribute('aria-disabled', disabled ? 'true' : 'false');
    }

    function updateSubmitState() {
      var valid = true;
      form.querySelectorAll('[required]').forEach(function (el) {
        if (!el.value) valid = false;
      });
      setButtonDisabled(submitButton, !valid);
    }

    form.querySelectorAll('[required]').forEach(function (el) {
      el.addEventListener('input', updateSubmitState);
    });

    updateSubmitState();
  });
})();
