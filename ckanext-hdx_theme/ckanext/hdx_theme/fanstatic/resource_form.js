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
			var file_name = $(this).val();
			$('#field-name').val(file_name);
		});


 	});