/**
 *
 * @param {?string} datasetId
 * @param {?string} typeOfCall this is used for analytics, to figure out from where the function was called from, sets [link type]
 * @returns {boolean}
 */
function contributeAddDetails(datasetId, typeOfCall, anchor){
  let popup = $("#addDataPopup");
  popup.show();

  let linkType = (typeOfCall ? typeOfCall + ' ' : '') + (datasetId ? 'edit data' : 'add data');
  hdxUtil.analytics.sendLinkClickEvent({
    destinationUrl: '#',
    linkType: linkType
  });

  if (popup.attr('dataset-id') != String(datasetId)) {
    prepareContributePopup(datasetId);
  }
  if (anchor) {
    $("#addDataPopupFrame").prop("src", _getContributeURL(datasetId, anchor));
  }

  return false;
}

function prepareContributePopup(datasetId, anchor) {
  let popup = $("#addDataPopup");
  popup.attr('dataset-id', String(datasetId));
  let url = _getContributeURL(datasetId, anchor);
  _generateContributeFrame(url);
  popup.find(".humanitarianicons-Exit-Cancel").click(_contributePopupReset);
}

function _generateContributeFrame(url) {
  let popup = $("#addDataPopup");
  popup.find(".details-content").html("<iframe id='addDataPopupFrame' src='" + url + "'></iframe>");
}
function _getContributeURL(datasetId, anchor) {
  let url;
  let popup = $("#addDataPopup");
  if (datasetId && datasetId !== "null") {
    url = '/contribute/edit/'+datasetId;
    popup.addClass('edit-mode');
  }
  else {
    url = '/contribute/new';
    popup.removeClass('edit-mode');
  }
  if (anchor) {
    url += anchor;
  }
  return url;
}

function _contributePopupReset() {
  console.log("resetting popup");
  const $addDataPopupFrame = $("#addDataPopupFrame");
  let src = $addDataPopupFrame.prop('src');
  $addDataPopupFrame.closest(".details-content").html('');
  _generateContributeFrame(src);
}

$(document).ready(function() {
  let link = $('.contribute-popup-init:last');
  let datasetId = link.attr('dataset-id');
  if (datasetId !== "DO_IGNORE") {
    prepareContributePopup(datasetId);
  }
});
