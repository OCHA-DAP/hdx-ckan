$(document).ready(() => {
  $(".qa-package-item").on("click", (ev) => {
    $('.qa-package-details').hide();
    $('.qa-package-item.open').removeClass('open');
    $(ev.currentTarget).addClass('open');
    let index = $(ev.currentTarget).attr('data-index');
    $(`#qa-package-details-${index}`).show();
  });
});
