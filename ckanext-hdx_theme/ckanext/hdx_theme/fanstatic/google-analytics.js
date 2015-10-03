

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

setUpResourcesTracking();