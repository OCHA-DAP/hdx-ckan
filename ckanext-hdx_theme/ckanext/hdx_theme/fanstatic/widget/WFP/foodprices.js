function initMap(){
    
    var base_osm = L.tileLayer(
            'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
            attribution: '&copy; OpenStreetMap contributors'}
    );
          
    var map = L.map('map', {
        center: [0,0],
        zoom: 2,
        layers: [base_osm]
    });

    return map;
}

function addCountriesToMap(results){
    
    var world_style = {
        color: '#fff',
        fillColor: '#2a93fc',
        fillOpacity:0.8,
        opacity:0.8,
        weight:1
    };
    
    var world = topojson.feature(un_world, un_world.objects.un_world);

    for(i = world.features.length-1; i >= 0; i--){
        if( $.inArray(world.features[i].properties.ADM0_CODE, results) === -1 ){
            world.features.splice(i, 1);
        }        
    }
    
    var overlay_world = L.geoJson(world.features,{
        style:world_style,
        onEachFeature: function(feature, layer){
            layer.on('click', function (e) {
                initCountry(feature.properties.ADM0_CODE,feature.properties.ADM0_NAME,embedded);
            });
        }  
    }).addTo(map);    
}

function initCountry(adm0_code,adm0_name){

    makeEmbedURL(adm0_code,'','','','');
    if(embedded!=='true'){
        var targetHeader = '#modal-header-content';
        $('#modal-body').html('Loading...');       
        $('#wfpModal').modal('show');        
    } else {
        var targetHeader = '#header';
        $('#map').hide();
        $('#charts').show();
        $('#header').show();
    }
    var html = '<h4>'+adm0_name+' Product Price since 2013</h4><p>';
    if(embedded ==='true'){
        html += '<a id="maplink" href="">Map</a> > ';
    }
    html +=adm0_name+'</p>';
    $(targetHeader).html(html);
    $('#maplink').click(function(event){
       event.preventDefault();
       backToMap();
    });
    
    getProductsByCountryID(adm0_code,adm0_name);
}

function generateSparklines(results,adm0_code,adm0_name){
    
    if(embedded!=='true'){
        var targetDiv = '#modal-body';
    } else {
        var targetDiv = '#charts';
    }
    
    var numProd = 0;
    var curProd = '';
    var curUnit = '';
    var topMonth = 0;
    var html='<div class="row">';

    results.forEach(function(e){
        if(e.mp_year*12+e.month_num*1>topMonth) {
            topMonth = e.mp_year*12+e.month_num*1;
        }
        if(e.cm_id!==curProd || e.um_id!==curUnit){
            numProd++;
            curProd = e.cm_id;
            curUnit = e.um_id;
            if(numProd>1 && numProd%4===1){
                html+= '</div><div class="row">';
            }
            html+='<div id="product_' + e.cm_id + '_' + e.um_id + '" class="productsparkline col-xs-3"><p>' + e.cm_name + ' per ' + e.um_name + '</p></div>';
        }
    });

    html+='</div>';
    
    $(targetDiv).html(html);
    var curProd = '';
    var curUnit = '';
    var data=[];
    results.forEach(function(e){
        if(e.cm_id!==curProd || e.um_id !==curUnit){
            if(data!==[]){
                generateSparkline(curProd,curUnit,data,topMonth);
                $('#product_' + e.cm_id + '_' + e.um_id).on('click',function(){
                    getProductDataByCountryID(adm0_code,e.cm_id,e.um_id,adm0_name,e.cm_name,e.um_name,'','');
                });
            }
            data = [];
            curProd = e.cm_id;
            curUnit = e.um_id;
        }
        var datum = {y:e.avg,x:e.mp_year*12+e.month_num};
        data.push(datum);
    });
    generateSparkline(curProd,curUnit,data,topMonth);
}

