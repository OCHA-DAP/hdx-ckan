$(document).ready(function(){
  const showDatavizInGallery = "field-in-dataviz-gallery";
  $(`#${showDatavizInGallery}`).change(_onShowDatavizInGalleryChange);
  _onShowDatavizInGalleryChange();
});

function _onShowDatavizInGalleryChange(e){
  const showInGallery = $('#field-in-dataviz-gallery').val();

  const showInCarouselEl = $('#field-in-carousel-section').closest('.control-group');
  const galleryLabelEl = $('#field-dataviz-label').closest('.control-group');
  if (showInGallery === "true") {
    showInCarouselEl.show();
    galleryLabelEl.show();
  } else {
    showInCarouselEl.hide();
    galleryLabelEl.hide();
  }
}

