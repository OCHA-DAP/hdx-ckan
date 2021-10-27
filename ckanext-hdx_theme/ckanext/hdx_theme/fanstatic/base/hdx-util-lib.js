(function() {
    var hdxUtil = {
        'ui': {},
        'text': {},
        'compute': {},
        'eventUtil': {},
        'analytics': {} // This will be populated from analytics.js
    };
    window.hdxUtil = hdxUtil;

    hdxUtil.ui.scrollTo = function (target, delta) {
        if (!delta){
            delta = 40;
        }
        $('html, body').animate({
            'scrollTop': $(target).offset().top - delta
        }, 700);
    };
    hdxUtil.text.sanitize = function (theString) {
        if (theString !== null && theString.length > 0){
            return new DOMParser().parseFromString(theString, 'text/html').body.textContent;
        } else {
          return '';
        }
    };

    hdxUtil.compute.strHash = function (theString, startHash) {
        var i, chr, len;
        var hash = startHash ? startHash : 0;
        if (!theString || theString.length === 0) return hash;
        for (i = 0, len = theString.length; i < len; i++) {
            chr = theString.charCodeAt(i);
            hash = ((hash << 5) - hash) + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };

    hdxUtil.compute.strListHash = function (strList) {
        var hash = 0;
        if (strList) {
            for(var i=0; i<strList.length; i++) {
                var curStr = strList[i];
                hash = hdxUtil.compute.strHash(curStr, hash);
            }
        }
        return hash;
    };

    /**
     * If the link is not meant to be opened in a new tag then the actual opening of a new page is being postponed
     * until the promise is being fulfilled.
     *
     * @param {MouseEvent} clickEvent
     * @param {Promise} promise
     * @param {?string} href url to override the one found in the <a> element
     * @returns {boolean} True if event was prevented
     */
    hdxUtil.eventUtil.postponeClickDefaultIfNotNewTab = function (clickEvent, promise, href) {

        var aElement = $(clickEvent.delegateTarget);
        var isBlankTarget = aElement.attr('target') === '_blank';
        var target = aElement.attr('target');
        var linkUrl = href ? href : aElement.attr('href');

        var ctrlCmdKey = clickEvent.ctrlKey || clickEvent.metaKey;
        var isNewTab = isBlankTarget || ctrlCmdKey;
        var prevented = false;
        if (!isNewTab) {
            clickEvent.preventDefault();
            prevented = true;
        }

        promise.done(
            /**
             * The callback function opens the link after the analytics events are sent.
             */
            function () {
                /* If it was a newTab-click the new tab was already opened */
                if (linkUrl && prevented) {
                    console.log("Executing original click action " + clickEvent.ctrlKey + " " + clickEvent.metaKey);

                    if (!target) {
                        window.location.href = linkUrl;
                    } else {
                        window.open(linkUrl, target);
                    }
                }
            }
        );

        return prevented;
    };

    hdxUtil.eventUtil.debouncer = function (originalFunction, timeout) {

      var timeout = timeout || 500;
      var timeoutId = null;

      return function () {
        var originalArgs = arguments;
        var originalFunctionCaller = function() {
          originalFunction.apply(this, originalArgs);
        }.bind(this);
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(originalFunctionCaller, timeout);
      };
    };

})();