function generateSparkline(prodID,unitID,data,topMonth){
    
    var svg = d3.select('#product_'+prodID+'_'+unitID).append('svg').attr('width',$('#product_'+prodID+'_'+unitID).width()).attr('height', '50px');
    var x = d3.scale.linear().domain([2013*12,topMonth]).range([0, $('#product_'+prodID+'_'+unitID).width()]);
    //var y = d3.scale.linear().domain([d3.max(data,function(d){return d.y;}),d3.min(data,function(d){return d.y;})]).range([0, 50]);
    var y = d3.scale.linear().domain([d3.max(data,function(d){return d.y;})*1.1,0]).range([0, 50]);

    var line = d3.svg.line()
        .x(function(d) {
            return x(d.x);
        })
        .y(function(d) {
            return y(d.y);
        });
        

    var yearLine = d3.svg.line()
        .x(function(d) {
            return x(d.x);
        })
        .y(function(d) {
            return d.y;
        });        
    
    for(i=0;i<25;i++){
        if((2013+i)*12<topMonth){
            var dataLine=[{
                x:(2013+i)*12,
                y:0
            },{
                x:(2013+i)*12,
                y:50
            }];
            svg.append('path').attr('d', yearLine(dataLine)).attr('class', 'sparkyearline');
        }
    }
    
    svg.append('path').attr('d', line(data)).attr('class', 'sparkline');
}

function crossfilterData(data){
    
    data.forEach(function(e){
        e.date = new Date(e.mp_year, e.month_num-1, 1);
    });       
    
    var cf = crossfilter(data);
    
    cf.byDate = cf.dimension(function(d){return d.date;});
    cf.byAdm1 = cf.dimension(function(d){return d.adm1_name;});
    cf.byMkt = cf.dimension(function(d){return d.mkt_name;});
    
    cf.groupByDateSum = cf.byDate.group().reduceSum(function(d) {return d.mp_price;});
    cf.groupByDateCount = cf.byDate.group();
    cf.groupByAdm1Sum = cf.byAdm1.group().reduceSum(function(d) {return d.mp_price;});
    cf.groupByAdm1Count = cf.byAdm1.group();
    cf.groupByMktSum = cf.byMkt.group().reduceSum(function(d) {return d.mp_price;});
    cf.groupByMktCount = cf.byMkt.group(); 
    return cf;
}

function generateChartView(cf,adm0,prod,unit,adm0_code){
    makeEmbedURL(adm0_code,prod,unit,'','');
    if(embedded!=='true'){
        var targetDiv = '#modal-body';
        var targetHeader = '#modal-header-content';
    } else {
        var targetDiv = '#charts';
        var targetHeader = '#header';
    }

    curLevel = 'adm0';
    
    cf.byDate.filterAll();
    cf.byAdm1.filterAll(); 
    cf.byMkt.filterAll();    
    
    
    var html = '<h4>Price of ' + prod + ' per ' + unit + ' in '+adm0+'</h4><p>';
    if(embedded ==='true'){
        html += '<a id="maplink" href="">Map</a> > ';
    }
    html +='<a id="adm0link" href="">'+adm0+'</a> > ' + prod + '</p>';
    $(targetHeader).html(html);
    
    $(targetDiv).html('<div class="row"><div id="nav_chart" class="col-xs-12"></div></div><div class="row"><div id="main_chart" class="col-xs-12"></div></div><div class="row"><div id="drilldown_chart" class="col-xs-12"></div></div>');
    $('#adm0link').click(function(event){
        event.preventDefault();
        initCountry(adm0_code,adm0);
    });
    $('#maplink').click(function(event){
       event.preventDefault();
       backToMap();
    });    
    generateTimeCharts(getAVG(cf.groupByDateSum.all(),cf.groupByDateCount.all()),cf);
    generateBarChart(getAVG(cf.groupByAdm1Sum.all(),cf.groupByAdm1Count.all()),cf,prod,unit,adm0,adm0_code);

}

