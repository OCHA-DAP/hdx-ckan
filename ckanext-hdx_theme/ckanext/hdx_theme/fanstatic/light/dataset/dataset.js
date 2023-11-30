$(document).ready(function() {
  $("#dataset-resources .resource-item-title").on("click", (e) => {
    const target = $(e.currentTarget);
    const icon = target.find(".fa");
    const parent = target.parents(".resource-item");
    const animation_wrapper = parent.find(".animation-wrapper");

    // icon.toggleClass("glyphicon-plus");
    // icon.toggleClass("glyphicon-minus");
    // content.toggle();resour
    if (animation_wrapper.hasClass("closed")) {
      animation_wrapper.removeClass("closed");
      icon.addClass("fa-minus");
      icon.removeClass("fa-plus");
    }
    else {
      animation_wrapper.addClass("closed");
      icon.addClass("fa-plus");
      icon.removeClass("fa-minus");
    }
  });

  $('#show-more-dates, #hide-more-dates').on('click', function(e) {
      e.preventDefault();
      $('#show-more-dates, #hide-more-dates').toggleClass('d-none');
      $('.more-dates').toggleClass('d-none');
  });
});
