function drawMap() {
    var map = L.map('crisis-map', { attributionControl: false });
    map.scrollWheelZoom.disable();
    L.tileLayer($('#crisis-map-url-div').text(), {
        attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: 7
    }).addTo(map);

    L.control.attribution({position: 'topright'}).addTo(map);
    map.setView([0, 0], 1);

    var countryMapPolygon = $("#countryMapPolygon");
    var rawData = countryMapPolygon.text();
    countryMapPolygon.text("");
    try{
        var data = JSON.parse(rawData);
    } catch (err) {
        console.log("Error parsing json - set default map");
        return;
    }
    if (data.geometry == null){
        console.log("Set default map");
        return;
    }

    //Need to compute Top-Left corner and Bottom-Right corner for polygon.
    var minLat, minLng, maxLat, maxLng;
    var init = false;

    //Use a stack to traverse the geojson since we can gave many levels of arrays in arrays
    var stackArrays = [];
    var stackIndex = [];

    stackArrays.push(data.geometry.coordinates);
    stackIndex.push(0);
    while (stackArrays.length > 0){
        var array = stackArrays.pop();
        var index = stackIndex.pop();

        if (index < array.length){
            var item = array[index];
            //check if we reached a tuple of coordinates
            if (!$.isArray(item)){
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



    var latitude = minLat + (maxLat-minLat)/2;
    var longitude = minLng + (maxLng-minLng)/2;
    var zoom = 16;

    console.log(latitude);
    console.log(longitude);

    L.geoJson(data,{
      style: function(feature){
          return {color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
      }
    }).addTo(map);

    map.setView([latitude, longitude], zoom);
    console.log([[minLat, minLng], [maxLat, maxLng]]);
    map.fitBounds([[minLat, minLng], [maxLat, maxLng]]);
}

function buildGraphs() {
    $(".topline-charts").each(function (index){
        var element = $(this);
        var dataRaw = element.find(".data").text();
        var data = JSON.parse(dataRaw);
        var chartEl = element.find(".chart-item")[0];

        var graph = c3.generate({
            bindto: chartEl,
            color: {
                pattern: ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700']
            },
            padding: {
                bottom: 20,
                right: 20
            },
            data: {
                json: data,
                xFormat: '%Y-%m-%d',
                keys: {
                    x: "date",
                    value: ["value"]
                },
                names: {
                    "value": "Value"
                },
                type: 'bar'
            },
            legend:{
                show: false
            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        rotate: 30,
                        //culling: false,
                        format: '%b %Y'
                    }
                },
                y: {
                    label: {
                        text: "Value",
                        position: 'outer-middle'
                    }
                }
            }
        });
    });
}

$(document).ready(function() {
    drawMap();
    buildGraphs();
});