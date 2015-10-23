$(document).ready(function() {
    bindOrderChange();
});

function bindOrderChange(){
    var dropdown = $(".dropdown.orderDropdown");
    dropdown.on('click', 'li a', function(){
        var $this = $(this);
        var value = $this.attr("val");
        var url = replaceParam('sort', value);

        var additional = "";
        var additionalValue = dropdown.attr("data-module-additional");
        if (additionalValue != undefined)
            additional = additionalValue;
        window.location.href = url + additional;

    });
}

function replaceParam(key, value){
    var pathname = window.location.pathname;
    var params = toParams(window.location.search);
    // Handle corruption of the query
    $.each(params, function(k,v){
        //reset page on resort
        if(k == 'page'){
            params[k] = 1
        }
    });
    params[key] = value;
    var parameters = decodeURIComponent(jQuery.param(params, true));
    var ret = pathname + "?" + parameters;
    return ret;
}

function toParams(searchUrl) {
    var result = {};
    if(searchUrl == '')
        return result;

    searchUrl = decodeURIComponent(searchUrl);

    var queryString = searchUrl.substr(1);
    var params = queryString.split("&");

    jQuery.each(params, function(index, param){
        var keyPair = param.split("=");

        var key = keyPair[0];
        var value = keyPair[1];

        if(result[key] == undefined)
            result[key] = value
        else{
            if(result[key] instanceof Array) //current var is an array just push another to it
                result[key].push(value)
            else{ //duplicate var, then it must store as an array
                result[key] = [result[key]]
                result[key].push(value)
            }
        }
    });
    return result;
}