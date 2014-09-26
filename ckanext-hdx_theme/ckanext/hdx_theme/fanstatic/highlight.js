$(document).ready(function() {
  $(".toHighlight").highlight("Population");
});


"use strict";

ckan.module('highlight', function ($, _) {
  return {
    initialize: function () {
      $(this.el).highlight(this.options.text);
    },
    options: {
    	text: ''
    }
  };
});
