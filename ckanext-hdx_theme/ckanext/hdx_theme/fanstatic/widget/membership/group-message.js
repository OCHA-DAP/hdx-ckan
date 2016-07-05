$(document).ready(function(){
    var $group = $('#group-message-form');
    $group.find("select").select2();
    $group.on('submit', function(){
        $this = $(this);
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        closeCurrentWidget($this); showOnboardingWidget('#membershipDonePopup');
        toMessage.find(".to-message-container").text($("#group-message-topics-selector").select2('data').text);
        toMessage.show();
        return false;
    });

});