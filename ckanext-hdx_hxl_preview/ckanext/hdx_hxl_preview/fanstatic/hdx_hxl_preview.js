ckan.module('hdx-hxl-preview', function ($, _) {
    return {
        initialize: function () {
            console.log("hxlpreview: initializing resize");
            var setHeight = function (element, newHeight) {
                var maxHeight = 700;
                element.style.height = (newHeight < maxHeight ? newHeight : maxHeight) + 'px';
                console.log("hxlpreview: Height is " + element.style.height);
            };
            $('iframe.hxl-preview-iframe').load(function () {

                    var self = this;
                    var iBody = this.contentWindow.document.body;
                    var iBodyHeight = iBody.offsetHeight;
                    setHeight(self, iBodyHeight);
                    // this.style.height = iBodyHeight + 'px';
                    var checkResize = function () {
                        if (iBody.offsetHeight != iBodyHeight) {
                            iBodyHeight = iBody.offsetHeight;
                            setHeight(self, iBodyHeight);
                            // self.style.height = iBodyHeight + 'px';
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