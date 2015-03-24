$(document).ready(function(){
    $('#customization-trigger').click(function(e){
		$('#customization-fields').toggle();
		if($('#customization-fields').is(':visible')){
			$('#field-custom_loc').prop('checked', true);
		}else{
			$('#field-custom_loc').prop('checked', false);
		}
	});

	$('#chart-select').change(function(){
		if(this.value =='multiple bar chart' || this.value == 'multiple line chart'){
			$('#second-line').show();
		}else{
			$('#second-line').hide();
		}
	})
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
