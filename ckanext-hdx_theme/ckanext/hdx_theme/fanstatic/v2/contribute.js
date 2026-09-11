/**
 *
 * @param {?string} datasetId
 * @param {?string} typeOfCall this is used for analytics, to figure out from where the function was called from, sets [link type]
 * @returns {boolean}
 */
function contributeAddDetails(datasetId, typeOfCall, anchor){
  let popup = document.getElementById('addDataPopup');
  popup.style.display = 'block';
  document.body.classList.add('contribute-mode');


  let linkType = (typeOfCall ? typeOfCall + ' ' : '') + (datasetId ? 'edit data' : 'add data');
  // hdxUtil.analytics.sendLinkClickEvent({
  //   destinationUrl: '#',
  //   linkType: linkType
  // });

  if (popup.getAttribute('dataset-id') != String(datasetId)) {
    prepareContributePopup(datasetId);
  }
  if (anchor) {
    document.getElementById('addDataPopupFrame').src = _getContributeURL(datasetId, anchor);
  }

  return false;
}

function prepareContributePopup(datasetId, anchor) {
  let popup = document.getElementById('addDataPopup');
  popup.setAttribute('dataset-id', String(datasetId));
  let url = _getContributeURL(datasetId, anchor);
  _generateContributeFrame(url);
}

function _generateContributeFrame(url) {
  let popup = document.getElementById('addDataPopup');
  popup.querySelector('.details-content').innerHTML = "<iframe id='addDataPopupFrame' src='" + url + "'></iframe>";

  let iframe = document.getElementById('addDataPopupFrame');
  iframe.addEventListener('load', function () {
    const iframeDocument = iframe.contentDocument || iframe.contentWindow.document;

    iframeDocument.addEventListener('click', function (event) {
      const link = event.target.closest('.close-iframe, .new-header a, .breadcrumb a, .hdx-v2-breadcrumb-row a, .hdx-footer a');
      if (!link) {
        return;
      }
      const url = link.getAttribute('href');
      const target = link.getAttribute('target');
      if (url !== '#' && target !== '_blank') {
        event.preventDefault();
        window.location.href = url;
      }
    });
  });
}

function _getContributeURL(datasetId, anchor) {
  let url;
  let popup = document.getElementById('addDataPopup');
  if (datasetId && datasetId !== "null") {
    url = '/contribute/edit/'+datasetId;
    popup.classList.add('edit-mode');
  }
  else {
    url = '/contribute/new';
    popup.classList.remove('edit-mode');
  }
  if (anchor) {
    url += anchor;
  }
  return url;
}

document.addEventListener('DOMContentLoaded', function() {
  let links = document.querySelectorAll('.contribute-popup-init');
  if (!links.length) {
    return;
  }
  let link = links[links.length - 1];
  let datasetId = link.getAttribute('dataset-id');
  if (datasetId !== "DO_IGNORE") {
    prepareContributePopup(datasetId);
  }
});
