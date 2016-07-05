$(document).ready(function(){
    var $group = $('#group-message-form');
    $group.find("select").select2();
    $group.on('submit', function(){
        $this = $(this);
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        $.post('/membership/group-message', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                closeCurrentWidget($this); showOnboardingWidget('#membershipDonePopup');
                toMessage.find(".to-message-container").text($("#group-message-topics-selector").select2('data').text);
                toMessage.show();
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