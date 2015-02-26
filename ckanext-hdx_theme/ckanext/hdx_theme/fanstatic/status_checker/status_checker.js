"use strict";

ckan.module('status_checker', function($, _) {
	return {
		initialize : function() {
            $.proxyAll(this, /_on/);
            var endpoint = this.options.endpoint;
			var client = this.sandbox.client;
            var params = '?' + this.options.params
            client.call('GET', endpoint, params, this._onLoad);
		},
        _onLoad: function(response) {
            if (response.success) {

                this.el.html(response.result.status)
            }
        },
		options : {
			endpoint: null,
            params: null
		}
	};
});