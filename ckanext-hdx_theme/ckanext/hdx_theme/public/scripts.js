$('#group_select').change(function(){
          var go = $('#group_select option:selected').val();
          window.location = go;
        });

$('.group_title input').blur(function(){
	var country = this.value;
	//Can we find country on Exversion?
	data = {
		'key':"dbc50657c7",
		'merge':1,
		'query': [{'dataset':"AGMCAZMGC6UF916", 'params':{'properties.name':country}}],
		'_limit': 1
	}
	$.ajax({
		url: "https://exversion.com/api/v1/dataset",
		data: data,
		type: "POST"
	}).success(function(e){
		if(e.body.length > 0){
			var link = 'http://'+$('.group_title span.slug-preview-prefix').text() + $('.group_title SPAN.slug-preview-value').text();
			//Insert url into geojson
			json = e.body[0]
			json.properties.url = link

			//Insert geojson into form
			$('#field-geojson').text(JSON.stringify(json));
		}
	});
});

$('#data-themes').change(function(){
          var go = $('#data-themes option:selected').val();
          window.location = go;
        });