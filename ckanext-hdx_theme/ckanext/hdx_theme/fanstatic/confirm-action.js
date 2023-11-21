this.ckan.module('confirm-action', function (jQuery, _) {
  return {
    /* An object of module options */
    options: {
      /* Locale options can be overidden with data-module-i18n attribute */
      i18n: {
        heading: _('Please Confirm Action'),
        content: _('Are you sure you want to perform this action?'),
        confirm: _('Confirm'),
        cancel: _('Cancel')
      },
      template: [
        '<div class="modal">',
        '<div class="modal-dialog modal-dialog-centered">',
    		'<div class="modal-content">',
        '<div class="modal-header">',
        '<h3 class="modal-title"></h3>',
        '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>',
        '</div>',
        '<div class="modal-body"></div>',
        '<div class="modal-footer">',
        '<button class="btn btn-cancel" data-bs-dismiss="modal></button>',
        '<button class="btn btn-primary"></button>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
      ].join('\n')
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
      this.modal.show();
    },

    /* Performs the action for the current item.
     *
     * Returns nothing.
     */
    performAction: function () {
      // create a form and submit it to confirm the deletion
      var form = jQuery('<form/>', {
        action: this.el.attr('href'),
        method: 'POST'
      });
      form.appendTo('body').submit();
    },

    /* Creates the modal dialog, attaches event listeners and localised
     * strings.
     *
     * Returns the newly created element.
     */
    createModal: function () {
      if (!this.modal) {
        var $element = jQuery(this.options.template);
        $element.on('click', '.btn-primary', this._onConfirmSuccess);
        $element.on('click', '.btn-cancel', this._onConfirmCancel);
        $element.find('h3').text(this.i18n('heading'));
        $element.find('.modal-body').text(this.i18n('content'));
        $element.find('.btn-primary').text(this.i18n('confirm'));
        $element.find('.btn-cancel').text(this.i18n('cancel'));
        this.modal = new bootstrap.Modal($element.get(0));
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
      this.modal.hide();
    }
  };
});
