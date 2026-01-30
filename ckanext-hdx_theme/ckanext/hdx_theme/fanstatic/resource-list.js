var DATA_USE_SURVEY_LOAD_COUNT;
function showDataUseSurveyPopup(resId, datasetId, datasetName, datasetSupportsNotifications, userSurveyUrl, authenticated) {
  const orgName = $("#dataUseSurveyOrgName").text();

  const SURVEY_KEY = "/organization:" + "hdx-data-use-survey-popup-" + orgName;
  DATA_USE_SURVEY_LOAD_COUNT = 0;
  function _iframeOnLoadCount() {
    DATA_USE_SURVEY_LOAD_COUNT++;
    console.log(`Load count: ${DATA_USE_SURVEY_LOAD_COUNT}`);
    if (DATA_USE_SURVEY_LOAD_COUNT > 1){
      window.localStorage.setItem(SURVEY_KEY, "true");
    }
  }
  let surveyStatus = window.localStorage.getItem(SURVEY_KEY);
  const iframe = $("#dataUseSurveyPopup .survey-widget iframe");
  iframe.prop('src', '');
  iframe[0].removeEventListener("load", _iframeOnLoadCount);

  const userSurveyIsValid = userSurveyUrl && userSurveyUrl !== '' && userSurveyUrl !== 'None';
  if (userSurveyIsValid && !surveyStatus) {
    $("#dataUseSurveyPopup a.btn-primary").click(function (e) {
      hdxUtil.analytics.sendSurveyEvent('confirm popup');
      const pkgId = $("#dataUseSurveyPkgId").text() || "";
      const pkgUrl = $("#dataUseSurveyPkgUrl").text() || "";
      const orgName = $("#dataUseSurveyOrgName").text() || "";

      userSurveyUrl = userSurveyUrl.replaceAll('hdx_organization_name', orgName);
      // userSurveyUrl = userSurveyUrl.replaceAll('hdx_dataset_id', pkgId);
      userSurveyUrl = userSurveyUrl.replaceAll('hdx_dataset_id', pkgUrl);
      userSurveyUrl = userSurveyUrl.replaceAll('hdx_resource_id', resId);
      // console.log(`org[${orgName}] pkg[${pkgId}] res[${resId}]`);

      $("#dataUseSurveyPopup .survey-widget .survey-content").hide();

      iframe.show();
      iframe.prop('src', userSurveyUrl);
      iframe[0].addEventListener("load", _iframeOnLoadCount);
    });
    hdxUtil.analytics.sendSurveyEvent('show popup');
    $("#dataUseSurveyPopup .survey-widget .survey-content").show();
    iframe.hide();
    $("#dataUseSurveyPopup").show();
  }
  else if(datasetSupportsNotifications.toString() === 'true') {
    var objectType = 'dataset';
    var subscribedTargets = hdxUtil.net.getNotificationSubscribedObjects(objectType);
    if (!subscribedTargets[datasetId]) {
        showNotificationsSignupModal('download', datasetId, datasetName, objectType, authenticated);
    }
  }
}

$('.resource-download-button').on('click', function (event) {
  var resId = $(this).data('resource-id');
  var datasetId = $(this).data('dataset-id');
  var datasetName = $(this).data('dataset-name');
  var datasetSupportsNotifications = $(this).data('dataset-supports-notifications');
  var userSurveyUrl = $(this).data('user-survey-url');
  var authenticated = $(this).data('is-authenticated');

  showDataUseSurveyPopup(resId, datasetId, datasetName, datasetSupportsNotifications, userSurveyUrl, authenticated);

  return true;
});
