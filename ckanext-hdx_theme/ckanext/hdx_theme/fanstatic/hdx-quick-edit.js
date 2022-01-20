/*
 *
 *
 */
this.ckan.module('hdx-quick-edit', function (jQuery, _, i18n) {
  return {
    /* Default options for the module */
    options: {
      template: [
      ]
    },

    /* Initializes the module,  creates new elements and registers event
     * listeners etc. This method is called by ckan.initialize() if there
     * is a corresponding element on the page.
     *
     * Returns nothing.
     */
    initialize: function() {
      jQuery.proxyAll(this, /_on/);
      let anchor = this.options.anchor;
      let dataset = this.options.dataset;
      //base template
      this.options.template.push(
        `
          <a class="btn btn-square quick-link" href="#" onclick="contributeAddDetails('${dataset}', 'quick-edit', '#${anchor}'); return false;">
            Edit
          </a>
        `
      );

      this.edit = jQuery(this.options.template.join('\n'));
      this.el.append(this.edit);
      this.el.addClass('quick-edit');
    },
  }
});
