$(document).ready(function() {
  var actionsMenuTimer;
  $(".base-actions-menu .hide-text").hover(
    function (e) {
      actionsMenuTimer = setTimeout(function () {
        $(e.currentTarget).toggleClass("hovering", true);
      }, 350);
    },
    function (e) {
      if (actionsMenuTimer) {
        clearTimeout(actionsMenuTimer);
        actionsMenuTimer = undefined;
      }
      $(e.currentTarget).toggleClass("hovering", false);
    }
  );

  $('#show-extra-dates, #hide-extra-dates').on('click', function(e) {
      e.preventDefault();
      $('#show-extra-dates, #hide-extra-dates').toggleClass('d-none');
      $('.more-dates').toggleClass('d-none');
  });

  $('#show-extra-fields, #hide-extra-fields').on('click', function(e) {
    e.preventDefault();
    $('#show-extra-fields, #hide-extra-fields').toggleClass('d-none');
    $('.additional-info-extra-fields').toggleClass('d-none');
  });

  $('#showDatasetActivity').on('change', function() {
      var checked = $(this).prop('checked');

      var $wrapper = $('.dataset-activity-wrapper');
      var datasetId = $wrapper.data('dataset-id');
      var fetched = $wrapper.data('fetched');

      if(checked) {
        if(fetched === false) {
          fetchActivities(datasetId, 7);
          $wrapper.data('fetched', true);
        }
        $wrapper.removeClass('d-none');
      }
      else {
        $wrapper.addClass('d-none');
      }
  });

  function fetchActivities(datasetId, limit) {
    var $wrapper = $('.dataset-activity-wrapper');
    $.ajax({
      url: '/api/3/action/hdx_package_activity_stream',
      type: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      contentType: 'application/json',
      data: JSON.stringify({
        id: datasetId,
        limit: limit
      }),
      success: function (response) {
        if (response.success) {
          $wrapper.html(response.result);
          var $activities = $wrapper.find('.activity');
          if($.trim($activities.text()) === '') {
            $activities.html('<p>No activities found.</p>');
          }
        } else {
          console.error('Error fetching activities: ', response.error);
        }
      },
      error: function (xhr, status, error) {
        console.error('AJAX error:', status, error);
      }
    });
  }
});
