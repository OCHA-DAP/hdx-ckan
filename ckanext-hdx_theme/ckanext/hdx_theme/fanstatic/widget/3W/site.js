//function to generate the 3W component
//data is the whole 3W Excel data set
//geom is geojson file

function generate3WComponent(config,data,geom){    
    $('#title').html(config.title);
    $('#description').html(config.description);

    var containerIdPrefix = "#hdx-3W-";
    var whoContainerId = containerIdPrefix + 'who';
    var whatContainerId = containerIdPrefix + 'what';
    var whereContainerId = containerIdPrefix + 'where';

    var whoChart = dc.rowChart(whoContainerId);
    var whatChart = dc.rowChart(whatContainerId);
    var whereChart = dc.leafletChoroplethChart(whereContainerId);

    var cf = crossfilter(data);

    var whoDimension = cf.dimension(function(d){ return d[config.whoFieldName]; });
    var whatDimension = cf.dimension(function(d){ return d[config.whatFieldName]; });
    var whereDimension = cf.dimension(function(d){ return d[config.whereFieldName]; });

    var whoGroup = whoDimension.group();
    var whatGroup = whatDimension.group();
    var whereGroup = whereDimension.group();
    var all = cf.groupAll();

    var whoWidth = $(whoContainerId).width();
    var whatWidth = $(whatContainerId).width();
    var whereWidth = $(whereContainerId).width();

    whoChart.width(whoWidth).height(400)
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

    whatChart.width(whatWidth).height(400)
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

    whereChart.width(whereWidth).height(360)
            .dimension(whereDimension)
            .group(whereGroup)
            .center([config.y,config.x])
            .zoom(config.zoom)
            .geojson(geom)
            .colors(['#CCCCCC', config.colors[4]])
            .colorDomain([0, 1])
            .colorAccessor(function (d) {
                if(d>0){
                    return 1;
                } else {
                    return 0;
                }
            })
            .featureKeyAccessor(function(feature){
                return feature.properties[config.joinAttribute];
            }).map();

    dc.renderAll();

    var map = whereChart.map();
    console.log(map);

    var g = d3.selectAll(whoContainerId).select('svg').append('g');
    
    g.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', whoWidth/2)
        .attr('y', 400)
        .text('Activities');

    var g = d3.selectAll(whatContainerId).select('svg').append('g');
    
    g.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', whatWidth/2)
        .attr('y', 400)
        .text('Activities');  

}

$(document).ready(
    function(){
        //load config
        var config = JSON.parse($('#visualization-data').val());

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
                dataArgs[0] = dataArgs[0]['result']['records']
            }
            if(config.geotype=='datastore'){
                geomArgs[0] = geomArgs[0]['result']['records']
            }
            var geom = geomArgs[0];
            geom.features.forEach(function(e){
                e.properties[config.joinAttribute] = String(e.properties[config.joinAttribute]);
            });
            generate3WComponent(config,dataArgs[0],geom);
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
    }
);

