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
		//Set timestamp
		$('#field-modified_at').val(new Date().getTime())
		if($('#field-custom_org').is(':checked')){
			var customization = {
				'highlight_color':$('#field-highlight-color').val(),
				'topline_dataset':$('#field-topline-dataset').val(),
				'topline_resource':$('#field-topline-resource').val()
			}
			$('#customization-json').val(JSON.stringify(customization));

			//Build visualization slu
			var visualization = {}
			$('.visualization_config').each(function(){
				visualization[$(this).attr('name')] = this.value;
			});
			$('#visualization-json').val(JSON.stringify(visualization));
		}
		$('form').submit();
	});
});