"use strict";

ckan.module('hdx_show_more', function ($, _) {
  return {
    initialize: function () {
      this.el.find('p').more({wordBreak: true, length: 370});
      this.el.css('visibility','visible')
    }
  };
});