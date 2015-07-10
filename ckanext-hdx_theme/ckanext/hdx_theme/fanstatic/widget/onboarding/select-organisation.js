$(document).ready(function(){
    var url = "/api/action/organization_list?package_count=true&include_extras=false&all_fields=true&sort=name asc";
    $.getJSON(url, {}, function(result){
        if (result.success){
            $.each(result.result, function(idx, el){
                $('#existing-org-selector').append("<option value='"+ el.id +"'>"+ el.title +"</option>");
            });
            $('#existing-org-selector').select2();
        }
    })
});