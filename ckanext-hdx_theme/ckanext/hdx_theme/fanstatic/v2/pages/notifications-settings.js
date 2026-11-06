// ============================================================
// notifications-settings.js — v2 Notifications Settings (task 078)
// - Unsubscribe → fill + open the drawers of
//   templates/notification_platform/unsubscribe_drawers.html
// - Confirm → onUnsubscribeSubmit (notification_platform/util.js)
// - Closing the Unsubscribed drawer reloads the page
// ============================================================
(function () {
  'use strict';

  var UNSUBSCRIBE_DRAWER_ID = 'notificationsUnsubscribeDrawer';
  var UNSUBSCRIBED_DRAWER_ID = 'notificationsUnsubscribedDrawer';
  var SUBMIT_ID = 'notificationsUnsubscribeButton';
  var current = null;

  function openDrawer(trigger) {
    var drawer = document.getElementById(UNSUBSCRIBE_DRAWER_ID);
    var unsubscribedDrawer = document.getElementById(UNSUBSCRIBED_DRAWER_ID);
    var submit = document.getElementById(SUBMIT_ID);
    if (!drawer || !unsubscribedDrawer || !submit) return;
    current = JSON.parse(trigger.getAttribute('data-notifications-unsubscribe'));

    drawer.querySelector('.c-drawer-form__text').textContent = current.confirmation_text;
    drawer.querySelector('.c-alert').hidden = true;
    unsubscribedDrawer.querySelector('.c-alert__message').textContent = current.unsubscribed_text;

    window.hdxV2Drawer(UNSUBSCRIBE_DRAWER_ID).open();
    window.hdxUtil.analytics.sendNotificationPlatformPopupInteractionEvent(
      'show popup',
      'unsubscribe from notifications',
      null,
      current.object_id,
      current.object_name,
      current.object_type,
      null,
      submit.getAttribute('data-is-authenticated')
    );
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var trigger = e.target.closest('[data-notifications-unsubscribe]');
    if (trigger) {
      openDrawer(trigger);
      return;
    }
    var submit = e.target.closest('#' + SUBMIT_ID);
    if (submit && current) {
      e.preventDefault();
      onUnsubscribeSubmit(
        current.object_id,
        current.object_name,
        current.object_type,
        current.token,
        current.email,
        null,
        submit.getAttribute('data-is-authenticated')
      );
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    var unsubscribedDrawer = document.getElementById(UNSUBSCRIBED_DRAWER_ID);
    if (!unsubscribedDrawer) return;
    unsubscribedDrawer.addEventListener('drawer:close', function () {
      window.location.reload();
    });
  });

})();
