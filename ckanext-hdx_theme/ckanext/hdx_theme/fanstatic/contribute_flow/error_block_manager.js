"use strict";

ckan.module('hdx_error_block_manager', function($, _) {
    return {
        initialize: function () {

            var moduleLog = this.moduleLog;

            var thisEl = this.el;
            // var errorEl = this.el.find('ul');

            var setMainErrorMessage = function(message){
              var messageEl = this.el.find('p');
              if (!message) {
                message = this.options.default_error_message;
              }
              messageEl.html(message);

            }.bind(this);


            var processKey = function (key) {
                var processedKey = null;
                if ( this.options.key_mappings.hasOwnProperty(key) ) {
                    var trnKey = this.options.key_mappings[key];
                    processedKey = this.i18n(trnKey);
                }
                else
                    processedKey = key;

                return processedKey;
            }.bind(this);

            // var generateErrorHtml = function (errorObj) {
            //     var resultingHtml = '';
            //     for (var key in errorObj) {
            //         var val = errorObj[key];
            //         var processedKey = processKey(key);
            //         if (typeof val === 'string')
            //             resultingHtml += '<li>' + processedKey + ': ' + val + '</li>';
            //         else if (typeof val === 'object') {
            //             // Resource 0 should be actually shown as resource 1
            //             var pat = /Resource\s(\d+)/;
            //             var result = pat.exec(processedKey);
            //             if (result) {
            //                 processedKey = "Resource " + (parseInt(result[1]) + 1);
            //             }
            //
            //             resultingHtml += '<li>' + processedKey + ':';
            //             resultingHtml += '<ul>';
            //             resultingHtml += generateErrorHtml(val);
            //             resultingHtml += '</ul>';
            //             resultingHtml += '</li>';
            //         }
            //     }
            //     return resultingHtml;
            // };

            this.sandbox.subscribe('hdx-form-validation',
                function (message) {

                    if (message.type === 'reset' ) {
                        thisEl.addClass('hdx-invisible-element');
                        thisEl.removeClass('hdx-visible-element');
                        // if (errorEl.length){
                        //     errorEl.html('');
                        // }
                    }
                    else if (message.elementName === 'error_block' && message.errorBlock) {
                        thisEl.removeClass('hdx-invisible-element');
                        thisEl.addClass('hdx-visible-element');
                        if (message.errorBlock !== null) {
                          let errorItems = [];
                          Object.keys(message.errorBlock).forEach((item) => {
                            if (['server_or_connection_error', 'resource-list'].includes(item)) {
                              errorItems.push(message.errorBlock[item]);
                            }
                          });

                          let errorMsg = errorItems.join(';');
                          setMainErrorMessage(errorMsg);
                        } else {
                          setMainErrorMessage();
                        }

                        // if (errorEl.length){
                        //     var existingText = errorEl.html().trim();
                        //     var errorBlock = message.errorBlock;
                        //     var newHtml= generateErrorHtml(message.errorBlock);
                        //
                        //     moduleLog("The new error block HTML is: " + newHtml);
                        //
                        //     existingText += newHtml;
                        //     errorEl.html(existingText);
                        // }

                        thisEl.get(0).scrollIntoView();
                    }
                }
            );

        },
        moduleLog: function (message) {
            //console.log(message);
        },
        options: {
            element_name: null,
            default_error_message: null,
            key_mappings: {
                'Notes': 'description',
                'Groups list': 'location'
            },
            i18n: {
                description: _('Description'),
                location: _('Location')
            }
        }
    };
});
