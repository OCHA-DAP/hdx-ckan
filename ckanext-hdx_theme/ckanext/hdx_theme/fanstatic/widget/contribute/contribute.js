/**
 *
 * @param {?string} datasetId
 * @param {?string} typeOfCall this is used for analytics, to figure out from where the function was called from, sets [link type]
 * @returns {boolean}
 */
function contributeAddDetails(datasetId, typeOfCall){

    var popup = $("#addDataPopup");
    popup.show();
    //$.ajax({
    //    url: '/contribute/new',
    //    type: 'GET',
    //    //dataType: 'JSON',
    //    context: this,
    //    success: function (result) {
    //        popup.find(".details-content").html(result);
    //    }
    //});
    var linkType = (typeOfCall ? typeOfCall + ' ' : '') + (datasetId ? 'edit data' : 'add data');
    hdxUtil.analytics.sendLinkClickEvent({
      destinationUrl: '#',
      linkType: linkType
    });

    var url;
    if (datasetId) {
        url = '/contribute/edit/'+datasetId;
        popup.addClass('edit-mode');
    }
    else {
        url = '/contribute/new';
        popup.removeClass('edit-mode');
    }
    popup.find(".details-content").html("<iframe src='" + url + "'></iframe>");

    return false;
}
