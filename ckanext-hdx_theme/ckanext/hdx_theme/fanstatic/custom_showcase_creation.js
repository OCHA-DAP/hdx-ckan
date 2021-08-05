/*jshint esversion: 6 */

$(document).ready(function(){
  const showDatavizInGallery = "field-in-dataviz-gallery";
  $(`#${showDatavizInGallery}`).change(_onShowDatavizInGalleryChange);
  _onShowDatavizInGalleryChange();
});

function _onShowDatavizInGalleryChange(e){
  const showInGallery = $('#field-in-dataviz-gallery').val();

  const gallerySection = $('#dataviz-gallery-section');
  if (showInGallery === "true") {
    gallerySection.show();
  } else {
    gallerySection.hide();
  }
}

