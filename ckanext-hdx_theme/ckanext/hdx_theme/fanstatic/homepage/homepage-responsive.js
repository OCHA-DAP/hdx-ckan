$(document).ready(function(){
    initMobileCarousel();
    mobileToolTabChange();
});

function mobileToolTabChange(){

  $("input[name='mobile-tool-categories']").change(function() {
    $('.tool.mobile-show').removeClass("mobile-show");
    $('#'+this.value).addClass("mobile-show");
  });

}
var mobileCarouselCurrentItem = 1;
var mobileCarouselItemWidth;
function initMobileCarousel(){
    var carousel = $(".mobile-carousel")[0];
    if(carousel) {
      var hammer = new Hammer(carousel);
      mobileCarouselItemWidth = $(carousel).find('.carousel-item').outerWidth(true);
      var numItems = $(carousel).find('.carousel-item').length;

      hammer.on('swipeleft swiperight', function (ev) {
          if (ev.type=="swipeleft" && mobileCarouselCurrentItem < numItems){
              _carouselSwipe(-1);
          }
          else{
              if (ev.type=="swiperight" && mobileCarouselCurrentItem > 1){
                  _carouselSwipe(+1);
              }
          }
      });
      initMobileCarouselPagination();
    }
}

function _carouselSwipe(delta) {
  let carousel = $(".mobile-carousel")[0];
  const sign = delta > 0 ? "+=" : "-=";


  $(carousel).find('.mobile-carousel-inner').animate({
    left: sign + mobileCarouselItemWidth*Math.abs(delta)
  }, 400);
  mobileCarouselCurrentItem -= delta;
  setMobileCarouselPagination(mobileCarouselCurrentItem);
}

function onCarouselPagination(el) {
  let newItem = parseInt($(el).attr('data-idx'))
  console.log(mobileCarouselCurrentItem + ' - '+ newItem);
  _carouselSwipe(mobileCarouselCurrentItem - newItem);
}

function initMobileCarouselPagination(){
    var carousel = $(".mobile-carousel")[0];
    $(carousel).find('.carousel-indicators').html('');
    for (let i = 0; i < $(carousel).find('.carousel-item').length; i++){
        $(carousel).find('.carousel-indicators').append(`<button type="button" data-idx="${i + 1}" data-bs-target onclick="onCarouselPagination(this);"></button>`);
    }
    $(carousel).find('.carousel-indicators button:first-child').addClass('active');
    $(carousel).find('.carousel-indicators').show();
}

function setMobileCarouselPagination(id){
    var carousel = $(".mobile-carousel")[0];
    $(carousel).find('.carousel-indicators button').removeClass('active');
    $(carousel).find('.carousel-indicators button:nth-child('+id+')').addClass('active');

}

function showPresentationModal(id){
  var modal = $(id);
  var iframe = $(id + ' iframe');
  iframe.attr('src', '');
  modal.modal('show');
  iframe.attr('src', iframe.attr('load-src'));
  iframe.focus();
}