function generateADMChartView(cf,adm1,prod,unit,adm0,adm0_code){
    makeEmbedURL(adm0_code,prod,unit,adm1,'');
    if(embedded!=='true'){
        var targetDiv = '#modal-body';
        var targetHeader = '#modal-header-content';
    } else {
        var targetDiv = '#charts';
        var targetHeader = '#header';
    }
    
    curLevel = 'adm1';
    var html = '<h4>Price of ' + prod + ' per ' + unit + ' in '+adm1+'</h4><p>';
    if(embedded ==='true'){
        html += '<a id="maplink" href="">Map</a> > ';
    }
    html +='<a id="adm0link" href="">'+adm0+'</a> > <a id="prodlink" href="">' + prod + '</a> > ' + adm1 + '</p>';
    $(targetHeader).html(html);
    $(targetDiv).html('<div class="row"><div id="nav_chart" class="col-xs-12"></div></div><div class="row"><div id="main_chart" class="col-xs-12"></div></div><div class="row"><div id="drilldown_chart" class="col-xs-12"></div></div>');
    
    $('#adm0link').click(function(event){
        event.preventDefault();
        initCountry(adm0_code,adm0);
    });
    
    $('#prodlink').click(function(event){
        event.preventDefault();
        generateChartView(cf,adm0,prod,unit,adm0_code);
    });
    $('#maplink').click(function(event){
       event.preventDefault();
       backToMap();
    });    
    cf.byDate.filterAll();
    cf.byMkt.filterAll();
    cf.byAdm1.filter(adm1);    
    
    generateTimeCharts(getAVG(cf.groupByDateSum.all(),cf.groupByDateCount.all()),cf);
    generateBarChart(getAVG(cf.groupByMktSum.all(),cf.groupByMktCount.all()),cf,prod,unit,adm0,adm0_code,adm1);

}

function generateMktChartView(cf,mkt,prod,unit,adm0,adm0_code,adm1){
    makeEmbedURL(adm0_code,prod,unit,adm1,mkt);
    if(embedded!=='true'){
        var targetDiv = '#modal-body';
        var targetHeader = '#modal-header-content';
    } else {
        var targetDiv = '#charts';
        var targetHeader = '#header';
    }
    
    curLevel = 'mkt';
    
    var html = '<h4>Price of ' + prod + ' per ' + unit + ' in '+mkt+'</h4><p>';
    if(embedded ==='true'){
        html += '<a id="maplink" href="">Map</a> > ';
    }
    html +='<a id="adm0link" href="">'+adm0+'</a> > <a id="prodlink" href="">' + prod + '</a> > <a id="adm1link" href="">' + adm1 + '</a> > ' + mkt + '</p>';
    $(targetHeader).html(html);
    $(targetDiv).html('<div class="row"><div id="nav_chart" class="col-xs-12"></div></div><div class="row"><div id="main_chart" class="col-xs-12"></div></div><div class="row"><div id="drilldown_chart" class="col-xs-12"></div></div>');
    
    $('#adm0link').click(function(event){
        event.preventDefault();
        initCountry(adm0_code,adm0);
    });
    
    $('#prodlink').click(function(event){
        event.preventDefault();
        generateChartView(cf,adm0,prod,unit,adm0_code);
    });
    
    $('#adm1link').click(function(event){
        event.preventDefault();
        generateADMChartView(cf,adm1,prod,unit,adm0,adm0_code);
    });     
    $('#maplink').click(function(event){
       event.preventDefault();
       backToMap();
    });    
    cf.byDate.filterAll();
    cf.byMkt.filter(mkt);    
    
    generateTimeCharts(getAVG(cf.groupByDateSum.all(),cf.groupByDateCount.all()),cf);
}

function getAVG(sum,count){
    var data =[];
    sum.forEach(function(e,i){
        var value=0;
        if(count[i].value!==0){
            value = e.value/count[i].value;
            data.push({key:e.key,value:value});
        }
    });

    return data;    
}

