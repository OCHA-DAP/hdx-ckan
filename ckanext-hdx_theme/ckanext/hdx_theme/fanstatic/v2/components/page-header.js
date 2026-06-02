(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var header = document.querySelector('.hdx-v2-page-header');
    if (!header) return;

    // ── Source "View more" — show only when text overflows ───
    var sourceMeta  = header.querySelector('[data-header-meta="source"]');
    if (sourceMeta) {
      var sourceSpan    = sourceMeta.querySelector('.hdx-v2-page-header__meta-value--source span');
      var viewMoreLink  = sourceMeta.querySelector('.hdx-v2-page-header__source-view-more');
      if (sourceSpan && viewMoreLink && sourceSpan.scrollWidth > sourceSpan.clientWidth) {
        viewMoreLink.style.display = 'inline-flex';
      }
    }

    // ── Tooltip triggers (click/tap for mobile; hover handled by CSS) ──
    var tooltipWraps = header.querySelectorAll('.c-tooltip-anchor');

    function closeAllTooltips() {
      tooltipWraps.forEach(function (wrap) {
        var icon = wrap.querySelector('.c-info-icon');
        if (icon) icon.classList.remove('is-open');
      });
    }

    tooltipWraps.forEach(function (wrap) {
      var icon = wrap.querySelector('.c-info-icon');
      if (!icon) return;

      icon.addEventListener('click', function (e) {
        e.stopPropagation();
        var isOpen = icon.classList.contains('is-open');
        closeAllTooltips();
        if (!isOpen) icon.classList.add('is-open');
      });
    });

    document.addEventListener('click', closeAllTooltips);
  });
})();
