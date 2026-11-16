(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('create_page_form');
    if (!form) return;

    var list    = form.querySelector('[data-section-fields]');
    var fields  = JSON.parse(list.getAttribute('data-section-fields'));
    var counter = document.getElementById('hdx_counter');
    var prefix  = form.querySelector('[data-slug-preview-prefix]');

    function showFields(select) {
      var used = fields[select.value] || [];
      select.closest('[data-config-item]').querySelectorAll('[data-section-field]').forEach(function (wrapper) {
        var visible = used.indexOf(wrapper.getAttribute('data-section-field')) !== -1;
        wrapper.hidden = !visible;
        wrapper.querySelector('input, textarea').disabled = !visible;
      });
    }

    form.addEventListener('change', function (e) {
      if (e.target.matches('[data-section-type]')) {
        showFields(e.target);
      } else if (e.target.matches('[data-slug-prefix]') && prefix) {
        prefix.textContent = e.target.getAttribute('data-slug-prefix');
      }
    });

    form.addEventListener('submit', function () {
      var cards = list.querySelectorAll('[data-config-item]');
      cards.forEach(function (card, index) {
        card.querySelectorAll('[name^="field_section_"]').forEach(function (control) {
          control.name = control.name.replace(/^field_section_\d+_/, 'field_section_' + index + '_');
        });
      });
      counter.value = cards.length;
    });
  });
})();
