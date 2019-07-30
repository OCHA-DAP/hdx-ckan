$(document).ready(function(e){
    $(".bottom-banner .content").on("click", function(e){
        e.stopPropagation(); //do not propagate click
    });
    // $(".bottom-banner i.close").on("click", function(e){
    //     $(this).parents(".bottom-banner").hide();
    // });

    function initBannerPopup(id){
        var viewedBanner = $.cookie(id);
        if (!viewedBanner) {
            $("#" + id + " .close").click(function () {
               $.cookie(id, true);
               $("#"+id).hide();
            });
            $("#"+id).show();
        }
    }

    initBannerPopup('hdx-dataset-banner');
    initBannerPopup('hdx-dataset-light-banner');

});
