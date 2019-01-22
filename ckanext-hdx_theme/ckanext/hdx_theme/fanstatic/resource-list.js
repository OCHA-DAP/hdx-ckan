function showDataCheck(url){
  var id = "#preview-data-check";
  var modal = $(id);
  var iframe = $(id + ' iframe');

  var baseUrl = 'https://feature-data.humdata.org';
  var datacheckUrl = 'http://localhost:4202';
  var encodedUrl = encodeURIComponent(baseUrl + url);
  console.log(encodedUrl);
  url = datacheckUrl+"/import;config=%7B%22dataSource%22:%22url%22,%22_selectedUrl%22:%22"+ encodedUrl +",%22_selectedRecipeUrl%22:%22https:%2F%2Fraw.githubusercontent.com%2FOCHA-DAP%2Ftools-datacheck-validation%2Fprod%2Fbasic-validation-schema.json%22,%22customValidation%22:false,%22customValidationList%22:null,%22ruleTypesMap%22:%7B%7D,%22_ruleTypeSelection%22:%7B%22%5Ba%5D%20Check%20for%20consistent%20data%20types%20%28dates,%20text,%20and%20numbers%29%22:true,%22%5Bb%5D%20Check%20for%20values%20that%20deviate%20from%20the%20norm%20for%20a%20column%22:true,%22%5Bc%5D%20Check%20for%20white%20space%20errors%22:true%7D%7D;config=%7B%22dataSource%22%3A%22url%22%2C%22_selectedUrl%22%3A%22https%3A%2F%2Ffeature-data.humdata.org%2Fdataset%2F0c20b278-cd81-44ed-ab00-4e1b85328054%2Fresource%2F711ed563-6e21-4b10-8ef4-1c33515b34ec%2Fdownload%2Ffts_funding_mmr.csv%22%2C%22_selectedRecipeUrl%22%3A%22https%3A%2F%2Fraw.githubusercontent.com%2FOCHA-DAP%2Ftools-datacheck-validation%2Fprod%2Fbasic-validation-schema.json%22%2C%22customValidation%22%3Afalse%2C%22customValidationList%22%3Anull%2C%22ruleTypesMap%22%3A%7B%7D%2C%22embedded%22%3Atrue%2C%22_ruleTypeSelection%22%3A%7B%22%5Ba%5D%20Check%20for%20consistent%20data%20types%20%28dates%2C%20text%2C%20and%20numbers%29%22%3Atrue%2C%22%5Bb%5D%20Check%20for%20values%20that%20deviate%20from%20the%20norm%20for%20a%20column%22%3Atrue%2C%22%5Bc%5D%20Check%20for%20white%20space%20errors%22%3Atrue%7D%7D";
  console.log(url);
  iframe.attr('src', '');
  modal.modal('show');
  iframe.attr('src', url);
  iframe.focus();
}
