$(document).ready(function(){
  $('#registered-form').on("submit", function(){
      $this = $(this);
      $.ajax({
          url: '/api/action/hdx_first_login',
          type: 'POST',
          data: $this.serialize(),
          dataType: 'json',
          headers: hdxUtil.net.getCsrfTokenAsObject(),
          success: function(result_data) {
              var result = JSON.parse(JSON.stringify(result_data));
              if (result.success) {
                  closeCurrentWidget($this);
                  showOnboardingWidget('#followPopup');
              } else {
                  alert("Can't move to next step: " + result.error.message);
              }
          }
      });
      return false;
  });
});
