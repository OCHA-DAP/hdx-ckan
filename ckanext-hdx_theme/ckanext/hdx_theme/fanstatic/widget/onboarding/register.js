$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    const $registerForm = $('#register-form');

    $registerForm.on("submit", function () {
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");
        $.ajax({
          url: "/user/register_details",
          type: 'POST',
          data: $this.serialize(),
          headers: hdxUtil.net.getCsrfTokenAsObject(),
          success: function (result_data) {
            var result = JSON.parse(result_data);
            if (result.success) {
              $this.unbind("submit");
              $this.attr("action", "/user/login?came_from=/dataset");
              hdxUtil.analytics.sendUserRegisteredEvent("user register").then(function () {
                $this.submit();
              });
            } else {
              if (result.error.message == "Captcha is not valid") {
                $iframe.css("border", "1px solid red");
              } else {
                alert("Can't register: " + result.error.message);
                // grecaptcha.reset();
              }
            }
          }
        });

        return false;
    });

    $registerForm.find('input, select, textarea').filter('[required]').on('input change', requiredFieldsFormValidator);
});
