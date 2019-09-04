$(document).ready(function() {
  $("#dataset-resources .resource-item-title").on("click", (e) => {
    const target = $(e.currentTarget);
    const icon = target.find(".glyphicon");
    const parent = target.parents(".resource-item");
    const animation_wrapper = parent.find(".animation-wrapper");

    // icon.toggleClass("glyphicon-plus");
    // icon.toggleClass("glyphicon-minus");
    // content.toggle();resour
    if (animation_wrapper.hasClass("closed")) {
      animation_wrapper.removeClass("closed");
      icon.addClass("glyphicon-minus");
      icon.removeClass("glyphicon-plus");
    }
    else {
      animation_wrapper.addClass("closed");
      icon.addClass("glyphicon-plus");
      icon.removeClass("glyphicon-minus");
    }
  });
});
