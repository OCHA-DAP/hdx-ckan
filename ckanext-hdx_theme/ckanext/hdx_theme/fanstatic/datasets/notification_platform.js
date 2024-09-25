var $notificationsSignupModal = $('#notificationsSignupBemModal');
var notificationsSignupModal = bootstrap.Modal.getOrCreateInstance($notificationsSignupModal.get(0));

$(document).ready(function () {
  var $verificationModal = $('#notificationsVerificationBemModal');
  var verificationModal = bootstrap.Modal.getOrCreateInstance($verificationModal.get(0));

  var $form = $notificationsSignupModal.find('#notification-platform-form');
  var $submitButton = $notificationsSignupModal.find('button[type="submit"]');
  var $dangerAlert = $notificationsSignupModal.find('.alert-danger');

  var onSubmit = function (e) {
    e.preventDefault();

    $.ajax({
      url: '/notifications/subscription-confirmation',
      method: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: $form.serialize(),
      success: function (data) {
        grecaptcha.reset();
        if (data.success) {
          hideAlert();
          hideNotificationsSignupModal();
          verificationModal.show();
        }
        else {
          showAlert(data.error.message);
        }
      },
      error: function (xhr, status, error) {
        grecaptcha.reset();
        showAlert('An error occurred. Please try again later.');
        console.log(xhr);
      },
    });
    return false;
  };

  var showAlert = function (text) {
    $dangerAlert.text(text).removeClass('d-none');
  };

  var hideAlert = function () {
    $dangerAlert.text('').addClass('d-none');
  };

  var displayNotificationOptinOption = function () {
    var optinLocation = hdxUtil.net.getNotificationOptinLocation();

    if (optinLocation === 'paragraph') {
      $('.notification-platform-opt-in-paragraph').removeClass('d-none');
    }
    else if (optinLocation === 'button') {
      $('.notification-platform-opt-in-button').removeClass('d-none');
    }
  };

  $form.on('submit', onSubmit);
  $submitButton.on('click', onSubmit);

  displayNotificationOptinOption();
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