function generateTimeCharts(data,cf){
    
    $('#nav_chart').html('<p>Select a portion of the chart below to zoom in the data.</p>');

    var margin = {top: 10, right: 20, bottom: 20, left: 60},
        width = $('#nav_chart').width() - margin.left - margin.right,
        height = 175 - margin.top - margin.bottom,
        height2 = 50 - margin.top - margin.bottom;

    var x = d3.time.scale().range([0, width]),
        x2 = d3.time.scale().range([0, width]),
        y = d3.scale.linear().range([height, 0]),
        y2 = d3.scale.linear().range([height2, 0]);

    var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(5),
        xAxis2 = d3.svg.axis().scale(x2).orient("bottom").ticks(5),
        yAxis = d3.svg.axis().scale(y).orient("left").ticks(5);

    var brush = d3.svg.brush()
        .x(x2)
        .on("brush", brushed)
        .on("brushend", function(){
            cf.byDate.filterRange(brush.empty() ? x2.domain() : brush.extent());
            if(curLevel === "adm0"){
                transitionBarChart(getAVG(cf.groupByAdm1Sum.all(),cf.groupByAdm1Count.all()));
            }
            if(curLevel === "adm1"){
                transitionBarChart(getAVG(cf.groupByMktSum.all(),cf.groupByMktCount.all()));
            }                        
        });

    var area = d3.svg.area()
        //.interpolate("monotone")
        .x(function(d) { return x(d.key); })
        .y0(height)
        .y1(function(d) { return y(d.value); });

    var area2 = d3.svg.area()
        //.interpolate("monotone")
        .x(function(d) { return x2(d.key); })
        .y0(height2)
        .y1(function(d) { return y2(d.value); });

    var main_chart = d3.select("#main_chart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    main_chart.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

    var focus = main_chart.append("g")
        .attr("class", "focus")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var nav_chart = d3.select("#nav_chart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height2 + margin.top + margin.bottom);

    var context = nav_chart.append("g")
        .attr("class", "context")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    x.domain(d3.extent(data.map(function(d) { return d.key; })));
    y.domain([0, d3.max(data.map(function(d) { return d.value; }))]);
    x2.domain(x.domain());
    y2.domain(y.domain());

    focus.append("path")
        .datum(data)
        .attr("class", "area")
        .attr("d", area);

    focus.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    focus.append("g")
        .attr("class", "y axis")
        .call(yAxis);
 
    context.append("path")
        .datum(data)
        .attr("class", "area")
        .attr("d", area2);

    context.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height2 + ")")
        .call(xAxis2);

    context.append("g")
        .attr("class", "x brush")
        .call(brush)
        .selectAll("rect")
          .attr("y", -6)
          .attr("height", height2 + 7);
  
    main_chart.append("text")
        .attr("class", "y label")
        .attr("text-anchor", "end")
        .attr("y", 20)
        .attr("x",-30)
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Price in local currency");
  
    $('#main_chart').append('<a id="mainchartdownload" href="">Download Data</a>');
    $('#mainchartdownload').click(function(event){
        event.preventDefault();
        downloadData(data,'Date');
    });
  
    function brushed() {
      x.domain(brush.empty() ? x2.domain() : brush.extent());
      focus.select(".area").attr("d", area);
      focus.select(".x.axis").call(xAxis);
    }      
}

function downloadData(data,name){
    var csvContent = 'data:text/csv;charset=utf-8,';
    csvContent += name+',Price\n';
    var m_names = new Array('January', 'February', 'March', 
    'April', 'May', 'June', 'July', 'August', 'September', 
    'October', 'November', 'December');    
    data.forEach(function(e, index){
       if(name==='Date'){
           var key = m_names[e.key.getMonth()] + '-' + e.key.getFullYear();
       } else {
           var key = e.key;
       }
           
       var dataString = key+','+e.value;
       csvContent += index < data.length ? dataString+ '\n' : dataString;
    });
    var encodedUri = encodeURI(csvContent);
    var link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'data.csv');
    link.click();
}

