// signup drawer
var signupDrawer = document.getElementById('notificationsSignupDrawer');
var verificationDrawer = document.getElementById('notificationsVerificationDrawer');
var unsubscribeDrawer = document.getElementById('notificationsUnsubscribeDrawer');
var unsubscribedDrawer = document.getElementById('notificationsUnsubscribedDrawer');

// signup
var signupDangerAlert = signupDrawer ? signupDrawer.querySelector('.c-form-alert') : null;
var signupSubmitButton = signupDrawer ? signupDrawer.querySelector('#notificationsSignupButton') : null;
var signupForm = signupDrawer ? signupDrawer.querySelector('#notification-platform-form') : null;
var signupFormPopupSourceInput = signupForm ? signupForm.querySelector('input[name="popup_source"]') : null;

// unsubscribe
var unsubscribeDangerAlert = unsubscribeDrawer ? unsubscribeDrawer.querySelector('.c-form-alert') : null;
var unsubscribeSubmitButton = unsubscribeDrawer ? unsubscribeDrawer.querySelector('#notificationsUnsubscribeButton') : null;

// opt in buttons
var actionMenuButton = document.querySelector('.notification-platform-opt-in-action-menu');
var floatingButton = document.querySelector('.notification-platform-opt-in-floating-button');

// opt out button
var optOutContainer = document.querySelector('.notification-platform-opt-out-action-menu');
var optOutButton = optOutContainer ? optOutContainer.querySelector('a') : null;

var onUnsubscribeSubmit = function (objectId, objectName, objectType, unsubscribeToken, unsubscribeEmail, unsubscribeSource, authenticated) {
  fetch('/notifications/unsubscribe-confirmation', {
    method: 'POST',
    headers: Object.assign(
      {'Content-Type': 'application/x-www-form-urlencoded'},
      hdxUtil.net.getCsrfTokenAsObject()
    ),
    body: new URLSearchParams({'token': unsubscribeToken})
  })
  .then(function (r) { return r.json(); })
  .then(function (data) {
    if (data.success) {
      hideAlert(unsubscribeDangerAlert);
      window.hdxV2Drawer('notificationsUnsubscribeDrawer').close();
      window.hdxV2Drawer('notificationsUnsubscribedDrawer').open();

      hdxUtil.net.removeNotificationSubscribedTarget(objectId, objectType);

      displayNotificationOptinOption(objectId, objectType);

      hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
        'confirm popup',
        'unsubscribe from notifications',
        null,
        objectId,
        objectName,
        objectType,
        hdxUtil.compute.strHash(unsubscribeEmail, 'notification_platform'),
        authenticated
      );
    } else {
      showAlert(unsubscribeDangerAlert, data.error.message);
    }
  })
  .catch(function (err) {
    var errorMessage = 'An error occurred. Please try again later.';
    showAlert(unsubscribeDangerAlert, errorMessage);
    console.log(err);
  });
};

var onSignupSubmit = function (objectId, objectName, objectType, authenticated) {
  var formData = {};
  new FormData(signupForm).forEach(function (value, key) {
    formData[key] = value;
  });

  var email = formData.email;

  fetch('/notifications/subscription-confirmation', {
    method: 'POST',
    headers: Object.assign(
      {'Content-Type': 'application/x-www-form-urlencoded'},
      hdxUtil.net.getCsrfTokenAsObject()
    ),
    body: new URLSearchParams({
      'email': email,
      'object_id': objectId,
      'object_type': objectType,
      'dataset_updates': formData['dataset_updates'],
      'g-recaptcha-response': formData['g-recaptcha-response']
    })
  })
  .then(function (r) { return r.json(); })
  .then(function (data) {
    if (authenticated && authenticated.toLowerCase() !== 'true') {
      grecaptcha.reset();
    }
    if (data.success) {
      hideAlert(signupDangerAlert);
      window.hdxV2Drawer('notificationsSignupDrawer').close();

      if (actionMenuButton) actionMenuButton.setAttribute('hidden', '');

      window.hdxV2Drawer('notificationsVerificationDrawer').open();

      hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
        'confirm popup',
        'subscribe to notifications',
        formData.popup_source,
        objectId,
        objectName,
        objectType,
        hdxUtil.compute.strHash(email, 'notification_platform'),
        authenticated
      );

      if (data.unsubscribe_token) {
        hdxUtil.net.addNotificationSubscribedTarget(objectId, objectType, data.unsubscribe_token);
        displayNotificationOptoutOption(objectId, objectType);
      }
    } else {
      showAlert(signupDangerAlert, data.error.message);
    }
  })
  .catch(function (err) {
    if (authenticated && authenticated.toLowerCase() !== 'true') {
      grecaptcha.reset();
    }
    var errorMessage = 'An error occurred. Please try again later.';
    showAlert(signupDangerAlert, errorMessage);
    console.log(err);
  });
};

var showAlert = function (alert, text) {
  if (!alert) return;
  alert.textContent = text;
  alert.hidden = false;
};

var hideAlert = function (alert) {
  if (!alert) return;
  alert.textContent = '';
  alert.hidden = true;
};

var displayNotificationOptoutOption = function (objectId, objectType) {
  var subscribedTargets = hdxUtil.net.getNotificationSubscribedObjects(objectType);
  if (subscribedTargets[objectId]) {
    var lSUnsubscribeToken = subscribedTargets[objectId];
    var objectEndpoint = objectType === 'crisis' ? 'event' : objectType;
    var unsubscribeUrl = '/' + objectEndpoint + '/' + objectId + '?_unsubscribe_token=' + lSUnsubscribeToken;
    if (optOutButton) optOutButton.setAttribute('href', unsubscribeUrl);
    if (optOutContainer) optOutContainer.removeAttribute('hidden');
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
    if (actionMenuButton) actionMenuButton.removeAttribute('hidden');
  } else if (optinLocation === 'floating_button') {
    if (actionMenuButton) actionMenuButton.removeAttribute('hidden');
    // if (floatingButton) floatingButton.classList.remove('d-none');
  }
};

var showNotificationsSignupModal = function (popupSource, objectId, objectName, objectType, authenticated) {
  var modalShownData = hdxUtil.net.getNotificationModalData() || {};

  if (!modalShownData[objectType + '_' + objectId] || popupSource !== 'download') {
    window.hdxV2Drawer('notificationsSignupDrawer').open();
    if (signupFormPopupSourceInput) signupFormPopupSourceInput.value = popupSource;
    hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'subscribe to notifications',
      popupSource,
      objectId,
      objectName,
      objectType,
      null,
      authenticated
    );

    if (popupSource === 'download') {
      var newData = {};
      newData[objectType + '_' + objectId] = true;
      hdxUtil.net.updateNotificationModalData(newData);
    }
  }
};
