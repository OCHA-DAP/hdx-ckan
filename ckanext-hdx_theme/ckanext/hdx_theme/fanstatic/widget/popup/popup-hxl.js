$(document).ready(function(){
    $('#hxl-preview-edit-trigger').on('click', function(){
       var url = $('#hxl-preview-edit-url').text();
       var iframe = '<iframe data-module="hdx-hxl-preview" style="width: 100%; border-style: none" src="' + url +
           '" class="hxl-preview-iframe"> </iframe>';
       $('#hxl-preview-edit-container').html(iframe);
       $('#hxl-preview-popup').show();
    });


});