function generateBarChart(data,cf,prod,unit,adm0,adm0_code,adm1){
    $('#drilldown_chart').html('<p>Click a bar on the chart below to explore data for that area.</p>');
    var margin = {top: 10, right: 60, bottom: 60, left: 60},
        width = $("#drilldown_chart").width() - margin.left - margin.right,
        height =  130 - margin.top - margin.bottom;
    
    var x = d3.scale.ordinal()
        .rangeRoundBands([0, width]);

    var y = d3.scale.linear()
        .range([0,height]); 

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(3);
    
    x.domain(data.map(function(d) {return d.key; }));
    y.domain([d3.max(data.map(function(d) { return d.value; })),0]);
    
    var svg = d3.select("#drilldown_chart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("g")
        .attr("class", "x axis xaxis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")  
            .style("text-anchor", "start")
            .attr("transform", function(d) {
                return "rotate(35)"; 
            });

    svg.append("g")
        .attr("class", "y axis yaxis")
        .call(yAxis);

    svg.selectAll("rect")
            .data(data)
            .enter()
            .append("rect") 
            .attr("x", function(d,i) { return x(d.key); })
            .attr("width", x.rangeBand()-1)
            .attr("y", function(d){
                           return y(d.value);        
            })
            .attr("height", function(d) {
                            return height-y(d.value);
            })
            .attr("class","bar")
            .on("click",function(d){
                if(curLevel === "adm1"){generateMktChartView(cf,d.key,prod,unit,adm0,adm0_code,adm1);};
                if(curLevel === "adm0"){generateADMChartView(cf,d.key,prod,unit,adm0,adm0_code);};
            });    
            
}

function transitionBarChart(data){
    
    var margin = {top: 10, right: 60, bottom: 60, left: 60},
        width = $("#drilldown_chart").width() - margin.left - margin.right,
        height =  130 - margin.top - margin.bottom;
    
    var x = d3.scale.ordinal()
        .rangeRoundBands([0, width]);

    var y = d3.scale.linear()
        .range([0,height]);

    
    x.domain(data.map(function(d) {return d.key; }));
    y.domain([d3.max(data.map(function(d) { return d.value; })),0]);
    
    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(3);    
    
    d3.selectAll(".yaxis")
        .transition().duration(200)
        .call(yAxis);

    d3.selectAll(".xaxis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")  
            .style("text-anchor", "start")
            .attr("transform", function(d) {
                return "rotate(35)"; 
            });
    var count = data.length;
    
    var svg = d3.select("#drilldown_chart").selectAll("rect")
            .attr("x", function(d,i) { return x(d.key); })
            .attr("width", x.rangeBand()-1)
            .attr("y", function(d){
                           return y(d.value);        
            })
            .attr("height", function(d,i) {
                if(i>count){
                            return 0;
                } else {
                            return height-y(d.value);
                }
            });      
    
    var svg = d3.select("#drilldown_chart").selectAll("rect").data(data)
        .transition().duration(200)  
            .attr("x", function(d,i) { return x(d.key); })
            .attr("width", x.rangeBand()-1)
            .attr("y", function(d){
                           return y(d.value);        
            })
            .attr("height", function(d) {
                            return height-y(d.value);
            });  
                
}

function backToMap(){
        $('#header').html('<h3>WFP collected Food prices</h3><p>Click a country to explore prices for different products</p>');
        $('#map').show();
        map.invalidateSize();
        $('#charts').hide(); 
}
 
function getCountryIDs(){
    
    var sql = 'SELECT distinct adm0_id FROM "' + datastoreID + '"';

    var data = encodeURIComponent(JSON.stringify({sql: sql}));

    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: '/api/3/action/datastore_search_sql',
      data: data,
      success: function(data) {
          var results = [];
          data.result.records.forEach(function(e){
              results.push(e.adm0_id);
          });
          addCountriesToMap(results);
      }
    });     
}

