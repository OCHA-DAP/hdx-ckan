"use strict";

ckan.module('hdx_custom_dataviz_show', function($, _) {
  return {
    initialize: function () {
      // The first option will be the active one
      if (this.options.index === 0) {
        this.deactivate();
      }
      else {
        this.activate();
      }
      this.targetEl = $('#' + this.options.target);

      this.el.click(this.onClick.bind(this));

      this.sandbox.subscribe('hdx_custom_dataviz_show', function (index) {
        if (index !== parseInt(this.options.index)) {
          this.activate();
        }
        else {
          this.targetEl.attr('src',this.options.url);
          this.deactivate();
        }
      }.bind(this));
    },
    deactivate: function() {
      this.el.addClass('viz-deactivated');
      this.currentlyShown = true;
      var fullscreen_el = $('#pkg_fullscreen');
      fullscreen_el.attr('href',this.options.url);
    },
    activate: function() {
      this.el.removeClass('viz-deactivated');
      this.currentlyShown = false;
    },
    onClick: function() {
      if (!this.currentlyShown) {
        this.sandbox.publish('hdx_custom_dataviz_show', this.options.index);
      }
    },
    options: {
      index: null,
      target: null,
      url: null
    }
  };
});
