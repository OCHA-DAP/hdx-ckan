var config = {
    dataURL:'data/data.json',
    geoURL:'data/geom.geojson',
    colors:['#FFFFFF','#BFDAEC','#80B5DA','#4190C7','#026BB5']
};

function generateROEADashboard(config,data,geom){
    var cf = crossfilter(data);

    var whereDimension= cf.dimension(function(d){return d.NAME;});
    var timeDimension = cf.dimension(function(d){return d.YEAR;});

    timeDimension.filter('2015');

    var hazardGroup = whereDimension.group().reduceSum(function(d){return d.HAZARDS});
    var copingGroup = whereDimension.group().reduceSum(function(d){return d.COPINGCAPACITY});
    var vulnerabilityGroup = whereDimension.group().reduceSum(function(d){return d.VULNERABILITY});
    var overallGroup = whereDimension.group().reduceSum(function(d){return d.INFORM});

    var fundingGroup = cf.groupAll().reduceSum(function(d){return d.FUNDED});
    var refugeesGroup = cf.groupAll().reduceSum(function(d){return d.REFUGEES});
    var idpsGroup = cf.groupAll().reduceSum(function(d){return d.IDPS});
    var fsGroup = cf.groupAll().reduceSum(function(d){return d.FS});

    var mapChart = dc.leafletChoroplethChart('#hdx-roea-where')
        .width($('#hdx-roea-where').width())
        .height(400)
        .dimension(whereDimension)
        .group(overallGroup)
        .center([0,0])
        .zoom(0)    
        .geojson(geom)
        .colors(config.colors)
        .colorDomain([0, 4])
        .colorAccessor(function (d) {
            var c=0;
            if(d>8){
                c=4;
            } else if (d>7) {
                c=3;
            } else if (d>5) {
                c=2;
            } else if (d>4) {
                c=1;
            } else {
                c=0
            } 
            return c;
            })   
        .featureKeyAccessor(function(feature){
            return feature.id;
        }).popup(function(feature){
            return 'Click to filter <br />'+feature.properties.name;
        })
        .renderPopup(true);

    var fundingND = dc.numberDisplay("#hdx-roea-funding")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(function(d){
            var output = d3.format(".3s")(d);
            if(output.slice(-1)=='k'){
                output = '<span class="hdx-roea-value">'+d3.format("0,000")(output.slice(0, -1) * 1000)+'</span>';
            } else if(output.slice(-1)=='M'){
                output = '<span class="hdx-roea-value">'+output.slice(0, -1)+'</span><span class="hdx-roea-small"> million</span>';
            } else {
                output = '<span class="hdx-roea-value">'+d3.format(".3s")(d)+'</span>';
            }            
            return '<span class="hdx-roea-small">$</span>'+output;
        })                                
        .group(fundingGroup);

    var refugeesND = dc.numberDisplay("#hdx-roea-refugees")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(function(d){
            var output = d3.format(".3s")(d);
            if(output.slice(-1)=='k'){
                output = '<span class="hdx-roea-value">'+d3.format("0,000")(output.slice(0, -1) * 1000)+'</span>';
            } else if(output.slice(-1)=='M'){
                output = '<span class="hdx-roea-value">'+output.slice(0, -1)+'</span><span class="hdx-roea-small"> million</span>';
            } else {
                output = '<span class="hdx-roea-value">'+d3.format(".3s")(d)+'</span>';
            }            
            return output;
        })             
        .group(refugeesGroup);

    var ipdsND = dc.numberDisplay("#hdx-roea-idps")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(function(d){
            var output = d3.format(".3s")(d);
            if(output.slice(-1)=='k'){
                output = '<span class="hdx-roea-value">'+d3.format("0,000")(output.slice(0, -1) * 1000)+'</span>';
            } else if(output.slice(-1)=='M'){
                output = '<span class="hdx-roea-value">'+output.slice(0, -1)+'</span><span class="hdx-roea-small"> million</span>';
            } else {
                output = '<span class="hdx-roea-value">'+d3.format(".3s")(d)+'</span>';
            }            
            return output;
        })                
        .group(idpsGroup);

    var fsND = dc.numberDisplay("#hdx-roea-food")
        .valueAccessor(function(d){
            return d;
        })
        .formatNumber(function(d){
            var output = d3.format(".3s")(d);
            if(output.slice(-1)=='k'){
                output = '<span class="hdx-roea-value">'+d3.format("0,000")(output.slice(0, -1) * 1000)+'</span>';
            } else if(output.slice(-1)=='M'){
                output = '<span class="hdx-roea-value">'+output.slice(0, -1)+'</span><span class="hdx-roea-small"> million</span>';
            } else {
                output = '<span class="hdx-roea-value">'+d3.format(".3s")(d)+'</span>';
            }            
            return output;
        })        
        .group(fsGroup);                        

    dc.renderAll();

    var map = mapChart.map();
    map.scrollWheelZoom.disable();
    zoomToGeom(geom);

    L.tileLayer($('#mapbox-baselayer-url-div').text(), {
        attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>',
        maxZoom: 7
    }).addTo(map);

    L.tileLayer($('#mapbox-labelslayer-url-div').text(), {
        maxZoom: 7
    }).addTo(map);

    $('#overall').on('click',function(){
        mapChart.group(overallGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#overall').removeClass('hdx-roea-inactive');
        $('#overall').addClass('hdx-roea-active');              
    })

    $('#hazard').on('click',function(){
        mapChart.group(hazardGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#hazard').removeClass('hdx-roea-inactive');
        $('#hazard').addClass('hdx-roea-active');                 
    })    

    $('#vulnerability').on('click',function(){
        mapChart.group(vulnerabilityGroup);
        mapChart.redraw();
        $('.tab').addClass('hdx-roea-inactive');
        $('.tab').removeClass('hdx-roea-active');
        $('#vulnerability').removeClass('hdx-roea-inactive');
        $('#vulnerability').addClass('hdx-roea-active');                 
    })

    $('#coping').on('click',function(){
        mapChart.group(copingGroup);
        mapChart.redraw();
        $('.tab').removeClass('hdx-roea-active');
        $('.tab').addClass('hdx-roea-inactive');
        $('#coping').removeClass('hdx-roea-inactive');
        $('#coping').addClass('hdx-roea-active');                 
    })

    $('.hdx-3w-info').css('color',config.colors[4]);

    function zoomToGeom(geom){
        var bounds = d3.geo.bounds(geom);
        map.fitBounds([[bounds[0][1],bounds[0][0]],[bounds[1][1],bounds[1][0]]]);
    }    
}


//load data

var dataCall = $.ajax({ 
    type: 'GET', 
    url: config.dataURL, 
    dataType: 'json',
});

//load geometry

var geomCall = $.ajax({ 
    type: 'GET', 
    url: config.geoURL, 
    dataType: 'json',
});

//when both ready construct dashboard

var tempData = [
  {
    "YEAR":2011,
    "NAME":"BRN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0.73,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0.12,
    "VULNERABILITY":0.78,
    "COPINGCAPACITY":4.19,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2012,
    "NAME":"BRN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0.72,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0.12,
    "VULNERABILITY":0.77,
    "COPINGCAPACITY":4.16,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2013,
    "NAME":"BRN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0.76,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0.12,
    "VULNERABILITY":0.77,
    "COPINGCAPACITY":4.75,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2014,
    "NAME":"BRN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":54179,
    "IDPS":78948,
    "INFORM":0.76,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0.12,
    "VULNERABILITY":0.79,
    "COPINGCAPACITY":4.62,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2015,
    "NAME":"BRN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":54179,
    "IDPS":78948,
    "INFORM":0.76,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":4.59,
    "VULNERABILITY":0.81,
    "COPINGCAPACITY":0.12,
    "PRIORITIES":""
  },
  {
    "YEAR":2011,
    "NAME":"DJI",
    "PIN":210000,
    "TAR":210000,
    "COMMITTED":33264338,
    "FUNDED":19370114,
    "REFUGEES":20611,
    "IDPS":0,
    "INFORM":4.93,
    "FS":210000,
    "NUTRITION":172500,
    "HEALTH":222500,
    "WASH":1941000,
    "EDUCATION":0,
    "HAZARDS":2.81,
    "VULNERABILITY":5.74,
    "COPINGCAPACITY":7.43,
    "PRIORITIES":"2011 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"DJI",
    "PIN":206000,
    "TAR":206000,
    "COMMITTED":79310556,
    "FUNDED":31661994,
    "REFUGEES":18658,
    "IDPS":0,
    "INFORM":4.94,
    "FS":206000,
    "NUTRITION":172500,
    "HEALTH":222500,
    "WASH":2500000,
    "EDUCATION":0,
    "HAZARDS":2.82,
    "VULNERABILITY":5.83,
    "COPINGCAPACITY":7.34,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"DJI",
    "PIN":139000,
    "TAR":139000,
    "COMMITTED":663311782,
    "FUNDED":370453728,
    "REFUGEES":19949,
    "IDPS":0,
    "INFORM":4.96,
    "FS":139000,
    "NUTRITION":344545,
    "HEALTH":152000,
    "WASH":2750000,
    "EDUCATION":0,
    "HAZARDS":2.89,
    "VULNERABILITY":5.82,
    "COPINGCAPACITY":7.26,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"DJI",
    "PIN":300000,
    "TAR":250000,
    "COMMITTED":74085087,
    "FUNDED":20563729,
    "REFUGEES":24425,
    "IDPS":0,
    "INFORM":4.65,
    "FS":257000,
    "NUTRITION":277786,
    "HEALTH":300000,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":2.8,
    "VULNERABILITY":5.15,
    "COPINGCAPACITY":6.99,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"DJI",
    "PIN":140000,
    "TAR":250000,
    "COMMITTED":74085087,
    "FUNDED":20563729,
    "REFUGEES":24425,
    "IDPS":0,
    "INFORM":4.49,
    "FS":257000,
    "NUTRITION":277786,
    "HEALTH":300000,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":6.76,
    "VULNERABILITY":4.81,
    "COPINGCAPACITY":2.79,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2011,
    "NAME":"ERI",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":4.75,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":2,
    "VULNERABILITY":6.76,
    "COPINGCAPACITY":7.92,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2012,
    "NAME":"ERI",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":4.84,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":2.22,
    "VULNERABILITY":6.34,
    "COPINGCAPACITY":8.04,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2013,
    "NAME":"ERI",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":4.7,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":2.1,
    "VULNERABILITY":6.23,
    "COPINGCAPACITY":7.94,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2014,
    "NAME":"ERI",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":2902,
    "IDPS":null,
    "INFORM":4.67,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":2.18,
    "VULNERABILITY":6.01,
    "COPINGCAPACITY":7.77,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2015,
    "NAME":"ERI",
    "PIN":900000,
    "TAR":900000,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":2902,
    "IDPS":null,
    "INFORM":4.62,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":7.75,
    "VULNERABILITY":5.75,
    "COPINGCAPACITY":2.22,
    "PRIORITIES":"Basic Social Services, national capacity development, food security and sustainable livelihoods, environment sustainability, gender equity and women advancement."
  },
  {
    "YEAR":2011,
    "NAME":"ETH",
    "PIN":3500000,
    "TAR":3500000,
    "COMMITTED":454400000,
    "FUNDED":290600000,
    "REFUGEES":254905,
    "IDPS":325000,
    "INFORM":6.74,
    "FS":3500000,
    "NUTRITION":3500000,
    "HEALTH":0,
    "WASH":4000000,
    "EDUCATION":0,
    "HAZARDS":5.8,
    "VULNERABILITY":6.43,
    "COPINGCAPACITY":8.19,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"ETH",
    "PIN":3900000,
    "TAR":3900000,
    "COMMITTED":189400000,
    "FUNDED":133700000,
    "REFUGEES":367000,
    "IDPS":350000,
    "INFORM":6.55,
    "FS":3900000,
    "NUTRITION":3900000,
    "HEALTH":0,
    "WASH":4239188,
    "EDUCATION":0,
    "HAZARDS":5.25,
    "VULNERABILITY":6.6,
    "COPINGCAPACITY":8.12,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"ETH",
    "PIN":3900000,
    "TAR":3900000,
    "COMMITTED":205000000,
    "FUNDED":183500000,
    "REFUGEES":423851,
    "IDPS":416315,
    "INFORM":6.49,
    "FS":3900000,
    "NUTRITION":3900000,
    "HEALTH":0,
    "WASH":3300000,
    "EDUCATION":0,
    "HAZARDS":5.34,
    "VULNERABILITY":6.41,
    "COPINGCAPACITY":7.99,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"ETH",
    "PIN":2736490,
    "TAR":2736490,
    "COMMITTED":451900000,
    "FUNDED":271140000,
    "REFUGEES":660987,
    "IDPS":834959,
    "INFORM":6.58,
    "FS":2736490,
    "NUTRITION":264298,
    "HEALTH":6800000,
    "WASH":2750000,
    "EDUCATION":522799,
    "HAZARDS":5.32,
    "VULNERABILITY":6.43,
    "COPINGCAPACITY":8.33,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"ETH",
    "PIN":2900000,
    "TAR":2900000,
    "COMMITTED":344922157,
    "FUNDED":0,
    "REFUGEES":682761,
    "IDPS":505150,
    "INFORM":6.41,
    "FS":3200000,
    "NUTRITION":2400000,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":7.71,
    "VULNERABILITY":6.4,
    "COPINGCAPACITY":5.34,
    "PRIORITIES":"Sustainable economic growth, risk reduction, basic social services, governance and capacity development, women, youth and children."
  },
  {
    "YEAR":2011,
    "NAME":"KEN",
    "PIN":3750000,
    "TAR":3750000,
    "COMMITTED":741818150,
    "FUNDED":528690146,
    "REFUGEES":557340,
    "IDPS":309200,
    "INFORM":6.11,
    "FS":3750000,
    "NUTRITION":475000,
    "HEALTH":7500000,
    "WASH":2880000,
    "EDUCATION":1707000,
    "HAZARDS":5.16,
    "VULNERABILITY":6.15,
    "COPINGCAPACITY":7.21,
    "PRIORITIES":"2011 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"KEN",
    "PIN":2100000,
    "TAR":2100000,
    "COMMITTED":795005122,
    "FUNDED":411119116,
    "REFUGEES":586068,
    "IDPS":309200,
    "INFORM":6.31,
    "FS":2200000,
    "NUTRITION":362000,
    "HEALTH":3200000,
    "WASH":3380000,
    "EDUCATION":1555000,
    "HAZARDS":5.13,
    "VULNERABILITY":6.83,
    "COPINGCAPACITY":7.16,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"KEN",
    "PIN":1700000,
    "TAR":1700000,
    "COMMITTED":69982984,
    "FUNDED":24753575,
    "REFUGEES":530959,
    "IDPS":309200,
    "INFORM":6.2,
    "FS":2100000,
    "NUTRITION":2999937,
    "HEALTH":5000000,
    "WASH":4500000,
    "EDUCATION":566217,
    "HAZARDS":5.78,
    "VULNERABILITY":6.72,
    "COPINGCAPACITY":6.13,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"KEN",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":551352,
    "IDPS":309200,
    "INFORM":6.09,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":5.78,
    "VULNERABILITY":6.53,
    "COPINGCAPACITY":5.97,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"KEN",
    "PIN":1500000,
    "TAR":1500000,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":549649,
    "IDPS":309200,
    "INFORM":6.21,
    "FS":1500000,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":6.57,
    "VULNERABILITY":6.32,
    "COPINGCAPACITY":5.78,
    "PRIORITIES":"Transformational governance, human capital development, inclusive and sustainable economic growth, environmental sustainability, land management and human security."
  },
  {
    "YEAR":2011,
    "NAME":"SDN",
    "PIN":7071000,
    "TAR":7071000,
    "COMMITTED":1132952016,
    "FUNDED":741484812,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":7.81,
    "FS":7071000,
    "NUTRITION":7997190,
    "HEALTH":11544400,
    "WASH":0,
    "EDUCATION":8926000,
    "HAZARDS":6.99,
    "VULNERABILITY":8.31,
    "COPINGCAPACITY":8.18,
    "PRIORITIES":"2011 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"SDN",
    "PIN":7000807,
    "TAR":7000807,
    "COMMITTED":1052446405,
    "FUNDED":505676232,
    "REFUGEES":142000,
    "IDPS":1765000,
    "INFORM":7.72,
    "FS":7000807,
    "NUTRITION":4420000,
    "HEALTH":11058279,
    "WASH":0,
    "EDUCATION":8346329,
    "HAZARDS":7.3,
    "VULNERABILITY":7.78,
    "COPINGCAPACITY":8.09,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"SDN",
    "PIN":7236500,
    "TAR":4000000,
    "COMMITTED":985120878,
    "FUNDED":549458369,
    "REFUGEES":163900,
    "IDPS":2900000,
    "INFORM":7.58,
    "FS":7236500,
    "NUTRITION":5078153,
    "HEALTH":6059692,
    "WASH":0,
    "EDUCATION":3080159,
    "HAZARDS":7.29,
    "VULNERABILITY":7.6,
    "COPINGCAPACITY":7.84,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"SDN",
    "PIN":6100000,
    "TAR":6100000,
    "COMMITTED":985696822,
    "FUNDED":549652696,
    "REFUGEES":287709,
    "IDPS":3100000,
    "INFORM":7.54,
    "FS":6100000,
    "NUTRITION":4600000,
    "HEALTH":6100000,
    "WASH":1258204,
    "EDUCATION":2700000,
    "HAZARDS":7.29,
    "VULNERABILITY":7.42,
    "COPINGCAPACITY":7.93,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"SDN",
    "PIN":6100000,
    "TAR":5400000,
    "COMMITTED":1035894093,
    "FUNDED":278544625,
    "REFUGEES":229226,
    "IDPS":3100000,
    "INFORM":7.24,
    "FS":3500000,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":7.26,
    "VULNERABILITY":7.18,
    "COPINGCAPACITY":7.29,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2011,
    "NAME":"SOM",
    "PIN":3200000,
    "TAR":3200000,
    "COMMITTED":1003322063,
    "FUNDED":868139570,
    "REFUGEES":2124,
    "IDPS":1460000,
    "INFORM":8.95,
    "FS":3200000,
    "NUTRITION":460893,
    "HEALTH":1934000,
    "WASH":210000,
    "EDUCATION":460000,
    "HAZARDS":8.64,
    "VULNERABILITY":8.72,
    "COPINGCAPACITY":9.52,
    "PRIORITIES":"2011 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"SOM",
    "PIN":4097000,
    "TAR":4097000,
    "COMMITTED":1164634356,
    "FUNDED":589872503,
    "REFUGEES":2128,
    "IDPS":1360000,
    "INFORM":9.01,
    "FS":4097000,
    "NUTRITION":834800,
    "HEALTH":4000000,
    "WASH":206000,
    "EDUCATION":1800000,
    "HAZARDS":8.64,
    "VULNERABILITY":8.93,
    "COPINGCAPACITY":9.49,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"SOM",
    "PIN":3800000,
    "TAR":3800000,
    "COMMITTED":1153087668,
    "FUNDED":585736464,
    "REFUGEES":2339,
    "IDPS":1106000,
    "INFORM":8.97,
    "FS":4748000,
    "NUTRITION":1944500,
    "HEALTH":7770000,
    "WASH":400000,
    "EDUCATION":848000,
    "HAZARDS":8.64,
    "VULNERABILITY":8.79,
    "COPINGCAPACITY":9.5,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"SOM",
    "PIN":3180000,
    "TAR":2000000,
    "COMMITTED":933070303,
    "FUNDED":458027750,
    "REFUGEES":2669,
    "IDPS":1106751,
    "INFORM":9.01,
    "FS":3170000,
    "NUTRITION":756000,
    "HEALTH":3170000,
    "WASH":300000,
    "EDUCATION":1740000,
    "HAZARDS":8.63,
    "VULNERABILITY":8.85,
    "COPINGCAPACITY":9.57,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"SOM",
    "PIN":3200000,
    "TAR":2760000,
    "COMMITTED":862579628,
    "FUNDED":99555616,
    "REFUGEES":2742,
    "IDPS":1110000,
    "INFORM":8.83,
    "FS":3000000,
    "NUTRITION":1300000,
    "HEALTH":3200000,
    "WASH":300000,
    "EDUCATION":1700000,
    "HAZARDS":9.55,
    "VULNERABILITY":8.36,
    "COPINGCAPACITY":8.63,
    "PRIORITIES":"Inclusive politics, security, justice, economic foundations, revenue and services"
  },
  {
    "YEAR":2011,
    "NAME":"SSD",
    "PIN":2550000,
    "TAR":2550000,
    "COMMITTED":619673235,
    "FUNDED":377760780,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":7.81,
    "FS":2550000,
    "NUTRITION":827551,
    "HEALTH":3304197,
    "WASH":0,
    "EDUCATION":754616,
    "HAZARDS":6.99,
    "VULNERABILITY":8.31,
    "COPINGCAPACITY":8.18,
    "PRIORITIES":"2011 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"SSD",
    "PIN":4700000,
    "TAR":4700000,
    "COMMITTED":1156130815,
    "FUNDED":570658539,
    "REFUGEES":207492,
    "IDPS":170000,
    "INFORM":7.72,
    "FS":4700000,
    "NUTRITION":1194876,
    "HEALTH":3587318,
    "WASH":0,
    "EDUCATION":463707,
    "HAZARDS":7.3,
    "VULNERABILITY":7.78,
    "COPINGCAPACITY":8.09,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"SSD",
    "PIN":4500000,
    "TAR":3000000,
    "COMMITTED":1072037430,
    "FUNDED":773745283,
    "REFUGEES":224930,
    "IDPS":159134,
    "INFORM":6.96,
    "FS":4100000,
    "NUTRITION":3700000,
    "HEALTH":3500000,
    "WASH":0,
    "EDUCATION":255000,
    "HAZARDS":6.96,
    "VULNERABILITY":6.41,
    "COPINGCAPACITY":7.56,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"SSD",
    "PIN":11600000,
    "TAR":11600000,
    "COMMITTED":1801753424,
    "FUNDED":1435985168,
    "REFUGEES":248152,
    "IDPS":1504768,
    "INFORM":7.7,
    "FS":4300000,
    "NUTRITION":3600000,
    "HEALTH":5800000,
    "WASH":0,
    "EDUCATION":993300,
    "HAZARDS":6.96,
    "VULNERABILITY":7.47,
    "COPINGCAPACITY":8.77,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"SSD",
    "PIN":6400000,
    "TAR":551000,
    "COMMITTED":1807069154,
    "FUNDED":378473656,
    "REFUGEES":259232,
    "IDPS":1500000,
    "INFORM":7.83,
    "FS":6381900,
    "NUTRITION":3142500,
    "HEALTH":6375100,
    "WASH":6400000,
    "EDUCATION":1732000,
    "HAZARDS":8.92,
    "VULNERABILITY":7.72,
    "COPINGCAPACITY":6.96,
    "PRIORITIES":"Not Available"
  },
  {
    "YEAR":2011,
    "NAME":"UGA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":133115,
    "IDPS":73239,
    "INFORM":5.74,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":3.78,
    "VULNERABILITY":6.59,
    "COPINGCAPACITY":7.57,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2012,
    "NAME":"UGA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":172923,
    "IDPS":30136,
    "INFORM":6.28,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":5.43,
    "VULNERABILITY":6.09,
    "COPINGCAPACITY":7.49,
    "PRIORITIES":"2012 Data not Available"
  },
  {
    "YEAR":2013,
    "NAME":"UGA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":206985,
    "IDPS":30136,
    "INFORM":5.5,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":3.63,
    "VULNERABILITY":6.06,
    "COPINGCAPACITY":7.58,
    "PRIORITIES":"2013 Data not Available"
  },
  {
    "YEAR":2014,
    "NAME":"UGA",
    "PIN":452523,
    "TAR":452523,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":422435,
    "IDPS":30136,
    "INFORM":6.41,
    "FS":0,
    "NUTRITION":452523,
    "HEALTH":90000,
    "WASH":null,
    "EDUCATION":20000,
    "HAZARDS":6.16,
    "VULNERABILITY":5.98,
    "COPINGCAPACITY":7.16,
    "PRIORITIES":"2014 Data not Available"
  },
  {
    "YEAR":2015,
    "NAME":"UGA",
    "PIN":23000,
    "TAR":23000,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":433029,
    "IDPS":30136,
    "INFORM":6.41,
    "FS":0,
    "NUTRITION":23000,
    "HEALTH":30000,
    "WASH":0,
    "EDUCATION":100000,
    "HAZARDS":7.15,
    "VULNERABILITY":5.99,
    "COPINGCAPACITY":6.16,
    "PRIORITIES":"Governance and human rights, sustainable livelihoods, quality social services."
  },
  {
    "YEAR":2011,
    "NAME":"RWA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0,
    "VULNERABILITY":0,
    "COPINGCAPACITY":null,
    "PRIORITIES":""
  },
  {
    "YEAR":2012,
    "NAME":"RWA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0,
    "VULNERABILITY":0,
    "COPINGCAPACITY":null,
    "PRIORITIES":""
  },
  {
    "YEAR":2013,
    "NAME":"RWA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":0,
    "IDPS":0,
    "INFORM":0,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0,
    "VULNERABILITY":0,
    "COPINGCAPACITY":null,
    "PRIORITIES":""
  },
  {
    "YEAR":2014,
    "NAME":"RWA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":74337,
    "IDPS":0,
    "INFORM":0,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0,
    "VULNERABILITY":0,
    "COPINGCAPACITY":null,
    "PRIORITIES":""
  },
  {
    "YEAR":2015,
    "NAME":"RWA",
    "PIN":0,
    "TAR":0,
    "COMMITTED":0,
    "FUNDED":0,
    "REFUGEES":74485,
    "IDPS":0,
    "INFORM":0,
    "FS":0,
    "NUTRITION":0,
    "HEALTH":0,
    "WASH":0,
    "EDUCATION":0,
    "HAZARDS":0,
    "VULNERABILITY":0,
    "COPINGCAPACITY":null,
    "PRIORITIES":""
  }
];
var tempGeo = {
    "type": "FeatureCollection",
    "features": [
            {"type":"Feature","id":"DJI","properties":{"id":"DJI","name":"Djibouti", "adm1_code": "1"},"geometry":{"type":"Polygon","coordinates":[[[43.081226,12.699639],[43.317852,12.390148],[43.286381,11.974928],[42.715874,11.735641],[43.145305,11.46204],[42.776852,10.926879],[42.55493,11.10511],[42.31414,11.0342],[41.75557,11.05091],[41.73959,11.35511],[41.66176,11.6312],[42,12.1],[42.35156,12.54223],[42.779642,12.455416],[43.081226,12.699639]]]}},
            {"type":"Feature","id":"ETH","properties":{"id":"ETH","name":"Ethiopia", "adm1_code": "2"},"geometry":{"type":"Polygon","coordinates":[[[42.35156,12.54223],[42,12.1],[41.66176,11.6312],[41.73959,11.35511],[41.75557,11.05091],[42.31414,11.0342],[42.55493,11.10511],[42.776852,10.926879],[42.55876,10.57258],[42.92812,10.02194],[43.29699,9.54048],[43.67875,9.18358],[46.94834,7.99688],[47.78942,8.003],[44.9636,5.00162],[43.66087,4.95755],[42.76967,4.25259],[42.12861,4.23413],[41.855083,3.918912],[41.1718,3.91909],[40.76848,4.25702],[39.85494,3.83879],[39.559384,3.42206],[38.89251,3.50074],[38.67114,3.61607],[38.43697,3.58851],[38.120915,3.598605],[36.855093,4.447864],[36.159079,4.447864],[35.817448,4.776966],[35.817448,5.338232],[35.298007,5.506],[34.70702,6.59422],[34.25032,6.82607],[34.0751,7.22595],[33.56829,7.71334],[32.95418,7.78497],[33.2948,8.35458],[33.8255,8.37916],[33.97498,8.68456],[33.96162,9.58358],[34.25745,10.63009],[34.73115,10.91017],[34.83163,11.31896],[35.26049,12.08286],[35.86363,12.57828],[36.27022,13.56333],[36.42951,14.42211],[37.59377,14.2131],[37.90607,14.95943],[38.51295,14.50547],[39.0994,14.74064],[39.34061,14.53155],[40.02625,14.51959],[40.8966,14.11864],[41.1552,13.77333],[41.59856,13.45209],[42.00975,12.86582],[42.35156,12.54223]]]}},
            {"type":"Feature","id":"KEN","properties":{"id":"KEN","name":"Kenya", "adm1_code": "3"},"geometry":{"type":"Polygon","coordinates":[[[40.993,-0.85829],[41.58513,-1.68325],[40.88477,-2.08255],[40.63785,-2.49979],[40.26304,-2.57309],[40.12119,-3.27768],[39.80006,-3.68116],[39.60489,-4.34653],[39.20222,-4.67677],[37.7669,-3.67712],[37.69869,-3.09699],[34.07262,-1.05982],[33.903711,-0.95],[33.893569,0.109814],[34.18,0.515],[34.6721,1.17694],[35.03599,1.90584],[34.59607,3.05374],[34.47913,3.5556],[34.005,4.249885],[34.620196,4.847123],[35.298007,5.506],[35.817448,5.338232],[35.817448,4.776966],[36.159079,4.447864],[36.855093,4.447864],[38.120915,3.598605],[38.43697,3.58851],[38.67114,3.61607],[38.89251,3.50074],[39.559384,3.42206],[39.85494,3.83879],[40.76848,4.25702],[41.1718,3.91909],[41.855083,3.918912],[40.98105,2.78452],[40.993,-0.85829]]]}},
            {"type":"Feature","id":"SDN","properties":{"id":"SDN","name":"Sudan", "adm1_code": "4"},"geometry":{"type":"Polygon","coordinates":[[[33.963393,9.464285],[33.824963,9.484061],[33.842131,9.981915],[33.721959,10.325262],[33.206938,10.720112],[33.086766,11.441141],[33.206938,12.179338],[32.743419,12.248008],[32.67475,12.024832],[32.073892,11.97333],[32.314235,11.681484],[32.400072,11.080626],[31.850716,10.531271],[31.352862,9.810241],[30.837841,9.707237],[29.996639,10.290927],[29.618957,10.084919],[29.515953,9.793074],[29.000932,9.604232],[28.966597,9.398224],[27.97089,9.398224],[27.833551,9.604232],[27.112521,9.638567],[26.752006,9.466893],[26.477328,9.55273],[25.962307,10.136421],[25.790633,10.411099],[25.069604,10.27376],[24.794926,9.810241],[24.537415,8.917538],[24.194068,8.728696],[23.88698,8.61973],[23.805813,8.666319],[23.459013,8.954286],[23.394779,9.265068],[23.55725,9.681218],[23.554304,10.089255],[22.977544,10.714463],[22.864165,11.142395],[22.87622,11.38461],[22.50869,11.67936],[22.49762,12.26024],[22.28801,12.64605],[21.93681,12.58818],[22.03759,12.95546],[22.29658,13.37232],[22.18329,13.78648],[22.51202,14.09318],[22.30351,14.32682],[22.56795,14.94429],[23.02459,15.68072],[23.88689,15.61084],[23.83766,19.58047],[23.85,20],[25,20.00304],[25,22],[29.02,22],[32.9,22],[36.86623,22],[37.18872,21.01885],[36.96941,20.83744],[37.1147,19.80796],[37.48179,18.61409],[37.86276,18.36786],[38.41009,17.998307],[37.904,17.42754],[37.16747,17.26314],[36.85253,16.95655],[36.75389,16.29186],[36.32322,14.82249],[36.42951,14.42211],[36.27022,13.56333],[35.86363,12.57828],[35.26049,12.08286],[34.83163,11.31896],[34.73115,10.91017],[34.25745,10.63009],[33.96162,9.58358],[33.963393,9.464285]]]}},
            {"type":"Feature","id":"SOM","properties":{"id":"SOM","name":"Somalia", "adm1_code": "5"},"geometry":{"type":"Polygon","coordinates":[[[47.78942,8.003],[46.948328,7.996877],[43.67875,9.18358],[43.296975,9.540477],[42.92812,10.02194],[42.55876,10.57258],[42.776852,10.926879],[43.145305,11.46204],[43.47066,11.27771],[43.666668,10.864169],[44.117804,10.445538],[44.614259,10.442205],[45.556941,10.698029],[46.645401,10.816549],[47.525658,11.127228],[48.021596,11.193064],[48.378784,11.375482],[48.948206,11.410622],[48.942005,11.394266],[48.948205,11.410617],[49.26776,11.43033],[49.72862,11.5789],[50.25878,11.67957],[50.73202,12.0219],[51.1112,12.02464],[51.13387,11.74815],[51.04153,11.16651],[51.04531,10.6409],[50.83418,10.27972],[50.55239,9.19874],[50.07092,8.08173],[49.4527,6.80466],[48.59455,5.33911],[47.74079,4.2194],[46.56476,2.85529],[45.56399,2.04576],[44.06815,1.05283],[43.13597,0.2922],[42.04157,-0.91916],[41.81095,-1.44647],[41.58513,-1.68325],[40.993,-0.85829],[40.98105,2.78452],[41.855083,3.918912],[42.12861,4.23413],[42.76967,4.25259],[43.66087,4.95755],[44.9636,5.00162],[47.78942,8.003]]]}},
            {"type":"Feature","id":"SSD","properties":{"id":"SSD","name":"South Sudan", "adm1_code": "6"},"geometry":{"type":"Polygon","coordinates":[[[33.963393,9.464285],[33.97498,8.68456],[33.8255,8.37916],[33.2948,8.35458],[32.95418,7.78497],[33.56829,7.71334],[34.0751,7.22595],[34.25032,6.82607],[34.70702,6.59422],[35.298007,5.506],[34.620196,4.847123],[34.005,4.249885],[33.39,3.79],[32.68642,3.79232],[31.88145,3.55827],[31.24556,3.7819],[30.83385,3.50917],[29.95349,4.1737],[29.715995,4.600805],[29.159078,4.389267],[28.696678,4.455077],[28.428994,4.287155],[27.979977,4.408413],[27.374226,5.233944],[27.213409,5.550953],[26.465909,5.946717],[26.213418,6.546603],[25.796648,6.979316],[25.124131,7.500085],[25.114932,7.825104],[24.567369,8.229188],[23.88698,8.61973],[24.194068,8.728696],[24.537415,8.917538],[24.794926,9.810241],[25.069604,10.27376],[25.790633,10.411099],[25.962307,10.136421],[26.477328,9.55273],[26.752006,9.466893],[27.112521,9.638567],[27.833551,9.604232],[27.97089,9.398224],[28.966597,9.398224],[29.000932,9.604232],[29.515953,9.793074],[29.618957,10.084919],[29.996639,10.290927],[30.837841,9.707237],[31.352862,9.810241],[31.850716,10.531271],[32.400072,11.080626],[32.314235,11.681484],[32.073892,11.97333],[32.67475,12.024832],[32.743419,12.248008],[33.206938,12.179338],[33.086766,11.441141],[33.206938,10.720112],[33.721959,10.325262],[33.842131,9.981915],[33.824963,9.484061],[33.963393,9.464285]]]}},
            {"type":"Feature","id":"RWA","properties":{"id":"RWA","name":"Rwanda", "adm1_code": "8"},"geometry":{"type":"Polygon","coordinates":[[[30.419105,-1.134659],[30.816135,-1.698914],[30.758309,-2.28725],[30.469696,-2.413858],[29.938359,-2.348487],[29.632176,-2.917858],[29.024926,-2.839258],[29.117479,-2.292211],[29.254835,-2.21511],[29.291887,-1.620056],[29.579466,-1.341313],[29.821519,-1.443322],[30.419105,-1.134659]]]}},
            {"type":"Feature","id":"BRN","properties":{"id":"BRN","name":"Burundi", "adm1_code": "9"},"geometry":{"type":"Polygon","coordinates":[[[29.024926,-2.839258],[29.632176,-2.917858],[29.938359,-2.348487],[30.469696,-2.413858],[30.527677,-2.807632],[30.743013,-3.034285],[30.752263,-3.35933],[30.50556,-3.568567],[30.116333,-4.090138],[29.753512,-4.452389],[29.339998,-4.499983],[29.276384,-3.293907],[29.024926,-2.839258]]]}},
            {"type":"Feature","id":"ERI","properties":{"id":"ERI","name":"Eritrea", "adm1_code": "10"},"geometry":{"type":"Polygon","coordinates":[[[42.35156,12.54223],[42.00975,12.86582],[41.59856,13.45209],[41.155194,13.77332],[40.8966,14.11864],[40.026219,14.519579],[39.34061,14.53155],[39.0994,14.74064],[38.51295,14.50547],[37.90607,14.95943],[37.59377,14.2131],[36.42951,14.42211],[36.323189,14.822481],[36.75386,16.291874],[36.85253,16.95655],[37.16747,17.26314],[37.904,17.42754],[38.41009,17.998307],[38.990623,16.840626],[39.26611,15.922723],[39.814294,15.435647],[41.179275,14.49108],[41.734952,13.921037],[42.276831,13.343992],[42.589576,13.000421],[43.081226,12.699639],[42.779642,12.455416],[42.35156,12.54223]]]}},
            {"type":"Feature","id":"UGA","properties":{"id":"UGA","name":"Uganda", "adm1_code": "7"},"geometry":{"type":"Polygon","coordinates":[[[31.86617,-1.02736],[30.76986,-1.01455],[30.419105,-1.134659],[29.821519,-1.443322],[29.579466,-1.341313],[29.587838,-0.587406],[29.8195,-0.2053],[29.875779,0.59738],[30.086154,1.062313],[30.468508,1.583805],[30.85267,1.849396],[31.174149,2.204465],[30.77332,2.33989],[30.83385,3.50917],[31.24556,3.7819],[31.88145,3.55827],[32.68642,3.79232],[33.39,3.79],[34.005,4.249885],[34.47913,3.5556],[34.59607,3.05374],[35.03599,1.90584],[34.6721,1.17694],[34.18,0.515],[33.893569,0.109814],[33.903711,-0.95],[31.86617,-1.02736]]]}}
        ]
};

$(document).ready(function(){
    generateROEADashboard(config, tempData, tempGeo);
});

//$.when(dataCall, geomCall).then(function(dataArgs, geomArgs){
//    generateROEADashboard(config,dataArgs[0],geomArgs[0]);
//});