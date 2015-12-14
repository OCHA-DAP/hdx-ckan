"use strict";

ckan.module('hdx_form_element_manager', function($, _) {
    return {
        initialize: function () {
            var errorEl = this.el.find('.error-block');
            var errorWrapperEl = this.el.find('.controls');
            var elementName = this.options.element_name;
            this.sandbox.subscribe('hdx-form-validation',
                function (message) {
                    if (message.type == 'reset' ) {
                        errorWrapperEl.removeClass('error');
                        errorEl.html('');
                    }
                    else
                        if (message.elementName == elementName) {
                            errorWrapperEl.addClass('error');

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