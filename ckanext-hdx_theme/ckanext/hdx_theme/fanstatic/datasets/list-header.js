$(document).ready(function() {
    var LS_FILTER_CONFIG = "/search:filterConfig";
    var filterConfig = window.localStorage.getItem(LS_FILTER_CONFIG);
    if (!filterConfig) {
        filterConfig = {
            showFilter: true,
            facets: {
                featured: true,
                organisations: true,
                locations: true,
                tags: true,
                formats: true,
                licenses: true
            }
        };
        window.localStorage.setItem(LS_FILTER_CONFIG, JSON.stringify(filterConfig));
    } else {
        filterConfig = JSON.parse(filterConfig);
    }

    $(".filter-category .categ-title").on("click", function() {
        $(this).siblings(".categ-content").toggle();
        var glyph = $(this).find("i.glyphicon");
        glyph.toggleClass("glyphicon-minus");
        glyph.toggleClass("glyphicon-plus");

        var facetName = $(this).attr("data-value");
        filterConfig.facets[facetName] = glyph.hasClass("glyphicon-minus");
        window.localStorage.setItem(LS_FILTER_CONFIG, JSON.stringify(filterConfig));
    });

    $(".filter-category .categ-actions .show-more").on("click", function() {
        $(this).children(".show-more-text").toggle();
        $(this).parents(".filter-category").find(".categ-list").toggleClass("show-all");
    });

    //prepare Lunr Index
    let categoryIndex = {};
    $(".filter-category").each((idx, el) => {
      if ($(el).find('.categ-search').length === 0) //only categs with search
        return;
      let category = $(el).find(".categ-title").attr('data-value');
      categoryIndex[category] = lunr(function () {
        this.field('title');
        this.ref('idx');

        let results = [];
        $(el).find(".categ-list .categ-items li input").each((idx, input) => {
          results.push({
            "idx": idx,
            "title": toNormalForm($(input).parent().text())
          });
        })
        results.forEach((v) => this.add(v));
      });
    })

    $(".filter-category .categ-search input").on("keyup", function() {
        let category = $(this).parents('.filter-category').find('.categ-title').attr('data-value');
        let index = categoryIndex[category];


        let searchVal = toNormalForm($(this).val()) + "*"; //added wildcard in
        let results = index.search(searchVal);
        let resultsIdx = results.map((el) => parseInt(el.ref));
        $(this).parents(".filter-category").find(".categ-items li").each((idx, el) => (resultsIdx.includes(idx) ? $(el).show() :$(el).hide()));
    });

    $(".filter-category .categ-items li input.parent-facet").on("change", function() {
      var childInputs = $(this).parent().find('li input');
      if(this.checked) {
        childInputs.prop('checked', true);
      } else {
        childInputs.prop('checked', false);
      }
      window.location = getFilterUrlNew(false);
    });

    $(".filter-category .categ-items li input").not(".parent-facet").on("change", function() {
        var location = getFilterUrlNew(false);
        console.log("Refresh to: " + location);
        window.location = location;
    });

    $("#headerSearch, .headerSearchBox").on("keydown", function(event){
        if (event.keyCode == '13'){
            var location = getFilterUrlNew(false);
            console.log("Refresh to: " + location);
            window.location = location;
            event.preventDefault();
        }
    });

    $("#search-page-filters .filter-clear").on("click", function(event) {
        event.stopPropagation();
        event.preventDefault();

        var location = getFilterUrlNew(true);
        console.log("Refresh to: " + location);
        window.location = location;
    });

    $(".filter-pagination input[type='radio']").click(function(){
        var location = getFilterUrlNew(false);
        console.log("Refresh to: " + location);
        window.location = location;
    });

    $("#show-filter-toggle").on("change", function(){
        filterConfig.showFilter = $(this).prop("checked");
        window.localStorage.setItem(LS_FILTER_CONFIG, JSON.stringify(filterConfig));

        $("#search-page-filters").toggle();
        var searchResults = $("#search-page-results");
        searchResults.toggleClass("col-xs-12");
        searchResults.toggleClass("col-xs-9");
    });

    if (!filterConfig.showFilter) {
        var toggleEl = $('#show-filter-toggle');
        toggleEl.prop("checked", false);
        toggleEl.change();
    }
    $.each(filterConfig.facets, function(key, val){
        if (!val){
            $(".filter-category .categ-title[data-value='"+ key +"']").click();
        }
    });

});

function getFilterUrlNew(resetFilters) {
    var params = "";
    if (!resetFilters){
        params = $(".filter-category .categ-items li input").not(".parent-facet").serialize();
        $("input.checkbox-filter:checked").each(function (idx, el) {
            if (params !== "") {
                params += "&";
            }
            params += $(el).attr("name");
            params += "=1";
        });
    }

    //check non filter params
    var params2 = $("#headerSearch:visible, #headerSearchMobile:visible, .filter-pagination input[name='ext_page_size'], #header-search-sort, " +
        "#ext_after_metadata_modified, #ext_batch").serialize();
    params += ((params !== "" && params2 != null) ? "&" : "") + params2;


    var base = $("#base-filter-location").text().trim();
    return base + ((params && params !== "") ? "?" + params : "") ;
}

