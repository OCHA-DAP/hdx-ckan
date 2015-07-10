$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    $("#register-form").on("submit", function(){
        $this = $(this);
        $.post("/user/register_details", $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                var actions = {
                    login: $("#register-username").val(),
                    password: $("#register-password").val(),
                    ajax: true
                };
                $.post("/login_generic", $this.serialize(), function(result_data){
                    var result = JSON.parse(result_data);
                    if (result.success){
                        closeCurrentWidget($this);showOnboardingWidget('#registeredPopup');
                    } else {
                        alert("Can't login with the newly created account!");
                    }
                });
            } else {
                alert("Can't register: " + result.error.message);
            }
        });

        return false;
    });
});