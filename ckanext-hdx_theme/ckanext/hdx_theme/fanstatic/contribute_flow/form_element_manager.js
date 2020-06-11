"use strict";

ckan.module('hdx_form_element_manager', function ($, _) {
  return {
    initialize: function () {
      var moduleEl = this.el;
      var errorEl = this.el.find('.error-block');
      var errorWrapperEl = this.el.find('.controls');
      var controlGroupEl = this.el.find('.control-group');
      var elementName = this.options.element_name;
      var required = [];
      if(this.options.required)
              required = this.options.required.split(',');

      var broadcastChange = this.options.broadcast_change;

      var moduleLog = this.moduleLog;

      /**
       * Messages on the topic hdx-form-validation are
       * related to validation UI changes
       */
      this.sandbox.subscribe('hdx-form-validation',
        function (message) {
          if (message.type === 'reset') {
            errorWrapperEl.removeClass('error');
            errorEl.html('');
          } else if (message.type === 'private_changed') {
              var reqFlag = false;
              for ( var i=0; i< required.length; i++){
                if (message.newValue === required[i]){
                  reqFlag = true;
                  break;
                }
              }
              if (reqFlag)
                controlGroupEl.addClass('required');
              else
                controlGroupEl.removeClass('required');
          } else if (message.elementName === elementName) {
            try {
              if (errorWrapperEl.find("input").attr("data-module") === "slug-preview-slug") {
                errorWrapperEl.parents(".form-section").find(".slug-preview").hide();
                errorWrapperEl.parent().show();
              }

              errorWrapperEl.addClass('error');

              var existingText = errorEl.html().trim();
              var newText = existingText ? existingText + ", " + message.errorInfo : message.errorInfo;
              errorEl.html(newText);
            } catch (e) {
              if (e && e.hasOwnProperty('message')) {
                moduleLog(e.message);
              }

            }

          }
        }
      );


      if (elementName.indexOf('_other') > 0) {
        this.sandbox.subscribe(this.options.broadcast_channel,
          function (message) {
            /* If we get the message from the correct select element */
            //moduleLog('Processing broadcast message: ' + JSON.stringify(message));
            if (elementName.indexOf(message.srcElement) === 0) {
              if (message.newValue === 'Other' || message.newValue === 'hdx-other' || message.newValue === 'dataset_preview_show')
                moduleEl.show();
              else
                moduleEl.hide();
            }
          }
        );
      }
      if (broadcastChange) {
        var changeableEl = this.findChangeableElement(moduleEl);
        var isText = changeableEl.prop('type') === 'text';
        if (isText) {
          var textChangeHandler = function () {
            this.broadcastChange(changeableEl);
          }.bind(this);
          changeableEl.keyup(textChangeHandler);
          changeableEl.change(textChangeHandler);
          this.broadcastChange(changeableEl);
        } else {
          changeableEl.change(
            function (e) {
              this.broadcastChange(changeableEl);
            }.bind(this)
          );
          this.broadcastChange(changeableEl);
        }
      }

    },
    findChangeableElement: function (moduleEl) {
      var changeableEl = moduleEl.find('select');
      if (!changeableEl.length) {
        changeableEl = moduleEl.find('input');
      }
      return changeableEl;
    },
    /**
     * Gets the value of the form element and returns the message that will be broadcasted
     * @param {jQuery} changeableEl
     */
    createBroadcastMessage: function (changeableEl) {
      var newValue = changeableEl.prop('value');
      if (changeableEl.prop('type') === 'checkbox' && true === changeableEl.prop('checked')) {
        newValue = 'dataset_preview_show'
      }
      var message = {
        'srcElement': this.options.element_name,
        'newValue': newValue
      };
      return message;
    },
    broadcastChange: function (changeableEl) {
      var broadcastMessage = this.createBroadcastMessage(changeableEl);
      this.sandbox.publish(this.options.broadcast_channel, broadcastMessage);
    },
    moduleLog: function (message) {
      //console.log(message);
    },
    options: {
      element_name: null,
      required: null,
      broadcast_change: false,
      broadcast_channel: 'hdx-dataset-form-change'
    }
  };
});
