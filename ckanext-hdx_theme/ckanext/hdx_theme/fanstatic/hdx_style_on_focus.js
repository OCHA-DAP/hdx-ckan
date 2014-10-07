"use strict";

ckan.module('hdx_style_on_focus', function ($, _) {
	return {
		initialize: function () {
			jQuery.proxyAll(this, /_on/);

			if ( this.el.prop("tagName").toLowerCase() == 'input' ) {
				this.inputEl = this.el;
			}
			else {
				var inputEls = this.el.find("input");
				if ( inputEls != null && inputEls.length > 0 ) {
					this.inputEl = inputEls[0];
				}
			}
			if (this.inputEl) {
				$(this.inputEl).focus(this._onFocus);
				$(this.inputEl).blur(this._onBlur);
			}
			this.el.addClass("mx-init-complete");
		},
		_onFocus: function() {
			if ( this.options.target_element_id.length > 0 && this.options.class_name.length > 0 ) {
				var targetEl = $('#'+this.options.target_element_id);
				targetEl.addClass(this.options.class_name);
			}
		},
		_onBlur: function() {
			if ( this.options.target_element_id.length > 0 && this.options.class_name.length > 0 ) {
				var targetEl = $('#'+this.options.target_element_id);
				targetEl.removeClass(this.options.class_name);
			}
		},
		options: {
			target_element_id: '',
			class_name: ''
		}
	};
});