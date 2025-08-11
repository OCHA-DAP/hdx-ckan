$(document).ready(function () {
  // unsubscribe
  var unsubscribeToken = $unsubscribeSubmitButton.data('unsubscribe-token').toLowerCase() !== 'none' ? $unsubscribeSubmitButton.data('unsubscribe-token') : null;
  var unsubscribeTokenValidated = $unsubscribeSubmitButton.data('unsubscribe-token-validated').toLowerCase() === 'true' ? $unsubscribeSubmitButton.data('unsubscribe-token-validated') : false;
  var unsubscribeTokenInvalidate = $unsubscribeSubmitButton.data('unsubscribe-token-invalidate').toLowerCase() === 'true' ? $unsubscribeSubmitButton.data('unsubscribe-token-invalidate') : false;

  const unsubscribeObjectId = $unsubscribeSubmitButton.data('object-id');
  const unsubscribeObjectName = $unsubscribeSubmitButton.data('object-name');
  const unsubscribeObjectType = $unsubscribeSubmitButton.data('object-type');

  if (unsubscribeTokenInvalidate) {
    hdxUtil.net.removeNotificationSubscribedTarget(unsubscribeObjectId, unsubscribeObjectType);
  }

  if (unsubscribeToken) {
    if (unsubscribeTokenValidated) {
      unsubscribeModal.show();

      hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
        'show popup',
        'unsubscribe from notifications',
        null,
        unsubscribeObjectId,
        unsubscribeObjectName,
        unsubscribeObjectType,
        null
      );
    } else {
      hdxUtil.net.addNotificationSubscribedTarget(unsubscribeObjectId, unsubscribeObjectType, unsubscribeToken);
      displayNotificationOptoutOption(unsubscribeObjectId, unsubscribeObjectType);
    }
  } else {
    displayNotificationOptinOption(unsubscribeObjectId, unsubscribeObjectType);
    displayNotificationOptoutOption(unsubscribeObjectId, unsubscribeObjectType);
  }

  $unsubscribeSubmitButton.on('click', function (e) {
    e.preventDefault();

    var objectId = $(this).data('object-id');
    var objectName = $(this).data('object-name');
    var objectType = $(this).data('object-type');

    var unsubscribeToken = $(this).data('unsubscribe-token');
    var unsubscribeEmail = $(this).data('unsubscribe-email');
    var unsubscribeSource = $(this).data('unsubscribe-source');

    onUnsubscribeSubmit(objectId, objectName, objectType, unsubscribeToken, unsubscribeEmail, unsubscribeSource);
    return false;
  });
  $unsubscribeHubLink.on('click', function (e) {
    e.preventDefault();

    var objectId = $(this).data('object-id');
    var objectName = $(this).data('object-name');
    var objectType = $(this).data('object-type');

    var unsubscribeToken = $(this).data('unsubscribe-token');
    var unsubscribeEmail = $(this).data('unsubscribe-email');
    var unsubscribeSource = $(this).data('unsubscribe-source');

    onUnsubscribeSubmit(objectId, objectName, objectType, unsubscribeToken, unsubscribeEmail, unsubscribeSource);
    return false;
  });
});
