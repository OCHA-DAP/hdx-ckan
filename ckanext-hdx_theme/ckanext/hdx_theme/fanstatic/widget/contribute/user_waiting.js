"use strict";

ckan.module('hdx_user_waiting', function($, _) {
    return {
        initialize: function () {
            this.messageBox = this.el.find(".user-waiting-text");

            this.sandbox.subscribe('hdx-user-waiting',
                function (message) {
                    var hideOrShow = function(){
                        if ( message.show ) {
                            this.el.show();
                            this.visible = true;
                        }
                        else {
                            this.el.hide();
                            this.visible = false;
                        }
                        this.messageBox.text(message.message);
                    }.bind(this);
                    if ( !this.visible )
                        hideOrShow();
                    else
                        setTimeout(hideOrShow, 500);
                }.bind(this)
            )

        },
        options: {
            widget_wrapper_id: null
        }
    }
});