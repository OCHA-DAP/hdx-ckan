
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {

    var messageSentInput = document.getElementById('message_sent');
    var messageSent = messageSentInput ? messageSentInput.value : null;
    var messageSubjectInput = document.getElementById('message_subject');
    var messageSubject = messageSubjectInput ? messageSubjectInput.value : null;

    if (messageSent && messageSent.toLowerCase() === 'true') {
      var analyticsPromise = hdxUtil.analytics.sendMessagingEvent(
        'dataset',
        'contact contributor',
        messageSubject,
        null,
        true
      );

      analyticsPromise.then(
        function () {
          console.log('Analytics event sent successfully');
        },
        function () {
          console.error('Failed to send the analytics event');
        }
      );
    }
  });
})();
