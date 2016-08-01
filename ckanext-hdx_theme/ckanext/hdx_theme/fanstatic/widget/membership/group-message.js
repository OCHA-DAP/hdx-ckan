$(document).ready(function(){
    var $group = $('#group-message-form');
    $group.find("select").select2();
    $group.on('submit', function(){
        $this = $(this);
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        var analyticsPromise =
            hdxUtil.analytics.sendMessagingEvent('dataset', 'group message',
                null, $this.find('select[name="topic"]').val(), true);
        var postPromise = $.post('/membership/contact_members', $this.serialize());

        $.when(postPromise, analyticsPromise).then(
            function (postData, analyticsData) {
                var result = postData[0];
                if (result.success) {
                    closeCurrentWidget($this);
                    showOnboardingWidget('#membershipDonePopup');
                    toMessage.find(".to-message-container").text($("#group-message-topics-selector").select2('data').text);
                    toMessage.show();
                } else {
                    if (result.error) {
                        alert("Can't send your request: " + result.error.message);
                    }
                }
            },
            function(){
                alert("Can't send your request!");
            }
        );

        return false;
    });

});