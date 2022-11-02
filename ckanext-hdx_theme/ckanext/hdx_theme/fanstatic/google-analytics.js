$(
    /**
     * We're only sending mixpanel events. GA deals with search differently / automatically
     */
    function setUpSearchTracking() {

        var resultType = "dataset";

        /* We now have 2 separate forms. One with the filters the other one with the query term*/
        var formEl1 = $("#search-page-filters-form");
        var formEl2 = $("#dataset-filter-form");

        var showCaseFormEl = $("#showcaseSection form");

        var paramList = [];

        if (formEl1.length > 0) {
            paramList = paramList.concat(formEl1.serializeArray());
        }
        if (formEl2.length > 0) {
            paramList = paramList.concat(formEl2.serializeArray());
        }
        if (showCaseFormEl.length > 0) {
            paramList = paramList.concat(showCaseFormEl.serializeArray());
            resultType = "showcase";
        }

        if (paramList.length > 0) {
            var mixpanelMapping = {
                'q': {
                    'name': 'search term',
                    'isList': false,
                    'mandatory': true
                },
                'vocab_Topics': {
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
                'license_id': {
                    'name': 'license filters',
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
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_subnational': {
                    'name': 'subnational filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_quickcharts': {
                    'name': 'quickcharts filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_geodata': {
                    'name': 'geodata filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_requestdata': {
                    'name': 'requestdata filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_hxl': {
                    'name': 'hxl filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_sadd': {
                    'name': 'sadd filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_showcases': {
                    'name': 'showcases filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                },
                'ext_administrative_divisions': {
                    'name': 'administrative divisions filter',
                    'isList': false,
                    'mandatory': true,
                    'valueMap': {
                        '1': 'on'
                    }
                }
            };

            var numberOfResults = parseInt($('#analytics-number-of-results').text().trim()) || 0;

            var mixpanelEventMeta = {
                "page title": analyticsInfo.pageTitle,
                "number of results": numberOfResults,
                "result type": resultType
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
         * @param mappingInfo {{name:string, isList: boolean, mandatory: boolean, valueMap: {Object}}} information about how the param should be formatted
         * @param paramValue {string} the value of the <form> parameter
         */
        function populateMetadata(mixpanelEventMeta, mappingInfo, paramValue) {
            if (mappingInfo.isList) {
                mixpanelEventMeta[mappingInfo.name] = mixpanelEventMeta[mappingInfo.name] ?
                    mixpanelEventMeta[mappingInfo.name] : [];
                mixpanelEventMeta[mappingInfo.name].push(paramValue);
            }
            else {
                if (mappingInfo.valueMap) {
                    mixpanelEventMeta[mappingInfo.name] = mappingInfo.valueMap[paramValue];
                }
                else{
                    mixpanelEventMeta[mappingInfo.name] = paramValue;
                }
            }
        }
    }
);

$(
    function () {
        function setupShareTracking() {
            var sendSharingEvent = function () {
                var sharedItem = $(this).attr('data-shared-item');
                var shareType = $(this).attr('data-share-type');

                /* This is a hack to identify the "Nepal Earthquake" page as a crises page */
                if (sharedItem === 'location' && analyticsInfo.pageTitle.toLowerCase() === 'nepal earthquake') {
                    sharedItem = 'crises';
                }

                hdxUtil.analytics.pushToGTMDataLayer({
                  'event': 'share hdx',
                  'label': sharedItem,
                  'type': shareType

                });
                var mixpanelMeta = {
                    'page title': analyticsInfo.pageTitle,
                    'shared item': sharedItem,
                    'share type': shareType
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
            hdxUtil.analytics.pushToGTMDataLayer({
                'event': 'resource download hdx',
                'label': rTitle,
                'dataset_name': dTitle,
                'type': analyticsInfo.isCod ? 'cod' : 'standard',
              });

            mixpanel.track("resource download", {
                "event source": "web",
                "resource name": rTitle,
                "resource id": rId,
                "dataset name": dTitle,
                "dataset id": analyticsInfo.datasetId,
                "page title": analyticsInfo.pageTitle,
                "org name": analyticsInfo.organizationName,
                "org id": analyticsInfo.organizationId,
                "group names": analyticsInfo.groupNames,
                "group ids": analyticsInfo.groupIds,
                "is cod": analyticsInfo.isCod,
                "is indicator": analyticsInfo.isIndicator,
                "is archived": analyticsInfo.isArchived,
                "authenticated": analyticsInfo.authenticated
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
            // ga('send', 'event', 'resource', 'preview', rTitle + " (" + dTitle + ")");
            // ga('send', 'event', 'dataset', 'resource-preview', dTitle);
            hdxUtil.analytics.pushToGTMDataLayer({
                'event': 'preview hdx',
                'label': rTitle,
                'dataset_name': dTitle,
                'type': analyticsInfo.isCod ? 'cod' : 'standard',
            });
        });
    }

    setUpResourcesTracking();

    /**
     * @param {[{name: string, value: string}]} formdata the data of the form
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendDatasetCreationEvent(formdata) {

        var pageTitle = null;
        try {
            pageTitle = window.parent.analyticsInfo.pageTitle;
        } catch (e) {
            // We can get the page title because the contribute iframe is on the same domain
            // as the HDX page on which it was created.
            // If the contribute iframe is called from another site, this will not work and will
            // raise an exception
        }

        /**
         *
         * @param {string} name - the name of the form field
         * @returns {[string]}
         */
        function getValuesFromFormData(name) {
            var resultList = [];
            for (var i=0; i<formdata.length; i++) {
                var formItem = formdata[i];
                if (name == formItem.name) {
                    resultList.push(formItem.value);
                }
            }
            return resultList;
        }

        var group_names = getValuesFromFormData('locations');
        var org_names = getValuesFromFormData('owner_org');
        var org_name = org_names.length > 0 ? org_names[0] : null;
        var privateVal = getValuesFromFormData('private');
        var reqdataTypeVal = getValuesFromFormData('is_requestdata_type');

        var isPrivate = privateVal.length > 0 ? privateVal[0] == "true" : false;
        var isMetadataOnly = reqdataTypeVal.length > 0 ? reqdataTypeVal[0] == "true" : false;

        var dataset_availability = isMetadataOnly ? 'metadata only' : isPrivate ? 'private' : 'public';

        /* tag_string looks something like "3 word address,cod,health" */
        var codVal = getValuesFromFormData('tag_string');
        codVal = codVal.length > 0 ? codVal[0].split(',') : [];
        var isCod = codVal.indexOf('cod') >= 0;

        var mixpanelData = {
            "eventName": "dataset create",
            "eventMeta": {
                "page title": pageTitle,
                "event source": "web",
                "group names": group_names,
                "org_name": org_name,
                "is cod": isCod,
                "is indicator": false,
                "is private": isPrivate,
                "dataset availability": dataset_availability
            }
        };

        var locationNames = null;
        if (group_names) {
          locationNames = group_names.length < 15 ? group_names.join('~') : 'many';
        }
        var gaData = {
            'event': 'dataset create hdx',
            'type': isCod ? 'cod' : 'standard',
            'location_names': locationNames,
            'org_name': org_name,
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);

    }

    hdxUtil.analytics.sendDatasetCreationEvent = sendDatasetCreationEvent;

    /**
     *
     * @param {object} data
     * @param {string} data.destinationUrl The faq question hashtag url
     * @param {string} data.destinationLabel The faq question text
     * @returns {boolean} true
     */
    function sendFaqClickEvent(data) {

        var metadata = {
            "page title": analyticsInfo.pageTitle
        };
        if (data.destinationUrl) {
            metadata["destination url"] = data.destinationUrl;
        }
        if (data.destinationLabel) {
            metadata["destination label"] = data.destinationLabel;
        }

        var mixpanelData = {
            "eventName": "faq click",
            "eventMeta": metadata
        };

        var gaData = {
            'event': 'faq click hdx',
            'label': data.destinationLabel,
            'url': data.destinationUrl,
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);

    }

    hdxUtil.analytics.sendFaqClickEvent = sendFaqClickEvent;

    /**
     *
     * @param {object} data
     * @param {'header icon' | 'item'} data.type The type of notification interaction (header icon /item)
     * @param {?string} data.destinationUrl The url where the link was supposed to navigate, only for type == "item"
     * @param {?boolean} data.personal false for global notifications, true for personal ones, only for type == "item"
     * @param {?number} data.count number of notifications, only for type == "header icon"
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendNotificationInteractionEvent(data) {

        var eventName = "notification interaction";

        var metadata = {
            "page title": analyticsInfo.pageTitle,
            "authenticated": analyticsInfo.authenticated
        };
        if (data.destinationUrl) {
            metadata["destination url"] = data.destinationUrl;
        }
        if (data.type) {
            metadata["type"] = data.type;
        }
        if (typeof data.personal === 'boolean') {
            metadata["personal"] = data.personal;
        }
        if (data.count) {
            metadata["count"] = data.count;
        }

        var mixpanelData = {
            "eventName": eventName,
            "eventMeta": metadata
        };

        var gaData = {
            'event': 'notification interaction hdx',
            'url': data.destinationUrl,
            'label': data.type,
            'type': data.personal ? 'personal' : 'general',
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);

    }

    hdxUtil.analytics.sendNotificationInteractionEvent = sendNotificationInteractionEvent;

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
            /* This was a spelling mistake. For historical reasons we need to keep it for a while.
            * It's deprecated by the correct spelling below */
            metadata["destionation url"] = data.destinationUrl;
            metadata["destination url"] = data.destinationUrl;
        }
        if (data.linkType) {
            metadata["link type"] = data.linkType;
        }

        var mixpanelData = {
            "eventName": "link click",
            "eventMeta": metadata
        };

        var gaData = {
            'event': 'link click hdx',
            'url': data.destinationUrl,
            'type': data.linkType,
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
     * @param {object} localAnalyticsInfo analytics data about dataset.
     * Useful when not on a dataset specific page, like the search page.
     * @returns {promise} Promise that gets fulfilled when the analytics tracking events were sent or time out exceeded
     */
    function sendMessagingEvent(messageSource, messageType, messageSubject, messageTarget,
                                isDatasetPage, localAnalyticsInfo) {

        if (localAnalyticsInfo) {
            localAnalyticsInfo.pageTitle = analyticsInfo.pageTitle;
        } else {
            localAnalyticsInfo = analyticsInfo;
        }
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
                "dataset name": localAnalyticsInfo.datasetName,
                "dataset id": localAnalyticsInfo.datasetId,
                "page title": localAnalyticsInfo.pageTitle,
                "org name": localAnalyticsInfo.organizationName,
                "org id": localAnalyticsInfo.organizationId,
                "group names": localAnalyticsInfo.groupNames,
                "group ids": localAnalyticsInfo.groupIds,
                "is cod": localAnalyticsInfo.isCod,
                "is indicator": localAnalyticsInfo.isIndicator,
                "is archived": localAnalyticsInfo.isArchived
            });
        }

        var mixpanelData = {
            "eventName": "message sent",
            "eventMeta": metadata
        };

        // var label = "on '" + analyticsInfo.pageTitle + "'";
        // if (metadata['message subject']) {
        //     label = "subject '" + metadata['message subject'] + "' " + label;
        // }
        // if (metadata['message target']) {
        //     label = label + " target '" + metadata['message target'] + "'";
        // }

         var gaData = {
            'event': 'message sent hdx',
            'type': messageType,
            'dataset_name': isDatasetPage ? localAnalyticsInfo.datasetName : undefined,
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);
    }
    hdxUtil.analytics.sendMessagingEvent = sendMessagingEvent;

    /**
     *
     * @param addMethod {string} "by request" or "by invitation"
     * @param rejected {boolean} whether the member was rejected (true) or accepted (false) in the org
     * @returns {promise}
     */
    function sendMemberAddRejectEvent(addMethod, rejected) {
        var eventName = rejected ? "member rejected" : "member add";
        var metadata = {
            "add method": addMethod,
            "page title": analyticsInfo.pageTitle,
            "org name": analyticsInfo.organizationName,
            "org id": analyticsInfo.organizationId
        };

        var mixpanelData = {
            "eventName": eventName,
            "eventMeta": metadata
        };

        var gaData = {
            'event': eventName + ' hdx',
            'type': addMethod,
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);
    }

    hdxUtil.analytics.sendMemberAddRejectEvent = sendMemberAddRejectEvent;

    /**
     * Sends events related to new user registration: user register, start user register, submit email register
     * @param eventName {string}
     */
    function sendUserRegisteredEvent(eventName) {
        // var eventName = "user register";
        var metadata = {
            "page title": analyticsInfo.pageTitle
        };

        var mixpanelData = {
            "eventName": eventName,
            "eventMeta": metadata
        };

        var gaData = {
            'event': eventName + ' hdx'
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);
    }

    hdxUtil.analytics.sendUserRegisteredEvent = sendUserRegisteredEvent;


    /**
     * Sends events related to QA sensitivity
     * @param resourceId {string}
     * @param isSensitive {boolean}
     * @param piiPredictScore {number}
     * @param piiReportId {string}
     */
    function sendQADashboardEvent(resourceId, isSensitive, piiPredictScore, piiReportId) {
        var eventName = "qa resource sensitivity set";
        var metadata = {
            "page title": analyticsInfo.pageTitle,
            "resource id": resourceId,
            "is sensitive": isSensitive,
            "pii predict score": piiPredictScore,
            "pii report id": piiReportId
        };

        var mixpanelData = {
            "eventName": eventName,
            "eventMeta": metadata
        };

        var gaData = {
            'event': eventName + ' hdx',
            'label': isSensitive ? 'sensitive' : 'not sensitive',
        };

        return sendAnalyticsEventsAsync(mixpanelData, gaData);
    }

    hdxUtil.analytics.sendQADashboardEvent = sendQADashboardEvent;
    /**
     *
     * @param {string} searchTerm
     * @param {string} resultType
     */
    function sendTopBarSearchEvents(searchTerm, resultType) {
        var mixpanelData = {
            "eventName": "search",
            "eventMeta": {
                "page title": analyticsInfo.pageTitle,
                "result type": resultType,
                "search term": searchTerm
            }
        };
        return sendAnalyticsEventsAsync(mixpanelData);

    }
    hdxUtil.analytics.sendTopBarSearchEvents = sendTopBarSearchEvents;

    /**
     *
     * @param {string} actionType
     */
    function sendSurveyEvent(interactionType) {
        var mixpanelData = {
            "eventName": "popup interaction",
            "eventMeta": {
                "popup title": "HDX Data Use Survey - 2020-06",
                "popup type": "general",
                "interaction type": interactionType
            }
        };
        return sendAnalyticsEventsAsync(mixpanelData);

    }
    hdxUtil.analytics.sendSurveyEvent = sendSurveyEvent;

    /**
     * This function will send the analytics events to the server async and will return a promise
     * which is fulfilled when the events are successfully sent OR when "timeout" seconds have passed
     *
     * @param {object} mixpanelData
     * @param {string} mixpanelData.eventName
     * @param {object.<string, string|number>} mixpanelData.eventMeta
     * @param {object} gaData
     * @param {string} gaData.event
     * @param {string} [gaData.label]
     * @param {string} [gaData.type]
     * @param {string} [gaData.url]
     * @param {string} [gaData.format]
     * @param {string} [gaData.dataset_name]
     * @param {string} [gaData.org_name]
     * @param {string} [gaData.location_names]
     * @param {number} [timeout=500] How long to wait until marking the promise as fulfilled. Optional, default 500ms
     * @returns {promise} aggregate promise of the promises for mixpanel and GA.
     */
    function sendAnalyticsEventsAsync(mixpanelData, gaData, timeout) {

        var _timeout = timeout || 500;

        var mixpanelDeferred = new $.Deferred();
        var gaDeferred = new $.Deferred();

        if (mixpanel && mixpanelData) {
            mixpanel.track(mixpanelData.eventName, mixpanelData.eventMeta, function () {
                if (mixpanelDeferred.state() === "pending") {
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
            gaData.eventCallback = function() {
              if (gaDeferred.state() === "pending") {
                  console.log("Finishing sending click event to GA");
                  gaDeferred.resolve(true);
              }
              else {
                  console.log("GA promise was already solved");
              }
            };
            hdxUtil.analytics.pushToGTMDataLayer(gaData);
            // ga('send', 'event', gaData.eventCategory, gaData.eventAction, gaData.eventLabel, {
            //     hitCallback: function () {
            //         if (gaDeferred.state() === "pending") {
            //             console.log("Finishing sending click event to GA");
            //             gaDeferred.resolve(true);
            //         }
            //         else {
            //             console.log("GA promise was already solved");
            //         }
            //     }
            // });
        }
        else {
            gaDeferred.resolve(true);
        }

        setTimeout(function () {
            console.log("Resolving mixpanel and ga promises after timeout");
            if (mixpanelDeferred.state() === "pending") {
                console.log("Resolving mixpanel promise after timeout");
                mixpanelDeferred.resolve(true);
            }
            if (gaDeferred.state() === "pending") {
                console.log("Resolving GA promise after timeout");
                gaDeferred.resolve(true);
            }
        }, _timeout);

        return $.when(mixpanelDeferred.promise(), gaDeferred.promise());

    }

  /**
   * Pushes event to datalayer but first resets the properties/dimensions
   *
   * @param {object} gaData
   * @param {string} gaData.event
   * @param {string} [gaData.label]
   * @param {string} [gaData.type]
   * @param {string} [gaData.url]
   * @param {string} [gaData.format]
   * @param {string} [gaData.dataset_name]
   * @param {string} [gaData.org_name]
   * @param {string} [gaData.location_names]
   */
  function pushToDatalayer(gaData) {
    dataLayer.push({
      'label': undefined,
      'dataset_name': undefined,
      'url': undefined,
      'type': undefined,
      'format': undefined,
    });
    dataLayer.push(gaData);
  }
  hdxUtil.analytics.pushToGTMDataLayer = pushToDatalayer;


}());
