$(document).ready(() => {
  _getQuestionData()
    .then((data) => data);

});


function openQAChecklist(resourcesID) {
  $("#qaChecklist").show();
  _initQATabs();
  _getQuestionData()
    .then((questionData) => {
      _populateResourcesTab(resourcesID, questionData.resources_checklist);
      _populateDataProtectionTab(questionData.data_protection_checklist);
      _populateMetadataTab(questionData.metadata_checklist);
    });
}

function _getQuestionData() {
  return new Promise((resolve, reject) => {
    $.get('/api/3/action/qa_questions_list')
      .done((result) => {
        if (result.success) {
          console.log(result.result);
          resolve(result.result);
        } else {
          reject(result);
        }
      })
      .fail((error) => {
        reject(error);
      });
  });
}

function _initQATabs(){
  $("#qaChecklist").find('.qa-checklist-widget .hdx-tab-button').click((ev) => {
    $(ev.currentTarget).tab('show');
  });
}

function _populateDataProtectionTab(questions) {
  let tab = $("#qa-data-protection").html('');
  tab.append(
    `<div class="questions">
      ${Object.keys(questions).map((key, i) => `
        <div><label><input name="${key}" type='checkbox'> ${questions[key]}</label></div>
      `).join('')}
    </div>
    `
  )
}

function _populateMetadataTab(questions) {
  let tab = $("#qa-metadata").html('');
  tab.append(
    `<div class="questions">
      ${Object.keys(questions).map((key, i) => `
        <div><label><input name="${key}" type='checkbox'> ${questions[key]}</label></div>
      `).join('')}
    </div>
    `
  )
}



function _populateResourcesTab(resourcesID, questions){
  let tab = $("#qa-resources").html('');
  tab.append('<ul class="hdx-bs3 resource-list"></ul>');
  let list = tab.find('ul');
  let resources = _getPackageResourceList(resourcesID);
  resources.forEach((res) => {
    list.append(
      `
        <li class="resource-item">
          <a class="heading" title="${res.name || res.description}">
            ${(res.name || res.description).slice(0,50)}
            <span class="format-label" property="dc:format" data-format="${res.format.toLowerCase() || 'data' }">${res.format}</span>
            ${res.in_quarantine ? '<i style="color: red"> - in quarantine</i>' : ''}
          </a>
          <div class="description">
            <span>${res.description}</span>
          </div>
          <div class="questions">
            ${Object.keys(questions).map((key, i) => `
              <div><label><input name="${key}" type='checkbox'> ${questions[key]}</label></div>
            `).join('')}
          </div>
      `);
  });
}
