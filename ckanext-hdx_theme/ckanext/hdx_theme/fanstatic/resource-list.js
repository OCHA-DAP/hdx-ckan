function showDataCheck(url){

  hdxUtil.analytics.sendLinkClickEvent({
    destinationUrl: url,
    linkType: "tools data check"
  });

  var id = "#preview-data-check";
  var modal = $(id);
  var iframe = $(id + ' iframe');

  var baseUrl = window.location.origin;
  var datacheckUrl = 'https://tools.humdata.org/wizard/datacheck';
  if (!url.startsWith("http")) {
    url = baseUrl + url;
  }
  var encodedUrl = encodeURIComponent(url);
  console.log(encodedUrl);
  url = datacheckUrl+"/import;config=%7B%22dataSource%22%3A%22url%22%2C%22_selectedUrl%22%3A%22"+ encodedUrl +"%22%2C%22customValidation%22%3Afalse%2C%22customValidationList%22%3Anull%2C%22ruleTypesMap%22%3A%7B%7D%2C%22embedded%22%3Atrue%2C%22_ruleTypeSelection%22%3A%7B%22%5Ba%5D%20Check%20against%20official%20COD%20sources%20for%20valid%20p-codes%20and%20admin%20unit%20names%22%3Atrue%2C%22%5Bb%5D%20Check%20p-codes%20and%20placenames%20are%20internally%20consistent%20within%20your%20file%22%3Atrue%2C%22%5Bc%5D%20Check%20for%20consistent%20data%20types%20%28dates%2C%20text%2C%20and%20numbers%29%22%3Atrue%2C%22%5Bd%5D%20Check%20for%20values%20that%20deviate%20from%20the%20norm%20for%20a%20column%22%3Atrue%2C%22%5Be%5D%20Check%20for%20white%20space%20errors%22%3Atrue%7D%7D";
  console.log(url);
  iframe.attr('src', '');
  modal.modal('show');
  iframe.attr('src', url);
  iframe.focus();
}
