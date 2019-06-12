var config = {
    dataURL:'data/data.json',
    geoURL:'data/geom.geojson',
    colors:['#FFFFFF','#d0d1e6','#a6bddb','#74a9cf','#2b8cbe','#045a8d'],
    source:'Text Source',
    link:'http://linktodata'
};

function generateROEADashboard(config,data,geom){

    //remove rwanda and burundi

    var cf = crossfilter(data);

    var whereDimension= cf.dimension(function(d){return d.NAME;});
    var timeDimension = cf.dimension(function(d){return d.YEAR;});

    timeDimension.filter('2015');

    var hazardGroup = whereDimension.group().reduceSum(function(d){return d.HAZARDS});
    var copingGroup = whereDimension.group().reduceSum(function(d){return d.COPINGCAPACITY});
    var vulnerabilityGroup = whereDimension.group().reduceSum(function(d){return d.VULNERABILITY});
    var overallGroup = whereDimension.group().reduceSum(function(d){return d.INFORM});

    var fundingGroup = cf.groupAll().reduceSum(function(d){return d.FUNDED});
    var refugeesGroup = cf.groupAll().reduceSum(function(d){return d.REFUGEES});
    var idpsGroup = cf.groupAll().reduceSum(function(d){return d.IDPS});
    var fsGroup = cf.groupAll().reduceSum(function(d){return d.FS});

    var mapChart = dc.leafletChoroplethChart('#hdx-roea-where')
        .width($('#hdx-roea-where').width())
        .height(400)
        .dimension(whereDimension)
        .group(overallGroup)
        .center([0,0])
        .zoom(0)    
        .geojson(geom)
        .colors(config.colors)
        .colorDomain([0, 4])
        .colorAccessor(function (d) {
            var c=0;
            if(d>8){
                c=5;
            } else if (d>7) {
                c=4;
            } else if (d>6) {
                c=3;
            } else if (d>5) {
                c=2;
            } else {
                c=1;
            } 
            return c;
            })   
        .featureKeyAccessor(function(feature){
            return feature.properties.id;
        }).popup(function(feature){
            return 'Click to filter <br />'+feature.properties.name;
        })
        .renderPopup(true);

    var formatNumber = function (d) {
        if (d > 0) {
            var output = d3.format(".4s")(d);
            if (output.slice(-1) == 'k') {
                output = Math.round(output.slice(0, -1) * 1000);
                output = '<span class="hdx-roea-value">' + d3.format("0,000")(output) + '</span>';
            } else if (output.slice(-1) == 'M') {
                output = '<span class="hdx-roea-value">' + d3.format(".1f")(output.slice(0, -1)) + '</span><span class="hdx-roea-small"> million</span>';
            } else if (output.slice(-1) == 'G') {
                output = '<span class="hdx-roea-value">' + output.slice(0, -1) + '</span><span class="hdx-roea-small"> billion</span>';
            } else {
                output = '<span class="hdx-roea-value">' + d3.format(".3s")(d) + '</span>';
            }
            return output;
        } else {
            return '<span class="hdx-roea-value">n/a</span>';
        }
    };

    var formatNumberDollar = function(d){
        return '<span class="hdx-roea-small">$</span>'+formatNumber(d);
    };

    var fundingND = dc.numberDisplay("#hdx-roea-funding")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(formatNumberDollar)
        .group(fundingGroup);

    var refugeesND = dc.numberDisplay("#hdx-roea-refugees")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(formatNumber)
        .group(refugeesGroup);

    var ipdsND = dc.numberDisplay("#hdx-roea-idps")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(formatNumber)
        .group(idpsGroup);

    var fsND = dc.numberDisplay("#hdx-roea-food")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(formatNumber)
        .group(fsGroup);                        

    dc.renderAll();

    map = mapChart.map();
    map.scrollWheelZoom.disable();
    zoomToGeom(geom);

    var legend = L.control({position: 'bottomright'});

    legend.onAdd = function (map) {

        var div = L.DomUtil.create('div', 'info legend'),
            labels = ['0 - 5','5.01 - 6','6.01 - 7','7.01 - 8','8.01+'];

        div.innerHTML = 'Risk Score<br />';
        for (var i = 0; i < labels.length; i++) {
            div.innerHTML +=
                '<i style="background:' + config.colors[4-i] + '"></i> ' + labels[4-i] +'<br />';
        }

        return div;
    };

    legend.addTo(map);


    L.tileLayer($('#mapbox-baselayer-url-div').text(), {
        attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>',
        maxZoom: 7
    }).addTo(map);

    L.tileLayer($('#mapbox-labelslayer-url-div').text(), {
        maxZoom: 7
    }).addTo(map);

    $('#overall').on('click',function(){
        mapChart.group(overallGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#overall').removeClass('hdx-roea-inactive');
        $('#overall').addClass('hdx-roea-active');              
    })

    $('#hazard').on('click',function(){
        mapChart.group(hazardGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#hazard').removeClass('hdx-roea-inactive');
        $('#hazard').addClass('hdx-roea-active');                 
    })    

    $('#vulnerability').on('click',function(){
        mapChart.group(vulnerabilityGroup);
        mapChart.redraw();
        $('.tab').addClass('hdx-roea-inactive');
        $('.tab').removeClass('hdx-roea-active');
        $('#vulnerability').removeClass('hdx-roea-inactive');
        $('#vulnerability').addClass('hdx-roea-active');                 
    })

    $('#coping').on('click',function(){
        mapChart.group(copingGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#coping').removeClass('hdx-roea-inactive');
        $('#coping').addClass('hdx-roea-active');                 
    })

    $('.hdx-3w-info').css('color',config.colors[4]);
}

function zoomToGeom(geom){
    var bounds = d3.geo.bounds(geom);
    map.fitBounds([[bounds[0][1],bounds[0][0]],[bounds[1][1],bounds[1][0]]]);
}

function reset(){
    dc.filterAll();
    dc.redrawAll();
    zoomToGeom(geom);
}

var map;
var geom;

$(document).ready(function(){
    //generateROEADashboard(config, tempData, tempGeo);

    var visConfig = JSON.parse($('#visualization-data').val());

    //load data
    var dataCall = $.ajax({
        type: 'GET',
        url: visConfig.data,
        dataType: 'json',
    });

    //load geometry
    var geomCall = $.ajax({
        type: 'GET',
        url: visConfig.geo,
        dataType: 'json',
    });
    //when both ready construct dashboard
    $.when(dataCall, geomCall).then(function(dataArgs, geomArgs){
        geom = geomArgs[0];
        for(var i= dataArgs[0].length-1;i>-1;i--){
            if(dataArgs[0][i].NAME=='RWA'||dataArgs[0][i].NAME=='BRN'){
                dataArgs[0].splice(i, 1);
            }
        }
        generateROEADashboard(config, dataArgs[0].result.records, geom);
        killLoadingEmbeddable("#hdx-roea");
    });
    $("#hdx-roea-datalink").html(visConfig.source+' <a href="'+visConfig.data_link_url+'">Data</a></p>');
    $('#reset').click(function(){reset();});
});

