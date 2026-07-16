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

      // ── Tooltip triggers ──────────────────────────────────────
      // Hover/focus visibility is handled by CSS (.c-info-icon:hover ~ .c-tooltip etc.).
      // JS manages the is-open state for click/tap, aria-expanded, and keyboard close.
      var tooltipWraps = header.querySelectorAll('.c-tooltip-anchor');

      tooltipWraps.forEach(function (wrap) {
        var icon = wrap.querySelector('.c-info-icon');
        if (!icon) return;

        icon.addEventListener('click', function (e) {
          e.stopPropagation();
          var isOpen = icon.classList.contains('is-open');
          closeAllTooltips();
          if (!isOpen) {
            icon.classList.add('is-open');
            icon.setAttribute('aria-expanded', 'true');
          }
        });
      });
    });

    function closeAllTooltips() {
      headers.forEach(function (header) {
        header.querySelectorAll('.c-tooltip-anchor .c-info-icon.is-open, .c-tooltip-anchor .c-info-icon[aria-expanded="true"]')
          .forEach(function (icon) {
            icon.classList.remove('is-open');
            icon.setAttribute('aria-expanded', 'false');
          });
      });
    }

    // Escape closes any open tooltip and returns focus to its trigger (V-13)
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var openIcon = null;
      headers.forEach(function (header) {
        openIcon = openIcon || header.querySelector('.c-info-icon.is-open');
      });
      if (openIcon) {
        closeAllTooltips();
        openIcon.focus();
      }
    });

    document.addEventListener('click', closeAllTooltips);
  });
})();
