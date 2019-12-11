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
      _setupQAChecklistEvents();
    });
}

function _toggleChecklistItemDisabled(selector, flag) {
  if (flag) {
    $(selector).attr('disabled', true);
  } else {
     $(selector).removeAttr('disabled');
  }
}

function _setupQAChecklistEvents() {
  $("input.checklist-item").change((ev) => {
    if ($(ev.currentTarget).is(":checked")) {
      _toggleChecklistItemDisabled("#checklist-complete", true);
    } else {
      if (!($("input.checklist-item").is(":checked"))) {
        _toggleChecklistItemDisabled("#checklist-complete", false);
      }
    }
  });

  $("#checklist-complete").change((ev) => {
    if ($(ev.currentTarget).is(":checked")) {
      _toggleChecklistItemDisabled("input.checklist-item", true);
    } else {
      _toggleChecklistItemDisabled("input.checklist-item", false);
    }
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
        <div><label class="checklist-label"><input class="checklist-item" name="${key}" type='checkbox'> <span>${questions[key]}</span></label></div>
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
        <div><label class="checklist-label"><input class="checklist-item" name="${key}" type='checkbox'> <span>${questions[key]}</span></label></div>
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
              <div><label class="checklist-label"><input class="checklist-item" name="${key}" type='checkbox'> <span>${questions[key]}</span></label></div>
            `).join('')}
          </div>
      `);
  });
}
