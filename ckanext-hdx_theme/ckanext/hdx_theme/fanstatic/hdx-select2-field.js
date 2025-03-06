this.ckan.module('hdx-select2-field', function ($) {
  return {
    initialize: function () {
      this.setupSelectField();
    },

    setupSelectField: function () {
      var $select = $(this.el).parents('.select2-field');
      this.initSelect2($select);
    },

    initSelect2: function ($select2Field) {
      var $selectElement = $select2Field.find('select');

      var placeholder = $selectElement.data('placeholder');
      var multiple = $selectElement.data('multiple') === true;
      var tags = $selectElement.data('tags') === true;
      var allowClear = $selectElement.data('allow-clear') !== false;

      var ajaxURL = $selectElement.data('ajax-url');

      var attributes = {
        'dropdownParent': $select2Field,
        'theme': 'bootstrap-5',
        'placeholder': placeholder,
        'multiple': multiple,
        'tags': tags,
        'allowClear': allowClear,
        'selectionCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
        // 'dropdownCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
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
                if (extraParam.selector) {
                  data[extraParam.key] = $(extraParam.selector).val();
                } else {
                  data[extraParam.key] = params.term;
                }
              });
            }

            return data;
          },
          processResults: function (data) {
            var responseParams = $selectElement.data('ajax-response-params');
            var results = [];
            var uniqueResults = [];
            var seenIds = new Set();

            if (data.ResultSet && Array.isArray(data.ResultSet.Result)) {
              results = $.map(data.ResultSet.Result, function (entry) {
                var result = {};
                responseParams.forEach(function (responseParam) {
                  result[responseParam.key] = entry[responseParam.value];
                });
                return result;
              });
            } else {
              results = $.map(data, function (entry) {
                var result = {};
                responseParams.forEach(function (responseParam) {
                  result[responseParam.key] = entry[responseParam.value];
                });
                return result;
              });
            }

            for (var result of results) {
              if (!seenIds.has(result.id)) {
                uniqueResults.push(result);
                seenIds.add(result.id);
              }
            }

            return {
              results: uniqueResults
            };
          },
          cache: true,
        };
        attributes['minimumInputLength'] = 1;
      }

      $selectElement.select2(attributes);

      if ($selectElement.data('has-other-option') === true) {
        this.setupOtherOptionEvents($selectElement);
      }
      this.fixAutofocus($selectElement);
    },

    setupOtherOptionEvents: function ($selectElement) {
      const otherValues = ['other', 'hdx-other'];

      $selectElement
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
    },

    // https://github.com/select2/select2/issues/5993
    fixAutofocus: function ($selectElement) {
      $selectElement
        .on('select2:open', function (e) {
          console.log($(this).parent().parent().find('.select2-search__field'));
          $(this).parent().parent().find('.select2-search__field').get(0).focus();
        });
    },

  };
});
