function prepareCountryList() {
  var columns = [['A', 'B', 'C'], ['D', 'E', 'F', 'G', 'H'], ['I', 'J', 'K', 'L'], ['M', 'N', 'O', 'P'], ['Q', 'R', 'S', 'T'], ['U', 'V', 'Y', 'Z']];
  $('#option_map').click(function() {
    $(this).addClass('selected');
    $('#option_az').removeClass('selected');
    $("#map").show();
    return $("#country_list").hide();
  });
  $("#option_az").click(function() {
    $(this).addClass('selected');
    $("#option_map").removeClass('selected');
    $("#map").hide();
    return $("#country_list").show();
  });

  var country_list = $('#country_list');
  for (var _k = 0, _len2 = columns.length; _k < _len2; _k++) {
    var column = columns[_k];
    var one_column = $('<div class="col-md-2"></div>').appendTo(country_list);
    for (var _l = 0, _len3 = column.length; _l < _len3; _l++) {
      var char = column[_l];
      var one_char_box = $("<div class='char-box'></div>").appendTo(one_column);
      var one_char_labe = $("<div class='char-label'>" + char + "</div>").appendTo(one_char_box);
      var _ref1 = countries[char];
      for (var _m = 0, _len4 = _ref1.length; _m < _len4; _m++) {
        var countryItem = _ref1[_m];
        var country_id = countryItem[0];
        var country = countDatasets[country_id];

        if (country == null || (country.dataset_count == null && country.indicator_count == null)) {
          $("<div class='country-item inactive'><a>" + countryItem[1] + "</a></div>").appendTo(one_char_box);
        } else {
          var displayDatasets = 0;
          var displayIndicators = 0;
          if (country.dataset_count != null)
            displayDatasets = country.dataset_count;
          if (country.indicator_count != null)
            displayIndicators = country.indicator_count;

          var item = $("<div class='country-item'></div>").appendTo(one_char_box);
          var countryIdLower = country_id.toLowerCase();
          var line = $("<a href='group/" + countryIdLower + "' data-code='" + countryIdLower + "' data-html='true' data-toggle='tooltip' data-placement='top'>" + country.title + "</a>").attr('data-title', "<div class='marker-container'><div class='marker-box'><div class='marker-number'>" + displayIndicators + "</div><div class='marker-label'>indicators</div></div><div class='line-break'></div><div class='marker-box'><div class='marker-number'>" + displayDatasets + "</div><div class='marker-label'>datasets</div></div></div>").appendTo(item);
        }
      }
    }
  }
  $('.country-item:not(inactive) a').tooltip().on('click', function(e) {
    code = $(this).data('code');
    if (code) {
      openURL("group/" + code);
    }
  });
}

