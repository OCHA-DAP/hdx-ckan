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
  var objectId = null;
  var objectName = null;
  var objectType = null;
  var unsubscribeToken = null;
  var unsubscribeTokenValidated = null;
  var unsubscribeEmail = null;
  if ($notificationPlatformData.length > 0) {
    objectId = $notificationPlatformData.data('object-id');
    objectName = $notificationPlatformData.data('object-name');
    objectType = $notificationPlatformData.data('object-type');
    unsubscribeToken = $notificationPlatformData.data('unsubscribe-token').toLowerCase() !== 'none' ? $notificationPlatformData.data('unsubscribe-token') : null;
    unsubscribeTokenValidated = $notificationPlatformData.data('unsubscribe-token-validated').toLowerCase() !== 'none' ? $notificationPlatformData.data('unsubscribe-token-validated') : null;
    unsubscribeEmail = $notificationPlatformData.data('unsubscribe-email').toLowerCase() !== 'none' ? $notificationPlatformData.data('unsubscribe-email') : null;
  }

  var onSignupSubmit = function (e) {
    e.preventDefault();

    var formDataArray = $signupForm.serializeArray(), formData = {};
    $(formDataArray).each(function (i, field) {
      formData[field.name] = field.value;
    });

    var email = formData.email;
    var is_authenticated = formData.is_authenticated.toLowerCase() === 'true';

    $.ajax({
      url: '/notifications/subscription-confirmation',
      method: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: {
        'email': email,
        'object_id': objectId,
        'object_type': objectType,
        'g-recaptcha-response': formData['g-recaptcha-response'],
      },
      success: function (data) {
        if(!is_authenticated) {
          grecaptcha.reset();
        }
        if (data.success) {
          hideAlert($signupDangerAlert);
          notificationsSignupModal.hide();

          verificationModal.show();

          hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
            'confirm popup',
            'subscribe to notifications',
            formData.popup_source,
            objectId,
            objectName,
            objectType,
            hdxUtil.compute.strHash(email, 'notification_platform')
          );

          if (data.unsubscribe_token) {
            hdxUtil.net.addNotificationSubscribedTarget(objectId, data.unsubscribe_token);
          }
        }
        else {
          showAlert($signupDangerAlert, data.error.message);
        }
      },
      error: function (xhr, status, error) {
        if(!is_authenticated) {
          grecaptcha.reset();
        }
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

          hdxUtil.net.removeNotificationSubscribedTarget(objectId);

          hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
            'confirm popup',
            'unsubscribe from notifications',
            null,
            objectId,
            objectName,
            objectType,
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
      hdxUtil.net.addNotificationSubscribedTarget(objectId, unsubscribeToken);
    }

    var optinLocation = hdxUtil.net.getNotificationOptinLocation(objectId);

    if (optinLocation === 'action_menu') {
      $actionMenuButton.removeClass('d-none');
    }
    else if (optinLocation === 'floating_button') {
      $actionMenuButton.removeClass('d-none');
      // $floatingButton.removeClass('d-none');
    }
  };

  var displayNotificationOptoutOption = function () {
    var subscribedTargets = hdxUtil.net.getNotificationSubscribedObjects();
    if (subscribedTargets[objectId]) {
      var unsubscribeToken = subscribedTargets[objectId];
      var unsubscribeUrl = '/dataset/' + objectId + '?unsubscribe_token=' + unsubscribeToken;
      $optOutButton.find('a').attr('href', unsubscribeUrl);
      $optOutButton.removeClass('d-none');
    }
  };

  $signupForm.on('submit', onSignupSubmit);
  $signupSubmitButton.on('click', onSignupSubmit);

  $unsubscribeSubmitButton.on('click', onUnsubscribeSubmit);

  $actionMenuButton.on('click', function(e) {
    e.preventDefault();
    showNotificationsSignupModal('action menu', objectId, objectName, objectType);
    return false;
  });
  $floatingButton.on('click', function(e) {
    e.preventDefault();
    showNotificationsSignupModal('floating button', objectId, objectName, objectType);
    return false;
  });

  $notificationsSignupModal.on('hide.bs.modal', function () {
    $signupFormPopupSourceInput.val('');
  });

  if(unsubscribeTokenValidated && unsubscribeTokenValidated.toLowerCase() === 'false') {
    hdxUtil.net.removeNotificationSubscribedTarget(objectId);
  }

  if(unsubscribeToken) {
    unsubscribeModal.show();

    hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'unsubscribe from notifications',
      null,
      objectId,
      objectName,
      objectType,
      null
    );
  }
  else {
    displayNotificationOptinOption();
    displayNotificationOptoutOption();
  }
});

var showNotificationsSignupModal = function (popupSource, objectId, objectName, objectType) {
  var modalShownData = hdxUtil.net.getNotificationModalData() || {};

  if (!modalShownData[objectId] || popupSource !== 'download') {
    notificationsSignupModal.show();
    $signupFormPopupSourceInput.val(popupSource);
    hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'subscribe to notifications',
      popupSource,
      objectId,
      objectName,
      objectType,
      null
    );

    if(popupSource === 'download') {
      var newData = {};
      newData[objectType] = true;
      hdxUtil.net.updateNotificationModalData(newData);
    }
  }
};
