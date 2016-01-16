(function() {
    var hdxUtil = {
        'ui': {}
    };
    window.hdxUtil = hdxUtil;

    hdxUtil.ui.scrollTo = function (target) {
        $('html, body').animate({
            'scrollTop': $(target).offset().top - 40
        }, 700);
    }

})();