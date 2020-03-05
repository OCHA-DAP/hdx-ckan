$(document).ready(function(){
  $('#registered-form').on("submit", function(){
      $this = $(this);
      $.post('/api/action/hdx_first_login', $this.serialize(), function(result_data){
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
