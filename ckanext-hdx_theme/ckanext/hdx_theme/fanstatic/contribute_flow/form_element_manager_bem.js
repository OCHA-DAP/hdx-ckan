"use strict";

ckan.module('hdx_form_element_manager_bem', function ($, _) {
  var selectors = {
    'groups_list': 'locations',
    'license': 'license_id'
  };

  return {
    initialize: function () {
      var moduleEl = this.el;
      var errorEl = this.el.find('.invalid-feedback');
      var wrapperEl = this.el.find('[class*="-field"]');

      var elementName = this.options.element_name;
      var selectorName = selectors[elementName] || elementName;
      var $element = $('[name="' + selectorName + '"]');

      var $requiredLabel = $element.parent().parent().find('[class*="-field__required"]');
      var required = [];
      if (this.options.required) {
        required = this.options.required.split(',');
      }

      var broadcastChange = this.options.broadcast_change;

      var moduleLog = this.moduleLog;

      /**
       * Messages on the topic hdx-form-validation are
       * related to validation UI changes
       */
      this.sandbox.subscribe('hdx-form-validation',
        function (message) {
          if (message.type === 'reset') {
            errorEl.html('');
            $element.removeClass('is-invalid');
          } else if (message.type === 'private_changed') {
            var reqFlag = false;
            for (var i = 0; i < required.length; i++) {
              if (message.newValue === required[i]) {
                reqFlag = true;
                break;
              }
            }
            if (reqFlag) {
              $requiredLabel.removeClass('d-none');
            } else {
              $requiredLabel.addClass('d-none');
            }
          } else if (message.elementName === elementName) {
            try {
              if (wrapperEl.find("input").attr("data-module") === "slug-preview-slug") {
                wrapperEl.parents(".form-section").find(".slug-preview").hide();
                wrapperEl.parent().show();
              }
              var existingText = errorEl.html().trim();
              var newText = existingText ? existingText + ", " + message.errorInfo : message.errorInfo;
              $element.addClass('is-invalid');
              errorEl.html(newText);
            } catch (e) {
              if (e && e.hasOwnProperty('message')) {
                moduleLog(e.message);
              }
            }
          }
        }
      );

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
