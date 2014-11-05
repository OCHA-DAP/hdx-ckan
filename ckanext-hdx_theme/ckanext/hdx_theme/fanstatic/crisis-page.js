$(document).ready(function() {
  map = L.map('ebola-map');

  L.tileLayer('http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: '<a class="mR45" href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>',
    maxZoom: 5
  }).addTo(map);

  map.setView([10, 0], 13);

});