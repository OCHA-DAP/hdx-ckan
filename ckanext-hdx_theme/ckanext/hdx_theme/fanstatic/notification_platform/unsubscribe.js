$(document).ready(function () {
  // unsubscribe
  var $unsubscribeSubmitButton = $unsubscribeModal.find('button[type="submit"]');
  var $unsubscribeHubLink = $('.hub-unsubscribe-link');
  var unsubscribeToken = $unsubscribeSubmitButton.data('unsubscribe-token').toLowerCase() !== 'none' ? $unsubscribeSubmitButton.data('unsubscribe-token') : null;
  var unsubscribeTokenValidated = $unsubscribeSubmitButton.data('unsubscribe-token-validated').toLowerCase() === 'true' ? $unsubscribeSubmitButton.data('unsubscribe-token-validated') : false;

  var objectId = $unsubscribeSubmitButton.data('object-id');
  var objectName = $unsubscribeSubmitButton.data('object-name');
  var objectType = $unsubscribeSubmitButton.data('object-type');

  $unsubscribeSubmitButton.on('click', onUnsubscribeSubmit);
  $unsubscribeHubLink.on('click', onUnsubscribeSubmit);

  if (unsubscribeToken) {
    if (unsubscribeTokenValidated) {
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
    } else {
      hdxUtil.net.addNotificationSubscribedTarget(objectId, objectType, unsubscribeToken);
      displayNotificationOptoutOption(objectId, objectType);
    }
  } else {
    displayNotificationOptinOption(objectId, objectType);
    displayNotificationOptoutOption(objectId, objectType);
  }
});
