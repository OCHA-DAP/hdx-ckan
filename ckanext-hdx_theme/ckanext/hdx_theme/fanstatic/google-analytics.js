$(function setUpSearchTracking() {
    var formEl = $("#dataset-filter-form");
    if (formEl.length > 0) {
        var mixpanelMapping = {
            'q': {
                'name': 'search term',
                'isList': false,
                'mandatory': true
            },
            'tags': {
                'name': 'tag filters',
                'isList': true,
                'mandatory': true
            },
            'res_format': {
                'name': 'format filters',
                'isList': true,
                'mandatory': true
            },
            'organization': {
                'name': 'org filters',
                'isList': true,
                'mandatory': true
            },
            'groups': {
                'name': 'location filters',
                'isList': true,
                'mandatory': true
            },
            /*'ext_page_size': {
                'name': 'items per page',
                'isList': false,
                'mandatory': false
            },
            'sort': {
                'name': 'sorting',
                'isList': false,
                'mandatory': false
            },*/
            'ext_cod': {
                'name': 'cod filter',
                'isList': false,
                'mandatory': true
            }
        };

        var paramList = formEl.serializeArray();
        var mixpanelEventMeta = {
            "page title": analyticsInfo.pageTitle
            /*"org name": analyticsInfo.organizationName,
            "org id": analyticsInfo.organizationId,
            "group names": analyticsInfo.groupNames,
            "group ids": analyticsInfo.groupIds*/
        };
        var sendTrackingEvent = false;
        for (var i = 0; i < paramList.length; i++) {
            var param = paramList[i];
            var mappingInfo = mixpanelMapping[param.name];
            var paramValue = param.value.trim();
            if (mappingInfo && paramValue) {
                populateMetadata(mixpanelEventMeta, mappingInfo, paramValue);
                sendTrackingEvent = sendTrackingEvent || mappingInfo.mandatory;
            }
        }
        if (sendTrackingEvent){
            var reResult = /ext_search_source=([^&]+)(&|$)/.exec(location.href);
            if (reResult && reResult.length > 1) {
                mixpanelEventMeta["search box location"] = reResult[1];
            }
            else {
                mixpanelEventMeta["search box location"] = "in-page";
            }
            console.log(JSON.stringify(mixpanelEventMeta));
            mixpanel.track("search", mixpanelEventMeta);
        }
        else {
            console.log("No mandatory properties found. Not sending search event to mixpanel.");
        }
    }

    /**
     * Populates the object that is sent to mixpanel for one <form> parameter
     * @param mixpanelEventMeta {Object} map of property-values to be sent to mixpanel
     * @param mappingInfo {{name:string, isList: boolean, mandatory: boolean}} information about how the param should be formatted
     * @param paramValue {string} the value of the <form> parameter
     */
    function populateMetadata(mixpanelEventMeta, mappingInfo, paramValue) {
        if (mappingInfo.isList) {
            mixpanelEventMeta[mappingInfo.name] = mixpanelEventMeta[mappingInfo.name] ?
                mixpanelEventMeta[mappingInfo.name] : [];
            mixpanelEventMeta[mappingInfo.name].push(paramValue);
        }
        else {
            mixpanelEventMeta[mappingInfo.name] = paramValue;
        }
    }
});


(function() {
    function setUpResourcesTracking() {
        $('.ga-download').on('click', function () {
            var rTitle = $(this).find(".ga-download-resource-title").text().trim();
            var rId = $(this).find(".ga-download-resource-id").text().trim();
            // var dTitle = $(this).find(".ga-download-dataset-title").text().trim();
            var dTitle = analyticsInfo.datasetName;
            ga('send', 'event', 'resource', 'download', rTitle + " (" + dTitle + ")");
            ga('send', 'event', 'dataset', 'resource-download', dTitle);

            mixpanel.track("resource download", {
                "event source": "web",
                "resource name": rTitle,
                "resource id": rId,
                "dataset name": analyticsInfo.datasetName,
                "dataset id": analyticsInfo.datasetId,
                "page title": analyticsInfo.pageTitle,
                "org name": analyticsInfo.organizationName,
                "org id": analyticsInfo.organizationId,
                "group names": analyticsInfo.groupNames,
                "group ids": analyticsInfo.groupIds,
                "is cod": analyticsInfo.isCod,
                "is indicator": analyticsInfo.isIndicator
            });
        });

        $('.ga-share').on('click', function () {
            var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
            var dTitle = $(".itemTitle").text().trim();
            ga('send', 'event', 'resource', 'share', rTitle + " (" + dTitle + ")");
            ga('send', 'event', 'dataset', 'resource-share', dTitle);
        });

        $('.ga-preview').on('click', function () {
            console.log("sending event");
            var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
            var dTitle = $(".itemTitle").text().trim();
            ga('send', 'event', 'resource', 'preview', rTitle + " (" + dTitle + ")");
            ga('send', 'event', 'dataset', 'resource-preview', dTitle);
        });
    }
    setUpResourcesTracking();
}());
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