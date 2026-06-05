(function () {
  'use strict';

  var MARGIN_PX = 5;  // gap between dot bottom and bar top

  function initBarchart(barsEl) {
    var bars     = barsEl.querySelectorAll('.hdx-v2-barchart__bar');
    var inner    = barsEl.closest('.hdx-v2-barchart__inner');
    var label    = inner.querySelector('.hdx-v2-barchart__label');
    var nameEl   = label.querySelector('.hdx-v2-barchart__label-name');
    var countEl  = label.querySelector('.hdx-v2-barchart__label-count');
    var interval = parseInt(barsEl.getAttribute('data-interval'), 10) || 2000;
    var activeIdx = Math.floor(Math.random() * bars.length);

    function positionLabel(bar) {
      var barRect   = bar.getBoundingClientRect();
      var innerRect = inner.getBoundingClientRect();

      // Horizontal: center label over bar; overflow is clipped by section's overflow:hidden
      var barCenter = (barRect.left - innerRect.left) + barRect.width / 2;
      var offsetX   = barCenter - label.offsetWidth / 2;

      // Vertical: dot bottom sits MARGIN_PX above the bar top
      var barTop  = barRect.top - innerRect.top;
      var offsetY = barTop - MARGIN_PX - label.offsetHeight;
      offsetY = Math.max(offsetY, 0);

      label.style.setProperty('--label-offset', offsetX + 'px');
      label.style.setProperty('--label-top', offsetY + 'px');
    }

    function nextRandom() {
      if (bars.length <= 1) { return 0; }
      var next;
      do { next = Math.floor(Math.random() * bars.length); } while (next === activeIdx);
      return next;
    }

    function activate(idx) {
      bars[activeIdx].classList.remove('is-active');
      activeIdx = idx;
      bars[activeIdx].classList.add('is-active');
      nameEl.textContent  = bars[activeIdx].getAttribute('data-name');
      countEl.textContent = bars[activeIdx].getAttribute('data-count') + ' datasets';
      positionLabel(bars[activeIdx]);
    }

    activate(activeIdx);
    setInterval(function () { activate(nextRandom()); }, interval);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var barsEl = document.querySelector('.hdx-v2-barchart__bars');
    if (barsEl) { initBarchart(barsEl); }
  });
}());