//
// function updateFilters(forceApply){
//
//     if (forceApply){
//         //only for order by drop down and show N items
//         $("#dataset-filter-form").submit();
//             return;
//     }
//
//     $(".list-header-apply").show(500);
//
//     var filtersActions = $(".list-header-apply .loading-image");
//     filtersActions.addClass("loading");
//     var url = getFilterUrl(true);
//     var data = null;
//     $.getJSON(url, data, function(data){
//         var results = 0;
//         var indicators = 0;
//         var cods = 0;
//         if (data){
//             results = data.num_of_total_items;
//             indicators = data.num_of_indicators;
//             cods = data.num_of_cods;
//             for (var facetId in data.facets){
//                 var facet = data.facets[facetId];
//                 var facetDiv = $(".list-header-filters select[name='"+facetId+"']");
//                 var newHtml = "";
//                 for (var itemIdx in facet.items){
//                     var item = facet.items[itemIdx];
//                     newHtml +="<option value='"+ item.name +"'";
//                     if (item.selected === true)
//                         newHtml += " selected='selected'";
//                     newHtml += " count='"+ item.count +"'";
//                     newHtml += "> " + item.display_name;
//                     newHtml += "</option>";
//                 }
//                 facetDiv.html(newHtml);
//             }
//         }
//         // $("#show-cods").prop("disabled", cods == 0);
//         // $("#show-indicators").prop("disabled", indicators == 0);
//
//         $(".list-header-filters select.filter-item").multipleSelect('refresh');
//         $(".list-header-apply .filter-results-number").text(results);
//         var filterResults = $(".list-header-apply .filter-results");
//         if (results == 0)
//             filterResults.addClass("error");
//         else
//             filterResults.removeClass("error");
//
//         filtersActions.removeClass("loading");
//
//     });
// }
//
// function getFilterUrl(onlyFilter) {
//     var params = $(".list-header-filters .filter-item, #headerSearch, .filter-pagination input[name='ext_page_size'], #header-search-sort").serialize();
//     $("input.checkbox-filter:checked").each(function (idx, el) {
//         if (params !== "") {
//             params += "&";
//         }
//         params += $(el).attr("name");
//         params += "=1";
//     });
//     if (onlyFilter){
//         if (params !== ""){
//             params += "&";
//         }
//         params += "ext_only_facets=true";
//     }
//
//     var base = $("#base-filter-location").text().trim();
//     return base + "?" + params;
// }
// function determineEnabledFirstTime(reset) {
//     if (reset){
//         $(".list-header-filters .checkbox-filter").prop("disabled", false);
//     }
//     $(".list-header-filters .checkbox-filter:checked").each(function () {
//         determineEnabled(this);
//     });
// }
// $(document).ready(function(){
//     $(".list-header-filters select.filter-item").each(function(index, el){
//         var $el = $(el);
//         var title = $el.attr("title");
//         $el.multipleSelect({
//             placeholder: title,
//             selectAll: false, //no point since we're using and "AND" filter
//             allSelected: null,
//             minumimCountSelected: 0,
//             countSelected: title + '(#/%)',
//             multipleWidth: 225,
//             filter: true,
//             onClick: function(view){
//                 updateFilters();
//             }
//         });
//     });
//
//     $(".list-header-filters .checkbox-filter").change(function(){
//         // determineEnabled(this);
//         updateFilters();
//     });
//
//     $(".filter-pagination input").change(function(){
//         updateFilters(true);
//     });
//
//     var dropdown = $(".dropdown.orderDropdown li a");
//     dropdown.unbind('click');
//     dropdown.on('click', function(event){
//         var $this = $(this);
//         var value = $this.attr("val");
//         var text = $this.text();
//
//         $("#header-search-sort").val(value);
//         $("#header-search-sort ~ .dropdown-toggle-text").text(text);
//
//         updateFilters(true);
//         event.preventDefault();
//         return false;
//     });
//
//
//     // determineEnabledFirstTime();
//
//     //$(".list-header-filters select.filter-item").attr("style", "");
//     $("#headerSearch").change(function(){
//         updateFilters();
//     });
//
//     $("#dataset-filter-form").submit(function(){
//         //
//         var $this = $(this);
//
//         var url = getFilterUrl(false);
//         var filtersActions = $(".list-header-apply .loading-div");
//
//         if ((window.location.pathname + window.location.search) != url){
//             filtersActions.addClass("loading");
//             window.location.href = url + "#dataset-filter-start";
//         }
//         return false;
//     });
//     $(".list-header-apply a.reset-action").click(function(event){
//         $(this).closest("form").resetForm();
//         $(this).closest("form").find('select').each(function(idx, el){
//             $el = $(el);
//             var name = $el.attr("name");
//             name += "_initial_values";
//             var html = $el.siblings("div[name='"+name+"']").html();
//             $el.html(html);
//         });
//         $("#header-search-sort").val($("#header-search-sort_initial_values").val());
//         $("#header-search-sort ~ .dropdown-toggle-text").text($("#header-search-sort_initial_values").attr("label"));
//
//         updateFilters();
//         // determineEnabledFirstTime(true);
//         event.preventDefault();
//         $(".list-header-apply").hide(500);
//     });
//
//     $(".list-header-apply a.main-action").click(function(event){
//         $(this).closest("form").submit();
//         event.preventDefault();
//     });
// });
//
// function determineEnabled(origin){
//     $(".list-header-filters .checkbox-filter").each(function(idx, el){
//         $el = $(el);
//         if (el != origin){
//             $el.prop("disabled", origin.checked);
//         }
//     });
//
// }
