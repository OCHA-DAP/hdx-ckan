//function to generate the 3W component
//data is the whole 3W Excel data set
//geom is geojson file

function generate3WComponent(config,data,geom){
    var lookup = genLookup(geom,config);

    $('#title').html(config.title);
    $('#description').html(config.description);

    var containerIdPrefix = "#hdx-3W-";
    var whoContainerId = containerIdPrefix + 'who';
    var whatContainerId = containerIdPrefix + 'what';
    var whereContainerId = containerIdPrefix + 'where';

    var whenSelector = containerIdPrefix + 'slider-axis';
    var sliderSelector = '#js-rangeslider-0';

    var whoChart = dc.rowChart(whoContainerId);
    var whatChart = dc.rowChart(whatContainerId);
    var whereChart = dc.leafletChoroplethChart(whereContainerId);

    var cf = crossfilter(data);

    var whoDimension = cf.dimension(function(d){ return d[config.whoFieldName]; });
    var whatDimension = cf.dimension(function(d){ return d[config.whatFieldName]; });
    var whereDimension = cf.dimension(function(d){
        return d[config.whereFieldName].toLowerCase();
    });

    var startDimension, endDimension, firstDate, lastDate, baseDate, startDate;
    var minDate, maxDate, dateExtent, paused = true;
    var slider = $("#4w").find("input.slider");

    var dateFormat = config.formatFieldName;
    if (dateFormat == null){
        dateFormat = "MM/DD/YYYY";
    }

    if (config.startFieldName && config.endFieldName){
        startDimension = cf.dimension(function(d){
            return moment(d[config.startFieldName], dateFormat).toDate();
        });
        endDimension = cf.dimension(function(d){
            return moment(d[config.endFieldName], dateFormat).toDate();
        });

        firstDate = startDimension.bottom(1)[0][config.startFieldName];
        lastDate = endDimension.top(1)[0][config.endFieldName];
        var minDateMoment = moment(firstDate, dateFormat);
        var maxDateMoment = moment(lastDate, dateFormat);
        dateExtent = [minDateMoment.toDate(), maxDateMoment.toDate()];
        baseDate = new Date('1/1/1970');
        var now = moment(new Date());
        startDate = now.diff(baseDate, 'days');
        minDate = minDateMoment.diff(baseDate, 'days');
        maxDate = maxDateMoment.diff(baseDate, 'days');
    }



    var whoGroup = whoDimension.group();
    var whatGroup = whatDimension.group();
    var whereGroup = whereDimension.group();
    //var whenGroup = startDimension.group();
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
            .colors([config.colors[4]])
            .colorAccessor(function(d, i){return 0;})
            .xAxis().ticks(5);

    whatChart.width(whatWidth).height(400)
            .dimension(whatDimension)
            .group(whatGroup)
            .elasticX(true)
            .data(function(group) {
                return group.top(15);
            })
            .labelOffsetY(13)
            .colors([config.colors[4]])
            .colorAccessor(function(d, i){return 0;})
            .xAxis().ticks(5);

    dc.dataCount('#count-info')
            .dimension(cf)
            .group(all);

    whereChart.width(whereWidth).height(360)
            .dimension(whereDimension)
            .group(whereGroup)
            .center([0,0])
            .zoom(0)
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
                return feature.properties[config.joinAttribute].toLowerCase();
            })
            .popup(function(d){
                return lookup[d.key];
            })
            .renderPopup(true);

    dc.renderAll();

    var map = whereChart.map();
    zoomToGeom(geom);

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

    if (startDimension && endDimension){
        initSlider();
        $("#4w").show();
    }

    function drawAxis() {
        var axisHeight, axisWidth, dateFormat, margin, whenAxis, whenHeight;
        var whenWidth, xAxis, xScale;

        dateFormat = d3.time.format.multi([
            ["%b", function(d) {return d.getMonth()}],
            ["%Y", function() {return true}]
        ]);

        whenWidth = $(whenSelector).parent().width();
        whenHeight = 50;
        margin = {top: 0, bottom: whenHeight * 1.3, left: 15, right: 15};
        axisWidth = whenWidth - margin.left - margin.right;
        axisHeight = whenHeight - margin.top - margin.bottom;

        xScale = d3.time.scale()
            .domain(dateExtent)
            .range([0, axisWidth]);

        xAxis = d3.svg.axis()
            .scale(xScale)
            .outerTickSize(0)
            .ticks(Math.max(whenWidth / 100, 2))
            .tickFormat(dateFormat);

        whenAxis = d3.select(whenSelector)
            .attr('width', whenWidth)
            .attr('height', whenHeight)
            .append('g')
            .attr('transform', "translate(" + margin.left + ", " + margin.right + ")");

        console.log(whenAxis)
        whenAxis.append('g')
            .attr('class', 'x axis')
            .attr('transform', "translate(0, " + axisHeight + ")")
            .call(xAxis);
    };

    function zoomToGeom(geom){
        var bounds = d3.geo.bounds(geom);
        map.fitBounds([[bounds[0][1],bounds[0][0]],[bounds[1][1],bounds[1][0]]]);
    }

    function genLookup(geojson,config){
        var lookup = {};
        geojson.features.forEach(function(e){
            lookup[e.properties[config.joinAttribute].toLowerCase()] = String(e.properties[config.nameAttribute]);
        });
        return lookup;
    }

    function initSlider() {
        var $value, count;
        count = $('.slider').length;
        $value = $('#value')[0];

        slider.attr("min", minDate);
        slider.attr("max", maxDate);
        slider.attr("value", minDate);
        slider.rangeslider({
            polyfill: false,
            onInit: function() {
                updateValue($value, this.value);
                updateCharts(this.value);
                drawAxis();
            },
            onSlide: function(pos, value) {
                if (this.grabPos) {
                    updateValue($value, value);
                }
            },
            onSlideEnd: function(pos, value) {updateCharts(this.value)}
        });

        $("#4w").find(".play").click(function(){
            var playIcon = $(this).find(".glyphicon-play");
            var pauseIcon = $(this).find(".glyphicon-pause");

            if (paused){
                pauseIcon.show();
                playIcon.hide();
                paused = false;
                play();
            } else {
                pauseIcon.hide();
                playIcon.show();
                pause();
            }
        })
    }

    function play(value) {
        var step = 30
            , delay = 2000;
        if (value == null){
            value = parseInt(slider.val()) + step;
        }
        if ((value <= maxDate) && !paused) {
            slider.val(value).change();
            updateCharts(value);
            return setTimeout((function() {
                play(value + step);
            }), delay);
        } else if (value > maxDate && !paused) {
            slider.val(minDate).change();
            updateCharts(minDate);
            value = minDate;
            return setTimeout((function() {
                play(value + step);
            }), delay);
        }
    }

    function updateCharts(value) {
        dc.filterAll();
        var m = moment(baseDate).add('days', value);
        endDimension.filterRange([m.toDate(), Infinity]);
        startDimension.filterRange([baseDate, (m.add('d', 1)).toDate()]);
        dc.redrawAll();
    }

    function updateValue(e, value) {
        var m = moment(baseDate).add('days', value);
        e.textContent = m.format("l");
        //window.value = value
    }

    function pause() {
        paused = true;
    }

    function reset() {
        slider.val(minDate).change();
        updateCharts(minDate);
        $('.play').removeClass('hide');
        $('.pause').addClass('hide');
    }

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
            var data = dataArgs[0];
            if(config.datatype=='datastore'){
                data = data['result']['records']
            }
            if(config.geotype=='datastore'){
                geomArgs[0] = geomArgs[0]['result']['records']
            }
            var geom = geomArgs[0];
            geom.features.forEach(function(e){
                e.properties[config.joinAttribute] = String(e.properties[config.joinAttribute]);
            });

            generate3WComponent(config, data,geom);
            killLoadingEmbeddable("#hdx-3w-visualization-wrapper");
        });
    }
);