function prepareMap(){
  var closeTooltip, country, countryLayer, country_id, feature, featureClicked, first_letter, getStyle, highlightFeature, k, line, map, mapID, onEachFeature, openURL, popup, resetFeature, topLayer, topPane, v, _i, _j, _len, _len1, _ref;
  //mapID = 'yumiendo.ijchbik8';
  openURL = function(url) {
    return window.open(url, '_self').focus();
  };
  closeTooltip = window.setTimeout(function() {
    return map.closePopup();
  }, 100);
  highlightFeature = function(e) {
    var countryID, layer;
    layer = e.target;
    countryID = layer.feature.id;
    layer.setStyle({
      weight: 1,
      opacity: 0.2,
      color: '#ccc',
      fillOpacity: 1.0,
      fillColor: '#f5837b'
    });
    popup.setLatLng(e.latlng);
    popup.setContent("<div class='marker-container'> <div class='marker-box'> <div class='marker-number'>" + layer.feature.properties.indicators + "</div> <div class='marker-label'>indicators</div> </div> <div class='line-break'></div> <div class='marker-box'> <div class='marker-number'>" + layer.feature.properties.datasets + "</div> <div class='marker-label'>datasets</div> </div> </div>");
    if (!popup._map) {
      popup.openOn(map);
    }
  };
  resetFeature = function(e) {
    var layer;
    layer = e.target;
    layer.setStyle({
      weight: 0,
      fillOpacity: 1,
      fillColor: '#f2f2ef'
    });
  };
  featureClicked = function(e) {
    var code, layer;
    layer = e.target;
    code = layer.feature.id.toLowerCase();
    openURL("group/" + code);
  };
  onEachFeature = function(feature, layer) {
    layer.on({
      mousemove: highlightFeature,
      mouseout: resetFeature,
      click: featureClicked
    });
  };
  _ref = worldJSON['features'];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    feature = _ref[_i];
    country_id = feature.id;
    first_letter = country_id.substring(0, 1);
    feature.properties.datasets = 0;
    feature.properties.indicators = 0;

    var countItem = countDatasets[country_id];
    if (countItem != null){
      if (countItem.dataset_count != null)
        feature.properties.datasets = countItem.dataset_count;
      if (countItem.indicator_count != null)
        feature.properties.indicators = countItem.indicator_count;
    }
  }
  map = L.map('map', {
    center: [20, 0],
    zoom: 2,
    minZoom: 2,
    maxZoom: 4,
    tileLayer: {
      continuousWorld: false,
      noWrap: false
    }
  });
  getStyle = function(feature) {
    return {
      weight: 0,
      fillOpacity: 1,
      fillColor: '#f2f2ef'
    };
  };

  map.scrollWheelZoom.disable();
  //map.featureLayer.setFilter(function() {
  //  return false;
  //});
  popup = new L.Popup({
    autoPan: false,
    offset: [0, 0]
  });
  countryLayer = L.geoJson(worldJSON, {
    style: getStyle,
    onEachFeature: onEachFeature
  });
  countryLayer.addTo(map);

  topPane = map._createPane('leaflet-top-pane', map.getPanes().mapPane);

  //TODO: Talk to Luis to change the base map to have the country names on zoom level 2
  //after that switch the base map url to "http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
  /**
   * DO NOT REFACTOR map URL without fixing the TODO above
   */
  topLayer = L.tileLayer('https://{s}.tiles.mapbox.com/v3/yumiendo.ijchbik8/{z}/{x}/{y}.png', {
    attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>',
    maxZoom: 7
  }).addTo(map);
  topPane.appendChild(topLayer.getContainer());
  topLayer.setZIndex(7);
}

var countDatasets = {};
function prepareCount() {
  var datasetCounts = $("#datasetCounts");
  var dataPlain = datasetCounts.text();
  datasetCounts.remove();

  var data = JSON.parse(dataPlain);

  for (var i in data){
    var item = data[i];
    var code = item.name.toUpperCase();
    var newItem = {};
    newItem.title = item.title;
    newItem.dataset_count = item.dataset_count;
    newItem.indicator_count = item.indicator_count;
    countDatasets[code] = newItem;
  }
}

function scrollTo(anchor){
  $('html, body').animate({
    scrollTop: $(anchor).offset().top - 40
  }, 700);
}

function browse_by_menu() {
  var window_top = $(window).scrollTop();
  var browseByMenuAnchor = $('#browseByMenuAnchor');
  var browseByMenu = $('#browseByMenu');
  var div_top = browseByMenuAnchor.offset().top;
  if (window_top > div_top) {
    browseByMenu.addClass('stick');
  } else {
    browseByMenu.removeClass('stick');
  }

  //order the sections last to first !!!
  var sections = ['organizationsSection','topicsSection' , 'locationSection'];
  var found = false;
  for (var i in sections){
    var section = sections[i];
    var section_menu_item = $("#" + section + "MenuItem");
    if (found){
      section_menu_item.removeClass("active");
    }
    else{
      var section_top = $("#" + section).offset().top;
      if (window_top > section_top - 80){
        found = true;
        section_menu_item.addClass("active");
      }
      else{
        section_menu_item.removeClass("active");
      }
    }
  }
}

(function() {
  //fixed page menu
  $(window).scroll(browse_by_menu);
  browse_by_menu();

  prepareCount();
  prepareMap();
  prepareCountryList();
}).call(this);

