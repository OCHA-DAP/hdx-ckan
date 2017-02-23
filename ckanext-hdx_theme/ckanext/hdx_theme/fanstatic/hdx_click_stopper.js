"use strict";

ckan.module('hdx_click_stopper', function ($, _) {
    return {
        initialize: function () {
            var aElement = this.options.selector ? $(this.options.selector) : this.el;
            var href = this.options.href ? this.options.href : aElement.attr('href');
            var target = aElement.attr('target');
            var isNewTab = "_blank" == target;
            aElement.click(function (e) {
                if (!isNewTab) {
                    e.preventDefault();
                }
                var data = {
                    id: aElement.attr('id'),
                    linkType: this.options.link_type,
                    destinationUrl: href
                };

                var promise = hdxUtil.analytics.sendLinkClickEvent(data);
                promise.done(
                    /**
                     * The callback function opens the link after the analytics events are sent.
                     */
                    function () {
                        if (data.destinationUrl) {
                            console.log("Executing original click action");
                            if (!target) {
                                window.location.href = data.destinationUrl;
                            }
                            else if (target != "_blank") {
                                window.open(data.destinationUrl, target);
                            }
                    }
                });

            }.bind(this));
        },
        options: {
            href: null,
            link_type: null,
            selector: null // when you can't add the data-module on the targeted <a>, use selector to specify it
        }
    };
});