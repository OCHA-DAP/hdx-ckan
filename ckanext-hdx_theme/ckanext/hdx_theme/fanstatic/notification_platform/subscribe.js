$(document).ready(function () {
  var objectId = null;
  var objectName = null;
  var objectType = null;

  // notification platform data
  var $notificationPlatformData = $('#notification_platform_data');
  if ($notificationPlatformData.length > 0) {
    objectId = $notificationPlatformData.data('object-id');
    objectName = $notificationPlatformData.data('object-name');
    objectType = $notificationPlatformData.data('object-type');
  }

  $signupForm.on('submit', function (e) {
    e.preventDefault();
    onSignupSubmit(objectId, objectName, objectType);
  });
  $signupSubmitButton.on('click', function (e) {
    e.preventDefault();
    onSignupSubmit(objectId, objectName, objectType);
  });

  $actionMenuButton.on('click', function (e) {
    e.preventDefault();
    showNotificationsSignupModal('action menu', objectId, objectName, objectType);
    return false;
  });
  $floatingButton.on('click', function (e) {
    e.preventDefault();
    showNotificationsSignupModal('floating button', objectId, objectName, objectType);
    return false;
  });

  $notificationsSignupModal.on('hide.bs.modal', function () {
    $signupFormPopupSourceInput.val('');
  });
});
