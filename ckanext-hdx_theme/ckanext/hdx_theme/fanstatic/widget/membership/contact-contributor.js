$(document).ready(function(){
    var $contact = $('#contact-contributor-form');
    $contact.find("select").select2();
    $contact.on('submit', function(){
        $this = $(this);
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        $.post('/membership/contact_contributor', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                closeCurrentWidget($this); showOnboardingWidget('#membershipDonePopup');
            } else {
                if (result.error){
                    alert("Can't send your request: " + result.error.message);
                }
            }
        })
            .fail(function(response){
                alert("Can't send your request!");
            });

        return false;
    });

});