(function () {
  'use strict';

  function labelIds(select) {
    var ids = [];
    Array.prototype.forEach.call(select.labels || [], function (label, i) {
      if (!label.id) label.id = select.id + '-label' + (i ? '-' + i : '');
      ids.push(label.id);
    });
    return ids.concat((select.getAttribute('aria-labelledby') || '').split(' ').filter(Boolean));
  }

  function init(select) {
    var wrapper     = select.closest('.c-dropdown');
    var placeholder = select.querySelector('option[value=""]');
    var $select     = jQuery(select);

    $select.select2({
      theme:             'hdx-v2',
      width:             '100%',
      dropdownParent:    jQuery(wrapper),
      selectionCssClass: 'c-dropdown__select',
      placeholder:       placeholder ? { id: '', text: placeholder.textContent } : null,
      allowClear:        !!placeholder
    });

    var selection   = wrapper.querySelector('.select2-selection');
    var ids         = labelIds(select);
    var describedBy = select.getAttribute('aria-describedby');

    if (ids.length) {
      selection.setAttribute('aria-labelledby', ids.concat(selection.getAttribute('aria-labelledby') || []).join(' '));
    }
    if (describedBy) selection.setAttribute('aria-describedby', describedBy);

    $select.on('select2:open', function () {
      var search = wrapper.querySelector('.select2-search__field');
      if (!search) return;
      if (ids.length) search.setAttribute('aria-labelledby', ids.join(' '));
      search.focus();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('select[data-searchable]').forEach(init);
  });
})();
