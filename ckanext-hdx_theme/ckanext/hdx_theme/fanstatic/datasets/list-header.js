function updateFilters(){
    var filtersActions = $(".list-header-filters .filters-actions .loading-div");
    filtersActions.addClass("loading");
    var url = getFilterUrl(true);
    var data = null;
    $.getJSON(url, data, function(data){
        var results = 0;
        if (data){
            results = data.num_of_total_items;
            for (var facetId in data.facets){
                var facet = data.facets[facetId];
                var facetDiv = $(".list-header-filters select[name='"+facetId+"']");
                var newHtml = "";
                for (var itemIdx in facet.items){
                    var item = facet.items[itemIdx];
                    newHtml +="<option value='"+ item.name +"'";
                    if (item.selected === true)
                        newHtml += " selected='selected'";
                    newHtml += " count='"+ item.count +"'";
                    newHtml += "> " + item.display_name;
                    newHtml += "</option>";
                }
                facetDiv.html(newHtml);
            }
        }
        $(".list-header-filters .filter-item").multipleSelect('refresh');
        $(".list-header-filters .filters-actions .filter-results-number").text(results);
        var filterResults = $(".list-header-filters .filters-actions");
        if (results == 0)
            filterResults.addClass("error");
        else
            filterResults.removeClass("error");

        filtersActions.removeClass("loading");

    });
}

function getFilterUrl(onlyFilter) {
    var params = $("select.filter-item").serialize();
    $("input.checkbox-filter:checked").each(function (idx, el) {
        if (params !== "") {
            params += "&";
        }
        params += $(el).attr("name");
        params += "=1";
    });
    if (onlyFilter){
        if (params !== ""){
            params += "&";
        }
        params += "ext_only_facets=true";
    }

    var base = $("#base-filter-location").text().trim();
    return base + "?" + params;
}
function determineEnabledFirstTime(reset) {
    if (reset){
        $(".list-header-filters .checkbox-filter").prop("disabled", false);
    }
    $(".list-header-filters .checkbox-filter:checked").each(function () {
        determineEnabled(this);
    });
}
$(document).ready(function(){
    $(".list-header-filters select.filter-item").each(function(index, el){
        var $el = $(el);
        var title = $el.attr("title");
        $el.multipleSelect({
            placeholder: title,
            selectAll: false, //no point since we're using and "AND" filter
            allSelected: null,
            minumimCountSelected: 0,
            countSelected: title + '(#/%)',
            multipleWidth: 225,
            filter: true,
            onClick: function(view){
                console.log(">>>" + view.label + '(' + view.value + ') ' +
                    (view.checked ? 'checked' : 'unchecked'));
                updateFilters();
            }
        });
    });

    $(".list-header-filters .checkbox-filter").change(function(){
        determineEnabled(this);
        updateFilters();
    });

    $(".filter-pagination a").on("click", function(){
        var $this = $(this);
        var value = $this.text();
        window.location.href = replaceParam("ext_page_size", value);
    });

    determineEnabledFirstTime();

    //$(".list-header-filters select.filter-item").attr("style", "");
    $(".list-header-filters form").submit(function(event){
        //
        var $this = $(this);

        var url = getFilterUrl(false);
        event.preventDefault();
        window.location = url;
    });
    $(".list-header-filters a.reset-action").click(function(){
        $(this).closest("form").resetForm();
        $(this).closest("form").find('select').each(function(idx, el){
            $el = $(el);
            var name = $el.attr("name");
            name += "_initial_values";
            var html = $el.siblings("div[name='"+name+"']").html();
            $el.html(html);
        });
        updateFilters();
        determineEnabledFirstTime(true);
        return false;
    });

    $(".list-header-filters a.main-action").click(function(){
        $(this).closest("form").submit();
    });
});

function determineEnabled(origin){
    $(".list-header-filters .checkbox-filter").each(function(idx, el){
        $el = $(el);
        if (el != origin){
            $el.prop("disabled", origin.checked);
        }
    });

}