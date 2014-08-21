"use strict";

ckan.module('hdx_clickable_div', function ($, _) {
  return {
    initialize: function () {
    	jQuery.proxyAll(this, /_on/);
    	this.el.click(this._onClick);
    	this.el.addClass("mx-init-complete");
    },
    _onClick: function() {
		  if ( this.options.popup_id.length > 0 ) {
			  var popupEl = $('#'+this.options.popup_id);
			  popupEl.modal();
		  }
		  else if ( this.options.url.length > 0 )
			  window.location = this.options.url;
	},
    options: {
    	url: '',
    	popup_id: ''
    }
  };
});