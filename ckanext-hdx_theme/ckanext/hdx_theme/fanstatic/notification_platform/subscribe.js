$(document).ready(function () {
  // notification platform data
  const $notificationPlatformData = $('#notification_platform_data');
  const subscribeObjectId = $notificationPlatformData.data('object-id');
  const subscribeObjectName = $notificationPlatformData.data('object-name');
  const subscribeObjectType = $notificationPlatformData.data('object-type');
  const authenticated = $notificationPlatformData.data('is-authenticated');

  if($signupForm) {
    $signupForm.on('submit', function (e) {
      e.preventDefault();
      onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
      return false;
    });
  }
  if($signupSubmitButton) {
    $signupSubmitButton.on('click', function (e) {
      e.preventDefault();
      onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
      return false;
    });
  }

  if($actionMenuButton) {
    $actionMenuButton.on('click', function (e) {
      e.preventDefault();
      showNotificationsSignupModal('action menu', subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
      return false;
    });
  }
  if($floatingButton) {
    $floatingButton.on('click', function (e) {
      e.preventDefault();
      showNotificationsSignupModal('floating button', subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
      return false;
    });
  }

  if($notificationsSignupModal) {
    $notificationsSignupModal.on('hide.bs.modal', function () {
      $signupFormPopupSourceInput.val('');
    });
  }
});
