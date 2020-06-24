var substituteDatasetNamesWithLinks; //function that will substitute dataset names :)
$(document).ready(function(){
    var LABEL_MAX_LENGTH = 40;
    var dataPageviews = JSON.parse($("#stats-data-pageviews").html());
    var dataTopDownloads = JSON.parse($("#stats-data-top-downloads").html());


    var configPageviews = {
        bindto: "#chart-data-pageviews",
        padding: {
            bottom: 20
        },
        color: '#0077ce',
        data: {
            json: dataPageviews,
            keys: {
                x: 'date',
                value: ['pageviews', 'downloads']
            },
            type: 'line',
            regions: {
                'pageviews': null,
                'downloads': null
            },
            names: {
                'pageviews': 'Page Views',
                'downloads': 'Downloads'

            },
            // axes: {
            //     'pageview': 'y',
            //     'downloads': 'y2'
            // }
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d'
                }
            },
            // y: {
            //     label: "Page Views"
            // },
            // y2: {
            //     label: "Downloads",
            //     show: true
            // }
        },
        grid: {
          y: {
            show: true
          }
        }
    };

    if (dataPageviews.length > 2){
        var startDate = dataPageviews[dataPageviews.length - 2].date;
        configPageviews.data.regions['pageviews'] = [{'start': startDate, 'style': 'dashed'}];
        configPageviews.data.regions['downloads'] = [{'start': startDate, 'style': 'dashed'}];
    }

    var pageviewChart = c3.generate(configPageviews);

    $.each(dataTopDownloads, function(idx, el) {
        //trim names
        var name = el['name'];
        var trimName = name;
        if (name && name.length > LABEL_MAX_LENGTH){
            trimName = name.slice(0, LABEL_MAX_LENGTH - 3) + "...";
        }
        el['idx'] = idx.toString();
        el['trimName'] = trimName;
    });

    substituteDatasetNamesWithLinks = function () {
        // console.log("Substituting");
        d3.selectAll('#chart-data-top-downloads .c3-axis-x .tick text')
            .each(function(d,i){
                // augment tick contents with link
                var self = d3.select(this);
                var text = self.text();
                var dataIndex = parseInt(text) % dataTopDownloads.length;
                var item = dataTopDownloads[dataIndex];
                self.html("<a xlink:href='"+ item['url'] +"' target='_blank' style='fill: #0077ce; cursor: pointer;'>"+ item['trimName'] +"</a>");
            });
        d3.selectAll('#chart-data-top-downloads svg > g:nth-of-type(2)').attr('style', 'display: none;');
    }.bind(this);

    var top_downloads_chart_id = "#chart-data-top-downloads";
    var configTopDownloads = {
        bindto: top_downloads_chart_id,
        padding: {
            bottom: 20,
            left: 250
        },
        size: {
            height: 320
        },
        color: '#0077ce',
        data: {
            json: dataTopDownloads,
            keys: {
                x: 'idx',
                value: ['value']
            },
            type: 'bar',
            names: {
                'value': 'Downloads'
            }
        },
        grid: {
            y: {
                show: true
            }
        },
        axis: {
            rotated: true,
            x: {
                type: 'category'
            }
        },
        legend: {
            show: false
        },
        zoom: {
            enabled: false,
            type: 'drag',
            extent: [1.5, 2]
        },
        subchart: {
            show: false
        },
        tooltip: {
            format: {
                title: function (d) {
                  return dataTopDownloads[d]['name'];
                },
                value: function (value, ratio, id, index) {
                    var el = dataTopDownloads[index];
                    var total = el['total'];
                    var numberFormat = d3.format(".2%");
                    var percent = numberFormat(el['value'] / total);
                    return value + " (" + percent + " out of " + total + ")";
                }
            }
        },
        onresized: substituteDatasetNamesWithLinks,
        onrendered: substituteDatasetNamesWithLinks
    };

    if (dataTopDownloads.length === 1){
        var datasetName = $('#stats-data-single-dataset-name').text();
        setupDatasetDownloads("#stats-data-single-dataset-downloads", top_downloads_chart_id, {
            size: {
                height: 320
            },
            data: {
                names: {
                    'value': datasetName
                }
            },
            legend: {
                show: true
            }

        });
        $(top_downloads_chart_id + ' .c3-legend-item-event').remove();
    } else {
        var topDownloadsChart = c3.generate(configTopDownloads);
        enableMouseWheelZoom(top_downloads_chart_id, dataTopDownloads.length, topDownloadsChart);
        substituteDatasetNamesWithLinks();
    }

});

