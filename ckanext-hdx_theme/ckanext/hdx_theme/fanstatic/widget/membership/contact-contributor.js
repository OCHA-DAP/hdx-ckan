$(document).ready(function(){
    $('#topics-selector').select2();

    $('#contact-contributor-form').on('submit', function(){
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");

        return false;
    });

});