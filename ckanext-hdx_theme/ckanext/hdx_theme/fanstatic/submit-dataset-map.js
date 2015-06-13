$(document).ready(function() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function (position) {
      var latitude = position.coords.latitude;
      var longitude = position.coords.longitude;
    });


    var map = L.map('country-map')
    var HDXIcon = L.divIcon({
      className: 'svg-marker',
      iconSize: [35, 35],
      iconAnchor: [15, 35]
    });

    L.tileLayer('https://{s}.tiles.mapbox.com/v3/reliefweb.im6jg6a0/{z}/{x}/{y}.png', {
      attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>',
      maxZoom: 5
    }).addTo(map);

    map.locate({setView: true, maxZoom: 5});

    function onLocationFound(e) {
      var radius = e.accuracy / 2;

      L.marker(e.latlng, {
        icon: HDXIcon
      }).addTo(map);

      //L.circle(e.latlng, radius).addTo(map);
    }

    map.on('locationfound', onLocationFound);

  } else {
    $('#country-map').html("Geolocation API is not supported in your browser. :(");
  }
});