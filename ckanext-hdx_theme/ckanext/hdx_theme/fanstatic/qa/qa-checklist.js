function openQAChecklist(resourcesID) {
  $("#qaChecklist").show();
  _initQATabs();
  _populateResourcesTab(resourcesID);
}

function _initQATabs(){
  $("#qaChecklist").find('.qa-checklist-widget .hdx-tab-button').click((ev) => {
    $(ev.currentTarget).tab('show');
  });
}

function _populateResourcesTab(resourcesID){
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
      `);
  });
}
