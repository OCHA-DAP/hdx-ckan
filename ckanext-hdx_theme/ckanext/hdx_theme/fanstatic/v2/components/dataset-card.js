(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-module="dataset-card"]').forEach(function (desc) {
      var btn     = desc.querySelector('.c-text-button');
      var content = desc.querySelector('.c-dataset-card__desc-text');
      var label   = btn && btn.querySelector('.c-text-button__label');

      if (!btn || !content) return;

      btn.addEventListener('click', function () {
        var isOpen = content.classList.toggle('is-open');
        desc.classList.toggle('is-open', isOpen);
        if (label) label.textContent = isOpen ? 'Show less' : 'Show more';
        btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
    });
  });
})();
