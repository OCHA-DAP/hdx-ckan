$(
    /**
     * We're only sending mixpanel events. GA deals with search differently / automatically
     */
    function setUpSearchTracking() {
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

            var numberOfResults = parseInt($('#analytics-number-of-results').text().trim()) || 0;

            var paramList = formEl.serializeArray();
            var mixpanelEventMeta = {
                "page title": analyticsInfo.pageTitle,
                "number of results": numberOfResults
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
            if (sendTrackingEvent) {
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
    }
);

$(
    function setupLinkClickEvent() {
        $(window.document).on("hdx-link-clicked", function(event, data){

            var gaDeferred = new $.Deferred();
            var mixpanelDeferred = new $.Deferred();

            var wasCallbackExecuted = false;
            /**
             * The callback function opens the link after the analytics events are sent.
             * We need to make sure that this function is called exactly once even if
             * sending the analytics events to GA and/or Mixpanel failed
             */
            var originalAction = function () {
                if (!wasCallbackExecuted && data.destinationUrl){
                    wasCallbackExecuted = true;
                    console.log("Executing original click action");
                    if (!data.target){
                        window.location.href = data.destinationUrl;
                    }
                    else if (data.target != "_blank") {
                        window.open(data.destinationUrl, data.target);
                    }
                }
            };


            var metadata = {
                "page title": analyticsInfo.pageTitle
            };
            if (data.destinationUrl){
                metadata["destionation url"] = data.destinationUrl;
            }
            if (data.linkType){
                metadata["link type"] = data.linkType;
            }

            mixpanel.track("link click", metadata, function(){
                console.log("Finished sending click event to mixpanel");
                mixpanelDeferred.resolve(true);
            });
            var eventCategory = (metadata["link type"] || "") + " link";
            var eventAction = metadata["destionation url"];
            var eventLabel = metadata["page title"] || "";
            ga('send', 'event', eventCategory, eventAction, eventLabel, {
                hitCallback: function () {
                    console.log("Finished sending click event to GA");
                    gaDeferred.resolve(true);
                }
            });
            $.when(gaDeferred.promise(), mixpanelDeferred.promise()).done(originalAction);
            setTimeout(function () {
                console.log("Trying to do original action anyway in case it was not triggered normally");
                originalAction();
            }, 500);


        });
    }
);


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

        // resource sharing was disabled in HDX-4246
        //
        // $('.ga-share').on('click', function () {
        //     var rTitle = $(this).parents(".resource-item").find(".heading").attr("title");
        //     var dTitle = $(".itemTitle").text().trim();
        //     ga('send', 'event', 'resource', 'share', rTitle + " (" + dTitle + ")");
        //     ga('send', 'event', 'dataset', 'resource-share', dTitle);
        // });

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
function setUpShareTracking() {
    var sendSharingEvent = function () {
        var sharedItem = $(this).attr('data-shared-item');

        /* This is a hack to identify the "Nepal Earthquake" page as a crises page */
        if (sharedItem == 'location' && analyticsInfo.pageTitle.toLowerCase() == 'nepal earthquake') {
            sharedItem = 'crises';
        }

        // var dTitle = $(".itemTitle").text().trim();
        ga('send', 'event', sharedItem, 'share', analyticsInfo.pageTitle);
        var mixpanelMeta = {
            'page title': analyticsInfo.pageTitle,
            'shared item': sharedItem,
            'share type': $(this).attr('data-share-type')
        };

        mixpanel.track("share", mixpanelMeta);
    };
    var analyticsWrapperEl = $('.mx-analytics-wrapper');
    if (analyticsWrapperEl.length) {
        /**
         * There are cases where the share icons for ( google, twitter, facebook, mail ) 
         * are rendered after this event listener is bound. So we bind it to an existing parent element. 
         */
        analyticsWrapperEl.on('click', '.mx-analytics-share',sendSharingEvent);
    }
    else {
        $('.mx-analytics-share').on('click', sendSharingEvent);
    }

}

function setUpGalleryTracking() {
  $("li.related-item.media-item a.media-view").on('click', function (){
    var rTitle = $(this).parent().find(".media-heading").text().trim();
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'gallery', 'click', rTitle + " (" + dTitle +")");
  });
}