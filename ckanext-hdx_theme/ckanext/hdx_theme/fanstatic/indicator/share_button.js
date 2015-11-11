$(document).ready(function(){
  $('.share_button').click(function(e){
    $.ajax({
      url: $(this).attr('short-path'),
      data:{'url':$(this).attr('target-url'), },
      type: 'POST'
    }).done(function(msg){
      $('.change-link-wrapper a').each(function(){
          var link = $(this).attr('href');
          $(this).attr('href', link.replace("data.hdx.rwlabs.org", msg['url']));
      });
    });
    return false;
  });

  $('.direct-share-links a').click(function(e){
    e.preventDefault();
    var button = $(this);
    var parent = $(this).parent();
    var shareWindow = window.open('about:blank', '');
    button.find("i").hide();
    button.find("img").show();
    $.ajax({
      url: parent.attr('short-path'),
      data:{'url':parent.attr('target-url'), },
      type: 'POST'
    }).done(function(msg){
      var link = button.attr('href');
      console.log(msg);
      link = link.replace("data.hdx.rwlabs.org", msg['url']);
      console.log("THIS:" + link);
      shareWindow.location.replace(link);
      //window.open(link);
    }).always(function(){
      button.find("i").show();
      button.find("img").hide();
    });
    return false;
  });
});