"use strict";

ckan.module('hdx_error_block_manager', function($, _) {
    return {
        initialize: function () {

            var moduleLog = this.moduleLog;

            var thisEl = this.el;
            var errorEl = this.el.find('ul');

            var generateErrorHtml = function (errorObj) {
                var resultingHtml = '';
                for (var key in errorObj) {
                    var val = errorObj[key];
                    if (typeof val === 'string')
                        resultingHtml += '<li>' + key + ': ' + val + '</li>';
                    else if (typeof val === 'object') {
                        resultingHtml += '<li>' + key + ':';
                        resultingHtml += '<ul>';
                        resultingHtml += generateErrorHtml(val);
                        resultingHtml += '</ul>';
                        resultingHtml += '</li>';
                    }
                }
                return resultingHtml;
            };
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
                            var newHtml= generateErrorHtml(message.errorBlock);

                            moduleLog("The new error block HTML is: " + newHtml);

                            existingText += newHtml;
                            errorEl.html(existingText);

                            hdxUtil.ui.scrollTo(thisEl);
                        }
                }
            );

        },
        moduleLog: function (message) {
            //console.log(message);
        },
        options: {
            element_name: null
        }
    };
});