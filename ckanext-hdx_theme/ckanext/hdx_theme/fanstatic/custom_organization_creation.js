$(document).ready(function(){
    $('.create-org header ul').hide();
	$('#field-highlight-color').spectrum({
		preferredFormat: "hex",
		showInput: true,
});
	$('.visualization_colors').spectrum({preferredFormat: "hex",
showInput: true});
	//When checkbox is clicked toogle customization fields
	$('#customization-trigger').click(function(e){
		$('#customization-fields').toggle();
		if($('#customization-fields').is(':visible')){
			$('#field-custom_org').prop('checked', true);
		}else{
			$('#field-custom_org').prop('checked', false);
		}
	});

	$('#field-highlight-color').change(function(){
		color = this.value;
		var rainbow = new Rainbow(); 
		rainbow.setNumberRange(1, 9);
		rainbow.setSpectrum(lighterColor(color, .5), darkerColor(color, .5));
		for (var i = 1; i <= 9; i++) {
    		$('#color-'+i).spectrum("set", rainbow.colourAt(i));
		}
	});

	//On form submit
	$('.create-org-btn').click(function(){
		//Set timestamp
		$('#field-modified_at').val(new Date().getTime())
		if($('#field-custom_org').is(':checked')){
            var use_org_color = "false"
            if($('#use_org_color').is(':checked'))
                use_org_color = "true"
			var customization = {
				'highlight_color':$('#field-highlight-color').val(),
				'topline_dataset':$('#field-topline-dataset').val(),
				'topline_resource':$('#field-topline-resource').val(),
                'use_org_color':use_org_color
			}
			$('#customization-json').val(JSON.stringify(customization));

			//Build visualization slug
			var visualization = {}
			var arrays = []
			$('.visualization_config').each(function(){
				//if this is an array, perserve it.
				if($.inArray($(this).attr('name').slice(0,-2), arrays) > -1){
					visualization[$(this).attr('name').slice(0,-2)].push(this.value);
				}
				else if($(this).attr('name').slice(-2) == '[]'){
					arrays.push($(this).attr('name').slice(0,-2));
					visualization[$(this).attr('name').slice(0,-2)] = [this.value];
				}else{
					visualization[$(this).attr('name')] = this.value;
				}
			});
			$('#visualization-json').val(JSON.stringify(visualization));
		}
		$('form').submit();
	});
});

var pad = function(num, totalChars) {
    var pad = '0';
    num = num + '';
    while (num.length < totalChars) {
        num = pad + num;
    }
    return num;
};

// Ratio is between 0 and 1
var changeColor = function(color, ratio, darker) {
    // Trim trailing/leading whitespace
    color = color.replace(/^\s*|\s*$/, '');

    // Expand three-digit hex
    color = color.replace(
        /^#?([a-f0-9])([a-f0-9])([a-f0-9])$/i,
        '#$1$1$2$2$3$3'
    );

    // Calculate ratio
    var difference = Math.round(ratio * 256) * (darker ? -1 : 1),
        // Determine if input is RGB(A)
        rgb = color.match(new RegExp('^rgba?\\(\\s*' +
            '(\\d|[1-9]\\d|1\\d{2}|2[0-4][0-9]|25[0-5])' +
            '\\s*,\\s*' +
            '(\\d|[1-9]\\d|1\\d{2}|2[0-4][0-9]|25[0-5])' +
            '\\s*,\\s*' +
            '(\\d|[1-9]\\d|1\\d{2}|2[0-4][0-9]|25[0-5])' +
            '(?:\\s*,\\s*' +
            '(0|1|0?\\.\\d+))?' +
            '\\s*\\)$'
        , 'i')),
        alpha = !!rgb && rgb[4] != null ? rgb[4] : null,

        // Convert hex to decimal
        decimal = !!rgb? [rgb[1], rgb[2], rgb[3]] : color.replace(
            /^#?([a-f0-9][a-f0-9])([a-f0-9][a-f0-9])([a-f0-9][a-f0-9])/i,
            function() {
                return parseInt(arguments[1], 16) + ',' +
                    parseInt(arguments[2], 16) + ',' +
                    parseInt(arguments[3], 16);
            }
        ).split(/,/),
        returnValue;

    // Return RGB(A)
    return !!rgb ?
        'rgb' + (alpha !== null ? 'a' : '') + '(' +
            Math[darker ? 'max' : 'min'](
                parseInt(decimal[0], 10) + difference, darker ? 0 : 255
            ) + ', ' +
            Math[darker ? 'max' : 'min'](
                parseInt(decimal[1], 10) + difference, darker ? 0 : 255
            ) + ', ' +
            Math[darker ? 'max' : 'min'](
                parseInt(decimal[2], 10) + difference, darker ? 0 : 255
            ) +
            (alpha !== null ? ', ' + alpha : '') +
            ')' :
        // Return hex
        [
            '#',
            pad(Math[darker ? 'max' : 'min'](
                parseInt(decimal[0], 10) + difference, darker ? 0 : 255
            ).toString(16), 2),
            pad(Math[darker ? 'max' : 'min'](
                parseInt(decimal[1], 10) + difference, darker ? 0 : 255
            ).toString(16), 2),
            pad(Math[darker ? 'max' : 'min'](
                parseInt(decimal[2], 10) + difference, darker ? 0 : 255
            ).toString(16), 2)
        ].join('');
};
var lighterColor = function(color, ratio) {
    return changeColor(color, ratio, false);
};
var darkerColor = function(color, ratio) {
    return changeColor(color, ratio, true);
};
