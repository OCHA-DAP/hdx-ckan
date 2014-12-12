"use strict";

ckan.module('hdx_show_more', function ($, _) {
  return {
    initialize: function () {
//      this.el.find('span').more({wordBreak: true, length: 370});
      this.el.css('visibility','visible');
      var innerDiv = this.el.find('div');
      innerDiv.expander({
          slicePoint:       370,
          expandPrefix:     ' ',
          expandText:       'More',
          userCollapsePrefix: ' ',
          userCollapseText:       'Less'
        }
      );
    }
  };
});