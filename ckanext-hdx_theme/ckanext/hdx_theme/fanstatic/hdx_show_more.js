"use strict";

ckan.module('hdx_show_more', function ($, _) {
  return {
	options: {
		points: 370
	},
    initialize: function () {
//      this.el.find('span').more({wordBreak: true, length: 370});
      this.el.css('visibility','visible');
      var innerDiv = this.el;
      innerDiv.expander({
          slicePoint:	this.options.points,
          expandPrefix:     ' ',
          expandText:       ' ... More',
          userCollapsePrefix: ' ',
          userCollapseText: 'Less'
        }
      );
    }
  };
});