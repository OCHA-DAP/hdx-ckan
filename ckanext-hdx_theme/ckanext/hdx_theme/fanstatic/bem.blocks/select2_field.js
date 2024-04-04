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

});
