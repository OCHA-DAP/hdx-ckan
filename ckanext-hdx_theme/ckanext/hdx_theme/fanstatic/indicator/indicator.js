$(document).ready(function() {
  $("#showOptions").on("click", function (){
    const showOptionsText = 'Select locations';
    const hideOptionsText = 'Hide select locations';
    if ($(this).text() == showOptionsText)
      $(this).text(hideOptionsText);
    else
      $(this).text(showOptionsText);

    $('#optionsContent').toggleClass('hidden');
    $('#graphContent').toggleClass('col-xs-12 col-xs-9');

    return false;
  });

  $("#optionDropDown").find("li > a").on("click", function (){
    var value = $(this).attr("val");
    var container = $("#" + value);
    container.parent().find("ul").hide();
    container.show();
    $("#location-dd").find("span").text($(this).text());
  });
  
  setUpGalleryTracking();

  //setup download chart
    (function setupDownloads(){
        var chartData = JSON.parse($("#dataset-downloads-data").html());
        var monthsSet = {};
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
            bindto: "#dataset-downloads-chart",
            padding: {
                bottom: 0
            },
            size: {
                height: 120
            },
            color: '#117be1',
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

    if (chartData.length > 2){
        var startDate = chartData[chartData.length - 2].date;
        chartConfig.data.regions['value'] = [{'start': startDate, 'style': 'dashed'}];
    }

    var chart = c3.generate(chartConfig);
  })();
});
