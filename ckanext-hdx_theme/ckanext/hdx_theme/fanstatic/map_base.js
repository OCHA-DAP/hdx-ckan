function setHDXBaseMap(map, maxZoomValue) {
  map.scrollWheelZoom.disable();

  getHDXBaseLayer(map, maxZoomValue);
  getHDXLabelsLayer(map, maxZoomValue);

  L.control.attribution({position: 'topright'}).addTo(map);
  map.setView([0, 0], 1);
}

function getHDXBaseLayer(map, maxZoomValue){
  return L.tileLayer($('#mapbox-baselayer-url-div').text(), {
    attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>',
    minZoom: 0,
    maxZoom: maxZoomValue
  }).addTo(map);
}

function getHDXLabelsLayer(map, maxZoomValue){
  return L.tileLayer($('#mapbox-labelslayer-url-div').text(), {
    minZoom: 0,
    maxZoom: maxZoomValue
  }).addTo(map);
}
