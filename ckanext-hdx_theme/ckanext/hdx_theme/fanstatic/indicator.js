ckan.module('hdx-indicator-graph', function ($, _) {
  return {
    initialize: function(){
      var data = [], indicatorCode;
      indicatorCode = indicatorMapping[this.options.name];

      var CHART_COLORS = ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700'];
      var elementId = '#' + $(this.el).attr('id');

      var chart_config = {
        bindto: elementId,
        padding: {
          top: 40
        },
        color: {
          pattern: CHART_COLORS
        },
        data: {
          json: data,
          keys: {
            x: 'trimName',
            value: ['value']
          },
          names: {
            value: this.options.label
          },
          type: 'bar'
        },
        axis: {
          x: {
            type: 'category'
          },
          y: {
            label: {
              text: "Units",
              position: 'outer-middle'
            },
            tick: {
              format: d3.format(',')
            }
          }
        },
        tooltip: {
          format: {
            title: function (d) {
              return data[d]['locationName'];
            }
          }
        },
        grid: {
          y: {
            show: true
          }
        }
      };
      var c3_chart = c3.generate(chart_config);
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + "&periodType=latest_year",
        success: function(json) {
          if (json.success)
            data = json.result.results;
        },
        async:false
      });

      if (data.length > 0)
        this.buildChart(data, c3_chart);
      else
        c3_chart.hide();
    },
    buildChart: function(alldata, c3_chart) {
      var CHART_COLORS = ['1ebfb3', '117be1', 'f2645a', '555555', 'ffd700'];
      var c3_chart, chart_config, data, elementId, alldata;
      elementId = '#' + $(this.el).attr('id');

      //sort data points based on value
      alldata.sort(function (a,b){
        return a.value - b.value;
      });

      data = [];
      //calculate a step so that we can have ~10 points in our graph
      var step = Math.floor(alldata.length / 10);
      if (step === 1)
        step = 2;

      var i;
      for (i = 0; i < alldata.length; i+= step){
        data.push(alldata[i]);
      }
      //include the last value if it hasn't been included already
      if (i - step < alldata.length-1)
        data.push(alldata[alldata.length-1]);


      //Let's select 10 data points that have different values
//      data = [];
//      for (var alldataEl in alldata){
//        if (data.length > 9)
//          break;
//        var found = false;
//        for (var dataEl in data){
//          if (data[dataEl].value === alldata[alldataEl].value){
//            found = true;
//            break;
//          }
//        }
//        if (!found || (alldata.length - alldataEl + data.length < 10)){
//          alldata[alldataEl]['trimName'] = alldata[alldataEl]['locationName'];
//          if (alldata[alldataEl]['trimName'].length > 20)
//            alldata[alldataEl]['trimName'] = alldata[alldataEl]['trimName'].substring(0, 18) + '...';
//
//          data.push(alldata[alldataEl]);
//        }
//      }

      //trim names
      for (var dataEl in data){
        data[dataEl]['trimName'] = data[dataEl]['locationName'];
        if (data[dataEl]['trimName'].length > 15)
          data[dataEl]['trimName'] = data[dataEl]['trimName'].substring(0, 15) + '...';
      }


      c3_chart.load({
        json: data,
        keys: {
          x: 'trimName',
          value: ['value']
        },
        names: {
          value: this.options.label
        },
        type: 'bar'
      });

//
//      chart_config = {
//        bindto: elementId,
//        padding: {
//          top: 40
//        },
//        color: {
//          pattern: CHART_COLORS
//        },
//        data: {
//          json: data,
//          keys: {
//            x: 'trimName',
//            value: ['value']
//          },
//          names: {
//            value: this.options.label
//          },
//          type: 'bar'
//        },
//        axis: {
//          x: {
//            type: 'category'
//          },
//          y: {
//            label: {
//              text: "Units",
//              position: 'outer-middle'
//            },
//            tick: {
//              format: d3.format(',')
//            }
//          }
//        },
//        tooltip: {
//          format: {
//            title: function (d) {
//              return data[d]['locationName'];
//            }
//          }
//        },
//        grid: {
//          y: {
//            show: true
//          }
//        }
//      };
//      c3_chart = c3.generate(chart_config);
    },
    options: {
    	label: "",
      name: ""
    }
  }
});