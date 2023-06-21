$(document).ready(function(){
    var $contactForm = $('#contact-contributor-form');
    $contactForm.find("select").select2();

    contactContributorOnSubmit = function(){
        $this = $contactForm;
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

    $contactForm.find('input, select, textarea').filter('[required]').on('input change', requiredFieldsFormValidator);
});
