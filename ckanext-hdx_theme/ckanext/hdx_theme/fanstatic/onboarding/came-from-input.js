(function () {
  var input = document.getElementById('came-from-input');
  if (input) {
    input.value = JSON.stringify(hdxUtil.net.getOnboardingFlowData());
  }
})();