function getProductDataByCountryID(adm0_code,cm_id,um_id,adm0_name,cm_name,um_name,adm1_name,mkt_name){
    var sql = 'SELECT adm1_id,adm1_name,mkt_id,mkt_name, cast(mp_month as double precision) as month_num, mp_year, mp_price FROM "'+datastoreID+'" where adm0_id='+adm0_code+' and cm_id='+cm_id+' and um_id='+um_id;

    var data = encodeURIComponent(JSON.stringify({sql: sql}));

    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: '/api/3/action/datastore_search_sql',
      data: data,
      success: function(data) {

           var cf = crossfilterData(data.result.records); 
           if(adm1_name===''){
              generateChartView(cf,adm0_name,cm_name,um_name,adm0_code); 
           } else if (mkt_name===''){
              generateADMChartView(cf,adm1_name,cm_name,um_name,adm0_name,adm0_code);  
           } else {
               cf.byAdm1.filter(adm1_name);
               generateMktChartView(cf,mkt_name,cm_name,um_name,adm0_name,adm0_code,adm1_name); 
           }
      }
    });    
}

function getProductsByCountryID(adm0_code,adm0_name){
    
    var sql = 'SELECT cm_id, cm_name, um_id, um_name, avg(cast(mp_month as double precision)) as month_num, mp_year, avg(mp_price) FROM "' + datastoreID + '" where adm0_id=' + adm0_code + ' and mp_year>2012 group by cm_id, cm_name, um_name, um_id, mp_month, mp_year order by cm_id, um_id, mp_year, month_num';    

    var data = encodeURIComponent(JSON.stringify({sql: sql}));

    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: '/api/3/action/datastore_search_sql',
      data: data,
      success: function(data) {
          generateSparklines(data.result.records,adm0_code,adm0_name);
      }
    });     
}

function getNameParams(adm0,prod,unit,adm1,mkt){
    
    if(prod=='Not found' && unit =='Not found'){
            var sql = 'SELECT distinct(adm0_name) FROM "'+datastoreID+'" where adm0_id='+adm0;

            var data = encodeURIComponent(JSON.stringify({sql: sql}));

            $.ajax({
              type: 'POST',
              dataType: 'json',
              url: '/api/3/action/datastore_search_sql',
              data: data,
              success: function(data) {              
                  initCountry(adm0,data.result.records[0].adm0_name);
              }
            });
    }
    if(prod!='Not found' && unit !='Not found'){
        var sql = 'SELECT distinct adm0_name,cm_id,um_id FROM "'+datastoreID+'" where adm0_id='+adm0+' and cm_name=\''+prod+'\' and um_name=\''+unit+'\'';

        var data = encodeURIComponent(JSON.stringify({sql: sql}));

        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '/api/3/action/datastore_search_sql',
            data: data,
            success: function(data) {              
                if(adm1=='Not found'){
                    getProductDataByCountryID(adm0,data.result.records[0].cm_id,data.result.records[0].um_id,data.result.records[0].adm0_name,prod,unit,'','');            
                }
                if(adm1!='Not found'&&mkt=='Not found'){
                    getProductDataByCountryID(adm0,data.result.records[0].cm_id,data.result.records[0].um_id,data.result.records[0].adm0_name,prod,unit,adm1,'');
                }
                if(adm1!='Not found'&&mkt!='Not found'){
                    getProductDataByCountryID(adm0,data.result.records[0].cm_id,data.result.records[0].um_id,data.result.records[0].adm0_name,prod,unit,adm1,mkt);
                }                
            }
        });        
    }   
}

