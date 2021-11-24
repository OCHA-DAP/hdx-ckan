$(document).ready(function(){
  spawnRecaptcha("#recoverPopup");
  showOnboardingWidget('#recoverPopup');
  $("#recoverSuccessPopup .close").click(() => {
    showOnboardingWidget("#loadingScreen");
    location = "/";
  });
});

function onSubmit() {
  $("#recover-form").submit();
}
