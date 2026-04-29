document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.c-search-input__toggle').forEach(function (btn) {
    var input    = btn.closest('.c-search-input').querySelector('input');
    var eyeEl    = btn.querySelector('.c-search-input__toggle-eye');
    var eyeOffEl = btn.querySelector('.c-search-input__toggle-eye-off');

    btn.addEventListener('click', function () {
      var isPassword  = input.type === 'password';
      input.type      = isPassword ? 'text' : 'password';
      eyeEl.hidden    = isPassword;
      eyeOffEl.hidden = !isPassword;
      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    });
  });
});
