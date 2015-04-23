$(document).ready(function() {
    var crisisMapDiv = $("#crisis-map");
    if (crisisMapDiv.length){
        var map = L.map('crisis-map', { attributionControl: false });
        map.scrollWheelZoom.disable();
        L.tileLayer($('#mapbox-baselayer-url-div').text(), {
            attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>',
            maxZoom: 7
        }).addTo(map);

        L.tileLayer($('#mapbox-labelslayer-url-div').text(), {
            maxZoom: 7
        }).addTo(map);

        L.control.attribution({position: 'topright'}).addTo(map);
        //map.setView([5, -70], 5);

        var confJsonText = $("#map-configuration").text();
        var confJson = JSON.parse(confJsonText);
        loadMapData(map, confJson);
    }
    autoGraph();
});

function prepareGraph(element, data, colX, colXType, colXFormat, colY, graphType) {
    var config = {
        bindto: element,
        color: {
            pattern: ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700']
        },
        padding: {
            bottom: 20,
            right: 20
        },

        data: {
            json: data,
            keys: {
                x: colX,
                value: [colY]
            },
            type: graphType
        },
        legend: {
            show: false
        },
        axis: {
            x: {
                tick: {
                    rotate: 20,
                    culling: {
                        max: 15
                    }
                }
            }
        }
    };

    if(colXType){
        config.axis.x.type = colXType;
        if (colXType == 'timeseries')
            config.axis.x.tick.format = '%b %d, %Y';
    }
    if (colXFormat)
        config.data.xFormat = colXFormat;

    var graph = c3.generate(config);
    //$("#graph1").find("svg g:eq(0)").on("click", function (d,i) { window.location.href="/dataset/idps-data-by-year"; });;
    return graph;
}

function prepareGraph2(element, data, colXType, colXFormat, graphType, colorList) {
    var config = {
        bindto: element,
        color: {
            pattern: colorList
        },
        padding: {
            bottom: 20,
            right: 20
        },

        data: {
            x: 'x',
            columns: data,
            type: graphType
        },
        legend: {
            show: true
        },
        axis: {
            x: {
                tick: {
                    rotate: 20,
                    culling: {
                        max: 15
                    }
                }
            }
        }
    };

    if(colXType){
        config.axis.x.type = colXType;
        if (colXType == 'timeseries')
            config.axis.x.tick.format = '%b %d, %Y';
    }
    if (colXFormat)
        config.data.xFormat = colXFormat;

    var graph = c3.generate(config);
    //$("#graph1").find("svg g:eq(0)").on("click", function (d,i) { window.location.href="/dataset/idps-data-by-year"; });;
    return graph;
}

function autoGraph() {
    var colorList = ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700'];

    $(".auto-graph").each(function(idx, element){
        var graphDataDiv = $(element).find(".graph-data");
        var sourceListDiv = $(element).find(".source-list");
        var graphData = JSON.parse(graphDataDiv.text());
        graphDataDiv.html("<div style='text-align: center;'><img src='/base/images/loading-spinner.gif' /></div>");
        graphDataDiv.css("display", "block");

        var graph = null;
        var promises = [];
        var results = [];
        var sourceList = "";
        var timeformat = '%Y-%m-%dT%H:%M:%S';
        for (var sIdx in graphData.sources){
            var source = graphData.sources[sIdx];
            sourceList += "<div><i style='background: " + colorList[sIdx] + "'></i> " + source.source + " - <a href='" + source.data_link_url + "'>Data</a></div>";
            if ( source['source_type']=='ckan' ) {
                source["data"] = null;
                results.push(source);
                var sql = 'SELECT "' + source.column_x + '", "' + source.column_y + '" FROM "' + source.datastore_id + '"';
                var urldata = encodeURIComponent(JSON.stringify({sql: sql}));
                var promise = $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: '/api/3/action/datastore_search_sql',
                    data: urldata,
                    index: sIdx,
                    success: function (data) {
                        results[this.index].data = data;
                    }
                });
                promises.push(promise);
            }
            else{
                results.push(source);
                timeformat = '%Y-%m-%d';
            }
        }
        sourceListDiv.html(sourceList);

        $.when.apply($, promises).done(function(sources){
            var columnX, columnXType, columnXFormat, columnY, graphType;

            var dataCols = [];
                dataColsInit = false;

            for (var s in results){
                var response = results[s];
                if (response){
                    var data = response.data.result ? response.data.result : response.data;
                    var colX = ['x'],
                        //colY = [graphData.sources[s]['title']];
                        colY = [response.label_x];

                    columnX = response.column_x,
                    columnXType = null,
                    columnXFormat = null,
                    columnY = response.column_y,
                    graphType = graphData.type;

                    if (data.fields[0].type == 'timestamp'){
                        columnXType = 'timeseries';
                        columnXFormat = timeformat;
                    } else if (data.fields[0].type == 'text'){
                        columnXType = 'category';
                    }

                    for (var i = 0; i < data.records.length; i++){
                        var dataEl = data.records[i];
                        if (!dataColsInit){
                            colX.push(dataEl[columnX]);
                        }
                        colY.push(dataEl[columnY]);
                    }

                    if (!dataColsInit){
                        dataCols.push(colX);
                        dataColsInit = true;
                    }
                    dataCols.push(colY);
                }
            }
            graph = prepareGraph2(graphDataDiv[0], dataCols, columnXType, columnXFormat, graphType, colorList);
        });

    });
}

