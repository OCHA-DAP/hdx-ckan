function positionWarningBar() {

    var win = $(window);
    var windowTop = win.scrollTop();
    var windowBottom = windowTop + win.height();

    var footerTop = $('.newFooter').offset().top;

    var datasetsCountTop = $('#datasets-count').offset().top;

    var warningBar = $('.hdx-warning');

    if (windowBottom < footerTop) {
        warningBar.css('position', 'fixed');
    }
    else {
        warningBar.css('position', 'absolute');
    }

    if ( datasetsCountTop > warningBar.offset().top ){
        warningBar.css('visibility', 'hidden');
    }
    else {
        warningBar.css('visibility', 'visible');
    }
}
$(document).ready(function(){
    $(window).scroll(positionWarningBar);
    positionWarningBar();
});