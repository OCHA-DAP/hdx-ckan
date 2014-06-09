"use strict";

ckan.module('trigger_click_hash', function($, _) {
	return {
		initialize : function() {
			var hash = window.location.hash;
			if ( hash==this.options.expected_hash ){
				this.el.trigger('click');
			}
		},
		options : {
			expected_hash : '#add-member'
		}
	};
});