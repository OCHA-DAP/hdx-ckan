$(document).ready(function() {
  map = L.map('ebola-map', null, { zoomControl:false });

  L.tileLayer('http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: '<a class="mR45" href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>',
    maxZoom: 10
  }).addTo(map);

  map.setView([9, 0], 5);


  //http://ckan.lo:5000/api/3/action/group_show?id=afg
  var countries = [
    'lbr',
    'sle',
    'gin'
  ];
  $.each(countries, function (idx, val){
    var url = "/api/3/action/group_show?id=";
    $.ajax({
      url: url + val
    })
      .done(function (json){
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
            if (dataList[i].key == "geojson"){
              var json = JSON.parse(dataList[i].value);
              data = json.geometry;
            }
          console.log(data);
          L.geoJson(data, {
            style: style
          }).addTo(map);
        }
      });
  });
});