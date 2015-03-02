"use strict";

ckan.module('status_checker', function($, _) {
	return {
		initialize : function() {
            $.proxyAll(this, /_on/);
            $.proxyAll(this, /cb/);
            this.cbCheck();

		},
        cbCheck: function(){
            var client = this.sandbox.client;
            var endpoint = this.options.endpoint;
            var params = '?' + this.options.params
            client.call('GET', endpoint, params, this._onLoad);
        },
        _onLoad: function(response) {
            if (response.success) {
                var statusChecker = this.el.find('div')[0];
                var statusCheckerEl = $(statusChecker);
                if ( response.result.status == 'pending' ) {
                    statusCheckerEl.attr("class", 'loading')
                    setTimeout(this.cbCheck, 5000)
                }
                else if ( response.result.status == 'error' ) {
                    statusCheckerEl.attr("class", 'glyphicon glyphicon-remove icon-remove')
                }
                else if ( response.result.status == 'complete' ) {
                    statusCheckerEl.attr("class", 'glyphicon glyphicon-ok icon-ok')
                }
                this.el.attr('title', response.result.status);
            }
        },
		options : {
			endpoint: null,
            params: null
		}
	};
});