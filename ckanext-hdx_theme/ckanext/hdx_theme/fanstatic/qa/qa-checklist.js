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
      _loadQAChecklist(resourcesID);
      _setupQAChecklistEvents(resourcesID);
    });
}

function _toggleChecklistItemDisabled(selector, flag) {
  if (flag) {
    $(selector).attr('disabled', true);
  } else {
     $(selector).removeAttr('disabled');
  }
}


function _checkDisableIndividualChecklistItems(ev) {
  let flag = true;
  if (!($("input.checklist-item").is(":checked"))) {
    flag = false;
  }
  _toggleChecklistItemDisabled("#checklist-complete", flag);
}

function _checkDisableMainQAComplete(ev) {
  if ($(ev.currentTarget).is(":checked")) {
    _toggleChecklistItemDisabled("input.checklist-item", true);
  } else {
    _toggleChecklistItemDisabled("input.checklist-item", false);
  }
}

function _setupQAChecklistEvents(resourceID) {
  $("input.checklist-item").off('change').change(_checkDisableIndividualChecklistItems);

  $("#checklist-complete").off('change').change(_checkDisableMainQAComplete);

  $("#checklist-save").off('click').click(_saveQAChecklist.bind(resourceID));
  $("#checklist-close").off('click').click((ev) => $(ev.currentTarget).parents(".popup").hide());
}

function _getQuestionData() {
  return new Promise((resolve, reject) => {
    $.get({
      url: '/api/3/action/qa_questions_list',
      cache: true
    })
      .done((result) => {
        if (result.success) {
          // console.log(result.result);
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

function _extractChecklistItem(query, collection, checkboxQuery= ".checklist-item") {
  $(query).find(checkboxQuery).toArray().forEach((item) => {
      if ($(item).is(':checked')){
        let code = $(item).attr('name');
        collection[code] = true;
      }
    });
}
function _populateChecklistItem(query, statuses, checkboxQuery= ".checklist-item") {
  $(query).find(checkboxQuery).toArray().forEach((item) => _setChecklistItem(item, statuses));
}
function _setChecklistItem(item, statuses) {
  let code = $(item).attr('name');
  if (statuses[code] === true) {
    $(item).prop('checked', true);
  }
}


function _loadQAChecklist(resourceId) {
  let packageId = $("" + resourceId).attr('data-package-id');

  $.get("/api/action/hdx_package_qa_checklist_show?id=" + packageId)
    .done((result) => {
      let data = result.result;
      $("#checklist-complete").prop('checked', false);
      if (data) {
        _populateChecklistItem("#qa-data-protection", data.dataProtection);
        _populateChecklistItem("#qa-metadata", data.metadata);
        _populateChecklistItem(".qa-checklist-widget", data, "#checklist-complete");
        if (data.resources) {
          data.resources.forEach((resource) => _populateChecklistItem(`.qa-checklist-widget .resource-item[data-resource-id=${resource.id}]`, resource));
        }
      }

      _checkDisableIndividualChecklistItems({currentTarget: ""});
      _checkDisableMainQAComplete({currentTarget: "#checklist-complete"});
    })
    .fail(() => {
      alert("Can't load data QA checklist!!!!");
    });
}

function _saveQAChecklist(event) {
  _updateLoadingMessage("QA checklist saving, please wait ...");
  _showLoading();
  let resourceIdSelector = this;
  let packageId = $("" + resourceIdSelector).attr('data-package-id');

  let data = {
    id: packageId,
    version: 1,
    resources: [],
    dataProtection: {},
    metadata: {}
  };

  $(".qa-checklist-widget .resource-item").toArray().forEach((item) => {
    let resId = $(item).attr('data-resource-id');
    let response = {
      id: resId
    };
    _extractChecklistItem(item, response);
    data.resources.push(response);
  });

  _extractChecklistItem("#qa-data-protection", data.dataProtection);
  _extractChecklistItem("#qa-metadata", data.metadata);
  _extractChecklistItem(".qa-checklist-widget", data, "#checklist-complete");

  $.post("/api/action/hdx_package_qa_checklist_update", JSON.stringify(data))
    .done((result) => {
      if (result.success) {
        _updateLoadingMessage("QA checklist successfully updated! Reloading page ...");
      } else {
        alert("Error, QA checklist not updated!");
        $("#loadingScreen").hide();
      }
    })
    .fail((fail) => {
      alert("Error, QA checklist not updated!");
      $("#loadingScreen").hide();
    })
    .always(() => {
      location.reload();
    });
}

function _initQATabs() {
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
        <li class="resource-item" data-resource-id="${res.id}">
          <a class="heading" title="${res.name || res.description}">
            ${(res.name || res.description).slice(0,50)}
            <span class="format-label" property="dc:format" data-format="${res.format.toLowerCase() || 'data' }">${res.format}</span>
            ${res.in_quarantine ? '<i style="color: red"> under review</i>' : ''}
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
