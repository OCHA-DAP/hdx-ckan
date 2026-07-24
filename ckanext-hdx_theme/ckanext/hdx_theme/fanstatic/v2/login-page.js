(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('hdx-login-form');
    if (!form) return;

    var loginField      = document.getElementById('field-login');
    var loginFieldWrap  = document.getElementById('auth-login-field');
    var passwordField   = document.getElementById('field-password');
    var mfaWrap         = document.getElementById('mfa-form-field');
    var mfaField        = document.getElementById('field-mfa');
    var submitButton    = document.getElementById('hdx-login-submit');
    var returningUser   = document.getElementById('auth-returning-user');
    var returningAvatar = document.getElementById('auth-returning-avatar');
    var returningName   = document.getElementById('auth-returning-name');
    var returningEmail  = document.getElementById('auth-returning-email');
    var notYouButton    = document.getElementById('auth-not-you');

    var lockoutCleared = false;

    // ── Helpers ──────────────────────────────────────────────

    function getCookie(name) {
      var match = document.cookie.match('(?:^|; )' + name + '=([^;]*)');
      return match ? decodeURIComponent(match[1]) : null;
    }

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

    // ── Required-field gating (mirrors button.html's disabled contract) ──

    function updateSubmitState() {
      var valid = true;
      form.querySelectorAll('[required]').forEach(function (el) {
        if (el.type === 'checkbox') { if (!el.checked) valid = false; }
        else if (!el.value) { valid = false; }
      });
      setButtonDisabled(submitButton, !valid);
    }

    [loginField, passwordField, mfaField].forEach(function (el) {
      el.addEventListener('input', updateSubmitState);
    });

    // ── MFA reveal (GET /util/user/check_mfa) ───────────────

    function setMfaVisible(show) {
      mfaWrap.hidden = !show;
      if (show) { mfaField.setAttribute('required', 'required'); }
      else { mfaField.removeAttribute('required'); mfaField.value = ''; }
      updateSubmitState();
    }

    function checkMfa() {
      var username = loginField.value;
      if (!username) { setMfaVisible(false); return; }
      fetch('/util/user/check_mfa?user=' + encodeURIComponent(username), {credentials: 'same-origin'})
        .then(function (r) { return r.json(); })
        .then(function (json) { setMfaVisible(json.result === true); })
        .catch(function () { setMfaVisible(false); });
    }

    loginField.addEventListener('change', checkMfa);

    // ── Lockout pre-check (GET /util/user/check_lockout) ────

    form.addEventListener('submit', function (e) {
      if (lockoutCleared) return;
      e.preventDefault();
      setButtonDisabled(submitButton, true);
      var username = loginField.value;
      fetch('/util/user/check_lockout?user=' + encodeURIComponent(username), {credentials: 'same-origin'})
        .then(function (r) { return r.json(); })
        .then(function (json) {
          if (json.result === true) {
            setFieldError(passwordField,
              'Too many wrong attempts. Login locked for ' + json.timeout + ' seconds. Please try again later!');
            updateSubmitState();
          } else {
            lockoutCleared = true;
            setButtonDisabled(submitButton, false);
            if (form.requestSubmit) { form.requestSubmit(); } else { form.submit(); }
          }
        })
        .catch(function () {
          lockoutCleared = true;
          setButtonDisabled(submitButton, false);
          if (form.requestSubmit) { form.requestSubmit(); } else { form.submit(); }
        });
    });

    // ── "Remember me" cookie prefill / returning-user swap ──
    // Initials-only avatar — reuses the server-rendered c-avatar markup,
    // just fills in the initial once the cookie is read client-side.

    function showReturningUser(data) {
      loginField.value = data.login || '';
      loginFieldWrap.hidden = true;
      returningUser.hidden = false;
      returningName.textContent = data.display_name || '';
      returningEmail.textContent = data.email || '';

      var avatarEl = returningAvatar.querySelector('.c-avatar');
      var initialsEl = returningAvatar.querySelector('.c-avatar__initials');
      var initial = (data.display_name || '').trim().charAt(0).toUpperCase() || '?';
      if (initialsEl) initialsEl.textContent = initial;
      if (avatarEl) avatarEl.setAttribute('aria-label', data.display_name || '');

      checkMfa();
      updateSubmitState();
    }

    function notYou() {
      loginField.value = '';
      loginFieldWrap.hidden = false;
      returningUser.hidden = true;
      setMfaVisible(false);
      updateSubmitState();
      loginField.focus();
    }

    notYouButton.addEventListener('click', notYou);

    var loginCookie = getCookie('hdx_login');
    if (loginCookie) {
      try { showReturningUser(JSON.parse(loginCookie)); }
      catch (e) { /* malformed cookie — ignore, show the plain form */ }
    }

    updateSubmitState();
  });
})();
