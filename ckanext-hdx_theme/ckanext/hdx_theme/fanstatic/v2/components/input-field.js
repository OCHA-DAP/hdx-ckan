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

// ── Clear (×) behavior + live --filled sync ─────────────────────
// Applies to every c-search-input with a clear button, EXCEPT wrappers
// marked data-search-managed (the global topbar autocomplete manages
// its own clear/state in search-autocomplete.js).
// Clicking × clears the term; when the term came server-rendered from
// the URL (an active search), it also resubmits the enclosing form so
// the results reset — pages that intercept `submit` (search-page.js,
// org-list-page.js) keep their setNavParam behavior.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.c-search-input').forEach(function (wrapper) {
    if (wrapper.hasAttribute('data-search-managed')) return;
    var input = wrapper.querySelector('input');
    var clear = wrapper.querySelector('.c-search-input__clear');
    if (!input || !clear) return;

    function syncFilled() {
      wrapper.classList.toggle('c-search-input--filled', input.value.trim() !== '');
    }

    input.addEventListener('input', syncFilled);
    syncFilled();

    clear.addEventListener('click', function () {
      var hadActiveSearch = input.defaultValue.trim() !== '';
      input.value = '';
      syncFilled();
      // notify listeners (e.g. the filter-panel MiniSearch reset)
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.focus();
      if (hadActiveSearch && input.form) {
        if (input.form.requestSubmit) { input.form.requestSubmit(); }
        else { input.form.submit(); }
      }
    });
  });
});
