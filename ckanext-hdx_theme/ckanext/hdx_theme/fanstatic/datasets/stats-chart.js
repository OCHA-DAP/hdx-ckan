function setupDatasetDownloads(dataDivId, placeholderDivId, extraConfigs){
        /**
         *
         * @param list {[number]}
         * @returns {boolean}
         */
        var sortedListHasDuplicatesWhenRoundUp = function (list) {
          var hasDuplicates = false;
          if (list && list.length > 1) {
            hasDuplicates = list
              .map(function(item) {
                return Math.ceil(item);
              })
              .some(function (item, idx, all) {
                if (idx >= 1 && item === all[idx-1]) {
                  return true;
                }
            });
          }
          return hasDuplicates;
        };
        var chartData = JSON.parse($(dataDivId).html());
        var monthsSet = {};
        if (!extraConfigs)
            extraConfigs = {};
        var maxDownloads = 0;
        $.each(chartData, function(idx, data){
            var date = new Date(data.date), y = date.getFullYear(), m = date.getMonth();
            var firstDay = new Date(y, m, 1);
            var format = d3.time.format("%Y-%m-%d");
            var firstDayStr = format(firstDay);
            monthsSet[firstDayStr] = true;
            if (data.value > maxDownloads){
                maxDownloads = data.value;
            }
        });
        var roundMaxDownloads = maxDownloads;
        var multiplier = 1;
        while (roundMaxDownloads > 1){
            roundMaxDownloads /= 10;
            multiplier *= 10;
        }
        roundMaxDownloads = roundMaxDownloads*10; multiplier /= 10;
        roundMaxDownloads = Math.ceil(roundMaxDownloads);
        roundMaxDownloads *= multiplier;

        var tickValues = [roundMaxDownloads/4, roundMaxDownloads/2, 3*roundMaxDownloads/4, roundMaxDownloads];
        console.log(tickValues);
        var months = $.map(monthsSet, function(val, key) { return key; });
        months = months.slice(1);

        var gridLines = [];
        $.each(tickValues, function(idx, data){
            gridLines.push({value: data});
        });

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
                },
                y: {
                    min: 0,
                    tick: {
                        count: tickValues.length,
                        format: sortedListHasDuplicatesWhenRoundUp(tickValues) ? null : d3.format('.0f'),
                        values: tickValues
                    }
                }
            },
            legend: {
                show: false
            },
            grid: {
                y: {
                    lines: gridLines
                }
            },
            tooltip: {
                format: {
                    title: d3.time.format('%Y-%m-%d')
                }
            }
        };
        $.extend(true, chartConfig, extraConfigs);

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
        var chartData = JSON.parse($(datasetDwdId).html());
        if (chartData.length > 0){
            setupDatasetDownloads(datasetDwdId, "#dataset-downloads-chart");
        } else {
            $("#dataset-downloads-chart-no-data").show();
        }
    }
});
