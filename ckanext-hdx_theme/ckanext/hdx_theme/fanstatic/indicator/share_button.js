$(document).ready(function(){
  $('.{{ button_class }}').click(function(){
    $.ajax({
      url: "{{ h.url(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='shorten')}}",
      data:{'url':"{{ url }}" },
      type: 'POST'
    }).done(function(msg){
      $('.resource-social a').each(function(){
          var link = $(this).attr('href');
          $(this).attr('href', link.replace("XXXX", msg['url']));
      });
    });
    return false;
  });
});