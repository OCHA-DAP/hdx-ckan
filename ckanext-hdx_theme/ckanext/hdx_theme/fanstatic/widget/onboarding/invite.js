$(document).ready(function(){
    $('#invite-form').on('submit', function(){
        $this = $(this);
        $.post('/user/invite_friends', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                closeCurrentWidget($this);showOnboardingWidget('#donePopup');
            } else {
                alert("Can't invite friends: " + result.error.message);
            }
        });
        return false;
    });
});