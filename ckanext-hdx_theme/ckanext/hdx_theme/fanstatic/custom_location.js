$(document).ready(function(){
    $('#customization-trigger').click(function(e){
		$('#customization-fields').toggle();
		if($('#customization-fields').is(':visible')){
			$('#field-custom_loc').prop('checked', true);
		}else{
			$('#field-custom_loc').prop('checked', false);
		}
	});
	//On form submit
	$('.create-loc-btn').click(function(){
		//Set timestamp
		if($('#field-custom_loc').is(':checked')){
			var customization = {}
			$('#customization-json').val(JSON.stringify(customization));

		}
		$('form').submit();
	});
});
