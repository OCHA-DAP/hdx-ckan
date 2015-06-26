function toggleVis(){
    $('#private_loading').show();
    $('#private_block').hide();
    $.ajax({
        url: '{% url_for controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='visibility', id=pkg_dict.id %}',
    }).done(function(e) {
        if(e.success){
            $('#visibility').html(e.status);
            $('#visibility_change').html(e.text);
            $('#private_loading').hide();
            $('#private_block').show();
        }
    });
}