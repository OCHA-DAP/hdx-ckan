/*jshint esversion: 6 */

function notYou(){
    const $fieldLogin = $('#field-login');
    $fieldLogin.val('').trigger('change');
    $fieldLogin.removeClass('input-content');
    $('#username-static, #login-photo-gravatar').hide();
    $('#username-form-field, #login-photo-default').show();
    $fieldLogin.focus();
    _displayMfaField();
}

function checkLockout(event) {
  const username = $("#field-login").val();
  const response = $.ajax({
    type: "GET",
    url: `/util/user/check_lockout?user=${username}`,
    cache: false,
    async: false
  }).responseText;
  if (response) {
    const json = JSON.parse(response);
    if (json.result === true){
      _showLoginError(`Too many wrong attempts. Login locked for ${json.timeout} seconds. Please try again later!`);
      event.preventDefault();
    }
  }

}


function _displayMfaField(show = false) {
  const $loginContent = $('.login-content');
  const $fieldMfa = $('#field-mfa');
  if (show) {
    $("#mfa-form-field").show();
    $fieldMfa.attr('required', true);
    // $loginContent.addClass('login-content--size-big');
  }
  else {
    $("#mfa-form-field").hide();
    $fieldMfa.removeAttr('required');
    // $loginContent.removeClass('login-content--size-big');
  }
  $fieldMfa.val('').trigger('change');
}

function checkMfa() {
  const username = $("#field-login").val();
  const response = $.ajax({
    type: "GET",
    url: `/util/user/check_mfa?user=${username}`,
    cache: false,
    async: false
  }).responseText;
  if (response) {
    const json = JSON.parse(response);
    if (json.result === true){
      _displayMfaField(true);
      return;
    }
  }
  _displayMfaField();
}

requiredFieldsFormValidator = function () {
  let error = false;
  const $form = $(this).closest('form');
  const $submitButton = $form.find('[type="submit"]');
  $form.find('input, select, textarea').filter('[required]').each(function (idx, el) {
    if ((el.type === 'checkbox') ? !el.checked : (el.value === null || el.value === '' || el.value === '-1')) {
      error = true;
      return true;
    }
  });
  if (error) {
    $submitButton.attr('disabled', true);
  } else {
    $submitButton.removeAttr('disabled');
  }
};

$(
  function(){
    const $loginForm = $('#hdx-login-form');
    const $loginFormRequiredFields = $loginForm.find('input, select, textarea').filter('[required]');
    $loginForm.on('submit', checkLockout);
    $loginFormRequiredFields.on('input change focus', requiredFieldsFormValidator);
    $("#field-login").on('change', checkMfa);
    $loginFormRequiredFields.filter(() => this.value !== '').first().trigger('change');
    //check cookies
    const loginCookie = $.cookie("hdx_login");
    const loginPopup = $("#loginPopup").length > 0;
    if (loginCookie && loginPopup){
        var data = JSON.parse(loginCookie);
        //console.log(data);

        $('#username-form-field, #login-photo-default').hide();
        $('#field-login').val(data.login);
        $('#user-display-name').text(data.display_name);
        if (data.email)
            $('#user-display-email').text(data.email);
        $('#login-photo-gravatar-img').attr("src", "//gravatar.com/avatar/"+ data.email_hash +"?s=95&d=identicon");
        $('#username-static, #login-photo-gravatar').show();
        checkMfa();
    }

    //check for login info message
    var loginInfo = $("#login-info").text();
    if (loginInfo && loginInfo !== ""){
        var errMsg = $("#login-info-message");
        errMsg.text(loginInfo);
        notYou();
        errMsg.show();
    }

    var userLogin = $("#user-login").text();
    if (userLogin && userLogin !== ""){
        showOnboardingWidget("#loginPopup");
        return;
    }

    $('.popup .content').css('visibility', 'visible');
  }
);
