"use strict";

ckan.module('bs_tooltip', function ($, _) {
  return {
    initialize: function () {
      this.el.tooltip({ 
    	  trigger: this.options.trigger,
          placement: this.options.placement});
    },
    options: {
    	placement: 'top',
    	trigger: 'hover'
    }
  };
});