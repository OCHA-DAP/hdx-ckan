$(document).ready(function(){
    $(".list-header-filters select.filter-item").each(function(index, el){
        var $el = $(el);
        var title = $el.attr("title");
        $el.multipleSelect({
            placeholder: title,
            allSelected: title + "(all)",
            minumimCountSelected: 0,
            countSelected: title + '(#)',
            multipleWidth: 225,
            filter: true
        });
    });

    $(".list-header-filters .checkbox-filter").change(function(){
        determineEnabled(this);
    });

    $(".list-header-filters .checkbox-filter:checked").each(function(){
        determineEnabled(this);
    });

    //$(".list-header-filters select.filter-item").attr("style", "");

});

function determineEnabled(origin){
    $(".list-header-filters .checkbox-filter").each(function(idx, el){
        $el = $(el);
        if (el != origin){
            $el.prop("disabled", origin.checked);
        }
    });

}