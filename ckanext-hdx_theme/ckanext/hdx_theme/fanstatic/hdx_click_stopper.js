"use strict";

ckan.module('hdx_click_stopper', function ($, _) {
    return {
        initialize: function () {
            var aElement = this.options.selector ? $(this.options.selector) : this.el;
            var href = this.options.href ? this.options.href : aElement.attr('href');
            var label = this.options.label ? this.options.label : $.trim(aElement.text());

            aElement.click(function (e) {

              var data = {
                  id: aElement.attr('id'),
                  linkType: this.options.link_type,
                  label: label,
                  destinationUrl: href
              };
              if (this.options.just_send_event) {
                hdxUtil.analytics.sendLinkClickEvent(data);
              }
              else {
                  var promise = hdxUtil.analytics.sendLinkClickEvent(data);

                  hdxUtil.eventUtil.postponeClickDefaultIfNotNewTab(e, promise, this.options.href);
              }

            }.bind(this));
        },
        options: {
            href: null,
            link_type: null,
            just_send_event: false,
            label: false,
            selector: null // when you can't add the data-module on the targeted <a>, use selector to specify it
        }
    };
});
