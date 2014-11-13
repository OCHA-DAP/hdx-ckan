$(document).ready(function() {
  map = L.map('ebola-map', { attributionControl: false });

  L.tileLayer($('#crisis-map-url-div').text(), {
    attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 10
  }).addTo(map);

  L.control.attribution({position: 'topright'}).addTo(map);

  map.setView([8, -8], 6);


  //drawCountries(map);
  drawDistricts(map);
});


function drawCountries(map) {
//http://ckan.lo:5000/api/3/action/group_show?id=afg
  var countries = [
    'lbr',
    'sle',
    'gin'
  ];
  $.each(countries, function (idx, val) {
    var url = "/api/3/action/group_show?id=";
    $.ajax({
      url: url + val
    })
      .done(function (json) {
        if (json.success) {
          var dataList = json.result.extras;
          var data;

          function style(feature) {
            return {
              fillColor: "#ff0000",
              weight: 1,
              opacity: 0.4,
              color: 'white',
              fillOpacity: 0.4
            };
          }

          for (var i = 0; i < dataList.length; i++)
            if (dataList[i].key == "geojson") {
              var json = JSON.parse(dataList[i].value);
              data = json.geometry;
            }
          console.log(data);
          L.geoJson(data, {
            style: style
          }).addTo(map);
        }
      });
  })
}

