$(document).ready(function () {
  $('input[type="password"]').each(function () {
    var $passwordField = $(this);
    var $passwordInputGroup = $passwordField.parent();
    var $toggleVisibilityButton = $passwordInputGroup.find('.input-field__input-group-text_state_clickable');
    var $showIcon = $toggleVisibilityButton.find('.fa-eye');
    var $hideIcon = $toggleVisibilityButton.find('.fa-eye-slash');

    $toggleVisibilityButton.on('click', function () {
      if ($passwordField.attr('type') === 'password') {
        $passwordField.attr('type', 'text');
        $showIcon.addClass('d-none');
        $hideIcon.removeClass('d-none');
      } else {
        $passwordField.attr('type', 'password');
        $showIcon.removeClass('d-none');
        $hideIcon.addClass('d-none');
      }
    });
  });
});
