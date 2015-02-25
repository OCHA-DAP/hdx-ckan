
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
            url: "http://192.168.59.103:5000/dataset/mali-one-to-one/resource_download/ba3531af-f091-4b90-8b24-e21b3ca3010",
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
        var pcode = $(options.pcodeSelectorId);
        var value = $(options.valueSelectorId);

        var opts = "<option value='null'>---Select---</option>";
        for (var i in options.fields){
            opts += "<option value='"+i+"'>" + options.fields[i] + "</option>"
        }

        pcode.children().remove();
        value.children().remove();

        pcode.append(opts);
        value.append(opts);
    }

    //get list of pcodes
    options.data = data.data;
    options.fields = data.fields;

    setFields(options);
    getDataPcodes(options);

    getGeoData(options);
}

function getGeoData(options){
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
    //match pcode from data and see what we can find in the geo data

    //if (errors)
    //    showErrors(options);
    //else{
    //    if (warnings)
    //        showWarnings(options);
    //
    //    buildMap(options);
    //}

    computeBondaryPoly(options, data);
    options.geoData = data;
    buildMap(options)
}

function buildClassification(options){

}

function buildMap(options){
    var map = L.map('map', { attributionControl: false });
    map.scrollWheelZoom.disable();
    L.tileLayer($('#crisis-map-url-div').text(), {
        attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: 10
    }).addTo(map);

    L.control.attribution({position: 'topright'}).addTo(map);
    //map.setView([9, -8], 5);

    L.geoJson(options.geoData, {
        style: function (feature) {
            return {color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
        }
    }).addTo(map);

    map.fitBounds([[options.boundaryPoly.minLat, options.boundaryPoly.minLng], [options.boundaryPoly.maxLat, options.boundaryPoly.maxLng]]);

}



$(document).ready(
    function (){
        getData(options);
    }
);