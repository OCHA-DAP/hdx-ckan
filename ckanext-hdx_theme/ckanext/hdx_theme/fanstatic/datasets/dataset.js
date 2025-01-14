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
      $('.dataset-activity-wrapper').toggleClass('d-none');
  });

});