function fitMap(map, data){
    //Need to compute Top-Left corner and Bottom-Right corner for polygon.
    var minLat, minLng, maxLat, maxLng;
    var init = false;

    //Use a stack to traverse the geojson since we can gave many levels of arrays in arrays
    var stackArrays = [];
    var stackIndex = [];

    for (var idx in data.features){
        var feature = data.features[idx];
        if (feature.geometry && feature.geometry.coordinates){
            stackArrays.push(feature.geometry.coordinates);
            stackIndex.push(0);
        }
    }

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


    map.fitBounds([[minLat, minLng], [maxLat, maxLng]], {
        maxZoom: 10
    });
    var computedZoom = map.getZoom();
    computedZoom++;
    map.setZoom(computedZoom);
}

function processMapValues(data, confJson, pcodeColumnName, valueColumnName){
    var map = {};
    for (var idx in data){
        var item = data[idx];
        map[item[pcodeColumnName]] = item[valueColumnName];
    }
    return map;
}

function loadMapData(map, confJson){
    var pcodeColumnName = confJson.map_column_1;
    var valueColumnName = confJson.map_values ? confJson.map_values : 'value';

    var data = null;
    var dataPromise = $.ajax({
        url: "/dataset/" + confJson.map_dataset_id_2 + "/resource_download/" + confJson.map_resource_id_2,
        type: 'GET',
        dataType: 'JSON',
        success: function (result) {
            data = result;
        }
    });
    var values = null;
    var sql = 'SELECT "'+ pcodeColumnName +'", "'+ valueColumnName +'" FROM "'+ confJson.map_resource_id_1 +'"';
    var urldata = encodeURIComponent(JSON.stringify({sql: sql}));
    var valuesPromise;
    if (confJson.map_datatype_1 == "filestore"){
        valuesPromise = $.ajax({
            url: "/dataset/" + confJson.map_dataset_id_1 + "/resource_download/" + confJson.map_resource_id_1,
            type: 'GET',
            dataType: 'JSON',
            success: function (result) {
                values = processMapValues(result, confJson, pcodeColumnName, valueColumnName);
            }
        });
    } else {
        valuesPromise = $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '/api/3/action/datastore_search_sql',
            data: urldata,
            success: function(result){
                values = processMapValues(result.result.records, confJson, pcodeColumnName, valueColumnName);
                return values;
            }
        });
    }

    $.when.apply($, [dataPromise, valuesPromise]).done(function(sources){
        drawDistricts(map, confJson, data, values, pcodeColumnName, valueColumnName);
    });

}

