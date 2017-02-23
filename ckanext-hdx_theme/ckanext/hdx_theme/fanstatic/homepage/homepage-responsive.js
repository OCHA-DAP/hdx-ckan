$(document).ready(function(){
    initMobileCarousel();
});

function initMobileCarousel(){
    var carousel = document.getElementById('mobileCarousel');
    var hammer = new Hammer(carousel);
    var itemW = $(carousel).find('.item').outerWidth(true);
    var numItems = $(carousel).find('.item').length;
    var currItem = 1;
    hammer.on('swipeleft swiperight', function (ev) {
        if (ev.type=="swipeleft" && currItem < numItems){
            $(carousel).find('.mobile-carousel-inner').animate({
                left: "-=" + itemW
            }, 400);
            currItem++;
        }
        else{
            if (ev.type=="swiperight" && currItem > 1){
                $(carousel).find('.mobile-carousel-inner').animate({
                    left: "+=" + itemW
                }, 400);
                currItem--;
            }
        }
        setMobileCarouselPagination(currItem);
    });
    initMobileCarouselPagination();
}

function initMobileCarouselPagination(){
    var carousel = document.getElementById('mobileCarousel');
    $(carousel).find('.carousel-indicators').html('');
    for (var i=0; i<$(carousel).find('.item').length; i++){
        $(carousel).find('.carousel-indicators').append('<li></li>');
    }
    $(carousel).find('.carousel-indicators li:first-child').addClass('active');
    $(carousel).find('.carousel-indicators').show();
}

function setMobileCarouselPagination(id){
    var carousel = document.getElementById('mobileCarousel');
    $(carousel).find('.carousel-indicators li').removeClass('active');
    $(carousel).find('.carousel-indicators li:nth-child('+id+')').addClass('active');

}
