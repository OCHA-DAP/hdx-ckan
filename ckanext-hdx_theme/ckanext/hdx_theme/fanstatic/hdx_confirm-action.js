this.ckan.module('hdx_confirm-action', function (jQuery, _) {
  return {
    /* An object of module options */
    options: {
      /* Locale options can be overidden with data-module-i18n attribute */
      i18n: {
        heading: _('Please Confirm Action'),
        content: _('Are you sure you want to perform this action?'),
        confirm: _('Confirm'),
        delete: null,
        cancel: _('Cancel'),
        error: _('There was a problem performing this action'), /* Text to show in the modal if the POST was not successful */
      },
      template: [
        '<div class="modal">',
        '<div class="modal-dialog">',
		'<div class="modal-content">',
        '<div class="modal-header">',
        '<button type="button" class="close" data-dismiss="modal">×</button>',
        '<h3 class="modal-title"></h3>',
        '</div>',
        '<div class="modal-body"></div>',
        '<div class="modal-footer">',
        '<button class="btn btn-empty btn-large btn-cancel"></button>',
        '<button class="btn btn-primary btn-large"></button>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
      ].join('\n'),

      /* Normally this js module would do a normal (non-AJAX) request to the server and the sever would
       * redirect the browser to a specific url.
       *
       * If you want the browser to go to a specific url after the POST set success_url. In this case
       * the POST will be done via AJAX.
       * In this case also check the params i18n.error, post_data, is_json
       */
      success_url: null,

      post_data: null, /* body of the AJAX POST */
      is_json: false
    },

    /* Sets up the event listeners for the object. Called internally by
     * module.createInstance().
     *
     * Returns nothing.
     */
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },

    /* Presents the user with a confirm dialogue to ensure that they wish to
     * continue with the current action.
     *
     * Examples
     *
     *   jQuery('.delete').click(function () {
     *     module.confirm();
     *   });
     *
     * Returns nothing.
     */
    confirm: function () {
      this.sandbox.body.append(this.createModal());
      this.modal.modal('show');

      // Center the modal in the middle of the screen.
      this.modal.css({
        'margin-top': this.modal.height() * -0.5,
        'top': '50%'
      });
    },

    /* Performs the action for the current item.
     *
     * Returns nothing.
     */
    performAction: function () {

      var successUrl = this.options.success_url;
      var originalBodyText = this.i18n('content');
      var errorBodyText = originalBodyText + "<div class='red'>" + this.i18n('error') + "{}</div>";
      var modal = this.modal;
      var uri = this.el.attr('href');

      var successHandler = function (data, status) {
        if (status == 'success') {
          window.top.location = successUrl;
        }
        else {
          modal.find('.modal-body').html(errorBodyText.replace('{}', ''));
        }
      };

      /* IF we have success URL we do an AJAX POST and then go to the URL if it succeeded */
      if (successUrl) {
        if (this.options.is_json) {
          $.ajax({
            beforeSend: function (xhrObj) {
              xhrObj.setRequestHeader("Content-Type", "application/json");
              xhrObj.setRequestHeader("Accept", "application/json");
            },
            type: "POST",
            url: uri,
            data: JSON.stringify(this.options.post_data),
            dataType: "json",
            success: successHandler,
            error: function (xhr, status, errorThrown) {
              var errorMsg = errorThrown;
              try {
                var jsonErrorMsg = xhr.responseJSON.error.message;
                errorMsg = jsonErrorMsg ? jsonErrorMsg : errorMsg;
              }
              catch(e){}
              modal.find('.modal-body').html(errorBodyText.replace('{}', ": " + errorMsg));
            }
          });
        }
        else {
          $.post(uri,this.options.post_data,successHandler);
        }
      }
      /* ELSE stick to the original behaviour of adding a FORM elemennt to the body and submitting it */
      else {
        // create a form and submit it to confirm the deletion
        var form = jQuery('<form/>', {
          action: uri,
          method: 'POST'
        });
        form.appendTo('body').submit();
      }

    },

    /* Creates the modal dialog, attaches event listeners and localised
     * strings.
     *
     * Returns the newly created element.
     */
    createModal: function () {
      if (!this.modal) {
        var element = this.modal = jQuery(this.options.template);
        element.on('click', '.btn-primary', this._onConfirmSuccess);
        element.on('click', '.btn-cancel', this._onConfirmCancel);
        element.modal({show: false});

        element.find('h3').text(this.i18n('heading'));
        element.find('.modal-body').text(this.i18n('content'));
        var mainButton = element.find('.btn-primary');
        if (this.i18n('delete')){
          mainButton.text(this.i18n('delete'));
          mainButton.addClass('btn-danger');
        } else {
          mainButton.text(this.i18n('confirm'));
        }



        element.find('.btn-cancel').text(this.i18n('cancel'));
      }
      return this.modal;
    },

    /* Event handler that displays the confirm dialog */
    _onClick: function (event) {
      event.preventDefault();
      this.confirm();
    },

    /* Event handler for the success event */
    _onConfirmSuccess: function (event) {
      this.performAction();
    },

    /* Event handler for the cancel event */
    _onConfirmCancel: function (event) {
      this.modal.modal('hide');
    }
  };
});
