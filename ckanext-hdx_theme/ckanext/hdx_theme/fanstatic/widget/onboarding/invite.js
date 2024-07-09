$(document).ready(function(){
    $('#invite-form').on('submit', function(){
        $this = $(this);
      $.ajax({
        url: '/user/invite_friends',
        type: 'POST',
        data: $this.serialize(),
        headers: hdxUtil.net.getCsrfTokenAsObject(),
        success: function (result_data) {
          var result = JSON.parse(result_data);
          if (result.success) {
            closeCurrentWidget($this);
            showOnboardingWidget('#donePopup');
          } else {
            alert("Can't invite friends: " + result.error.message);
          }
        }
      });

        return false;
    });
});
