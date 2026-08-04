(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {

    var requestSentInput = document.getElementById('request_sent');
    var requestSent = requestSentInput ? requestSentInput.value : null;

    if (requestSent && requestSent.toLowerCase() === 'true') {
      var analyticsPromise = hdxUtil.analytics.sendMessagingEvent(
        'dataset',
        'data request',
        null,
        null,
        true
      );

      analyticsPromise.then(
        function () {
          console.log('Analytics event sent successfully');
        },
        function () {
          console.error('Failed to send the analytics event');
        }
      );
    }

    var form = document.getElementById('request-access-form');
    if (!form) {
      return;
    }

    var otherValues = ['other', 'hdx-other'];

    function wireOtherReveal(selectId, otherFieldSelector, requiredWhenShown) {
      var select = form.querySelector('#' + selectId);
      var otherField = form.querySelector(otherFieldSelector);

      if (!select || !otherField) {
        return;
      }

      var input = otherField.querySelector('input, textarea');

      var sync = function () {
        var value = (select.value || '').toLowerCase();
        var isOther = otherValues.indexOf(value) !== -1;

        if (isOther) {
          otherField.classList.remove('hdx-v2-request-access-other--hidden');
          if (requiredWhenShown && input) {
            input.setAttribute('required', 'required');
          }
        } else {
          otherField.classList.add('hdx-v2-request-access-other--hidden');
          if (input) {
            input.removeAttribute('required');
            input.value = '';
          }
        }
      };

      select.addEventListener('change', sync);
      sync();
    }

    wireOtherReveal('request-sender-organization-id', '[data-other-field-for="sender_organization_id"]', false);
    wireOtherReveal('request-sender-organization-type', '[data-other-field-for="sender_organization_type"]', true);
    wireOtherReveal('request-sender-intend', '[data-other-field-for="sender_intend"]', true);

    // Auto-fill "Your organization type" from the selected organization's known type
    var orgSelect = form.querySelector('#request-sender-organization-id');
    var orgTypeSelect = form.querySelector('#request-sender-organization-type');

    if (orgSelect && orgTypeSelect) {
      orgSelect.addEventListener('change', function () {
        var selectedOption = orgSelect.options[orgSelect.selectedIndex];
        var orgType = selectedOption ? selectedOption.getAttribute('data-org-type') : null;

        orgTypeSelect.value = orgType || '';
        orgTypeSelect.dispatchEvent(new Event('change'));
      });
    }

  });
})();
