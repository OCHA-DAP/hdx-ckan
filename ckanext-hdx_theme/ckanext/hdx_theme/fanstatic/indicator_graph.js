ckan.module('hdx-indicator-graph', function ($, _) {
  return {
    initialize: function(){
      //CKAN Module init function

      this.el.context.ckanModule = this;
      /**
       * Two ways of init:
       * 1. Regular - Graph spawns straight away in the current element
       * 2. Click Only - Graph spanws in the options.container when the user clicks on the current element
       */
      if (!this.options.click_only)
        this._init();
      else
        $(this.el).click(this._onClick);
    },
    c3_chart: null,
    data: [],
    dataCallbacks: [],
    elementId: null,
    _onClick: function(){
      /**
       * Click Only callback
       */
      var container = this.ckanModule.options.container;
      const cont = $("#" + container);
      cont.slideUp(100);
      cont.dequeue();
      var parent = $(this).parents(this.ckanModule.options.parent_selector);
      cont.remove();
      parent.append('<div id="' + container + '" style="max-height: 320px; position: relative;">');
      this.ckanModule._init();
    },
    _init: function(){
      /**
       * Regular init - spawns a new graph in the container
       */
      var indicatorCode, sourceCode;
      indicatorCode = indicatorCodeMapping[this.options.name];
      sourceCode = indicatorSourceMapping[this.options.name];
      //get container id
      this.elementId = '#' + $(this.el).attr('id');
      if (this.options.click_only)
        this.elementId = '#' + this.options.container;
      var elementId = this.elementId;

      //init chart with no data yet
      var chart_config = this._build_chart_config(elementId, this);
      this.c3_chart = c3.generate(chart_config);
      var c3_chart = this.c3_chart;
      c3_chart.internal.margin2.top=260;

      /**
       * Callbacks
       */
      //setup side_panel onclick function to resize the chart
      this._setupSidePanelCallback();
      //Continuous location callback;
      if (this.options.continuous_location != "")
        this.dataCallbacks.push($.proxy(this._callback_location, this));

      //prepare source aux for url
      var urlSourceAux = "";
      if (sourceCode != "")
        urlSourceAux = "&s="+sourceCode;
      //get the data synchronously from the server
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + urlSourceAux + "&periodType=LATEST_YEAR_BY_COUNTRY&sorting=VALUE_DESC",
        success: $.proxy(this._data_ajax_success, this),
        complete: $.proxy(this._data_ajax_complete, this),
        async:false
      });
      //build the chart
      if (this.data.length > 0)
        this.data = this.buildChart(this.data, c3_chart);
      else
        c3_chart.hide();
    },
    //Callback for data load success - we update the data field and run all the callbacks
    _data_ajax_success: function(json) {
      if (json.success){
        this.data = json.result.results;
        var data = this.data;
        //Call all callbacks that new data was loaded
        for (var i = 0; i < this.dataCallbacks.length; i++){
          this.dataCallbacks[i]();
        }
      }
    },
    //Callback for data load complete - we set the initial viewport for the graph
    _data_ajax_complete: function(){
      var c3_chart = this.c3_chart;
      $('body').delay(500).queue(function(){
        c3_chart.internal.brush.extent([0,20]).update();
        c3_chart.internal.redrawForBrush();
        c3_chart.internal.redrawSubchart();
        $(this).dequeue();
        $(this.elementId).attr("style", "max-height: 310px; position: relative;");
      });
    },
    //Callback to setup the continuous location widget
    _callback_location: function (){
      var continuousLocation = this.options.continuous_location;
      var data = this.data;
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
          locationList.append('<li><a style="cursor: pointer;" onclick="$(this).parent().siblings().show();$(this).hide(); $(this).parents(\'.cb-border-wrapper\').attr(\'style\', \'overflow-y: scroll;\'); $(this).parents(\'.cb-border-wrapper\').animate({scrollTop: 160}, \'slow\'); ">More</a></li>');
        for (var i = 5; i < data.length; i++){
          var name = data[i]['locationName'].substring(0, 18).toLowerCase();
          name = name.charAt(0).toUpperCase() + name.slice(1);
          locationList.append('<li style="display: none"><a href="/group/'+data[i]['locationCode'].toLowerCase()+'" title="'+data[i]['locationName']+'">'+ name +'</a></li>');
        }
      }
    },
    //Callback for the sidepanel show/hide trigger - resizes the chart
    _setupSidePanelCallback: function (){
      if (this.options.side_panel != ""){
        var showPanel = $("#"+this.options.side_panel);
        showPanel.bind("click", $.proxy(function (){
          var c3_chart = this.c3_chart;
          c3_chart.resize();
          c3_chart.internal.redrawForBrush();
          c3_chart.internal.redrawSubchart();
        }, this));
      }
    },
    //Callback for the zoom event, but trigger no redraw
    _zoomEventNoRedraw: function(w, domain){
      var dif = w[1] - w[0]; //number of data points shown

      var MAGIC = 30; //magic number under which the country names can be displayed
      var c3_chart = this.c3_chart;
      if (dif < MAGIC){
        c3_chart.internal.config.axis_x_tick_culling = false;
      } else {
        c3_chart.internal.config.axis_x_tick_culling_max =  Math.floor(this.data.length*MAGIC/dif);
        c3_chart.internal.config.axis_x_tick_culling = true;
      }
    },
    //Callback for the zoom event with additional redraw
    _zoomEvent: function (w, domain){
      this._zoomEventNoRedraw(w, domain);
      this.c3_chart.internal.redrawForBrush();
    },
    //Setup the chart config
    _build_chart_config: function (elementId, data, scope){
      return {
        bindto: elementId,
        padding: {
          bottom: 20
        },
        color: {
          pattern: ['#1ebfb3', '#117be1', '#f2645a', '#555555', '#ffd700']
        },
        data: {
          json: this.data,
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
          onbrush: $.proxy(this._zoomEventNoRedraw, this)
        },
        zoom: {
          enabled: this.options.zoom,
          onzoom: $.proxy(this._zoomEvent, this)
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
            title: $.proxy(function (d) {
              return this.data[d]['locationName'];
            }, this),
            value: $.proxy(function (value, ratio, id, idx){
              var format = d3.format('s');
              var year = this.data[idx]['time'].substring(0,4);
              return format(value) + " (" + year + ")";
            }, this)
          }
        },
        grid: {
          y: {
            show: true
          }
        }
      };
    },
    //Builds the chart when the data is available
    buildChart: function () {
      var data;
      data = this.data;
      //trim names
      for (var dataEl in data){
        data[dataEl]['trimName'] = data[dataEl]['locationName'];
        if (data[dataEl]['trimName'].length > 15)
          data[dataEl]['trimName'] = data[dataEl]['trimName'].substring(0, 15) + '...';
      }

      this.c3_chart.load({
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
    //default module options
    options: {
    	label: "",
      name: "",
      subchart: false,
      zoom: false,
      continuous_location: "",
      click_only: false,
      container: "",
      parent_selector: "",
      side_panel: ""
    }
  }
});