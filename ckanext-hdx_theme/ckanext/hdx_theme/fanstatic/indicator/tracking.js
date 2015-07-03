$(function (){
  //Only open a new window for non-file uploads
  // Tracking
  var url = location.pathname;
  // remove any site root from url
  url = url.substring($('body').data('locale-root'), url.length);
  // trim any trailing /
  url = url.replace(/\/*$/, '');
  $.ajax({url : $('body').data('site-root') + '_tracking',
          type : 'POST',
          data : {url:url, type:'page'},
          timeout : 300 });
  $('a.resource-url-analytics').click(function (e){
    var url = $(e.target).closest('a').attr('href');
    //Only open a new window for non-file uploads
    var type = $(e.target).closest('a').attr('tracking-type');
    if(!type || type == 'file.upload'){
      $.ajax({url : $('body').data('site-root') + '_tracking',
            data : {url:url, type:'resource'},
            type : 'POST',
            complete : function () {location.href = url;},
            timeout : 30});
      e.preventDefault();
    }else{
      $.ajax({url : $('body').data('site-root') + '_tracking',
            data : {url:url, type:'resource'},
            type : 'POST',
            complete : function () {window.open(url);},
            timeout : 30});
      e.preventDefault();
    }
  });
});
