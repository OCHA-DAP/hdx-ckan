$(document).ready(function(){
  $('.share_button').click(function(e){
    $.ajax({
      url: $(this).attr('short-path'),
      data:{'url':$(this).attr('target-url'), },
      type: 'POST'
    }).done(function(msg){
      $('.resource-social a').each(function(){
          var link = $(this).attr('href');
          $(this).attr('href', link.replace("data.hdx.rwlabs.org", msg['url']));
      });
    });
    return false;
  });
});