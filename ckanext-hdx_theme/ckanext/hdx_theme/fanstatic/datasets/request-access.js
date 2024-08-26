$(document).ready(function () {

  var request_sent = $('#request_sent').val();

  if (request_sent && request_sent.toLowerCase() === 'true') {
    var analyticsPromise = hdxUtil.analytics.sendMessagingEvent(
      'dataset',
      'data request',
      null,
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

  var $form = $('#request-access-form');
  var $org_select = $form.find('#select-sender_organization_id');
  var $org_type_select = $form.find('#select-sender_organization_type');

  $org_select
    .on('select2:select', function (e) {
      var selected_option = $(this).find(':selected');
      var org_type = selected_option.data('org_type');

      $org_type_select.val((org_type) ? org_type : null).trigger('change');
    })
    .on('select2:clear', function (e) {
      $org_type_select.val(null).trigger('change');
    });

});
