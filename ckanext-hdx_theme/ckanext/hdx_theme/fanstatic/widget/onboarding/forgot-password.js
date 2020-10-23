$(document).ready(function(){
  showOnboardingWidget('#recoverPopup');
  $("#recoverSuccessPopup .close").click(() => {
    showOnboardingWidget("#loadingScreen");
    location = "/";
  });
});
