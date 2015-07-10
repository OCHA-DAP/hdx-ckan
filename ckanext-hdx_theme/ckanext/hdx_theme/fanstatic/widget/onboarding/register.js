$(document).ready(function(){
    showOnboardingWidget('#registerPopup');

    $("#register-form").on("submit", function(){
        $this = $(this);
        $.post("/user/register_details", $this.serialize(), function(result){
            console.log(result);
        });

        return false;
    });
});