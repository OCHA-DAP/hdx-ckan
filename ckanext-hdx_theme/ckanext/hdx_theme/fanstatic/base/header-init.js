$(document).ready(function(){
    //select 2 everywhere
    $(".hdx-form").find("select").select2({
        allowClear: true
    });

    $(".dropdown.dropdown-on-hover").hover(
        function(){ $(this).addClass('open') },
        function(){ $(this).removeClass('open') }
    );

    function initCookiePopup(){
        var consent = $.cookie("hdx-cookie-consent");
        if (!consent) {
            $(".allow-cookies-container .allow-cookies-continue").click(function () {
               $.cookie("hdx-cookie-consent", true);
               $(".allow-cookies-container").hide();
            });
            $(".allow-cookies-container").show();
        }
    }

    // initCookiePopup();
});