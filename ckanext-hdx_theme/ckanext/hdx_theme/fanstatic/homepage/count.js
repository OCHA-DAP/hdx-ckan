// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('count', function ($, _) {
  return {
    anim: (function($) {
        $.fn.animateNumbers = function(stop, commas, duration, ease) {
          return this.each(function() {
            var $this = $(this);
            var start = parseInt($this.text().replace(/,/g, ""));
            commas = (commas === undefined) ? true : commas;
            $({value: start}).animate({value: stop}, {
              duration: duration == undefined ? 1000 : duration,
              easing: ease == undefined ? "swing" : ease,
              step: function() {
                $this.text(Math.floor(this.value));
                if (commas) { $this.text($this.text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,")); }
              },
              complete: function() {
                if (parseInt($this.text()) !== stop) {
                  $this.text(stop);
                  if (commas) { $this.text($this.text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,")); }
                }
              }
            });
          });
        };
      })(jQuery),
    initialize: function () {
      const currentElement = this.el;
      const count = parseInt($(currentElement).text());
      $(currentElement).text("0");
      $(currentElement).animateNumbers(count, true, 1000);
      
    }
  };
});
