$(document).ready(function() {
    var crisisMapDiv = $("#crisis-map");
    if (crisisMapDiv.length){
        var confJsonText = $("#map-configuration").text();
        var confJson = JSON.parse(confJsonText);

        var map = L.map('crisis-map', { attributionControl: false });
        map.scrollWheelZoom.disable();
        if ( confJson.is_crisis=='false' ) {
             L.tileLayer($('#mapbox-baselayer-url-div').text(), {
                attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>',
                maxZoom: 7
            }).addTo(map);

            L.tileLayer($('#mapbox-labelslayer-url-div').text(), {
                maxZoom: 7
            }).addTo(map);
        }
        else {
            var attribution = '<a href="http://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap contributors</a>' +
                ' | <a href="http://earthquake.usgs.gov/earthquakes/eventpage/us20002926#impact_shakemap" target="_blank">USGS</a>';
            L.tileLayer(confJson.basemap_url, {
                attribution: attribution,
                //maxZoom: 14
            }).addTo(map);
        }

        L.control.attribution({position: 'topright'}).addTo(map);
        //map.setView([5, -70], 5);

        var layers = [];

        loadMapData(map, confJson, layers);
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

function prepareGraph2(element, data, colXType, colXFormat, graphType, colorList, columnYLabel) {
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
                    rotate: 25,
                    culling: {
                        max: 22
                    }
                }
            },
            y: {
                label: {
                    text: columnYLabel,
                    position: 'outer-middle'
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
            sourceList += "<div><i style='background: "+ colorList[sIdx] +"'></i> "+ source.source;
            if (source.data_link_url) {
                sourceList += " - <a target='_blank' href='" + source.data_link_url + "'>Data</a></div>";
            }
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
            var columnX, columnXType, columnXFormat, columnY, columnYLabel, graphType;

            var dataCols = [];
            var dataColsInit = false;

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
                    columnYLabel = graphData.title_y,
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
            graph = prepareGraph2(graphDataDiv[0], dataCols, columnXType, columnXFormat, graphType, colorList, columnYLabel);
        });

    });
}

function fitMap(map, data, confJson){
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

    if (confJson && confJson.max_zoom && confJson.max_zoom!='default') {
        map.setZoom(confJson.max_zoom);
    }
    else {
        var computedZoom = map.getZoom();
        computedZoom++;
        map.setZoom(computedZoom);
    }
}

function processMapValues(data, confJson, pcodeColumnName, valueColumnName, descriptionColumnName){
    var map = {};
    for (var idx in data){
        var item = data[idx];
        map[item[pcodeColumnName]] = {
            'value': item[valueColumnName],
            'description': descriptionColumnName ? item[descriptionColumnName] : null
        };
    }
    return map;
}

function generatePointLayerObject(map, infoObj, circleMarkersData, layers){
    var pointLayerObject = {
        'drawLayer': function () {
            function generatePropSymbolsObject(minRadius, maxRadius, featureData, fieldName) {
                var obj = {
                    'init': function() {
                        this.numOfSegments = maxRadius - minRadius + 1;
                        this.min = -1;
                        this.max = -1;
                        for (var i=0; i<featureData.features.length; i++) {
                            var strValue = featureData.features[i].properties[fieldName];
                            value = parseFloat(strValue);
                            if ( !isNaN(value) ) {
                                if (this.min == -1 || this.min > value)
                                    this.min = value;
                                if (this.max == -1 || this.max < value)
                                    this.max = value;
                            }
                        }
                        this.segmentSize = (this.max - this.min) / this.numOfSegments;
                    },
                    'computeRadius': function(value){
                        if ( !isNaN(value) ) {
                            var reducedValue = value - this.min;
                            var segmentNum = reducedValue / this.segmentSize;
                            var radius = minRadius + segmentNum;
                            return radius;
                        }
                        else {
                            return minRadius + ((maxRadius - minRadius) / 2)
                        }
                    }

                };
                obj.init();
                return obj;
            }

            var propSymbolsCalculator = generatePropSymbolsObject(6, 6, this.data, 'Individuals');

            var pointsLayer = L.geoJson(this.data, {
                pointToLayer: function (feature, latlng) {
                    var circleConfig = {
                        radius: 8,
                        fillColor: "gray",
                        color: "#000",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.6
                    };
                    var indivNum = parseInt(feature.properties.Individuals);
                    circleConfig.radius = propSymbolsCalculator.computeRadius(indivNum);
                    if (!isNaN(indivNum)) {
                        circleConfig.fillColor = "#91a7ff";
                    }
                    return L.circleMarker(latlng, circleConfig);
                },
                onEachFeature: function (feature, layer) {
                    (function (layer, properties) {
                        // Create a mouseover event
                        layer._originalStyle = layer.options;

                        layer.on("mouseover", function (e) {
                            layer.setStyle({'fillColor': "red"});
                            var indivNum = feature.properties.Individuals;
                            var siteName = feature.properties["Site Name"];
                            infoObj.update('IDP Locations', [
                                {'key': "Site Name", 'value': siteName},
                                {'key': 'Individuals', 'value': indivNum}
                            ]);
                        });
                        // Create a mouseout event that undoes the mouseover changes
                        layer.on("mouseout", function (e) {

                            layer.setStyle( layer._originalStyle );
                            infoObj.update();
                        });
                        // Close the "anonymous" wrapper function, and call it while passing
                        // in the variables necessary to make the events work the way we want.
                    })(layer, feature.properties);
                }

            });
            layers.push(pointsLayer);
            pointsLayer.addTo(map);
        },
        'process': function () {
            this.data = circleMarkersData;
            this.drawLayer();
        }
    };
    return pointLayerObject;
}

