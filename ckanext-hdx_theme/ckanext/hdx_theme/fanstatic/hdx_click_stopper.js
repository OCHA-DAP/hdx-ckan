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
                    destinationUrl: href,
                    target: target
                };

                this.sandbox.publish('hdx-click-stopper-bus', data);

                $(window.document).trigger("hdx-link-clicked", [data]);
            }.bind(this));
        },
        options: {
            href: null,
            link_type: null,
            selector: null // when you can't add the data-module on the targeted <a>, use selector to specify it
        }
    };
});