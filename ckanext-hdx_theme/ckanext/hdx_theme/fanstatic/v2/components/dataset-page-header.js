(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var header = document.querySelector('.hdx-v2-dataset-header');
    if (!header) return;

    // ── Source "View more" — show only when text overflows ───
    var sourceMeta  = header.querySelector('#metadata-source');
    if (sourceMeta) {
      var sourceSpan    = sourceMeta.querySelector('.hdx-v2-dataset-header__meta-value--source span');
      var viewMoreLink  = sourceMeta.querySelector('.hdx-v2-dataset-header__source-view-more');
      if (sourceSpan && viewMoreLink && sourceSpan.scrollWidth > sourceSpan.clientWidth) {
        viewMoreLink.style.display = 'inline-flex';
      }
    }

    // ── Tooltip triggers ─────────────────────────────────────
    var tooltipWraps = header.querySelectorAll('.hdx-v2-dataset-header__tooltip-wrap');

    function closeAllTooltips() {
      tooltipWraps.forEach(function (wrap) {
        var triggerBtn = wrap.querySelector('.c-button');
        if (triggerBtn) triggerBtn.setAttribute('aria-expanded', 'false');
      });
    }

    tooltipWraps.forEach(function (wrap) {
      var triggerBtn = wrap.querySelector('.c-button');
      if (!triggerBtn) return;

      triggerBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var isOpen = triggerBtn.getAttribute('aria-expanded') === 'true';
        closeAllTooltips();
        if (!isOpen) triggerBtn.setAttribute('aria-expanded', 'true');
      });
    });

    document.addEventListener('click', closeAllTooltips);
  });
})();
