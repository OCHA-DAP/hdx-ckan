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
        subchart: {
          show: this.options.subchart
        },
        padding:{
          bottom: 20
        },
        zoom: {
          enabled: this.options.zoom
        },
        legend:{
          show: false
        },
        axis: {
          x: {
            type: 'category',
            tick: {
              rotate: 20
            }
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
      c3_chart = c3.generate(chart_config);
      c3_chart.internal.margin2.top=260;
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + "&periodType=latest_year",
        success: function(json) {
          if (json.success)
            data = json.result.results;
        },
        complete: function(){
          $('body').delay(500).queue(function(){
            c3_chart.internal.brush.extent([0,20]).update();
            c3_chart.internal.redrawForBrush();
            c3_chart.internal.redrawSubchart();
          });
        },
        async:false
      });

      if (data.length > 0)
        data = this.buildChart(data, c3_chart);
      else
        c3_chart.hide();
    },
    buildChart: function(alldata, c3_chart) {
      var data, elementId;

      //sort data points based on value
//      alldsata.sort(function (a,b){
//        return a.value - b.value;
//      });

//      data = [];
//      //calculate a step so that we can have ~10 points in our graph
//      var step = Math.floor(alldata.length / 10);
//      if (step === 1)
//        step = 2;
//
//      var i;
//      for (i = 0; i < alldata.length; i+= step){
//        data.push(alldata[i]);
//      }
//      //include the last value if it hasn't been included already
//      if (i - step < alldata.length-1)
//        data.push(alldata[alldata.length-1]);
      data = alldata;
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
        }
      });
      return data;
    },
    options: {
    	label: "",
      name: "",
      subchart: false,
      zoom: false
    }
  }
});