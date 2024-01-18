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

  $('#show-more-dates, #hide-more-dates').on('click', function(e) {
      e.preventDefault();
      $('#show-more-dates, #hide-more-dates').toggleClass('d-none');
      $('.more-dates').toggleClass('d-none');
  });

  $('#showDatasetActivity').on('change', function() {
      $('.dataset-activity-wrapper').toggleClass('d-none');
  });

});
