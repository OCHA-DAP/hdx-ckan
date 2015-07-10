$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    $("#register-form").on("submit", function(){
        $this = $(this);
        $.post("/user/register_details", $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                $.post("/login_generic", $this.serialize(), function(result_data){
                    closeCurrentWidget($this);showOnboardingWidget('#registeredPopup');
                });
            } else {
                alert("Can't register: " + result.error.message);
            }
        });

        return false;
    });
});