function drawDistricts(map){
//  var color_simon = ["none","#ffe082","#ffca28","#ffb300","#ff8f00"];
//  var color3 = ["none","#ffe082", "#ffca28", "#ff5631", "#ff1100"];
//  var color2 = ["none","#ffe082", "#ffca28", "#ff6b3d", "#ff2f27"];
  var color = ["none","#ffe082", "#ffbd13", "#ff8053", "#ff493d"];

  var layers = {
    newCases: {
      name: 'New Cases in the last 4 weeks',
      threshold: [1, 25, 50, 200],
      values: newCases
    },
    totalDeaths: {
      name: 'Total Deaths',
      threshold: [1, 50, 100, 500],
      values: totalDeaths
    },
    totalCases: {
      name: 'Total Cases',
      threshold: [1, 100, 300, 800],
      values: totalCases
    },
    newCasesPerArea:{
      name: 'New Cases in the last 4 weeks per 1000 Sq. km',
      threshold: [1, 10, 50, 250],
      values: newCasesPerArea
    },
    totalCasesPerArea: {
      name: 'Total Cases per 1000 Sq. km',
      threshold: [1, 50, 100, 500],
      values: totalCasesPerArea
    },
    totalDeathsPerArea: {
      name: 'Total Deaths per 1000 Sq. km',
      threshold: [1, 25, 50, 200],
      values: totalDeathsPerArea
    },
    newCasesPerPop:{
      name: 'New Cases in the last 4 weeks per 100,000 people',
      threshold: [0.1, 10, 25, 50],
      values: newCasesPerPop
    },

    totalCasesPerPop:{
      name: 'Total Cases per 100,000 people',
      threshold: [0.1, 25, 50, 100],
      values: totalCasesPerPop
    },
    totalDeathsPerPop:{
      name: 'Total Deaths per 100,000 people',
      threshold: [0.1, 20, 40, 80],
      values: totalDeathsPerPop
    }
//

  };

  function getStyle(values, threshold){
    function internalGetColor(color, i){
      return {color: color[i], fillColor: color[i], fillOpacity: 0.6, opacity: 0.7, weight: 2};
    }
    return function (feature){
      var pcoderef = feature.properties.PCODE_REF;
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

  var medicalCentresStyle = function(feature){
      if(feature.properties.Status == "Functional"){
          return   {radius: 5,
                  fillColor: "#A3C990",
                  color: "#000",
                  weight: 1,
                  opacity: 1,
                  fillOpacity: 1};
              }
      else {
          return   {radius: 5,
                  fillColor: "#738ffe",
                  color: "#000",
                  weight: 1,
                  opacity: 1,
                  fillOpacity: 1};
              }
  };

  var SBTFMedicalCentresStyle = function(){
      return   {radius: 5,
                  fillColor: "#91a7ff",
                  color: "#000",
                  weight: 1,
                  opacity: 1,
                  fillOpacity: 1};
  };

    var medicalCentresLayer = L.geoJson(medicalCentres, {
        pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng,medicalCentresStyle(feature));
        },
        onEachFeature: function (feature, layer) {
//          layer.bindPopup("Centre Name: " + feature.properties["Centre Name"] + "<br />Type: " + feature.properties["Type1"] + "<br />Status: " + feature.properties["Status"] + "<br />Organisation: " + feature.properties["Primary Organisation"]);
          (function (layer, properties) {
            // Create a mouseover event
            layer.on("mouseover", function (e) {
              var message = '<h4>Ebola Medical Centers</h4>' +
                            '<table>' +
                            '<tr><td style="text-align: right;">Center Name: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Centre Name"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Type: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Type1"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Status: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Status"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Organisation: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Primary Organisation"] + '</b><td></tr>' +
                            '</table>';
              info.showOtherMessage(message);
            });
            layer.on("mouseout", function (e) {
              // Start by reverting the style back
              layer.setStyle(layer.defaultOptions.style({properties: properties}));
              info.update();
            });
          })(layer, feature.properties);
        }
    });

    var SBTFMedicalCentresLayer = L.geoJson(SBTFMedicalCentres, {
        pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng,SBTFMedicalCentresStyle());
        },
        onEachFeature: function (feature, layer) {
//            layer.bindPopup("Centre ID: "+feature.properties["Centre ID"]+"<br />Centre Name: "+feature.properties["Center"]+"<br />Type: "+feature.properties["Type"]+"<br />Activity: "+feature.properties["Activity"]+"<br />Org: "+feature.properties["Org"]);
          (function (layer, properties) {
            // Create a mouseover event
            layer.on("mouseover", function (e) {
              var message = '<h4>Ebola Medical Centers</h4>' +
                            '<table>' +
                            '<tr><td style="text-align: right;">Center Name: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Centre"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Type: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Type"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Status: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Activity"] + '</b><td></tr>' +
                            '<tr><td style="text-align: right;">Organisation: </td><td>&nbsp;&nbsp; <b>' + feature.properties["Org"] + '</b><td></tr>' +
                            '</table>';
              info.showOtherMessage(message);
            });
            layer.on("mouseout", function (e) {
              // Start by reverting the style back
              layer.setStyle(layer.defaultOptions.style({properties: properties}));
              info.update();
            });
          })(layer, feature.properties);
        }
    });
    var extraLayers = {
        'Ebola Medical Centres': medicalCentresLayer,
        'SBTF Medical Centres': SBTFMedicalCentresLayer
    };

    var info;
    var regularLayers = {};

    $.each(layers, function (idx, val) {
      regularLayers[val['name']] = L.geoJson(regions,{
        style: getStyle(val['values'], val['threshold']),
        onEachFeature: function (feature, layer) {
          var pcoderef = feature.properties.PCODE_REF;
          var nameref = feature.properties.NAME_REF;
          layer.bindPopup("<b>" + nameref + " ("+ pcoderef+")</b><br />" + val['name'] + ": "+val['values'][pcoderef]);

          (function(layer, properties) {
            // Create a mouseover event
            layer.on("mouseover", function (e) {
              // Change the style to the highlighted version

              if (layer.defaultOptions.style != undefined) {
                var currentStyle = layer.defaultOptions.style({properties: properties});
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
              layer.setStyle(layer.defaultOptions.style({properties: properties}));
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
            '<tr><td style="text-align: right;">Country: </td><td>&nbsp;&nbsp; <b>' + props.CNTRY_NAME + '</b><td></tr>' +
            '<tr><td style="text-align: right;">District: </td><td>&nbsp;&nbsp; <b>' + props.NAME_REF + '</b><td></tr>' +
            '<tr><td style="text-align: right;">Value: </td><td>&nbsp;&nbsp; <b>' + layers[this._layer]['values'][props.PCODE_REF] + '</b><td></tr>' +
            '</table>'
            : 'Hover over a country/district');
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

      this._div.innerHTML = '<i style="background: white"></i> 0&ndash;' + threshold[0] + '<br>';
      for (var i = 0; i < threshold.length; i++) {
        this._div.innerHTML +=
            '<i style="background:' + color[i+1] + '"></i> ' +
            threshold[i] + (threshold[i + 1] ? '&ndash;' + threshold[i + 1] + '<br>' : '+');
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

    L.control.layers(regularLayers,extraLayers).addTo(map);


    map.on('baselayerchange', function (eventLayer) {
      info.updateLayer(eventLayer.name);
      legend.updateLayer(eventLayer.name);
    });


    var defaultLayer = layers['totalDeaths']['name'];
    map.addLayer(regularLayers[defaultLayer]);
    info.updateLayer(defaultLayer);
    legend.updateLayer(defaultLayer);
}