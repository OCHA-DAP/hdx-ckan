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
    function () {
        function setupShareTracking() {
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
                analyticsWrapperEl.on('click', '.mx-analytics-share', sendSharingEvent);
            }
            else {
                $('.mx-analytics-share').on('click', sendSharingEvent);
            }

        }
        setupShareTracking();
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

    /**
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendDatasetCreationEvent() {

        var pageTitle = null;
        try {
            pageTitle = window.parent.analyticsInfo.pageTitle;
        } catch (e) {
            // We can get the page title because the contribute iframe is on the same domain
            // as the HDX page on which it was created.
            // If the contribute iframe is called from another site, this will not work and will
            // raise an exception
        }

        var mixpanelData = {
            "eventName": "dataset create",
            "eventMeta": {
                "page title": pageTitle,
                "event source": "web"
            }
        };

        var gaData = {
            "eventCategory": "dataset",
            "eventAction": "create",
            "eventLabel": pageTitle || ""
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);

    }

    hdxUtil.analytics.sendDatasetCreationEvent = sendDatasetCreationEvent;

    /**
     *
     * @param {object} data
     * @param {?string} data.destinationUrl The url where the link was supposed to navigate
     * @param {?string} data.linkType One of: carousel, learn more faq, find data box, trending topic, main nav, footer
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendLinkClickEvent(data) {

        var metadata = {
            "page title": analyticsInfo.pageTitle
        };
        if (data.destinationUrl) {
            metadata["destionation url"] = data.destinationUrl;
        }
        if (data.linkType) {
            metadata["link type"] = data.linkType;
        }

        var mixpanelData = {
            "eventName": "link click",
            "eventMeta": metadata
        };

        var gaData = {
            "eventCategory": (metadata["link type"] || "") + " link",
            "eventAction": metadata["destionation url"],
            "eventLabel": metadata["page title"] || ""
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);

    }

    hdxUtil.analytics.sendLinkClickEvent = sendLinkClickEvent;

    /**
     * @param {string} messageSource From what type of page is the message sent from: dataset, faq
     * @param {string} messageType Type of the msg being sent, for now one of: contact contributor, group message, faq
     * @param {string} messageSubject The problem type flagged by this message (for now only for "contact contributor")
     * @param {string} messageTarget Which people will receive this message (for now only for "group message")
     * @param {boolean} isDatasetPage is the event sent from a dataset page (include dataset meta)
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendMessagingEvent(messageSource, messageType, messageSubject, messageTarget, isDatasetPage) {
        var metadata = {
            'message type': messageType
        };
        if (messageSubject) {
            $.extend(metadata, {'message subject': messageSubject});
        }
        if (messageTarget) {
            $.extend(metadata, {'message target': messageTarget});
        }
        if (isDatasetPage) {
            $.extend(metadata, {
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
        }

        var mixpanelData = {
            "eventName": "message sent",
            "eventMeta": metadata
        };

        var label = "on '" + analyticsInfo.pageTitle + "'";
        if (metadata['message subject']) {
            label = "subject '" + metadata['message subject'] + "' " + label;
        }
        if (metadata['message target']) {
            label = label + " target '" + metadata['message target'] + "'";
        }

         var gaData = {
            "eventCategory": messageSource,
            "eventAction": "message sent",
            "eventLabel": label
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);
    }
    hdxUtil.analytics.sendMessagingEvent = sendMessagingEvent;

    /**
     * This function will send the analytics events to the server async and will return a promise
     * which is fulfilled when the events are successfully sent OR when "timeout" seconds have passed
     *
     * @param {object} mixpanelData
     * @param {string} mixpanelData.eventName
     * @param {object.<string, string|number>} mixpanelData.eventMeta
     * @param {object} gaData
     * @param {string} gaData.eventCategory
     * @param {string} gaData.eventAction
     * @param {string} gaData.eventLabel
     * @param {number} [timeout=500] How long to wait until marking the promise as fulfilled. Optional, default 500ms
     * @returns {promise} aggregate promise of the promises for mixpanel and GA.
     */
    function sendAnalyticsEventsAsync(mixpanelData, gaData, timeout) {

        var _timeout = timeout || 500;

        var mixpanelDeferred = new $.Deferred();
        var gaDeferred = new $.Deferred();

        if (mixpanelData) {
            mixpanel.track(mixpanelData.eventName, mixpanelData.eventMeta, function () {
                if (mixpanelDeferred.state() == "pending") {
                    console.log("Finishing sending click event to mixpanel");
                    mixpanelDeferred.resolve(true);
                }
                else {
                    console.log("Mixpanel promise was already solved");
                }
            });
        }
        else {
            mixpanelDeferred.resolve(true);
        }

        if (gaData) {
            ga('send', 'event', gaData.eventCategory, gaData.eventAction, gaData.eventLabel, {
                hitCallback: function () {
                    if (gaDeferred.state() == "pending") {
                        console.log("Finishing sending click event to GA");
                        gaDeferred.resolve(true);
                    }
                    else {
                        console.log("GA promise was already solved");
                    }
                }
            });
        }
        else {
            gaDeferred.resolve(true);
        }

        setTimeout(function () {
            console.log("Resolving mixpanel and ga promises after timeout");
            if (mixpanelDeferred.state() == "pending") {
                console.log("Resolving mixpanel promise after timeout");
                mixpanelDeferred.resolve(true);
            }
            if (gaDeferred.state() == "pending") {
                console.log("Resolving GA promise after timeout");
                gaDeferred.resolve(true);
            }
        }, _timeout);

        return $.when(mixpanelDeferred.promise(), gaDeferred.promise());

    }


}());

function setUpGalleryTracking() {
  $("li.related-item.media-item a.media-view").on('click', function (){
    var rTitle = $(this).parent().find(".media-heading").text().trim();
    var dTitle = $(".itemTitle").text().trim();
    ga('send', 'event', 'gallery', 'click', rTitle + " (" + dTitle +")");
  });
}