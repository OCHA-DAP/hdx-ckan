"use strict";

ckan.module('hdx_click_stopper', function ($, _) {
    return {
        initialize: function () {
            var aElement = this.options.selector ? $(this.options.selector) : this.el;
            var href = this.options.href ? this.options.href : aElement.attr('href');
            var target = aElement.attr('target');
            var isNewTab = "_blank" === target;
            aElement.click(function (e) {

              var data = {
                  id: aElement.attr('id'),
                  linkType: this.options.link_type,
                  destinationUrl: href
              };
              if (this.options.just_send_event) {
                hdxUtil.analytics.sendLinkClickEvent(data);
              }
              else {

                var ctrlCmdKey = e.ctrlKey || e.metaKey;
                if (!isNewTab && !ctrlCmdKey) {
                  e.preventDefault();
                }


                var promise = hdxUtil.analytics.sendLinkClickEvent(data);
                promise.done(
                  /**
                   * The callback function opens the link after the analytics events are sent.
                   */
                  function () {
                    if (data.destinationUrl && !ctrlCmdKey) {
                      console.log("Executing original click action " + e.ctrlKey + " " + e.metaKey);

                      if (target) {
                        window.open(data.destinationUrl, target);
                      } else {
                        window.location.href = data.destinationUrl;
                      }
                    }
                  }
                );
              }

            }.bind(this));
        },
        options: {
            href: null,
            link_type: null,
            just_send_event: false,
            selector: null // when you can't add the data-module on the targeted <a>, use selector to specify it
        }
    };
});
