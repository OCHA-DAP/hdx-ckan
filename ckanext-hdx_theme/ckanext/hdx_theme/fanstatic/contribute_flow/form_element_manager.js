"use strict";

ckan.module('hdx_form_element_manager', function($, _) {
    return {
        initialize: function () {
            var errorEl = this.el.find('.error-block');
            var elementName = this.options.element_name;
            this.sandbox.subscribe('hdx-form-validation',
                function (message) {
                    if (message.type == 'reset' ) {
                        errorEl.addClass('hdx-invisible-element');
                        errorEl.removeClass('hdx-visible-element');
                        errorEl.html('');
                    }
                    else
                        if (message.elementName == elementName) {
                            errorEl.removeClass('hdx-invisible-element');
                            errorEl.addClass('hdx-visible-element');

                            var existingText = errorEl.html().trim();
                            var newText = existingText ? existingText + ", " + message.errorInfo : message.errorInfo;
                            errorEl.html(newText);
                        }
                }
            );

        },
        options: {
            element_name: null
        }
    };
});