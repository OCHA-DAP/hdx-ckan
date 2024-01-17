$(document).ready(function(){
  $('#registered-form').on("submit", function(){
      $this = $(this);
      var csrf_value = $('meta[name=_csrf_token]').attr('content');
      var formData = $this.serialize();
      var postData = formData + '&_csrf_token=' + encodeURIComponent(csrf_value);
      $.post('/api/action/hdx_first_login', postData, function(result_data){
          var result = JSON.parse(JSON.stringify(result_data));
          if (result.success){
              closeCurrentWidget($this);showOnboardingWidget('#followPopup');
          } else {
              alert("Can't move to next step: " + result.error.message);
          }
      });
      return false;
  });
});
