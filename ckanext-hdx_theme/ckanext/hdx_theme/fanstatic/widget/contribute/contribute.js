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
    var url = datasetId ? '/contribute/edit/'+datasetId : '/contribute/new';
    popup.find(".details-content").html("<iframe src='" + url + "'></iframe>");

    return false;
}