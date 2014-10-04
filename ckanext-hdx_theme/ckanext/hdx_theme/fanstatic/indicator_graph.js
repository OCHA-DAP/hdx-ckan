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
    filteredLocations: null,
    graphData: [],
    data: [],
    dataCallbacks: [],
    elementId: null,
    view_port_reset: true,
    _last_datapoints_div: null,
    _sort_order_values:{
      VALUE_DESC: "Value descending",
      VALUE_ASC: "Value ascending",
      ALPH_AZ: "Alphabet A-Z",
      ALPH_ZA: "Alphabet Z-A"
    },
    _sort_order: "VALUE_DESC",
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
    _internal_load_data_build_graph: function (){
      var indicatorCode, sourceCode;
      indicatorCode = indicatorCodeMapping[this.options.name];
      sourceCode = indicatorSourceMapping[this.options.name];
      //prepare source aux for url
      var urlSourceAux = "";
      if (sourceCode != "")
        urlSourceAux = "&s="+sourceCode;
      //get the data synchronously from the server
      jQuery.ajax({
        url: "/api/action/hdx_get_indicator_values?it=" + indicatorCode + urlSourceAux + "&periodType=LATEST_YEAR_BY_COUNTRY&sorting="+this._sort_order,
        success: $.proxy(this._data_ajax_success, this),
//        complete: $.proxy(this._data_ajax_complete, this),
        async:false
      });
      //build the chart
      if (this.data.length > 0)
        this.buildChart();
      else
        this.c3_chart.hide();
    },
    //Filter the newly loaded data to show just the selected locations
    _callback_process_data: function(){
      //Check if the filtered Locations were not initialized before
      if (this.filteredLocations === null){
        this.filteredLocations = {};
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
      if (json.success){
        this.data = json.result.results;

        //Call all callbacks that new data was loaded
        for (var i = 0; i < this.dataCallbacks.length; i++){
          this.dataCallbacks[i]();
        }
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
    },
    _callback_trim_names: function () {
      var data = this.data;
      //trim names
      for (var dataEl in data){
        data[dataEl]['trimName'] = data[dataEl]['locationName'];
        if (data[dataEl]['trimName'].length > 15)
          data[dataEl]['trimName'] = data[dataEl]['trimName'].substring(0, 15) + '...';
      }
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
        locationContainer.append("<li><input id='" + id + "' value='" + code + "' class='locationCheckbox' checked type='checkbox'/><label for='" + id + "'>" + name + "</label></li>");
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
        for (var code in module.filteredLocations)
          module.filteredLocations[code] = this.checked;
        $("#"+module.options.side_panel_locations + " li input").prop('checked', this.checked);
      }
      else
        module.filteredLocations[code] = this.checked;

      module._callback_process_data();//adjust the new data
      module.buildChart();
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
      if (continuousLocation != ""){
        $("#"+continuousLocation+" .cb-item-count").html(data.length);
        var locationList = $("#" + continuousLocation + " .cb-item-links ul");
        locationList.children().remove();
        if (data.length > 0)
          locationList.html("");

        for (var i = 0; i <= 4; i++){
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
    //Callback for the zoom event, but trigger no redraw
    _zoomEventNoRedraw: function(w, domain){
      var dif = w[1] - w[0]; //number of data points shown

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
      data = this.graphData;

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
      container: "",
      parent_selector: "",
      side_panel: "",
      side_panel_locations: "",
      side_panel_sortorder: ""
    }
  }
});