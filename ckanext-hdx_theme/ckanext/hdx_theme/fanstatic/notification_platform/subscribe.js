$(document).ready(function () {
  // notification platform data
  const $notificationPlatformData = $('#notification_platform_data');
  const subscribeObjectId = $notificationPlatformData.data('object-id');
  const subscribeObjectName = $notificationPlatformData.data('object-name');
  const subscribeObjectType = $notificationPlatformData.data('object-type');

  $signupForm.on('submit', function (e) {
    e.preventDefault();
    onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType);
    return false;
  });
  $signupSubmitButton.on('click', function (e) {
    e.preventDefault();
    onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType);
    return false;
  });

  $actionMenuButton.on('click', function (e) {
    e.preventDefault();
    showNotificationsSignupModal('action menu', subscribeObjectId, subscribeObjectName, subscribeObjectType);
    return false;
  });
  $floatingButton.on('click', function (e) {
    e.preventDefault();
    showNotificationsSignupModal('floating button', subscribeObjectId, subscribeObjectName, subscribeObjectType);
    return false;
  });

  $notificationsSignupModal.on('hide.bs.modal', function () {
    $signupFormPopupSourceInput.val('');
  });
});
