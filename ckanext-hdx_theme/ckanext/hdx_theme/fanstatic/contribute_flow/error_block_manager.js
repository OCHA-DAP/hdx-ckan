"use strict";

ckan.module('hdx_error_block_manager', function($, _) {
    return {
        initialize: function () {
            var thisEl = this.el;
            var errorEl = this.el.find('ul');
            this.sandbox.subscribe('hdx-form-validation',
                function (message) {
                    if (message.type == 'reset' ) {
                        thisEl.addClass('hdx-invisible-element');
                        thisEl.removeClass('hdx-visible-element');
                        errorEl.html('');
                    }
                    else
                        if (message.elementName == 'error_block' && message.errorBlock) {
                            thisEl.removeClass('hdx-invisible-element');
                            thisEl.addClass('hdx-visible-element');

                            var existingText = errorEl.html().trim();
                            var errorBlock = message.errorBlock;
                            var newHtml= '';
                            for (var key in errorBlock) {
                                var val = errorBlock[key];
                                newHtml += '<li>' + key + ': ' + val + '</li>';
                            }
                            existingText += newHtml;
                            errorEl.html(existingText);
                        }
                }
            );

        },
        options: {
            element_name: null
        }
    };
});