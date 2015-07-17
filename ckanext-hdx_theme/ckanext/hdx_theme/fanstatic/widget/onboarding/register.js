$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    $("#register-form").on("submit", function () {
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");
        $.post("/user/register_details", $this.serialize(), function (result_data) {
            var result = JSON.parse(result_data);
            if (result.success) {
                $.post("/login_generic", $this.serialize())
                .fail(function (data, status, xhr) {
                    var status = data.status;
                    var redirect_url = data.getResponseHeader('Location');
                    if (status = 302 && redirect_url && redirect_url.indexOf('logged_in') > 0) {
                        // Repoze returns by default a redirect to /user/logged_in which
                        // causes the AJAX request to fail
                        closeCurrentWidget($this);
                        showOnboardingWidget('#registeredPopup');
                    }
                })
                .done(function (data, status, xhr) {
                    closeCurrentWidget($this);
                    showOnboardingWidget('#registeredPopup');
                });

            } else {
                if (result.error.message == "Captcha is not valid"){
                    $iframe.css("border", "1px solid red");
                } else {
                    alert("Can't register: " + JSON.stringify(result.error.message));
                }
            }
        });

        return false;
    });
});