"use strict";

ckan.module('hdx_visibility_toggler', function ($, _) {
  return {
    initialize: function () {
    	$.proxyAll(this, /_on/);
    	this.el.click(this._onClick);
    	this.allButtonEl = this.el.find(this.options.all_button_selector);
    	this.filterButtonEl = this.el.find(this.options.filter_button_selector);
    	this.toHideEls = $(this.options.elements_to_hide_selector);
    	this.toShowEls = $(this.options.elements_to_show_selector);
    },
    _onClick: function(event) {
		  if ( this.allButtonEl.hasClass(this.options.selected_button_class) ) {
			  this.toHideEls.hide();
			  this.toShowEls.show();
			  this.allButtonEl.removeClass(this.options.selected_button_class);
			  this.allButtonEl.addClass(this.options.disabled_button_class);
			  this.filterButtonEl.removeClass(this.options.disabled_button_class);
			  this.filterButtonEl.addClass(this.options.selected_button_class);
		  }
		  else {
		    this.toHideEls.show();
		    this.toShowEls.hide();
		    this.filterButtonEl.removeClass(this.options.selected_button_class);
			  this.filterButtonEl.addClass(this.options.disabled_button_class);
			  this.allButtonEl.removeClass(this.options.disabled_button_class);
			  this.allButtonEl.addClass(this.options.selected_button_class);
      }
		  this.allButtonEl.blur();
      this.filterButtonEl.blur();
		  event.preventDefault();
		  event.stopPropagation();
	},
    options: {
    	elements_to_hide_selector: '',
      elements_to_show_selector: '',
      all_button_selector: '',
      filter_button_selector: '',
      selected_button_class: 'btn-primary',
      disabled_button_class: 'btn-default'
    }
  };
});
