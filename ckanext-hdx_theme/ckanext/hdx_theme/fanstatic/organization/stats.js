$(document).ready(function(){
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
                'pageviews': null
            },
            names: {
                'pageviews': 'Page Views',
                'downloads': 'Downloads'

            },
            axes: {
                'pageview': 'y',
                'downloads': 'y2'
            }
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d'
                }
            },
            y: {
                label: "Page Views"
            },
            y2: {
                label: "Downloads",
                show: true
            }
        },
        regions: {
            'value': [{'start': dataPageviews.length-1, 'style': 'dashed'}]
        },
        grid: {
          y: {
            show: true
          }
        }
    };

    if (dataPageviews.length > 2){
        var startDate = dataPageviews[dataPageviews.length - 2].date;
        configPageviews.data.regions['value'] = [{'start': startDate, 'style': 'dashed'}];
    }

    var pageviewChart = c3.generate(configPageviews);

    var configTopDownloads = {
        bindto: "#chart-data-top-downloads",
        padding: {
            bottom: 20
        },
        color: '#0077ce',
        data: {
            json: dataTopDownloads,
            keys: {
                x: 'name',
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
        }
    };
    var topDownloadsChart = c3.generate(configTopDownloads);


    d3.selectAll('#chart-data-top-downloads .c3-axis-x .tick text')
        .each(function(d,i){
            // augment tick contents with link
            var self = d3.select(this);
            var text = self.text();
            var url;
            var item = $.grep(dataTopDownloads, function(el, idx) {
               return (el['name'] === text);
            });
            if (item.length !== 1) {
                logger.error('Two datasets with same name!');
            }
            self.html("<a xlink:href='"+ item[0]['url'] +"' target='_blank' style='fill: #0077ce;'>Dataset: "+text+"</a>");
        });
});