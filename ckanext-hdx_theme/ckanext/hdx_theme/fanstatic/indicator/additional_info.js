function toggleVis(){
    $('#private_loading').show();
    $('#private_block').hide();
    $.ajax({
        url: $('#controller_url').attr('value'),
    }).done(function(e) {
        if(e.success){
            $('#visibility').html(e.status);
            $('#visibility_change').html(e.text);
            $('#private_loading').hide();
            $('#private_block').show();
        }
    });
}