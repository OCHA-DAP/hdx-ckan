/* global dc, L */
dc.leafletChart = function (_chart) {
    "use strict";
    _chart = dc.baseChart(_chart);

    var _map;

    var _mapOptions = false;
    var _defaultCenter = false;
    var _defaultZoom = false;

    var _tiles = function (map) {
        L.tileLayer('https://a.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    };

    _chart._doRender = function () {
        _map = L.map(_chart.root().node(), _mapOptions);
        if (_defaultCenter && _defaultZoom) {
            _map.setView(_chart.toLocArray(_defaultCenter), _defaultZoom);
        }
        _chart.tiles()(_map);

        _chart._postRender();

        return _chart._doRedraw();
    };

    _chart._postRender = function () {
        //abstract
    };

    _chart.mapOptions = function (_) {
        if (!arguments.length) {
            return _mapOptions;
        }
        _mapOptions = _;
        return _chart;
    };

    _chart.center = function (_) {
        if (!arguments.length) {
            return _defaultCenter;
        }
        _defaultCenter = _;
        return _chart;
    };

    _chart.zoom = function (_) {
        if (!arguments.length) {
            return _defaultZoom;
        }
        _defaultZoom = _;
        return _chart;
    };

    _chart.tiles = function (_) {
        if (!arguments.length) {
            return _tiles;
        }
        _tiles = _;
        return _chart;
    };

    _chart.map = function () {
        return _map;
    };

    _chart.toLocArray = function (value) {
        if (typeof value === "string") {
            // expects '11.111,1.111'
            value = value.split(",");
        }
        // else expects [11.111,1.111]
        return value;
    };

    return _chart;
};


/***************************
 LeafletBubbleChart
 ***************************/
dc.leafletBubbleChart = function (parent, chartGroup) {
    "use strict";

    /* ####################################
     * Private variables -- default values.
     * ####################################
     */
    var _chart = dc.leafletChart({});
    var _selectedMarkerList = [];
    var _selectedColor = 'blue';
    var _unselectedColor = 'gray';
    var _layerGroup = false;

    var _location = function (d) {
        return _chart.keyAccessor()(d);
    };

    var _r = d3.scale.linear().domain([0, 100]);
    var _brushOn = true;

    var _marker = function (d, map) {
        var key = _chart.locationAccessor()(d);
        var locArray = _chart.toLocArray(key);

        var latlng = L.latLng(+locArray[0], +locArray[1]);
        var circle = L.circleMarker(latlng);

        circle.setRadius(_chart.r()(_chart.valueAccessor()(d)));
        circle.on("mouseover", function (e) {
            // TODO - Tooltips!
            console.log(_chart.title()(d));
        });
        var isSelected = (-1 !== _selectedMarkerList.indexOf(key));

        circle.options.color = isSelected ? _chart.selectedColor() : _chart.unselectedColor();

        return circle;
    };

    /* ########################
     * Private helper functions
     * ########################
     */

    function clearSelectedMarkerList() {
        while (_selectedMarkerList.length > 0) {
            _selectedMarkerList.pop();
        }
    }

    /* ################
     * Public interface
     * ################
    */


    /**
     #### .r([bubbleRadiusScale])
     Get or set bubble radius scale. By default bubble chart uses ```d3.scale.linear().domain([0, 100])``` as it's r scale .

     **/
    _chart.r = function (_) {
        if (!arguments.length) return _r;
        _r = _;
        return _chart;
    };

    _chart.brushOn = function (_) {
        if (!arguments.length) {
            return _brushOn;
        }
        _brushOn = _;
        return _chart;
    };

    _chart.locationAccessor = function (_) {
        if (!arguments.length) {
            return _location;
        }
        _location = _;
        return _chart;
    };
    /**
     #### .selectedColor([color])
     Get or set the color of a selected (filter) bubble.

     */
    _chart.selectedColor = function (_) {
        if (!arguments.length) {
            return _selectedColor;
        }
        _selectedColor = _;
        return _chart;
    };

    /**
     #### .unselectedColor([color])
     Get or set the color of a bubble which is not currently in the filter.

     */
    _chart.unselectedColor = function (_) {
        if (!arguments.length) {
            return _unselectedColor;
        }
        _unselectedColor = _;
        return _chart;
    };

    var createmarker = function (v, k) {
        var marker = _chart.marker()(v);
        marker.key = k;
        if (_chart.brushOn()) {
            marker.on("click", selectFilter);
        }
        return marker;
    };

    _chart.marker = function (_) {
        if (!arguments.length) {
            return _marker;
        }
        _marker = _;
        return _chart;
    };

    /* Render and redraw overrides */
    _chart.filterAll = function () {
        // Clear selectedMarkerList on a call to filterAll.
        clearSelectedMarkerList();
        return _chart.filter(null);
    };

    _chart._postRender = function () {
        if (_chart.brushOn()) {

            _chart.map().on('click', function (e) {
                while (_selectedMarkerList.length > 0) {
                    _selectedMarkerList.pop();
                }
                dc.events.trigger(function () {
                    _chart.filter(null);
                    dc.redrawAll(_chart.chartGroup());
                });
            });
        }
        _chart.map().on('boxzoomend', boxzoomFilter, this);
        _layerGroup = new L.LayerGroup();
        _chart.map().addLayer(_layerGroup);
    };

    _chart._doRedraw = function () {
        var groups = _chart._computeOrderedGroups(_chart.data()).filter(function (d) {
            return _chart.valueAccessor()(d) !== 0;
        });
        _layerGroup.clearLayers();
        groups.forEach(function (v, i) {
            var key = _chart.keyAccessor()(v);
            var marker = null;

            marker = createmarker(v, key);
            _layerGroup.addLayer(marker)
        });
    };

    /* Callback functions */
    function boxzoomFilter(e) {
        clearSelectedMarkerList();

        _layerGroup.eachLayer(function (layer) {
            var latLng = layer.getLatLng();
            if (e.boxZoomBounds.contains(latLng)) {
                _selectedMarkerList.push(layer.key);
            }
        });

        dc.events.trigger(function (e) {
            _chart.dimension().filterFunction(function (d) {
                return _selectedMarkerList.indexOf(d) !== -1;
            });
            dc.redrawAll();
        });
    }

    var selectFilter = function (e) {
        if (!e.target) {
            dc.events.trigger(function () {
                _chart.filter(null);
                dc.redrawAll(_chart.chartGroup());
            });
            return;
        }
        var filter = e.target.key;

        if (e.originalEvent.ctrlKey) {
            // If ctrl key modifier was pressed on click.
            var selectedIndex = _selectedMarkerList.indexOf(filter);
            if (selectedIndex === -1) {
                // If target not already in selected marker list, add it.
                _selectedMarkerList.push(filter);
            }
            else {
                // Else, remove it.
                _selectedMarkerList.splice(selectedIndex, 1);
            }
        }
        else {
            // If ctrl key wasnt pressed, clear filter and selection and add target to a empty selectedMarkersList.
            while (_selectedMarkerList.length > 0) {
                _selectedMarkerList.pop();
            }
            _selectedMarkerList.push(filter);
        }
        dc.events.trigger(function () {
            if (_selectedMarkerList.length > 0) {
                _chart.dimension().filterFunction(function (d) {
                    return _selectedMarkerList.indexOf(d) !== -1;
                });
            } else {
                _chart.filter(null);
            }
            dc.redrawAll(_chart.chartGroup());
        });
    };


    return _chart.anchor(parent, chartGroup);
}
;

/***********************************
 Markers
 ***********************************/
dc.leafletMarkerChart = function (parent, chartGroup) {
    "use strict";
    var _chart = dc.leafletChart({});

    var _renderPopup = true;
    var _cluster = false; // requires leaflet.markerCluster
    var _clusterOptions = false;
    var _rebuildMarkers = false;
    var _brushOn = true;
    var _filterByArea = false;

    var _filter;
    var _innerFilter = false;
    var _zooming = false;
    var _layerGroup = false;
    var _markerList = [];
    var _currentGroups = false;

    _chart.renderTitle(true);

    var _location = function (d) {
        return _chart.keyAccessor()(d);
    };

    var _marker = function (d, map) {
        var marker = new L.Marker(_chart.toLocArray(_chart.locationAccessor()(d)), {
            title: _chart.renderTitle() ? _chart.title()(d) : '',
            alt: _chart.renderTitle() ? _chart.title()(d) : '',
            icon: _icon(),
            clickable: _chart.renderPopup() || (_chart.brushOn() && !_filterByArea),
            draggable: false
        });
        return marker;
    };

    var _icon = function (d, map) {
        return new L.Icon.Default();
    };

    var _popup = function (d, marker) {
        return _chart.title()(d);
    };

    _chart._postRender = function () {
        if (_chart.brushOn()) {
            if (_filterByArea) {
                _chart.filterHandler(doFilterByArea);
            }

            _chart.map().on('zoomend moveend', zoomFilter, this);
            if (!_filterByArea) {
                _chart.map().on('click', zoomFilter, this);
                    }
            _chart.map().on('zoomstart', zoomStart, this);
                }

        if (_cluster) {
            _layerGroup = new L.MarkerClusterGroup(_clusterOptions ? _clusterOptions : null);
        }
        else {
            _layerGroup = new L.LayerGroup();
        }
        _chart.map().addLayer(_layerGroup);
    };

    _chart._doRedraw = function () {
        var groups = _chart._computeOrderedGroups(_chart.data()).filter(function (d) {
            return _chart.valueAccessor()(d) !== 0;
        });
        if (_currentGroups && _currentGroups.toString() === groups.toString()) {
            return;
        }
        _currentGroups = groups;

        if (_rebuildMarkers) {
            _markerList = [];
        }
        _layerGroup.clearLayers();

        var addList = [];
        groups.forEach(function (v, i) {
            var key = _chart.keyAccessor()(v);
            var marker = null;
            if (!_rebuildMarkers && key in _markerList) {
                marker = _markerList[key];
            }
            else {
                marker = createmarker(v, key);
                }
            if (!_chart.cluster()) {
                _layerGroup.addLayer(marker);
            }
            else {
                addList.push(marker);
            }
        });

        if (_chart.cluster() && addList.length > 0) {
            _layerGroup.addLayers(addList);
        }
    };

    _chart.locationAccessor = function (_) {
        if (!arguments.length) {
            return _location;
        }
        _location = _;
        return _chart;
    };

    _chart.marker = function (_) {
        if (!arguments.length) {
            return _marker;
        }
        _marker = _;
        return _chart;
    };

    _chart.icon = function (_) {
        if (!arguments.length) {
            return _icon;
        }
        _icon = _;
        return _chart;
    };

    _chart.popup = function (_) {
        if (!arguments.length) {
            return _popup;
        }
        _popup = _;
        return _chart;
    };

    _chart.renderPopup = function (_) {
        if (!arguments.length) {
            return _renderPopup;
        }
        _renderPopup = _;
        return _chart;
    };


    _chart.cluster = function (_) {
        if (!arguments.length) {
            return _cluster;
        }
        _cluster = _;
        return _chart;
    };

    _chart.clusterOptions = function (_) {
        if (!arguments.length) {
            return _clusterOptions;
        }
        _clusterOptions = _;
        return _chart;
    };

    _chart.rebuildMarkers = function (_) {
        if (!arguments.length) {
            return _rebuildMarkers;
        }
        _rebuildMarkers = _;
        return _chart;
    };

    _chart.brushOn = function (_) {
        if (!arguments.length) {
            return _brushOn;
        }
        _brushOn = _;
        return _chart;
    };

    _chart.filterByArea = function (_) {
        if (!arguments.length) {
            return _filterByArea;
        }
        _filterByArea = _;
        return _chart;
    };

    _chart.markerGroup = function () {
        return _layerGroup;
    };

    var createmarker = function (v, k) {
        var marker = _marker(v);
        marker.key = k;
        if (_chart.renderPopup()) {
            marker.bindPopup(_chart.popup()(v, marker));
        }
        if (_chart.brushOn() && !_filterByArea) {
            marker.on("click", selectFilter);
        }
        _markerList[k] = marker;
        return marker;
    };

    var zoomStart = function (e) {
        _zooming = true;
    };

    var zoomFilter = function (e) {
        if (e.type === "moveend" && (_zooming || e.hard)) {
            return;
        }
        _zooming = false;

        if (_filterByArea) {
            var filter;
            if (_chart.map().getCenter().equals(_chart.center()) && _chart.map().getZoom() === _chart.zoom()) {
                filter = null;
            }
            else {
                filter = _chart.map().getBounds();
            }
            dc.events.trigger(function () {
                _chart.filter(null);
                if (filter) {
                    _innerFilter = true;
                    _chart.filter(filter);
                    _innerFilter = false;
                }
                dc.redrawAll(_chart.chartGroup());
            });
        } else if (_chart.filter() && (e.type === "click" ||
            (_markerList.indexOf(_chart.filter()) !== -1 && !_chart.map().getBounds().contains(_markerList[_chart.filter()].getLatLng())))) {
            dc.events.trigger(function () {
                _chart.filter(null);
                if (_renderPopup) {
                    _chart.map().closePopup();
                }
                dc.redrawAll(_chart.chartGroup());
            });
        }
    };

    var doFilterByArea = function (dimension, filters) {
        _chart.dimension().filter(null);
        if (filters && filters.length > 0) {
            _chart.dimension().filterFunction(function (d) {
                if (!(d in _markerList)) {
                    return false;
                }
                var locO = _markerList[d].getLatLng();
                return locO && filters[0].contains(locO);
            });
            if (!_innerFilter && _chart.map().getBounds().toString !== filters[0].toString()) {
                _chart.map().fitBounds(filters[0]);
            }
        }
    };

    var selectFilter = function (e) {
        if (!e.target) {
            return;
        }
        var filter = e.target.key;
        dc.events.trigger(function () {
            _chart.filter(filter);
            dc.redrawAll(_chart.chartGroup());
        });
    };

    return _chart.anchor(parent, chartGroup);
};


/***************************
 choropleth
 ***************************/


dc.leafletChoroplethChart = function (parent, chartGroup) {
    "use strict";
    var _chart = dc.colorChart(dc.leafletChart({}));

    var _geojsonLayer = false;
    var _dataMap = [];
    var _info = false;

    var _geojson = false;
    var _renderPopup = true;
    var _brushOn = true;
    var _featureOptions = {
        'fillColor': 'black',
        'color': 'gray',
        'opacity':0,
        'fillOpacity': 0,
        'weight': 1
    };
    var _defaultFillOpacity = 0.6;

    var _featureKey = function (feature) {
        return feature.key;
    };
    
    function isSelectedGeo(d) {
        return _chart.hasFilter(d.key);
    }    

    var _featureStyle = function (feature) {
        var options = _chart.featureOptions();
        if (options instanceof Function) {
            options = options(feature);
        }
        options = JSON.parse(JSON.stringify(options));
        var v = _dataMap[_chart.featureKeyAccessor()(feature)];
        if (v && v.d) {
            if (_chart.hasFilter()) {
                if (isSelectedGeo(v.d)) {
                    options.fillColor = _chart.getColor(v.d.value, v.i);
                    options.opacity = 0.8;
                    options.fillOpacity = _defaultFillOpacity;
                } else {
                    options.fillColor = _chart.getColor(0, v.i);
                    options.opacity = 0.8;
                    options.fillOpacity = _defaultFillOpacity;
                }
            } else {
                options.fillColor = _chart.getColor(v.d.value, v.i);
                options.opacity = 0.8;
                options.fillOpacity = _defaultFillOpacity;
            }           
        }
        return options;
    };

    var _hoverFeatureStyle = function(feature){
        var result = _featureStyle(feature);
        result.fillOpacity = 1;
        return result;
    };

    var _popup = function (d, feature) {
        return _chart.title()(d);
    };

    _chart._postRender = function () {
        _geojsonLayer = L.geoJson(_chart.geojson(), {
            style: _chart.featureStyle(),
            onEachFeature: processFeatures
        });

        _info = L.control();

        _info.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'hdx-3w-info');
            this.update();
            return this._div;
        };

        _info.update = function (name) {
            this._div.innerHTML = (name ? name: 'Hover for details');
        };

        _info.addTo(_chart.map());

        _chart.map().addLayer(_geojsonLayer);
    };

    _chart._doRedraw = function () {
        _geojsonLayer.clearLayers();
        _dataMap = [];
        _chart._computeOrderedGroups(_chart.data()).forEach(function (d, i) {
            _dataMap[_chart.keyAccessor()(d)] = {'d': d, 'i': i};
        });
        _geojsonLayer.addData(_chart.geojson());
    };

    _chart.geojson = function (_) {
        if (!arguments.length) {
            return _geojson;
        }
        _geojson = _;
        return _chart;
    };

    _chart.featureOptions = function (_) {
        if (!arguments.length) {
            return _featureOptions;
        }
        _featureOptions = _;
        return _chart;
    };

    _chart.featureKeyAccessor = function (_) {
        if (!arguments.length) {
            return _featureKey;
        }
        _featureKey = _;
        return _chart;
    };

    _chart.featureStyle = function (_) {
        if (!arguments.length) {
            return _featureStyle;
        }
        _featureStyle = _;
        return _chart;
    };

    _chart.popup = function (_) {
        if (!arguments.length) {
            return _popup;
        }
        _popup = _;
        return _chart;
    };

    _chart.renderPopup = function (_) {
        if (!arguments.length) {
            return _renderPopup;
        }
        _renderPopup = _;
        return _chart;
    };

    _chart.brushOn = function (_) {
        if (!arguments.length) {
            return _brushOn;
        }
        _brushOn = _;
        return _chart;
    };

    var processFeatures = function (feature, layer) {
        var v = _dataMap[_chart.featureKeyAccessor()(feature)];
        if (v && v.d) {
            layer.key = v.d.key;
            if (_chart.renderPopup()) {
                //layer.bindPopup(_chart.popup()(v.d, feature));
                layer.on("mouseover",function(){
                    layer.setStyle(_hoverFeatureStyle(feature));
                    _info.update(_chart.popup()(v.d, feature));
                });
                layer.on("mouseout",function(){
                    layer.setStyle(_featureStyle(feature));
                    _info.update();
                });
            }
            if (_chart.brushOn()) {
                layer.on("click", selectFilter);
            }
        }
    };

    var selectFilter = function (e) {
        if (!e.target) {
            return;
        }
        var filter = e.target.key;
        dc.events.trigger(function () {
            _chart.filter(filter);
            dc.redrawAll(_chart.chartGroup());
        });
    };

    return _chart.anchor(parent, chartGroup);
};
