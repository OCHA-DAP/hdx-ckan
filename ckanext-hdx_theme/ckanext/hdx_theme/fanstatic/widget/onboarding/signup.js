$(document).ready(function(){
    $("#signup-form").on("submit", function(){
        var $this = $(this);
        var email = $("#field-email").val();
        if (email){
            var url = "/user/register_email";
            var data = {
                email: email
            };

            $.post(url, data, function(result_data){
                var result = JSON.parse(result_data);
                console.log(result);
                if (result.success){
                    $("#verifyPopup").find(".verify-email").html(email);
                    closeCurrentWidget($this);showOnboardingWidget('#verifyPopup');
                } else {
                    alert("Can't signup: " + result.error.message);
                }
            });
        }
        return false;
    })
});