$(document).ready(function(){
	//When checkbox is clicked toogle customization fields
	$('#customization-trigger').click(function(e){
		$('#customization-fields').toggle();
		if($('#customization-fields').is(':visible')){
			$('#field-custom_org').prop('checked', true);
		}else{
			$('#field-custom_org').prop('checked', false);
		}
	})

	//On form submit
	$('.create-org-btn').click(function(){
		if($('#field-custom_org').is(':checked')){
			var customization = {
				'highlight_color':$('#field-highlight-color').val(),
				'topline_dataset':$('#field-topline-dataset').val(),
				'topline_resource':$('#field-topline-resource').val()
			}
			$('#customization-json').val(JSON.stringify(customization));
		}
		$('form').submit();
	});
});