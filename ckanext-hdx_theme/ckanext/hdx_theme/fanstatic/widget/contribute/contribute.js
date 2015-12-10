function contributeAddDetails(){
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
    popup.find(".details-content").html("<iframe src='/contribute/new'></iframe>");

    return false;
}