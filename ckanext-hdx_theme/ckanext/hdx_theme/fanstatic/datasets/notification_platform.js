// modals
var $notificationsSignupModal = $('#notificationsSignupBemModal');
var $verificationModal = $('#notificationsVerificationBemModal');
var $unsubscribeModal = $('#notificationsUnsubscribeBemModal');
var $unsubscribedModal = $('#notificationsUnsubscribedBemModal');

// BS modals
var notificationsSignupModal = bootstrap.Modal.getOrCreateInstance($notificationsSignupModal.get(0));
var verificationModal = bootstrap.Modal.getOrCreateInstance($verificationModal.get(0));
var unsubscribeModal = bootstrap.Modal.getOrCreateInstance($unsubscribeModal.get(0));
var unsubscribedModal = bootstrap.Modal.getOrCreateInstance($unsubscribedModal.get(0));

// signup
var $signupSubmitButton = $notificationsSignupModal.find('button[type="submit"]');
var $signupDangerAlert = $notificationsSignupModal.find('.alert-danger');
var $signupForm = $notificationsSignupModal.find('#notification-platform-form');
var $signupFormPopupSourceInput = $signupForm.find('input[name="popup_source"]');

$(document).ready(function () {
  // unsubscribe
  var $unsubscribeSubmitButton = $unsubscribeModal.find('button[type="submit"]');
  var $unsubscribeDangerAlert = $unsubscribeModal.find('.alert-danger');

  // opt in buttons
  var $actionMenuButton = $('.notification-platform-opt-in-action-menu');
  var $floatingButton = $('.notification-platform-opt-in-floating-button');

  // opt out button
  var $optOutButton = $('.notification-platform-opt-out-action-menu');

  // notification platform data
  var $notificationPlatformData = $('#notification_platform_data');
  var datasetId = null;
  var datasetName = null;
  var unsubscribeToken = null;
  var unsubscribeEmail = null;
  if ($notificationPlatformData.length > 0) {
    datasetId = $notificationPlatformData.data('dataset-id');
    datasetName = $notificationPlatformData.data('dataset-name');
    unsubscribeToken = $notificationPlatformData.data('unsubscribe-token').toLowerCase() !== 'none' ? $notificationPlatformData.data('unsubscribe-token') : null;
    unsubscribeEmail = $notificationPlatformData.data('unsubscribe-email').toLowerCase() !== 'none' ? $notificationPlatformData.data('unsubscribe-email') : null;
  }

  var onSignupSubmit = function (e) {
    e.preventDefault();

    var formDataArray = $signupForm.serializeArray(), formData = {};
    $(formDataArray).each(function (i, field) {
      formData[field.name] = field.value;
    });

    var email = formData.email;

    $.ajax({
      url: '/notifications/subscription-confirmation',
      method: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: {
        'email': email,
        'dataset_id': datasetId,
        'g-recaptcha-response': formData['g-recaptcha-response'],
      },
      success: function (data) {
        grecaptcha.reset();
        if (data.success) {
          hideAlert($signupDangerAlert);
          notificationsSignupModal.hide();

          verificationModal.show();

          hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
            'confirm popup',
            'subscribe to notifications',
            formData.popup_source,
            datasetId,
            datasetName,
            hdxUtil.compute.strHash(email, 'notification_platform')
          );

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

          hdxUtil.net.removeNotificationSubscribedDataset(datasetId);

          hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
            'confirm popup',
            'unsubscribe from notifications',
            null,
            datasetId,
            datasetName,
            hdxUtil.compute.strHash(unsubscribeEmail, 'notification_platform')
          );
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
    var queryString = window.location.search;
    var urlParams = new URLSearchParams(queryString);
    var cameFrom = urlParams.get('came_from');
    var unsubscribeToken = urlParams.get('u');
    if ((cameFrom === 'notification_platform_subscription' || cameFrom === 'notification_platform_email') && unsubscribeToken) {
      hdxUtil.net.addNotificationSubscribedDataset(datasetId, unsubscribeToken);
    }

    var optinLocation = hdxUtil.net.getNotificationOptinLocation(datasetId);

    if (optinLocation === 'action_menu') {
      $actionMenuButton.removeClass('d-none');
    }
    else if (optinLocation === 'floating_button') {
      $floatingButton.removeClass('d-none');
    }
  };

  var displayNotificationOptoutOption = function () {
    var subscribedDatasets = hdxUtil.net.getNotificationSubscribedDatasets();
    if (subscribedDatasets[datasetId]) {
      var unsubscribeToken = subscribedDatasets[datasetId];
      var unsubscribeUrl = '/dataset/' + datasetId + '?unsubscribe_token=' + unsubscribeToken;
      $optOutButton.find('a').attr('href', unsubscribeUrl);
      $optOutButton.removeClass('d-none');
    }
  };

  $signupForm.on('submit', onSignupSubmit);
  $signupSubmitButton.on('click', onSignupSubmit);

  $unsubscribeSubmitButton.on('click', onUnsubscribeSubmit);

  $actionMenuButton.on('click', function(e) {
    e.preventDefault();
    showNotificationsSignupModal('action menu', datasetId, datasetName);
    return false;
  });
  $floatingButton.on('click', function(e) {
    e.preventDefault();
    showNotificationsSignupModal('floating button', datasetId, datasetName);
    return false;
  });

  $notificationsSignupModal.on('hide.bs.modal', function () {
    $signupFormPopupSourceInput.val('');
  });

  if(unsubscribeToken) {
    unsubscribeModal.show();

    hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'unsubscribe from notifications',
      null,
      datasetId,
      datasetName,
      null
    );
  }
  else {
    displayNotificationOptinOption();
    displayNotificationOptoutOption();
  }
});

var showNotificationsSignupModal = function (popupSource, datasetId, datasetName) {
  var modalShownData = hdxUtil.net.getNotificationModalData() || {};

  if (!modalShownData[datasetId] || popupSource !== 'download') {
    notificationsSignupModal.show();
    $signupFormPopupSourceInput.val(popupSource);
    hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'subscribe to notifications',
      popupSource,
      datasetId,
      datasetName,
      null
    );

    if(popupSource === 'download') {
      var newData = {};
      newData[datasetId] = true;
      hdxUtil.net.updateNotificationModalData(newData);
    }
  }
};
