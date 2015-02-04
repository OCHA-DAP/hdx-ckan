$(document).ready(function() {
  map = L.map('colombia-map', { attributionControl: false });
  map.scrollWheelZoom.disable();
  L.tileLayer($('#crisis-map-url-div').text(), {
    attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 10
  }).addTo(map);

  L.control.attribution({position: 'topright'}).addTo(map);
  map.setView([4, -77], 5);

  drawDistricts(map);
  // c3Sparklines();
});

// function c3Sparklines(){
//   $('.sparkline').each(function() {
//     var th = $(this),
//     data = JSON.parse(th.text());
//     th.text("");
//     th.attr("style", "");

//     var chart = c3.generate({
//       bindto: this,
//       point: {
//         show: false
//       },
//       legend:{
//         show: false
//       },
//       color: {
//           pattern: ['#007ce0']
//       },
//       data: {
//         json: data,
//         keys: {
//           x: 'date',
//           value: ['value']
//         },
//         x: 'x',
//         xFormat: '%b %d, %Y' //'%Y-%m-%dT%H:%M:%S'
//       },
//       axis: {
//         x: {
//           show: false,
//           type: 'timeseries',
//           tick: {
//             format: '%b %d, %Y'
//           }
//         },
//         y: {
//           show: false
//         }
//       },
//       tooltip: {
//         format: {
//           value: d3.format(",")
//         }
//       }
//     });
//     });
// }

function drawDistricts(map){
  var color = ["none","#ffe082", "#ffbd13", "#ff8053", "#ff493d"];

  var layers = {
    totalIDPs: {
      name: 'Number of IDPs per 100,000 inhabitants in 2013',
      threshold: [1, 50, 100, 500],
      values: totalIDPs
    }
    // totalCases: {
    //   name: 'Cumulative Cases of Ebola',
    //   threshold: [1, 100, 300, 800],
    //   values: totalCases
    // },
    // totalCasesPerArea: {
    //   name: 'Cumulative Cases per 1000 Sq. km',
    //   threshold: [1, 50, 100, 500],
    //   values: totalCasesPerArea
    // },
    // totalDeathsPerArea: {
    //   name: 'Cumulative Deaths per 1000 Sq. km',
    //   threshold: [1, 25, 50, 200],
    //   values: totalDeathsPerArea
    // },
    // totalCasesPerPop:{
    //   name: 'Cumulative Cases per 100,000 people',
    //   threshold: [0.1, 25, 50, 100],
    //   values: totalCasesPerPop
    // },
    // totalDeathsPerPop:{
    //   name: 'Cumulative Deaths per 100,000 people',
    //   threshold: [0.1, 20, 40, 80],
    //   values: totalDeathsPerPop
    // }
  };

  function getStyle(values, threshold){
    function internalGetColor(color, i){
      return {color: color[i], fillColor: color[i], fillOpacity: 0.6, opacity: 0.7, weight: 2};
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

  // var medicalCentresStyle = function(feature){
  //   if(feature.properties.Status == "Functional"){
  //     return   {radius: 5,
  //       fillColor: "#1ebfb3",
  //       color: "#000",
  //       weight: 1,
  //       opacity: 0.8,
  //       fillOpacity: 0.8};
  //   }
  //   else {
  //     return   {radius: 5,
  //       fillColor: "#007ce0",
  //       color: "#000",
  //       weight: 1,
  //       opacity: 0.8,
  //       fillOpacity: 0.8};
  //   }
  // };

//   var medicalCentresLayer = L.geoJson(medicalCentres, {
//     pointToLayer: function (feature, latlng) {
//       return L.circleMarker(latlng,medicalCentresStyle(feature));
//     },
//     onEachFeature: function (feature, layer) {
// //          layer.bindPopup("Centre Name: " + feature.properties["Centre Name"] + "<br />Type: " + feature.properties["Type1"] + "<br />Status: " + feature.properties["Status"] + "<br />Organisation: " + feature.properties["Primary Organisation"]);
//       (function (layer, properties) {
//         // Create a mouseover event
//         layer.on("mouseover", function (e) {
//           if (!L.Browser.ie && !L.Browser.opera) {
//             layer.bringToFront();
//           }
//           var name = feature.properties["Centre Name"];
//           if (name == null)
//             name = "";
//           var type = feature.properties["Type1"];
//           if (type == null)
//             type = "";
//           var status = feature.properties["Status"];
//           if (status == null)
//             status = "";
//           var organisation = feature.properties["Primary Organisation"];
//           if (organisation == null)
//             organisation = "";

//           var message = '<h4>Ebola Medical Centers</h4>' +
//             '<table>' +
//             '<tr><td style="text-align: right;">Center Name: </td><td>&nbsp;&nbsp; <b>' + name + '</b><td></tr>' +
//             '<tr><td style="text-align: right;">Type: </td><td>&nbsp;&nbsp; <b>' + type + '</b><td></tr>' +
//             '<tr><td style="text-align: right;">Status: </td><td>&nbsp;&nbsp; <b>' + status + '</b><td></tr>' +
//             '<tr><td style="text-align: right;">Organisation: </td><td>&nbsp;&nbsp; <b>' + organisation + '</b><td></tr>' +
//             '</table>';
//           info.showOtherMessage(message);
//         });
//         layer.on("mouseout", function (e) {
//           // Start by reverting the style back
//           layer.setStyle(layer.defaultOptions.style({properties: properties}));
//           info.update();
//         });
//       })(layer, feature.properties);
//     }
//   });
//   var extraLayers = {
//     'Ebola Treatment Centres (ETCs)': medicalCentresLayer
//   };

  var info;
  var regularLayers = {};

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
              // if (!L.Browser.ie && !L.Browser.opera) {
              //   layer.bringToFront();
              //   for (eLayer in extraLayers)
              //     if (map.hasLayer(extraLayers[eLayer]))
              //       extraLayers[eLayer].bringToFront();
              // }

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
      '<tr><td style="text-align: right;">Country: </td><td>&nbsp;&nbsp; <b>' + props.NAME + '</b><td></tr>' +
      '<tr><td style="text-align: right;">District: </td><td>&nbsp;&nbsp; <b>' + props.NAME_DEPT + '</b><td></tr>' +
      '<tr><td style="text-align: right;">Value: </td><td>&nbsp;&nbsp; <b>' + layers[this._layer]['values'][props.PCODE] + '</b><td></tr>' +
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

    this._div.innerHTML = '<div><i style="background: white"></i> 0&ndash;' + threshold[0] + '</div>';
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

  L.control.layers(regularLayers).addTo(map);


  map.on('baselayerchange', function (eventLayer) {
    info.updateLayer(eventLayer.name);
    legend.updateLayer(eventLayer.name);
  });


  var defaultLayer = layers['totalIDPs']['name'];
  map.addLayer(regularLayers[defaultLayer]);
  info.updateLayer(defaultLayer);
  legend.updateLayer(defaultLayer);
}
