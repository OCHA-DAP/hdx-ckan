function file_upload_selected(){
  $('#field-url').closest('.control-group').hide();
  $('#field-resource-type-upload').click();
}

$(document).ready(function(){
 		$('.dataset-resource-form').submit(function(){
 			if(!$('#field-name').val()){
 				$('#field-name').parent().append('<div class="error-explanation alert alert-error" id="error-license"><p>Please give this file a name.</p></div>');
 				return false;
 			}else{
				$("#loadingScreen").show();
 				return true;
 			}
 		});

 		if($('#mx-file').attr('is-upload') == "True"){
 			file_upload_selected();
 		}


 		$('#field-link-upload').click(function(){
        	$('#field-url').closest('.control-group').show();
    	});

		$('#mx-file').change(function (e) {
			try {
				var html5_file = this.files[0];
				$('#field-name').val( html5_file.name );
				//alert("File size is: " + html5_file.size)
			}
			catch(e) {
				// The browser does not support html5 file api
				//alert("HTML 5 not supported");
				var url = $(this).val();
				if ( url.indexOf('/') >= 0 || url.indexOf('\\') >= 0 ) {
					$('#field-name').val( url.match(/[^\/\\]+$/) );
				}
				else {
					$('#field-name').val(url);
				}
			}

		});


 	});