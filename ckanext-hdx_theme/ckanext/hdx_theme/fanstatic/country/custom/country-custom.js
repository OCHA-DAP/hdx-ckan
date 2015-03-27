$(document).ready(function() {
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
    map.setView([5, -70], 5);

    //drawDistricts(map);
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
            }
        }
    };

    if(colXType){
        config.data.xFormat = colXFormat;
        config.axis.x.type = colXType;
    }

    var graph = c3.generate(config);
    //$("#graph1").find("svg g:eq(0)").on("click", function (d,i) { window.location.href="/dataset/idps-data-by-year"; });;
    return graph;
}
function autoGraph() {
    $(".auto-graph").each(function(idx, element){
        var graphData = $(element).find(".graph-data");
        var data = JSON.parse(graphData.text());
        graphData.html("<img src='/base/images/loading-spinner.gif' />");
        graphData.css("display", "block");

        var graph = null;
        var promises = [];
        var results = [];
        for (var sIdx in data.sources){
            var source = data.sources[sIdx];
            source["data"] = null;
            results.push(source);
            var sql = 'SELECT "'+ source.column_x + '", "'+ source.column_y +'" FROM "'+ source.datastore_id +'"';
            var urldata = encodeURIComponent(JSON.stringify({sql: sql}));
            var promise = $.ajax({
                type: 'POST',
                dataType: 'json',
                url: '/api/3/action/datastore_search_sql',
                data: urldata,
                index: sIdx,
                success: function(data){
                    results[this.index].data = data;
                }
            });
            promises.push(promise);
        }

        $.when.apply($, promises).done(function(sources){
            for (var s in results){
                var response = results[s];
                if (response){
                    var data = response.data.result;

                    var columnX = response.column_x,
                        columnXType = null,
                        columnXFormat = null,
                        columnY = response.column_y,
                        graphType = element.type;

                    if (data.fields[0].type == 'timestamp'){
                        columnXType = 'timeseries';
                        columnXFormat = '%Y-%m-%dT%H:%M:%S';
                    }


                    if (!graph){
                        graph = prepareGraph(graphData[0], data.records, columnX, columnXType, columnXFormat, columnY, 'bar');
                    }
                    else
                        graph.load({
                            json: data,
                            keys: {
                                x: columnX,
                                value: [columnY]
                            },
                            type: 'area'
                        });
                }
            }
        });
    });
}

function drawDistricts(map){
    var color = ["#EAFF94","#ffe082", "#ffbd13", "#ff8053", "#ff493d"];
//  var color = ["#fcdcd2","#fabdae", "#f48272", "#f1635a", "#c06c5f"];

    var layers = {
        totalIDPs: {
            name: 'Number of IDPs per 100,000 inhabitants in 2013',
//      threshold: [1, 10, 100, 500],
//      threshold: [10, 100, 500, 1000],
            threshold: [100, 500, 1000, 2000],
            values: totalIDPs
        }
    };

    function getStyle(values, threshold){
        function internalGetColor(color, i){
            return {color: color[i], fillColor: color[i], fillOpacity: 0.6, opacity: 0.7, weight: 1};
        }
        return function (feature){
            var pcoderef = feature.properties.PCODE;
            if(pcoderef in values) {
                for (var i = 0; i < 4; i++){
                    if (values[pcoderef] < threshold[i])
                        return internalGetColor(color, i);
                }
                return internalGetColor(color, 4);
            } else {
                return {"color": "none","opacity":1};
            }
        };

    }

    var info;
    var regularLayers = {}, extraLayers = {};

    $.each(layers, function (idx, val) {
        regularLayers[val['name']] = L.geoJson(regions,{
            style: getStyle(val['values'], val['threshold']),
            onEachFeature: function (feature, layer) {
                // no longer implementing the click function on the layers for now
//          layer.on('click', function (){
//            window.location.href="/group/" + feature.properties.CNTRY_CODE.toLowerCase() + "?sort=metadata_modified+desc"
//          });
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
                                for (eLayer in extraLayers)
                                    if (map.hasLayer(extraLayers[eLayer]))
                                        extraLayers[eLayer].bringToFront();
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
        });
    });

    info = L.control({position: 'topleft'});

    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'map-info'); // create a div with a class "info"
        return this._div;
    };

    // method that we will use to update the control based on feature properties passed
    info.update = function (props) {
        this._div.innerHTML = '<h4>' + layers[this._layer]['name'] + '</h4>' +  (props ?
        '<table>' +
        '<tr><td style="text-align: right;">Department: </td><td>&nbsp;&nbsp; <b>' + props.NAME + '</b><td></tr>' +
        '<tr><td style="text-align: right;">Municipality: </td><td>&nbsp;&nbsp; <b>' + props.NAME_DEPT + '</b><td></tr>' +
        '<tr><td style="text-align: right;">Value: </td><td>&nbsp;&nbsp; <b>' + layers[this._layer]['values'][props.PCODE] + '</b><td></tr>' +
        '</table>'
            : 'No data available');
    };
    info.showOtherMessage = function (message){
        this._div.innerHTML = message;
    };
    info.updateLayer = function (layer) {
        for (l in layers)
            if (layers[l]['name'] == layer){
                this._layer = l;
                this.update();
                return;
            }
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
        var threshold = layers[this._layer]['threshold'];

        this._div.innerHTML = '<div><i style="background: ' + color[0] + '"></i> 0&ndash;' + threshold[0] + '</div>';
        for (var i = 0; i < threshold.length; i++) {
            this._div.innerHTML +=
                '<div><i style="background:' + color[i+1] + '"></i> ' +
                threshold[i] + (threshold[i + 1] ? '&ndash;' + threshold[i + 1] + '</div>' : '+</div>');
        }
    };
    legend.updateLayer = function (layer){
        for (l in layers)
            if (layers[l]['name'] == layer){
                this._layer = l;
                this.update();
                return;
            }

        this.update();
        this._layer = null;
    };
    legend.addTo(map);

    //L.control.layers(regularLayers).addTo(map);

    map.on('baselayerchange', function (eventLayer) {
        info.updateLayer(eventLayer.name);
        legend.updateLayer(eventLayer.name);
    });

    var defaultLayer = layers['totalIDPs']['name'];
    map.addLayer(regularLayers[defaultLayer]);
    info.updateLayer(defaultLayer);
    legend.updateLayer(defaultLayer);
}
