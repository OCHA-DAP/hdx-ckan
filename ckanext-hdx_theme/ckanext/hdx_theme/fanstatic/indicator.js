ckan.module('hdx-indicator-graph', function ($, _) {
  return {
    initialize: function(){
      this.el.context.ckanModule	= this;
      if (!this.options.click_only)
        this._init();
      else
        $(this.el).click(this._onClick);
    },
    _onClick: function(){
      var container = this.ckanModule.options.container;
//      $("#"+container).slideUp(500, function (){
//        var parent = $(this).parents(this.ckanModule.options.parent_selector);
//        $("#"+container).remove();
//        parent.append('<div id="' + container + '" style="max-height: 320px; position: relative;">');
//        this.ckanModule._init();
//      });
//      $("#"+container).dequeue();
      $("#"+container).slideUp(100);
      $("#"+container).dequeue();
      var parent = $(this).parents(this.ckanModule.options.parent_selector);
      $("#"+container).remove();
      parent.append('<div id="' + container + '" style="max-height: 320px; position: relative;">');
      this.ckanModule._init();
    },
    _init: function(){
      var data = [], indicatorCode;
      indicatorCode = indicatorMapping[this.options.name];

      var CHART_COLORS = ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700'];

      var elementId = '#' + $(this.el).attr('id');
      if (this.options.click_only)
        elementId = '#' + this.options.container;

      var zoomEventNoRedraw = function(w, domain){
        var dif = w[1] - w[0]; //number of data points shown

        var MAGIC = 30; //magic number under which the country names can be displayed
        if (dif < MAGIC){
          c3_chart.internal.config.axis_x_tick_culling = false;
        } else {
          c3_chart.internal.config.axis_x_tick_culling_max =  Math.floor(data.length*MAGIC/dif);
          c3_chart.internal.config.axis_x_tick_culling = true;
        }
      };
      var zoomEvent = function (w, domain){
        zoomEventNoRedraw(w, domain);
        c3_chart.internal.redrawForBrush();
      };

      var chart_config = {
        bindto: elementId,
        padding: {
          bottom: 20
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
          show: this.options.subchart,
          onbrush: zoomEventNoRedraw
        },
        zoom: {
          enabled: this.options.zoom,
          onzoom: zoomEvent
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
              format: d3.format('s')
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
      c3_chart.internal.margin2.top=260;
      var continuousLocation = this.options.continuous_location;
      var setZoomFunc = this._setZoom;
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + "&periodType=latest_year",
        success: function(json) {
          if (json.success){
            data = json.result.results;
            if (continuousLocation != ""){
              $("#"+continuousLocation+" .cb-item-count").html(data.length);
              var locationList = $("#" + continuousLocation + " .cb-item-links ul");

              if (data.length > 0)
                locationList.html("");

              for (var i = 0; i <= 4; i++){
                var name = data[i]['locationName'].substring(0, 18).toLowerCase();
                name = name.charAt(0).toUpperCase() + name.slice(1);
                locationList.append('<li><a href="/group/'+data[i]['locationCode'].toLowerCase()+'" title="'+data[i]['locationName']+'">'+ name +'</a></li>');
              }
              if (data.length > 4)
                locationList.append('<li><a style="cursor: pointer;" onclick="$(this).parent().siblings().show();$(this).hide(); $(this).parents(\'.cb-border-wrapper\').animate({scrollTop: 160}, \'slow\'); ">More</a></li>');
              for (var i = 5; i < data.length; i++){
                var name = data[i]['locationName'].substring(0, 18).toLowerCase();
                name = name.charAt(0).toUpperCase() + name.slice(1);
                locationList.append('<li style="display: none"><a href="/group/'+data[i]['locationCode'].toLowerCase()+'" title="'+data[i]['locationName']+'">'+ name +'</a></li>');
              }
            }
          }
        },
        complete: function(){
          $('body').delay(500).queue(function(){
            c3_chart.internal.brush.extent([0,20]).update();
            c3_chart.internal.redrawForBrush();
            c3_chart.internal.redrawSubchart();
            $(this).dequeue();
            $(elementId).attr("style", "max-height: 310px; position: relative;");
          });
        },
        async:false
      });

      if (data.length > 0)
        data = this.buildChart(data, c3_chart);
      else
        c3_chart.hide();
    },
    _setZoom: function(){
      c3_chart.internal.brush.extent([0,20]).update();
      c3_chart.internal.redrawForBrush();
      c3_chart.internal.redrawSubchart();
    },
    buildChart: function(alldata, c3_chart) {
      var data, elementId;

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
      zoom: false,
      continuous_location: "",
      click_only: false,
      container: "",
      parent_selector: ""
    }
  }
});