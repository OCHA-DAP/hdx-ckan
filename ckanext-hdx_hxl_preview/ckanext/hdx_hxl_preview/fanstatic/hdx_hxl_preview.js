ckan.module('hdx-hxl-preview', function ($, _) {
    return {
        initialize: function () {
            console.log("hxlpreview: initializing resize");
            var setHeight = function (element, newHeight) {
                var maxHeight = 700;
                element.style.height = (newHeight < maxHeight ? newHeight : maxHeight) + 'px';
                console.log("hxlpreview: Height is " + element.style.height);
            };
            var iframeEl = this.el[0];
            var iBodyHeight;
            $('iframe.hxl-preview-iframe').load(function () {
                    var iBody = iframeEl.contentWindow.document.body;
                    var iBodyHeight = iBody.offsetHeight;
                    setHeight(iframeEl, iBodyHeight);
                    // this.style.height = iBodyHeight + 'px';
                }
            );

            var checkResize = function () {
                var iBody = iframeEl.contentWindow.document.body;
                if (iBody.offsetHeight != iBodyHeight) {
                    iBodyHeight = iBody.offsetHeight;
                    setHeight(iframeEl, iBodyHeight);
                    // self.style.height = iBodyHeight + 'px';
                }
            };
            var timer = setInterval(checkResize, 500);
            console.log("hxlpreview: resize timer initialized");
        },
        options: {
            //placement: 'top',
            //trigger: 'hover'
        }
    };
});