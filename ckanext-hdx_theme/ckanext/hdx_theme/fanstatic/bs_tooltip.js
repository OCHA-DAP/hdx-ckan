"use strict";

ckan.module('bs_tooltip', function ($, _) {
  return {
    initialize: function () {
      const options = {
        trigger: this.options.trigger,
        placement: this.options.placement
      };
      if (this.options.inner_class) {
        options.template =
          `<div class="tooltip" role="tooltip">
            <div class="tooltip-arrow"></div>
            <div class="tooltip-inner ${this.options.inner_class}"></div>
           </div>`;
      }
      this.el.tooltip(options);
    },
    options: {
    	placement: 'top',
    	trigger: 'hover',
      inner_class: null
    }
  };
});
