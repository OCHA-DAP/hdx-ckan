$(document).ready(() => {
  $(".qa-package-item").on("click", (ev) => {
    $('.qa-package-details').hide();
    let index = $(ev.currentTarget).attr('data-index');
    $(`#qa-package-details-${index}`).show();
  });
});
