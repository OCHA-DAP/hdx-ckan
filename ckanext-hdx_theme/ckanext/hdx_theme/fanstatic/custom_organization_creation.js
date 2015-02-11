$(document).ready(function(){
	//When checkbox is clicked toogle customization fields
	$('#customization-trigger').click(function(){
		$('#customization-fields').toggle();
		if($('#field-custom_org').is(':checked')){
			$('#field-custom_org').prop('checked', false);
		}else{
			$('#field-custom_org').prop('checked', true);
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