/**
 *
 * @param {?string} datasetId
 * @param {?string} typeOfCall this is used for analytics, to figure out from where the function was called from, sets [link type]
 * @returns {boolean}
 */
function contributeAddDetails(datasetId, typeOfCall, anchor){
  let popup = $("#addDataPopup");
  let $body = $('body');
  popup.show();
  $body.addClass('contribute-mode');

  let linkType = (typeOfCall ? typeOfCall + ' ' : '') + (datasetId ? 'edit data' : 'add data');
  // hdxUtil.analytics.sendLinkClickEvent({
  //   destinationUrl: '#',
  //   linkType: linkType
  // });

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
}

function _generateContributeFrame(url) {
  let popup = $("#addDataPopup");
  popup.find(".details-content").html("<iframe id='addDataPopupFrame' src='" + url + "'></iframe>");

  var iframe = popup.find('#addDataPopupFrame');
  iframe.on('load', function () {
    const iframeDocument = iframe[0].contentDocument || iframe[0].contentWindow.document;

    $(iframeDocument).on('click', '.close-iframe, .new-header a, .breadcrumb a, .hdx-v2-breadcrumb-row a, .hdx-footer a', function (event) {
      const url = $(this).attr('href');
      const target = $(this).attr('target');
      if (url !== '#' && target !== '_blank') {
        event.preventDefault();
        window.location.href = url;
      }
    });
  });
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

$(document).ready(function() {
  let link = $('.contribute-popup-init:last');
  let datasetId = link.attr('dataset-id');
  if (datasetId !== "DO_IGNORE") {
    prepareContributePopup(datasetId);
  }
});
