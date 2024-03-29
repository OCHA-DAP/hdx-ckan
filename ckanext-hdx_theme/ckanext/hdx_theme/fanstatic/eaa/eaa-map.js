function prepareCountryList(countDatasets) {
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

          var veryActive = (country.activity_level == "active") ? "very-active-country" : "";

          var item = $("<div class='country-item " + veryActive + "'></div>").appendTo(one_char_box);
          var countryIdLower = country_id.toLowerCase();
          var line = $("<a href='group/" + countryIdLower + "' data-code='" + countryIdLower + "' data-bs-html='true' data-bs-placement='top'>" + country.title + "</a>").attr('data-bs-title', "<div class='marker-container'><div class='marker-box'><div class='marker-number'>" + displayDatasets + "</div><div class='marker-label'>datasets</div></div></div>").appendTo(item);
        }
      }
    }
  }
  $('.country-item:not(inactive) a').on('click', function(e) {
    var code = $(this).data('code');
    if (code) {
      openURL("group/" + code);
    }
  });
  var countryItems = document.querySelectorAll('.country-item:not(.inactive) a');
  countryItems.forEach(function(item) {
      new bootstrap.Tooltip(item);
  });
}

function getPopupContent(layer){
  let facilites = statistics = response = other = {};
  const eaaStats = layer.feature.properties.eaa_stats;
  if (eaaStats) {
    facilites = eaaStats.education_facilities;
    statistics = eaaStats.education_statistics;
    response = eaaStats.crisis_response;
    other = eaaStats.other;
  }

  return `
    <div class="leaflet-like-container">
      <div class="leaflet-popup-content-wrapper">
        <div class="leaflet-popup-content">
          <div class='marker-container-large'>
            <div class="title">${layer.feature.properties.title}</div>
            <div class="marker-set">
              <div class='marker-box'>
                <a href="${facilites.url || '#'}" target="_parent">
                  <div class='marker-title'>Education Facilities</div>
                  <div class='marker-number'>${facilites.count || '0'}</div>
                  <div class='marker-label'>datasets</div>
                </a>
              </div>
              <div class="line-break"></div>
              <div class='marker-box'>
                <a href="${statistics.url || '#'}" target="_parent">
                  <div class='marker-title'>Education Statistics</div>
                  <div class='marker-number'>${statistics.count || '0'}</div>
                  <div class='marker-label'>datasets</div>
                </a>
              </div>
              <div class="line-break"></div>
              <div class='marker-box'>
                <a href="${response.url || '#'}" target="_parent">
                  <div class='marker-title'>Crisis Response</div>
                  <div class='marker-number'>${response.count || '0'}</div>
                  <div class='marker-label'>datasets</div>
                </a>
              </div>
              <div class="line-break"></div>
              <div class='marker-box'>
                <a href="${other.url || '#'}" target="_parent">
                  <div class='marker-title'>Other</div>
                  <div class='marker-number'>${other.count || '0'}</div>
                  <div class='marker-label'>datasets</div>
                </a>
              </div>
          </div>
          </div>
        </div>
      </div>
      <div class="leaflet-popup-tip-container"><div class="leaflet-popup-tip"></div></div>
    </div>
    `;
}

function prepareMap(countDatasets, openNewWindow){
  var closeTooltip, country, countryLayer, country_id, feature, featureClicked, first_letter, getStyle, highlightFeature, k, line, map, mapID, onEachFeature, openURL, popup, resetFeature, topLayer, topPane, v, _i, _j, _len, _len1, _ref, closePopupTimeout;
  var openTarget = openNewWindow ? "_blank" : "_self";
  openURL = function(url) {
    return window.open(url, openTarget).focus();
  };
  closeTooltip = window.setTimeout(function() {
    return map.closePopup();
  }, 100);
  const $map = $("#map-popup");
  $map.on('mouseover', function(){
    clearTimeout(closePopupTimeout);
  });
  $map.on('mouseout', function(){
    resetFeature();
  });
  highlightFeature = function(e, update) {
    var countryID, layer;
    // clearTimeout(closePopupTimeout);
    layer = e.target;
    countryID = layer.feature.id;
    layer.setStyle({
      weight: 1,
      opacity: 0.2,
      color: '#ccc',
      fillOpacity: 1.0,
      fillColor: '#f5837b'
    });

    if (update){
      $map.html(getPopupContent(layer));
      $map.css('top', e.originalEvent.clientY + 'px');
      $map.css('left', e.originalEvent.clientX + 'px');
    }
  };

  getStyle = function(feature) {
    if (feature.properties.activity_level == "active"){
      return {
        weight: 0,
        fillOpacity: 0.5,
        fillColor: '#f5837b'
      }
    }

    return {
      weight: 0,
      fillOpacity: 0,
      fillColor: '#f2f2ef'
    };
  };

  resetFeature = function(e) {
    var layer;
    if (e) {
      layer = e.target;
      layer.setStyle(getStyle(layer.feature));
    }
    closePopupTimeout = setTimeout(function() {
        const $map = $("#map-popup").html('');
    }, 200);
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
      click: function(e) {
        highlightFeature(e, true);
      }
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
      feature.properties.title = countItem.title;
      feature.properties.eaa_stats = countItem.eaa_stats;
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
  getHDXBaseLayer(map, 7);

  map.scrollWheelZoom.disable();
  //map.featureLayer.setFilter(function() {
  //  return false;
  //});
  popup = new L.Popup({
    autoPan: false,
    offset: [0, 20]
  });
  $(popup._container).css('z-index', 20000);
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


  // var topLayer2 = getHDXLabelsLayer(map, 6);
  // topLayer2.setZIndex(7);

  // topPane.appendChild(topLayer2.getContainer());

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
}

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
    newItem.activity_level = item.activity_level;
    newItem.eaa_stats = item.eaa_stats;
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

