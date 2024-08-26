$(document).ready(function () {

  var message_sent = $('#message_sent').val();
  var message_subject = $('#message_subject').val();

  if (message_sent && message_sent.toLowerCase() === 'true') {
    var analyticsPromise = hdxUtil.analytics.sendMessagingEvent(
      'dataset',
      'contact contributor',
      message_subject,
      null,
      true
    );

    $.when(analyticsPromise).then(
      function () {
        console.log('Analytics event sent successfully');
      },
      function () {
        console.error('Failed to send the analytics event');
      }
    );
  }
});
