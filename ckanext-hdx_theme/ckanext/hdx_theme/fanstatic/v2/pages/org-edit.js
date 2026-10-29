(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('req-create-org-form');
    if (!form) return;

    var description = document.getElementById('field-description');
    var modifiedAt  = document.getElementById('field-modified_at');
    var customOrg   = document.getElementById('field-custom_org');
    var booleans    = ['closed_organization', 'request_membership'].map(function (name) {
      return {
        checkbox: document.getElementById('field-' + name),
        hidden:   document.getElementById('hidden-field-' + name)
      };
    });

    function syncBooleans() {
      booleans.forEach(function (item) {
        item.hidden.value = item.checkbox.checked ? 'true' : 'false';
      });
    }

    booleans.forEach(function (item) {
      item.checkbox.addEventListener('change', syncBooleans);
    });

    form.addEventListener('image-upload:change', function () {
      customOrg.checked = true;
    });

    form.addEventListener('submit', function () {
      description.value = description.value.trim();
      modifiedAt.value = Date.now();
      syncBooleans();
    });
  });
})();
