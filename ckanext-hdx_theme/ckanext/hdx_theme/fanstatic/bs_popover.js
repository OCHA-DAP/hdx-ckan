"use strict";

ckan.module('bs_popover', function($, _) {
	return {
		initialize : function() {
			var content = this.options.content;
			if (this.options.social_div_id) {
				var contentEl 	= $('#'+this.options.social_div_id);
				var newContent 	= contentEl.html();
				contentEl.remove();
				if ( newContent && newContent.length > 0 )
					content = newContent;
			}
			
			var popoverWrapper 	= document.body; 
			if (this.options.social_wrapper_div_id) {
				var tempPopoverWrapper	= $('#'+this.options.social_wrapper_div_id);
				if (tempPopoverWrapper) {
					popoverWrapper = tempPopoverWrapper;
					this.popoverWrapper	= tempPopoverWrapper;
				}
			}
			
			this.el.popover({
				trigger : this.options.trigger,
				placement : this.options.placement,
				content : content,
				title : this.options.title,
				html: true,
				container: popoverWrapper
			});
			
			this.el.on('click.bs_popover', $.proxy(this._onClick, this));
		},
		_onClick: function(e){
			this.el.popover("show");
			e.stopPropagation();
			$('html').on('click.bs_popover', $.proxy(this._onOtherClick, this));
		},
		_onOtherClick:  function(e) {
			this.el.popover("hide");
			$('html').off('click.bs_popover');
				
		},
//		_isVisible: function() {
//			var popoverDivEls	= this.popoverWrapper.find('.popover');
//			if (popoverDivEls && popoverDivEls.length > 0 )
//				return true;
//			
//			return false;
//		},
		options : {
			placement : 'top',
			trigger : 'manual',
			content : 'Empty !',
			title : 'No Title !',
			social_div_id : null,
			social_wrapper_div_id: null

		}
	};
});