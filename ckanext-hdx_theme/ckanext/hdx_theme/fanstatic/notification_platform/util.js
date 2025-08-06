// modals
var $notificationsSignupModal = $('#notificationsSignupBemModal');
var $verificationModal = $('#notificationsVerificationBemModal');
var $unsubscribeModal = $('#notificationsUnsubscribeBemModal');
var $unsubscribedModal = $('#notificationsUnsubscribedBemModal');

// BS modals
var notificationsSignupModal = $notificationsSignupModal.length > 0 ? bootstrap.Modal.getOrCreateInstance($notificationsSignupModal.get(0)) : null;
var verificationModal = $verificationModal.length > 0 ? bootstrap.Modal.getOrCreateInstance($verificationModal.get(0)) : null;
var unsubscribeModal = bootstrap.Modal.getOrCreateInstance($unsubscribeModal.get(0));
var unsubscribedModal = bootstrap.Modal.getOrCreateInstance($unsubscribedModal.get(0));

// signup
var $signupDangerAlert = $notificationsSignupModal.find('.alert-danger');
var $signupSubmitButton = $notificationsSignupModal.find('#notificationsSignupButton');
var $signupForm = $notificationsSignupModal.find('#notification-platform-form');
var $signupFormPopupSourceInput = $signupForm.find('input[name="popup_source"]');

// unsubscribe
var $unsubscribeDangerAlert = $unsubscribeModal.find('.alert-danger');
var $unsubscribeSubmitButton = $unsubscribeModal.find('#notificationsUnsubscribeButton');
var $unsubscribeHubLink = $('.hub-unsubscribe-link');

// opt in buttons
var $actionMenuButton = $('.notification-platform-opt-in-action-menu');
var $floatingButton = $('.notification-platform-opt-in-floating-button');

// opt out button
var $optOutContainer = $('.notification-platform-opt-out-action-menu');
var $optOutButton = $optOutContainer.find('a');

var onUnsubscribeSubmit = function (objectId, objectName, objectType, unsubscribeToken, unsubscribeEmail, unsubscribeSource) {
  var isFromHub = unsubscribeSource === 'hub';

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

        if (isFromHub) {
          $('.hub-unsubscribe-row[data-unsubscribe-token="' + unsubscribeToken + '"]').remove();
          if ($('.hub-unsubscribe-row').length === 0) {
            $('.hub-no-subscriptions').removeClass('d-none');
          }
        }

        hdxUtil.net.removeNotificationSubscribedTarget(objectId, objectType);

        displayNotificationOptinOption(objectId, objectType);

        hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
          'confirm popup',
          'unsubscribe from notifications',
          null,
          objectId,
          objectName,
          objectType,
          hdxUtil.compute.strHash(unsubscribeEmail, 'notification_platform')
        );
      } else {
        showAlert($unsubscribeDangerAlert, data.error.message);
        if (isFromHub) unsubscribeModal.show();
      }
    },
    error: function (xhr, status, error) {
      let errorMessage = 'An error occurred. Please try again later.';
      try {
          const response = JSON.parse(xhr.responseText);
          if (response.error && response.error.message) {
              errorMessage = response.error.message;
          }
      } catch (e) {
          console.error('Failed to parse response: ', e);
      }
      showAlert($unsubscribeDangerAlert, errorMessage);
      if (isFromHub) unsubscribeModal.show();
      console.log(xhr);
    },
  });
};

var onSignupSubmit = function (objectId, objectName, objectType) {
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
      'dataset_updates': formData['dataset_updates'],
      'g-recaptcha-response': formData['g-recaptcha-response'],
    },
    success: function (data) {
      if (!is_authenticated) {
        grecaptcha.reset();
      }
      if (data.success) {
        hideAlert($signupDangerAlert);
        notificationsSignupModal.hide();

        $actionMenuButton.addClass('d-none');

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
          hdxUtil.net.addNotificationSubscribedTarget(objectId, objectType, data.unsubscribe_token);
          displayNotificationOptoutOption(objectId, objectType);
        }
      } else {
        showAlert($signupDangerAlert, data.error.message);
      }
    },
    error: function (xhr, status, error) {
      if (!is_authenticated) {
        grecaptcha.reset();
      }
      let errorMessage = 'An error occurred. Please try again later.';
      try {
          const response = JSON.parse(xhr.responseText);
          if (response.error && response.error.message) {
              errorMessage = response.error.message;
          }
      } catch (e) {
          console.error('Failed to parse response: ', e);
      }
      showAlert($signupDangerAlert, errorMessage);
      console.log(xhr);
    },
  });
};

var showAlert = function ($alert, text) {
  $alert.text(text).removeClass('d-none');
};

var hideAlert = function ($alert) {
  $alert.text('').addClass('d-none');
};

var displayNotificationOptoutOption = function (objectId, objectType) {
  var subscribedTargets = hdxUtil.net.getNotificationSubscribedObjects(objectType);
  if (subscribedTargets[objectId]) {
    var lSUnsubscribeToken = subscribedTargets[objectId];
    var objectEndpoint = objectType === 'crisis' ? 'event' : objectType;
    var unsubscribeUrl = '/' + objectEndpoint + '/' + objectId + '?_unsubscribe_token=' + lSUnsubscribeToken;
    $optOutButton.attr('href', unsubscribeUrl);
    $optOutContainer.removeClass('d-none');
  }
};

var displayNotificationOptinOption = function (objectId, objectType) {
  var queryString = window.location.search;
  var urlParams = new URLSearchParams(queryString);
  var cameFrom = urlParams.get('_came_from');
  var urlUnsubscribeToken = urlParams.get('_u');
  if ((cameFrom === 'notification_platform_subscription' || cameFrom === 'notification_platform_email') && urlUnsubscribeToken) {
    hdxUtil.net.addNotificationSubscribedTarget(objectId, objectType, urlUnsubscribeToken);
  }

  var optinLocation = hdxUtil.net.getNotificationOptinLocation(objectId, objectType);

  if (optinLocation === 'action_menu') {
    $actionMenuButton.removeClass('d-none');
  } else if (optinLocation === 'floating_button') {
    $actionMenuButton.removeClass('d-none');
    // $floatingButton.removeClass('d-none');
  }
};

var showNotificationsSignupModal = function (popupSource, objectId, objectName, objectType) {
  var modalShownData = hdxUtil.net.getNotificationModalData() || {};

  if (!modalShownData[objectType + '_' + objectId] || popupSource !== 'download') {
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

    if (popupSource === 'download') {
      var newData = {};
      newData[objectType + '_' + objectId] = true;
      hdxUtil.net.updateNotificationModalData(newData);
    }
  }
};
