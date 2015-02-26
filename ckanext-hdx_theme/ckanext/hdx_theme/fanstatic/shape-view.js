var options = {
    pcode: null,
    value: null,
    pcodeSelectorId: "#pcode",
    valueSelectorId: "#value",
    baseLayer: null,
    invertLatLong: true,
    boundaryPoly:{
        minLat: null,
        maxLat: null,
        minLong: null,
        maxLong: null
    },
    data: null,
    fields: null,
    geoData: null,
    pcodeMap: {}

};

function getData(options){
    //call DataProxy to get data for resource
    var data = JSON.parse($("#shapeData").text());
    var layers = [];
    for (var i in data){
        var value = data[i];
        computeBondaryPoly(options, value);
    }

    addLayersToMap(options, data);
}


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

    if (options.boundaryPoly.minLat > minLat || options.boundaryPoly.minLat == null)
        options.boundaryPoly.minLat = minLat;
    if (options.boundaryPoly.maxLat < maxLat || options.boundaryPoly.maxLat == null)
        options.boundaryPoly.maxLat = maxLat;
    if (options.boundaryPoly.minLng > minLng || options.boundaryPoly.minLng == null)
        options.boundaryPoly.minLng = minLng;
    if (options.boundaryPoly.maxLng > maxLng || options.boundaryPoly.maxLng == null)
        options.boundaryPoly.maxLng = maxLng;
}

function buildMap(options){
    var map = L.map('map', { attributionControl: false });
    map.scrollWheelZoom.disable();
    L.tileLayer($('#crisis-map-url-div').text(), {
        attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: 10
    }).addTo(map);

    L.control.attribution({position: 'topright'}).addTo(map);
    map.setView([0, 0], 1);

    options.map = map;
    getData(options);
}

function addLayersToMap(option, data){
    var map = option.map;
    var defaultStyle = {color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
    var defaultPointStyle = {radius: 7, color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
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

    var layers = [];
    var firstLayer = false;
    for (var key in data){
        var value = data[key];
        var layer = L.geoJson(value, {
            style: function (feature) {
                return defaultStyle;
            },
            pointToLayer: function (feature, latlng) {
                return L.circleMarker(latlng, defaultPointStyle);
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
        });
        if (!firstLayer){
            layer.addTo(map);
            firstLayer = true;
        }
        layers[key] = layer;
    }

    L.control.layers(layers).addTo(map);

    map.fitBounds([[options.boundaryPoly.minLat, options.boundaryPoly.minLng], [options.boundaryPoly.maxLat, options.boundaryPoly.maxLng]]);
}


$(document).ready(
    function (){
        buildMap(options);
    }
);