function makeEmbedURL(adm0,prod,unit,adm1,mkt){
    var embed='';

    if(prod==''){
        embed = url+'?embedded=true&adm0='+adm0;
    }
    if(prod!=''&&adm1==''){
        embed = url+'?embedded=true&adm0='+adm0+'&prod='+prod+'&unit='+unit;
    }
    if(adm1!=''&&mkt==''){
        embed = url+'?embedded=true&adm0='+adm0+'&prod='+prod+'&unit='+unit+'&adm1='+adm1;
    }
    if(mkt!=''){
        embed = url+'?embedded=true&adm0='+adm0+'&prod='+prod+'&unit='+unit+'&adm1='+adm1+'&mkt='+mkt;
    }
    var value = '<iframe src="'+embed+'&size=medium" width=900 height=600></iframe>';
    var html = '<button id="embedbutton" class="btn btn-default">Embed</button><div id="embedoptions"><p>Choose a size and embed the code in your web page</p><p><input type="radio" name="sizewfpviz" value="small">Small <input type="radio" name="sizewfpviz" checked="checked" value="medium">Medium <input type="radio" name="sizewfpviz" value="large">Large</p><input id="embedtext" type="text" size="75" name="embed" value=\''+value+'\' readonly></div> <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
    $('#modal-footer').html(html);
    $('#embedbutton').click(function(){
        $('#embedbutton').hide();
        $('#embedoptions').show();
    });
    $('input[type=radio][name=sizewfpviz]').change(function() {

        if(this.value==='small'){
            var value = '<iframe src="'+embed+'&size=small" width=500 height=600></iframe>';
        }
        if(this.value==='medium'){
            var value = '<iframe src="'+embed+'&size=medium" width=900 height=600></iframe>';
        }
        if(this.value==='large'){
            var value = '<iframe src="'+embed+'&size=large" width=1100 height=600></iframe>';
        }        
        $('#embedtext').val(value);
    });    
}

function parseGet(val) {
    
    var result = 'Not found',
        tmp = [];

    var items = location.search.substr(1).split('&');
    
    for (var index = 0; index < items.length; index++) {
        tmp = items[index].split('=');
        if (tmp[0] === val) result = decodeURIComponent(tmp[1]);
    }
    
    return result;
}

function initembed(){
    var size = parseGet('size');
    var prod = parseGet('prod');
    var unit = parseGet('unit');
    var adm0 = parseGet('adm0');
    var adm1 = parseGet('adm1');
    var mkt = parseGet('mkt');
    
    if(size==='small'){
        $('#map').width(470);
        $('#map').height(485);
        $('#charts').width(496); 
    }
    if(size==='medium'){
        $('#map').width(750);
        $('#map').height(485);
        $('#charts').width(750); 
    }
    if(size==='large'){
        $('#map').width(960);
        $('#map').height(485);
        $('#charts').width(960); 
    }
    $('#charts').hide();
    $('#chart').height(500);
    if(adm0!=='Not found'){
        $('#map').hide();
        $('#charts').show();
        $('#header').show();        
        getNameParams(adm0,prod,unit,adm1,mkt);
    }
}

function initHDX(){
    var embed='?embedded=true';
    var value = '<iframe src="'+url+embed+'&size=medium" width=900 height=600></iframe>';
    var html = '<button id="hdxembedbutton" class="btn btn-default">Embed</button><div id="hdxembedoptions"><p>Choose a size and embed the code in your web page</p><p><input type="radio" name="hdxsizewfpviz" value="small">Small <input type="radio" name="hdxsizewfpviz" checked="checked" value="medium">Medium <input type="radio" name="hdxsizewfpviz" value="large">Large</p><input id="hdxembedtext" type="text" size="75" name="embed" value=\''+value+'\' readonly></div>';
    $('#hdxembed').show();
    $('#hdxembed').html(html);
    $('#hdxembedbutton').click(function(){
        $('#hdxembedbutton').hide();
        $('#hdxembedoptions').show();
    });
    $('input[type=radio][name=hdxsizewfpviz]').change(function() {

        if(this.value==='small'){
            var value = '<iframe src="'+url+embed+'&size=small" width=500 height=600></iframe>';
        }
        if(this.value==='medium'){
            var value = '<iframe src="'+url+embed+'&size=medium" width=900 height=600></iframe>';
        }
        if(this.value==='large'){
            var value = '<iframe src="'+url+embed+'&size=large" width=1100 height=600></iframe>';
        }        
        $('#hdxembedtext').val(value);
    });     
}

var datastoreID = '9e1eb333-333e-4a1f-acfe-f0b43ba73379';
var url = 'http://127.0.0.1:8000/index.html';
var map;
var embedded = (parseGet('embedded'));

$(document).ready(function(){
    if(embedded ==='true'){
        initembed();
    } else {
        initHDX();
    }

    var curLevel = '';

    map = initMap();
    getCountryIDs();
});
