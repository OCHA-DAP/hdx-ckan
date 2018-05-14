this.ckan.module('hdx_terms_checkbox', function (jQuery, _) {
  return {
    /* An object of module options */
    options: {
      button: null
    },
    checkboxEl: null,
    buttonEl: null,

    /* Sets up the event listeners for the object. Called internally by
     * module.createInstance().
     *
     * Returns nothing.
     */
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.checkboxEl = jQuery(jQuery(this.el).find("input[type='checkbox']")[0]);
      this.checkboxEl.on('change', this._onClick);
      this.buttonEl = jQuery(jQuery("#" + this.options.button)[0]);

      this._updateButtonStatus();
    },

    /* Event handler that displays the confirm dialog */
    _onClick: function (event) {
      this._updateButtonStatus();
    },

    _updateButtonStatus: function () {
      if (this.checkboxEl.is(":checked")) {
          this.buttonEl.removeClass("disabled");
      } else {
          this.buttonEl.addClass("disabled");
      }
    }

  };
});
