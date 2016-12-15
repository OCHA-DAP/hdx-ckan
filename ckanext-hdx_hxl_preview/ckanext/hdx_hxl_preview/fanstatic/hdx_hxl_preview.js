ckan.module('hdx-hxl-preview', function ($, _) {
    return {
        initialize: function () {
            $('iframe.hxl-preview-iframe').load(function () {
                    var self = this;
                    var iBody = this.contentWindow.document.body;
                    var iBodyHeight = iBody.offsetHeight;
                    this.style.height = iBodyHeight + 'px';
                    var checkResize = function () {
                        if (iBody.offsetHeight != iBodyHeight) {
                            iBodyHeight = iBody.offsetHeight;
                            self.style.height = iBodyHeight + 'px';
                        }
                    };
                    var timer = setInterval(checkResize, 500);
                }
            );
        },
        options: {
            //placement: 'top',
            //trigger: 'hover'
        }
    };
});