function enableMouseWheelZoom(chartId, itemCount, c3_chart){
    var MAX_NUMBER_OF_VALUES = 7.5;

    var normalizeWheel = function (/*object*/ event) /*object*/ {
        var sX = 0, sY = 0,       // spinX, spinY
            pX = 0, pY = 0;       // pixelX, pixelY
        var PIXEL_STEP  = 10;
        var LINE_HEIGHT = 40;
        var PAGE_HEIGHT = 800;


        // Legacy
        if ('detail'      in event) { sY = event.detail; }
        if ('wheelDelta'  in event) { sY = -event.wheelDelta / 120; }
        if ('wheelDeltaY' in event) { sY = -event.wheelDeltaY / 120; }
        if ('wheelDeltaX' in event) { sX = -event.wheelDeltaX / 120; }

        // side scrolling on FF with DOMMouseScroll
        if ( 'axis' in event && event.axis === event.HORIZONTAL_AXIS ) {
            sX = sY;
            sY = 0;
        }

        pX = sX * PIXEL_STEP;
        pY = sY * PIXEL_STEP;

        if ('deltaY' in event) { pY = event.deltaY; }
        if ('deltaX' in event) { pX = event.deltaX; }

        if ((pX || pY) && event.deltaMode) {
            if (event.deltaMode == 1) {          // delta in LINE units
                pX *= LINE_HEIGHT;
                pY *= LINE_HEIGHT;
            } else {                             // delta in PAGE units
                pX *= PAGE_HEIGHT;
                pY *= PAGE_HEIGHT;
            }
        }

        // Fall-back if spin cannot be determined
        if (pX && !sX) { sX = (pX < 1) ? -1 : 1; }
        if (pY && !sY) { sY = (pY < 1) ? -1 : 1; }

        return {
            spinX  : sX,
            spinY  : sY,
            pixelX : pX,
            pixelY : pY
        };
    };

    var zoomHandler = function() {
        var event = d3.event;
        event.preventDefault();
        event.stopPropagation();
        var eventDelta = normalizeWheel(event);

        var swapAxis = true;
        var delta = -1*(swapAxis ? eventDelta.pixelY : eventDelta.pixelX);

        if (!c3_chart.internal.brush.leftMargin) {
            c3_chart.internal.brush.leftMargin = 0;
            c3_chart.internal.brush.leftMarginRedraw = 0;
        }
        // c3_chart.internal.brush.extent([0, MAX_NUMBER_OF_VALUES]).update();
        var leftMargin = c3_chart.internal.brush.leftMargin;
        leftMargin = leftMargin - delta / 10;
        if (leftMargin < 0) {
            leftMargin = 0;
        }
        if (leftMargin + MAX_NUMBER_OF_VALUES > itemCount) {
            leftMargin = itemCount - MAX_NUMBER_OF_VALUES;
        }
        c3_chart.internal.brush.leftMargin = leftMargin;
        c3_chart.internal.brush.extent([leftMargin, leftMargin + MAX_NUMBER_OF_VALUES]);
        var dif = c3_chart.internal.brush.leftMarginRedraw - c3_chart.internal.brush.leftMargin;
        if (dif < 0) {
            dif *= -1;
        }
        if (dif > 0.1) {
            c3_chart.internal.redrawForBrush();
            c3_chart.internal.brush.leftMarginRedraw = c3_chart.internal.brush.leftMargin;
            // console.log('Redraw for delta: ' + delta / 10);
            substituteDatasetNamesWithLinks();
        } else {
            // console.log('Skipped redraw');
        }

    };


    if (itemCount > MAX_NUMBER_OF_VALUES) {
        d3.select(chartId).select('svg')
            .on('wheel.zoom', zoomHandler.bind(this))
            .on('mousewheel.zoom', zoomHandler.bind(this))
            .on('DOMMouseScroll.zoom', zoomHandler.bind(this));
        c3_chart.internal.brush.leftMargin = 0;
        c3_chart.internal.brush.extent([0, MAX_NUMBER_OF_VALUES]).update();
        c3_chart.internal.redrawForBrush();
    }
}
