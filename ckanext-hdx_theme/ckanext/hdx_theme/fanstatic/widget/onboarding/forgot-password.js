$(document).ready(function(){
  showOnboardingWidget('#recoverPopup');
  $("#recoverSuccessPopup .close").click(() => {
    showOnboardingWidget("#loadingScreen");
    location = "/";
  });
});
function onloadRecaptchaFPCallback() {
  spawnRecaptcha("#recoverPopup");
}
function onSubmit() {
  $("#recover-form").submit();
}
