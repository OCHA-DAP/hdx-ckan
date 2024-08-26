$(document).ready(function () {

  $('.select2-field').each(function () {
    var $selectElement = $(this).find('select');
    $selectElement.select2({
      'dropdownParent': $(this),
      'theme': 'bootstrap-5',
      'placeholder': $(this).data('placeholder'),
      'selectionCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
      // 'dropdownCssClass': $selectElement.hasClass('select2-field__select_size_large') ? 'select2--large' : $selectElement.hasClass('select2-field__select_size_small') ? 'select2--small' : '',
      'allowClear': 'true',
      'width': '100%'
    });
  });

  $('.select2-field__select[data-has-other-option="true"]')
    .on('select2:select', function (e) {
      var value = e.params.data.id;

      var name = $(this).attr('name');
      var new_name = name + "_other";

      var $form = $(this).closest('form');
      var $other_input = $form.find('input[name="' + new_name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field

      if (value === 'other') {
        $other_input_container.removeClass('d-none');
      } else {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    })
    .on('select2:clear', function (e) {
      var value = e.params.data[0].id;

      var name = $(this).attr('name');
      var new_name = name + "_other";

      var $form = $(this).closest('form');
      var $other_input = $form.find('input[name="' + new_name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field

      if (value === 'other') {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    })
    .on('change', function (e) {
      var name = $(this).attr('name');
      var new_name = name + "_other";

      var $form = $(this).closest('form');
      var $other_input = $form.find('input[name="' + new_name + '"]');
      var $other_input_container = $other_input.parent().parent(); // .input-field

      var value = $(this).val();
      if (value !== 'other') {
        $other_input.val('');
        $other_input_container.addClass('d-none');
      }
    });

});
