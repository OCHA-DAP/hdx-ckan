$(document).ready(function(){
    var $contact = $('#contact-contributor-form');
    $contact.find("select").select2();
    $contact.on('submit', function(){
        $this = $(this);
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        closeCurrentWidget($this); showOnboardingWidget('#membershipDonePopup');

        return false;
    });

});