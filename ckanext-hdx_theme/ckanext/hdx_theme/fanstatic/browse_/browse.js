function prepareCountryList(countDatasets) {
  var columns = [['A', 'B', 'C'], ['D', 'E', 'F', 'G', 'H'], ['I', 'J', 'K', 'L'], ['M', 'N', 'O', 'P'], ['Q', 'R', 'S', 'T'], ['U', 'V', 'W', 'Y', 'Z']];
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
          // console.log(JSON.stringify(country));
          var displayDatasets = 0;
          var displayIndicators = 0;
          if (country.dataset_count != null)
            displayDatasets = country.dataset_count;
          if (country.indicator_count != null)
            displayIndicators = country.indicator_count;

          var veryActive = (country.activity_level == "active") ? "very-active-country" : "";

          var item = $("<div class='country-item " + veryActive + "'></div>").appendTo(one_char_box);
          var countryIdLower = country_id.toLowerCase();
          var line = $("<a href='/group/" + countryIdLower + "' data-code='" + countryIdLower + "' data-bs-html='true' data-bs-placement='top'>" + country.title + "</a>").attr('data-bs-title', "<div class='marker-container'><div class='marker-box'><div class='marker-number'>" + displayDatasets + "</div><div class='marker-label'>datasets</div></div></div>").appendTo(item);
        }
      }
    }
  }
  $('.country-item:not(inactive) a').on('click', function(e) {
    var code = $(this).data('code');
    if (code) {
      window.open("group/" + code, "_self");
    }
  });
  var countryItems = document.querySelectorAll('.country-item:not(.inactive) a');
  countryItems.forEach(function(item) {
      new bootstrap.Tooltip(item);
  });
}

function prepareMap(countDatasets, openNewWindow){
  var closeTooltip, countryLayer, country_id, feature, featureClicked, first_letter, getStyle, highlightFeature, map, onEachFeature, openURL, popup, resetFeature, topLayer, topPane, _i, _len, _ref, closePopupTimeout;
  var openTarget = openNewWindow ? "_blank" : "_self";
  openURL = function(url) {
    return window.open(url, openTarget).focus();
  };
  closeTooltip = window.setTimeout(function() {
    return map.closePopup();
  }, 100);
  var shownPopup = null;
  highlightFeature = function(e) {
    var layer;
    clearTimeout(closePopupTimeout);
    layer = e.target;
    shownPopup = e;
    layer.setStyle({
      weight: 1,
      opacity: 0.2,
      color: '#ccc',
      fillOpacity: 1.0,
      fillColor: '#f5837b'
    });
    popup.setLatLng(e.latlng);
    popup.setContent("<div class='marker-container'>" +
      "<div class='marker-label'>"+layer.feature.properties.name +"</div>" +
      "<div class='marker-box'> <div class='marker-number'>" + layer.feature.properties.datasets +
      "</div> <div class='marker-label'>datasets</div>" +
      "</div> </div>");
    if (!popup._map) {
      popup.openOn(map);
    }
  };

  getStyle = function(feature) {
    if (feature.properties.activity_level == "active"){
      return {
        weight: 0,
        fillOpacity: 0.5,
        fillColor: '#f5837b'
      };
    }

    return {
      weight: 0,
      fillOpacity: 0,
      fillColor: '#f2f2ef'
    };
  };

  resetFeature = function(e) {
    var layer;
    layer = e.target;
    layer.setStyle(getStyle(layer.feature));
    shownPopup = null;
    closePopupTimeout = setTimeout(function() {
      map.closePopup();
    }, 200);
  };
  featureClicked = function(e) {
    var code, layer;
    layer = e.target;
    code = layer.feature.id.toLowerCase();
    if (!shownPopup || code != shownPopup.target.feature.id.toLowerCase()) {
      if (shownPopup) {
        resetFeature(shownPopup);
      }
      highlightFeature(e);
      return;
    }
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
      feature.properties.activity_level = countItem.activity_level;
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

  var urlToParse = location.search;
  var result = parseQueryString(urlToParse );

  var country = $(worldJSON.features).filter(function(idx, el){
    return el.id === result['id'];
  });

  if(country && country[0] != null)
  {
    var specificCountryLayer = L.geoJson(country[0]);
    map.fitBounds(specificCountryLayer.getBounds());
  }


  topLayer = getHDXBaseLayer(map, 7);
  // map.addBaseLayer(topLayer);
  // topPane.appendChild(topLayer.getContainer());

  topPane = map.createPane('leaflet-labels-layer');
  topPane.style.zIndex = 450;
  // var topLayer2 = getHDXLabelsLayer(map, 6, 'leaflet-labels-layer');
  // topLayer2.setZIndex(7);
  // topPane.appendChild(topLayer2.getContainer());
  // topLayer.setZIndex(1);
}

var parseQueryString = function(url) {
  var urlParams = {};
  url.replace(
    new RegExp("([^?=&]+)(=([^&]*))?", "g"),
    function($0, $1, $2, $3) {
      urlParams[$1] = $3;
    }
  );

  return urlParams;
};

function prepareCount() {
  var countDatasets = {};
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
    newItem.activity_level = item.activity_level;
    countDatasets[code] = newItem;
  }
  return countDatasets;
}

function hdxScrollTo(anchor){
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

