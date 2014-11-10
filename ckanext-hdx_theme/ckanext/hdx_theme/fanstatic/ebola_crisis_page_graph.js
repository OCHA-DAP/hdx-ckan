var sql = 'SELECT "Indicator", "Date", "Country", value FROM "f48a3cf9-110e-4892-bedf-d4c1d725a7d1" ' +
        'WHERE "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola deaths\' '+
        'OR "Indicator"=\'Cumulative number of confirmed, probable and suspected Ebola cases\' '+
        'ORDER BY "Date"';

var data = encodeURIComponent(JSON.stringify({sql: sql}));

$.ajax({
  type: 'POST',
  dataType: 'json',
  url: 'https://data.hdx.rwlabs.org/api/3/action/datastore_search_sql',
  data: data,
  success: function(data) {
      console.log(data);
      var prcoessedData = processData(data.result.records);
      generateLineChart('#ebola_graph',prcoessedData);
  }
});

function processData(dataIn){
    var deathsData = [];
    var casesData=[];
    var deathsFirstLine = true;
    var casesFirstLine = true;
    dataIn.forEach(function(e){
        if(e.Indicator=='Cumulative number of confirmed, probable and suspected Ebola deaths'){
            if(deathsFirstLine || e['Date']!=deathsData[deathsData.length-1]['date']){
                deathsData.push({
                    'date':e['Date'],
                    'total':0,
                    'Guinea':0,
                    'Liberia':0,
                    'Sierra Leone':0,
                    'other':0
                });
                deathsFirstLine=false;
            }
            deathsData[deathsData.length-1]['total']+=e['value'];
            if(e['Country']=='Guinea'||e['Country']=='Liberia'||e['Country']=='Sierra Leone'){
                deathsData[deathsData.length-1][e['Country']]=e['value'];
            } else {
                deathsData[deathsData.length-1]['other']+=e['value'];
            }
        } else {
            if(casesFirstLine || e['Date']!=casesData[casesData.length-1]['date']){
               casesData.push({
                    'date':e.Date,
                    'total':0,
                    'Guinea':0,
                    'Liberia':0,
                    'Sierra Leone':0,
                    'other':0
                });
                casesFirstLine=false;
            }
            casesData[casesData.length-1]['total']+=e['value'];
            if(e['Country']=='Guinea'||e['Country']=='Liberia'||e['Country']=='Sierra Leone'){
                casesData[casesData.length-1][e['Country']]=e['value'];
            } else {
                casesData[casesData.length-1]['other']+=e['value'];
            }            
        }
    });
    return {cases:casesData,deaths:deathsData};
};

function generateLineChart(id,data){
    console.log(data);
    data.deaths.forEach(function(e){
        e.date = new Date(e.date);
    });
    data.cases.forEach(function(e){
        e.date = new Date(e.date);
    });
    var margin = {top: 20, right: 20, bottom: 25, left: 50},
        width = $(id).width() - margin.left - margin.right,
        height = $(id).height() - margin.top - margin.bottom;

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
            .range([height, 0]);
    
    x.domain(d3.extent(data.deaths, function(d) { 
        return d.date; }));
    y.domain([0,d3.max(data.cases, function(d) { return d.total; })]);    

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    var line = d3.svg.line()
        .x(function(d) {
            console.log(d.date);
            return x(d.date);
        })
        .y(function(d) { return y(d.total); });

    var svg = d3.select(id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


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
        .style("text-anchor", "end")
        .text("Cases");

    svg.append("path")
        .datum(data.cases)
        .attr("class", "line")
        .attr("d", line)
        .attr("fill","none")
        .attr("stroke","steelblue")
        .attr("stroke-width","1px");

    svg.append("path")
        .datum(data.deaths)
        .attr("class", "line2")
        .attr("d", line)
        .attr("fill","none")
        .attr("stroke","red")
        .attr("stroke-width","1px");
}