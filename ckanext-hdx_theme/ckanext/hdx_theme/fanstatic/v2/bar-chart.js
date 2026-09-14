(function () {
  'use strict';

  function initBarchart(barsEl) {
    var groups    = barsEl.querySelectorAll('.hdx-v2-barchart__bar-group');
    var inner     = barsEl.closest('.hdx-v2-barchart__inner');
    var announcer = inner.querySelector('[data-barchart-announcer]');
    var interval  = parseInt(barsEl.getAttribute('data-interval'), 10) || 2500;
    var activeIdx = Math.floor(Math.random() * groups.length);

    function nextRandom() {
      if (groups.length <= 1) { return 0; }
      var next;
      do { next = Math.floor(Math.random() * groups.length); } while (next === activeIdx);
      return next;
    }

    function activate(idx) {
      groups[activeIdx].classList.remove('is-active');
      activeIdx = idx;
      groups[activeIdx].classList.add('is-active');
      if (announcer) {
        announcer.textContent = groups[activeIdx].getAttribute('data-name') + ', ' +
          groups[activeIdx].getAttribute('data-count') + ' datasets';
      }
    }

    activate(activeIdx);
    setInterval(function () { activate(nextRandom()); }, interval);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var barsEl = document.querySelector('.hdx-v2-barchart__bars');
    if (barsEl) { initBarchart(barsEl); }
  });
}());
