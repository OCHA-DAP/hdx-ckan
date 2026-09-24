document.addEventListener('DOMContentLoaded', function () {
  var notificationPlatformData = document.getElementById('notification_platform_data');
  if (!notificationPlatformData) return;

  var subscribeObjectId   = notificationPlatformData.getAttribute('data-object-id');
  var subscribeObjectName = notificationPlatformData.getAttribute('data-object-name');
  var subscribeObjectType = notificationPlatformData.getAttribute('data-object-type');
  var authenticated       = notificationPlatformData.getAttribute('data-is-authenticated');

  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      if (e.defaultPrevented) return;
      e.preventDefault();
      onSignupSubmit(subscribeObjectId, subscribeObjectName, subscribeObjectType, authenticated);
    });
  }

  if (signupSubmitButton) {
    signupSubmitButton.addEventListener('click', function (e) {
      e.preventDefault();
      signupForm.requestSubmit();
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

  document.addEventListener('click', function (e) {
    var downloadButton = e.target.closest('.resource-download-button');
    if (!downloadButton) return;
    if (!downloadButton.closest('.c-resource-card')) return;

    if (downloadButton.getAttribute('data-dataset-supports-notifications') !== 'true') return;

    var downloadDatasetId = downloadButton.getAttribute('data-dataset-id');
    var subscribedTargets = hdxUtil.net.getNotificationSubscribedObjects('dataset');
    if (subscribedTargets[downloadDatasetId]) return;

    showNotificationsSignupModal(
      'download',
      downloadDatasetId,
      downloadButton.getAttribute('data-dataset-name'),
      'dataset',
      downloadButton.getAttribute('data-is-authenticated')
    );
  });

  if (signupDrawer) {
    signupDrawer.addEventListener('drawer:close', function () {
      if (signupFormPopupSourceInput) signupFormPopupSourceInput.value = '';
    });
  }
});
