(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var header = document.querySelector('.hdx-v2-dataset-header');
    if (!header) return;

    // ── Description expand / collapse ────────────────────────
    var descModule = header.querySelector('[data-module="dataset-page-header"]');
    if (descModule) {
      var btn   = descModule.querySelector('.c-text-button');
      var label = btn && btn.querySelector('.c-text-button__label');
      if (btn) {
        btn.addEventListener('click', function () {
          var isExpanded = descModule.classList.toggle('is-expanded');
          if (label) label.textContent = isExpanded ? 'Show less' : 'Show more';
          btn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        });
      }
    }

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
