$(document).ready(function(e){
    $(".popup:not(.popup-close-only-x)").on("click", function(){
       $(this).hide();
    });
    $(".popup:not(.popup-close-only-x) .content").on("click", function(e){
        e.stopPropagation(); //do not propagate click
    });
    $(".popup i.close").on("click", function(e){
        $(this).parents(".popup").hide();
    });

});
