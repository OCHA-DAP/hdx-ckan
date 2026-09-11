document.addEventListener('DOMContentLoaded', function () {
  if (!unsubscribeSubmitButton) return;

  var rawToken = unsubscribeSubmitButton.getAttribute('data-unsubscribe-token') || '';
  var unsubscribeToken = rawToken.toLowerCase() !== 'none' ? rawToken : null;

  var rawValidated = unsubscribeSubmitButton.getAttribute('data-unsubscribe-token-validated') || '';
  var unsubscribeTokenValidated = rawValidated.toLowerCase() === 'true';

  var rawInvalidate = unsubscribeSubmitButton.getAttribute('data-unsubscribe-token-invalidate') || '';
  var unsubscribeTokenInvalidate = rawInvalidate.toLowerCase() === 'true';

  var authenticated        = unsubscribeSubmitButton.getAttribute('data-is-authenticated');
  var unsubscribeObjectId  = unsubscribeSubmitButton.getAttribute('data-object-id');
  var unsubscribeObjectName = unsubscribeSubmitButton.getAttribute('data-object-name');
  var unsubscribeObjectType = unsubscribeSubmitButton.getAttribute('data-object-type');

  if (unsubscribeTokenInvalidate) {
    hdxUtil.net.removeNotificationSubscribedTarget(unsubscribeObjectId, unsubscribeObjectType);
  }

  if (unsubscribeToken) {
    if (unsubscribeTokenValidated) {
      window.hdxV2Drawer('notificationsUnsubscribeDrawer').open();

      hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
        'show popup',
        'unsubscribe from notifications',
        null,
        unsubscribeObjectId,
        unsubscribeObjectName,
        unsubscribeObjectType,
        null,
        authenticated
      );
    } else {
      hdxUtil.net.addNotificationSubscribedTarget(unsubscribeObjectId, unsubscribeObjectType, unsubscribeToken);
      displayNotificationOptoutOption(unsubscribeObjectId, unsubscribeObjectType);
    }
  } else {
    displayNotificationOptinOption(unsubscribeObjectId, unsubscribeObjectType);
    displayNotificationOptoutOption(unsubscribeObjectId, unsubscribeObjectType);
  }

  unsubscribeSubmitButton.addEventListener('click', function (e) {
    e.preventDefault();
    var btn = e.currentTarget;
    onUnsubscribeSubmit(
      btn.getAttribute('data-object-id'),
      btn.getAttribute('data-object-name'),
      btn.getAttribute('data-object-type'),
      btn.getAttribute('data-unsubscribe-token'),
      btn.getAttribute('data-unsubscribe-email'),
      btn.getAttribute('data-unsubscribe-source'),
      btn.getAttribute('data-is-authenticated')
    );
  });
});
