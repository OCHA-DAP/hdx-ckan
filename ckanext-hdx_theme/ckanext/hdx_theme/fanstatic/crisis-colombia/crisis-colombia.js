$(document).ready(function() {
  map = L.map('crisis-map', { attributionControl: false });
  map.scrollWheelZoom.disable();
  L.tileLayer($('#crisis-map-url-div').text(), {
    attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 7
  }).addTo(map);

  L.control.attribution({position: 'topright'}).addTo(map);
  map.setView([5, -70], 5);

  drawDistricts(map);
  drawGraph1();
  drawGraph2();
});

function spawnGraph1(jsondata, id, dateName, valueName){

}

function drawGraph1() {
  var sql = 'SELECT "Year", "Persons" FROM "6b0175c6-1209-42ed-9026-8bbaca7ea310"';

  var data = encodeURIComponent(JSON.stringify({sql: sql}));

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: '/api/3/action/datastore_search_sql',
    data: data,
    success: function(data) {
      var graph = c3.generate({
        bindto: "#graph1",
        color: {
          pattern: ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700']
        },
        padding: {
          bottom: 20,
          right: 20
        },

        data: {
          json: data.result.records,
          keys: {
            x: "Year",
            value: ["Persons"]
          },
          names: {
            "Persons": "Number of Internally Displaced People"
          },
          type: 'bar'
        },
        legend:{
          show: false
        },
        axis: {
          x: {
            tick: {
              rotate: 20
              //culling: false
            }
          },
          y: {
            label: {
              text: "Persons",
              position: 'outer-middle'
            }
          }
        }
      });
      $("#graph1").find("svg g:eq(0)").on("click", function (d,i) { window.location.href="/dataset/idps-data-by-year"; });;
    }
  });
}

function drawGraph2() {
  var sql = 'SELECT "Date", "Persons" FROM "9e69d499-0b2b-4da6-9c61-10e453a57504"';

  var data = encodeURIComponent(JSON.stringify({sql: sql}));

  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: '/api/3/action/datastore_search_sql',
    data: data,
    success: function(data) {
      var graph = c3.generate({
        bindto: "#graph2",
        padding: {
          bottom: 20,
          right: 20
        },
        color: {
          pattern: ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700']
        },
        data: {
          json: data.result.records,
          xFormat: '%Y-%m-%dT%H:%M:%S',
          keys: {
            x: "Date",
            value: ["Persons"]
          },
          names: {
            "Persons": "Number of People with Access Constraints"
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
              text: "Persons",
              position: 'outer-middle'
            }
          }
        }

      });
      $("#graph2").find("svg g:eq(0)").on("click", function (d,i) { window.location.href="/dataset/restricciones-de-acceso"; });;
    }
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