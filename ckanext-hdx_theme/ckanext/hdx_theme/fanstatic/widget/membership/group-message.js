$(document).ready(function(){
    var $group = $('#group-message-form');
    $group.find("select").select2();
    $group.on('submit', function(){
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");

        return false;
    });

});