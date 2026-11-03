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
    var source      = select.getAttribute('data-source');
    var $select     = jQuery(select);
    var options     = {
      theme:             'hdx-v2',
      width:             '100%',
      dropdownParent:    jQuery(wrapper),
      selectionCssClass: 'c-dropdown__select',
      placeholder:       placeholder ? { id: '', text: placeholder.textContent } : null,
      allowClear:        !!placeholder
    };

    if (select.multiple) {
      options.placeholder = select.getAttribute('data-placeholder');
      options.allowClear  = false;
    }

    if (source) {
      options.minimumInputLength = 1;
      options.ajax = {
        url:      source,
        dataType: 'json',
        delay:    300,
        data:     function (params) { return { q: params.term }; },
        processResults: function (users) {
          return {
            results: users.map(function (user) {
              return { id: user.name, text: user.fullname ? user.fullname + ' (' + user.name + ')' : user.name };
            })
          };
        }
      };
      if (select.getAttribute('data-source-type') === 'tag') {
        options.ajax.data = function (params) { return { incomplete: params.term }; };
        options.ajax.processResults = function (reply) {
          return {
            results: reply.ResultSet.Result.map(function (tag) {
              return { id: tag.Name, text: tag.Name };
            })
          };
        };
      }
    }

    $select.select2(options);

    var selection   = wrapper.querySelector('.select2-selection');
    var inline      = wrapper.querySelector('.select2-search--inline .select2-search__field');
    var ids         = labelIds(select);
    var describedBy = select.getAttribute('aria-describedby');

    if (ids.length) {
      selection.setAttribute('aria-labelledby', ids.concat(selection.getAttribute('aria-labelledby') || []).join(' '));
      if (inline) inline.setAttribute('aria-labelledby', ids.join(' '));
    }
    if (describedBy) {
      selection.setAttribute('aria-describedby', describedBy);
      if (inline) inline.setAttribute('aria-describedby', describedBy + ' ' + inline.getAttribute('aria-describedby'));
    }

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
