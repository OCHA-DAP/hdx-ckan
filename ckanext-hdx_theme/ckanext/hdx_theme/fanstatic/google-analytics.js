(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-48221887-3', 'auto');

//swap the two create calls in order to enable recording data from localhost instances
//this is useful when testing to see realtime data on the Google Analytics site
//ga('create', 'UA-48221887-3', {
//  'cookieDomain': 'none'
//});
ga('send', 'pageview');

function setUpResourcesTracking(){
  $('.ga-download').on('click', function(){
    var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'resource', 'download', rTitle + " (" + dTitle +")");
    ga('send', 'event', 'dataset', 'resource-download', dTitle);
  });

  $('.ga-share').on('click', function(){
    var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'resource', 'share', rTitle + " (" + dTitle +")");
    ga('send', 'event', 'dataset', 'resource-share', dTitle);
  });

  $('.ga-preview').on('click', function(){
    console.log("sending event");
    var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'resource', 'preview', rTitle + " (" + dTitle +")");
    ga('send', 'event', 'dataset', 'resource-preview', dTitle);
  });
}

function setUpShareTracking(){
  $(".indicator-actions.followButtonContainer a").on('click', function (){
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'dataset', 'share', dTitle);
  });
}

function setUpGalleryTracking() {
  $("li.related-item.media-item a.media-view").on('click', function (){
    var rTitle = $(this).parent().find(".media-heading").text().trim();
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'gallery', 'click', rTitle + " (" + dTitle +")");
  });
}