$(document).ready(function() {
  $("#dataset-resources .resource-item-title").on("click", (e) => {
    const target = $(e.currentTarget);
    const icon = target.find(".glyphicon");
    const parent = target.parents(".resource-item");
    const content = parent.find(".content");

    icon.toggleClass("glyphicon-plus");
    icon.toggleClass("glyphicon-minus");
    content.toggle();
  });
});
