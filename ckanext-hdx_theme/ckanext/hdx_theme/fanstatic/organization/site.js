
//function to generate the 3W component
//data is the whole 3W Excel data set
//geom is geojson file

function generate3WComponent(config,data,geom){    
    
    $('#title').html(config.title);
    $('#description').html(config.description);

    var whoChart = dc.rowChart('#hdx-3W-who');
    var whatChart = dc.rowChart('#hdx-3W-what');
    var whereChart = dc.geoChoroplethChart('#hdx-3W-where');

    var cf = crossfilter(data);

    var whoDimension = cf.dimension(function(d){ return d[config.whoFieldName]; });
    var whatDimension = cf.dimension(function(d){ return d[config.whatFieldName]; });
    var whereDimension = cf.dimension(function(d){ return d[config.whereFieldName]; });

    var whoGroup = whoDimension.group();
    var whatGroup = whatDimension.group();
    var whereGroup = whereDimension.group();
    var all = cf.groupAll();

    whoChart.width($('#hxd-3W-who').width()).height(400)
            .dimension(whoDimension)
            .group(whoGroup)
            .elasticX(true)
            .data(function(group) {
                return group.top(15);
            })
            .labelOffsetY(13)
            .colors(config.colors)
            .colorDomain([0,7])
            .colorAccessor(function(d, i){return i%8;})
            .xAxis().ticks(5);

    whatChart.width($('#hxd-3W-what').width()).height(400)
            .dimension(whatDimension)
            .group(whatGroup)
            .elasticX(true)
            .data(function(group) {
                return group.top(15);
            })
            .labelOffsetY(13)
            .colors(config.colors)
            .colorDomain([0,7])
            .colorAccessor(function(d, i){return i%8;})
            .xAxis().ticks(5);

    dc.dataCount('#count-info')
            .dimension(cf)
            .group(all);

    whereChart.width($('#hxd-3W-where').width()).height(400)
            .dimension(whereDimension)
            .group(whereGroup)
            .colors(['#DDDDDD', config.colors[3]])
            .colorDomain([0, 1])
            .colorAccessor(function (d) {
                if(d>0){
                    return 1;
                } else {
                    return 0;
                }
            })
            .overlayGeoJson(geom.features, 'Regions', function (d) {
                return d.properties[config.joinAttribute];
            })
            .projection(d3.geo.mercator().center([config.x,config.y]).scale(config.zoom))
            .title(function(d){
                return d.key;
            });

    dc.renderAll();
    
    var g = d3.selectAll('#hdx-3W-who').select('svg').append('g');
    
    g.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', $('#hdx-3W-who').width()/2)
        .attr('y', 400)
        .text('Activities');

    var g = d3.selectAll('#hdx-3W-what').select('svg').append('g');
    
    g.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', $('#hdx-3W-what').width()/2)
        .attr('y', 400)
        .text('Activities');  

}

//load 3W data

var dataCall = $.ajax({ 
    type: 'GET', 
    url: config.data, 
    dataType: 'json',
});

//load geometry

var geomCall = $.ajax({ 
    type: 'GET', 
    url: config.geo, 
    dataType: 'json',
});

//when both ready construct 3W

$.when(dataCall, geomCall).then(function(dataArgs, geomArgs){
    if(config.datatype=='datastore'){

    }else{

    }

    if(config.geotype=='datastore'){

    }else{

    }
    var geom = geomArgs[0];
    geom.features.forEach(function(e){
        e.properties[config.joinAttribute] = String(e.properties[config.joinAttribute]);
    })
    generate3WComponent(config,dataArgs[0],geomArgs[0]);
});

/*
 * Example of datastore query used previously.
 * 
var sql = 'SELECT "Indicator", "Date", "Country", value FROM "f48a3cf9-110e-4892-bedf-d4c1d725a7d1" ' +
        'WHERE "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola deaths\' '+
        'OR "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola cases\' '+
        'ORDER BY "Date"';

var data = encodeURIComponent(JSON.stringify({sql: sql}));


$.ajax({
  type: 'POST',
  dataType: 'json',
  url: 'https://data.hdx.rwlabs.org/api/3/action/datastore_search_sql',
  data: data,
  success: function(data) {

  }
});
*/