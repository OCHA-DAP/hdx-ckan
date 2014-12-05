$(document).ready(function() {
  map = L.map('crisis-map', { attributionControl: false });
  map.scrollWheelZoom.disable();
  L.tileLayer($('#crisis-map-url-div').text(), {
    attribution: ' © <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 10
  }).addTo(map);

  L.control.attribution({position: 'topright'}).addTo(map);
  map.setView([5, -70], 5);

//  drawDistricts(map);
//  c3Sparklines();
});
