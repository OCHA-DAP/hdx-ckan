$(document).ready(function(){
    var url = "/api/action/organization_list?package_count=true&include_extras=false&all_fields=true&sort=name asc";
    $.getJSON(url, {}, function(result){
        if (result.success){
            $.each(result.result, function(idx, el){
                $('#existing-org-selector').append("<option value='"+ el.id +"'>"+ el.title +"</option>");
            });
            $('#existing-org-selector').select2();
        }
    });

    $('#organisation-form-submit').on('click', function(){
        if ($('#select-organisation').is(':visible')){
            $('#select-organisation-form').submit();
        } else {
            if ($('#create-organisation').is(':visible')){
                $('#create-organisation-form').submit();
            }
        }
    });

    $('#select-organisation-form').on('submit', function(){
        $this = $(this);
        $.post('/user/request_membership', $this.serialize(), function(result_data){
            var result = JSON.stringify(result_data);
            if (result.success){
                closeCurrentWidget($this);showOnboardingWidget('#invitePopup');
            } else {
                alert("Can't join org: " + result.error.message);
            }
        });
    });

    $('#create-organisation-form').on('submit', function(){
        $this = $(this);
        $.post('/user/request_new_organization', $this.serialize(), function(result_data){
            var result = JSON.stringify(result_data);
            if (result.success){
                closeCurrentWidget($this);showOnboardingWidget('#invitePopup');
            } else {
                alert("Can't create org: " + result.error.message);
            }
        })
    });

});