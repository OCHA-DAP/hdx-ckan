$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    $("#register-form").on("submit", function () {
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");
        $.post("/user/register_details", $this.serialize(), function (result_data) {
            var result = JSON.parse(result_data);
            if (result.success) {
                $this.unbind("submit");
                $this.attr("action", "/login_generic");
                hdxUtil.analytics.sendUserRegisteredEvent().then(function(){
                    $this.submit();
                });
            } else {
                if (result.error.message == "Captcha is not valid"){
                    $iframe.css("border", "1px solid red");
                } else {
                    alert("Can't register: " + result.error.message);
                    grecaptcha.reset();

                }
            }
        });

        return false;
    });
});