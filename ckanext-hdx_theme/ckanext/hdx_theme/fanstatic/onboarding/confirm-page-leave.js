(function () {
  var shouldPreventBeforeUnload = false;
  var form = document.getElementById('user-info-form');
  var requiredInputs = form ? Array.from(form.querySelectorAll('input[required]')) : [];

  function checkInputs() {
    shouldPreventBeforeUnload = requiredInputs.some(function (input) {
      return input.value.trim() !== '';
    });
  }

  window.addEventListener('beforeunload', function (e) {
    if (shouldPreventBeforeUnload) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  ['user-info-cancel-button', 'user-info-submit-button'].forEach(function (id) {
    var btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener('click', function () {
        shouldPreventBeforeUnload = false;
      });
    }
  });

  requiredInputs.forEach(function (input) {
    input.addEventListener('input', function () {
      shouldPreventBeforeUnload = false;
      checkInputs();
    });
  });

  checkInputs();
})();
