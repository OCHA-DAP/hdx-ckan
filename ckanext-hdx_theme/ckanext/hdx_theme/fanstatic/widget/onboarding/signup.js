$(document).ready(function(){
    const $signupForm = $('#signup-form');

    signupFormOnSubmit = function(){
        var $this = $(this);
        var email = $("#field-email").val();
        if (email){
            var url = "/user/register_email";
            var data = {
                email: email,
                signup: $("#signup-send-updates").prop("checked"),
                'g-recaptcha-response': grecaptcha.getResponse()
            };

            $.post(url, data, function(result_data){
                var result = JSON.parse(result_data);
                console.log(result);
                if (result.success){
                    hdxUtil.analytics.sendUserRegisteredEvent("submit email register").then(function() {
                        //check for newsletter - we're moving the registration to the backend
                        // if ($("#signup-send-updates").is(":checked")){
                        //     console.log("Attempt to register to newsletter!");
                        //     $.ajax({
                        //         url: "//unocha.us2.list-manage.com/subscribe/post-json",
                        //         dataType: "jsonp",
                        //         jsonp: "c",
                        //         data: {
                        //             u: "83487eb1105d72ff2427e4bd7",
                        //             id: "6fd988326c",
                        //             EMAIL: email,
                        //             subscribe: "Subscribe",
                        //             _: Date.now()
                        //         },
                        //         success: function(result){
                        //             if (result.result == "success")
                        //                 console.log("Registered to the newsletter!");
                        //             else
                        //                 console.log("Error:" + JSON.stringify(result));
                        //         }
                        //     });
                        // }

                        $("#verifyPopup").find(".verify-email").html(email);
                        closeCurrentWidget($(".signup-widget:first"));
                        showOnboardingWidget('#verifyPopup');
                    });
                } else {
                    var errMsg = $signupForm.find(".error-message");
                    errMsg.text(result.error.message);
                    $("#field-email").addClass("error");
                    errMsg.show();
                }
            });
        }
        grecaptcha.reset();
        return false;
    };
    // $("#signup-form").on("submit", signupFormOnSubmit)

    $signupForm.find('input, select, textarea').filter('[required]').on('input change', requiredFieldsFormValidator);
});
