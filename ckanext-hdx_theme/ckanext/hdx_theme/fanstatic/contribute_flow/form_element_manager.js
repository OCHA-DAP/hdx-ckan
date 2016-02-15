"use strict";

ckan.module('hdx_form_element_manager', function($, _) {
    return {
        initialize: function () {
            var moduleEl = this.el;
            var errorEl = this.el.find('.error-block');
            var errorWrapperEl = this.el.find('.controls');
            var controlGroupEl = this.el.find('.control-group');
            var elementName = this.options.element_name;
            var required = this.options.required;
            var broadcastChange = this.options.broadcast_change;

            var moduleLog = this.moduleLog;

            /**
             * Messages on the topic hdx-form-validation are
             * related to validation UI changes
             */
            this.sandbox.subscribe('hdx-form-validation',
                function (message) {
                    if (message.type == 'reset') {
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
                    else if (message.elementName == elementName) {
                        try {
                            errorWrapperEl.addClass('error');

                            var existingText = errorEl.html().trim();
                            var newText = existingText ? existingText + ", " + message.errorInfo : message.errorInfo;
                            errorEl.html(newText);
                        }
                        catch (e) {
                            if (e && e.hasOwnProperty('message')) {
                                moduleLog(e.message);
                            }

                        }

                    }
                }
            );


            if (elementName.indexOf('_other') > 0) {
                this.sandbox.subscribe('hdx-other-selection',
                    function (message) {
                        /* If we get the message from the correct select element */
                        //moduleLog('Processing broadcast message: ' + JSON.stringify(message));
                        if (elementName.indexOf(message.srcElement) == 0) {
                            if (message.newValue == 'Other' || message.newValue == 'hdx-other')
                                moduleEl.show();
                            else
                                moduleEl.hide();
                        }
                    }
                );
            }
            var selectEl = moduleEl.find('select');
            if ( broadcastChange ) {
                selectEl.change(
                    function (e) {
                        this.broadcastSelectChange(selectEl);
                    }.bind(this)
                );
                this.broadcastSelectChange(selectEl);
            }

        },
        broadcastSelectChange: function(selectEl) {
            /**
             * Sends a message when a select element changes. Useful for displaying license_other and
             * methodology_other textboxes
             */
            var newValue = selectEl.prop('value');
            var message = {
                'srcElement': this.options.element_name,
                'newValue': newValue
            };
            //this.moduleLog('Broadcasting message: ' + JSON.stringify(message));
            this.sandbox.publish('hdx-other-selection', message);
        },
        moduleLog: function(message) {
            //console.log(message);
        },
        options: {
            element_name: null,
            required: null,
            broadcast_change: false
        }
    };
});