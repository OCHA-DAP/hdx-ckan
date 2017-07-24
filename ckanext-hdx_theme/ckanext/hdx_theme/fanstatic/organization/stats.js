$(document).ready(function(){
    const LABEL_MAX_LENGTH = 40;
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
        el['trimName'] = trimName;
    });

    var substituteDatasetNamesWithLinks = function () {
        console.log("Substituting");
        d3.selectAll('#chart-data-top-downloads .c3-axis-x .tick text')
            .each(function(d,i){
                // augment tick contents with link
                var self = d3.select(this);
                var text = self.text();
                var url;
                var item = $.grep(dataTopDownloads, function(el, idx) {
                   return (el['trimName'] === text);
                });
                if (item.length !== 1) {
                    console.error('Two datasets with same name!');
                }
                self.html("<a xlink:href='"+ item[0]['url'] +"' target='_blank' style='fill: #0077ce;'>"+ text +"</a>");
            });
    }.bind(this);

    var configTopDownloads = {
        bindto: "#chart-data-top-downloads",
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
                x: 'trimName',
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
        setupDatasetDownloads("#stats-data-single-dataset-downloads", "#chart-data-top-downloads", {
            size: {
                height: 320
            }
        });
    } else {
        var topDownloadsChart = c3.generate(configTopDownloads);
        substituteDatasetNamesWithLinks();
    }

});