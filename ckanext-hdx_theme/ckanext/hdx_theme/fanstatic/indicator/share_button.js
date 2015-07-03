$(document).ready(function(){
  $('#button_class').click(function(){
    $.ajax({
      url: $('#short_path').val(),
      data:{'url':$('#target_url').val() },
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