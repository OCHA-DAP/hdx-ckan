$(document).ready(function(){
    var $contact = $('#contact-contributor-form');
    $contact.find("select").select2();
    _contactContributorFormValidator = function(){
      var contactContributorMessageMsg = $("#contact-contributor-msg");
      var contactContributorSelector = $("#contact-contributor-topics-selector");
      if(contactContributorSelector.val() !== "" && contactContributorMessageMsg.val()!==""){
        $("#submitContactContributorMessage").removeClass("disabled");
      }
      else {
        $("#submitContactContributorMessage").addClass("disabled");
      }
    };
    contactContributorOnSubmit = function(){
        $this = $('#contact-contributor-form');
        var toMessage = $("#membershipDonePopup").find(".to-message ");
        toMessage.hide();

        var analyticsPromise =
            hdxUtil.analytics.sendMessagingEvent('dataset', 'contact contributor',
                $this.find('select[name="topic"]').val(), null, true);
        var postPromise = $.post('/membership/contact_contributor', $this.serialize());

        $.when(postPromise, analyticsPromise).then(
            function (postData, analyticsData) {
                var result = postData[0];
                if (result.success) {
                    closeCurrentWidget($this);
                    showOnboardingWidget('#membershipDonePopup');
                } else {
                    if (result.error) {
                        alert("Can't send your request: " + result.error.message);
                    }
                    grecaptcha.reset();
                }
            },
            function(){
                alert("Can't send your request!");
            }
        );

        return false;
    }
});
