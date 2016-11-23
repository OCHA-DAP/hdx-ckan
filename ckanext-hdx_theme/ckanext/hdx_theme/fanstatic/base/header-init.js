$(document).ready(function(){
    //select 2 everywhere
    $(".hdx-form").find("select").select2({
        allowClear: true
    });

    $(".dropdown.dropdown-on-hover").hover(
        function(){ $(this).addClass('open') },
        function(){ $(this).removeClass('open') }
    );
});