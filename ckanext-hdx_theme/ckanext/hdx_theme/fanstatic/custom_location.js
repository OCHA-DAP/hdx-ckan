$(document).ready(function(){
    $('#customization-trigger').click(function(e){
		$('#customization-fields').toggle();
		if($('#customization-fields').is(':visible')){
			$('#field-custom_loc').prop('checked', true);
		}else{
			$('#field-custom_loc').prop('checked', false);
		}
	});

	$('#chart-select-1, #chart-select-2').click(function(){
		chart_num = $(this).attr('chart-num');
		if(this.value =='multiple bar chart' || this.value == 'multiple line chart'){
			$('#chart_'+chart_num+'_second_line').show();
		}else{
			$('#chart_'+chart_num+'_second_line').hide();
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

			var resource_keys1 = ['chart_dataset_id_1','chart_resource_id_1', 'chart_x_column_1', 'chart_y_column_1']
			var resource_keys2 = ['chart_dataset_id_2','chart_resource_id_2', 'chart_x_column_2', 'chart_y_column_2']


			//Grab chart config
			var charts = []
			var chart1 = {}
			chart1['resources'] = [{},{}]
			$('#chart1 .chart_config').each(function(){
					if($.inArray($(this).attr('name'), resource_keys1) > -1){
						chart1['resources'][0][$(this).attr('name').slice(0,-2)] = this.value;
					}else if($.inArray($(this).attr('name'), resource_keys2) > -1){
						chart1['resources'][1][$(this).attr('name').slice(0,-2)] = this.value;
					}else{
						chart1[$(this).attr('name')] = this.value;
					}
			});

			charts.push(chart1);

			var chart2 = {}
			chart2['resources'] = [{},{}]
			$('#chart2 .chart_config').each(function(){
				if($.inArray($(this).attr('name'), resource_keys1) > -1){
						chart2['resources'][0][$(this).attr('name').slice(0,-2)] = this.value;
					}else if($.inArray($(this).attr('name'), resource_keys2) > -1){
						chart2['resources'][1][$(this).attr('name').slice(0,-2)] = this.value;
					}else{
						chart2[$(this).attr('name')] = this.value;
					}
			});

			charts.push(chart2);

			customization['charts'] = charts;
			customization['map'] = map;
			
			$('#customization-json').val(JSON.stringify(customization));

		}
		$('form').submit();
	});
});
