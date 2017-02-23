function contributeAddDetails(datasetId){
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