function drawDistricts(map, confJson, data, values, pcodeColumnName, valueColumnName){
    var newcolor = [
        ["#ffbd13"], //1 color
        ["#ffbd13", "#ff493d"], //2 colors
        ["#ffe082", "#ff8053", "#ff493d"], //3 colors
        ["#ffe082", "#ffbd13", "#ff8053", "#ff493d"], //4 colors
        ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d"], //5 colors
        ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d", "#930D05"], //6 colors
        ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d","#D01A0E", "#510702"], //7 colors
        ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d","#D01A0E", "#930D05", "#510702"] //8 colors
    ];
    //var color = ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d","#D01A0E", "#930D05", "#510702"];

    function getStyle(values, threshold){
        function internalGetColor(color, i){
            return {color: color[i], fillColor: color[i], fillOpacity: 0.6, opacity: 0.7, weight: 1};
        }
        return function (feature){
            var pcoderef = feature.properties[confJson.map_column_2];
            if(pcoderef in values) {
                for (var i = 0; i < threshold.length; i++){
                    if (values[pcoderef] < threshold[i])
                        return internalGetColor(newcolor[threshold.length], i);
                }
                return internalGetColor(newcolor[threshold.length], threshold.length);
            } else {
                return {"color": "none","opacity":1};
            }
        };
    }

    function getThreshold(defaultThreshold) {
        var returnNew = true;
        var threshold = [];
        if (confJson.map_threshold) {
            try{
                var items = confJson.map_threshold.split(',');
                if (items.length > 0) {
                    for (var i = 0; i < items.length; i++) {
                        var item = items[i].trim();
                        var itemInt = parseInt(item);
                        if (itemInt && !isNaN(itemInt)){
                            threshold.push(itemInt);
                        }
                        else {
                            returnNew = false;
                            break;
                        }
                    }
                }
                else
                    returnNew = false;
            }
            catch (e){
                returnNew = false;
            }
        }
        else
            returnNew = false
        if (returnNew)
            return threshold;
        return defaultThreshold;
    }

    var threshold = getThreshold([1, 1000, 5000, 10000]);
    var info;

    fitMap(map, data);
    L.geoJson(data,{
        style: getStyle(values, threshold),
        onEachFeature: function (feature, layer) {
            (function(layer, properties) {
                // Create a mouseover event
                layer.on("mouseover", function (e) {
                    // Change the style to the highlighted version

                    var styleFunction;
                    if (layer.defaultOptions == null)
                        styleFunction = layer._options.style;
                    else
                        styleFunction = layer.defaultOptions.style;
                    if (styleFunction != undefined) {
                        var currentStyle = styleFunction({properties: properties});
                        currentStyle['fillOpacity'] = 1;
                        currentStyle['opacity'] = 1;
                        currentStyle['color'] = '#888888';
                        if (!L.Browser.ie && !L.Browser.opera) {
                            layer.bringToFront();
                            //for (eLayer in extraLayers)
                            //    if (map.hasLayer(extraLayers[eLayer]))
                            //        extraLayers[eLayer].bringToFront();
                        }

                        layer.setStyle(currentStyle);
                    }

                    info.update(properties);
                });
                // Create a mouseout event that undoes the mouseover changes
                layer.on("mouseout", function (e) {
                    // Start by reverting the style back
                    var styleFunction;
                    if (layer.defaultOptions == null)
                        styleFunction = layer._options.style;
                    else
                        styleFunction = layer.defaultOptions.style;
                    layer.setStyle(styleFunction({properties: properties}));
                    info.update();
                });
                // Close the "anonymous" wrapper function, and call it while passing
                // in the variables necessary to make the events work the way we want.
            })(layer, feature.properties);
        }
    }).addTo(map);

    info = L.control({position: 'topleft'});

    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'map-info'); // create a div with a class "info"
        return this._div;
    };

    // method that we will use to update the control based on feature properties passed
    info.update = function (properties) {
        var titleField = confJson.map_district_name_column ? confJson.map_district_name_column : 'admin1Name';
        this._div.innerHTML = '<h4>' + confJson.map_title + '</h4>' +  (properties ?
        '<table>' +
        '<tr><td style="text-align: right;">Name: </td><td>&nbsp;&nbsp; <b>' + properties[titleField] + '</b><td></tr>' +
        //'<tr><td style="text-align: right;">Municipality: </td><td>&nbsp;&nbsp; <b>' + props.NAME_DEPT + '</b><td></tr>' +
        '<tr><td style="text-align: right;">Value: </td><td>&nbsp;&nbsp; <b>' + values[properties[confJson.map_column_2]] + '</b><td></tr>' +
        '</table>'
            : 'No data available');
    };
    info.showOtherMessage = function (message){
        this._div.innerHTML = message;
    };
    info.updateLayer = function (layer) {
        //for (var l in layers)
        //    if (layers[l]['name'] == layer){
        //        this._layer = l;
        //        this.update();
        //        return;
        //    }
        this.update();
        this._layer = null;
    };

    info.addTo(map);

    var legend = L.control({position: 'bottomleft'});

    legend.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'map-info legend');
        return this._div;
    };
    legend.update = function (){
        this._div.innerHTML = '<div><i style="background: ' + newcolor[threshold.length][0] + '"></i> 0&ndash;' + threshold[0] + '</div>';
        for (var i = 0; i < threshold.length; i++) {
            this._div.innerHTML +=
                '<div><i style="background:' + newcolor[threshold.length][i+1] + '"></i> ' +
                threshold[i] + (threshold[i + 1] ? '&ndash;' + threshold[i + 1] + '</div>' : '+</div>');
        }
    };
    legend.updateLayer = function (layer){
        //for (l in layers)
        //    if (layers[l]['name'] == layer){
        //         this._layer = l;
        //        this.update();
        //        return;
        //    }

        this.update();
        this._layer = null;
    };
    legend.addTo(map);
    legend.updateLayer();
    info.updateLayer();

}
