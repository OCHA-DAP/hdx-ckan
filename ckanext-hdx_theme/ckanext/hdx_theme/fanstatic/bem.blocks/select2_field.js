$(document).ready(function () {

  $('.select2-field').each(function () {
    var $selectElement = $(this).find('select');

    var placeholder = $selectElement.data('placeholder');
    var multiple = $selectElement.data('multiple') === true;

    var ajaxURL = $selectElement.data('ajax-url');

    var attributes = {
      'dropdownParent': $(this),
      'theme': 'bootstrap-5',
      'placeholder': placeholder,
      'multiple': multiple,
      'selectionCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
      // 'dropdownCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
      'allowClear': 'true',
      'width': '100%',
    };

    if (ajaxURL) {
      attributes['ajax'] = {
        dataType: 'json',
        delay: 250,
        data: function (params) {
          var data = {
            q: params.term,
          };

          var extraParams = $selectElement.data('ajax-extra-params');

          if (Array.isArray(extraParams)) {
            extraParams.forEach(function (extraParam) {
              data[extraParam.key] = $(extraParam.selector).val();
            });
          }

          return data;
        },
        processResults: function (data) {
          var responseParams = $selectElement.data('ajax-response-params');

          return {
            results: $.map(data, function (entry) {
              var result = {};
              // Set id and text based on the ajax-response-params
              responseParams.forEach(function (responseParam) {
                result[responseParam.key] = entry[responseParam.value];
              });
              return result;
            })
          };
        },
        cache: true,
      };
      attributes['minimumInputLength'] = 1;
    }

    $selectElement.select2(attributes);
  });

  const otherValues = ['other', 'hdx-other'];
  $('.select2-field__select[data-has-other-option="true"]')
    .on('select2:select', function (e) {
      var value = e.params.data.id;

      var name = $(this).attr('name');

      var $form = $(this).closest('form');
      var $other_input = $form.find('[data-parent-field="' + name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field or .textarea-field

      if (otherValues.includes(value.toLowerCase())) {
        $other_input_container.removeClass('d-none');
      } else {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    })
    .on('select2:clear', function (e) {
      var value = e.params.data[0].id;

      var name = $(this).attr('name');

      var $form = $(this).closest('form');
      var $other_input = $form.find('[data-parent-field="' + name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field or .textarea-field

      if (otherValues.includes(value.toLowerCase())) {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    })
    .on('change', function (e) {
      var name = $(this).attr('name');

      var $form = $(this).closest('form');
      var $other_input = $form.find('[data-parent-field="' + name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field or .textarea-field

      var value = $(this).val();
      if (!otherValues.includes(value.toLowerCase())) {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    });

});
