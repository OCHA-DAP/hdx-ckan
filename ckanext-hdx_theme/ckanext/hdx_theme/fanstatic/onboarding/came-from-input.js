$(document).ready(function () {
  var cameFromInput = $('#came-from-input');

  if (cameFromInput.length) {
    var onboardingFlowData = hdxUtil.net.getOnboardingFlowData();
    cameFromInput.val(JSON.stringify(onboardingFlowData));
  }
});
