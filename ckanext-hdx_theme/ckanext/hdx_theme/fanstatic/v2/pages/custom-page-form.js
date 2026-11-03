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

    list.addEventListener('config-item:add', function (e) {
      var index = parseInt(e.target.querySelector('[data-section-type]').name.match(/^field_section_(\d+)_type$/)[1], 10);
      counter.value = Math.max(parseInt(counter.value, 10) || 0, index + 1);
    });
  });
})();
