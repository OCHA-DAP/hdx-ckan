function showFaqWidget(id) {

    $(id).show();


    function _faqTriggerInputDataClass($this){
        if ($this.val() === "")
            $this.removeClass("input-content");
        else
            $this.addClass("input-content");
    }

    $(id).find('input[type="password"], input[type="text"], textarea').each(
        function(idx, el){
            _faqTriggerInputDataClass($(el));
        }
    );

    $(id).find('input[type="password"], input[type="text"], textarea').change(
        function(){
            var $this = $(this);
            _faqTriggerInputDataClass($this);
        }
    );
    $(id).find('input[type="password"], input[type="text"], textarea').on("keyup",
        function(){
            var $this = $(this);
            _faqTriggerInputDataClass($this);
        }
    );

    $(id).find('input[type="submit"]').on("click", function(){
        var result = faqPrecheckForm(id);
        return !result;
    });

    function faqPrecheckForm(id){
        var error = false;
        $(id).find("input.required, textarea.required, select.required").each(function(idx, el){
            var $el = $(el);
            if ($el.is(":visible") && ($el.val() === null || $el.val() === "")){
                $el.addClass("error");
                error = true;
            } else {
                $el.removeClass("error");
            }
        });
        return error;
    }

    return false;
}

$(document).ready(function(){
    $('#topics-selector').select2();

    faqSendMessageOnSubmit = function(){
        $this = $("#faq-send-message-form");
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");
        //$sel = $($("#faq-send-message-form .select2-container.mTop20.required").find("a:first"));
        //$sel.css("border", "");
        var grecaptchaID = 0;
        var grecaptchaElementID = $("#faq-send-message-form").find(".g-recaptcha-response").prop("id");
        var gRecaptchaResponseText = "g-recaptcha-response-";
        if (grecaptchaElementID && grecaptchaElementID.indexOf(gRecaptchaResponseText) >= 0) {
          var idNum = grecaptchaElementID.substr(grecaptchaElementID.indexOf(gRecaptchaResponseText) + gRecaptchaResponseText.length);
          if (idNum.length > 0){
            grecaptchaID = parseInt(idNum);
          }
        } else {
          if (___grecaptcha_cfg && ___grecaptcha_cfg.count) {
            grecaptchaID = ___grecaptcha_cfg.count - 1;
          }
        }

        var analyticsPromise =
            hdxUtil.analytics.sendMessagingEvent('faq', 'faq',
                $this.find('select[name="topic"]').val(), null, false);
        var postPromise = $.post('/faq/contact_us', $this.serialize());

        $.when(postPromise, analyticsPromise).then(
            function (postData, analyticsData) {
                var result = postData[0];
                if (result.success) {
                    $this[0].reset();
                    closeCurrentWidget($this);
                    showFaqWidget('#faqDonePopup');
                }
                else {
                    if (result.error.message == "Captcha is not valid") {
                        $iframe.css("border", "1px solid red");
                    } else {
                        alert("Can't send your request: " + result.error.message);
                    }
                }
            },
            function(){
                alert("Can't send your request!");
            }
        );
        grecaptcha.reset(grecaptchaID);
    };
    // $('#faq-send-message-form').on('submit', faqSendMessageOnSubmit);

});
