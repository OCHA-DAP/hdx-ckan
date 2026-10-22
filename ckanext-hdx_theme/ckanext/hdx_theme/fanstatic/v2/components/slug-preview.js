(function () {
  'use strict';

  function init(root) {
    var field       = root.querySelector('[data-slug-preview-field]');
    var input       = field.querySelector('input');
    var preview     = root.querySelector('[data-slug-preview-preview]');
    var valueEl     = root.querySelector('[data-slug-preview-value]');
    var edit        = root.querySelector('[data-slug-preview-edit]');
    var placeholder = valueEl.getAttribute('data-slug-preview-placeholder');
    var target      = document.getElementById(root.getAttribute('data-slug-preview-target'));

    function update() {
      valueEl.textContent = jQuery.url.escape(input.value) || placeholder;
    }

    function reveal() {
      edit.setAttribute('aria-expanded', 'true');
      preview.hidden = true;
      field.hidden = false;
    }

    jQuery(input).slug();

    if (target && target.value === '') {
      var follow = function () {
        input.value = jQuery.url.slugify(target.value, true);
        update();
      };
      var stop = function (e) {
        if (e.type === 'keypress' && !e.charCode) return;
        target.removeEventListener('input', follow);
        input.removeEventListener('keypress', stop);
        input.removeEventListener('input', stop);
      };
      target.addEventListener('input', follow);
      input.addEventListener('keypress', stop);
      input.addEventListener('input', stop);
    }

    if (root.hasAttribute('data-slug-preview-error')) return;

    update();
    field.hidden = true;
    preview.hidden = false;

    input.addEventListener('invalid', reveal);
    edit.addEventListener('click', function () {
      reveal();
      input.focus();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-slug-preview]').forEach(init);
  });
})();
