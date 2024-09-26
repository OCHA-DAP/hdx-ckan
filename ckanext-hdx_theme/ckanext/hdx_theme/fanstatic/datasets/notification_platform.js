var $notificationsSignupModal = $('#notificationsSignupBemModal');
var notificationsSignupModal = bootstrap.Modal.getOrCreateInstance($notificationsSignupModal.get(0));

$(document).ready(function () {
  var $verificationModal = $('#notificationsVerificationBemModal');
  var verificationModal = bootstrap.Modal.getOrCreateInstance($verificationModal.get(0));
  var $unsubscribeModal = $('#notificationsUnsubscribeBemModal');
  var unsubscribeModal = bootstrap.Modal.getOrCreateInstance($unsubscribeModal.get(0));
  var $unsubscribedModal = $('#notificationsUnsubscribedBemModal');
  var unsubscribedModal = bootstrap.Modal.getOrCreateInstance($unsubscribedModal.get(0));

  var $signupForm = $notificationsSignupModal.find('#notification-platform-form');
  var $signupSubmitButton = $notificationsSignupModal.find('button[type="submit"]');
  var $signupDangerAlert = $notificationsSignupModal.find('.alert-danger');

  var $unsubscribeSubmitButton = $unsubscribeModal.find('button[type="submit"]');
  var $unsubscribeDangerAlert = $unsubscribeModal.find('.alert-danger');

  var $unsubscribeToken = $('#unsubscribe_token');
  var unsubscribeToken = null;
  if($unsubscribeToken.length > 0 && $unsubscribeToken.data('token').toLowerCase() !== 'none') {
    unsubscribeToken = $unsubscribeToken.data('token');
  }

  var onSignupSubmit = function (e) {
    e.preventDefault();

    $.ajax({
      url: '/notifications/subscription-confirmation',
      method: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: $signupForm.serialize(),
      success: function (data) {
        grecaptcha.reset();
        if (data.success) {
          hideAlert($signupDangerAlert);
          hideNotificationsSignupModal();
          verificationModal.show();
        }
        else {
          showAlert($signupDangerAlert, data.error.message);
        }
      },
      error: function (xhr, status, error) {
        grecaptcha.reset();
        showAlert($signupDangerAlert, 'An error occurred. Please try again later.');
        console.log(xhr);
      },
    });
    return false;
  };

  var onUnsubscribeSubmit = function (e) {
    e.preventDefault();

    $.ajax({
      url: '/notifications/unsubscribe-confirmation',
      method: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: {
        'token': unsubscribeToken
      },
      success: function (data) {
        if (data.success) {
          hideAlert($unsubscribeDangerAlert);
          unsubscribeModal.hide();
          unsubscribedModal.show();
        }
        else {
          showAlert($unsubscribeDangerAlert, data.error.message);
        }
      },
      error: function (xhr, status, error) {
        showAlert($unsubscribeDangerAlert, 'An error occurred. Please try again later.');
        console.log(xhr);
      },
    });
    return false;
  };

  var showAlert = function ($alert, text) {
    $alert.text(text).removeClass('d-none');
  };

  var hideAlert = function ($alert) {
    $alert.text('').addClass('d-none');
  };

  var displayNotificationOptinOption = function () {
    var optinLocation = hdxUtil.net.getNotificationOptinLocation();

    if (optinLocation === 'action_menu') {
      $('.notification-platform-opt-in-action-menu').removeClass('d-none');
    }
    else if (optinLocation === 'floating_button') {
      $('.notification-platform-opt-in-floating-button').removeClass('d-none');
    }
  };

  $signupForm.on('submit', onSignupSubmit);
  $signupSubmitButton.on('click', onSignupSubmit);

  $unsubscribeSubmitButton.on('click', onUnsubscribeSubmit);

  if(unsubscribeToken) {
    unsubscribeModal.show();
  }
  else {
    displayNotificationOptinOption();
  }
});

var showNotificationsSignupModal = function (datasetId) {
  var modalShownData = hdxUtil.net.getNotificationModalData() || {};

  if (!modalShownData[datasetId]) {
    notificationsSignupModal.show();

    var newData = {};
    newData[datasetId] = true;
    hdxUtil.net.updateNotificationModalData(newData);
  }
};

var hideNotificationsSignupModal = function () {
  notificationsSignupModal.hide();
};
