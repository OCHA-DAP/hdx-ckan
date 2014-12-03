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
      else{
        $(this.el).click(this._onClickPreview);
        if (this.options.click_only_show)
          $(this.el).click();
      }
    },
    c3_chart: null,
    filteredLocations: null,
    graphData: [],
    data: [],
    dataCallbacks: [],
    elementId: null,
    view_port_reset: true,
    view_port_start:0,
    view_port_stop: 19,
    _last_datapoints_div: null,
    _sort_order_values:{
      VALUE_DESC: "Value descending",
      VALUE_ASC: "Value ascending",
      COUNTRY_ASC: "Alphabet A-Z",
      COUNTRY_DESC: "Alphabet Z-A"
    },
    _sort_order: "VALUE_DESC",
    _period_type: "LATEST_YEAR_BY_COUNTRY",
    _period_type_default: "LATEST_YEAR_BY_COUNTRY",
    _continuous_location_initialize: true,
    _chart_initialized: false,
    _onClickPreview: function(){
      /**
       * Reset Module state
       */
      this.ckanModule._chart_initialized = false;

      /**
       * Click Only callback
       */
      var container = this.ckanModule.options.container;
      var cont = $("#" + container);
      if (cont.length > 0){
        $(cont.context.previewLink).trigger("click", $.proxy(this.ckanModule._onClickPreviewGenerate, this));
      }
      else{
        $.proxy(this.ckanModule._onClickPreviewGenerate, this)();
      }
    },
    _onClickPreviewGenerate: function (){
      var container = this.ckanModule.options.container;
      var parent = $(this).parents(this.ckanModule.options.parent_selector);
      parent.append('<div id="' + container + '" style="max-height: 320px; position: relative;">');
      var cont = $("#" + container);
      cont.context.previewLink = this;
      this.ckanModule._init();
      $(this).text("Hide preview");
      $(this).unbind("click");

      $(this).click(this.ckanModule._onClickHidePreview);
    },
    _onClickHidePreview: function (context, callback){
      $(this).text("Preview");
      $(this).unbind("click");
      $(this).click(this.ckanModule._onClickPreview);

      var container = $("#"+this.ckanModule.options.container);
      container.slideUp(300, function (){
        container.remove();
        if (callback){
          callback();
        }
      });
    },
    _init: function(){
      /**
       * Regular init - spawns a new graph in the container
       */
      //get container id
      this.elementId = '#' + $(this.el).attr('id');
      if (this.options.click_only)
        this.elementId = '#' + this.options.container;
      var elementId = this.elementId;

      //Loading icon + text
      $(this.elementId).append('<div style="height: 310px; text-align: center; padding-top: 140px;"><img src="/base/images/loading-spinner.gif" />Loading sample data from this indicator . . . </div>');

      //init year filter dropdown
      this._init_year_filter_dropdown();

      /**
       * Priority Callbacks - that need to setup data for the rest
       */
      this.dataCallbacks.push($.proxy(this._callback_trim_names, this)); //Trim the names
      this.dataCallbacks.push($.proxy(this._callback_process_data, this)); //Process the data for the graph

      /**
       * Regular Callbacks
       */
      //setup side_panel onclick function to resize the chart
      if (this.options.side_panel != "") {
        this._sidePanelResizeCallback();
        this.dataCallbacks.push($.proxy(this._callback_sidepanel, this));
      }
      //Continuous location callback;
      if (this.options.continuous_location != "")
        this.dataCallbacks.push($.proxy(this._callback_location, this));

      this._internal_load_data_build_graph();
    },
    _init_year_filter_dropdown: function (){
      if (this.options.side_panel != "") {

        var indicatorCode, sourceCode;
        indicatorCode = indicatorCodeMapping[this.options.name];
        sourceCode = indicatorSourceMapping[this.options.name];
        //prepare source aux for url
        var urlSourceAux = "";
        if (sourceCode != "")
          urlSourceAux = "&s="+sourceCode;

        jQuery.ajax({
          url: "/api/action/hdx_get_indicator_available_periods?it=" + indicatorCode + urlSourceAux,
          success: $.proxy(this._init_year_filter_dropdown_items, this)
        });
//          this._init_year_filter_dropdown_items();
      }
    },
    _init_year_filter_dropdown_items: function (json){
      var container = $("#"+this.options.side_panel_years);
      if (json.success){
        var data = json.result.results;

        for (var i = 0; i < 10 && i < data.length; i++){
          var item = data[i];
          container.append("<option value='" + item + "'>" + item + "</option>");
        }
        container.append("<option disabled value='disabled'>Download the data below for more dates</option>");
      }
      container.data("ckanModule", this);
      container.on("change", function(){
        var year = $(this).select2().val();
        var module = $(this).data("ckanModule");

        module._period_type = year;
        module._internal_load_data_build_graph();
      })
    },
    _internal_load_data_build_graph: function (){
      var indicatorCode, sourceCode;
      indicatorCode = indicatorCodeMapping[this.options.name];
      sourceCode = indicatorSourceMapping[this.options.name];


      if (this._chart_initialized) {
        $(this.elementId).parent().append('<div id="' + this.elementId.slice(1) + "Loading" + '" style="position: absolute; top: 50px;"><img src="/base/images/loading-spinner.gif" /></div>');
      }

      //
      var periodTypeAux = "&periodType=" + this._period_type;
      if (this._period_type != this._period_type_default)
        periodTypeAux = "&minTime="+ this._period_type +"&maxTime=" + this._period_type + 
        			"&periodType=" + this._period_type_default;

      //prepare source aux for url
      var urlSourceAux = "";
      if (sourceCode != "")
        urlSourceAux = "&s="+sourceCode;
      //get the data synchronously from the server
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + urlSourceAux + periodTypeAux + "&sorting="+this._sort_order,
        success: $.proxy(this._data_ajax_success, this)
//        complete: $.proxy(this._data_ajax_complete, this),
//        async:false
      });
    },
    //Filter the newly loaded data to show just the selected locations
    _callback_process_data: function(){
      //Check if the filtered Locations were not initialized before
      if (this.filteredLocations === null){
        this.filteredLocations = {"*ALL*": true};
        for (var i = 0; i < this.data.length; i++){
          this.filteredLocations[this.data[i]['locationCode']] = true;
        }
      }
      this.graphData = [];
      for (var i = 0; i < this.data.length; i++){
        if (this.filteredLocations[this.data[i]['locationCode']])
          this.graphData.push(this.data[i]);
      }
    },
    //Callback for data load success - we update the data field and run all the callbacks
    _data_ajax_success: function(json) {

      if (!this._chart_initialized){
        //init chart with no data yet
        var chart_config = this._build_chart_config(this.elementId, this);
        this.c3_chart = c3.generate(chart_config);
        var c3_chart = this.c3_chart;
        c3_chart.internal.margin2.top=260;
      }

      if (json.success){
        this.data = json.result.results;

        //#1595 - fix not active until datateam will clean the data
//        var unitName = this.data[0].unitName;
//        if (unitName){
//          this.c3_chart.axis.labels({y: unitName});
//        }
        //Call all callbacks that new data was loaded
        for (var i = 0; i < this.dataCallbacks.length; i++){
          this.dataCallbacks[i]();
        }
      }
      //build the chart
      if (this.data.length > 0)
        this.buildChart();
      else
        this.c3_chart.hide();

      if (!this._chart_initialized){
        $(this.elementId).find("svg > g:eq(1) rect[class='background']").attr("style", "cursor: crosshair;");
        this._set_view_port_bar_color();

        $(this.elementId).find('g.resize rect').each(function (){
          $(this).attr("x", "-10");
          $(this).attr("y", "20");
          $(this).attr("rx", "3");
          $(this).attr("ry", "3");
          $(this).attr("width", "20");
          $(this).attr("height", "20");
          $(this).attr("style", "fill: #ffffff; stroke: #cccccc;");
        });

        $(this.elementId).find('g.resize').each(function (){
          var rect = d3.select(this).append("rect");
          rect.attr("x", "-4").attr("width", "1").attr("height", "10").attr("y", "25").attr("style", "fill: #888888;");
          rect = d3.select(this).append("rect");
          rect.attr("x", "0").attr("width", "1").attr("height", "10").attr("y", "25").attr("style", "fill: #888888;");
          rect = d3.select(this).append("rect");
          rect.attr("x", "4").attr("width", "1").attr("height", "10").attr("y", "25").attr("style", "fill: #888888;");
        });

        this._chart_initialized = true;
      }

    },
    //Callback for data load complete - we reset the initial viewport for the graph
    _set_view_port_size: function(){
      var c3_chart = this.c3_chart;
      var graphData = this.graphData;
      var end = graphData.length > 20 || graphData.length == 0 ? 20 : graphData.length;
      c3_chart.internal.brush.extent([0,end]).update();
      c3_chart.internal.redrawForBrush();
      c3_chart.internal.redrawSubchart();
      $(this.elementId).attr("style", "max-height: 310px; position: relative;");
      this._zoomEventNoRedraw([0,end]);
    },
    _callback_trim_names: function () {
      var data = this.data;
      //trim names
      for (var dataEl in data){
        data[dataEl]['trimName'] = data[dataEl]['locationName'];
        if (data[dataEl]['trimName'].length > 15)
          data[dataEl]['trimName'] = data[dataEl]['trimName'].substring(0, 15) + '...';
      }
      //build the chart
      if (this.data.length > 0)
        this.buildChart();
      else
        this.c3_chart.hide();

      $(this.elementId+"Loading").remove();
    },
    //Callback for the setup of the side panel locations
    _callback_sidepanel: function (){
      var data = this.data.slice(0); //make copy of array
      data.sort(function(a, b){return a['locationName'].localeCompare(b['locationName'])});
      data.unshift({'locationName': "Countries", 'locationCode': "*ALL*"});
      var locationContainer = $("#"+this.options.side_panel_locations);
      locationContainer.children().remove();
      for (var i = 0; i < data.length; i++){
        var name = data[i]['locationName'];
        var code = data[i]['locationCode'];
        var id = "sidePanelLocation" + i;
        var checked = "";
        var fullname = name;
        if (name.length > 28){
          name = name.substring(0, 25) + "...";
        }
        if (this.filteredLocations[code])
          checked = "checked";
        locationContainer.append("<li><input id='" + id + "' value='" + code + "' class='locationCheckbox' " + checked + " type='checkbox' /><label for='" + id + "' title='" + fullname + "'>" + name + "</label></li>");
        var element = $("#"+id);
        element.data("ckanModule", this);
      }
      locationContainer.find("li input").on("click", this._callback_location_click);

      var sortContainer = $("#"+this.options.side_panel_sortorder);
      sortContainer.children().remove();
      for (var si in this._sort_order_values){
        var styleExtra = "";
        if (si == this._sort_order)
          styleExtra = "style='font-weight: bold;'";
        var id = "sidePanelSort" + si;
        sortContainer.append("<li><a id='" + id + "' href='#' value='" + si + "' " + styleExtra + ">" + this._sort_order_values[si] + "</a>");
        var element = $("#"+id);
        element.data("ckanModule", this);
      }
      sortContainer.find("li a").on("click", this._callback_sortorder_click);

    },
    _callback_location_click: function (){
      var code = $(this).attr('value');
      var module = $(this).data("ckanModule");

      if (code === "*ALL*"){
        for (var icode in module.filteredLocations)
          module.filteredLocations[icode] = this.checked;
        $("#"+module.options.side_panel_locations + " li input").prop('checked', this.checked);
      }
      else
        module.filteredLocations[code] = this.checked;

      module._callback_process_data();//adjust the new data
      module.buildChart();
      module._set_view_port_bar_color();
    },
    _callback_sortorder_click: function(){
      var order = $(this).attr('value');
      var module = $(this).data("ckanModule");

      module._sort_order = order;
      module._internal_load_data_build_graph();
    },
    //Callback to setup the continuous location widget
    _callback_location: function (){
      var continuousLocation = this.options.continuous_location;
      var data = this.data;
      if (continuousLocation != "" && this._continuous_location_initialize){
        $("#"+continuousLocation+" .cb-item-count").html(data.length);
        var locationList = $("#" + continuousLocation + " .cb-item-links ul");
        locationList.children().remove();
        if (data.length > 0)
          locationList.html("");

        for (var i = 0; i <= 4 && i < data.length; i++){
          var name = data[i]['locationName'].substring(0, 18).toLowerCase();
          name = name.charAt(0).toUpperCase() + name.slice(1);
          locationList.append('<li><a href="/group/'+data[i]['locationCode'].toLowerCase()+'" title="'+data[i]['locationName']+'">'+ data[i]['trimName'] +'</a></li>');
        }
        if (data.length > 4)
          locationList.append('<li><a style="cursor: pointer;" onclick="$(this).parent().siblings().show();$(this).hide(); $(this).parents(\'.cb-border-wrapper\').attr(\'style\', \'overflow-y: scroll;\'); $(this).parents(\'.cb-border-wrapper\').animate({scrollTop: 160}, \'slow\'); ">More</a></li>');
        for (var i = 5; i < data.length; i++){
          var name = data[i]['locationName'].substring(0, 18).toLowerCase();
          name = name.charAt(0).toUpperCase() + name.slice(1);
          locationList.append('<li style="display: none"><a href="/group/'+data[i]['locationCode'].toLowerCase()+'" title="'+data[i]['locationName']+'">'+ data[i]['trimName'] +'</a></li>');
        }
        this._continuous_location_initialize = false;
      }
    },
    //Callback for the sidepanel show/hide trigger - resizes the chart
    _sidePanelResizeCallback: function (){
      var showPanel = $("#"+this.options.side_panel);
      showPanel.bind("click", $.proxy(function (){
        var c3_chart = this.c3_chart;
        c3_chart.resize();
        c3_chart.internal.redrawForBrush();
        c3_chart.internal.redrawSubchart();
      }, this));
    },
    //Color the bars in the subgraph for the current scope
    _set_view_port_bar_color: function (){
      $(this.elementId).find("svg > g:eq(1) g.c3-chart-bar.c3-target.c3-target-value path.c3-shape.c3-bar").attr("style", "stroke: none; fill: #cccccc; opacity: 1;");
      for (var i = this.view_port_start; i <= this.view_port_stop; i++){
        $(this.elementId).find("svg > g:eq(1) g.c3-chart-bar.c3-target.c3-target-value path.c3-shape.c3-bar-"+i).attr("style", "stroke: none; fill: #1ebfb3; opacity: 1;");
      }
    },
    //Callback for the zoom event, but trigger no redraw
    _zoomEventNoRedraw: function(w, domain){

      var dif = w[1] - w[0]; //number of data points shown
      var start = Math.round(w[0]), stop = Math.round(w[1] - 1);

      if (start != this.view_port_start || stop != this.view_port_stop) {
        this.view_port_start = start;
        this.view_port_stop = stop;

        this._set_view_port_bar_color();
      }
      if (this._last_datapoints_div != null && this._last_datapoints_div != dif && dif > 20){
        this.view_port_reset = false;
      }

      if (this._last_datapoints_div != dif){
        this._last_datapoints_div = dif;
      }

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
          json: this.graphData,
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
              format: this._abbrNum
            }
          }
        },
        tooltip: {
          format: {
            title: $.proxy(function (d) {
              return this.graphData[d]['locationName'];
            }, this),
            value: $.proxy(function (value, ratio, id, idx){
              var format = this._abbrNum;
              var year = this.graphData[idx]['time'].substring(0,4);
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
    _abbrNum: function (number) {
      //fixed decimal places
      var decPlacesNo = 2;
      // 2 decimal places => 100, 3 => 1000, etc
      var decPlaces = Math.pow(10,decPlacesNo);
      // Enumerate number abbreviations
      var abbrev = [ "k", "m", "b", "t" ];
      var sign = 1;
      if (number < 0){
        sign = -1;
      }
      number = number * sign;

      // Go through the array backwards, so we do the largest first
      for (var i=abbrev.length-1; i>=0; i--) {
        // Convert array index to "1000", "1000000", etc
        var size = Math.pow(10,(i+1)*3);
        // If the number is bigger or equal do the abbreviation
        if(size <= number) {
          // Here, we multiply by decPlaces, round, and then divide by decPlaces.
          // This gives us nice rounding to a particular decimal place.
          number = Math.round(number*decPlaces/size)/decPlaces;
          // Handle special case where we round up to the next abbreviation
          if((number == 1000) && (i < abbrev.length - 1)) {
            number = 1;
            i++;
          }
          number = number * sign;
          // Add the letter for the abbreviation
          number += abbrev[i];
          // We are done... stop
          return number;
        }
      }
      //if we got here we just need to set the decimal places
      number = number * sign;
      return parseFloat(Math.round(number * decPlaces) / decPlaces).toFixed(decPlacesNo);
    },
    //Builds the chart when the data is available
    buildChart: function () {
      var data;
      data = this.graphData;

      var subchart = $(this.elementId).find("svg > g:eq(1)");
      var prevSubchartShow = this.c3_chart.internal.config.subchart_show;

      if (this.graphData.length > 20){
        this.c3_chart.internal.config.subchart_show = this.options.subchart;
        subchart.attr("style", "");
      }
      else {
        this.c3_chart.internal.config.subchart_show = false;
        subchart.attr("style", "visibility: hidden !important;");
      }

      if (this.c3_chart.internal.config.subchart_show != prevSubchartShow){
        this.c3_chart.internal.updateAndRedraw();
        this.view_port_reset = true;
      }

      if (this.view_port_reset){
        this._set_view_port_size();
      }
      if (data.length > 0){
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

      }
      else{
        this.c3_chart.unload();
        this.view_port_reset = true;
      }
    },
    //default module options
    options: {
    	label: "",
      name: "",
      subchart: false,
      zoom: false,
      continuous_location: "",
      click_only: false,
      click_only_show: false,
      container: "",
      parent_selector: "",
      side_panel: "",
      side_panel_locations: "",
      side_panel_sortorder: "",
      side_panel_years: ""
    }
  }
});
