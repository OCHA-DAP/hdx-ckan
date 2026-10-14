(function () {
  'use strict';

  function init(container) {
    var btn     = container.querySelector('[data-clamped-toggle]');
    var content = container.querySelector('[data-clamped-content]');
    var label   = btn && btn.querySelector('.c-text-button__label');

    if (!btn || !content) return;

    // If the card was pre-opened server-side (is-open already on container),
    // we can't measure clamped height — assume it would be clamped.
    // Otherwise check actual overflow.
    var isClamped = container.classList.contains('is-open') ||
                    content.scrollHeight > content.clientHeight;

    if (!isClamped) return;

    container.classList.add('is-clamped');

    btn.addEventListener('click', function () {
      var isOpen = content.classList.toggle('is-open');
      container.classList.toggle('is-open', isOpen);
      if (label) label.textContent = isOpen ? 'Show less' : 'Show more';
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-module~="clamped-text"]').forEach(function (container) {
      var details = container.closest('details:not([open])');
      if (!details) {
        init(container);
        return;
      }
      details.addEventListener('toggle', function onToggle() {
        if (!details.open) return;
        details.removeEventListener('toggle', onToggle);
        init(container);
      });
    });
  });
})();
