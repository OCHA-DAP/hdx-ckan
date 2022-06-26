$(document).ready(function(){
    // var url = "/api/action/organization_list?package_count=true&include_extras=false&all_fields=true&sort=name asc";
    var url = "/api/action/cached_organization_list";

    $.getJSON(url, {}, function(result){
        if (result.success){
            $.each(result.result, function(idx, el){
                if (el.request_membership !== "false") {
                    $('#existing-org-selector').append("<option value='"+ el.id +"'>"+ hdxUtil.text.sanitize(el.title) +"</option>");
                }
            });
            $('#existing-org-selector').select2();
        }
    });
    $('#org-type-selector').select2();


    $('#select-organisation-form').on('submit', function(){
        $this = $(this);
        $.post('/user/request_membership', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            $sel = $($("#select-organisation-form .select2-container.mTop20.required").find("a:first"));
            $sel.css("border", "");
            if (result.success){
                closeCurrentWidget($this);
                let skipNext = false;
                if ($this.attr('skipNext') === 'true') {
                  $this.removeAttr('skipNext');
                  skipNext = true;
                }
                if (!skipNext) {
                  $('#select-organisation-form')[0].reset();
                  showOnboardingWidget('#invitePopup');
                }
            } else {
                alert("Can't join org: " + result.error.message);
                $sel.css("border", "1px solid red");
            }
        });
        return false;
    });

    $('#create-organisation-form').on('submit', function(){
        $this = $(this);
        $.post('/user/request_new_organization', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
              let skipNext = false;
              if ($this.attr('skipNext') === 'true') {
                $this.removeAttr('skipNext');
                skipNext = true;
              }
              $('#create-organisation-form')[0].reset();
              closeCurrentWidget($this);
              if(!skipNext && $('#user_extra').val() === 'True'){
                showOnboardingWidget('#invitePopup');
              }
            } else {
                alert("Can't create org: " + result.error.message);
            }
        });
        return false;
    });

});
