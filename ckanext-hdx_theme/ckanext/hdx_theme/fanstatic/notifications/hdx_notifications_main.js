ckan.module('hdx_notifications_main', function ($, _) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);

            if (this.options.type === 'header icon') {
                this.initHeaderIcon();
            }
            else if (this.options.type === 'item') {
                this.initItem();
            }
        },
        initItem() {
            var href = this.el.attr('href');

            this.data = {
                type: this.options.type,
                personal: this.options.personal,
                destinationUrl: href
            };

            this.el.click(this._onItemClick);
        },
        _onItemClick(e) {
            var promise = hdxUtil.analytics.sendNotificationInteractionEvent(this.data);

            var eventPrevented = hdxUtil.eventUtil.postponeClickDefaultIfNotNewTab(e, promise);
        },
        initHeaderIcon() {
            this.data = {
                type: this.options.type,
                count: this.options.count
            };

            this.el.find('.dropdown').on('shown.bs.dropdown', this._onDropdownShown);
        },
        _onDropdownShown: function (event) {
            hdxUtil.analytics.sendNotificationInteractionEvent(this.data);
        },
        options: {
            type: null,
            count: null,
            personal: true
        }
    };
});
