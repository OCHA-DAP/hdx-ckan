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

  $('#show-extra-fields').on('click', function(e) {
    e.preventDefault();
    var $wrapper = $(this).parent();
    var $extraFields = $wrapper.parent().find('.additional-info-extra-fields');
    $wrapper.remove();
    $extraFields.removeClass('d-none');
  });

  $('#showDatasetActivity').on('change', function() {
      $('.dataset-activity-wrapper').toggleClass('d-none');
  });

});
