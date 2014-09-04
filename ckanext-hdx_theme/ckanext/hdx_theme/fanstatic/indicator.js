ckan.module('hdx-indicator-graph', function ($, _) {
  return {
    initialize: function(){
      var CHART_COLORS = ['1ebfb3', '117be1', 'f2645a', '555555', 'ffd700'];
      var c3_chart, chart_config, data, elementId, alldata;
      //alldata = initialData.results;
      alldata = this._retrieveData();

      elementId = '#' + $(this.el).attr('id');

      //Let's select 10 data points that have different values
      data = [];
      for (var alldataEl in alldata){
        if (data.length > 9)
          break;
        var found = false;
        for (var dataEl in data){
          if (data[dataEl].value === alldata[alldataEl].value){
            found = true;
            break;
          }
        }
        if (!found || (alldata.length - alldataEl + data.length < 10)){
          alldata[alldataEl]['trimName'] = alldata[alldataEl]['locationName'];
          if (alldata[alldataEl]['trimName'].length > 20)
            alldata[alldataEl]['trimName'] = alldata[alldataEl]['trimName'].substring(0, 18) + '...';

          data.push(alldata[alldataEl]);
        }
      }

      chart_config = {
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
            value: 'Indicator Name '
          },
          type: 'bar'
        },
        axis: {
          x: {
            type: 'category'
          },
          y: {
            label: {
              text: this.options.label,
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

    },
    options: {
    	label: "",
      code: ""
    },
    _retrieveData: function (){

    }
  }
});