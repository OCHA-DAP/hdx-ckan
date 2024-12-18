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
});
