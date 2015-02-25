var options = {
    pcode: null,
    value: null,
    pcodeSelectorId: "#pcode",
    valueSelectorId: "#value",
    baseLayer: null,
    invertLatLong: true,
    boundaryPoly:{
        minLat: 0,
        maxLat: 0,
        minLong: 0,
        maxLong: 0
    },
    data: null,
    fields: null,
    geoData: null,
    pcodeMap: {}

};

function getData(options){
    //call DataProxy to get data for resource
    $.ajax({
        url:"http://192.168.59.103:5001",
        data:{
            url: "http://192.168.59.103:5000/dataset/mali-pcode/resource_download/ff4f1c6e-ba46-4195-b30a-e77c6b8dd676",
            "max-results": 100000,
            type: "csv",
            format: "json"
        },
        dataType: 'json',
        success:function(data){
            // do stuff with json (in this case an array)
            processData(options, data);
        },
        error:function(error){
            console.log(error);
        }
    });

    //call back
}

function processData(options, data){
    function getDataPcodes(options) {
    }

    function setFields(options) {
        function pcodeOnChange(){
            options.pcode = $(this).val();
            getGeoData(options);
        }
        function valueOnChange(){
            options.value = $(this).val();
            processValues(options);
        }

        var pcode = $(options.pcodeSelectorId);
        var value = $(options.valueSelectorId);

        var optsPcode = "<option value='null'>---Select---</option>";
        var optsValue = "<option value='null'>---Select---</option>";
        for (var i in options.fields){
            var extraPcode = "", extraValue = "";
            if (i == options.pcode)
                extraPcode = "selected='selected'";
            if (i == options.value)
                extraValue = "selected='selected'";

            optsPcode += "<option value='"+i+"' " + extraPcode + ">" + options.fields[i] + "</option>"
            optsValue += "<option value='"+i+"' " + extraValue + ">" + options.fields[i] + "</option>"
        }

        pcode.children().remove();
        value.children().remove();

        pcode.append(optsPcode);
        value.append(optsValue);

        //setup listeners
        pcode.change(pcodeOnChange);
        value.change(valueOnChange);

    }

    //get list of pcodes
    options.data = data.data;
    options.fields = data.fields;

    setFields(options);
    getDataPcodes(options);


    if (options.pcode != null)
        getGeoData(options);
}

function getGeoData(options){
    options.geoData = null;
    $.ajax({
        url:"/api/action/hdx_get_pcode_mapper_values",
        dataType: 'jsonp',
        success:function(data){
            // do stuff with json (in this case an array)
            processGeoData(options, JSON.parse(data.result));
        },
        error:function(error){
            console.log(error);
        }
    });
}

function processGeoData(options, data){
    function computeBondaryPoly(options, data) {
        //Need to compute Top-Left corner and Bottom-Right corner for polygon.
        var minLat, minLng, maxLat, maxLng;
        var init = false;

        //Use a stack to traverse the geojson since we can gave many levels of arrays in arrays
        var stackArrays = [];
        var stackIndex = [];

        for (var featureIdx in data.features){
            var featureItem = data.features[featureIdx];
            stackArrays.push(featureItem.geometry.coordinates);
            stackIndex.push(0);
        }
        //stackArrays.push(data.geometry.coordinates);
        //stackIndex.push(0);
        while (stackArrays.length > 0){
            var array = stackArrays.pop();
            var index = stackIndex.pop();

            if (index < array.length){
                var item = array[index];
                //check if we reached a tuple of coordinates
                if (!$.isArray(item)){
                    //if (options.invertLatLong){
                    //    var temp = array[0];
                    //    array[0] = array[1];
                    //    array[1] = temp;
                    //}

                    var lat = parseFloat(array[1]);
                    var lng = parseFloat(array[0]);
                    //adjust min/max
                    if (init){
                        if (lat < minLat)
                            minLat = lat;
                        if (lat > maxLat)
                            maxLat = lat;
                        if (lng < minLng)
                            minLng = lng;
                        if (lng > maxLng)
                            maxLng = lng;
                    } else {
                        init = true;
                        minLat = maxLat = lat;
                        minLng = maxLng = lng;
                    }
                }
                //push in the stack the current array with the next index
                index++;
                stackArrays.push(array);
                stackIndex.push(index);
                //if we haven't reached a tuple of coordinates, add in the stack the array
                if ($.isArray(item)){
                    stackArrays.push(item);
                    stackIndex.push(0);
                }
            }
        }

        options.boundaryPoly.minLat = minLat;
        options.boundaryPoly.maxLat = maxLat;
        options.boundaryPoly.minLng = minLng;
        options.boundaryPoly.maxLng = maxLng;
    }

    computeBondaryPoly(options, data);
    options.geoData = data;

    if (options.value != null)
        processValues(options);
}

function processValues(options){
    if (options.geoData != null)
        addLayersToMap(options);
}

function buildMap(options){
    var map = L.map('map', { attributionControl: false });
    map.scrollWheelZoom.disable();
    L.tileLayer($('#crisis-map-url-div').text(), {
        attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: 10
    }).addTo(map);

    L.control.attribution({position: 'topright'}).addTo(map);

    options.map = map;
    getData(options);
}

function addLayersToMap(option){
    var map = option.map;
    var defaultStyle = {color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
    var hoverStyle = {color: '#000000', fillColor: '#ff493d', fillOpacity: 1, opacity: 0.7, weight: 1};


    var info = L.control({position: 'topleft'});

    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'map-info'); // create a div with a class "info"
        return this._div;
    };

    // method that we will use to update the control based on feature properties passed
    info.update = function (props) {
        var innerData = "";
        if (props){
            for (var key in props){
                var value = props[key];
                innerData += '<tr><td style="text-align: right;">' + key + '</td><td>&nbsp;&nbsp; <b>' + value + '</b><td></tr>';
            }
        }
        this._div.innerHTML = '<h4>' + "Shape info" + '</h4>' +  (props ? '<table>' + innerData + '</table>' : 'Hover over a shape');
    };
    info.showOtherMessage = function (message){
        this._div.innerHTML = message;
    };
    info.addTo(map);


    var layer = L.geoJson(options.geoData, {
        style: function (feature) {
            return defaultStyle;
        },
        onEachFeature: function (feature, layer) {
            (function(layer, properties) {
                // Create a mouseover event
                layer.on("mouseover", function (e) {
                    if (!L.Browser.ie && !L.Browser.opera) {
                        layer.bringToFront();
                    }

                    layer.setStyle(hoverStyle);
                    info.update(properties);
                    console.log(properties);
                });
                // Create a mouseout event that undoes the mouseover changes
                layer.on("mouseout", function (e) {
                    // Start by reverting the style back
                    layer.setStyle(defaultStyle);
                    info.update();
                });
                // Close the "anonymous" wrapper function, and call it while passing
                // in the variables necessary to make the events work the way we want.
            })(layer, feature.properties);
        }
    }).addTo(map);

    var layers = [];
    layers['Shape file1'] = layer;
    L.control.layers(layers).addTo(map);

    map.fitBounds([[options.boundaryPoly.minLat, options.boundaryPoly.minLng], [options.boundaryPoly.maxLat, options.boundaryPoly.maxLng]]);
}


$(document).ready(
    function (){
        buildMap(options);
    }
);