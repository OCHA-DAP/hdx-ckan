var sql = 'SELECT "Indicator", "Date", "Country", value FROM "table_name_placeholder" ' +
        'WHERE "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola deaths\' '+
        'OR "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola cases\' '+
        'ORDER BY "Date"';

sql = sql.replace('table_name_placeholder', $('#cases-datastore-id').text().trim());

var data = encodeURIComponent(JSON.stringify({sql: sql}));

$.ajax({
  type: 'POST',
  dataType: 'json',
  url: '/api/3/action/datastore_search_sql',
  data: data,
  success: function(data) {
      var processedData = processData(data.result.records);
      generateLineChart('#ebola_graph',processedData);
  }
});

function processData(dataIn){
    var data = [];
    var firstLine = true;
    dataIn.forEach(function(e){
        if(firstLine || e['Date']!=data[data.length-1]['date']){
            data.push({
                'date':e['Date'],
                'deaths':{
                'total':0,
                'Guinea':0,
                'Liberia':0,
                'Sierra Leone':0,
                'other':0
                },
                'cases':{
                'total':0,
                'Guinea':0,
                'Liberia':0,
                'Sierra Leone':0,
                'other':0
                }
            });
            firstLine=false;
        }
        if(e.Indicator=='Cumulative number of confirmed, probable and suspected Ebola deaths'){
            data[data.length-1]['deaths']['total']+=e['value'];
            if(e['Country']=='Guinea'||e['Country']=='Liberia'||e['Country']=='Sierra Leone'){
                data[data.length-1]['deaths'][e['Country']]=e['value'];
            } else {
                data[data.length-1]['deaths']['other']+=e['value'];
            }
        } else {
            data[data.length-1]['cases']['total']+=e['value'];
            if(e['Country']=='Guinea'||e['Country']=='Liberia'||e['Country']=='Sierra Leone'){
                data[data.length-1]['cases'][e['Country']]=e['value'];
            } else {
                data[data.length-1]['cases']['other']+=e['value'];
            }            
        }
    });
    return data;
};

