function showDataCheck(url){

  hdxUtil.analytics.sendLinkClickEvent({
    destinationUrl: url,
    linkType: "tools data check"
  });

  var id = "#preview-data-check";
  var modal = $(id);
  var iframe = $(id + ' iframe');

  var baseUrl = window.location.origin;
  // var datacheckUrl = 'https://tools.humdata.org/wizard/datacheck';
  var datacheckUrl = '/tools/datacheck';
  if (!url.startsWith("http")) {
    url = baseUrl + url;
  }
  var encodedUrl = encodeURIComponent(url);
  console.log(encodedUrl);

  url = datacheckUrl+"/import;config=%7B%22dataSource%22%3A%22url%22%2C%22_selectedUrl%22%3A%22"+ encodedUrl +"%22%2C%22_selectedRecipeUrl%22%3A%22https%3A%2F%2Fraw.githubusercontent.com%2FOCHA-DAP%2Ftools-datacheck-validation%2Fprod%2Fbasic-validation-schema.json%22%2C%22customValidation%22%3Afalse%2C%22customValidationList%22%3Anull%2C%22ruleTypesMap%22%3A%7B%7D%2C%22embedded%22%3Atrue%2C%22_ruleTypeSelection%22%3A%7B%22%5Ba%5D%20Check%20against%20official%20COD%20sources%20for%20valid%20p-codes%20and%20admin%20unit%20names%22%3Atrue%2C%22%5Bb%5D%20Check%20p-codes%20and%20placenames%20are%20internally%20consistent%20within%20your%20file%22%3Atrue%2C%22%5Bc%5D%20Check%20for%20consistent%20data%20types%20%28dates%2C%20text%2C%20and%20numbers%29%22%3Atrue%2C%22%5Bd%5D%20Check%20for%20values%20that%20deviate%20from%20the%20norm%20for%20a%20column%22%3Atrue%2C%22%5Be%5D%20Check%20for%20white%20space%20errors%22%3Atrue%7D%7D";
  console.log(url);
  iframe.attr('src', '');
  modal.modal('show');
  iframe.attr('src', url);
  iframe.focus();
}
var DATA_USE_SURVEY_LOAD_COUNT;
function showDataUseSurveyPopup(resId, userSurveyUrl) {
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
}
