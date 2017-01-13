$(document).ready(function(){
    var startEditModePopup = function () {
        var url = $('#hxl-preview-edit-url').text();
        var iframe = '<iframe id="hxl-edit-iframe" style="width: 100%; border-style: none" src="' + url +
            '" class="hxl-preview-iframe"> </iframe>';
        $('#hxl-preview-edit-container').html(iframe);
        $('#hxl-preview-popup').show();
    };
    $('#hxl-preview-edit-trigger').on('click', function(){
        startEditModePopup();
    });
    if (window.location.hash == '#hxlEditMode') {
        startEditModePopup();
    }


    $(document.body).on('hxlPreviewSaved', function(event){
        console.log('hxlpreview: "saved" event received');
        $('#hxl-view-iframe')[0].contentWindow.location.reload();
        $('#hxl-preview-popup').hide();
    });
    $(document.body).on('hxlPreviewCancelled', function(event){
        $('#hxl-preview-popup').hide();
    });


});