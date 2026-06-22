document.addEventListener('DOMContentLoaded', function () {
  var notificationPlatformData = document.getElementById('notification_platform_data');
  if (!notificationPlatformData) return;

  var subscribeObjectId   = notificationPlatformData.getAttribute('data-object-id');
  var subscribeObjectName = notificationPlatformData.getAttribute('data-object-name');
  var subscribeObjectType = notificationPlatformData.getAttribute('data-object-type');
  var authenticated       = notificationPlatformData.getAttribute('data-is-authenticated');

  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      e.preventDefault();
      onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
    });
  }

  if (signupSubmitButton) {
    signupSubmitButton.addEventListener('click', function (e) {
      e.preventDefault();
      onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
    });
  }

  if (actionMenuButton) {
    actionMenuButton.addEventListener('click', function (e) {
      e.preventDefault();
      showNotificationsSignupModal('action menu', subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
    });
  }

  if (floatingButton) {
    floatingButton.addEventListener('click', function (e) {
      e.preventDefault();
      showNotificationsSignupModal('floating button', subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
    });
  }

  if (signupDrawer) {
    signupDrawer.addEventListener('drawer:close', function () {
      if (signupFormPopupSourceInput) signupFormPopupSourceInput.value = '';
    });
  }
});
