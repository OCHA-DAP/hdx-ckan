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
                value: ['value']
            },
            type: 'line',
            regions: {
                'value': null
            },
            names: {
                'value': 'Downloads and Page Views'
            }
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d'
                }
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
                x: 'dataset_id',
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
            self.html("<a xlink:href='http://google.ro' target='_blank' style='fill: #0077ce;'>Dataset: "+text+"</a>");
        });
});