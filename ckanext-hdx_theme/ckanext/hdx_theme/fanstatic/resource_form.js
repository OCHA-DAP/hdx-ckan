$(document).ready(function(){
 		$('.dataset-resource-form').submit(function(){
 			if(!$('#field-name').val()){
 				$('#field-name').parent().append('<div class="error-explanation alert alert-error" id="error-license"><p>Please give this file a name.</p></div>');
 				return false;
 			}else{
 				return true;
 			}
 		});
 	});