function _addRemoveLayers(layers, choroplethLayerId, legend) {
    for (var idx in  layers){
        var layer = layers[idx];
        if (layer._map)
            layer.bringToFront();

        if (layer._leaflet_id == choroplethLayerId){
            var legendC = $(legend.getContainer());
            if (layer._map)
                legendC.show();
            else
                legendC.hide();
        }
    }
}

function loadMapData(map, confJson, layers){
    var pcodeColumnName = confJson.map_column_1;
    var valueColumnName = confJson.map_values ? confJson.map_values : 'value';
    var descriptionColumnName =  confJson.map_description_column ? confJson.map_description_column.trim() : null;

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
    var sql = null;
    if ( descriptionColumnName ) {
        sql = 'SELECT "'+ pcodeColumnName +'", "'+ valueColumnName +'", "' +
            descriptionColumnName + '" FROM "'+ confJson.map_resource_id_1 +'"';
    }
    else {
        sql = 'SELECT "'+ pcodeColumnName +'", "'+ valueColumnName +'" FROM "'+ confJson.map_resource_id_1 +'"';
    }
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
                values = processMapValues(result.result.records, confJson, pcodeColumnName, valueColumnName, descriptionColumnName);
                return values;
            }
        });
    }

    var promiseList = [dataPromise, valuesPromise];
    var circleMarkersData = null, shakeMapData = null;
    if (confJson.is_crisis=='true'){
        var circleMarkers = $.ajax({
            url: confJson.circle_markers,
            type: 'GET',
            dataType: 'JSON',
            context: this,
            success: function (result) {
                circleMarkersData = result;
            }
        });
        promiseList.push(circleMarkers);

        var shakeMap = $.ajax({
            url: confJson.shakemap,
            type: 'GET',
            dataType: 'JSON',
            context: this,
            success: function (result) {
                shakeMapData = result;
            }
        });
        promiseList.push(shakeMap);
    }

    var info = null;
    $.when.apply($, promiseList).done(function(sources){
        var controls = drawDistricts(map, confJson, data, values, pcodeColumnName, valueColumnName, layers);
        info = controls.info;
        var legend = controls.legend;
        if ( confJson.is_crisis=='true' ) {
            drawShakeMap(map, shakeMapData, info, confJson, layers);
            generatePointLayerObject(map, info, circleMarkersData, layers).process();
            map.setView([27.69844, 85.38183], 11);

            var layersName = ["Choropleth", "Shake Map", "IDP Camps with Population"];
            var layerControl = L.control.layers();
            var choroplethLayerId = null;
            for (var idx in layers){
                var name = layersName[idx];
                var layer = layers[idx];
                if (name == "Choropleth"){
                    choroplethLayerId = layer._leaflet_id;
                }

                layerControl.addOverlay(layer, name);
            }
            layerControl.addTo(map);

            map.on('overlayadd', function(){
                _addRemoveLayers(layers, choroplethLayerId, legend);
            });
            map.on('overlayremove', function(){
                _addRemoveLayers(layers, choroplethLayerId, legend);
            })
            _addRemoveLayers(layers, choroplethLayerId, legend);
        }

    });
}


