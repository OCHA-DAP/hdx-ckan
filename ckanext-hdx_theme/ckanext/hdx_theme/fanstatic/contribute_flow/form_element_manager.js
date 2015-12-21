"use strict";

ckan.module('hdx_form_element_manager', function($, _) {
    return {
        initialize: function () {
            var errorEl = this.el.find('.error-block');
            var errorWrapperEl = this.el.find('.controls');
            var controlGroupEl = this.el.find('.control-group');
            var elementName = this.options.element_name;
            var required = this.options.required;

            var moduleLog = this.moduleLog;

            this.sandbox.subscribe('hdx-form-validation',
                function (message) {
                    if (message.type == 'reset' ) {
                        errorWrapperEl.removeClass('error');
                        errorEl.html('');
                    }
                    else if (message.type == 'private_changed') {
                        if (required && message.newValue == 'public' || required == 'private') {
                            controlGroupEl.addClass('required');
                        }
                        else {
                            controlGroupEl.removeClass('required');
                        }
                    }
                    else
                        if (message.elementName == elementName) {
                            try {
                                errorWrapperEl.addClass('error');

                                var existingText = errorEl.html().trim();
                                var newText = existingText ? existingText + ", " + message.errorInfo : message.errorInfo;
                                errorEl.html(newText);
                            }
                            catch(e) {
                                if (e && e.hasOwnProperty('message')) {
                                    moduleLog(e.message);
                                }

                            }

                        }
                }
            );

        },
        moduleLog: function(message) {
            //console.log(message);
        },
        options: {
            element_name: null,
            required: null
        }
    };
});