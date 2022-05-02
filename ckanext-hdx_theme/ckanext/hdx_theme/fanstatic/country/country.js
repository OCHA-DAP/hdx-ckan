function drawMap() {
    let crisisMapDiv = $("#crisis-map");
    if (!crisisMapDiv.length){
        return;
    }

    let maxZoomValue = 4;
    let map = L.map('crisis-map', { attributionControl: false });
    setHDXBaseMap(map, maxZoomValue);

    let countryMapPolygon = $("#countryMapPolygon");
    let rawData = countryMapPolygon.text();
    countryMapPolygon.text("");
    try{
        let data = JSON.parse(rawData);
    } catch (err) {
        console.log("Error parsing json - set default map");
        return;
    }
    if (data.geometry == null){
        console.log("Set default map");
        return;
    }

    //Need to compute Top-Left corner and Bottom-Right corner for polygon.
    let minLat, minLng, maxLat, maxLng;
    let init = false;

    //Use a stack to traverse the geojson since we can gave many levels of arrays in arrays
    var stackArrays = [];
    var stackIndex = [];

    stackArrays.push(data.geometry.coordinates);
    stackIndex.push(0);
    while (stackArrays.length > 0){
        var array = stackArrays.pop();
        var index = stackIndex.pop();

        if (index < array.length){
            var item = array[index];
            //check if we reached a tuple of coordinates
            if (!$.isArray(item)){
                var lat = parseFloat(array[1]);
                var lng = parseFloat(array[0]);
                //adjust min/max
                if (init){
                    if (lat < minLat)
                        minLat = lat;
                    if (lat > maxLat)
                        maxLat = lat;
                    if (lng < minLng)
                        minLng = lng;
                    if (lng > maxLng)
                        maxLng = lng;
                } else {
                    init = true;
                    minLat = maxLat = lat;
                    minLng = maxLng = lng;
                }
            }
            //push in the stack the current array with the next index
            index++;
            stackArrays.push(array);
            stackIndex.push(index);
            //if we haven't reached a tuple of coordinates, add in the stack the array
            if ($.isArray(item)){
                stackArrays.push(item);
                stackIndex.push(0);
            }
        }
    }



    // var latitude = minLat + (maxLat-minLat)/2;
    // var longitude = minLng + (maxLng-minLng)/2;
    // var zoom = maxZoomValue;
    //
    // console.log(latitude);
    // console.log(longitude);

    L.geoJson(data,{
      style: function(feature){
          return {color: '#ff493d', fillColor: '#ff493d', fillOpacity: 0.6, opacity: 0.7, weight: 1};
      }
    }).addTo(map);

    //map.setView([latitude, longitude], zoom);
    console.log([[minLat, minLng], [maxLat, maxLng]]);
    map.fitBounds([[minLat, minLng], [maxLat, maxLng]], {
        maxZoom: maxZoomValue
    });

}

function c3ActiveSparklineRedraw() {
  $('.carousel-inner .item.active .sparkline').each(function() {
    var th = $(this);
    var chart = th.data("chart");
    th.css("overflow", "hidden");
    var width = th.width();
    console.log("width: " + width);
    chart.resize({
      height: 74,
      width: width
    });
    th.css("visibility", "visible");
    th.css("overflow", "visible");
  });
}

function c3Sparklines(){
  $('.sparkline').each(function() {
    var th = $(this),
    data = JSON.parse(th.text());
    th.text("");
    th.attr("style", "");

    var chart = c3.generate({
      bindto: this,
      point: {
        show: false
      },
      legend:{
        show: false
      },
      color: {
          pattern: ['#007ce0']
      },
      data: {
        json: data,
        keys: {
          x: 'formatted_date',
          value: ['value']
        },
        x: 'x',
        xFormat: '%b %d, %Y' //'%Y-%m-%dT%H:%M:%S'
      },
      axis: {
        x: {
          show: false,
          type: 'timeseries',
          tick: {
            format: '%b %d, %Y'
          }
        },
        y: {
          show: false
        }
      },
      tooltip: {
        format: {
          value: d3.format(",")
        }
      }
    });
    th.data("chart", chart);
    if (th.parents(".item.active").length === 0) {
      th.css("visibility", "hidden");
    }
  });
}


function buildGraphs() {
    $(".topline-charts").each(function (index){
        var element = $(this);
        var dataEl = element.find(".data");
        var dataRaw = dataEl.text();
        dataEl.remove();

        var unitEl = element.find(".unit-name");
        var unitName = unitEl.text();
        unitEl.remove();

        var data = JSON.parse(dataRaw);
        var chartEl = element.find(".chart-item")[0];

        var chartType = 'bar';
        if (data.length > 4)
            chartType = 'area';

        var graph = c3.generate({
            bindto: chartEl,
            color: {
                //pattern: [['#46c7c3', '#f7968f', '#3b93ea', '#00bfb4', '#f46358'][index%5]] //previous colours
                pattern: ['#46c7c3', '#f7968f', '#3b93ea', '#00bfb4', '#f46358'] //previous colours
            },
            padding: {
                bottom: 10
            },
            data: {
                json: data,
                xFormat: '%Y-%m-%d',
                keys: {
                    x: "date",
                    value: ["value"]
                },
                names: {
                    "value": unitName
                },
                type: chartType
            },
            legend:{
                show: false
            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        rotate: 30,
                        //culling: false,
                        format: '%Y'
                    }
                },
                y: {
                    label: {
                        text: unitName,
                        position: 'outer-middle'
                    }
                }
            }
        });
    });
}

function onDataCompletenessExpand() {
  $(".data-item-details").toggle(this.checked);
}

function handleWindowWidth() {
  const CUT_POINT = 1024;
  if (!window.hdxMobileTopline) {
    if (window.innerWidth < CUT_POINT) {
      window.hdxMobileTopline = true;
      $(".carousel").hide();
      $(".mobile-carousel").show();
    }
  } else {
    if (window.innerWidth >= CUT_POINT) {
      window.hdxMobileTopline = false;
      $(".carousel").show();
      $(".mobile-carousel").hide();
    }
  }
}

function mobileTopline() {
  handleWindowWidth(); //initial setup
  $( window ).resize(handleWindowWidth);
}

$(document).ready(function() {
    drawMap();
    buildGraphs();
    c3Sparklines();
    c3ActiveSparklineRedraw(); //reset visibility / overflow
    $("#expand-data-completeness").change(onDataCompletenessExpand);
    $('#key-figures-carousel').bind('slid.bs.carousel', function (e) {
      console.log('after');
      c3ActiveSparklineRedraw();
    });
    mobileTopline();
});
