function setupDatasetDownloads(dataDivId, placeholderDivId, extraConfigs){
        var chartData = JSON.parse($(dataDivId).html());
        var monthsSet = {};
        if (!extraConfigs)
            extraConfigs = {};
        $.each(chartData, function(idx, data){
            var date = new Date(data.date), y = date.getFullYear(), m = date.getMonth();
            var firstDay = new Date(y, m, 1);
            var format = d3.time.format("%Y-%m-%d");
            var firstDayStr = format(firstDay);
            monthsSet[firstDayStr] = true;
        });
        var months = $.map(monthsSet, function(val, key) { return key; });
        months = months.slice(1);

        var chartConfig = {
            bindto: placeholderDivId,
            padding: {
                bottom: 0
            },
            size: {
                height: 120
            },
            color: '#0077ce',
            data: {
                json: chartData,
                keys: {
                    x: 'date',
                    value: ['value']
                },
                type: 'line',
                regions: {
                    'value': null
                },
                names: {
                    'value': 'Downloads'
                }

            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        format: '%b',
                        values: months
                    }
                }
            },
            legend: {
                show: false
            },
            grid: {
                y: {
                    show: true
                }
            },
            tooltip: {
                format: {
                    title: d3.time.format('%Y-%m-%d')
                }
            }
        };
        $.extend(chartConfig, extraConfigs);

        if (chartData.length > 2){
            var startDate = chartData[chartData.length - 2].date;
            chartConfig.data.regions['value'] = [{'start': startDate, 'style': 'dashed'}];
        }

        var chart = c3.generate(chartConfig);
    }
$(document).ready(function(){
    //setup download chart

    var datasetDwdId = "#dataset-downloads-data";
    var datasetDwdDiv = $(datasetDwdId);
    if (datasetDwdDiv.length > 0){
        setupDatasetDownloads(datasetDwdId, "#dataset-downloads-chart");
    }
});