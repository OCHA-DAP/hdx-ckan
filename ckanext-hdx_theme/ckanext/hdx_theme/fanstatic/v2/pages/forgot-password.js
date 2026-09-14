(function () {
  'use strict';

  var recaptchaWidgetId = null;

  document.addEventListener('DOMContentLoaded', function () {
    var form         = document.getElementById('recover-form');
    if (!form) return;

    var idField       = document.getElementById('field-recover-id');
    var recoverCard   = document.getElementById('auth-recover-card');
    var successCard   = document.getElementById('auth-recover-success-card');
    var submitButton  = document.getElementById('recover-submit');
    var recaptchaContainer = document.getElementById('recover-recaptcha');

    function setButtonDisabled(btn, disabled) {
      btn.disabled = disabled;
      btn.classList.toggle('is-disabled', disabled);
      btn.setAttribute('aria-disabled', disabled ? 'true' : 'false');
    }

    function setFieldError(input, message) {
      var wrapper = input.closest('.c-search-input');
      if (!wrapper) return;
      var errorEl = wrapper.parentElement && wrapper.parentElement.querySelector('.c-search-input__error');
      wrapper.classList.toggle('c-search-input--error', !!message);
      if (errorEl) errorEl.textContent = message || '';
    }

    function updateSubmitState() {
      setButtonDisabled(submitButton, idField.value.trim() === '');
    }

    idField.addEventListener('input', updateSubmitState);
    updateSubmitState();

    // Renders the invisible reCAPTCHA into its dedicated container (between
    // the field and the button) instead of onto the button itself.
    function ensureRecaptcha() {
      if (!recaptchaContainer) return false;
      if (recaptchaWidgetId !== null) return true;
      if (window.grecaptcha && window.grecaptcha.render) {
        recaptchaWidgetId = window.grecaptcha.render(recaptchaContainer, {
          sitekey: recaptchaContainer.getAttribute('data-sitekey'),
          size: 'invisible',
          badge: 'inline',
          callback: submitRecoverForm
        });
        return true;
      }
      return false;
    }

    // Render as soon as the (async) recaptcha script is ready, instead of
    // waiting for the submit click, so the badge doesn't pop in after the
    // user has already clicked. Falls back to the submit handler's own
    // ensureRecaptcha() call if the script is still slow to load.
    (function tryRenderRecaptcha(attemptsLeft) {
      if (ensureRecaptcha() || attemptsLeft <= 0) return;
      setTimeout(function () { tryRenderRecaptcha(attemptsLeft - 1); }, 150);
    })(20);

    function submitRecoverForm(token) {
      setFieldError(idField, '');
      var data = new URLSearchParams(new FormData(form));
      if (token) data.set('g-recaptcha-response', token);
      fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: Object.assign({'X-Requested-With': 'XMLHttpRequest'}, window.hdxUtil.net.getCsrfTokenAsObject()),
        body: data
      })
        .then(function (r) { return r.json(); })
        .then(function (result) {
          if (result.success) {
            recoverCard.hidden = true;
            successCard.hidden = false;
            successCard.setAttribute('tabindex', '-1');
            successCard.focus();
          } else {
            setFieldError(idField, result.error && result.error.message);
            if (recaptchaWidgetId !== null) window.grecaptcha.reset(recaptchaWidgetId);
          }
        })
        .catch(function () {
          setFieldError(idField, 'Something went wrong. Please try again.');
          if (recaptchaWidgetId !== null) window.grecaptcha.reset(recaptchaWidgetId);
        });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (submitButton.disabled) return;
      if (ensureRecaptcha()) {
        window.grecaptcha.execute(recaptchaWidgetId);
      } else {
        // recaptcha script unavailable — submit anyway, server validates
        submitRecoverForm('');
      }
    });
  });
})();
