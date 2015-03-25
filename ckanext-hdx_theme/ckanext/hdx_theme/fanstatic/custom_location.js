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
			//Grab misc customization values
			$('.customization_config').each(function(){
					customization[$(this).attr('name')] = this.value;
				});
			//Grab map config
			var map = {}
			$('.map_config').each(function(){
					map[$(this).attr('name')] = this.value;
			});

			//Grab chart config
			var charts = []
			var chart1 = {}
			$('#chart1 .chart_config').each(function(){
					chart1[$(this).attr('name')] = this.value;
			});

			charts.append(chart1);

			var chart2 = {}
			$('#chart2 .chart_config').each(function(){
				chart2[$(this).attr('name')] = this.value;
			});

			charts.append(chart2);

			customization['charts'] = charts;
			customization['map'] = map;
			
			$('#customization-json').val(JSON.stringify(customization));

		}
		$('form').submit();
	});
});
