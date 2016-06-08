

function setUpResourcesTracking(){
  $('.ga-download').on('click', function(){
    var rTitle = $(this).find(".ga-download-resource-title").text().trim();
    // var dTitle = $(this).find(".ga-download-dataset-title").text().trim();
    var dTitle = analyticsInfo.datasetName;
    ga('send', 'event', 'resource', 'download', rTitle + " (" + dTitle +")");
    ga('send', 'event', 'dataset', 'resource-download', dTitle);

    mixpanel.track("resource download", {
        "resource name": rTitle,
        "dataset name": dTitle,
        "dataset id": analyticsInfo.datasetId,
        "org name": analyticsInfo.organizationName,
        "org id": analyticsInfo.organizationId,
        "group names": analyticsInfo.groupNames,
        "group ids": analyticsInfo.groupIds,
        "is cod": analyticsInfo.isCod,
        "is indicator": analyticsInfo.isIndicator
    });
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