function generateLineChart(id,data){
    data.forEach(function(e){
        e.date = new Date(e.date);
    });
    
    var varNames = d3.keys(data[0].deaths).filter(function (key) { return key !== 'total';});;
    
    var seriesDeathArr = [], series = {};
        varNames.forEach(function (name) {
          series[name] = {name: name, values:[]};
          seriesDeathArr.push(series[name]);
        });
        data.forEach(function (d) {
          varNames.map(function (name) {
            series[name].values.push({label: d.date, value: +d.deaths[name]});
          });
        });
        
    var seriesDeathArr = [], series = {};
        varNames.forEach(function (name) {
          series[name] = {name: name, values:[]};
          seriesDeathArr.push(series[name]);
        });
        data.forEach(function (d) {
          varNames.map(function (name) {
            series[name].values.push({label: d.date, value: +d.deaths[name]});
          });
        });        
        
    var deathColor = d3.scale.ordinal()
          //.range(["#B71C1C","#E53935","#EF9A9A","#FFEBEE"]);
            .range(["#f2645a","#F58A83","#F8B1AC","#FBD8D5"]);
  
    var seriesCaseArr = [], series = {};
        varNames.forEach(function (name) {
          series[name] = {name: name, values:[]};
          seriesCaseArr.push(series[name]);
        });
        data.forEach(function (d) {
          varNames.map(function (name) {
            series[name].values.push({label: d.date, value: +d.cases[name]});
          });
        });        

    var caseColor = d3.scale.ordinal()
          //.range(["#1A237E","#3949AB","#7986CB","#E8EAF6"])
          .range(["#007ce0","#4CA3E9","#7FBDEF","#CCE4F8"]);

    var margin = {top: 20, right: 150, bottom: 25, left: 50},
        width = $(id).width() - margin.left - margin.right,
        height = $(id).height() - margin.top - margin.bottom;

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
            .range([height, 0]);
    
    x.domain(d3.extent(data, function(d) { 
        return d.date; }));
    y.domain([0,d3.max(data, function(d) { return d.cases.total; })]);    

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    var gridAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .tickSize(-width, 0, 0)
        .tickFormat("");

    var deathLine = d3.svg.line()
        .x(function(d) {
            return x(d.date);
        })
        .y(function(d) { return y(d.deaths.total); });

    var caseLine = d3.svg.line()
        .x(function(d) {
            return x(d.date);
        })
        .y(function(d) { return y(d.cases.total); });

    var deathArea = d3.svg.area()
        .x(function(d) { return x(d.date); })
        .y0(function(d) { return y(0); })
        .y1(function(d) { return y(d.deaths.total); });

    var caseArea = d3.svg.area()
        .x(function(d) { return x(d.date); })
        .y0(function(d) { return y(d.deaths.total); })
        .y1(function(d) { return y(d.cases.total); });

    var stack = d3.layout.stack()
        .offset("zero")
        .values(function (d) { return d.values; })
        .x(function (d) { return x(d.label); })
        .y(function (d) { return d.value; });

    var area = d3.svg.area()
        .x(function (d) { return x(d.label); })
        .y0(function (d) { return y(d.y0); })
        .y1(function (d) { return y(d.y0 + d.y); });
  
    stack(seriesDeathArr);
    stack(seriesCaseArr);
    var svg = d3.select(id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("g")
        .attr("class", "grid")
        .call(gridAxis);

    svg.append("g")
        .attr("class", "xaxis axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "yaxis axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end");

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].cases.total))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Cases ("+data[data.length-1].cases.total+")")
        .attr("class","linelabels");

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].deaths.total))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Deaths ("+data[data.length-1].deaths.total+")")
        .attr("class","linelabels");

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].cases['other']/2+data[data.length-1].cases['Sierra Leone']
            +data[data.length-1].cases['Liberia']+data[data.length-1].cases['Guinea']
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Other ("+data[data.length-1].cases['other']+")")
        .attr("class","areacaselabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].cases['Sierra Leone']/2
            +data[data.length-1].cases['Liberia']+data[data.length-1].cases['Guinea']
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Sierra Leone ("+data[data.length-1].cases['Sierra Leone']+")")
        .attr("class","areacaselabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].cases['Liberia']/2+data[data.length-1].cases['Guinea']
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Liberia ("+data[data.length-1].cases['Liberia']+")")
        .attr("class","areacaselabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].cases['Guinea']/2
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Guinea ("+data[data.length-1].cases['Guinea']+")")
        .attr("class","areacaselabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].deaths['other']/2+data[data.length-1].deaths['Sierra Leone']
            +data[data.length-1].deaths['Liberia']+data[data.length-1].deaths['Guinea']
        )-5)
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Other ("+data[data.length-1].deaths['other']+")")
        .attr("class","areadeathlabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].deaths['Sierra Leone']/2
            +data[data.length-1].deaths['Liberia']+data[data.length-1].deaths['Guinea']
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Sierra Leone ("+data[data.length-1].deaths['Sierra Leone']+")")
        .attr("class","areadeathlabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].deaths['Liberia']/2+data[data.length-1].deaths['Guinea']
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Liberia ("+data[data.length-1].deaths['Liberia']+")")
        .attr("class","areadeathlabels")
        .attr("opacity",0);

    svg.append("g")
        .append("text")
        .attr("x",width+10)
        .attr("y", y(data[data.length-1].deaths['Guinea']/2
        ))
        .attr("dy", ".2em")
        .style("text-anchor", "start")
        .text("Guinea ("+data[data.length-1].deaths['Guinea']+")")
        .attr("class","areadeathlabels")
        .attr("opacity",0);

    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("d", caseLine)
        .attr("fill","none")
        .attr("stroke","#007ce0")
        .attr("stroke-width","2px");

    svg.append("path")
        .datum(data)
        .attr("class", "line deathline")
        .attr("d", deathLine)
        .attr("fill","none")
        .attr("stroke","#f2645a")
        .attr("stroke-width","2px");

    var selection = svg.selectAll(".seriesdeath")
          .data(seriesDeathArr)
          .enter().append("g")
            .attr("class", "series");

        selection.append("path")
          .attr("class", "deathPath")
          .attr("d", function (d) { return area(d.values); })
          .style("fill", function (d) { return deathColor(d.name); })
          .style("stroke", function (d) { return deathColor(d.name); })
          .attr("opacity",0);

      var selection = svg.selectAll(".seriescases")
          .data(seriesCaseArr)
          .enter().append("g")
            .attr("class", "series");

        selection.append("path")
            .attr("class", "casePath")
            .attr("d", function (d) { return area(d.values); })
            .style("fill", function (d) { return caseColor(d.name); })
            .style("stroke", function (d) { return caseColor(d.name); })
            .attr("opacity",0);

    svg.append("path")
        .datum(data)
        .attr("class", "area")
        .attr("d", deathArea)
        .attr("opacity",0)
        .on("mouseover",function(){
            d3.selectAll(".deathPath").transition().duration(500).attr("opacity",0.5);
            d3.selectAll(".linelabels").transition().duration(500).attr("opacity",0);
            d3.selectAll(".areadeathlabels").transition().duration(500).attr("opacity",1);
        })
        .on("mouseout",function(){
            d3.selectAll(".deathPath").transition().duration(500).attr("opacity",0);
            d3.selectAll(".linelabels").transition().duration(500).attr("opacity",1);
            d3.selectAll(".areadeathlabels").transition().duration(500).attr("opacity",0);
        });        

    svg.append("path")
        .datum(data)
        .attr("class", "area")
        .attr("d", caseArea)
        .attr("opacity",0)
        .on("mouseover",function(){
            d3.selectAll(".casePath").transition().duration(500).attr("opacity",0.5);
            d3.selectAll(".linelabels").transition().duration(500).attr("opacity",0);
            d3.selectAll(".areacaselabels").transition().duration(500).attr("opacity",1);
            d3.selectAll(".deathline").transition().duration(500).attr("opacity",0);
        })
        .on("mouseout",function(){
            d3.selectAll(".casePath").transition().duration(500).attr("opacity",0);
            d3.selectAll(".linelabels").transition().duration(500).attr("opacity",1);
            d3.selectAll(".areacaselabels").transition().duration(500).attr("opacity",0);
            d3.selectAll(".deathline").transition().duration(500).attr("opacity",1);
        });
}