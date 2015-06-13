function file_upload_selected(){
  $('#field-url').parent().parent().css({'opacity':0, 'height':0});
  $('label.type-file').click();
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

 		$('#field-link-upload').click(function(){
        $('#field-url').parent().parent().css({'opacity':100, 'height':'inherit'});
    });

 		//Add red asterisks
 		$('#field-name').parent().parent().addClass('dataset-required');
 	});