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

    // ── Tooltip triggers ──────────────────────────────────────
    // Hover/focus visibility is handled by CSS (.c-info-icon:hover ~ .c-tooltip etc.).
    // JS manages the is-open state for click/tap, aria-expanded, and keyboard close.
    var tooltipWraps = header.querySelectorAll('.c-tooltip-anchor');

    function closeAllTooltips() {
      tooltipWraps.forEach(function (wrap) {
        var icon = wrap.querySelector('.c-info-icon');
        if (icon) {
          icon.classList.remove('is-open');
          icon.setAttribute('aria-expanded', 'false');
        }
      });
    }

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

    // Escape closes any open tooltip and returns focus to its trigger (V-13)
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var openIcon = header.querySelector('.c-info-icon.is-open');
      if (openIcon) {
        closeAllTooltips();
        openIcon.focus();
      }
    });

    document.addEventListener('click', closeAllTooltips);
  });
})();
