(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var headers = document.querySelectorAll('.c-page-header');
    if (!headers.length) return;

    headers.forEach(function (header) {
      // ── "View more" on overflow — reveal only when the value truncates ──
      var overflowItems = header.querySelectorAll('[data-header-meta-overflow]');
      overflowItems.forEach(function (item) {
        var valueSpan    = item.querySelector('.c-page-header__meta-value--truncate span');
        var viewMoreLink = item.querySelector('.c-page-header__meta-view-more');
        if (valueSpan && viewMoreLink && valueSpan.scrollWidth > valueSpan.clientWidth) {
          viewMoreLink.style.display = 'inline-flex';
        }
      });
    });
    // Tooltip open/close + positioning for .c-tooltip-anchor is handled
    // site-wide by v2/components/tooltip.js, not scoped to the header.
  });
})();
