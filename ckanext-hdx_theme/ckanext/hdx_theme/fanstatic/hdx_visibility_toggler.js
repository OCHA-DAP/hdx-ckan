"use strict";

ckan.module('hdx_visibility_toggler', function ($, _) {
  return {
    initialize: function () {
    	$.proxyAll(this, /_on/);
    	this.el.click(this._onClick);
    	this.allButtonEl = this.el.find(this.options.all_button_selector);
    	this.filterButtonEl = this.el.find(this.options.filter_button_selector);
    	this.targetEls = $(this.options.target_element_selector);
    },
    _onClick: function(event) {
		  if ( this.allButtonEl.hasClass(this.options.selected_button_class) ) {
			  this.targetEls.hide();
			  this.allButtonEl.removeClass(this.options.selected_button_class);
			  this.allButtonEl.addClass(this.options.disabled_button_class);
			  this.filterButtonEl.removeClass(this.options.disabled_button_class);
			  this.filterButtonEl.addClass(this.options.selected_button_class);
		  }
		  else {
		    this.targetEls.show();
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
    	target_element_selector: '',
      all_button_selector: '',
      filter_button_selector: '',
      selected_button_class: 'btn-primary',
      disabled_button_class: 'btn-default'
    }
  };
});
