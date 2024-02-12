$(document).ready(function () {
  var shouldPreventBeforeUnload = false;
  var requiredInputs = $('#user-info-form input[required]');

  function checkInputs() {
    requiredInputs.each(function() {
      if ($(this).val().trim() !== '') {
        shouldPreventBeforeUnload = true;
        return false;
      }
    });
  }

  $(window).on('beforeunload', function (e) {
    if (shouldPreventBeforeUnload) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  $('#user-info-cancel-button, #user-info-submit-button').on('click', function () {
    shouldPreventBeforeUnload = false;
  });

  requiredInputs.on('input', function () {
    shouldPreventBeforeUnload = false;
    checkInputs();
  });

  checkInputs();
});