function drawShakeMap(map, shakeMapData, info, confJson, layers) {
    var newcolor = [
        ["#ffffff"], //1 color
        ["#ffffff", "#ffffff"], //2 colors
        ["#ffffff", "#ffffff", "#ffffff"], //3 colors
        ["#ffffff", "#ffffff", "#ffffff", "#ffffff"], //4 colors
        ["#ffffff","#ffffff", "#ffffff", "#ffffff", "#ffffff"], //5 colors
        ["#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#020202"], //6 colors
        ["#ffffff","#ffffff", "#ffffff", "#ffffff", "#ffffff","#ffffff", "#ffffff"], //7 colors
        ["#ffffff","#ffffff", "#ffffff", "#ffffff", "#ffffff","#ffffff", "#ffffff", "#ffffff"] //8 colors
    ];

    function _getStyle(threshold){
        function internalGetColor(color, i){
            var weight = 2;
            return {color: color[i], fillColor: color[i], fillOpacity: 0, opacity: 0.7, weight: weight};
        }
        return function (feature){
            var value = feature.properties["value"];
            for (var i = 0; i < threshold.length; i++){
                if (value < threshold[i]){
                    return internalGetColor(newcolor[threshold.length], i);
                }
            }
            return internalGetColor(newcolor[threshold.length], threshold.length);
        };
    }

    function _internalDraw(data) {
        var layer = L.geoJson(data, {
            style: _getStyle(threshold),
            onEachFeature: function (feature, layer) {
                (function (layer, properties) {
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
                            currentStyle['fillOpacity'] = 0;
                            currentStyle['opacity'] = 1;
                            currentStyle['color'] = '#888888';
                            layer.setStyle(currentStyle);
                        }
                        var titleField = confJson.map_district_name_column ? confJson.map_district_name_column : 'admin1Name';
                        var titleValue = 'Earthquake Intensity';
                        var updateValue = properties["value"];
                        info.update('Nepal Earthquake', [{'key': 'Name', 'value': titleValue}, {
                            'key': 'Value',
                            'value': updateValue
                        }]);
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
        });
        layers.push(layer);
        //layer.addTo(map);
    }
    var threshold = [4, 5, 6, 7, 8];
    _internalDraw(shakeMapData);
}


function drawDistricts(map, confJson, data, values, pcodeColumnName, valueColumnName, layers){
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
            var weight = 1;
            return {color: color[i], fillColor: color[i], fillOpacity: 0.6, opacity: 0.7, weight: weight};
        }
        return function (feature){
            var pcoderef = feature.properties[confJson.map_column_2];
            if(pcoderef in values) {
                for (var i = 0; i < threshold.length; i++){
                    if (values[pcoderef].value == 0 && confJson.is_crisis=='true'){
                        var tmpColor = internalGetColor(newcolor[threshold.length], i);
                        tmpColor["fillOpacity"] = 0;
                        return tmpColor;
                    }

                    if (values[pcoderef].value < threshold[i])
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
                        var itemInt = parseFloat(item);
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
            returnNew = false;
        if (returnNew)
            return threshold;
        return defaultThreshold;
    }

    var threshold = getThreshold([1, 1000, 5000, 10000]);
    var info;
    info = L.control({position: 'topleft'});

    if ( confJson.is_crisis != 'true' )
        fitMap(map, data, confJson);

    var choroplethLayer = L.geoJson(data,{
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
                        //if (!L.Browser.ie && !L.Browser.opera) {
                        //    layer.bringToFront();
                            //for (eLayer in extraLayers)
                            //    if (map.hasLayer(extraLayers[eLayer]))
                            //        extraLayers[eLayer].bringToFront();
                        //}

                        layer.setStyle(currentStyle);
                    }
                    var titleField = confJson.map_district_name_column ? confJson.map_district_name_column : 'admin1Name';
                    var titleValue = properties[titleField] ;
                    var updateValue = values[properties[confJson.map_column_2]];

                    var infoUpdateList = [{'key': 'Name', 'value': titleValue}];
                    if ('description' in updateValue && updateValue.description )
                        infoUpdateList.push({'key': 'Description', 'value': updateValue.description});
                    infoUpdateList.push({'key': 'Value', 'value': updateValue.value});
                    info.update(confJson.map_title, infoUpdateList);
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
    });
    layers.push(choroplethLayer);
    if (confJson.is_crisis!='true') {
        choroplethLayer.addTo(map);
    }

    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'map-info'); // create a div with a class "info"
        return this._div;
    };

    // method that we will use to update the control based on feature properties passed
    info.update = function (title, itemArray) {
        var html = '<h4>' + (title ? title : confJson.map_title) + '</h4>' ;
        if (itemArray) {
            html += '<table>';
            for (var i=0; i<itemArray.length; i++) {
                html += '<tr><td style="text-align: right;">' + itemArray[i].key
                        + ': </td><td>&nbsp;&nbsp; <b>' + itemArray[i].value + '</b><td></tr>';
            }
            html += '</table>';
        }
        else {
            // html += 'No data available';
            html += 'Hover over the map';
        }

        this._div.innerHTML = html;
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

    var returnValue = {info: info};
    if (confJson.show_legend != 'false') {
        var legend = L.control({position: 'bottomleft'});

        legend.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'map-info legend');
            return this._div;
        };
        legend.update = function () {
            this._div.innerHTML = '<div><i style="background: ' + newcolor[threshold.length][0] + '"></i> 0&ndash;' + threshold[0] + '</div>';
            for (var i = 0; i < threshold.length; i++) {
                this._div.innerHTML +=
                    '<div><i style="background:' + newcolor[threshold.length][i + 1] + '"></i> ' +
                    threshold[i] + (threshold[i + 1] ? '&ndash;' + threshold[i + 1] + '</div>' : '+</div>');
            }
        };
        legend.updateLayer = function (layer) {
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

        returnValue['legend'] = legend;
    }
    info.updateLayer();

    return returnValue;
}
