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
    $(".list-header-filters form").submit(function(event){
        //
        var $this = $(this);

        var params = $("select.filter-item").serialize();
        $("input.checkbox-filter:checked").each(function(idx, el){
            if (params !== ""){
                params += "&";
            }
            params += $(el).attr("name");
            params += "=1";
        });
        console.log(params);
        event.preventDefault();
        var base = $("#base-filter-location").text().trim();
        window.location = base + "?" + params;
    });
    $(".list-header-filters a.reset-action").click(function(){
        $(this).closest("form").resetForm();
        $(this).closest("form").find('select').multipleSelect('refresh');
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